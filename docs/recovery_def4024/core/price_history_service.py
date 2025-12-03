from __future__ import annotations  # Active l'évaluation différée des annotations

import logging  # Gestion du logging applicatif
import os  # Lecture des variables d'environnement
import re  # Expressions régulières pour nettoyage de texte
from datetime import datetime, timedelta, timezone  # Manipulation des dates et fuseaux
from typing import Iterable  # Typage pour les collections de codes

import pandas as pd  # DataFrames pour manipuler les historiques
from sqlalchemy import text  # Construction de requêtes SQL textuelles

from .data_repository import exec_sql, query_df  # Fonctions d'accès base pour lire/écrire

LOGGER = logging.getLogger(__name__)  # Logger du module
_TABLE_READY = False  # Flag interne indiquant si la table a été initialisée
_MARGIN_MULTIPLIER = 1.4  # Multiplicateur pour proposer un prix de vente
_MARGIN_ALERT_MIN = float(os.getenv("MARGIN_ALERT_MIN", "0.2"))  # Seuil de marge mini pour alerte (20% par défaut)
_STOCKOUT_REPEAT_MIN = int(os.getenv("STOCKOUT_REPEAT_MIN", "3"))  # Nb de mouvements sortie pour considérer une rupture répétée
_STOCKOUT_WINDOW_DAYS = int(os.getenv("STOCKOUT_WINDOW_DAYS", "45"))  # Fenêtre de détection des ruptures répétées


def _normalize_column_name(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(raw).strip().lower()).strip("_")  # Normalise un nom de colonne en snake_case


def _build_column_index(df: pd.DataFrame) -> dict[str, str]:
    index: dict[str, str] = {}  # Dictionnaire normalisé -> nom original
    for col in df.columns:  # Parcourt chaque colonne du DataFrame
        norm = _normalize_column_name(col)  # Normalise le nom
        index.setdefault(norm, col)  # Conserve la première occurrence rencontrée
    return index  # Retourne la table de correspondance


def _get_column(index: dict[str, str], candidates: list[str]) -> str | None:
    for candidate in candidates:  # Parcourt les noms candidats
        key = _normalize_column_name(candidate)  # Normalise le candidat
        if key in index:  # Si présent dans l'index
            return index[key]  # Retourne le nom original associé
    return None  # Aucun match trouvé


def _to_float(value) -> float | None:
    if value is None:  # Pas de valeur
        return None  # Retourne None
    if isinstance(value, (int, float)):  # Déjà numérique
        return float(value)  # Conversion simple
    text_value = str(value).strip()  # Convertit en chaîne et enlève les espaces
    if not text_value:  # Chaîne vide
        return None  # Retourne None
    normalized = text_value.replace(",", ".")  # Remplace la virgule par un point
    normalized = re.sub(r"[^0-9.\-]", "", normalized)  # Supprime tout caractère non numérique
    if not normalized:  # Si rien après nettoyage
        return None  # Retourne None
    try:
        return float(normalized)  # Tente la conversion en float
    except ValueError:  # Conversion échouée
        return None  # Retourne None


def _parse_facture_date(value, fallback: datetime) -> datetime:
    if value is None or (isinstance(value, str) and not value.strip()):  # Valeur vide
        return fallback  # Utilise la date par défaut
    try:
        ts = pd.to_datetime(value, dayfirst=True, errors="coerce")  # Parse en tenant compte du format jour/mois
    except Exception:  # pragma: no cover - défense
        ts = None  # Parsing impossible
    if ts is None or pd.isna(ts):  # Résultat invalide
        return fallback  # Retourne la date fallback
    dt = ts.to_pydatetime()  # Convertit en datetime natif
    if dt.tzinfo is None:  # Pas de fuseau
        return dt.replace(tzinfo=timezone.utc)  # Force UTC
    return dt.astimezone(timezone.utc)  # Convertit en UTC


