"""Invoice extraction and import services."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from datetime import date, datetime, time, timezone

import pandas as pd
from sqlalchemy import text

from backend.services.invoice_utils import prepare_invoice_dataframe
from core import invoice_extractor, products_loader
from core.parsers import parse_invoice
from core.data_repository import exec_sql, query_df
from core.inventory_service import match_invoice_products, register_invoice_reception, suggest_product_matches
from core.pdf_utils import split_pdf_into_invoices
from core.price_history_service import record_price_history
from sqlalchemy import text as sa_text


# Mapping pour harmoniser les noms de fournisseurs
# Les clés sont des patterns (regex) et les valeurs sont les noms normalisés
SUPPLIER_NORMALIZATION_MAP = {
    r"metro": "METRO",
    r"eurociel|euro\s*ciel": "EUROCIEL",
    r"tai\s*yat|taiyat": "TAIYAT",
    r"pomona|passionfroid|passion\s*froid": "POMONA",
    r"transgourmet|trans\s*gourmet": "TRANSGOURMET",
    r"promocash|promo\s*cash": "PROMOCASH",
    r"carrefour": "CARREFOUR",
    r"auchan": "AUCHAN",
    r"sysco": "SYSCO",
    r"brake": "BRAKE",
}


def normalize_supplier_name(supplier: str | None) -> str:
    """Normalise le nom d'un fournisseur selon les conventions standard.

    Exemples:
        - "METRO" -> "METRO"
        - "euro ciel" -> "EUROCIEL"
        - "TAI YAT DISTRIBUTION" -> "TAIYAT"
        - "L'INCONTOURNABLE" -> "TAIYAT" (si détecté comme facture TAIYAT)
        - "Inconnu" -> "Inconnu"
    """
    if not supplier:
        return "Inconnu"

    cleaned = supplier.strip()
    if not cleaned:
        return "Inconnu"

    lowered = cleaned.lower()

    # Vérifie chaque pattern de normalisation
    for pattern, normalized_name in SUPPLIER_NORMALIZATION_MAP.items():
        if re.search(pattern, lowered, re.IGNORECASE):
            return normalized_name

    # Si pas de match, retourne le nom nettoyé en majuscules
    return cleaned.upper()


def detect_supplier_from_invoice(invoice_df: pd.DataFrame, raw_text: str | None = None) -> str:
    """Détecte automatiquement le fournisseur à partir des données de facture.

    Priorité de détection :
    1. Préfixe de l'invoice_id (EURO-, TAIYAT-, INV-)
    2. Contenu du texte brut (si fourni)
    3. Fallback sur "Inconnu"
    """
    # 1. Détection par préfixe d'invoice_id
    if isinstance(invoice_df, pd.DataFrame) and "invoice_id" in invoice_df.columns:
        invoice_ids = invoice_df["invoice_id"].dropna().astype(str).tolist()
        for inv_id in invoice_ids:
            inv_upper = inv_id.upper()
            if inv_upper.startswith("EURO-") or inv_upper.startswith("EUROCIEL"):
                return "EUROCIEL"
            if inv_upper.startswith("TAIYAT-"):
                return "TAIYAT"
            if inv_upper.startswith("POMONA-"):
                return "POMONA"
            if inv_upper.startswith("TRANS-") or inv_upper.startswith("TRANSGOURMET"):
                return "TRANSGOURMET"
            # INV-XXX est typiquement METRO
            if inv_upper.startswith("INV-"):
                return "METRO"

    # 2. Détection par contenu du texte brut
    if raw_text:
        format_detected = invoice_extractor.detect_invoice_format(raw_text)
        if format_detected and format_detected != "generic":
            return normalize_supplier_name(format_detected)

    return "Inconnu"


def _normalize_invoice_datetime(value: datetime | date | None) -> datetime | None:
    """Uniformise une date/datetime de facture en datetime timezone-aware (UTC)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def get_last_invoice_sequence(tenant_id: int = 1) -> int:
    """Récupère le dernier numéro de séquence INV-XXX depuis la base."""
    import re
    sql = text(
        """
        SELECT invoice_id FROM processed_invoices
        WHERE tenant_id = :tenant_id AND invoice_id LIKE 'INV-%'
        ORDER BY invoice_id DESC
        LIMIT 1
        """
    )
    df = query_df(sql, {"tenant_id": tenant_id})
    if df.empty:
        return 0
    last_id = df.iloc[0]["invoice_id"]
    # Extrait le numéro de INV-XXX
    match = re.search(r"INV-(\d+)", last_id)
    if match:
        return int(match.group(1))
    return 0


