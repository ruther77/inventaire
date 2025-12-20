# inventory_service.py  # Module de services pour les stocks (ventes, réceptions, tickets)
from collections import defaultdict  # Fournit un dict avec valeurs par défaut
from datetime import datetime, date, time, timezone  # Gestion des horodatages
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP  # Décimaux précis et arrondis
from typing import Iterable  # Typage des collections

import pandas as pd  # Manipulation de DataFrames pour les factures

from .data_repository import get_engine, query_df  # Accès au moteur et requêtes SQL
from . import inventory_costing  # Gestion des couches de coûts
from .pdf_utils import (
    render_receipt_pdf,
    sanitize_receipt_text,
    format_currency_line,
    format_quantity,
)
from sqlalchemy import text, exc as sa_exc  # Requêtes SQL textuelles et exceptions SQLAlchemy


def _as_decimal(value, default: str = "0") -> Decimal:
    """Safely convert any value to Decimal while handling errors."""  # Docstring conversion sûre

    try:  # Tente la conversion en Decimal
        return Decimal(str(value))  # Conversion via représentation chaîne
    except (InvalidOperation, TypeError, ValueError):  # Cas de conversion invalide
        return Decimal(default)  # Retourne la valeur par défaut


def _normalise_quantity(value) -> Decimal:
    """Convertit n'importe quelle quantité en Decimal positif."""  # Docstring pour normalisation
    try:  # Tente de convertir
        qty = Decimal(str(value))  # Conversion en Decimal
    except (InvalidOperation, TypeError, ValueError):  # Conversion échouée
        return Decimal("0")  # Retourne zéro

    if qty.is_nan() or qty <= 0:  # Filtre NaN ou valeurs négatives
        return Decimal("0")  # Retourne zéro

    return qty  # Quantité normalisée


