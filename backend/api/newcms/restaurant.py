"""Endpoints API NewCMS Restaurant et Mobile.

Restaurant : utilise les tables restaurant_plats, restaurant_ingredients, restaurant_plat_ingredients
Mobile : utilise la table produits (épicerie, tenant_id=1) avec code-barres EAN
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from pydantic import BaseModel

from backend.dependencies.tenant import Tenant, get_current_tenant_or_default
from core.data_repository import get_engine, query_df
from backend.services.restaurant import menus as restaurant_menus_service
from backend.services.restaurant import overview as restaurant_overview_service
from backend.schemas.restaurant import RestaurantMenuOverview, PlatDetail


# =============================================================================
# SCHEMAS
# =============================================================================

class RestaurantPlatCost(BaseModel):
    plat_id: int
    nom: str
    prix_vente_ttc: float
    cout_matiere: float
    food_cost_pct: float
    marge_pct: float


class RestaurantIngredientAlert(BaseModel):
    ingredient_id: int
    nom: str
    stock_actuel: float
    cout_unitaire: float
    status: str  # "rupture" or "bas" or "ok"


class RestaurantStockLocation(BaseModel):
    location: str
    valeur: float
    count: int


class RestaurantTopPlat(BaseModel):
    plat_id: int
    nom: str
    marge_pct: float
    prix_vente_ttc: float
    cout_matiere: float


class RestaurantOverviewMetrics(BaseModel):
    total_plats: int
    avg_food_cost_pct: float
    alerts_count: int
    top_plats: List[RestaurantTopPlat]


class RestaurantOverviewResponse(BaseModel):
    success: bool = True
    metrics: RestaurantOverviewMetrics
    plat_costs: List[RestaurantPlatCost]
    stock_locations: List[RestaurantStockLocation]
    ingredient_alerts: List[RestaurantIngredientAlert]


# Mobile schemas - pour les produits epicerie
class MobileInventoryItem(BaseModel):
    id: int
    nom: str
    ean: Optional[str] = None
    stock_actuel: float
    seuil_alerte: float
    categorie: Optional[str] = None


class MobileInventoryListResponse(BaseModel):
    success: bool = True
    items: List[MobileInventoryItem]
    total: int
    page: int
    page_size: int


class MobileScanRequest(BaseModel):
    ean: str


class MobileScanResponse(BaseModel):
    success: bool = True
    found: bool
    product: Optional[MobileInventoryItem] = None
    message: Optional[str] = None


class MobileAdjustRequest(BaseModel):
    product_id: int
    adjustment: float
    adjustment_type: str = "delta"  # "delta" or "absolute"
    reason: str  # breakage, theft, error, expiry, other
    notes: Optional[str] = None


class MobileAdjustResponse(BaseModel):
    success: bool = True
    product_id: int
    product_name: str
    old_stock: float
    new_stock: float
    adjustment: float
    reason: str
    timestamp: datetime


# =============================================================================
# ROUTERS
# =============================================================================

router = APIRouter(prefix="/restaurant", tags=["newcms-restaurant"])
mobile_router = APIRouter(prefix="/mobile", tags=["newcms-mobile"])


# =============================================================================
# RESTAURANT OVERVIEW - Tables restaurant_*
# =============================================================================

@router.get("/overview", response_model=RestaurantOverviewResponse, summary="Overview Restaurant", tags=["newcms-restaurant"])
def get_restaurant_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
    """
    **Restaurant Overview - Vue d'ensemble restaurant**

    Endpoint agrégé pour la gestion restaurant avec calcul des coûts plats,
    alertes ingrédients et indicateurs de food cost.

    ## Données retournées

    ### Métriques globales
    - **total_plats**: Nombre de plats actifs au menu
    - **avg_food_cost_pct**: Food cost moyen en % du prix de vente
    - **alerts_count**: Nombre d'alertes ingrédients
    - **top_plats**: Top 5 plats par marge

    ### Coûts des plats
    Pour chaque plat:
    - **prix_vente_ttc**: Prix de vente TTC (€)
    - **cout_matiere**: Coût matière calculé (€)
    - **food_cost_pct**: Food cost en %
    - **marge_pct**: Marge en %

    ### Alertes ingrédients
    - Ingrédients en rupture (stock <= 0)
    - Ingrédients en stock bas (stock < 5)
    - Coût unitaire et impact

    ### Stock par localisation
    - Valeur totale du stock (€)
    - Nombre d'ingrédients

    ## Tags
    - newcms-restaurant
    """
    # 1. Plat costs avec food cost %
    plat_costs_sql = text("""
        WITH ingredient_costs AS (
            SELECT
                rpi.plat_id,
                SUM(rpi.quantite * COALESCE(ri.cout_unitaire, 0)) AS cout_matiere
            FROM restaurant_plat_ingredients rpi
            JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
            WHERE rpi.tenant_id = :tenant_id
            GROUP BY rpi.plat_id
        )
        SELECT
            rp.id AS plat_id,
            rp.nom,
            COALESCE(rp.prix_vente_ttc, 0) AS prix_vente_ttc,
            COALESCE(ic.cout_matiere, 0) AS cout_matiere,
            CASE
                WHEN COALESCE(rp.prix_vente_ttc, 0) > 0 THEN
                    ROUND((COALESCE(ic.cout_matiere, 0) / rp.prix_vente_ttc * 100)::numeric, 2)
                ELSE 0
            END AS food_cost_pct,
            CASE
                WHEN COALESCE(rp.prix_vente_ttc, 0) > 0 THEN
                    ROUND(((rp.prix_vente_ttc - COALESCE(ic.cout_matiere, 0)) / rp.prix_vente_ttc * 100)::numeric, 2)
                ELSE 0
            END AS marge_pct
        FROM restaurant_plats rp
        LEFT JOIN ingredient_costs ic ON ic.plat_id = rp.id
        WHERE rp.tenant_id = :tenant_id AND rp.actif = true
        ORDER BY rp.nom
    """)

    plat_costs_df = query_df(plat_costs_sql, {"tenant_id": tenant.id})
    plat_costs = [
        RestaurantPlatCost(
            plat_id=int(row["plat_id"]),
            nom=row["nom"],
            prix_vente_ttc=float(row["prix_vente_ttc"]),
            cout_matiere=float(row["cout_matiere"]),
            food_cost_pct=float(row["food_cost_pct"]),
            marge_pct=float(row["marge_pct"]),
        )
        for row in plat_costs_df.to_dict("records")
    ] if not plat_costs_df.empty else []

    # 2. Alertes ingredients (stock bas ou rupture)
    alert_sql = text("""
        SELECT
            ri.id AS ingredient_id,
            ri.nom,
            COALESCE(ri.stock_actuel, 0) AS stock_actuel,
            COALESCE(ri.cout_unitaire, 0) AS cout_unitaire,
            CASE
                WHEN COALESCE(ri.stock_actuel, 0) <= 0 THEN 'rupture'
                WHEN COALESCE(ri.stock_actuel, 0) < 5 THEN 'bas'
                ELSE 'ok'
            END AS status
        FROM restaurant_ingredients ri
        WHERE ri.tenant_id = :tenant_id
          AND COALESCE(ri.stock_actuel, 0) < 5
        ORDER BY stock_actuel ASC, ri.nom
        LIMIT 20
    """)

    alerts_df = query_df(alert_sql, {"tenant_id": tenant.id})
    ingredient_alerts = [
        RestaurantIngredientAlert(
            ingredient_id=int(row["ingredient_id"]),
            nom=row["nom"],
            stock_actuel=float(row["stock_actuel"]),
            cout_unitaire=float(row["cout_unitaire"]),
            status=row["status"],
        )
        for row in alerts_df.to_dict("records")
    ] if not alerts_df.empty else []

    # 3. Stock par location (valeur totale des ingredients)
    stock_value_sql = text("""
        SELECT
            COALESCE(SUM(ri.stock_actuel * ri.cout_unitaire), 0) AS valeur_totale,
            COUNT(*) AS count
        FROM restaurant_ingredients ri
        WHERE ri.tenant_id = :tenant_id
    """)
    stock_df = query_df(stock_value_sql, {"tenant_id": tenant.id})
    total_value = float(stock_df["valeur_totale"].iloc[0]) if not stock_df.empty else 0.0
    total_count = int(stock_df["count"].iloc[0]) if not stock_df.empty else 0

    stock_locations = [
        RestaurantStockLocation(location="cuisine", valeur=total_value, count=total_count),
    ]

    # 4. Top 5 plats par marge %
    top_plats = sorted(plat_costs, key=lambda x: x.marge_pct, reverse=True)[:5]
    top_plats_list = [
        RestaurantTopPlat(
            plat_id=p.plat_id,
            nom=p.nom,
            marge_pct=p.marge_pct,
            prix_vente_ttc=p.prix_vente_ttc,
            cout_matiere=p.cout_matiere,
        )
        for p in top_plats
    ]

    # Metrics
    avg_food_cost = sum(p.food_cost_pct for p in plat_costs) / len(plat_costs) if plat_costs else 0.0

    metrics = RestaurantOverviewMetrics(
        total_plats=len(plat_costs),
        avg_food_cost_pct=round(avg_food_cost, 2),
        alerts_count=len(ingredient_alerts),
        top_plats=top_plats_list,
    )

    return RestaurantOverviewResponse(
        metrics=metrics,
        plat_costs=plat_costs,
        stock_locations=stock_locations,
        ingredient_alerts=ingredient_alerts,
    )


@router.get("/menus/overview", response_model=RestaurantMenuOverview, summary="Menus & Coûts", tags=["newcms-restaurant"])
def get_menus_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
    """Vue d'ensemble Menus & Coûts (food cost, marges, alertes ingrédients)"""
    return restaurant_menus_service.get_menu_overview(tenant.id)


