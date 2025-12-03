import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


SOURCE_PATH = Path("docs/articles_prix_ttc_cond_inclus_clean.csv")
EXISTING_PATH = Path("db/Produit.csv")
OUTPUT_PATH = Path("docs/articles_prix_ttc_cond_inclus_prepared.csv")


def _to_ascii_upper(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.upper()


def clean_label(text: str) -> str:
    """Normalize label for insertion (uppercase, ascii, tidy packs/units)."""
    label = _to_ascii_upper(text)
    label = label.replace(",", ".")
    label = re.sub(r"[\[\]{}()]", " ", label)
    label = re.sub(
        r"(\d+)\s*[X]\s*(\d+[.,]?\d*\s*(?:KG|G|CL|L|ML)?)",
        lambda m: f"{m.group(1)}X{m.group(2).replace(' ', '')}",
        label,
    )
    label = re.sub(r"[^A-Z0-9.]+", " ", label)
    label = re.sub(r"\s+", " ", label).strip()
    return label


def parse_pack(label: str):
    """Extract simple pack info: (count, size, unit)."""
    m = re.search(r"(\d+)[X]\s*(\d+(?:\.\d+)?)(KG|G|L|CL|ML|GR|PCS)", label)
    if m:
        return int(m.group(1)), float(m.group(2)), m.group(3)
    m = re.search(r"(\d+(?:\.\d+)?)(?:\s*)(KG|G|L|CL|ML|GR|PCS)\b", label)
    if m:
        return 1, float(m.group(1)), m.group(2)
    return None, None, None


def base_key(text: str) -> str:
    """Simplified key used for matching similar products (drops pack sizes)."""
    label = clean_label(text)
    label = re.sub(r"\b\d+X\d+[A-Z0-9.]*\b", " ", label)
    label = re.sub(r"\b\d+[.,]?\d*(?:KG|G|CL|L|ML)\b", " ", label)
    label = re.sub(r"\b\d+[.,]?\d*\b", " ", label)
    label = re.sub(r"\s+", " ", label).strip()
    return label


def load_existing() -> pd.DataFrame:
    df = pd.read_csv(EXISTING_PATH)
    df["nom_clean"] = df["nom"].map(clean_label)
    df["base_key"] = df["nom"].map(base_key)
    packs = df["nom_clean"].map(parse_pack)
    df[["pack_count", "pack_size", "pack_unit"]] = pd.DataFrame(packs.tolist(), index=df.index)
    return df


def build_token_index(base_series: pd.Series) -> dict[str, set[int]]:
    token_index: dict[str, set[int]] = {}
    for idx, value in base_series.items():
        for token in value.split():
            token_index.setdefault(token, set()).add(idx)
    return token_index


def best_fuzzy_match(new_base: str, candidates: set[int], existing_df: pd.DataFrame) -> tuple[int | None, float]:
    best_idx = None
    best_score = 0.0
    for idx in candidates:
        score = SequenceMatcher(None, new_base, existing_df.at[idx, "base_key"]).ratio()
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx, best_score


def prepare():
    new_df = pd.read_csv(SOURCE_PATH)
    existing_df = load_existing()

    norm_lookup: dict[str, list[str]] = {}
    base_lookup: dict[str, list[str]] = {}
    for _, row in existing_df.iterrows():
        norm_lookup.setdefault(row["nom_clean"], []).append(row["nom"])
        base_lookup.setdefault(row["base_key"], []).append(row["nom"])

    token_index = build_token_index(existing_df["base_key"])

    rows = []
    for _, row in new_df.iterrows():
        raw = row["Nom"]
        price = row["Prix_TTC"]
        nom_clean = clean_label(raw)
        base = base_key(raw)
        match_type = "none"
        match_score = 0.0
        matched_nom = ""
        matched_pack = (None, None, None)

        if nom_clean in norm_lookup:
            match_type = "exact_norm"
            match_score = 1.0
            matched_nom = norm_lookup[nom_clean][0]
        elif base and base in base_lookup:
            match_type = "exact_base"
            match_score = 1.0
            matched_nom = base_lookup[base][0]
        elif base:
            tokens = base.split()
            candidate_idxs: set[int] = set()
            for token in tokens:
                candidate_idxs.update(token_index.get(token, ()))
            if not candidate_idxs and tokens:
                candidate_idxs = set(range(len(existing_df)))
            if candidate_idxs:
                best_idx, score = best_fuzzy_match(base, candidate_idxs, existing_df)
                if best_idx is not None:
                    match_type = "fuzzy_base"
                    match_score = score
                    matched_nom = existing_df.at[best_idx, "nom"]
                    matched_pack = (
                        existing_df.at[best_idx, "pack_count"],
                        existing_df.at[best_idx, "pack_size"],
                        existing_df.at[best_idx, "pack_unit"],
                    )

        pack_info = parse_pack(nom_clean)
        packaging_diff = False
        if match_type != "none" and pack_info != (None, None, None):
            packaging_diff = pack_info != matched_pack

        is_new = match_score < 0.86 or packaging_diff
        rows.append(
            {
                "nom_original": raw,
                "nom_clean": nom_clean,
                "prix_ttc": price,
                "base_key": base,
                "matched_nom_bdd": matched_nom,
                "match_type": match_type,
                "match_score": round(match_score, 3),
                "pack_count": pack_info[0],
                "pack_size": pack_info[1],
                "pack_unit": pack_info[2],
                "matched_pack_count": matched_pack[0],
                "matched_pack_size": matched_pack[1],
                "matched_pack_unit": matched_pack[2],
                "packaging_diff": packaging_diff,
                "is_new": is_new,
            }
        )

    output_df = pd.DataFrame(rows)
    output_df.to_csv(OUTPUT_PATH, index=False)

    summary = output_df["is_new"].value_counts()
    print("Fichier genere:", OUTPUT_PATH)
    print("Nouveaux produits potentiels:", int(summary.get(True, 0)))
    print("Correspondances probables:", int(summary.get(False, 0)))


if __name__ == "__main__":
    prepare()