def extract_invoice_lines(
    text: str,
    *,
    margin_percent: float = 40.0,
    supplier_hint: str | None = None,
    tenant_id: int = 1,
) -> pd.DataFrame:
    """Extract structured lines from raw invoice text."""

    if not text.strip():
        return pd.DataFrame()

    # Récupère le dernier numéro de séquence pour continuer la numérotation
    last_sequence = get_last_invoice_sequence(tenant_id)

    # Passage marge (%) -> taux pour le calcul du prix de vente proposé
    margin_rate = max(0.0, margin_percent) / 100.0
    normalized_df = parse_invoice(
        text,
        supplier_hint=supplier_hint,
        margin_rate=margin_rate,
        start_sequence=last_sequence,
    )
    return normalized_df


def _detect_price_anomalies(
    df: pd.DataFrame,
    *,
    tenant_id: int = 1,
    threshold_pct: float = 15.0,
) -> pd.DataFrame:
    """Détecte les anomalies de prix en comparant avec l'historique et le catalogue.

    Marque les lignes avec:
    - is_anomaly: True si anomalie détectée
    - price_anomaly: Type d'anomalie (increase/decrease/new_price)
    - price_anomaly_pct: Pourcentage de variation
    - price_anomaly_description: Description lisible
    - last_price: Dernier prix d'achat connu
    - suggestion: Suggestion IA basée sur l'historique

    Args:
        df: DataFrame avec les lignes de facture
        tenant_id: ID du tenant
        threshold_pct: Seuil de variation pour détecter une anomalie (défaut: 15%)

    Returns:
        DataFrame enrichi avec les colonnes d'anomalie
    """
    if df.empty:
        return df

    result = df.copy()

    # Initialiser les colonnes d'anomalie
    result["is_anomaly"] = False
    result["price_anomaly"] = None
    result["price_anomaly_pct"] = None
    result["price_anomaly_description"] = None
    result["last_price"] = None
    result["suggestion"] = None

    # Récupérer les produits avec un produit_id valide
    if "produit_id" not in result.columns:
        return result
    valid_product_ids = result["produit_id"].dropna().astype(int).unique().tolist()
    if not valid_product_ids:
        return result

    # Récupérer l'historique des prix pour ces produits
    placeholders = ", ".join(f":pid{i}" for i in range(len(valid_product_ids)))
    params = {f"pid{i}": pid for i, pid in enumerate(valid_product_ids)}
    params["tenant_id"] = int(tenant_id)

    # Query pour obtenir le dernier prix d'achat connu par produit
    history_sql = f"""
        WITH latest_prices AS (
            SELECT DISTINCT ON (produit_id)
                produit_id,
                prix_achat as last_price,
                facture_date as recorded_at
            FROM produits_price_history
            WHERE produit_id IN ({placeholders})
            ORDER BY produit_id, facture_date DESC
        )
        SELECT
            p.id as produit_id,
            COALESCE(lp.last_price, p.prix_achat) as last_price,
            p.prix_achat as catalogue_price,
            lp.recorded_at as last_price_date
        FROM produits p
        LEFT JOIN latest_prices lp ON lp.produit_id = p.id
        WHERE p.id IN ({placeholders})
          AND p.tenant_id = :tenant_id
    """

    try:
        price_history = query_df(history_sql, params=params)
    except Exception as e:
        logging.warning(f"Erreur lors de la récupération de l'historique des prix: {e}")
        return result

    if price_history.empty:
        return result

    # Créer un dictionnaire de lookup pour les prix historiques
    price_lookup = {}
    for _, row in price_history.iterrows():
        pid = int(row["produit_id"])
        price_lookup[pid] = {
            "last_price": float(row["last_price"] or 0),
            "catalogue_price": float(row["catalogue_price"] or 0),
            "last_price_date": row.get("last_price_date"),
        }

    # Analyser chaque ligne
    for idx, row in result.iterrows():
        produit_id = row.get("produit_id")
        if pd.isna(produit_id):
            continue

        try:
            pid = int(produit_id)
        except (ValueError, TypeError):
            continue

        if pid not in price_lookup:
            continue

        prix_facture = float(row.get("prix_achat", 0) or 0)
        prix_historique = price_lookup[pid]["last_price"]
        prix_catalogue = price_lookup[pid]["catalogue_price"]

        # Si pas de prix de référence, marquer comme nouveau prix
        if prix_historique <= 0 and prix_catalogue <= 0:
            if prix_facture > 0:
                result.at[idx, "is_anomaly"] = True
                result.at[idx, "price_anomaly"] = "new_price"
                result.at[idx, "price_anomaly_description"] = "Premier prix enregistré"
                result.at[idx, "suggestion"] = "Vérifiez que ce prix correspond au marché"
            continue

        # Utiliser le prix le plus récent comme référence
        prix_reference = prix_historique if prix_historique > 0 else prix_catalogue
        result.at[idx, "last_price"] = prix_reference

        # Calculer la variation
        if prix_reference > 0 and prix_facture > 0:
            variation_pct = ((prix_facture - prix_reference) / prix_reference) * 100

            if abs(variation_pct) >= threshold_pct:
                result.at[idx, "is_anomaly"] = True
                result.at[idx, "price_anomaly_pct"] = round(variation_pct, 1)

                if variation_pct > 0:
                    result.at[idx, "price_anomaly"] = "increase"
                    result.at[idx, "price_anomaly_description"] = (
                        f"Hausse de {variation_pct:.1f}% vs dernier achat ({prix_reference:.2f}€ → {prix_facture:.2f}€)"
                    )
                    # Suggestion contextuelle
                    if variation_pct > 30:
                        result.at[idx, "suggestion"] = "Variation importante - Vérifiez avec le fournisseur"
                    elif variation_pct > 20:
                        result.at[idx, "suggestion"] = "Possible hausse saisonnière ou rupture marché"
                    else:
                        result.at[idx, "suggestion"] = "Légère hausse - À surveiller sur les prochains achats"
                else:
                    result.at[idx, "price_anomaly"] = "decrease"
                    result.at[idx, "price_anomaly_description"] = (
                        f"Baisse de {abs(variation_pct):.1f}% vs dernier achat ({prix_reference:.2f}€ → {prix_facture:.2f}€)"
                    )
                    result.at[idx, "suggestion"] = "Bonne opportunité - Vérifiez la qualité du produit"

    return result


