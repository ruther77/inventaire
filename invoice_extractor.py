from __future__ import annotations

import io
import re
from typing import Iterable, Mapping, Sequence

import pandas as pd

try:  # pragma: no cover - import de compatibilité
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - environnement sans pypdf
    class PdfReader:  # type: ignore
        """Substitut minimal rappelant d'installer pypdf."""

        def __init__(self, *_args, **_kwargs):
            raise ImportError(
                "La dépendance 'pypdf' est requise pour lire les factures PDF. "
                "Ajoutez-la via `pip install pypdf`."
            )
from docx import Document

# Mapping par défaut des codes TVA METRO connus.
#
# Les codes sont documentés par METRO et couvrent l'ensemble des taux
# appliqués sur les factures françaises :
#
# - 20 % (taux normal)      : A, C, D, F, J, K
# - 10 % (taux intermédiaire): B, H, N, T
# - 5,5 % (taux réduit)     : E, I, L, P, Q, R, S, U, V, W, Y
# - 2,1 % (taux particulier): M
# - 0 % (exonérations)      : G, O, X, Z
#
# Un code inconnu tombera sur ``default_tva`` mais il est toujours possible
# de surcharger ce mapping via ``tva_map`` lors de l'appel.
_METRO_TVA_CODE_GROUPS: tuple[tuple[float, tuple[str, ...]], ...] = (
    (20.0, ("A", "C", "D", "F", "J", "K")),
    (10.0, ("B", "H", "N", "T")),
    (5.5, ("E", "I", "L", "P", "Q", "R", "S", "U", "V", "W", "Y")),
    (2.1, ("M",)),
    (0.0, ("G", "O", "X", "Z")),
)

DEFAULT_TVA_CODE_MAP: dict[str, float] = {
    code: rate
    for rate, codes in _METRO_TVA_CODE_GROUPS
    for code in codes
}

DEFAULT_MARGIN_RATE = 0.0


def clean_data(value):
    """Nettoie une valeur numérique (remplace la virgule par le point)."""
    if isinstance(value, str):
        # Remplace la virgule par le point et supprime tout caractère non numérique/point/espace
        return value.replace(',', '.').replace('-', '').strip()
    return value


def extract_text_from_file(uploaded_file):
    """
    Extrait le texte brut d'un fichier téléversé (PDF ou DOCX/DOC).
    """
    file_type = uploaded_file.type

    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)

    # 1. Traitement des PDF
    if 'pdf' in file_type:
        try:
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception:
            return "Erreur lors de la lecture du PDF."

    # 2. Traitement des DOCX (Word)
    elif 'word' in file_type or 'document' in file_type or uploaded_file.name.endswith('.docx'):
        try:
            document = Document(uploaded_file)
            text = '\n'.join([paragraph.text for paragraph in document.paragraphs])
            return text
        except Exception:
            return "Erreur lors de la lecture du fichier Word (.docx)."

    # 3. Traitement du texte brut
    elif 'text' in file_type or uploaded_file.name.endswith('.txt'):
        return uploaded_file.getvalue().decode("utf-8")
        
    else:
        return "" # Type de fichier non supporté

# Fichier : invoice_extractor.py (Mise à jour de la fonction d'extraction)

# ... (les imports et la fonction clean_data restent inchangés) ...

def _normalise_tva_code(code: str | None) -> str | None:
    if not code:
        return None
    cleaned = str(code).strip().upper()
    return cleaned or None


def _resolve_tva_value(code: str | None, tva_lookup: Mapping[str, float], default_tva: float) -> float:
    if code is None:
        return default_tva
    if code in tva_lookup:
        return float(tva_lookup[code])
    return default_tva


_IGNORED_DESIGNATION_KEYWORDS: tuple[str, ...] = (
    "duplicata",
    "prix au kg ou au litre",
    "plus cotis",
    "montant ttc",
    "volume effectif",
    "page",
    "total",
    "client",
    "commande",
)


def _normalise_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _should_skip_line(line: str) -> bool:
    lowered = line.lower()
    return any(keyword in lowered for keyword in _IGNORED_DESIGNATION_KEYWORDS)