def process_sale_transaction(
    cart: list,
    username: str,
    *,
    tenant_id: int = 1,
) -> tuple[bool, str | None, dict[str, bytes] | None]:
    """Enregistre une vente en décrémentant le stock et en traçant les mouvements."""  # Docstring vente

    # Args:
    #     cart: liste d'articles issus du panier (doit contenir au moins les clés ``id`` et ``qty``).
    #     username: nom d'utilisateur Streamlit effectuant la vente.
    #
    # Returns:
    #     Tuple (succès, message, reçu). En cas d'échec, le reçu vaut ``None``.
    if not cart:  # Panier vide
        return False, "Le panier est vide, aucune vente n'a été effectuée.", None  # Échec immédiat

    # Agrégation par produit pour éviter les insertions multiples dans mouvements_stock.
    aggregated: dict[int, dict[str, Decimal | str]] = defaultdict(
        lambda: {
            "qty": Decimal("0"),
            "label": None,
            "unit_price": Decimal("0"),
            "tva_rate": Decimal("0"),
        }
    )  # Structure des lignes agrégées

    for raw_item in cart:  # Parcourt chaque article du panier
        try:  # Validation de l'identifiant produit
            pid = int(raw_item["id"])  # Convertit l'id en entier
        except (KeyError, TypeError, ValueError):  # Erreur d'accès ou de conversion
            return False, "Un article du panier est invalide (identifiant manquant).", None  # Échec

        qty = _normalise_quantity(raw_item.get("qty"))  # Normalise la quantité
        if qty <= 0:  # Ignore les quantités nulles ou négatives
            continue  # Passe à l'article suivant

        aggregated_item = aggregated[pid]  # Récupère la ligne agrégée pour ce produit
        aggregated_item["qty"] = aggregated_item["qty"] + qty  # Cumule la quantité
        aggregated_item["label"] = raw_item.get("nom") or f"Produit {pid}"  # Libellé affiché

        unit_price = _as_decimal(raw_item.get("prix_vente"))  # Prix de vente unitaire
        tva_rate = _as_decimal(raw_item.get("tva"))  # Taux de TVA

        if aggregated_item["unit_price"] == 0 and unit_price > 0:  # Premier prix valide trouvé
            aggregated_item["unit_price"] = unit_price  # Affecte le prix unitaire

        if aggregated_item["tva_rate"] == 0 and tva_rate >= 0:  # Premier taux valide trouvé
            aggregated_item["tva_rate"] = tva_rate  # Affecte le taux de TVA

    if not aggregated:  # Si aucune ligne n'a été retenue
        return False, "Toutes les lignes du panier ont une quantité nulle.", None  # Échec

    eng = get_engine()  # Récupère le moteur SQL

    try:  # Transaction de vente
        with eng.begin() as conn:  # Démarre une transaction
            # On liste les produits introuvables ou à stock insuffisant avant toute insertion.
            missing_products: list[int] = []  # Produits absents
            insufficient: list[str] = []  # Produits à stock insuffisant

            for pid, item in aggregated.items():  # Parcourt chaque produit agrégé
                stock_row = conn.execute(
                    text("SELECT stock_actuel FROM produits WHERE id = :pid AND tenant_id = :tenant_id FOR UPDATE"),
                    {"pid": pid, "tenant_id": int(tenant_id)},
                ).fetchone()  # Verrouille la ligne produit

                if stock_row is None:  # Produit introuvable
                    missing_products.append(pid)  # Ajoute à la liste
                    continue  # Passe au produit suivant

                current_stock = Decimal(str(stock_row[0] or 0))  # Stock actuel
                if current_stock < item["qty"]:  # Stock insuffisant
                    insufficient.append(
                        f"{item['label']} (stock {current_stock} < vente {item['qty']})"
                    )  # Note le message

            if missing_products:  # Si des produits manquent
                return False, f"Produits introuvables: {', '.join(map(str, missing_products))}.", None  # Échec

            if insufficient:  # Si stock insuffisant
                return (
                    False,
                    "Stock insuffisant: " + ", ".join(insufficient),
                    None,
                )  # Échec avec détails

            ordered_items = list(aggregated.items())  # Fige l'ordre
            movements_payload = []  # Liste des payloads mouvements
            for pid, item in ordered_items:  # Construit les payloads d'insertion
                movements_payload.append(
                    {
                        "pid": pid,
                        "qty": item["qty"],
                        "source": f"Vente par {username or 'inconnu'}",
                        "tenant_id": int(tenant_id),
                    }
                )  # Données pour mouvements_stock

            result = conn.execute(
                text(
                    """
                    INSERT INTO mouvements_stock (produit_id, type, quantite, source, tenant_id)
                    VALUES (:pid, 'SORTIE', :qty, :source, :tenant_id)
                    RETURNING id
                    """
                ),
                movements_payload,
            )  # Insère les mouvements de sortie
            result.fetchall()  # consume to satisfy DB-API

            # Mise à jour explicite du stock (sous verrou) pour chaque mouvement.
            for payload in movements_payload:
                conn.execute(
                    text(
                        """
                        UPDATE produits
                        SET stock_actuel = stock_actuel - :qty,
                            updated_at = now()
                        WHERE id = :pid AND tenant_id = :tenant_id
                        """
                    ),
                    {
                        "pid": payload["pid"],
                        "qty": payload["qty"],
                        "tenant_id": payload["tenant_id"],
                    },
                )  # Décrémente le stock

            for pid, item in ordered_items:  # Consume les couches de coût FIFO
                inventory_costing.consume_layers(
                    conn,
                    tenant_id=int(tenant_id),
                    product_id=pid,
                    quantity=item["qty"],
                )  # Débit des couches de coûts

        receipt = _build_sale_receipt(aggregated, username)  # Génère le ticket PDF
        return True, None, receipt  # Succès

    except sa_exc.IntegrityError as exc:  # Conflits ou contraintes en base
        return False, f"Erreur d'intégrité lors de l'enregistrement de la vente: {exc.orig}", None  # Échec avec message
    except ValueError as exc:  # Erreurs de validation
        return False, str(exc), None  # Échec
    except Exception as exc:  # pragma: no cover - sécurité supplémentaire pour la session Streamlit
        return False, f"Erreur inattendue lors de la vente: {exc}", None  # Échec générique


