"""
Invoice Workflow - Flux unifié d'import de facture.

Ce module centralise le flux complet d'import d'une facture :
1. Extraction des lignes (PDF/texte)
2. Matching avec le catalogue
3. Création/MAJ des produits
4. Enregistrement des mouvements de stock AVEC prix unitaire
5. Historisation des prix
6. Émission des événements pour synchronisation

TOUT est fait dans une transaction unique pour garantir la cohérence.
"""

from __future__ import annotations

import logging
from datetime import datetime, date, time, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df
from core import invoice_extractor, products_loader
from core.inventory_service import match_invoice_products
from core.price_history_service import record_price_history
from core.finance.event_sourcing import (
    EventDispatcher,
    EventType,
    emit_invoice_imported,
    emit_price_updated,
    emit_stock_movement,
)
from core.event_handlers import register_all_handlers

LOGGER = logging.getLogger(__name__)


def _normalize_datetime(value: datetime | date | None) -> datetime | None:
    """Uniformise une date/datetime en datetime timezone-aware (UTC)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _get_product_current_price(product_id: int, tenant_id: int) -> Optional[float]:
    """Récupère le prix d'achat actuel d'un produit."""
    sql = text("""
        SELECT prix_achat FROM produits
        WHERE id = :product_id AND tenant_id = :tenant_id
    """)
    df = query_df(sql, {"product_id": product_id, "tenant_id": tenant_id})
    if df.empty:
        return None
    return float(df.iloc[0].get("prix_achat") or 0)


def _create_stock_movement_with_cost(
    conn,
    tenant_id: int,
    product_id: int,
    quantity: float,
    prix_unitaire_ht: float,
    movement_type: str,
    reference: str,
    username: str,
    movement_date: datetime,
    supplier: str = None,
):
    """Crée un mouvement de stock AVEC le coût unitaire."""
    conn.execute(
        text("""
            INSERT INTO mouvements_stock
            (tenant_id, produit_id, quantite, type_mouvement, reference,
             utilisateur, date_mouvement, fournisseur, prix_unitaire_ht, source)
            VALUES
            (:tenant_id, :produit_id, :quantite, :type_mouvement, :reference,
             :utilisateur, :date_mouvement, :fournisseur, :prix_unitaire_ht, :source)
        """),
        {
            "tenant_id": tenant_id,
            "produit_id": product_id,
            "quantite": quantity,
            "type_mouvement": movement_type,
            "reference": reference,
            "utilisateur": username,
            "date_mouvement": movement_date,
            "fournisseur": supplier,
            "prix_unitaire_ht": prix_unitaire_ht,
            "source": "FACTURE",
        }
    )


def _update_product_stock(conn, tenant_id: int, product_id: int, quantity_delta: float):
    """Met à jour le stock d'un produit."""
    conn.execute(
        text("""
            UPDATE produits
            SET stock_actuel = COALESCE(stock_actuel, 0) + :delta,
                updated_at = NOW()
            WHERE id = :product_id AND tenant_id = :tenant_id
        """),
        {
            "tenant_id": tenant_id,
            "product_id": product_id,
            "delta": quantity_delta,
        }
    )


def _record_price_history_line(
    conn,
    tenant_id: int,
    product_id: int,
    code: str,
    supplier: str,
    prix_achat: float,
    prix_vente: float,
    tva: float,
    invoice_date: datetime,
):
    """Enregistre une entrée dans l'historique des prix."""
    conn.execute(
        text("""
            INSERT INTO produits_price_history
            (tenant_id, produit_id, code, fournisseur, prix_achat, prix_vente, tva, date_facture, created_at)
            VALUES
            (:tenant_id, :produit_id, :code, :fournisseur, :prix_achat, :prix_vente, :tva, :date_facture, NOW())
        """),
        {
            "tenant_id": tenant_id,
            "produit_id": product_id,
            "code": code or "",
            "fournisseur": supplier or "Inconnu",
            "prix_achat": prix_achat,
            "prix_vente": prix_vente,
            "tva": tva,
            "date_facture": invoice_date,
        }
    )


