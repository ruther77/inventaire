"""Utility functions for restaurant services."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, Tuple

from sqlalchemy import text

from core.data_repository import get_engine
from backend.services.restaurant.constants import (
    CATEGORY_RULES,
    CATEGORY_GROUP_PRESETS,
    CREDIT_KEYWORDS,
    DEBIT_KEYWORDS,
    STOP_PREFIXES,
    HEADER_START_PREFIXES,
    DETAIL_PREFIXES,
)


@lru_cache(maxsize=1)
def _get_restaurant_entity_id() -> int:
    """Retourne l'entity_id finance associee au restaurant (code RESTO)."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id
                FROM finance_entities
                WHERE code = 'RESTO'
                ORDER BY is_active DESC, id ASC
                LIMIT 1
                """
            )
        ).fetchone()
        if row:
            return int(row.id)
        fallback = conn.execute(text("SELECT id FROM finance_entities ORDER BY id ASC LIMIT 1")).fetchone()
        if fallback:
            return int(fallback.id)
    raise RuntimeError("Aucune entite finance n'a ete trouvee (code RESTO manquant ?)")


def _safe_float(value: Any) -> float:
    """Convertit prudemment une valeur en float sans lever d'exception."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_amount(raw: str) -> float:
    """Transforme une chaine `1 234,56` en float Python."""
    return _safe_float(raw.replace(" ", "").replace(",", "."))


def _is_stop_line(line: str) -> bool:
    """Detecte les lignes systeme indiquant qu'on sort du bloc de transactions."""
    upper = line.upper()
    return any(upper.startswith(prefix) for prefix in STOP_PREFIXES)


def _looks_like_header_line(line: str) -> bool:
    """Identifie les debuts d'en-tetes (codes operation, postes bancaires...)."""
    upper = line.upper()
    return any(upper.startswith(prefix) for prefix in HEADER_START_PREFIXES)


def _is_detail_line(line: str) -> bool:
    """Reconnait les lignes de details qui completent l'en-tete d'operation."""
    upper = line.upper()
    if any(upper.startswith(prefix) for prefix in DETAIL_PREFIXES):
        return True
    cleaned = upper.replace(" ", "")
    return cleaned.isdigit()


def _normalize_description(parts: list[str]) -> str:
    """Concatene et nettoie les segments de description pour un mouvement."""
    text_val = " ".join(parts)
    return re.sub(r"\s+", " ", text_val).strip()


def _extract_descriptions(header_lines: list[str]) -> list[str]:
    """Regroupe les lignes extraites du PDF en descriptions lisibles."""
    descriptions: list[str] = []
    current: list[str] = []
    capturing = False
    for raw in header_lines:
        line = raw.strip()
        if not line:
            continue
        if _is_stop_line(line):
            if current:
                descriptions.append(_normalize_description(current))
                current = []
            capturing = False
            continue
        if _looks_like_header_line(line):
            if current:
                descriptions.append(_normalize_description(current))
            current = [line]
            capturing = True
            continue
        if capturing:
            if _is_detail_line(line):
                current.append(line)
            else:
                descriptions.append(_normalize_description(current))
                current = [line]
                capturing = True
    if current:
        descriptions.append(_normalize_description(current))
    return [desc for desc in descriptions if desc]


def _align_descriptions(descriptions: list[str], target_count: int) -> list[str]:
    """Ajuste le nombre d'intitules pour coller au nombre de montants trouves."""
    if target_count <= 0:
        return []
    if not descriptions:
        return [""] * target_count
    if len(descriptions) == target_count:
        return descriptions
    if len(descriptions) > target_count:
        drop = len(descriptions) - target_count
        trimmed = descriptions[drop:]
        if len(trimmed) < target_count:
            trimmed.extend([""] * (target_count - len(trimmed)))
        return trimmed
    padded = descriptions[:]
    padded.extend([""] * (target_count - len(descriptions)))
    return padded