def _build_sale_receipt(aggregated: dict[int, dict[str, Decimal | str]], username: str | None) -> dict[str, bytes]:
    """Construit un ticket PDF minimaliste à partir des lignes agrégées."""  # Docstring ticket

    #     Le ticket est ensuite encodé en base64 par l’API FastAPI si la vente réussit,
    #     pour affichage dans la SPA.

    timestamp = datetime.now()  # Horodatage du ticket
    header_lines = [
        "LINCONTOURNABLE MARKET",
        "Epicerie urbaine",
        "83 RUE DES POISSONNIERES 75018 PARIS",
        "RCS PARIS 922478706",
        "",
        f"Ticket genere le {timestamp.strftime('%d/%m/%Y %H:%M:%S')}",
        f"Caissier: {username or 'inconnu'}",
        "",
        "Articles vendus:",
    ]  # En-tête du ticket

    total_ht = Decimal("0")  # Total hors taxes
    total_tva = Decimal("0")  # Total TVA
    total_ttc = Decimal("0")  # Total TTC
    detail_lines: list[str] = []  # Lignes de détail

    for item in aggregated.values():  # Parcourt les lignes agrégées
        qty = item.get("qty", Decimal("0")) or Decimal("0")  # Quantité vendue
        if qty <= 0:  # Ignore quantités nulles
            continue  # Poursuit

        label = sanitize_receipt_text(item.get("label") or "Produit")  # Libellé nettoyé
        unit_price = _as_decimal(item.get("unit_price"), "0")  # Prix unitaire
        tva_rate = _as_decimal(item.get("tva_rate"), "0")  # Taux de TVA

        line_total = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # Montant TTC ligne
        if tva_rate > 0:  # Si TVA > 0
            divisor = Decimal("1") + (tva_rate / Decimal("100"))  # Coefficient pour extraire HT
            line_ht = (line_total / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # Montant HT
        else:  # Pas de TVA
            line_ht = line_total  # Montant HT = TTC
        line_tva = (line_total - line_ht).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # TVA calculée

        total_ht += line_ht  # Cumul HT
        total_tva += line_tva  # Cumul TVA
        total_ttc += line_total  # Cumul TTC

        unit_display = (line_total / qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if qty else Decimal("0")  # Prix unitaire affiché
        qty_display = format_quantity(qty)  # Quantité formatée
        detail_lines.append(
            sanitize_receipt_text(
                f"- {label} x {qty_display} = {line_total:.2f} EUR (PU {unit_display:.2f} EUR)"
            )
        )  # Ajoute la ligne de ticket

    footer_lines = [
        "",
        format_currency_line("Total HT", total_ht),
        format_currency_line("TVA", total_tva),
        format_currency_line("Total TTC", total_ttc),
        "",
        "Merci pour votre achat !",
    ]  # Pied de ticket

    sanitized_lines = [sanitize_receipt_text(line) for line in header_lines + detail_lines + footer_lines]  # Nettoie toutes les lignes
    pdf_bytes = render_receipt_pdf(sanitized_lines)  # Génère le PDF

    filename = f"ticket_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"  # Nom de fichier
    return {"filename": filename, "content": pdf_bytes}  # Retourne le fichier et le contenu binaire



# ---------------------------------------------------------------------------
#  Pipelines de factures → commandes
# ---------------------------------------------------------------------------


def match_invoice_products(invoice_df: pd.DataFrame, *, tenant_id: int = 1) -> pd.DataFrame:
    """Associe les lignes d'une facture aux produits du catalogue via code-barres."""  # Docstring mapping facture→catalogue

    # Ce mapping est essentiel pour éviter les doublons et pré-remplir les informations du catalogue
    # lors d’un import factures : on récupère id/nom/catégorie/prix/TVA pour chaque code détecté.

    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:  # Si DataFrame invalide ou vide
        return pd.DataFrame(
            columns=[
                "code",
                "produit_id",
                "produit_nom",
                "categorie",
                "prix_achat_catalogue",
                "prix_vente_catalogue",
            ]
        )  # Retourne une structure vide

    if "codes" not in invoice_df.columns:  # Si colonne codes absente
        return pd.DataFrame(
            columns=[
                "code",
                "produit_id",
                "produit_nom",
                "categorie",
                "prix_achat_catalogue",
                "prix_vente_catalogue",
            ]
        )  # Retourne vide

    codes: list[str] = []  # Liste des codes collectés
    for raw in invoice_df["codes"].tolist():  # Parcourt la colonne codes
        if isinstance(raw, str):  # Code sous forme de chaîne
            normalized = raw.strip()  # Nettoie
            if normalized:  # Si non vide
                codes.append(normalized)  # Ajoute
        elif isinstance(raw, Iterable):  # Si la cellule est une collection
            for part in raw:  # Parcourt chaque élément
                part_str = str(part or "").strip()  # Nettoie l'élément
                if part_str:  # Si non vide
                    codes.append(part_str)  # Ajoute

    unique_codes = sorted({code.lower() for code in codes if code})  # Dédoublonne en minuscules
    if not unique_codes:  # Si aucun code valide
        return pd.DataFrame(
            columns=[
                "code",
                "produit_id",
                "produit_nom",
                "categorie",
                "prix_achat_catalogue",
                "prix_vente_catalogue",
            ]
        )  # Retourne vide

    placeholders = ", ".join(f"LOWER(:code{i})" for i in range(len(unique_codes)))  # Paramètres pour clause IN
    params = {f"code{i}": code for i, code in enumerate(unique_codes)}  # Paramètres de requête
    params["tenant_id"] = int(tenant_id)  # Paramètre tenant

    sql = f"""
        SELECT
            LOWER(pb.code) AS code,
            p.id AS produit_id,
            p.nom AS produit_nom,
            p.categorie,
            COALESCE(p.prix_achat, 0) AS prix_achat_catalogue,
            COALESCE(p.prix_vente, 0) AS prix_vente_catalogue,
            COALESCE(p.tva, 0) AS tva_catalogue
        FROM produits_barcodes pb
        JOIN produits p ON p.id = pb.produit_id
        WHERE LOWER(pb.code) IN ({placeholders})
          AND pb.tenant_id = :tenant_id
          AND p.tenant_id = :tenant_id
    """  # Requête pour lier codes à produits du catalogue

    try:
        df = query_df(sql, params=params)  # Exécute la requête
    except Exception:  # En cas d'erreur de connexion ou SQL
        return pd.DataFrame(
            columns=[
                "code",
                "produit_id",
                "produit_nom",
                "categorie",
                "prix_achat_catalogue",
                "prix_vente_catalogue",
            ]
        )  # Retourne vide

    if "code" in df.columns:  # Normalise la colonne code
        df["code"] = df["code"].astype(str).str.lower()  # Passe en minuscules
    return df  # Retourne le mapping


def find_similar_products(
    product_name: str,
    *,
    tenant_id: int = 1,
    max_results: int = 3,
    min_similarity: float = 0.3,
) -> list[dict]:
    """Trouve des produits similaires par nom en utilisant trigram similarity.

    Utilisé pour suggérer des correspondances quand un produit de facture
    n'est pas trouvé via code-barres.

    Args:
        product_name: Nom du produit à rechercher
        tenant_id: ID du tenant
        max_results: Nombre max de suggestions
        min_similarity: Score minimum de similarité (0-1)

    Returns:
        Liste de dictionnaires avec les produits similaires et leur score
    """
    if not product_name or not product_name.strip():
        return []

    normalized_name = product_name.strip().lower()

    # Utiliser la similarité trigram de PostgreSQL (extension pg_trgm)
    # Fallback sur LIKE si l'extension n'est pas disponible
    sql = """
        SELECT
            p.id as produit_id,
            p.nom as produit_nom,
            p.categorie,
            COALESCE(p.prix_achat, 0) as prix_achat,
            COALESCE(p.prix_vente, 0) as prix_vente,
            pb.code as barcode,
            SIMILARITY(LOWER(p.nom), :search_name) as similarity_score
        FROM produits p
        LEFT JOIN LATERAL (
            SELECT code FROM produits_barcodes
            WHERE produit_id = p.id
            ORDER BY is_principal DESC, id
            LIMIT 1
        ) pb ON TRUE
        WHERE p.tenant_id = :tenant_id
          AND SIMILARITY(LOWER(p.nom), :search_name) >= :min_similarity
        ORDER BY similarity_score DESC
        LIMIT :max_results
    """

    try:
        df = query_df(sql, params={
            "search_name": normalized_name,
            "tenant_id": int(tenant_id),
            "min_similarity": min_similarity,
            "max_results": max_results,
        })
    except Exception:
        # Fallback si pg_trgm n'est pas installé: utiliser LIKE
        sql_fallback = """
            SELECT
                p.id as produit_id,
                p.nom as produit_nom,
                p.categorie,
                COALESCE(p.prix_achat, 0) as prix_achat,
                COALESCE(p.prix_vente, 0) as prix_vente,
                pb.code as barcode,
                0.5 as similarity_score
            FROM produits p
            LEFT JOIN LATERAL (
                SELECT code FROM produits_barcodes
                WHERE produit_id = p.id
                ORDER BY is_principal DESC, id
                LIMIT 1
            ) pb ON TRUE
            WHERE p.tenant_id = :tenant_id
              AND LOWER(p.nom) LIKE :search_pattern
            ORDER BY p.nom
            LIMIT :max_results
        """
        try:
            # Chercher des mots clés
            words = normalized_name.split()
            main_word = max(words, key=len) if words else normalized_name
            search_pattern = f"%{main_word}%"
            df = query_df(sql_fallback, params={
                "search_pattern": search_pattern,
                "tenant_id": int(tenant_id),
                "max_results": max_results,
            })
        except Exception:
            return []

    if df.empty:
        return []

    results = []
    for _, row in df.iterrows():
        results.append({
            "produit_id": int(row["produit_id"]),
            "produit_nom": row["produit_nom"],
            "categorie": row.get("categorie", ""),
            "prix_achat": float(row.get("prix_achat", 0)),
            "prix_vente": float(row.get("prix_vente", 0)),
            "barcode": row.get("barcode", ""),
            "similarity_score": float(row.get("similarity_score", 0)),
            "match_type": "name_similarity",
        })

    return results


def suggest_product_matches(
    invoice_df: pd.DataFrame,
    *,
    tenant_id: int = 1,
    auto_match_threshold: float = 0.65,
) -> pd.DataFrame:
    """Enrichit les lignes de facture non-matchées avec des suggestions de produits similaires.

    Pour chaque ligne sans produit_id, cherche des produits similaires par nom
    et ajoute les suggestions. AUTO-MATCH si score >= auto_match_threshold.

    Args:
        invoice_df: DataFrame avec les lignes de facture
        tenant_id: ID du tenant
        auto_match_threshold: Score minimum pour auto-matcher (défaut: 0.65)

    Returns:
        DataFrame enrichi avec colonnes:
        - has_suggestion: True si une suggestion existe
        - suggestion_id: ID du produit suggéré
        - suggestion_nom: Nom du produit suggéré
        - suggestion_score: Score de similarité (0-1)
        - suggestion_type: Type de match (name_similarity)
        - produit_id: Rempli automatiquement si score >= auto_match_threshold
    """
    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:
        return invoice_df

    result = invoice_df.copy()

    # Initialiser les colonnes de suggestion
    result["has_suggestion"] = False
    result["suggestion_id"] = None
    result["suggestion_nom"] = None
    result["suggestion_score"] = None
    result["suggestion_type"] = None

    # Identifier les lignes sans match (produit_id manquant ou 0)
    if "produit_id" not in result.columns:
        result["produit_id"] = None

    mask_no_match = result["produit_id"].isna() | (result["produit_id"] == 0)

    if not mask_no_match.any():
        return result

    # Pour chaque ligne sans match, chercher des suggestions
    auto_matched_count = 0
    for idx in result[mask_no_match].index:
        nom = result.at[idx, "nom"] if "nom" in result.columns else None
        if not nom or not str(nom).strip():
            continue

        suggestions = find_similar_products(
            str(nom),
            tenant_id=tenant_id,
            max_results=1,
            min_similarity=0.3,
        )

        if suggestions:
            best = suggestions[0]
            result.at[idx, "has_suggestion"] = True
            result.at[idx, "suggestion_id"] = best["produit_id"]
            result.at[idx, "suggestion_nom"] = best["produit_nom"]
            result.at[idx, "suggestion_score"] = best["similarity_score"]
            result.at[idx, "suggestion_type"] = best["match_type"]

            # AUTO-MATCH si score suffisant
            if best["similarity_score"] >= auto_match_threshold:
                result.at[idx, "produit_id"] = best["produit_id"]
                result.at[idx, "catalogue_id"] = best["produit_id"]
                result.at[idx, "catalogue_nom"] = best["produit_nom"]
                auto_matched_count += 1

    if auto_matched_count > 0:
        import logging
        logging.getLogger(__name__).info(
            f"Auto-matched {auto_matched_count} products by name similarity (threshold={auto_match_threshold})"
        )

    return result


def register_invoice_reception(
    invoice_df: pd.DataFrame,
    *,
    username: str,
    supplier: str | None = None,
    movement_type: str = "ENTREE",
    reception_date: datetime | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    """Crée des mouvements d'entrée à partir d'une réception de facture."""  # Docstring réception facture

    summary = {
        "rows_received": int(len(invoice_df)) if isinstance(invoice_df, pd.DataFrame) else 0,
        "movements_created": 0,
        "quantity_total": 0.0,
        "errors": [],
    }  # Bilan des traitements

    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:  # Si pas de données
        return summary  # Retourne le bilan vide

    safe_type = (movement_type or "ENTREE").upper()  # Normalise le type de mouvement
    if safe_type not in {"ENTREE", "TRANSFERT"}:  # Valeurs autorisées
        safe_type = "ENTREE"  # Valeur par défaut

    label_parts = [supplier.strip() for supplier in [supplier] if isinstance(supplier, str) and supplier.strip()]  # Prépare l'étiquette source
    if username:  # Si un utilisateur est fourni
        label_parts.append(f"traité par {username}")  # Ajoute le nom
    source_label = " · ".join(label_parts) or "Réception facture"  # Libellé source final


    working_df = invoice_df.copy()
    # Prépare les quantités (fallback sur qte_init)
    if "quantite_recue" not in working_df.columns and "qte_init" in working_df.columns:
        working_df["quantite_recue"] = working_df["qte_init"]
    elif "quantite_recue" in working_df.columns and "qte_init" in working_df.columns:
        mask_missing = working_df["quantite_recue"].isna()
        if mask_missing.any():
            working_df.loc[mask_missing, "quantite_recue"] = working_df.loc[mask_missing, "qte_init"]

    # Filtre set-based: produit_id valide + quantité > 0
    working_df["produit_id_num"] = pd.to_numeric(working_df.get("produit_id"), errors="coerce")
    working_df["qty_norm"] = working_df.get("quantite_recue", pd.Series([], dtype="float")).apply(_normalise_quantity)
    valid_mask = working_df["produit_id_num"].notna() & (working_df["produit_id_num"] > 0) & (working_df["qty_norm"] > 0)
    invalid_rows = working_df[~valid_mask]
    if not invalid_rows.empty:
        for row in invalid_rows.itertuples():
            summary["errors"].append(
                f"Ligne ignorée (produit_id invalide ou quantité nulle): produit_id={getattr(row, 'produit_id', None)}, qty={getattr(row, 'quantite_recue', None)}"
            )
    valid_df = working_df[valid_mask]
    if valid_df.empty:
        return summary

    def _get_line_date(row):
        """Récupère la date de la ligne (facture_date) ou fallback sur reception_date."""
        line_date = getattr(row, "facture_date", None)
        if line_date is not None and pd.notna(line_date):
            # Convertir en datetime si c'est une string
            if isinstance(line_date, str) and line_date.strip():
                try:
                    # Format DD-MM-YYYY ou DD/MM/YYYY
                    import re
                    match = re.match(r"^(\d{2})[-/](\d{2})[-/](\d{4})", line_date)
                    if match:
                        return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), tzinfo=timezone.utc)
                    # Format YYYY-MM-DD
                    if re.match(r"^\d{4}-\d{2}-\d{2}", line_date):
                        return datetime.fromisoformat(line_date[:10]).replace(tzinfo=timezone.utc)
                except Exception:
                    pass
            elif isinstance(line_date, (datetime, date)):
                if isinstance(line_date, datetime):
                    return line_date if line_date.tzinfo else line_date.replace(tzinfo=timezone.utc)
                return datetime.combine(line_date, time.min, tzinfo=timezone.utc)
        return reception_date

    payloads: list[dict[str, object]] = [
        {
            "pid": int(row.produit_id_num),
            "qty": row.qty_norm,
            "source": source_label,
            "tenant_id": int(tenant_id),
            "date_mvt": _get_line_date(row),
            "type": safe_type,
        }
        for row in valid_df.itertuples()
    ]
    summary["movements_created"] = len(payloads)
    summary["quantity_total"] = float(valid_df["qty_norm"].sum())

    cost_entries: list[dict[str, object]] = []
    for row in valid_df.itertuples():
        price_achat = getattr(row, "prix_achat", None)
        unit_cost = _as_decimal(price_achat) if price_achat is not None else None
        cost_entries.append(
            {
                "product_id": int(row.produit_id_num),
                "quantity": row.qty_norm,
                "unit_cost": unit_cost,
                "tenant_id": int(tenant_id),
            }
        )

    if not payloads:  # Si aucune ligne valide
        return summary  # Retourne le bilan

    eng = get_engine()  # Récupère l'engine
    inserted_movements = []  # Liste de tuples (movement_id, cost_entry_index) - initialisé ici pour accès après le bloc
    try:
        with eng.begin() as conn:  # Démarre une transaction
            product_ids = sorted({item["pid"] for item in payloads})  # Ensemble des IDs produits concernés
            if product_ids:  # Si des produits sont présents
                placeholders = ", ".join(f":pid_{idx}" for idx, _ in enumerate(product_ids))  # Placeholders IN
                params = {f"pid_{idx}": pid for idx, pid in enumerate(product_ids)}  # Paramètres IDs
                params["tenant_id"] = int(tenant_id)  # Paramètre tenant
                rows = conn.execute(
                    text(
                        f"""
                        SELECT id
                        FROM produits
                        WHERE tenant_id = :tenant_id
                          AND id IN ({placeholders})
                        """
                    ),
                    params,
                ).fetchall()  # Vérifie l'existence des produits
                valid_ids = {int(row.id) for row in rows}  # IDs valides
                if len(valid_ids) != len(product_ids):  # Des IDs invalides détectés
                    invalid = sorted(set(product_ids) - valid_ids)  # Liste des manquants
                    summary["errors"].append(
                        f"Produits hors environnement ou introuvables: {', '.join(map(str, invalid))}"
                    )  # Ajoute un message
                    payloads = [payload for payload in payloads if payload["pid"] in valid_ids]  # Filtre les payloads
                    cost_entries = [entry for entry in cost_entries if entry["pid"] in valid_ids]  # Filtre les coûts

            if not payloads:  # Si plus rien à insérer
                return summary  # Retourne le bilan

            # Vérification anti-doublon: on vérifie si des mouvements identiques existent déjà
            check_duplicate_sql = text(
                """
                SELECT produit_id, date_mvt::date, quantite
                FROM mouvements_stock
                WHERE tenant_id = :tenant_id
                  AND source = :source
                  AND produit_id = :pid
                  AND date_mvt::date = CAST(:date_mvt AS date)
                  AND quantite = :qty
                LIMIT 1
                """
            )

            # Insert mouvements un par un pour récupérer les IDs (SQLAlchemy 2.0 batch RETURNING issue)
            insert_sql = text(
                """
                INSERT INTO mouvements_stock (produit_id, type, quantite, source, date_mvt, tenant_id)
                VALUES (:pid, :type, :qty, :source, COALESCE(:date_mvt, now()), :tenant_id)
                RETURNING id
                """
            )
            skipped_duplicates = 0
            for idx, payload in enumerate(payloads):
                # Vérifie si ce mouvement existe déjà
                existing = conn.execute(check_duplicate_sql, payload).fetchone()
                if existing:
                    skipped_duplicates += 1
                    continue  # Skip ce doublon
                result = conn.execute(insert_sql, payload)
                row = result.fetchone()
                if row:
                    inserted_movements.append((row.id, idx))

            if skipped_duplicates > 0:
                summary["skipped_duplicates"] = skipped_duplicates
                summary["errors"].append(f"{skipped_duplicates} mouvement(s) ignoré(s) car déjà existant(s)")

            for movement_id, idx in inserted_movements:  # Aligne chaque coût avec un mouvement
                entry = cost_entries[idx]
                inventory_costing.add_cost_layer(
                    conn,
                    tenant_id=int(tenant_id),
                    product_id=entry["product_id"],
                    quantity=entry["quantity"],
                    unit_cost=entry["unit_cost"],
                    movement_id=movement_id,
                    source=source_label,
                    received_at=entry.get("received_at"),
                )  # Ajoute la couche de coût
    except sa_exc.IntegrityError as exc:  # Violations de contraintes
        summary["errors"].append(f"Erreur d'intégrité lors de l'enregistrement: {exc.orig}")  # Ajoute l'erreur
        return summary  # Retourne le bilan
    except Exception as exc:  # pragma: no cover - sécurité runtime
        summary["errors"].append(str(exc))  # Ajoute le message
        return summary  # Retourne le bilan

    summary["movements_created"] = len(inserted_movements)  # Nombre de mouvements réellement créés
    summary["quantity_total"] = float(sum(payloads[idx]["qty"] for _, idx in inserted_movements))  # Quantité totale mouvementée
    return summary  # Retourne le bilan final

# Ajoutez d'autres fonctions de service ici (ex: adjust_stock, create_product_with_barcode)  # Commentaire de rappel
