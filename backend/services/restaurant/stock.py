"""
Service Stock Restaurant - Gestion du stock indépendant du restaurant.

Le stock restaurant est séparé du stock épicerie et tracé via les mouvements
avec référence aux factures d'origine.
"""

import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df


def _df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convertit un DataFrame en liste de dicts avec gestion des NaN."""
    if df.empty:
        return []
    # Remplacer NaN par None
    df = df.where(pd.notnull(df), None)
    # Convertir les colonnes entières
    int_cols = ['id', 'ingredient_id', 'produit_epicerie_id', 'facture_id', 'nb_mouvements']
    for col in int_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if x is not None and not pd.isna(x) else None)
    # Utiliser json pour une sérialisation correcte
    return json.loads(df.to_json(orient='records', date_format='iso'))


def list_stock_movements(
    tenant_id: int,
    ingredient_id: Optional[int] = None,
    source: Optional[str] = None,
    type_mouvement: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Liste les mouvements de stock restaurant avec filtres.
    """
    conditions = ["m.tenant_id = :tenant_id"]
    params: Dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

    if ingredient_id:
        conditions.append("m.ingredient_id = :ingredient_id")
        params["ingredient_id"] = ingredient_id

    if source:
        conditions.append("m.source = :source")
        params["source"] = source

    if type_mouvement:
        conditions.append("m.type_mouvement = :type_mouvement")
        params["type_mouvement"] = type_mouvement

    if date_from:
        conditions.append("m.date_mouvement >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("m.date_mouvement <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            m.id,
            m.ingredient_id,
            ri.nom AS ingredient_nom,
            ri.unite_base,
            ri.categorie AS ingredient_categorie,
            m.type_mouvement,
            m.quantite,
            m.unite,
            m.cout_unitaire,
            m.cout_total,
            m.source,
            m.facture_id,
            m.facture_ref,
            m.fournisseur,
            m.produit_epicerie_id,
            p.nom AS produit_epicerie_nom,
            m.commentaire,
            m.date_mouvement,
            m.created_by,
            m.created_at
        FROM restaurant_stock_movements m
        JOIN restaurant_ingredients ri ON ri.id = m.ingredient_id
        LEFT JOIN produits p ON p.id = m.produit_epicerie_id
        WHERE {where_clause}
        ORDER BY m.date_mouvement DESC, m.id DESC
        LIMIT :limit OFFSET :offset
    """)

    df = query_df(sql, params)
    return _df_to_records(df)


def get_stock_summary(tenant_id: int) -> List[Dict[str, Any]]:
    """
    Retourne le résumé du stock actuel par ingrédient avec dernier mouvement.
    """
    sql = text("""
        SELECT
            ri.id AS ingredient_id,
            ri.nom AS ingredient_nom,
            ri.unite_base,
            ri.stock_actuel,
            ri.stock_min,
            ri.cout_unitaire,
            ri.categorie,
            ri.fournisseur,
            COALESCE(v.stock_calcule, 0) AS stock_calcule,
            v.dernier_mouvement,
            v.nb_mouvements,
            CASE
                WHEN ri.stock_min > 0 AND COALESCE(v.stock_calcule, 0) <= ri.stock_min THEN 'alerte'
                WHEN COALESCE(v.stock_calcule, 0) <= 0 THEN 'rupture'
                ELSE 'ok'
            END AS statut_stock
        FROM restaurant_ingredients ri
        LEFT JOIN v_restaurant_stock_actuel v ON v.ingredient_id = ri.id AND v.tenant_id = :tenant_id
        WHERE ri.tenant_id = :tenant_id
        ORDER BY ri.nom
    """)

    df = query_df(sql, {"tenant_id": tenant_id})
    return _df_to_records(df)


def get_daily_movements_by_category(
    tenant_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    type_mouvement: str = "sortie",
) -> Dict[str, Any]:
    """
    Agrège les mouvements par jour et catégorie pour les graphiques.
    Retourne les données pivotées par catégorie.
    """
    conditions = ["m.tenant_id = :tenant_id", "LOWER(m.type_mouvement) = LOWER(:type_mouvement)"]
    params: Dict[str, Any] = {"tenant_id": tenant_id, "type_mouvement": type_mouvement}

    if date_from:
        conditions.append("m.date_mouvement >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("m.date_mouvement <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            m.date_mouvement::date AS jour,
            COALESCE(ri.categorie, 'Non classé') AS categorie,
            SUM(m.quantite) AS total_quantite
        FROM restaurant_stock_movements m
        JOIN restaurant_ingredients ri ON ri.id = m.ingredient_id
        WHERE {where_clause}
        GROUP BY m.date_mouvement::date, ri.categorie
        ORDER BY jour
    """)

    df = query_df(sql, params)
    if df.empty:
        return {"series": [], "categories": []}

    # Pivoter les données par catégorie
    pivot = df.pivot(index='jour', columns='categorie', values='total_quantite').fillna(0)
    pivot = pivot.reset_index()
    pivot['jour'] = pivot['jour'].astype(str)

    categories = [col for col in pivot.columns if col != 'jour']

    return {
        "series": json.loads(pivot.to_json(orient='records')),
        "categories": categories,
    }


