"""FastAPI application exposing the inventory features for the new SPA."""

from __future__ import annotations

import base64
import os
from functools import lru_cache
from typing import Iterable, List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

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
from backend.dependencies.auth import optional_api_key
from backend.dependencies.security import enforce_default_rbac
from backend.settings import Settings
from core.user_service import bootstrap_users_if_enabled
from core.products_loader import ensure_barcode_constraints


class ProductPayload(BaseModel):
    """Lightweight projection of a product for the SPA."""

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


def _load_allowed_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if not raw_origins:
        # Vite/React dev server par défaut (ports fréquents + front docker)
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
            parsed.append(cleaned)
    # Allow explicit wildcard only if set
    return parsed or ["http://localhost:5173"]


@lru_cache
def create_app() -> FastAPI:
    """Construit l'application FastAPI ainsi que tous les routeurs de domaine."""

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
            {"name": "auth", "description": "Authentification et gestion des tokens"},
            {"name": "epicerie", "description": "Gestion du catalogue et stock epicerie"},
            {"name": "restaurant", "description": "Module restaurant (plats, ingredients, marges)"},
            {"name": "finance", "description": "Tresorerie et releves bancaires"},
            {"name": "admin", "description": "Administration et configuration"},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
    )

    settings = Settings.load()

    # Initialise la table tenants sans bloquer en prod si la DB est indisponible.
    bootstrap_tenants_if_enabled()
    bootstrap_users_if_enabled()
    ensure_barcode_constraints()

    allowed_origins = settings.cors_allowed_origins or _load_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials="*" not in allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _security_dependencies() -> list[Depends]:
        # Force l'authentification + le rôle par défaut sur l'ensemble des routes métier.
        return [Depends(optional_api_key), Depends(enforce_default_rbac)]

    app.include_router(auth_router.router)

    epicerie_router = APIRouter(tags=['epicerie'], dependencies=_security_dependencies())
    epicerie_router.include_router(catalog_router.router)
    epicerie_router.include_router(supply_router.router)
    epicerie_router.include_router(audit_router.router)
    epicerie_router.include_router(invoices_router.router)
    epicerie_router.include_router(stock_router.router)
    epicerie_router.include_router(dashboard_router.router)
    epicerie_router.include_router(prices_router.router)
    epicerie_router.include_router(maintenance_router.router)
    epicerie_router.include_router(reports_router.router)
    epicerie_router.include_router(admin_router.router)
    epicerie_router.include_router(finance_router.router)
    epicerie_router.include_router(analytics_router.router)
    app.include_router(epicerie_router)

    restaurant_domain_router = APIRouter(tags=['restaurant'], dependencies=_security_dependencies())
    restaurant_domain_router.include_router(restaurant_router.router)
    app.include_router(restaurant_domain_router)

    app.include_router(capital_router.router, dependencies=_security_dependencies())

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

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
        except ProductNotFoundError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except InvalidBarcodeError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return {"status": "updated", "result": result}

    return app


app = create_app()