def _parse_decimal(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = (
        str(value)
        .replace("\u202f", "")
        .replace("\xa0", "")
        .replace(",", ".")
        .strip()
    )
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    decimal = _parse_decimal(value)
    if decimal is None:
        return None
    return int(round(decimal))


def _parse_detail_line(line: str) -> dict[str, object] | None:
    tokens = _normalise_whitespace(line).split()
    if len(tokens) < 8:
        return None

    regie = tokens[0]
    if not re.fullmatch(r"[A-Za-z]", regie):
        return None

    tva_code: str | None = None
    if re.fullmatch(r"[A-Za-z]", tokens[-1]):
        tva_code = tokens[-1].upper()
        tokens = tokens[:-1]

    if len(tokens) < 8:
        return None

    volume = _parse_decimal(tokens[1])
    vap = _parse_decimal(tokens[2])
    poids_unitaire = _parse_decimal(tokens[3])
    unit_price = _parse_decimal(tokens[4])
    quantity = _parse_int(tokens[5])
    colisage = _parse_int(tokens[6])
    total_amount = _parse_decimal(tokens[7])

    if unit_price is None or quantity is None or total_amount is None:
        return None

    detail: dict[str, object] = {
        "regie": regie.upper(),
        "volume_litre": volume or 0.0,
        "vap": vap or 0.0,
        "poids_unitaire": poids_unitaire or 0.0,
        "prix_unitaire": round(unit_price, 2),
        "quantite_colis": max(quantity, 0),
        "colisage": max(colisage or 1, 1),
        "montant_total": round(total_amount, 2),
    }

    if tva_code:
        detail["tva_code"] = tva_code

    if len(tokens) > 8:
        extras = tokens[8:]
        if extras:
            detail["extra"] = " ".join(extras)

    return detail


def _parse_inline_summary(label: str) -> dict[str, object] | None:
    tokens = _normalise_whitespace(label).split()
    if len(tokens) < 4:
        return None

    tva_candidate = tokens[-1]
    total_candidate = tokens[-2] if len(tokens) >= 2 else None
    qty_candidate = tokens[-3] if len(tokens) >= 3 else None
    price_candidate = tokens[-4] if len(tokens) >= 4 else None
    name_tokens = tokens[:-4]

    price = _parse_decimal(price_candidate)
    quantity = _parse_int(qty_candidate)
    total = _parse_decimal(total_candidate)

    if price is None or quantity is None:
        return None

    tva_code: str | None = None
    if tva_candidate and re.fullmatch(r"[A-Za-z]", tva_candidate):
        tva_code = tva_candidate.upper()
    else:
        name_tokens.append(tva_candidate)

    designation = " ".join(name_tokens).strip()
    if not designation:
        return None

    detail: dict[str, object] = {
        "nom": designation,
        "prix_unitaire": round(price, 2),
        "quantite_colis": max(quantity, 0),
        "colisage": 1,
        "montant_total": round(
            total if total is not None else price * max(quantity, 0),
            2,
        ),
    }

    if tva_code:
        detail["tva_code"] = tva_code

    return detail


def _join_designation(parts: Sequence[str]) -> str:
    cleaned: list[str] = []
    for part in parts:
        normalised = _normalise_whitespace(part)
        if not normalised or _should_skip_line(normalised):
            continue
        cleaned.append(normalised)
    return " ".join(cleaned).strip()


def _ensure_margin(purchase: float | None, sale: float | None, margin: float) -> float | None:
    if purchase is None:
        return sale
    safe_margin = max(0.0, float(margin))
    baseline = round(float(purchase) * (1.0 + safe_margin), 2)
    if sale is None:
        return baseline
    return round(sale if sale >= baseline else baseline, 2)


def extract_products_from_metro_invoice(
    raw_product_text: str,
    *,
    tva_map: Mapping[str, float] | None = None,
    default_tva: float = 20.0,
    margin_rate: float = 0.0,
) -> pd.DataFrame:
    """ Analyse une facture METRO """
    overrides = {k.upper(): float(v) for k, v in (tva_map or {}).items()}
    lookup = {**DEFAULT_TVA_CODE_MAP, **overrides}
    margin = DEFAULT_MARGIN_RATE
    
    lines = [
        _normalise_whitespace(chunk)
        for chunk in (raw_product_text or "").replace("\r", "").splitlines()
    ]

    start_pattern = re.compile(r"^(?P<ean>\d{10,14})\s+(?P<article>\d{4,10})\s*(?P<label>.*)")

    records: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    designation_parts: list[str] = []
    
    for line in lines:
        if not line:
            continue

        start_match = start_pattern.match(line)
        if start_match:
            if current and "prix_unitaire" in current:
                designation = _join_designation(designation_parts)
                if designation:
                    current["nom"] = designation
                if "montant_total" not in current:
                    qty = int(current.get("quantite_colis", 0))
                    colis = int(current.get("colisage", 1))
                    current["montant_total"] = round(
                        float(current["prix_unitaire"]) * max(qty, 0) * max(colis, 1),
                        2,
                    )
                records.append(current)

            current = {
                "codes": start_match.group("ean"),
                "numero_article": start_match.group("article"),
            }
            label = start_match.group("label").strip()
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
            inline_detail = _parse_inline_summary(label)
            if inline_detail:
                if "nom" in inline_detail:
                    current["nom"] = inline_detail.pop("nom")
                current.update(inline_detail)
                designation_parts = []
            else:
                designation_parts = [label] if label else []
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
            fallback_detail: dict[str, object] | None = None
            inline_tokens = _normalise_whitespace(label).split()
            parsed_count = 0
            if inline_tokens:
                candidate_code = inline_tokens[-1]
                has_code = bool(re.fullmatch(r"[A-Za-z]", candidate_code))
                if has_code:
                    parsed_count += 1
                if len(inline_tokens) >= parsed_count + 3:
                    total_raw = inline_tokens[-(parsed_count + 1)]
                    qty_raw = inline_tokens[-(parsed_count + 2)]
                    unit_raw = inline_tokens[-(parsed_count + 3)]
                    unit_val = _parse_decimal(unit_raw)
                    qty_val = _parse_int(qty_raw)
                    total_val = _parse_decimal(total_raw)
                    if unit_val is not None and qty_val is not None:
                        fallback_detail = {
                            "prix_unitaire": round(unit_val, 2),
                            "quantite_colis": max(qty_val, 0),
                            "colisage": 1,
                            "montant_total": round(
                                total_val if total_val is not None else unit_val * qty_val,
                                2,
                            ),
                        }
                        if has_code:
                            fallback_detail["tva_code"] = inline_tokens[-1].upper()
                        parsed_count += 3
            if fallback_detail:
                current.update(fallback_detail)
                remaining_tokens = inline_tokens[:-parsed_count] if parsed_count else inline_tokens
            else:
                remaining_tokens = inline_tokens
            designation_text = " ".join(remaining_tokens).strip()
            designation_parts = [designation_text] if designation_text else []
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
            continue

        if current is None:
            continue

        detail = _parse_detail_line(line)
        if detail:
            current.update(detail)
            continue

        if not _should_skip_line(line):
            designation_parts.append(line)

    if current and "prix_unitaire" in current:
        designation = _join_designation(designation_parts)
        if designation:
            current["nom"] = designation
        if "montant_total" not in current:
            qty = int(current.get("quantite_colis", 0))
            colis = int(current.get("colisage", 1))
            current["montant_total"] = round(
                float(current["prix_unitaire"]) * max(qty, 0) * max(colis, 1),
                2,
            )
        records.append(current)

    if not records:
        return pd.DataFrame(columns=[
            'nom',
            'codes',
            'numero_article',
            'qte_init',
            'prix_achat',
            'prix_vente',
            'tva',
            'tva_code',
            'montant_total_facture',
        ])


    normalised: list[dict[str, object]] = []

    for record in records:
        designation = str(record.get("nom", "")).strip()
        if not designation:
            continue

        ean = str(record.get("codes", "")).strip()
        article = str(record.get("numero_article", "")).strip()
        unit_price = _parse_decimal(record.get("prix_unitaire"))
        qty = _parse_int(record.get("quantite_colis")) or 0
        colis = _parse_int(record.get("colisage")) or 1
        total_units = max(qty, 0) * max(colis, 1)
        amount = _parse_decimal(record.get("montant_total"))
        tva_code = _normalise_tva_code(record.get("tva_code"))
        tva_value = _resolve_tva_value(tva_code, lookup, default_tva)

        if unit_price is None:
            continue

        sale_price = _ensure_margin(unit_price, None, margin_rate)
        montant_ht = round(unit_price * total_units, 2)
        montant_tva = round(montant_ht * (tva_value / 100.0), 2)
        montant_ttc = round(montant_ht + montant_tva, 2)

        normalised.append(
            {
                "nom": designation,
                "codes": ean,
                "numero_article": article,
                "regie": record.get("regie"),
                "volume_litre": round(float(record.get("volume_litre", 0.0)), 3),
                "vap": round(float(record.get("vap", 0.0)), 3),
                "poids_unitaire": round(float(record.get("poids_unitaire", 0.0)), 3),
                "quantite_colis": qty,
                "colisage": colis,
                "qte_init": total_units,
                "prix_achat": round(unit_price, 2),
                "prix_vente": sale_price if sale_price is not None else round(unit_price, 2),
                "prix_vente_minimum": sale_price if sale_price is not None else round(unit_price, 2),
                "tva": round(tva_value, 2),
                "tva_code": tva_code,
                "montant_ht": montant_ht,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc,
                "montant_total_facture": round(
                    amount if amount is not None else unit_price * total_units,
                    2,
                ),
            }
        )

    df = pd.DataFrame(normalised)
    if df.empty:
        return df
        
    desired_order: Iterable[str] = (
        "nom",
        "codes",
        "numero_article",
        "regie",
        "volume_litre",
        "vap",
        "poids_unitaire",
        "quantite_colis",
        "colisage",
        "qte_init",
        "prix_achat",
        "prix_vente",
        "prix_vente_minimum",
        "tva",
        "tva_code",
        "montant_ht",
        "montant_tva",
        "montant_ttc",
        "montant_total_facture",
    )
    available = [col for col in desired_order if col in df.columns]
    return df.loc[:, available]
