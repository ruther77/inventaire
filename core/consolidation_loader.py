"""Helpers to populate the consolidation tables (dim_*, fact_*)."""  # Docstring décrivant le module

from __future__ import annotations  # Active les annotations différées

import datetime as dt  # Alias datetime pour dates/temps
import json  # Sérialisation JSON pour métadonnées
import re  # Expressions régulières pour slugification
import unicodedata  # Normalisation Unicode pour slug
from typing import Iterable  # Typage des itérables

import pandas as pd  # Manipulation de DataFrames
from sqlalchemy import text  # Requêtes SQL textuelles

from core.data_repository import get_engine, query_df  # Utilitaires base de données


def _slugify(value: str, *, fallback: str = "unknown") -> str:
    text_value = (value or "").strip().lower()  # Nettoie et met en minuscules
    if not text_value:  # Si vide
        text_value = fallback  # Utilise le fallback
    normalized = unicodedata.normalize("NFKD", text_value)  # Décompose les accents
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")  # Garde uniquement ASCII
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")  # Remplace les séparateurs par des tirets
    return slug or fallback  # Retourne le slug ou le fallback si vide


def _ensure_dim_date(conn, invoice_date: dt.date) -> int:
    payload = {
        "date_value": invoice_date,
        "year": invoice_date.year,
        "quarter": (invoice_date.month - 1) // 3 + 1,
        "month": invoice_date.month,
        "day": invoice_date.day,
        "week": invoice_date.isocalendar().week,
    }  # Données pour la dimension date
    result = conn.execute(
        text(
            """
            INSERT INTO dim_date (date_value, year, quarter, month, day, week)
            VALUES (:date_value, :year, :quarter, :month, :day, :week)
            ON CONFLICT (date_value) DO UPDATE
            SET year = EXCLUDED.year,
                quarter = EXCLUDED.quarter,
                month = EXCLUDED.month,
                day = EXCLUDED.day,
                week = EXCLUDED.week
            RETURNING id
            """
        ),
        payload,
    )  # Insert ou met à jour la dimension date
    row = result.fetchone()  # Récupère l'ID retourné
    return int(row.id)  # Retourne l'identifiant


def _ensure_dim_tenant(conn, tenant_id: int) -> int:
    tenant_df = query_df(text("SELECT id, code, name FROM tenants WHERE id = :id"), {"id": tenant_id})  # Récupère le tenant
    if tenant_df.empty:  # Si aucun tenant trouvé
        raise ValueError(f"Tenant #{tenant_id} introuvable")  # Erreur explicite
    row = tenant_df.iloc[0]  # Prend la première ligne
    conn.execute(
        text(
            """
            INSERT INTO dim_tenant (id, code, name)
            VALUES (:id, :code, :name)
            ON CONFLICT (id) DO UPDATE SET code = EXCLUDED.code, name = EXCLUDED.name
            """
        ),
        {"id": int(row.id), "code": row.code, "name": row.name},
    )  # Insert ou met à jour le tenant dans la dimension
    return int(row.id)  # Retourne l'identifiant


def _ensure_dim_category(conn, label: str | None) -> int:
    label_value = (label or "Non classé").strip() or "Non classé"  # Valeur nettoyée avec fallback
    code = _slugify(label_value)  # Slug pour la clé
    result = conn.execute(
        text(
            """
            INSERT INTO dim_category (code, label)
            VALUES (:code, :label)
            ON CONFLICT (code) DO UPDATE SET label = EXCLUDED.label
            RETURNING id
            """
        ),
        {"code": code, "label": label_value},
    )  # Upsert de la catégorie
    return int(result.scalar_one())  # Retourne l'identifiant


def _ensure_dim_supplier(conn, supplier_name: str) -> int:
    label = supplier_name.strip() or "Inconnu"  # Nettoie le nom fournisseur
    code = _slugify(label)  # Slug du fournisseur
    result = conn.execute(
        text(
            """
            INSERT INTO dim_supplier (code, name)
            VALUES (:code, :name)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """
        ),
        {"code": code, "name": label},
    )  # Upsert du fournisseur
    return int(result.scalar_one())  # Retourne l'identifiant


def _fetch_product_metadata(conn, product_id: int) -> dict | None:
    row = conn.execute(
        text(
            """
            SELECT p.id, p.nom, p.categorie, pb.code AS barcode
            FROM produits p
            LEFT JOIN produits_barcodes pb ON pb.produit_id = p.id AND pb.is_principal = TRUE
            WHERE p.id = :pid
            LIMIT 1
            """
        ),
        {"pid": int(product_id)},
    ).fetchone()  # Récupère les métadonnées produit
    if not row:  # Aucun résultat
        return None  # Retourne None
    return {
        "id": int(row.id),
        "name": row.nom,
        "category": row.categorie,
        "barcode": row.barcode,
    }  # Dictionnaire des champs utiles


