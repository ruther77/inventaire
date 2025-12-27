"""
API CRUD pour la gestion des fournisseurs.
Endpoints pour créer, lire, mettre à jour et supprimer des fournisseurs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

from backend.dependencies.security import get_current_user, CurrentUser
from backend.dependencies.database import get_db_pool

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


# ============================================================================
# SCHEMAS
# ============================================================================

class SupplierBase(BaseModel):
    """Schéma de base pour un fournisseur."""
    nom: str = Field(..., min_length=1, max_length=200, description="Nom du fournisseur")
    email: Optional[str] = Field(None, max_length=200)
    telephone: Optional[str] = Field(None, max_length=50)
    adresse: Optional[str] = Field(None, max_length=500)
    contact_nom: Optional[str] = Field(None, max_length=200)
    iban: Optional[str] = Field(None, max_length=50)
    siret: Optional[str] = Field(None, max_length=20)
    delai_paiement: Optional[int] = Field(30, ge=0, le=365, description="Délai de paiement en jours")
    notes: Optional[str] = Field(None, max_length=2000)
    actif: bool = Field(True)


class SupplierCreate(SupplierBase):
    """Schéma pour créer un fournisseur."""
    pass


class SupplierUpdate(BaseModel):
    """Schéma pour mettre à jour un fournisseur."""
    nom: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    telephone: Optional[str] = Field(None, max_length=50)
    adresse: Optional[str] = Field(None, max_length=500)
    contact_nom: Optional[str] = Field(None, max_length=200)
    iban: Optional[str] = Field(None, max_length=50)
    siret: Optional[str] = Field(None, max_length=20)
    delai_paiement: Optional[int] = Field(None, ge=0, le=365)
    notes: Optional[str] = Field(None, max_length=2000)
    actif: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Schéma de réponse pour un fournisseur."""
    id: int
    tenant_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Stats calculées
    total_commandes: Optional[int] = 0
    total_achats: Optional[float] = 0.0
    score: Optional[float] = None