@router.get("/plat/{plat_id}", response_model=PlatDetail, summary="Détail plat (restaurant)", tags=["newcms-restaurant"])
def get_plat_detail(
    plat_id: int,
    tenant: Tenant = Depends(get_current_tenant_or_default),
):
    """Détail d'un plat restaurant (fiche technique, prix, marge)."""
    payload = restaurant_overview_service.get_plat_detail(tenant.id, plat_id)
    return PlatDetail(**payload)


# =============================================================================
# MOBILE ENDPOINTS - Table produits (epicerie)
# =============================================================================

EPICERIE_TENANT_ID = 1  # Les produits mobile sont dans le tenant epicerie


@mobile_router.get("/inventory", response_model=MobileInventoryListResponse, summary="Inventaire mobile", tags=["newcms-mobile"])
def get_mobile_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    tenant: Tenant = Depends(get_current_tenant_or_default),
):
    """
    **Inventaire mobile - Liste paginée**

    Endpoint optimisé pour l'application mobile d'inventaire.
    Permet de naviguer dans le catalogue produits avec recherche.

    ## Paramètres

    - **page**: Numéro de page (défaut: 1)
    - **page_size**: Taille de page (1-200, défaut: 50)
    - **search**: Recherche sur nom ou code EAN

    ## Données retournées

    Pour chaque produit:
    - **id**: ID du produit
    - **nom**: Nom du produit
    - **ean**: Code-barres EAN (si disponible)
    - **stock_actuel**: Stock actuel
    - **seuil_alerte**: Seuil d'alerte
    - **categorie**: Catégorie

    ## Tags
    - newcms-mobile
    """
    offset = (page - 1) * page_size

    search_clause = ""
    params = {"tenant_id": EPICERIE_TENANT_ID}

    if search:
        search_clause = "AND (p.nom ILIKE :search OR p.ean ILIKE :search)"
        params["search"] = f"%{search}%"

    # LIMIT et OFFSET sont des entiers sûrs, on les injecte directement
    inventory_sql = text(f"""
        SELECT
            p.id,
            p.nom,
            p.ean,
            COALESCE(p.stock_actuel, 0) AS stock_actuel,
            COALESCE(p.seuil_alerte, 0) AS seuil_alerte,
            p.categorie
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
          {search_clause}
        ORDER BY p.nom
        LIMIT {page_size} OFFSET {offset}
    """)

    count_sql = text(f"""
        SELECT COUNT(*) AS total
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
          {search_clause}
    """)

    items_df = query_df(inventory_sql, params)
    count_df = query_df(count_sql, params)
    total = int(count_df["total"].iloc[0]) if not count_df.empty else 0

    items = [
        MobileInventoryItem(
            id=int(row["id"]),
            nom=row["nom"],
            ean=row.get("ean"),
            stock_actuel=float(row["stock_actuel"]),
            seuil_alerte=float(row["seuil_alerte"]),
            categorie=row.get("categorie"),
        )
        for row in items_df.to_dict("records")
    ] if not items_df.empty else []

    return MobileInventoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@mobile_router.post("/scan", response_model=MobileScanResponse, summary="Scan code-barres", tags=["newcms-mobile"])