def _ensure_dim_product(conn, product_id: int, *, category_id: int, fallback_name: str | None, barcode: str | None) -> int:
    metadata = _fetch_product_metadata(conn, product_id)  # Métadonnées produit si existant
    name = metadata["name"] if metadata else (fallback_name or f"Produit {product_id}")  # Nom retenu
    category_label = metadata["category"] if metadata else None  # Catégorie du catalogue
    category_fk = category_id if category_id else _ensure_dim_category(conn, category_label)  # FK de catégorie
    sku = metadata["barcode"] or barcode or f"prod-{product_id}"  # SKU/barcode de référence
    conn.execute(
        text(
            """
            INSERT INTO dim_product (id, sku, name, barcode, default_category_id)
            VALUES (:id, :sku, :name, :barcode, :category_id)
            ON CONFLICT (id) DO UPDATE
            SET sku = EXCLUDED.sku,
                name = EXCLUDED.name,
                barcode = EXCLUDED.barcode,
                default_category_id = EXCLUDED.default_category_id
            """
        ),
        {
            "id": int(product_id),
            "sku": sku,
            "name": name,
            "barcode": barcode or metadata.get("barcode") if metadata else barcode,
            "category_id": category_fk,
        },
    )  # Upsert du produit dimensionnel
    return int(product_id)  # Retourne l'ID produit


def _infer_invoice_date(invoice_df: pd.DataFrame, default_date: dt.date | None = None) -> dt.date:
    if "facture_date" in invoice_df.columns:  # Si colonne date disponible
        values = pd.to_datetime(invoice_df["facture_date"], errors="coerce").dropna()  # Parse les dates valides
        if not values.empty:  # Si au moins une date
            return values.iloc[0].date()  # Utilise la première date trouvée
    return default_date or dt.date.today()  # Sinon fallback