def _get_grouping_preset(name: str | None) -> Tuple[str, Dict[str, Any]]:
    """Selectionne le prereglage de regroupement a utiliser pour les resumes."""
    if name and name in CATEGORY_GROUP_PRESETS:
        return name, CATEGORY_GROUP_PRESETS[name]
    return "default", CATEGORY_GROUP_PRESETS["default"]


def _resolve_group_name(categorie: str | None, entry_type: str, preset: Dict[str, Any]) -> str:
    """Mappe une categorie individuelle vers un libelle de regroupement."""
    cat = (categorie or "").strip()
    entry_type = entry_type or "Sortie"
    groups = preset.get("groups", {})
    for group_name, definition in groups.items():
        allowed_types = definition.get("types")
        categories = definition.get("categories") or ()
        keywords = definition.get("keywords") or ()
        if allowed_types and entry_type not in allowed_types:
            continue
        if cat and cat in categories:
            return group_name
        if keywords and any(keyword.upper() in cat.upper() for keyword in keywords):
            return group_name
    fallback = preset.get("fallback", {})
    if entry_type in fallback:
        return fallback[entry_type]
    return fallback.get("default", "Autres")


def _normalize_for_keyword(text_val: str) -> str:
    """Supprime la ponctuation pour effectuer des comparaisons robustes."""
    return re.sub(r"[^A-Z0-9]", "", text_val.upper())


def _keyword_matches(label_upper: str, normalized_label: str, keyword: str) -> bool:
    """Teste la presence d'un mot-cle dans une etiquette brute ou normalisee."""
    if not keyword:
        return False
    keyword_clean = keyword.upper().strip()
    keyword_trimmed = keyword_clean.replace("%", "")
    if keyword_trimmed and keyword_trimmed in label_upper:
        return True
    normalized_keyword = _normalize_for_keyword(keyword_trimmed)
    if normalized_keyword and normalized_keyword in normalized_label:
        return True
    return False


def _guess_category(label: str | None, entry_type: str) -> str | None:
    """Essaye de categoriser une ligne bancaire en se basant sur les mots-cles connues."""
    if not label:
        return "Encaissement" if entry_type == "Entree" else "Autres"
    upper = label.upper()
    normalized_label = _normalize_for_keyword(label)
    for keywords, category, allowed_types in CATEGORY_RULES:
        if allowed_types and entry_type not in allowed_types:
            continue
        if any(_keyword_matches(upper, normalized_label, keyword) for keyword in keywords):
            return category
    if entry_type == "Entree":
        return "Encaissement"
    return "Autres"


def _looks_like_credit(label: str) -> bool:
    """Renvoie True si le libelle ressemble a un encaissement (utile pour les releves PDF)."""
    label_upper = label.upper()
    if any(keyword in label_upper for keyword in CREDIT_KEYWORDS):
        return True
    if any(keyword in label_upper for keyword in DEBIT_KEYWORDS):
        return False
    return True


def _should_skip_line(line: str) -> bool:
    """Ignore les lignes vides ou les en-tetes parasites lors du parsing PDF."""
    if not line:
        return True
    return _is_stop_line(line)


def _ensure_depense_category(conn, tenant_id: int, nom: str | None) -> int | None:
    """Ensure a depense category exists, creating it if needed."""
    if not nom:
        return None
    normalized = nom.strip()
    if not normalized:
        return None
    row = conn.execute(
        text(
            """
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = :tenant AND UPPER(nom) = UPPER(:nom)
            """
        ),
        {"tenant": tenant_id, "nom": normalized},
    ).fetchone()
    if row:
        return row.id
    row = conn.execute(
        text(
            """
            INSERT INTO restaurant_depense_categories (tenant_id, nom)
            VALUES (:tenant, :nom)
            RETURNING id
            """
        ),
        {"tenant": tenant_id, "nom": normalized},
    ).fetchone()
    return int(row.id) if row else None
