"""
Module principal de l'application FastAPI.

Ce module configure et initialise l'application complète incluant:

Architecture:
- API REST modulaire avec routeurs séparés par domaine
- Support multi-tenant avec isolation des données
- Authentification JWT avec cookies httpOnly
- Middleware avancés (CORS, performance, contexte, idempotence)
- Cache Redis pour optimisation des requêtes
- Event sourcing pour synchronisation des données

Modules principaux:
1. Operations: Catalogue, stock, factures, approvisionnement
2. Restaurant: Plats, ingrédients, marges restauration
3. Finance: Trésorerie, relevés bancaires, rapprochement
4. Intelligence: Prévisions, anomalies, scoring fournisseurs
5. Cockpit: Vue consolidée avec KPIs
6. Admin: Administration système et sauvegardes

Sécurité:
- Validation stricte des origines CORS en production
- Secrets JWT configurables via env vars
- Rate limiting sur endpoints sensibles
- RBAC (Role-Based Access Control) par endpoint
- Headers de sécurité (HSTS, CSP, etc.)

Monitoring:
- Métriques de performance par endpoint
- Statistiques cache Redis
- Logging structuré avec request IDs
- Server-Timing headers pour debugging
"""

from __future__ import annotations

import base64
import os
from functools import lru_cache
from typing import Iterable, List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from backend.middleware import (
    RequestContextMiddleware,
    PerformanceMiddleware,
    ResponseWrapperMiddleware,
    IdempotencyMiddleware,
    get_performance_stats,
)
from backend.cache import get_redis_client, CacheManager, CacheTTL

from core.data_repository import query_df
from core.catalog_sql_repository import CatalogSqlRepository
from core.inventory_service import process_sale_transaction
from core.product_service import (
    InvalidBarcodeError,
    ProductNotFoundError,
    update_catalog_entry,
)
from backend.dependencies.tenant import Tenant, bootstrap_tenants_if_enabled, get_current_tenant

from backend.api import auth as auth_router
from backend.api import catalog as catalog_router
from backend.api import supply as supply_router
from backend.api import audit as audit_router
from backend.api import invoices as invoices_router
from backend.api import stock as stock_router
from backend.api import dashboard as dashboard_router
from backend.api import prices as prices_router
from backend.api import maintenance as maintenance_router
from backend.api import finance as finance_router
from backend.api import reports as reports_router
from backend.api import admin as admin_router
from backend.api import restaurant as restaurant_router
from backend.api import capital as capital_router
from backend.api import analytics as analytics_router
from backend.api import eurociel as eurociel_router
# Modules Finance avancés
from backend.api import inventory_intelligence as inventory_intelligence_router
from backend.api import forecasting as forecasting_router
from backend.api import audit_trail as audit_trail_router
from backend.api import anomaly_detection as anomaly_detection_router
from backend.api import margins as margins_router
from backend.api import data_quality as data_quality_router
from backend.api import bank_reconciliation as bank_reconciliation_router
from backend.api import rules_engine as rules_engine_router
from backend.api import supplier_scoring as supplier_scoring_router
from backend.api import cockpit as cockpit_router
from backend.api import newcms as newcms_router
from backend.dependencies.auth import optional_api_key
from backend.dependencies.security import enforce_default_rbac
from backend.settings import Settings
from core.user_service import bootstrap_users_if_enabled
from core.products_loader import ensure_barcode_constraints


class ProductPayload(BaseModel):
    """Projection légère d'un produit pour la SPA."""

    id: int
    nom: str
    categorie: str | None = None
    prix_vente: float = Field(..., ge=0)
    prix_achat: float | None = Field(default=None, ge=0)
    stock_actuel: float | None = Field(default=None, ge=0)
    tva: float | None = Field(default=None, ge=0)