def sync_invoice_dataframe(
    invoice_df: pd.DataFrame,
    *,
    tenant_id: int,
    supplier_name: str,
    invoice_reference: str | None = None,
    invoice_date: dt.date | None = None,
) -> dict[str, int]:
    if invoice_df.empty:  # Aucun contenu à traiter
        return {"lines_inserted": 0}  # Retourne un bilan vide

    working_df = invoice_df.copy()  # Copie pour éviter de modifier l'entrée
    invoice_dt = invoice_date or _infer_invoice_date(working_df, dt.date.today())  # Date de facture retenue
    engine = get_engine()  # Moteur SQLAlchemy partagé
    lines_inserted = 0  # Compteur de lignes insérées

    numeric_df = working_df.copy()  # Copie pour manipuler les colonnes numériques

    def _numeric_column(*candidates: str, default: float = 0.0) -> pd.Series:
        for column in candidates:  # Parcourt les colonnes candidates
            if column in numeric_df.columns:  # Si la colonne existe
                series = pd.to_numeric(numeric_df[column], errors="coerce")  # Convertit en numérique
                if not series.isna().all():  # Si au moins une valeur valide
                    return series.fillna(default)  # Retourne la série complétée
        return pd.Series([default] * len(numeric_df))  # Série par défaut si rien trouvé

    quantity_series = _numeric_column("quantite_recue", "qte_init")  # Quantités reçues
    unit_cost_series = _numeric_column("prix_achat", "unit_cost")  # Coût unitaire HT
    vat_series = _numeric_column("tva")  # Taux de TVA

    line_totals_excl = quantity_series * unit_cost_series  # Montant HT par ligne
    line_totals_incl = line_totals_excl * (1 + vat_series / 100)  # Montant TTC par ligne
    total_excl_tax = float(line_totals_excl.sum())  # Total HT
    total_incl_tax = float(line_totals_incl.sum())  # Total TTC
    with engine.begin() as conn:  # Démarre une transaction
        tenant_dim_id = _ensure_dim_tenant(conn, tenant_id)  # Assure la dimension tenant
        date_dim_id = _ensure_dim_date(conn, invoice_dt)  # Assure la dimension date
        supplier_dim_id = _ensure_dim_supplier(conn, supplier_name)  # Assure la dimension fournisseur

        invoice_reference_value = (invoice_reference or "").strip()  # Nettoie la référence fournie
        if not invoice_reference_value:  # Si vide
            invoice_reference_value = f"import-{tenant_dim_id}-{supplier_dim_id}-{invoice_dt.isoformat()}"  # Génère une référence
        doc_payload = {
            "tenant_id": tenant_dim_id,
            "supplier_id": supplier_dim_id,
            "supplier_name": supplier_name.strip() or "Inconnu",
            "invoice_reference": invoice_reference_value,
            "invoice_number": invoice_reference or invoice_reference_value,
            "invoice_date": invoice_dt,
            "total_excl_tax": total_excl_tax,
            "total_incl_tax": total_incl_tax,
            "currency": "EUR",
            "metadata": json.dumps({"line_count": len(working_df)}),
        }  # Charge utile pour le document facture
        document_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO finance_invoice_documents (
                        tenant_id, supplier_id, supplier_name, invoice_reference, invoice_number,
                        invoice_date, total_excl_tax, total_incl_tax, currency, metadata
                    )
                    VALUES (
                        :tenant_id, :supplier_id, :supplier_name, :invoice_reference, :invoice_number,
                        :invoice_date, :total_excl_tax, :total_incl_tax, :currency, CAST(:metadata AS JSONB)
                    )
                    ON CONFLICT (tenant_id, invoice_reference) DO UPDATE SET
                        supplier_id = EXCLUDED.supplier_id,
                        supplier_name = EXCLUDED.supplier_name,
                        invoice_number = EXCLUDED.invoice_number,
                        invoice_date = EXCLUDED.invoice_date,
                        total_excl_tax = EXCLUDED.total_excl_tax,
                        total_incl_tax = EXCLUDED.total_incl_tax,
                        currency = EXCLUDED.currency,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING id
                    """
                ),
                doc_payload,
            ).scalar_one()
        )  # Insert ou update le document facture et récupère son ID

        category_cache: dict[str, int] = {}  # Cache pour éviter les requêtes répétées sur les catégories
        product_cache: dict[int, int] = {}  # Cache pour les produits dimensionnels

        for row in working_df.to_dict("records"):  # Parcourt chaque ligne de facture
            product_id = row.get("produit_id")  # ID produit brut
            if not product_id:  # Si absent
                continue  # Ignore la ligne
            try:
                product_key = int(float(product_id))  # Convertit en entier robuste
            except (TypeError, ValueError):  # Conversion échouée
                continue  # Ignore la ligne

            category_label = row.get("catalogue_categorie") or row.get("categorie")  # Catégorie fournie
            if category_label not in category_cache:  # Si pas encore en cache
                category_cache[category_label or "Non classé"] = _ensure_dim_category(conn, category_label)  # Crée/charge la catégorie
            category_dim_id = category_cache[category_label or "Non classé"]  # Récupère l'ID catégorie

            if product_key not in product_cache:  # Si produit pas encore traité
                product_cache[product_key] = _ensure_dim_product(
                    conn,
                    product_key,
                    category_id=category_dim_id,
                    fallback_name=row.get("nom") or row.get("catalogue_nom"),
                    barcode=row.get("codes"),
                )  # Crée/assure la dimension produit

            fact_payload = {
                "tenant_id": tenant_dim_id,
                "date_id": date_dim_id,
                "supplier_id": supplier_dim_id,
                "document_id": document_id,
                "product_id": product_cache[product_key],
                "category_id": category_dim_id,
                "invoice_number": invoice_reference or row.get("invoice_number") or row.get("numero_facture") or "import",
                "sku": row.get("codes"),
                "quantity": float(row.get("quantite_recue") or row.get("qte_init") or 0),
                "unit_cost": float(row.get("prix_achat") or 0),
                "vat_rate": float(row.get("tva") or 0),
                "currency": "EUR",
            }  # Données de la ligne fact_invoices

            conn.execute(
                text(
                    """
                    INSERT INTO fact_invoices (
                        tenant_id, date_id, supplier_id, document_id, product_id, category_id,
                        invoice_number, sku, quantity, unit_cost_excl_tax, vat_rate, currency
                    )
                    VALUES (
                        :tenant_id, :date_id, :supplier_id, :document_id, :product_id, :category_id,
                        :invoice_number, :sku, :quantity, :unit_cost, :vat_rate, :currency
                    )
                    """
                ),
                fact_payload,
            )  # Insère la ligne factuelle
            lines_inserted += 1  # Incrémente le compteur

    return {"lines_inserted": lines_inserted}  # Retourne le bilan d'insertion


__all__ = ["sync_invoice_dataframe"]  # Exporte la fonction principale