def create_stock_movement(
    tenant_id: int,
    ingredient_id: int,
    type_mouvement: str,
    quantite: float,
    source: str,
    unite: Optional[str] = None,
    cout_unitaire: Optional[float] = None,
    facture_id: Optional[int] = None,
    facture_ref: Optional[str] = None,
    fournisseur: Optional[str] = None,
    produit_epicerie_id: Optional[int] = None,
    commentaire: Optional[str] = None,
    date_mouvement: Optional[datetime] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crée un mouvement de stock et met à jour le stock de l'ingrédient.
    """
    if date_mouvement is None:
        date_mouvement = datetime.now()

    cout_total = (cout_unitaire or 0) * quantite if cout_unitaire else None

    with get_engine().begin() as conn:
        # Insérer le mouvement
        result = conn.execute(
            text("""
                INSERT INTO restaurant_stock_movements (
                    tenant_id, ingredient_id, type_mouvement, quantite, unite,
                    cout_unitaire, cout_total, source, facture_id, facture_ref,
                    fournisseur, produit_epicerie_id, commentaire, date_mouvement, created_by
                )
                VALUES (
                    :tenant_id, :ingredient_id, :type_mouvement, :quantite, :unite,
                    :cout_unitaire, :cout_total, :source, :facture_id, :facture_ref,
                    :fournisseur, :produit_epicerie_id, :commentaire, :date_mouvement, :created_by
                )
                RETURNING id
            """),
            {
                "tenant_id": tenant_id,
                "ingredient_id": ingredient_id,
                "type_mouvement": type_mouvement,
                "quantite": quantite,
                "unite": unite,
                "cout_unitaire": cout_unitaire,
                "cout_total": cout_total,
                "source": source,
                "facture_id": facture_id,
                "facture_ref": facture_ref,
                "fournisseur": fournisseur,
                "produit_epicerie_id": produit_epicerie_id,
                "commentaire": commentaire,
                "date_mouvement": date_mouvement,
                "created_by": created_by,
            },
        )
        movement_id = result.fetchone()[0]

        # Mettre à jour le stock de l'ingrédient
        delta = quantite if type_mouvement in ("entree", "transfert_epicerie", "ajustement") else -quantite
        conn.execute(
            text("""
                UPDATE restaurant_ingredients
                SET stock_actuel = COALESCE(stock_actuel, 0) + :delta
                WHERE id = :ingredient_id AND tenant_id = :tenant_id
            """),
            {"delta": delta, "ingredient_id": ingredient_id, "tenant_id": tenant_id},
        )

        # Si c'est une entrée avec coût, mettre à jour le coût unitaire moyen
        if type_mouvement == "entree" and cout_unitaire:
            conn.execute(
                text("""
                    UPDATE restaurant_ingredients
                    SET cout_unitaire = COALESCE(
                        (COALESCE(cout_unitaire, 0) * GREATEST(stock_actuel - :quantite, 0) + :cout_unitaire * :quantite)
                        / NULLIF(stock_actuel, 0),
                        :cout_unitaire
                    )
                    WHERE id = :ingredient_id AND tenant_id = :tenant_id
                """),
                {
                    "quantite": quantite,
                    "cout_unitaire": cout_unitaire,
                    "ingredient_id": ingredient_id,
                    "tenant_id": tenant_id,
                },
            )

    return {"id": movement_id, "type_mouvement": type_mouvement, "quantite": quantite}


def transfer_from_epicerie(
    tenant_id: int,
    ingredient_id: int,
    produit_epicerie_id: int,
    quantite: float,
    commentaire: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transfère du stock depuis un produit épicerie vers un ingrédient restaurant.
    Crée un mouvement de type 'transfert_epicerie'.
    """
    # Récupérer les infos du produit épicerie
    sql = text("""
        SELECT nom, prix_achat, categorie
        FROM produits
        WHERE id = :produit_id
    """)
    df = query_df(sql, {"produit_id": produit_epicerie_id})

    if df.empty:
        raise ValueError(f"Produit épicerie {produit_epicerie_id} non trouvé")

    produit = df.iloc[0]
    cout_unitaire = float(produit["prix_achat"] or 0)

    # Créer le mouvement de transfert
    return create_stock_movement(
        tenant_id=tenant_id,
        ingredient_id=ingredient_id,
        type_mouvement="transfert_epicerie",
        quantite=quantite,
        source="epicerie",
        cout_unitaire=cout_unitaire,
        produit_epicerie_id=produit_epicerie_id,
        commentaire=commentaire or f"Transfert depuis épicerie: {produit['nom']}",
        created_by=created_by,
    )


def record_invoice_entry(
    tenant_id: int,
    ingredient_id: int,
    quantite: float,
    cout_unitaire: float,
    facture_id: int,
    facture_ref: str,
    fournisseur: str,
    unite: Optional[str] = None,
    date_mouvement: Optional[datetime] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enregistre une entrée de stock depuis une facture.
    """
    return create_stock_movement(
        tenant_id=tenant_id,
        ingredient_id=ingredient_id,
        type_mouvement="entree",
        quantite=quantite,
        source="facture",
        unite=unite,
        cout_unitaire=cout_unitaire,
        facture_id=facture_id,
        facture_ref=facture_ref,
        fournisseur=fournisseur,
        date_mouvement=date_mouvement,
        created_by=created_by,
    )


def record_consumption(
    tenant_id: int,
    ingredient_id: int,
    quantite: float,
    commentaire: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enregistre une sortie de stock pour consommation.
    """
    return create_stock_movement(
        tenant_id=tenant_id,
        ingredient_id=ingredient_id,
        type_mouvement="sortie",
        quantite=quantite,
        source="consommation",
        commentaire=commentaire,
        created_by=created_by,
    )


def record_adjustment(
    tenant_id: int,
    ingredient_id: int,
    new_quantity: float,
    commentaire: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ajuste le stock à une nouvelle quantité (inventaire).
    """
    # Récupérer le stock actuel
    sql = text("""
        SELECT stock_actuel FROM restaurant_ingredients
        WHERE id = :ingredient_id AND tenant_id = :tenant_id
    """)
    df = query_df(sql, {"ingredient_id": ingredient_id, "tenant_id": tenant_id})

    if df.empty:
        raise ValueError(f"Ingrédient {ingredient_id} non trouvé")

    current_stock = float(df.iloc[0]["stock_actuel"] or 0)
    delta = new_quantity - current_stock

    if delta == 0:
        return {"id": None, "message": "Stock déjà à jour"}

    return create_stock_movement(
        tenant_id=tenant_id,
        ingredient_id=ingredient_id,
        type_mouvement="ajustement",
        quantite=abs(delta),
        source="inventaire",
        commentaire=commentaire or f"Ajustement inventaire: {current_stock} → {new_quantity}",
        created_by=created_by,
    )


def get_daily_consumption_by_plat(
    tenant_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Agrège les ventes par jour et par plat.
    Retourne le CA (quantité × prix de vente) par plat.
    """
    conditions = ["rs.tenant_id = :tenant_id"]
    params: Dict[str, Any] = {"tenant_id": tenant_id}

    if date_from:
        conditions.append("rs.sold_at >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("rs.sold_at <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            rs.sold_at::date AS jour,
            rp.nom AS plat,
            SUM(rs.quantity) AS quantite_vendue,
            SUM(rs.quantity * COALESCE(rp.prix_vente_ttc, 0)) AS ca_total
        FROM restaurant_sales rs
        JOIN restaurant_plats rp ON rp.id = rs.plat_id
        WHERE {where_clause}
        GROUP BY rs.sold_at::date, rp.nom
        ORDER BY jour, ca_total DESC
    """)

    df = query_df(sql, params)
    if df.empty:
        return {"series": [], "plats": []}

    # Pivoter par CA pour le graphique
    pivot = df.pivot_table(
        index='jour',
        columns='plat',
        values='ca_total',
        aggfunc='sum'
    ).fillna(0)
    pivot = pivot.reset_index()
    pivot['jour'] = pivot['jour'].astype(str)

    # Prendre les top 30 plats par CA total
    plat_totals = df.groupby('plat')['ca_total'].sum().sort_values(ascending=False)
    top_plats = plat_totals.head(30).index.tolist()

    # Filtrer pour ne garder que les top plats + "Autres"
    autres_cols = [col for col in pivot.columns if col != 'jour' and col not in top_plats]
    if autres_cols:
        pivot['Autres'] = pivot[autres_cols].sum(axis=1)
        pivot = pivot.drop(columns=autres_cols)
        top_plats.append('Autres')

    plats = [col for col in pivot.columns if col != 'jour']

    return {
        "series": json.loads(pivot.to_json(orient='records')),
        "plats": plats,
    }


def get_stock_analytics(
    tenant_id: int,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Statistiques de stock sur une période.
    """
    sql = text("""
        WITH period_movements AS (
            SELECT
                type_mouvement,
                source,
                SUM(quantite) AS total_quantite,
                SUM(cout_total) AS total_cout,
                COUNT(*) AS nb_mouvements
            FROM restaurant_stock_movements
            WHERE tenant_id = :tenant_id
              AND date_mouvement >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY type_mouvement, source
        ),
        top_ingredients AS (
            SELECT
                ri.nom,
                SUM(CASE WHEN m.type_mouvement = 'entree' THEN m.quantite ELSE 0 END) AS entrees,
                SUM(CASE WHEN m.type_mouvement = 'sortie' THEN m.quantite ELSE 0 END) AS sorties
            FROM restaurant_stock_movements m
            JOIN restaurant_ingredients ri ON ri.id = m.ingredient_id
            WHERE m.tenant_id = :tenant_id
              AND m.date_mouvement >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY ri.nom
            ORDER BY sorties DESC
            LIMIT 10
        )
        SELECT
            (SELECT json_agg(row_to_json(pm)) FROM period_movements pm) AS par_type,
            (SELECT json_agg(row_to_json(ti)) FROM top_ingredients ti) AS top_consommation
    """)

    df = query_df(sql, {"tenant_id": tenant_id, "days": days})
    if df.empty:
        return {"par_type": [], "top_consommation": []}

    row = df.iloc[0]
    return {
        "par_type": row["par_type"] or [],
        "top_consommation": row["top_consommation"] or [],
        "periode_jours": days,
    }