def enrich_lines_with_catalog(
    lines: pd.DataFrame,
    *,
    margin_percent: float = 40.0,
    tenant_id: int = 1,
) -> pd.DataFrame:
    """Attach catalogue metadata (matches) to parsed invoice lines."""

    df = lines.copy()
    if "codes" not in df.columns or df.empty:
        return df

    # Normalise les codes bars pour matcher avec le catalogue (case/espaces)
    df["_code_lower"] = df["codes"].fillna("").astype(str).str.lower().str.strip()
    matches_df = match_invoice_products(df, tenant_id=tenant_id)
    if not matches_df.empty:
        matches_df = matches_df.rename(
            columns={
                "code": "_code_lower",
                "produit_id": "catalogue_id",
                "produit_nom": "catalogue_nom",
                "categorie": "catalogue_categorie",
                "prix_achat_catalogue": "prix_achat_catalogue",
            }
        )
        df = df.merge(matches_df, on="_code_lower", how="left")
        if "catalogue_id" in df.columns:
            if "produit_id" not in df.columns:
                df["produit_id"] = df["catalogue_id"]
            else:
                df["produit_id"] = df["produit_id"].fillna(df["catalogue_id"])

    # Rattrapage par nom (utile pour les factures Eurociel sans code-barres ou avec codes TVA type C2/C07)
    # On associe sur lower(nom) et on récupère le code principal du produit.
    # Cela permet de peupler codes / produit_id même quand "codes" est vide ou contient un code TVA.
    if not df.empty:
        names = sorted({str(n).strip().lower() for n in df.get("nom", []) if str(n).strip()})
        if names:
            placeholders = ", ".join(f":n{i}" for i in range(len(names)))
            params = {f"n{i}": name for i, name in enumerate(names)}
            params["tenant_id"] = int(tenant_id)
            sql = f"""
                SELECT
                    lower(p.nom) AS nom_lower,
                    p.id AS produit_id,
                    p.nom AS produit_nom,
                    p.categorie,
                    COALESCE(p.prix_achat, 0) AS prix_achat_catalogue,
                    COALESCE(p.prix_vente, 0) AS prix_vente_catalogue,
                    COALESCE(p.tva, 0) AS tva_catalogue,
                    pb.code AS barcode
                FROM produits p
                LEFT JOIN LATERAL (
                    SELECT code
                    FROM produits_barcodes
                    WHERE produit_id = p.id
                    ORDER BY is_principal DESC, id
                    LIMIT 1
                ) pb ON TRUE
                WHERE lower(p.nom) IN ({placeholders})
                  AND p.tenant_id = :tenant_id
            """
            try:
                name_matches = query_df(sql, params=params)
            except Exception:
                name_matches = pd.DataFrame()

            if not name_matches.empty:
                name_matches = name_matches.rename(
                    columns={
                        "nom_lower": "_nom_lower",
                        "produit_id": "name_catalogue_id",
                        "produit_nom": "name_catalogue_nom",
                        "categorie": "name_catalogue_categorie",
                        "prix_achat_catalogue": "name_prix_achat_catalogue",
                        "prix_vente_catalogue": "name_prix_vente_catalogue",
                        "tva_catalogue": "name_tva_catalogue",
                        "barcode": "name_barcode",
                    }
                )
                df["_nom_lower"] = df["nom"].astype(str).str.lower().str.strip()
                df = df.merge(name_matches, on="_nom_lower", how="left")
                # Remplit les champs catalogue/produit manquants avec le match par nom
                for target, src in [
                    ("catalogue_id", "name_catalogue_id"),
                    ("catalogue_nom", "name_catalogue_nom"),
                    ("catalogue_categorie", "name_catalogue_categorie"),
                ]:
                    if target not in df.columns:
                        df[target] = df[src]
                    else:
                        df[target] = df[target].fillna(df[src])
                if "produit_id" not in df.columns:
                    df["produit_id"] = df["name_catalogue_id"]
                else:
                    df["produit_id"] = df["produit_id"].fillna(df["name_catalogue_id"])
                if "codes" in df.columns:
                    # Évite l'erreur pandas "dict-value and non-None to_replace" en utilisant fillna/mask.
                    df["codes"] = df["codes"].replace("", pd.NA)
                    df["codes"] = df["codes"].fillna(df["name_barcode"])
                # Nettoyage colonnes temporaires
                df.drop(columns=["_nom_lower"], inplace=True, errors="ignore")
                tmp_cols = [c for c in df.columns if c.startswith("name_")]
                df.drop(columns=tmp_cols, inplace=True, errors="ignore")
    df.drop(columns=["_code_lower"], inplace=True, errors="ignore")
    for column in ("catalogue_id", "catalogue_nom", "catalogue_categorie"):
        if column not in df.columns:
            df[column] = None

    # ==========================================================================
    # DÉTECTION ANOMALIES DE PRIX
    # Compare le prix d'achat facture vs prix catalogue et historique
    # ==========================================================================
    df = _detect_price_anomalies(df, tenant_id=tenant_id)

    # ==========================================================================
    # SUGGESTIONS IA POUR PRODUITS NON-MATCHÉS
    # Trouve des produits similaires par nom pour les lignes sans produit_id
    # ==========================================================================
    df = suggest_product_matches(df, tenant_id=tenant_id)

    # Finalise les totaux/marges et colonnes numériques normalisées
    margin_rate = max(0.0, margin_percent) / 100.0
    return prepare_invoice_dataframe(df, margin_rate)