def _normalize_code(value) -> str | None:
    if value is None:  # Aucun code
        return None  # Retourne None
    text_value = str(value).strip()  # Convertit en chaîne et nettoie
    text_value = text_value.replace(" ", "")  # Retire les espaces internes
    return text_value or None  # Retourne la chaîne ou None si vide


def _ensure_table() -> None:
    global _TABLE_READY  # Référence le flag global
    if _TABLE_READY:  # Si déjà initialisé
        return  # Rien à faire

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS produits_price_history (
            id SERIAL PRIMARY KEY,
            tenant_id INT NOT NULL DEFAULT 1,
            code TEXT NOT NULL,
            fournisseur TEXT,
            prix_achat NUMERIC(12, 4) NOT NULL,
            quantite NUMERIC(12, 3),
            facture_date TIMESTAMPTZ NOT NULL DEFAULT now(),
            source_context TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "ALTER TABLE produits_price_history ADD COLUMN IF NOT EXISTS tenant_id INT NOT NULL DEFAULT 1",
        "CREATE INDEX IF NOT EXISTS idx_price_history_code ON produits_price_history (tenant_id, code)",
        "CREATE INDEX IF NOT EXISTS idx_price_history_date ON produits_price_history (tenant_id, facture_date DESC)",
    ]  # Script DDL idempotent pour créer/ajouter colonnes et indexes

    try:
        for statement in ddl_statements:  # Exécute chaque instruction DDL
            exec_sql(text(statement))  # Envoie la requête à la base
    except Exception as exc:  # pragma: no cover - dépendance base
        LOGGER.warning("Impossible d'initialiser la table d'historique prix: %s", exc)  # Logue l'échec
        return  # Abandonne l'initialisation

    _TABLE_READY = True  # Marque la table comme prête


def _update_sale_prices(codes: set[str], *, tenant_id: int) -> None:
    if not codes:  # Aucun code à traiter
        return  # Sort
    placeholders = {f"code_{idx}": code for idx, code in enumerate(codes)}  # Prépare les paramètres pour clause IN
    in_clause = ", ".join(f":{key}" for key in placeholders)  # Construit la liste de placeholders
    sql = text(
        f"""
        WITH latest AS (
            SELECT pb.produit_id, MAX(ph.prix_achat) AS max_price
            FROM produits_price_history ph
            JOIN produits_barcodes pb ON pb.code = ph.code
            WHERE ph.code IN ({in_clause})
              AND ph.tenant_id = :tenant_id
              AND pb.tenant_id = :tenant_id
            GROUP BY pb.produit_id
        ),
        enriched AS (
            SELECT
                l.produit_id,
                l.max_price,
                COALESCE(p.tva, 0) AS tva
            FROM latest l
            JOIN produits p ON p.id = l.produit_id
            WHERE p.tenant_id = :tenant_id
        )
        UPDATE produits p
        SET prix_vente = ROUND(enriched.max_price * :margin_multiplier * (1 + enriched.tva / 100), 4)
        FROM enriched
        WHERE p.id = enriched.produit_id AND p.tenant_id = :tenant_id
        """
    )  # Requête qui met à jour le prix de vente à partir du dernier prix achat et TVA
    params = {**placeholders, "margin_multiplier": _MARGIN_MULTIPLIER, "tenant_id": int(tenant_id)}  # Paramètres SQL
    try:
        exec_sql(sql, params)  # Exécute la mise à jour des prix
    except Exception as exc:  # pragma: no cover - dépendance base
        LOGGER.warning("Impossible de mettre à jour le prix de vente: %s", exc)  # Logue l'échec


