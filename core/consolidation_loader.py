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
    text_value = str(value or "").strip().lower()  # Nettoie et met en minuscules
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
    conn.execute(
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
            """
        ),
        payload,
    )  # Upsert sans RETURNING
    return int(invoice_date.strftime("%Y%m%d"))  # Utilise la date comme identifiant stable


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
    label_value = str(label or "Non classé").strip() or "Non classé"  # Valeur nettoyée avec fallback
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
    label = str(supplier_name or "").strip() or "Inconnu"  # Nettoie le nom fournisseur
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


def _ensure_dim_product(
    conn,
    product_id: int | None,
    *,
    category_id: int,
    fallback_name: str | None,
    barcode: str | None,
    tenant_id: int,
) -> int:
    """Assure un produit dimensionnel, avec fallback si produit_id absent."""
    # Fallback: si pas d'ID catalogue, on génère un ID stable basé sur le libellé/code
    if product_id is None:
        raw_key = str(fallback_name or barcode or "inconnu").strip() or "inconnu"
        product_key = abs(hash((tenant_id, raw_key))) % (10**12)
    else:
        product_key = int(product_id)

    metadata = _fetch_product_metadata(conn, product_key) if product_id else None
    name = metadata["name"] if metadata else (fallback_name or f"Produit {product_key}")
    category_label = metadata["category"] if metadata else None
    category_fk = category_id if category_id else _ensure_dim_category(conn, category_label)
    sku = metadata["barcode"] if metadata else (barcode or f"prod-{product_key}")

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
            "id": int(product_key),
            "sku": sku,
            "name": name,
            "barcode": sku,
            "category_id": category_fk,
        },
    )
    return int(product_key)


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
    analyze: bool = True,
    group_by_invoice_id: bool = True,
    _skip_grouping: bool = False,
) -> dict[str, int]:
    """Synchronise un DataFrame de facture vers les tables dimensionnelles.

    Args:
        invoice_df: DataFrame contenant les lignes de facture
        tenant_id: ID du tenant
        supplier_name: Nom du fournisseur
        invoice_reference: Référence de la facture (optionnel)
        invoice_date: Date de la facture (optionnel, inférée sinon)
        analyze: Si True, génère un rapport d'analyse de qualité

    Returns:
        Dict avec lines_inserted et optionnellement quality_report
    """
    if invoice_df.empty:  # Aucun contenu à traiter
        return {"lines_inserted": 0}  # Retourne un bilan vide

    # Segmentation par facture si plusieurs invoice_id dans un même DataFrame
    if group_by_invoice_id and not _skip_grouping and "invoice_id" in invoice_df.columns:
        unique_ids = sorted({str(v).strip() for v in invoice_df["invoice_id"].dropna().unique() if str(v).strip()})
        if len(unique_ids) > 1:
            total = 0
            details: list[dict[str, object]] = []
            for inv_id in unique_ids:
                subset = invoice_df[invoice_df["invoice_id"].astype(str).str.strip() == inv_id]
                res = sync_invoice_dataframe(
                    subset,
                    tenant_id=tenant_id,
                    supplier_name=supplier_name,
                    invoice_reference=inv_id,
                    invoice_date=invoice_date,
                    analyze=analyze,
                    group_by_invoice_id=group_by_invoice_id,
                    _skip_grouping=True,
                )
                total += res.get("lines_inserted", 0)
                details.append({"invoice_reference": inv_id, "lines": res.get("lines_inserted", 0)})
            return {"lines_inserted": total, "details": details}

    # Analyse de qualité optionnelle
    quality_report = None
    if analyze:
        try:
            from core.import_analyzer import analyze_invoice_import
            source_file = invoice_reference or f"{supplier_name}_{invoice_date or 'unknown'}"
            quality_report = analyze_invoice_import(invoice_df, source_file)
        except ImportError:
            pass  # Module non disponible

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

    # Mapping étendu des variantes de colonnes quantités
    quantity_series = _numeric_column(
        "quantite_recue", "qte_recue", "qte_init", "quantite", "qty", "quantity",
        "qte", "nb", "nombre", "units", "pieces"
    )

    # Mapping étendu des variantes de colonnes prix/montants
    unit_cost_series = _numeric_column(
        "prix_achat", "prix_achat_ht", "prix_ht", "unit_cost", "prix_unitaire",
        "pu_ht", "pu", "cout_unitaire", "unit_price", "price", "tarif",
        "montant_unitaire", "px_achat"
    )

    # Colonnes montant total (alternative si pas de prix unitaire)
    total_ht_series = _numeric_column(
        "montant_ht", "total_ht", "montant", "amount", "total_excl_tax",
        "ht", "net", "subtotal"
    )
    total_ttc_series = _numeric_column(
        "montant_ttc", "total_ttc", "prix_ttc", "total_incl_tax",
        "ttc", "gross", "total"
    )

    # Si prix unitaire absent mais montant total présent, recalculer
    if unit_cost_series.sum() == 0 and total_ht_series.sum() > 0:
        safe_qty = quantity_series.replace(0, 1)
        unit_cost_series = total_ht_series / safe_qty

    vat_series = _numeric_column("tva", "tva_pct", "vat", "vat_rate", "taxe")

    # Totaux ligne HT : privilégier total_ht, sinon qty*unit
    line_totals_excl = total_ht_series.copy()
    mask_missing_ht = line_totals_excl == 0
    line_totals_excl.loc[mask_missing_ht] = quantity_series.loc[mask_missing_ht].replace(0, 1) * unit_cost_series.loc[mask_missing_ht]

    # Si qty = 0 mais montant HT présent, déduire qty
    qty_missing = quantity_series == 0
    inferred_qty = line_totals_excl / unit_cost_series.replace(0, pd.NA)
    quantity_series.loc[qty_missing] = inferred_qty.loc[qty_missing].fillna(0)

    # Totaux ligne TTC : privilégier total_ttc, sinon recalcul avec TVA
    line_totals_incl = total_ttc_series.copy()
    mask_missing_ttc = line_totals_incl == 0
    line_totals_incl.loc[mask_missing_ttc] = line_totals_excl.loc[mask_missing_ttc] * (1 + vat_series.loc[mask_missing_ttc] / 100)

    total_excl_tax = float(line_totals_excl.sum())
    total_incl_tax = float(line_totals_incl.sum())
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

        # Nettoie les lignes existantes de ce document pour éviter les doublons lors des reimport
        conn.execute(
            text("DELETE FROM fact_invoices WHERE document_id = :doc_id"),
            {"doc_id": document_id},
        )

        category_cache: dict[str, int] = {}  # Cache pour éviter les requêtes répétées sur les catégories
        product_cache: dict[int, int] = {}  # Cache pour les produits dimensionnels

        for idx, row in enumerate(working_df.to_dict("records")):  # Parcourt chaque ligne de facture
            product_id = row.get("produit_id")  # ID produit brut (peut être None)
            try:
                product_key = int(float(product_id)) if product_id is not None else None
            except (TypeError, ValueError):  # Conversion échouée
                product_key = None

            category_label = row.get("catalogue_categorie") or row.get("categorie")  # Catégorie fournie
            if category_label not in category_cache:  # Si pas encore en cache
                category_cache[category_label or "Non classé"] = _ensure_dim_category(conn, category_label)  # Crée/charge la catégorie
            category_dim_id = category_cache[category_label or "Non classé"]  # Récupère l'ID catégorie

            cache_key = product_key if product_key is not None else (row.get("codes") or row.get("nom") or "fallback")
            if cache_key not in product_cache:
                product_cache[cache_key] = _ensure_dim_product(
                    conn,
                    product_key,
                    category_id=category_dim_id,
                    fallback_name=row.get("nom") or row.get("catalogue_nom") or row.get("libelle"),
                    barcode=row.get("codes"),
                    tenant_id=tenant_dim_id,
                )

            fact_payload = {
                "tenant_id": tenant_dim_id,
                "date_id": date_dim_id,
                "supplier_id": supplier_dim_id,
                "document_id": document_id,
                "product_id": product_cache[cache_key],
                "category_id": category_dim_id,
                "invoice_number": invoice_reference or row.get("invoice_number") or row.get("numero_facture") or "import",
                "sku": row.get("codes"),
                "quantity": float(quantity_series.iloc[idx] if idx < len(quantity_series) else 0),
                "unit_cost": float(unit_cost_series.iloc[idx] if idx < len(unit_cost_series) else 0),
                "vat_rate": float(vat_series.iloc[idx] if idx < len(vat_series) else 0),
                "currency": "EUR",
            }  # Données de la ligne fact_invoices

            # Ne rien insérer si aucune info monétaire
            if (
                fact_payload["quantity"] == 0
                and fact_payload["unit_cost"] == 0
                and (line_totals_excl.iloc[idx] if idx < len(line_totals_excl) else 0) == 0
                and (line_totals_incl.iloc[idx] if idx < len(line_totals_incl) else 0) == 0
            ):
                continue

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

    result = {"lines_inserted": lines_inserted}  # Bilan d'insertion
    if quality_report:
        result["quality_report"] = {
            "quality_score": quality_report.quality_score,
            "total_rows": quality_report.total_rows,
            "valid_rows": quality_report.valid_rows,
            "rejected_rows": quality_report.rejected_rows,
            "flags": quality_report.quality_flags,
            "anomaly_count": len(quality_report.anomalies),
        }
    return result


__all__ = ["sync_invoice_dataframe"]  # Exporte la fonction principale