def _has_missing_product_ids(df: pd.DataFrame) -> bool:
    """Return True when at least one invoice line lacks a valid produit_id."""

    if "produit_id" not in df.columns:
        return True

    numeric_ids = pd.to_numeric(df["produit_id"], errors="coerce")
    return bool(numeric_ids.isna().any() or (numeric_ids <= 0).any())


def _prepare_lines_for_import(invoice_df: pd.DataFrame, *, tenant_id: int = 1) -> pd.DataFrame:
    """Ensure movements can be created even if the frontend lacks produit_id/quantities."""

    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:
        return invoice_df

    working_df = invoice_df.copy()

    has_codes = "codes" in working_df.columns
    if has_codes and _has_missing_product_ids(working_df):
        # Re-run the catalogue reconciliation with the latest DB state so newly
        # created products (or updated barcodes) are picked up automatically.
        return enrich_lines_with_catalog(working_df, margin_percent=40.0, tenant_id=tenant_id)

    if "quantite_recue" not in working_df.columns and "qte_init" in working_df.columns:
        working_df["quantite_recue"] = working_df["qte_init"]
    elif "quantite_recue" in working_df.columns and "qte_init" in working_df.columns:
        missing_mask = working_df["quantite_recue"].isna()
        if missing_mask.any():
            working_df.loc[missing_mask, "quantite_recue"] = working_df.loc[missing_mask, "qte_init"]

    return working_df