class InvoiceImportResult:
    """Résultat d'un import de facture."""

    def __init__(self):
        self.success = False
        self.invoice_id: Optional[str] = None
        self.supplier: Optional[str] = None
        self.total_lines = 0
        self.products_created = 0
        self.products_updated = 0
        self.movements_created = 0
        self.prices_recorded = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.product_ids: List[int] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "invoice_id": self.invoice_id,
            "supplier": self.supplier,
            "total_lines": self.total_lines,
            "products_created": self.products_created,
            "products_updated": self.products_updated,
            "movements_created": self.movements_created,
            "prices_recorded": self.prices_recorded,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def import_invoice_complete(
    invoice_df: pd.DataFrame,
    *,
    username: str,
    supplier: str = None,
    movement_type: str = "ENTREE",
    invoice_date: datetime | date = None,
    invoice_id: str = None,
    initialize_stock: bool = False,
    tenant_id: int = 1,
    user_id: int = None,
) -> InvoiceImportResult:
    """
    Import complet d'une facture en UNE SEULE TRANSACTION.

    Cette fonction garantit la cohérence des données en faisant :
    1. Création/MAJ des produits (si nouveaux)
    2. Création des mouvements de stock AVEC prix unitaire
    3. Mise à jour des stocks produits
    4. Enregistrement de l'historique des prix
    5. Émission des événements pour synchronisation

    Args:
        invoice_df: DataFrame avec les lignes de facture
        username: Utilisateur effectuant l'import
        supplier: Nom du fournisseur
        movement_type: Type de mouvement (ENTREE/SORTIE)
        invoice_date: Date de la facture
        invoice_id: Identifiant de la facture
        initialize_stock: Si True, initialise le stock au lieu d'ajouter
        tenant_id: ID du tenant
        user_id: ID de l'utilisateur (pour événements)

    Returns:
        InvoiceImportResult avec le résumé de l'import
    """
    # Enregistre les handlers si pas déjà fait
    register_all_handlers()

    result = InvoiceImportResult()
    result.invoice_id = invoice_id
    result.supplier = supplier

    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:
        result.errors.append("DataFrame vide ou invalide")
        return result

    result.total_lines = len(invoice_df)
    normalized_date = _normalize_datetime(invoice_date) or datetime.now(timezone.utc)
    supplier_label = (supplier or "Inconnu").strip() or "Inconnu"

    # Quantité selon le type de mouvement
    qty_multiplier = 1 if movement_type == "ENTREE" else -1

    engine = get_engine()

    try:
        with engine.begin() as conn:
            # Étape 1: Enrichir les lignes avec le catalogue
            working_df = invoice_df.copy()

            # Matching avec le catalogue existant
            if "codes" in working_df.columns:
                working_df["_code_lower"] = working_df["codes"].fillna("").astype(str).str.lower().str.strip()
                matches_df = match_invoice_products(working_df, tenant_id=tenant_id)

                if not matches_df.empty:
                    matches_df = matches_df.rename(columns={
                        "code": "_code_lower",
                        "produit_id": "catalogue_id",
                    })
                    working_df = working_df.merge(matches_df[["_code_lower", "catalogue_id"]], on="_code_lower", how="left")

                    if "produit_id" not in working_df.columns:
                        working_df["produit_id"] = working_df["catalogue_id"]
                    else:
                        working_df["produit_id"] = working_df["produit_id"].fillna(working_df["catalogue_id"])

            # Étape 2: Créer les produits manquants
            for idx, row in working_df.iterrows():
                product_id = row.get("produit_id")
                code = str(row.get("codes") or "").strip()
                nom = str(row.get("nom") or "").strip()
                prix_achat = float(row.get("prix_achat") or row.get("prix_ht") or 0)
                prix_vente = float(row.get("prix_vente") or 0)
                tva = float(row.get("tva") or 0)
                quantite = float(row.get("quantite_recue") or row.get("qte_init") or row.get("quantite") or 0)

                if not nom:
                    result.warnings.append(f"Ligne {idx}: nom manquant, ignorée")
                    continue

                # Créer le produit si inexistant
                if pd.isna(product_id) or product_id is None:
                    # Vérifie si produit existe par nom
                    check_sql = text("""
                        SELECT id FROM produits
                        WHERE tenant_id = :tenant_id AND LOWER(nom) = LOWER(:nom)
                        LIMIT 1
                    """)
                    existing = conn.execute(check_sql, {"tenant_id": tenant_id, "nom": nom}).fetchone()

                    if existing:
                        product_id = existing[0]
                        result.products_updated += 1
                    else:
                        # Créer le produit
                        insert_sql = text("""
                            INSERT INTO produits
                            (tenant_id, nom, prix_achat, prix_vente, tva, stock_actuel, actif, created_at, updated_at)
                            VALUES
                            (:tenant_id, :nom, :prix_achat, :prix_vente, :tva, :stock, TRUE, NOW(), NOW())
                            RETURNING id
                        """)
                        new_product = conn.execute(insert_sql, {
                            "tenant_id": tenant_id,
                            "nom": nom,
                            "prix_achat": prix_achat,
                            "prix_vente": prix_vente,
                            "tva": tva,
                            "stock": quantite if initialize_stock else 0,
                        }).fetchone()

                        product_id = new_product[0]
                        result.products_created += 1

                        # Ajouter le code-barres si présent
                        if code:
                            conn.execute(
                                text("""
                                    INSERT INTO produits_barcodes (produit_id, code, tenant_id, is_principal)
                                    VALUES (:produit_id, :code, :tenant_id, TRUE)
                                    ON CONFLICT (tenant_id, code) DO NOTHING
                                """),
                                {"produit_id": product_id, "code": code, "tenant_id": tenant_id}
                            )

                    working_df.at[idx, "produit_id"] = product_id

                product_id = int(product_id)
                result.product_ids.append(product_id)

                # Récupérer l'ancien prix pour détecter les variations
                old_price = _get_product_current_price(product_id, tenant_id)

                # Étape 3: Créer le mouvement de stock AVEC prix unitaire
                if quantite > 0:
                    reference = f"FACT-{invoice_id or 'IMPORT'}-{idx}"

                    _create_stock_movement_with_cost(
                        conn,
                        tenant_id=tenant_id,
                        product_id=product_id,
                        quantity=quantite * qty_multiplier,
                        prix_unitaire_ht=prix_achat,
                        movement_type=movement_type,
                        reference=reference,
                        username=username,
                        movement_date=normalized_date,
                        supplier=supplier_label,
                    )
                    result.movements_created += 1

                    # Mise à jour du stock (sauf si initialize_stock car déjà fait)
                    if not initialize_stock:
                        _update_product_stock(conn, tenant_id, product_id, quantite * qty_multiplier)

                # Étape 4: Enregistrer l'historique des prix
                if prix_achat > 0:
                    _record_price_history_line(
                        conn,
                        tenant_id=tenant_id,
                        product_id=product_id,
                        code=code,
                        supplier=supplier_label,
                        prix_achat=prix_achat,
                        prix_vente=prix_vente,
                        tva=tva,
                        invoice_date=normalized_date,
                    )
                    result.prices_recorded += 1

                    # Mettre à jour le prix du produit
                    conn.execute(
                        text("""
                            UPDATE produits
                            SET prix_achat = :prix_achat,
                                updated_at = NOW()
                            WHERE id = :product_id AND tenant_id = :tenant_id
                        """),
                        {"prix_achat": prix_achat, "product_id": product_id, "tenant_id": tenant_id}
                    )

                    # Émettre événement PRICE_UPDATED si variation significative
                    if old_price and old_price > 0 and abs(prix_achat - old_price) / old_price > 0.01:
                        emit_price_updated(
                            tenant_id=tenant_id,
                            product_id=product_id,
                            old_price=old_price,
                            new_price=prix_achat,
                            supplier=supplier_label,
                            source="invoice_import",
                            user_id=user_id,
                        )

                # Émettre événement STOCK_MOVEMENT
                if quantite > 0:
                    emit_stock_movement(
                        tenant_id=tenant_id,
                        product_id=product_id,
                        movement_type="in" if movement_type == "ENTREE" else "out",
                        quantity=quantite,
                        reason=f"Import facture {invoice_id or 'N/A'}",
                        reference=invoice_id,
                        user_id=user_id,
                    )

            # Enregistrer la facture dans processed_invoices
            if invoice_id:
                conn.execute(
                    text("""
                        INSERT INTO processed_invoices
                        (tenant_id, invoice_id, supplier, facture_date, line_count, created_at)
                        VALUES (:tenant_id, :invoice_id, :supplier, :facture_date, :line_count, NOW())
                        ON CONFLICT (tenant_id, invoice_id) DO UPDATE SET
                            supplier = EXCLUDED.supplier,
                            line_count = EXCLUDED.line_count,
                            updated_at = NOW()
                    """),
                    {
                        "tenant_id": tenant_id,
                        "invoice_id": invoice_id,
                        "supplier": supplier_label,
                        "facture_date": normalized_date,
                        "line_count": result.total_lines,
                    }
                )

        # Transaction committée - émettre l'événement global
        emit_invoice_imported(
            tenant_id=tenant_id,
            invoice_id=invoice_id or "IMPORT",
            filename=invoice_id or "import_manuel",
            supplier=supplier_label,
            total=sum(float(row.get("total_ttc") or row.get("prix_achat") or 0) for _, row in working_df.iterrows()),
            items_count=result.total_lines,
            user_id=user_id,
        )

        result.success = True
        LOGGER.info(
            "✅ Import facture réussi: %s lignes, %s produits créés, %s mouvements, %s prix historisés",
            result.total_lines, result.products_created, result.movements_created, result.prices_recorded
        )

    except Exception as e:
        LOGGER.error("❌ Erreur import facture: %s", e)
        result.errors.append(str(e))
        result.success = False

    return result


def get_invoice_workflow_summary(tenant_id: int, days: int = 30) -> Dict[str, Any]:
    """Retourne un résumé des imports de factures récents."""
    sql = text("""
        SELECT
            COUNT(*) as total_invoices,
            SUM(line_count) as total_lines,
            COUNT(DISTINCT supplier) as unique_suppliers
        FROM processed_invoices
        WHERE tenant_id = :tenant_id
          AND created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
    """)
    df = query_df(sql, {"tenant_id": tenant_id, "days": days})

    if df.empty:
        return {"total_invoices": 0, "total_lines": 0, "unique_suppliers": 0}

    return df.iloc[0].to_dict()
