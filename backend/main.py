"""FastAPI application exposing the inventory features for the new SPA."""

from __future__ import annotations

import base64
from functools import lru_cache
from typing import Iterable, List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from core.data_repository import query_df
from core.inventory_service import process_sale_transaction
from core.product_service import (
    InvalidBarcodeError,
    ProductNotFoundError,
    update_catalog_entry,
)
from backend.dependencies.tenant import Tenant, get_current_tenant

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
from backend.dependencies.auth import optional_api_key
from backend.dependencies.security import enforce_default_rbac


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

    @validator("nom")
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
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

    @validator("barcodes")
    def _clean_barcodes(cls, value: Iterable[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for raw in value:
            text = str(raw or "").strip()
            if text:
                cleaned.append(text)
        return cleaned


def _fetch_products(tenant_id: int) -> list[ProductPayload]:
    """Retourne la projection minimale des produits pour le catalogue SPA."""

    sql = """
        SELECT
            p.id,
            p.nom,
            p.categorie,
            COALESCE(p.prix_vente, 0) AS prix_vente,
            p.prix_achat,
            p.stock_actuel,
            p.tva
        FROM produits p
        WHERE tenant_id = :tenant_id
        ORDER BY p.nom ASC
    """
    df = query_df(sql, params={"tenant_id": tenant_id})
    if df.empty:
        return []
    return [ProductPayload(**record) for record in df.to_dict("records")]


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


@lru_cache
def create_app() -> FastAPI:
    """Construit l'application FastAPI ainsi que tous les routeurs de domaine."""

    app = FastAPI(title="Inventaire Epicerie API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
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
    app.include_router(epicerie_router)

    restaurant_domain_router = APIRouter(tags=['restaurant'], dependencies=_security_dependencies())
    restaurant_domain_router.include_router(restaurant_router.router)
    app.include_router(restaurant_domain_router)

    app.include_router(capital_router.router, dependencies=_security_dependencies())

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/products", response_model=list[ProductPayload], dependencies=_security_dependencies())
    def list_products(tenant: Tenant = Depends(get_current_tenant)) -> list[ProductPayload]:
        return _fetch_products(tenant.id)

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