def apply_invoice_import(
    invoice_df: pd.DataFrame,
    *,
    username: str,
    supplier: str | None = None,
    movement_type: str = "ENTREE",
    invoice_date: datetime | date | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    """Persist movements based on the invoice lines."""

    # Sécurise les données avant création des mouvements (quantités, produit_id)
    prepared_df = _prepare_lines_for_import(invoice_df, tenant_id=tenant_id)

    normalized_invoice_dt = _normalize_invoice_datetime(invoice_date)
    if normalized_invoice_dt is None and "facture_date" in invoice_df.columns and not invoice_df["facture_date"].dropna().empty:
        first_value = invoice_df["facture_date"].dropna().iloc[0]
        try:
            normalized_invoice_dt = _normalize_invoice_datetime(pd.to_datetime(first_value).to_pydatetime())
        except Exception:
            normalized_invoice_dt = None

    result = register_invoice_reception(
        prepared_df,
        username=username,
        supplier=supplier,
        movement_type=movement_type,
        reception_date=normalized_invoice_dt,
        tenant_id=tenant_id,
    )
    record_processed_invoices(prepared_df, supplier=supplier, tenant_id=tenant_id)
    return result


def import_catalog_from_invoice(
    invoice_df: pd.DataFrame,
    *,
    supplier: str | None = None,
    initialize_stock: bool = False,
    invoice_date: datetime | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    """Create/update catalogue entries from invoice lines and log price history."""

    if not isinstance(invoice_df, pd.DataFrame):
        raise ValueError("Le format des lignes est invalide.")

    # 1) Création/MAJ produits + codes, 2) historisation des prix avec date facture
    summary = products_loader.load_products_from_df(
        invoice_df,
        initialize_stock=initialize_stock,
        tenant_id=tenant_id,
    )
    normalized_invoice_dt = _normalize_invoice_datetime(invoice_date)
    record_price_history(
        invoice_df,
        supplier=supplier,
        context="Extraction",
        invoice_date=normalized_invoice_dt or datetime.now(timezone.utc),
        tenant_id=tenant_id,
    )
    record_processed_invoices(invoice_df, supplier=supplier, tenant_id=tenant_id)
    return summary


__all__ = [
    "extract_invoice_lines",
    "enrich_lines_with_catalog",
    "apply_invoice_import",
    "import_catalog_from_invoice",
    "record_processed_invoices",
    "find_processed_invoice_ids",
    "persist_invoice_documents",
    "list_processed_invoices",
    "get_processed_invoice_file",
    "normalize_supplier_name",
    "detect_supplier_from_invoice",
]
LOGGER = logging.getLogger(__name__)
INVOICE_ARCHIVE_DIR = Path("data/processed_invoices")
INVOICE_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _build_invoice_filename(tenant_id: int, invoice_id: str) -> Path:
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in invoice_id)
    return INVOICE_ARCHIVE_DIR / f"{tenant_id}_{safe_id}.pdf"


def _collect_invoice_groups(invoice_df: pd.DataFrame) -> list[dict[str, object]]:
    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty or "invoice_id" not in invoice_df.columns:
        return []

    groups: list[dict[str, object]] = []
    for invoice_id, group in invoice_df.groupby("invoice_id"):
        invoice_key = str(invoice_id or "").strip()
        if not invoice_key:
            continue
        facture_date = None
        if "facture_date" in group.columns:
            facture_candidates = [str(value).strip() for value in group["facture_date"].dropna().tolist() if str(value).strip()]
            if facture_candidates:
                facture_date = facture_candidates[0]
        groups.append(
            {
                "invoice_id": invoice_key,
                "line_count": int(len(group)),
                "facture_date": facture_date,
            }
        )
    return groups


def _fetch_processed_invoice_ids(invoice_ids: set[str], *, tenant_id: int) -> set[str]:
    if not invoice_ids:
        return set()

    params: dict[str, object] = {"tenant_id": int(tenant_id)}
    placeholders: list[str] = []
    for idx, invoice_id in enumerate(sorted(invoice_ids)):
        key = f"invoice_{idx}"
        placeholders.append(f":{key}")
        params[key] = invoice_id

    sql = text(
        f"""
        SELECT invoice_id
        FROM processed_invoices
        WHERE tenant_id = :tenant_id
          AND invoice_id IN ({", ".join(placeholders)})
        """
    )

    try:
        df = query_df(sql, params=params)
    except Exception as exc:  # pragma: no cover - base indisponible
        LOGGER.warning("Impossible de vérifier les factures importées: %s", exc)
        return set()

    if df.empty:
        return set()
    return {str(entry) for entry in df["invoice_id"].tolist()}


def record_processed_invoices(invoice_df: pd.DataFrame, *, supplier: str | None, tenant_id: int) -> None:
    groups = _collect_invoice_groups(invoice_df)
    if not groups:
        return
    # Normalise ou détecte automatiquement le fournisseur
    if supplier:
        supplier_label = normalize_supplier_name(supplier)
    else:
        supplier_label = detect_supplier_from_invoice(invoice_df)
    sql = text(
        """
        INSERT INTO processed_invoices (tenant_id, invoice_id, supplier, facture_date, line_count, file_path)
        VALUES (:tenant_id, :invoice_id, :supplier, :facture_date, :line_count, :file_path)
        ON CONFLICT (tenant_id, invoice_id)
        DO UPDATE SET
            supplier = EXCLUDED.supplier,
            facture_date = COALESCE(EXCLUDED.facture_date, processed_invoices.facture_date),
            line_count = EXCLUDED.line_count,
            file_path = COALESCE(EXCLUDED.file_path, processed_invoices.file_path),
            updated_at = now()
        """
    )
    params_batch: list[dict[str, object]] = []
    for group in groups:
        invoice_id = group["invoice_id"]
        default_path = _build_invoice_filename(tenant_id, invoice_id)
        file_path = str(default_path) if default_path.exists() else None
        params_batch.append(
            {
                "tenant_id": int(tenant_id),
                "invoice_id": invoice_id,
                "supplier": supplier_label,
                "facture_date": group.get("facture_date"),
                "line_count": group.get("line_count", 0),
                "file_path": file_path,
            }
        )
    try:
        exec_sql(sql, params=params_batch)
    except Exception as exc:  # pragma: no cover - base indisponible
        LOGGER.warning("Impossible d'enregistrer les factures (batch): %s", exc)


def find_processed_invoice_ids(invoice_ids: set[str], *, tenant_id: int) -> set[str]:
    try:
        return _fetch_processed_invoice_ids(invoice_ids, tenant_id=tenant_id)
    except Exception:
        return set()


def list_processed_invoices(
    *,
    tenant_id: int,
    supplier: str | None = None,
    invoice_id: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int = 100,
) -> list[dict[str, object]]:
    filters = ["tenant_id = :tenant_id"]
    params: dict[str, object] = {"tenant_id": int(tenant_id), "limit": int(max(1, min(limit, 500)))}

    if supplier:
        filters.append("supplier ILIKE :supplier")
        params["supplier"] = f"%{supplier}%"
    if invoice_id:
        filters.append("invoice_id ILIKE :invoice_id")
        params["invoice_id"] = f"%{invoice_id}%"
    if date_start:
        filters.append("facture_date >= :date_start")
        params["date_start"] = date_start
    if date_end:
        filters.append("facture_date <= :date_end")
        params["date_end"] = date_end

    where_clause = " AND ".join(filters)
    sql = text(
        f"""
        SELECT invoice_id, supplier, facture_date, line_count, file_path, created_at, updated_at
        FROM processed_invoices
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
    )

    df = query_df(sql, params=params)
    if df.empty:
        return []
    return df.to_dict(orient="records")


def persist_invoice_documents(pdf_bytes: bytes, *, tenant_id: int, supplier: str | None = None) -> dict[str, dict[str, str]]:
    """Découpe et stocke physiquement chaque facture détectée."""

    documents = split_pdf_into_invoices(pdf_bytes)
    if not documents:
        return {}

    stored: dict[str, dict[str, str]] = {}
    for entry in documents:
        invoice_id = str(entry.get("invoice_id") or "").strip()
        if not invoice_id:
            continue
        pdf_chunk: bytes = entry.get("pdf_bytes") or b""
        if not pdf_chunk:
            continue
        file_path = _build_invoice_filename(tenant_id, invoice_id)
        try:
            file_path.write_bytes(pdf_chunk)
            stored[invoice_id] = {
                "facture_date": entry.get("facture_date"),
                "file_path": str(file_path),
                "supplier": supplier,
            }
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Impossible de sauvegarder la facture %s: %s", invoice_id, exc)
    return stored


def get_processed_invoice_file(*, tenant_id: int, invoice_id: str) -> Path | None:
    if not invoice_id:
        return None
    sql = text(
        """
        SELECT file_path
        FROM processed_invoices
        WHERE tenant_id = :tenant_id AND invoice_id = :invoice_id
        LIMIT 1
        """
    )
    df = query_df(sql, params={"tenant_id": int(tenant_id), "invoice_id": invoice_id})
    if df.empty:
        # tente un chemin dérivé
        candidate = _build_invoice_filename(tenant_id, invoice_id)
        return candidate if candidate.exists() else None
    raw_path = df.iloc[0].get("file_path")
    if raw_path:
        path = Path(raw_path)
        if path.exists():
            return path
    candidate = _build_invoice_filename(tenant_id, invoice_id)
    return candidate if candidate.exists() else None