def record_price_history(
    df: pd.DataFrame,
    *,
    supplier: str | None = None,
    context: str | None = None,
    invoice_date: datetime | None = None,
    tenant_id: int = 1,
) -> None:
    """Enregistre un instantané des prix d'achat extraits d'une facture."""  # Docstring métier

    # Le flux métier : normalisation des colonnes, conversions prix/quantité/date,
    # insertion de l'historique puis recalcul d'un prix de vente conseillé.

    if not isinstance(df, pd.DataFrame) or df.empty:  # Valide l'entrée
        return  # Rien à enregistrer

    _ensure_table()  # Prépare la table si besoin
    if not _TABLE_READY:  # Si l'init a échoué
        return  # Sort sans traiter

    invoice_dt = invoice_date.astimezone(timezone.utc) if invoice_date else datetime.now(timezone.utc)  # Date facture
    context_label = context or "Importation"  # Contexte d'origine
    column_index = _build_column_index(df)  # Index normalisé des colonnes
    code_column = _get_column(column_index, ["code", "ean", "codes", "barcode"])  # Colonne code produit
    supplier_column = _get_column(column_index, ["fournisseur", "supplier", "on_le_marquera"])  # Colonne fournisseur
    price_column = _get_column(column_index, ["prix_achat", "prix_unitaire", "price", "prix_unitaire_ht"])  # Colonne prix
    quantity_column = _get_column(
        column_index,
        ["quantite", "quantite_recue", "qte_init", "colisage_x_cont_unit_l", "quantite_totale"],
    )  # Colonne quantité principale
    colisage_column = _get_column(column_index, ["colisage", "nb_colis"])  # Colonne colisage
    contenance_column = _get_column(column_index, ["cont_unit_l", "cont_unit", "contenance", "contenance_unit_l"])  # Colonne contenance
    facture_column = _get_column(column_index, ["facture_date", "date_facture", "date"])  # Colonne date facture

    payloads: list[dict[str, object]] = []  # Lignes à insérer
    observed_codes: set[str] = set()  # Codes collectés pour recalculer les prix de vente

    for record in df.to_dict(orient="records"):  # Itère sur chaque ligne de la facture
        raw_code = record.get(code_column) if code_column else record.get("code")  # Récupère le code
        code_value = _normalize_code(raw_code)  # Normalise le code
        if not code_value:  # Code manquant ou invalide
            continue  # Ignore la ligne

        price_value = _to_float(record.get(price_column)) if price_column else _to_float(record.get("prix_achat"))  # Prix
        if price_value is None or price_value <= 0:  # Prix non valide
            continue  # Ignore la ligne

        quantity_value = None  # Initialise la quantité
        if quantity_column:  # Si colonne quantité identifiée
            quantity_value = _to_float(record.get(quantity_column))  # Convertit la quantité
        if quantity_value is None and colisage_column and contenance_column:  # Fallback colisage * contenance
            colisage_value = _to_float(record.get(colisage_column))  # Colisage
            contenance_value = _to_float(record.get(contenance_column))  # Contenance
            if colisage_value is not None and contenance_value is not None:  # Deux valeurs présentes
                quantity_value = colisage_value * contenance_value  # Calcule quantité totale
        if quantity_value is None and colisage_column:  # Fallback sur colisage seul
            quantity_value = _to_float(record.get(colisage_column))  # Utilise colisage
        if quantity_value is None and contenance_column:  # Fallback sur contenance seule
            quantity_value = _to_float(record.get(contenance_column))  # Utilise contenance
        if quantity_value is None:  # Dernier recours
            quantity_value = _to_float(record.get("quantite"))  # Cherche une colonne générique

        supplier_value = record.get(supplier_column) if supplier_column else record.get("fournisseur")  # Fournisseur brut
        if isinstance(supplier_value, str):  # Si chaîne
            supplier_value = supplier_value.strip()  # Nettoie les espaces
        supplier_name = supplier_value or (supplier or "").strip() or None  # Choisit le fournisseur final

        facture_value = record.get(facture_column) if facture_column else record.get("facture_date")  # Date brute
        facture_dt = _parse_facture_date(facture_value, invoice_dt)  # Date normalisée

        payloads.append(
            {
                "code": code_value,
                "fournisseur": supplier_name,
                "prix_achat": round(price_value, 4),
                "quantite": quantity_value,
                "facture_date": facture_dt,
                "source_context": context_label,
                "tenant_id": int(tenant_id),
            }
        )  # Ajoute la ligne prête pour insertion
        observed_codes.add(code_value)  # Stocke le code pour mise à jour des prix de vente

    if not payloads:  # Si aucune ligne valide n'a été collectée
        return  # Sort sans écrire

    insert_sql = text(
        """
        INSERT INTO produits_price_history (
            code, fournisseur, prix_achat, quantite, facture_date, source_context, tenant_id
        )
        VALUES (
            :code, :fournisseur, :prix_achat, :quantite, :facture_date, :source_context, :tenant_id
        )
        """
    )  # Requête batch d'insertion dans l'historique

    try:
        exec_sql(insert_sql, payloads)  # Exécute l'insertion en lot
        _update_sale_prices(observed_codes, tenant_id=int(tenant_id))  # Met à jour les prix de vente recommandés
    except Exception as exc:  # pragma: no cover - dépendance base
        LOGGER.warning("Échec d'enregistrement de l'historique prix: %s", exc)  # Logue l'erreur