class POSCartLine(BaseModel):
    id: int = Field(..., description="Identifiant du produit")
    qty: float = Field(..., gt=0, description="Quantité vendue")
    nom: str | None = Field(default=None, description="Nom affiché dans le ticket")
    prix_vente: float | None = Field(default=None, ge=0)
    tva: float | None = Field(default=None, ge=0)

    @field_validator("nom", mode="before")
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class CheckoutRequest(BaseModel):
    cart: List[POSCartLine]
    username: str | None = Field(default=None, description="Utilisateur effectuant la vente")


class CheckoutResponse(BaseModel):
    success: bool
    message: str | None = None
    receipt_filename: str | None = None
    receipt_base64: str | None = None


class ProductUpdateRequest(BaseModel):
    nom: str | None = None
    categorie: str | None = None
    prix_vente: float | None = Field(default=None, ge=0)
    prix_achat: float | None = Field(default=None, ge=0)
    tva: float | None = Field(default=None, ge=0)
    actif: bool | None = None
    seuil_alerte: float | None = Field(default=None, ge=0)
    barcodes: List[str] | None = Field(default=None, description="Codes-barres associés")

    @field_validator("barcodes", mode="before")
    def _clean_barcodes(cls, value: Iterable[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for raw in value:
            text = str(raw or "").strip()
            if text:
                cleaned.append(text)
        return cleaned


def _fetch_products_repo(tenant_id: int) -> list[ProductPayload]:
    """Retourne la projection minimale des produits pour le catalogue SPA."""

    repo = CatalogSqlRepository()
    return [ProductPayload(**product.__dict__) for product in repo.list_active_products(tenant_id)]


def _compute_inventory_value(tenant_id: int) -> dict[str, float]:
    """Calcule la valorisation achat/vente du stock courant."""

    sql = """
        SELECT
            SUM(COALESCE(prix_achat, 0) * COALESCE(stock_actuel, 0)) AS total_achat,
            SUM(COALESCE(prix_vente, 0) * COALESCE(stock_actuel, 0)) AS total_vente
        FROM produits
        WHERE tenant_id = :tenant_id
    """
    df = query_df(sql, params={"tenant_id": tenant_id})
    if df.empty:
        return {"total_purchase_value": 0.0, "total_sale_value": 0.0}
    row = df.iloc[0]
    return {
        "total_purchase_value": float(row.get("total_achat") or 0),
        "total_sale_value": float(row.get("total_vente") or 0),
    }


def _is_production_env() -> bool:
    """Vérifie si l'application tourne dans un environnement de production."""
    env = (os.getenv("APP_ENV") or os.getenv("ENV") or "development").lower()
    return env in {"prod", "production", "staging"}


def _load_allowed_origins() -> list[str]:
    """Charge les origines CORS autorisées avec contrôle strict en production.

    En production :
    - CORS_ALLOWED_ORIGINS doit être défini explicitement
    - Lève une RuntimeError si non configuré
    - Le wildcard (*) est refusé

    En développement :
    - Repli sur les ports localhost courants si aucune valeur n'est fournie
    """
    raw_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    is_prod = _is_production_env()

    if not raw_origins:
        if is_prod:
            raise RuntimeError(
                "CORS_ALLOWED_ORIGINS doit etre configure en production. "
                "Exemple: CORS_ALLOWED_ORIGINS=https://mondomaine.com,https://app.mondomaine.com"
            )
        # Repli en développement : serveurs Vite/React (ports usuels)
        import logging
        logging.getLogger(__name__).warning(
            "CORS_ALLOWED_ORIGINS non defini, utilisation des valeurs dev par defaut"
        )
        return [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:3000",
            "http://localhost:8501",
        ]

    parsed: list[str] = []
    for entry in raw_origins.split(","):
        cleaned = entry.strip()
        if cleaned:
            # Refuser le wildcard en production
            if cleaned == "*" and is_prod:
                raise RuntimeError(
                    "Wildcard CORS (*) interdit en production. "
                    "Specifiez les origines explicitement."
                )
            parsed.append(cleaned)

    if not parsed:
        if is_prod:
            raise RuntimeError("CORS_ALLOWED_ORIGINS est vide en production.")
        return ["http://localhost:5173"]

    return parsed


@lru_cache
def create_app() -> FastAPI:
    """
    Factory pour créer et configurer l'application FastAPI complète.

    Cette fonction:
    1. Configure les métadonnées OpenAPI (titre, version, description)
    2. Initialise les tables système (tenants, users)
    3. Configure CORS avec validation stricte en production
    4. Ajoute les middlewares de sécurité et performance
    5. Enregistre tous les routeurs par domaine métier
    6. Configure les event handlers pour synchronisation
    7. Initialise le pool Redis pour le cache

    Le résultat est caché (lru_cache) pour éviter les reconfigurations.

    Returns:
        Instance FastAPI configurée et prête à démarrer

    Security Notes:
        - En production, CORS_ALLOWED_ORIGINS DOIT être configuré
        - Wildcard (*) CORS est interdit en production
        - JWT_SECRET_KEY doit être robuste (>32 caractères)

    Example:
        >>> app = create_app()
        >>> # Lancer avec: uvicorn backend.main:app --reload
    """

    app = FastAPI(
        title="Inventaire Epicerie API",
        version="1.0.0",
        description="""
## API de gestion d'inventaire pour Epicerie et Restaurant

Cette API permet de gerer:
- **Catalogue produits** : CRUD produits, codes-barres, categories
- **Stock** : Mouvements d'entree/sortie, alertes de seuil
- **Factures** : Import et extraction de factures PDF
- **Restaurant** : Gestion des plats, ingredients, marges
- **Finance** : Releves bancaires, tresorerie, rapprochement
- **Rapports** : Analytics et tableaux de bord

### Authentification
L'API utilise OAuth2 avec JWT tokens. Obtenez un token via `/auth/token`.

### Multi-tenant
Chaque requete est filtree par tenant_id pour isoler les donnees.
        """,
        openapi_tags=[
            # === Auth ===
            {"name": "auth", "description": "Authentification et gestion des tokens"},
            # === Operations (Catalogue, Stock, Factures) ===
            {"name": "operations", "description": "Operations quotidiennes: catalogue, stock, factures, approvisionnement"},
            {"name": "restaurant", "description": "Module restaurant: plats, ingredients, marges restauration"},
            # === Finance (Tresorerie, Comptabilite) ===
            {"name": "finance", "description": "Tresorerie, releves bancaires, rapprochement, regles de categorisation"},
            # === Intelligence (Previsions, Optimisation) ===
            {"name": "intelligence", "description": "Intelligence business: previsions, optimisation stock, anomalies, scoring fournisseurs"},
            # === Cockpit (Vue consolidee) ===
            {"name": "cockpit", "description": "Vue consolidee unifiee avec KPIs et alertes"},
            # === Admin ===
            {"name": "admin", "description": "Administration et configuration systeme"},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
    )

    settings = Settings.load()

    # Initialise la table tenants sans bloquer en prod si la DB est indisponible.
    bootstrap_tenants_if_enabled()
    bootstrap_users_if_enabled()
    ensure_barcode_constraints()

    # Enregistre les event handlers pour synchroniser les entités
    try:
        from core.event_handlers import register_all_handlers
        register_all_handlers()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Event handlers non enregistrés: %s", e)

    allowed_origins = settings.cors_allowed_origins or _load_allowed_origins()
    is_prod = _is_production_env()

    # En production, appliquer des réglages CORS plus stricts
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,  # Requis pour les cookies httpOnly
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"] if is_prod else ["*"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"] if is_prod else ["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
        max_age=86400 if is_prod else 600,  # Cache preflight : 24h en prod, 10min en dev
    )

    # Middleware UX avancés (ordre inverse d'exécution)
    # ResponseWrapper doit être ajouté en premier pour wrapper la réponse finale
    app.add_middleware(
        ResponseWrapperMiddleware,
        exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/metrics"],
        wrap_errors_only=False,  # Wrapper toutes les réponses, pas seulement les erreurs
    )
    app.add_middleware(IdempotencyMiddleware)  # Clés d'idempotence pour sécuriser les retries
    app.add_middleware(PerformanceMiddleware)  # Suivi des performances
    app.add_middleware(RequestContextMiddleware)  # ID de requête et contexte

    # Initialiser le cache Redis au démarrage
    @app.on_event("startup")
    async def startup_event():
        """Initialise le pool de connexions Redis au démarrage."""
        redis_client = get_redis_client()
        if redis_client:
            import logging
            logging.getLogger(__name__).info("Redis cache connected successfully")
        else:
            import logging
            logging.getLogger(__name__).warning("Redis not available - caching disabled")

    def _security_dependencies() -> list[Depends]:
        # Force l'authentification + le rôle par défaut sur l'ensemble des routes métier.
        return [Depends(optional_api_key), Depends(enforce_default_rbac)]

    app.include_router(auth_router.router)

    # =========================================================================
    # OPERATIONS - Catalogue, Stock, Factures, Approvisionnement
    # =========================================================================
    operations_router = APIRouter(tags=['operations'], dependencies=_security_dependencies())
    operations_router.include_router(catalog_router.router)       # /catalog/*
    operations_router.include_router(supply_router.router)        # /supply/*
    operations_router.include_router(stock_router.router)         # /stock/*
    operations_router.include_router(invoices_router.router)      # /invoices/*
    operations_router.include_router(prices_router.router)        # /prices/*
    operations_router.include_router(audit_router.router)         # /audit/*
    # Dashboard démo ouvert (sans dépendances d'auth)
    app.include_router(dashboard_router.router, tags=['dashboard'])
    operations_router.include_router(reports_router.router)       # /reports/*
    operations_router.include_router(maintenance_router.router)   # /maintenance/*
    operations_router.include_router(eurociel_router.router)      # /eurociel/*
    operations_router.include_router(data_quality_router.router)  # /data-quality/*
    app.include_router(operations_router)

    # =========================================================================
    # RESTAURANT - Module restaurant
    # (Sans dépendances d'auth globales - gérées au niveau des endpoints)
    # =========================================================================
    app.include_router(restaurant_router.router, tags=['restaurant'])

    # =========================================================================
    # FINANCE - Tresorerie, Comptabilite, Rapprochement
    # (Sans dépendances d'auth globales - gérées au niveau des endpoints)
    # =========================================================================
    app.include_router(finance_router.router, tags=['finance'])
    app.include_router(bank_reconciliation_router.router, tags=['finance'])
    app.include_router(rules_engine_router.router, tags=['finance'])
    app.include_router(audit_trail_router.router, tags=['finance'])
    app.include_router(capital_router.router, tags=['finance'])
    app.include_router(analytics_router.router, tags=['finance'])

    # =========================================================================
    # INTELLIGENCE - Previsions, Optimisation, Scoring
    # =========================================================================
    intelligence_router = APIRouter(tags=['intelligence'], dependencies=_security_dependencies())
    intelligence_router.include_router(inventory_intelligence_router.router)  # /inventory-intelligence/*
    intelligence_router.include_router(forecasting_router.router)             # /forecasting/*
    intelligence_router.include_router(anomaly_detection_router.router)       # /anomaly-detection/*
    intelligence_router.include_router(margins_router.router)                 # /margins/*
    app.include_router(intelligence_router)

    # =========================================================================
    # COCKPIT - Vue consolidee unifiee
    # =========================================================================
    app.include_router(cockpit_router.router, tags=['cockpit'], dependencies=_security_dependencies())

    # =========================================================================
    # newCMS Demo (sans dépendances d'auth pour facilités de test/démo)
    # =========================================================================
    app.include_router(newcms_router.router, tags=['newcms'])

    # Supplier scoring (ouvert pour démos et tests front)
    app.include_router(supplier_scoring_router.router, tags=['supplier-scoring'])

    # =========================================================================
    # ADMIN - Administration systeme
    # =========================================================================
    app.include_router(admin_router.router, tags=['admin'], dependencies=_security_dependencies())

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics/performance", dependencies=_security_dependencies())
    def performance_metrics():
        """Retourne les statistiques de performance des endpoints."""
        return get_performance_stats()

    @app.get("/metrics/cache", dependencies=_security_dependencies())
    def cache_metrics():
        """Retourne les statistiques du cache Redis."""
        redis_client = get_redis_client()
        if redis_client is None:
            return {"status": "disconnected", "message": "Redis not available"}
        try:
            info = redis_client.info("memory")
            return {
                "status": "connected",
                "memory_used": info.get("used_memory_human"),
                "memory_peak": info.get("used_memory_peak_human"),
                "keys_count": redis_client.dbsize(),
                "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.post("/cache/invalidate/{pattern}", dependencies=_security_dependencies())
    def invalidate_cache(pattern: str, tenant: Tenant = Depends(get_current_tenant)):
        """Invalide les entrées de cache correspondant au pattern."""
        cache = CacheManager(prefix=pattern)
        count = cache.invalidate_tenant(tenant.id)
        return {"status": "ok", "invalidated": count}

    # Ajout : petit tuto/lexique VSCode (lettres Git U/M et points/icônes)
    @app.get("/vscode/tuto")
    def vscode_tuto() -> dict[str, str]:
        return {
            "titre": "Tuto VSCode — lettres Git et points",
            "résumé": "Significations rapides pour le panneau Source Control et les icônes d'onglet.",
            "U": "Untracked — fichier non suivi par Git. Utilisez 'git add' pour le suivre.",
            "M": "Modified — fichier existant modifié. Stagez ('git add') puis 'git commit'.",
            "points": "Point rempli (●) sur l'onglet = modifications non sauvegardées. Dans l'explorateur, les décorations (lettres/icônes) indiquent l'état Git : U (untracked), M (modified), A (added), D (deleted), R (renamed).",
            "actions_vs_code": "Ouvrir Source Control (Ctrl+Shift+G) → cliquer sur + pour staged files → saisir message → ✓ pour commit.",
            "exemple_cli": "git add <fichier> && git commit -m 'message' && git push"
        }

    @app.get("/products", response_model=list[ProductPayload], dependencies=_security_dependencies())
    def list_products(tenant: Tenant = Depends(get_current_tenant)) -> list[ProductPayload]:
        return _fetch_products_repo(tenant.id)

    @app.get("/inventory/summary", dependencies=_security_dependencies())
    def inventory_summary(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, float]:
        return _compute_inventory_value(tenant.id)

    @app.post("/pos/checkout", response_model=CheckoutResponse, dependencies=_security_dependencies())
    def checkout(payload: CheckoutRequest, tenant: Tenant = Depends(get_current_tenant)) -> CheckoutResponse:
        success, message, receipt = process_sale_transaction(
            [item.dict() for item in payload.cart],
            payload.username or "api_user",
            tenant_id=tenant.id,
        )

        if not success:
            return CheckoutResponse(success=False, message=message)

        receipt_filename = None
        receipt_base64 = None
        if receipt:
            receipt_filename = receipt.get("filename")
            raw_content = receipt.get("content")
            if isinstance(raw_content, bytes):
                # L'encodage Base64 permet de renvoyer le ticket directement dans la réponse JSON.
                receipt_base64 = base64.b64encode(raw_content).decode("ascii")

        return CheckoutResponse(
            success=True,
            message=message,
            receipt_filename=receipt_filename,
            receipt_base64=receipt_base64,
        )

    @app.patch("/products/{product_id}", dependencies=_security_dependencies())
    def update_product(
        product_id: int,
        payload: ProductUpdateRequest,
        tenant: Tenant = Depends(get_current_tenant),
    ) -> dict[str, object]:
        try:
            result = update_catalog_entry(
                product_id,
                {
                    key: value
                    for key, value in payload.dict(exclude={"barcodes"}).items()
                    if value is not None
                },
                payload.barcodes,
                tenant_id=tenant.id,
            )
        except ProductNotFoundError as exc:  # pragma: no cover - cas defensif
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except InvalidBarcodeError as exc:  # pragma: no cover - cas defensif
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return {"status": "updated", "result": result}

    return app


app = create_app()
