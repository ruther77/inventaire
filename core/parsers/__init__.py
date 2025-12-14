"""Registry of invoice parsers (light wrappers around core.invoice_extractor).

These wrappers normalize the output columns to a shared ProductInput shape:
code_barre, libelle, prix_achat_ht, prix_vente_ttc, tva, unite, conditionnement, invoice_id.
"""

from __future__ import annotations

from typing import Callable
import pandas as pd

from core import invoice_extractor

Parser = Callable[[str, float, int], pd.DataFrame]


def _first_column(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    """Return the first existing column Series or an empty Series."""
    for name in candidates:
        if name in df.columns:
            return df[name]
    return pd.Series(dtype=object)


def _normalize_df(df: pd.DataFrame, margin_rate: float) -> pd.DataFrame:
    """Ensure a minimal set of columns for ProductInput."""
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "code_barre",
                "libelle",
                "prix_achat_ht",
                "prix_vente_ttc",
                "tva",
                "unite",
                "conditionnement",
                "invoice_id",
            ]
        )

    normalized = pd.DataFrame(df).copy()

    # Conserve toutes les colonnes d'origine, puis ajoute les alias utilisés par le reste du pipeline.
    # Map common columns
    normalized["code_barre"] = _first_column(
        normalized, ["code_barre", "barcode", "ean", "codes", "numero_article"]
    )
    normalized["libelle"] = _first_column(normalized, ["libelle", "nom"])
    normalized["prix_achat_ht"] = _first_column(normalized, ["prix_achat", "prix_achat_ht"]).astype(float)
    # Alias interne attendu plus loin (prepare_invoice_dataframe utilise prix_achat)
    if "prix_achat" not in normalized.columns:
        normalized["prix_achat"] = normalized["prix_achat_ht"]
    else:
        normalized["prix_achat"] = normalized["prix_achat"].fillna(normalized["prix_achat_ht"])

    # Quantités : normalise vers quantite_recue et qte_init (fallback sur quantite_colis/quantite/conditionnement)
    if "quantite_recue" not in normalized.columns:
        normalized["quantite_recue"] = _first_column(
            normalized, ["quantite_recue", "qte_init", "quantite_colis", "quantite", "conditionnement"]
        )
    if "qte_init" not in normalized.columns:
        normalized["qte_init"] = normalized.get("quantite_recue", pd.Series(dtype=object))
    normalized["quantite_recue"] = normalized["quantite_recue"].fillna(normalized.get("qte_init"))

    # Montants : conserve HT/TTC si présents, sinon recalcule proprement (utile pour TAIYAT où montant_total_facture est TTC)
    tva_series = pd.to_numeric(_first_column(normalized, ["tva", "tva_pct", "taxe"]), errors="coerce").fillna(0)
    price = pd.to_numeric(normalized.get("prix_achat", 0), errors="coerce").fillna(0)
    qty = pd.to_numeric(normalized.get("quantite_recue", 0), errors="coerce").fillna(0)

    montant_ht_calc = (price * qty).round(2)
    montant_ttc_calc = (montant_ht_calc * (1 + tva_series / 100)).round(2)

    # TTC prioritaire si fourni explicitement
    montant_ttc_source = normalized.get("montant_total_facture", normalized.get("montant_total", pd.Series(dtype=float)))
    if not isinstance(montant_ttc_source, pd.Series):
        montant_ttc_source = pd.Series([montant_ttc_source] * len(normalized))
    montant_ttc_source = pd.to_numeric(montant_ttc_source, errors="coerce")

    normalized["montant_ttc"] = montant_ttc_source.fillna(montant_ttc_calc)
    normalized["montant_ht"] = montant_ht_calc

    # prix_vente : si absent, on applique la marge cible sur prix_achat
    normalized["prix_vente_ttc"] = _first_column(normalized, ["prix_vente", "prix_vente_ttc"])
    if normalized["prix_vente_ttc"].isna().all():
        purchase = normalized["prix_achat_ht"].fillna(0).astype(float)
        normalized["prix_vente_ttc"] = (purchase * (1 + margin_rate)).round(2)

    normalized["tva"] = _first_column(normalized, ["tva"]).fillna(0)
    normalized["unite"] = _first_column(normalized, ["unite", "poids"])
    normalized["conditionnement"] = _first_column(normalized, ["conditionnement", "qte_init"])
    normalized["invoice_id"] = _first_column(normalized, ["invoice_id"])
    # Laisse passer toutes les colonnes d'origine pour la consolidation (fact_invoices) et les imports stock.
    return normalized


def parse_metro(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
    return _normalize_df(
        invoice_extractor.extract_products_from_metro_invoice(
            text, margin_rate=margin_rate, start_invoice_sequence=start_sequence
        ),
        margin_rate,
    )


def parse_eurociel(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
    return _normalize_df(
        invoice_extractor.extract_products_from_eurociel_invoice(
            text, margin_rate=margin_rate, start_invoice_sequence=start_sequence
        ),
        margin_rate,
    )


def parse_taiyat(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
    return _normalize_df(
        invoice_extractor.extract_products_from_taiyat_invoice(
            text, margin_rate=margin_rate, start_invoice_sequence=start_sequence
        ),
        margin_rate,
    )


PARSERS: dict[str, Parser] = {
    "metro": parse_metro,
    "eurociel": parse_eurociel,
    "taiyat": parse_taiyat,
}


def parse_invoice(text: str, supplier_hint: str | None, margin_rate: float, start_sequence: int) -> pd.DataFrame:
    key = (supplier_hint or "").lower().strip()
    parser = PARSERS.get(key)
    if parser:
        return parser(text, margin_rate, start_sequence)
    # fallback to invoice_extractor detection
    df = invoice_extractor.extract_products(
        text, supplier_hint=supplier_hint, margin_rate=margin_rate, start_invoice_sequence=start_sequence
    )
    return _normalize_df(df, margin_rate)