def fetch_price_history(
    *,
    produit_id: int | None = None,
    code: str | None = None,
    search: str | None = None,
    supplier: str | None = None,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    limit: int = 500,
    tenant_id: int = 1,
) -> pd.DataFrame:
    """Récupère l'historique des prix d'achat selon différents filtres."""  # Docstring de lecture

    # Utilisée par l'API pour exposer les derniers prix connus ; joint latéralement
    # le produit par code, d'où le LEFT JOIN LATERAL et les index associés.

    _ensure_table()  # Vérifie l'initialisation de la table
    if not _TABLE_READY:  # Table non prête
        return pd.DataFrame(
            columns=[
                "id",
                "produit_id",
                "code",
                "nom",
                "fournisseur",
                "prix_achat",
                "quantite",
                "montant",
                "facture_date",
                "source_context",
            ]
        )  # Retourne un DataFrame vide structuré

    filters: list[str] = []  # Liste des prédicats dynamiques
    params: dict[str, object] = {"limit": int(max(1, limit)), "tenant_id": int(tenant_id)}  # Paramètres de base
    params["margin_floor"] = float(max(0.0, _MARGIN_ALERT_MIN))
    params["stockout_repeat_min"] = int(max(1, _STOCKOUT_REPEAT_MIN))
    params["recent_window_start"] = datetime.utcnow() - timedelta(days=max(1, _STOCKOUT_WINDOW_DAYS))

    if produit_id:  # Filtre par produit
        filters.append(
            "EXISTS (SELECT 1 FROM produits_barcodes pb "
            "WHERE pb.code = ph.code AND pb.produit_id = :produit_id AND pb.tenant_id = :tenant_id)"
        )  # S'assure que le code correspond à ce produit
        params["produit_id"] = int(produit_id)  # Paramètre produit
    if code:  # Filtre par code texte
        filters.append("ph.code ILIKE :code")  # Clause LIKE
        params["code"] = f"%{code.strip()}%"  # Paramètre LIKE
    if search:  # Filtre recherche générique
        filters.append("(ph.code ILIKE :search OR prod_data.nom ILIKE :search)")  # Cherche dans code/nom
        params["search"] = f"%{search.strip()}%"  # Paramètre de recherche
    if supplier:  # Filtre fournisseur
        filters.append("ph.fournisseur ILIKE :supplier")  # Clause fournisseur
        params["supplier"] = f"%{supplier.strip()}%"  # Paramètre LIKE fournisseur
    if date_start:  # Filtre date minimale
        filters.append("ph.facture_date >= :date_start")  # Clause date début
        params["date_start"] = date_start  # Paramètre début
    if date_end:  # Filtre date maximale
        filters.append("ph.facture_date <= :date_end")  # Clause date fin
        params["date_end"] = date_end + timedelta(days=1)  # Inclut toute la journée de fin

    predicates = ["ph.tenant_id = :tenant_id"]  # Toujours filtrer par tenant
    predicates.extend(filters)  # Ajoute les filtres dynamiques
    where_clause = " AND ".join(predicates)  # Construit la clause WHERE complète
    sql = f"""
        WITH filtered AS (
            SELECT
                ph.*,
                LAG(ph.prix_achat) OVER (
                    PARTITION BY ph.code
                    ORDER BY ph.facture_date, ph.created_at
                ) AS prev_prix_achat,
                LAG(ph.facture_date) OVER (
                    PARTITION BY ph.code
                    ORDER BY ph.facture_date, ph.created_at
                ) AS prev_facture_date
            FROM produits_price_history ph
            WHERE {where_clause}
        ),
        sorties_recentes AS (
            SELECT produit_id, COUNT(*) AS sorties_recent
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND date_mvt >= :recent_window_start
              AND type = 'SORTIE'
            GROUP BY produit_id
        )
        SELECT
            f.id,
            f.code,
            f.fournisseur,
            f.prix_achat,
            f.prev_prix_achat AS prev_prix_achat,
            f.prev_facture_date,
            (f.prix_achat - f.prev_prix_achat) AS delta_prix,
            CASE
                WHEN f.prev_prix_achat IS NOT NULL AND f.prev_prix_achat <> 0
                    THEN ((f.prix_achat - f.prev_prix_achat) / f.prev_prix_achat) * 100
                ELSE NULL
            END AS delta_pct,
            f.quantite,
            f.facture_date,
            f.source_context,
            f.created_at,
            prod_data.produit_id,
            prod_data.nom,
            prod_data.tva,
            prod_data.prix_vente,
            prod_data.stock_actuel,
            prod_data.seuil_alerte,
            prod_data.ean,
            prod_data.marge_unitaire,
            prod_data.marge_pct,
            prod_data.margin_alert,
            prod_data.stock_alert,
            prod_data.stockout_repeated,
            prod_data.stockout_events
        FROM filtered f
        LEFT JOIN LATERAL (
            SELECT
                p.id AS produit_id,
                p.nom,
                p.tva,
                p.prix_vente,
                p.stock_actuel,
                p.seuil_alerte,
                p.ean,
                CASE
                    WHEN p.prix_vente > 0 THEN (p.prix_vente - f.prix_achat)
                    ELSE NULL
                END AS marge_unitaire,
                CASE
                    WHEN p.prix_vente > 0 THEN ((p.prix_vente - f.prix_achat) / p.prix_vente) * 100
                    ELSE NULL
                END AS marge_pct,
                CASE
                    WHEN p.prix_vente > 0 AND ((p.prix_vente - f.prix_achat) / p.prix_vente) < :margin_floor
                        THEN TRUE ELSE FALSE END AS margin_alert,
                CASE WHEN p.stock_actuel <= COALESCE(p.seuil_alerte, 0) THEN TRUE ELSE FALSE END AS stock_alert,
                COALESCE(sr.sorties_recent, 0) AS stockout_events,
                CASE
                    WHEN p.stock_actuel <= COALESCE(p.seuil_alerte, 0)
                         AND COALESCE(sr.sorties_recent, 0) >= :stockout_repeat_min
                        THEN TRUE ELSE FALSE
                END AS stockout_repeated
            FROM produits_barcodes pb
            JOIN produits p ON p.id = pb.produit_id
            LEFT JOIN sorties_recentes sr ON sr.produit_id = p.id
            WHERE pb.code = f.code AND pb.tenant_id = :tenant_id
            ORDER BY pb.is_principal DESC NULLS LAST, pb.created_at ASC
            LIMIT 1
        ) AS prod_data ON TRUE
        ORDER BY f.facture_date DESC
        LIMIT :limit
    """  # Requête principale enrichie (deltas + marges + alertes)

    try:
        df = query_df(text(sql), params=params)  # Exécute la requête et retourne un DataFrame
    except Exception as exc:  # pragma: no cover - dépendance base
        LOGGER.warning("Impossible de lire l'historique prix: %s", exc)  # Logue l'échec
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur

    if df.empty:  # Aucun résultat
        return df  # Retourne tel quel

    df = df.replace({"": pd.NA})  # Remplace les chaînes vides par NA
    if "produit_id" in df.columns:  # Harmonise le type de produit_id
        df["produit_id"] = pd.to_numeric(df["produit_id"], errors="coerce").astype("Int64")  # Convertit en int nullable
    else:
        df["produit_id"] = pd.Series(dtype="Int64")  # Crée une colonne vide cohérente

    if "prix_achat" in df.columns:  # Harmonise le prix
        df["prix_achat"] = pd.to_numeric(df["prix_achat"], errors="coerce")  # Convertit en float
    else:
        df["prix_achat"] = 0.0  # Valeur par défaut

    if "quantite" in df.columns:  # Harmonise la quantité
        df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")  # Convertit en numérique
    else:
        df["quantite"] = pd.NA  # Valeur manquante

    df["montant"] = df["prix_achat"] * df["quantite"].fillna(1)  # Calcule le montant total avec fallback quantité=1
    numeric_candidates = ["delta_prix", "delta_pct", "prev_prix_achat", "marge_unitaire", "marge_pct", "prix_vente", "stock_actuel", "seuil_alerte"]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    bool_cols = ["margin_alert", "stock_alert", "stockout_repeated"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    if "stockout_events" in df.columns:
        df["stockout_events"] = pd.to_numeric(df["stockout_events"], errors="coerce").fillna(0).astype(int)

    df["facture_date"] = pd.to_datetime(df["facture_date"])  # Convertit en datetime
    return df  # Retourne le DataFrame enrichi


def fetch_latest_price_per_code(
    *,
    tenant_id: int = 1,
    codes: Iterable[str] | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Récupère la dernière entrée par code pour le tenant demandé."""  # Docstring lecture dernier prix

    filters: list[str] = ["ph.tenant_id = :tenant_id"]  # Filtre tenant obligatoire
    params: dict[str, object] = {"tenant_id": int(tenant_id), "limit": int(max(1, limit))}  # Paramètres de base
    if codes:  # Filtre optionnel par liste de codes
        placeholders = ", ".join(f":code_{idx}" for idx in range(len(codes)))  # Placeholders IN
        for idx, code in enumerate(codes):  # Prépare les paramètres code
            params[f"code_{idx}"] = str(code).strip()  # Nettoie et stocke
        filters.append(f"ph.code IN ({placeholders})")  # Ajoute le filtre IN

    where_clause = " AND ".join(filters)  # Construit la clause WHERE
    sql = f"""
        WITH ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY ph.code
                       ORDER BY ph.facture_date DESC, ph.created_at DESC
                   ) AS rn
            FROM produits_price_history ph
            WHERE {where_clause}
        )
        SELECT
            code,
            fournisseur,
            prix_achat,
            quantite,
            facture_date,
            source_context,
            created_at
        FROM ranked
        WHERE rn = 1
        ORDER BY facture_date DESC
        LIMIT :limit
    """  # Requête renvoyant la dernière entrée par code

    try:
        return query_df(text(sql), params=params)  # Exécute et retourne le DataFrame
    except Exception as exc:  # pragma: no cover - dépendance base
        LOGGER.warning("Impossible de lire le dernier prix par code: %s", exc)  # Logue l'échec
        return pd.DataFrame()  # Retourne un DataFrame vide


def fetch_price_history_for_product(
    *,
    produit_id: int | None = None,
    code: str | None = None,
    limit: int = 120,
    tenant_id: int = 1,
) -> pd.DataFrame:
    """Retourne l'historique pour un produit ou un code spécifique."""  # Docstring façade de convenance

    return fetch_price_history(
        produit_id=produit_id,
        code=code,
        limit=limit,
        tenant_id=tenant_id,
    )  # Délègue à la fonction principale avec filtres spécialisés
