from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.catalog import (
    ProductCreate,
    ProductOut,
    ProductPage,
    ProductUpdate,
)
from backend.services import catalog as catalog_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/catalog", tags=["catalogue"])


@router.get("/products", response_model=ProductPage)
def list_products(
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
    tenant: Tenant = Depends(get_current_tenant),
):
    items, total = catalog_service.list_products_page(
        tenant_id=tenant.id,
        search=search,
        category=category,
        status=status,
        page=page,
        per_page=per_page,
    )
    return {
        "items": items,
        "meta": {"page": page, "per_page": per_page, "total": total},
    }


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
    try:
        return catalog_service.get_product(product_id, tenant_id=tenant.id)
    except catalog_service.ProductNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, tenant: Tenant = Depends(get_current_tenant)):
    record = catalog_service.create_product(
        payload.model_dump(exclude={"codes"}),
        tenant_id=tenant.id,
        codes=payload.codes,
    )
    return record


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, tenant: Tenant = Depends(get_current_tenant)):
    try:
        return catalog_service.update_product(
            product_id,
            payload.model_dump(
                exclude_none=True,
                exclude={"codes"},
            ),
            codes=payload.codes,
            tenant_id=tenant.id,
        )
    except catalog_service.ProductNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
    try:
        catalog_service.delete_product(product_id, tenant_id=tenant.id)
    except catalog_service.ProductNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/products/barcode/{barcode}", response_model=ProductOut)
def get_product_by_barcode(barcode: str, tenant: Tenant = Depends(get_current_tenant)):
    try:
        return catalog_service.get_product_by_barcode(barcode, tenant_id=tenant.id)
    except catalog_service.ProductNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