class SupplierListResponse(BaseModel):
    """Réponse paginée de la liste des fournisseurs."""
    suppliers: List[SupplierResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============================================================================
# HELPERS
# ============================================================================

async def ensure_supplier_columns(pool, tenant_id: int):
    """S'assure que les colonnes supplémentaires existent."""
    async with pool.acquire() as conn:
        # Vérifier/ajouter les colonnes manquantes
        columns_to_add = [
            ("email", "TEXT"),
            ("telephone", "TEXT"),
            ("adresse", "TEXT"),
            ("contact_nom", "TEXT"),
            ("delai_paiement", "INTEGER DEFAULT 30"),
            ("notes", "TEXT"),
            ("actif", "BOOLEAN DEFAULT TRUE"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()"),
            ("updated_at", "TIMESTAMPTZ DEFAULT NOW()"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                await conn.execute(f"""
                    ALTER TABLE restaurant_fournisseurs
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                """)
            except Exception:
                pass  # Column might already exist


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=SupplierListResponse)
async def list_suppliers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    actif: Optional[bool] = Query(None),
    sort_by: str = Query("nom", regex="^(nom|created_at|total_achats)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    user: CurrentUser = Depends(get_current_user),
    pool=Depends(get_db_pool),
):
    """Liste paginée des fournisseurs."""
    tenant_id = user.tenant_id
    await ensure_supplier_columns(pool, tenant_id)

    offset = (page - 1) * per_page

    # Construire la requête
    where_clauses = ["f.tenant_id = $1"]
    params = [tenant_id]
    param_idx = 2

    if search:
        where_clauses.append(f"(f.nom ILIKE ${param_idx} OR f.email ILIKE ${param_idx} OR f.contact_nom ILIKE ${param_idx})")
        params.append(f"%{search}%")
        param_idx += 1

    if actif is not None:
        where_clauses.append(f"f.actif = ${param_idx}")
        params.append(actif)
        param_idx += 1

    where_sql = " AND ".join(where_clauses)
    order_sql = f"f.{sort_by} {sort_order.upper()}"
    if sort_by == "total_achats":
        order_sql = f"COALESCE(stats.total_achats, 0) {sort_order.upper()}"

    async with pool.acquire() as conn:
        # Count total
        count_sql = f"SELECT COUNT(*) FROM restaurant_fournisseurs f WHERE {where_sql}"
        total = await conn.fetchval(count_sql, *params)

        # Fetch suppliers with stats
        query = f"""
            SELECT
                f.id, f.tenant_id, f.nom, f.email, f.telephone, f.adresse,
                f.contact_nom, f.iban, f.siret,
                COALESCE(f.delai_paiement, 30) as delai_paiement,
                f.notes, COALESCE(f.actif, true) as actif,
                f.created_at, f.updated_at,
                COALESCE(stats.total_commandes, 0) as total_commandes,
                COALESCE(stats.total_achats, 0) as total_achats,
                scores.overall_score as score
            FROM restaurant_fournisseurs f
            LEFT JOIN (
                SELECT
                    fournisseur_id,
                    COUNT(*) as total_commandes,
                    SUM(montant_ttc) as total_achats
                FROM restaurant_depenses
                WHERE tenant_id = $1
                GROUP BY fournisseur_id
            ) stats ON stats.fournisseur_id = f.id
            LEFT JOIN (
                SELECT DISTINCT ON (supplier_name)
                    supplier_name,
                    overall_score
                FROM supplier_scores
                WHERE tenant_id = $1
                ORDER BY supplier_name, calculation_date DESC
            ) scores ON LOWER(scores.supplier_name) = LOWER(f.nom)
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([per_page, offset])

        rows = await conn.fetch(query, *params)

        suppliers = []
        for row in rows:
            suppliers.append(SupplierResponse(
                id=row["id"],
                tenant_id=row["tenant_id"],
                nom=row["nom"],
                email=row["email"],
                telephone=row["telephone"],
                adresse=row["adresse"],
                contact_nom=row["contact_nom"],
                iban=row["iban"],
                siret=row["siret"],
                delai_paiement=row["delai_paiement"],
                notes=row["notes"],
                actif=row["actif"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                total_commandes=row["total_commandes"] or 0,
                total_achats=float(row["total_achats"] or 0),
                score=float(row["score"]) if row["score"] else None,
            ))

        total_pages = (total + per_page - 1) // per_page

        return SupplierListResponse(
            suppliers=suppliers,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    user: CurrentUser = Depends(get_current_user),
    pool=Depends(get_db_pool),
):
    """Récupère un fournisseur par son ID."""
    tenant_id = user.tenant_id
    await ensure_supplier_columns(pool, tenant_id)

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                f.id, f.tenant_id, f.nom, f.email, f.telephone, f.adresse,
                f.contact_nom, f.iban, f.siret,
                COALESCE(f.delai_paiement, 30) as delai_paiement,
                f.notes, COALESCE(f.actif, true) as actif,
                f.created_at, f.updated_at,
                COALESCE(stats.total_commandes, 0) as total_commandes,
                COALESCE(stats.total_achats, 0) as total_achats,
                scores.overall_score as score
            FROM restaurant_fournisseurs f
            LEFT JOIN (
                SELECT
                    fournisseur_id,
                    COUNT(*) as total_commandes,
                    SUM(montant_ttc) as total_achats
                FROM restaurant_depenses
                WHERE tenant_id = $1
                GROUP BY fournisseur_id
            ) stats ON stats.fournisseur_id = f.id
            LEFT JOIN (
                SELECT DISTINCT ON (supplier_name)
                    supplier_name,
                    overall_score
                FROM supplier_scores
                WHERE tenant_id = $1
                ORDER BY supplier_name, calculation_date DESC
            ) scores ON LOWER(scores.supplier_name) = LOWER(f.nom)
            WHERE f.id = $2 AND f.tenant_id = $1
        """, tenant_id, supplier_id)

        if not row:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")

        return SupplierResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            nom=row["nom"],
            email=row["email"],
            telephone=row["telephone"],
            adresse=row["adresse"],
            contact_nom=row["contact_nom"],
            iban=row["iban"],
            siret=row["siret"],
            delai_paiement=row["delai_paiement"],
            notes=row["notes"],
            actif=row["actif"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            total_commandes=row["total_commandes"] or 0,
            total_achats=float(row["total_achats"] or 0),
            score=float(row["score"]) if row["score"] else None,
        )


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    data: SupplierCreate,
    user: CurrentUser = Depends(get_current_user),
    pool=Depends(get_db_pool),
):
    """Crée un nouveau fournisseur."""
    tenant_id = user.tenant_id
    await ensure_supplier_columns(pool, tenant_id)

    async with pool.acquire() as conn:
        # Vérifier unicité du nom
        existing = await conn.fetchval(
            "SELECT id FROM restaurant_fournisseurs WHERE tenant_id = $1 AND LOWER(nom) = LOWER($2)",
            tenant_id, data.nom
        )
        if existing:
            raise HTTPException(status_code=400, detail="Un fournisseur avec ce nom existe déjà")

        # Insérer
        row = await conn.fetchrow("""
            INSERT INTO restaurant_fournisseurs
            (tenant_id, nom, email, telephone, adresse, contact_nom, iban, siret, delai_paiement, notes, actif, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
            RETURNING id, tenant_id, nom, email, telephone, adresse, contact_nom, iban, siret, delai_paiement, notes, actif, created_at, updated_at
        """, tenant_id, data.nom, data.email, data.telephone, data.adresse,
            data.contact_nom, data.iban, data.siret, data.delai_paiement, data.notes, data.actif)

        return SupplierResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            nom=row["nom"],
            email=row["email"],
            telephone=row["telephone"],
            adresse=row["adresse"],
            contact_nom=row["contact_nom"],
            iban=row["iban"],
            siret=row["siret"],
            delai_paiement=row["delai_paiement"],
            notes=row["notes"],
            actif=row["actif"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            total_commandes=0,
            total_achats=0.0,
            score=None,
        )


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    user: CurrentUser = Depends(get_current_user),
    pool=Depends(get_db_pool),
):
    """Met à jour un fournisseur."""
    tenant_id = user.tenant_id
    await ensure_supplier_columns(pool, tenant_id)

    # Construire les champs à mettre à jour
    updates = {}
    if data.nom is not None:
        updates["nom"] = data.nom
    if data.email is not None:
        updates["email"] = data.email
    if data.telephone is not None:
        updates["telephone"] = data.telephone
    if data.adresse is not None:
        updates["adresse"] = data.adresse
    if data.contact_nom is not None:
        updates["contact_nom"] = data.contact_nom
    if data.iban is not None:
        updates["iban"] = data.iban
    if data.siret is not None:
        updates["siret"] = data.siret
    if data.delai_paiement is not None:
        updates["delai_paiement"] = data.delai_paiement
    if data.notes is not None:
        updates["notes"] = data.notes
    if data.actif is not None:
        updates["actif"] = data.actif

    if not updates:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    async with pool.acquire() as conn:
        # Vérifier existence
        existing = await conn.fetchval(
            "SELECT id FROM restaurant_fournisseurs WHERE id = $1 AND tenant_id = $2",
            supplier_id, tenant_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")

        # Vérifier unicité du nom si changé
        if "nom" in updates:
            duplicate = await conn.fetchval(
                "SELECT id FROM restaurant_fournisseurs WHERE tenant_id = $1 AND LOWER(nom) = LOWER($2) AND id != $3",
                tenant_id, updates["nom"], supplier_id
            )
            if duplicate:
                raise HTTPException(status_code=400, detail="Un fournisseur avec ce nom existe déjà")

        # Construire la requête UPDATE
        set_clauses = [f"{k} = ${i+3}" for i, k in enumerate(updates.keys())]
        set_clauses.append("updated_at = NOW()")
        set_sql = ", ".join(set_clauses)

        params = [supplier_id, tenant_id] + list(updates.values())

        await conn.execute(f"""
            UPDATE restaurant_fournisseurs
            SET {set_sql}
            WHERE id = $1 AND tenant_id = $2
        """, *params)

    # Retourner le fournisseur mis à jour
    return await get_supplier(supplier_id, user, pool)


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: int,
    user: CurrentUser = Depends(get_current_user),
    pool=Depends(get_db_pool),
):
    """Supprime un fournisseur."""
    tenant_id = user.tenant_id

    async with pool.acquire() as conn:
        # Vérifier existence
        existing = await conn.fetchval(
            "SELECT id FROM restaurant_fournisseurs WHERE id = $1 AND tenant_id = $2",
            supplier_id, tenant_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")

        # Vérifier s'il a des dépenses associées
        has_expenses = await conn.fetchval(
            "SELECT 1 FROM restaurant_depenses WHERE fournisseur_id = $1 LIMIT 1",
            supplier_id
        )
        if has_expenses:
            # Soft delete - marquer comme inactif
            await conn.execute(
                "UPDATE restaurant_fournisseurs SET actif = FALSE, updated_at = NOW() WHERE id = $1",
                supplier_id
            )
        else:
            # Hard delete
            await conn.execute(
                "DELETE FROM restaurant_fournisseurs WHERE id = $1 AND tenant_id = $2",
                supplier_id, tenant_id
            )

    return None