def scan_barcode(
    payload: MobileScanRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
):
    """
    **Scan code-barres - Recherche par EAN**

    Endpoint pour scanner un code-barres EAN et récupérer les informations produit.
    Utilisé par l'application mobile pour l'inventaire rapide.

    ## Body de la requête

    ```json
    {
      "ean": "3760123456789"
    }
    ```

    ## Réponse

    - **found**: true si produit trouvé, false sinon
    - **product**: Informations du produit (si trouvé)
    - **message**: Message d'erreur (si non trouvé)

    ## Tags
    - newcms-mobile
    """
    scan_sql = text("""
        SELECT
            p.id,
            p.nom,
            p.ean,
            COALESCE(p.stock_actuel, 0) AS stock_actuel,
            COALESCE(p.seuil_alerte, 0) AS seuil_alerte,
            p.categorie
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND p.ean = :ean
          AND p.actif = true
        LIMIT 1
    """)

    result_df = query_df(scan_sql, {"tenant_id": EPICERIE_TENANT_ID, "ean": payload.ean})

    if result_df.empty:
        return MobileScanResponse(
            found=False,
            product=None,
            message=f"Aucun produit trouve pour le code EAN: {payload.ean}",
        )

    row = result_df.iloc[0]
    product = MobileInventoryItem(
        id=int(row["id"]),
        nom=row["nom"],
        ean=row.get("ean"),
        stock_actuel=float(row["stock_actuel"]),
        seuil_alerte=float(row["seuil_alerte"]),
        categorie=row.get("categorie"),
    )

    return MobileScanResponse(
        found=True,
        product=product,
        message=None,
    )


@mobile_router.post("/adjust", response_model=MobileAdjustResponse, summary="Ajustement stock mobile", tags=["newcms-mobile"])
def adjust_stock(
    payload: MobileAdjustRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
):
    """
    **Ajustement stock - Correction depuis mobile**

    Endpoint pour ajuster le stock depuis l'application mobile.
    Crée un mouvement de stock pour la traçabilité complète.

    ## Body de la requête

    ```json
    {
      "product_id": 123,
      "adjustment": -5,
      "adjustment_type": "delta",
      "reason": "breakage",
      "notes": "Casse lors du déballage"
    }
    ```

    ## Paramètres

    - **product_id**: ID du produit
    - **adjustment**: Quantité d'ajustement
    - **adjustment_type**: "delta" (relatif) ou "absolute" (absolu)
    - **reason**: Raison (breakage, theft, error, expiry, other)
    - **notes**: Notes optionnelles (max 500 caractères)

    ## Validations

    - Raison obligatoire parmi les valeurs acceptées
    - Stock ne peut pas être négatif (min: 0)
    - Mouvement de stock créé pour traçabilité

    ## Tags
    - newcms-mobile
    """
    if payload.reason not in ["breakage", "theft", "error", "expiry", "other"]:
        raise HTTPException(status_code=400, detail="Raison d'ajustement invalide")

    with get_engine().begin() as conn:
        # Recuperer le stock actuel
        current_row = conn.execute(
            text("""
                SELECT p.nom, COALESCE(p.stock_actuel, 0) AS stock_actuel
                FROM produits p
                WHERE p.id = :product_id AND p.tenant_id = :tenant_id
                FOR UPDATE
            """),
            {"product_id": payload.product_id, "tenant_id": EPICERIE_TENANT_ID},
        ).fetchone()

        if not current_row:
            raise HTTPException(status_code=404, detail="Produit non trouve")

        old_stock = float(current_row.stock_actuel)
        product_name = current_row.nom

        # Calculer le nouveau stock
        if payload.adjustment_type == "absolute":
            new_stock = max(0.0, float(payload.adjustment))
            actual_adjustment = new_stock - old_stock
        else:  # delta
            new_stock = max(0.0, old_stock + float(payload.adjustment))
            actual_adjustment = float(payload.adjustment)

        # Mettre a jour le stock
        conn.execute(
            text("""
                UPDATE produits
                SET stock_actuel = :new_stock, updated_at = NOW()
                WHERE id = :product_id AND tenant_id = :tenant_id
            """),
            {"new_stock": new_stock, "product_id": payload.product_id, "tenant_id": EPICERIE_TENANT_ID},
        )

        # Creer un mouvement de stock pour tracabilite
        movement_type = "ENTREE" if actual_adjustment > 0 else "SORTIE"
        conn.execute(
            text("""
                INSERT INTO mouvements_stock (
                    tenant_id,
                    produit_id,
                    type,
                    quantite,
                    date_mvt,
                    source
                )
                VALUES (
                    :tenant_id,
                    :product_id,
                    :type,
                    :quantite,
                    NOW(),
                    :source
                )
            """),
            {
                "tenant_id": EPICERIE_TENANT_ID,
                "product_id": payload.product_id,
                "type": movement_type,
                "quantite": abs(actual_adjustment),
                "source": f"mobile:{payload.reason}:{payload.notes or ''}",
            },
        )

    return MobileAdjustResponse(
        product_id=payload.product_id,
        product_name=product_name,
        old_stock=round(old_stock, 2),
        new_stock=round(new_stock, 2),
        adjustment=round(actual_adjustment, 2),
        reason=payload.reason,
        timestamp=datetime.utcnow(),
    )


__all__ = ["router", "mobile_router"]
