from __future__ import annotations  # Active les annotations différées

"""Chargement des produits à partir de factures/extracteurs.

Le service scrute les lignes extraites (nom, code, quantités, prix, TVA) et :
1. Découvre si un produit existe déjà (code-barres, nom).
2. Met à jour les champs financiers (prix d'achat, prix de vente, marges).
3. Maintient la table produits_barcodes (insert/update).
4. Optionnellement, crée un mouvement d’init stock.
Les erreurs sont collectées dans un résumé renvoyé à l’API invoices."""

from typing import Any, Dict, List, Mapping, Sequence  # Types utilitaires
import json
from datetime import datetime  # Pour les dates de facture

import io  # Buffers en mémoire pour CSV rejeté
import math  # Utilitaires math (NaN)
import re  # Expressions régulières pour nettoyage
import unicodedata  # Normalisation Unicode
from pathlib import Path  # Gestion de chemins

import pandas as pd  # DataFrame pour les imports
from sqlalchemy import exc as sa_exc, text  # Exceptions SQLAlchemy et SQL textuel
from sqlalchemy.engine import Connection  # Type de connexion SQLAlchemy

from .invoice_extractor import DEFAULT_TVA_CODE_MAP  # Mapping codes TVA par défaut
from .data_repository import get_engine  # Récupération du moteur SQL

ALCOHOL_KEYWORDS = [
    "biere",
    "bière",
    "beer",
    "vin",
    "whisky",
    "rhum",
    "vodka",
    "liqueur",
    "champagne",
    "cidre",
    "tequila",
    "gin",
    "pastis",
    "cognac",
    "armagnac",
    "porto",
]  # Mots clés pour détecter l'alcool

DEFAULT_MARGIN_RATE = 0.40  # Marge par défaut 40 %
PRICE_DELTA_THRESHOLD = 0.10  # Seuil de variation prix significative


def _empty_summary(rows_received: int = 0) -> Dict[str, Any]:
    return {
        "rows_received": rows_received,  # Lignes reçues
        "rows_processed": 0,  # Lignes traitées
        "created": 0,  # Produits créés
        "updated": 0,  # Produits mis à jour
        "stock_initialized": 0,  # Stocks initialisés
        "barcode": {"added": 0, "conflicts": 0, "skipped": 0},  # Statistiques codes-barres
        "errors": [],  # Erreurs rencontrées
        "rejected_rows": [],  # Lignes rejetées
        "rejected_csv": None,  # CSV des rejets
        "flags": [],  # Flags data-quality (ex: prix manquant)
    }


def _ensure_import_rejets(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS import_rejets (
              id bigserial PRIMARY KEY,
              table_name text NOT NULL,
              reason text NOT NULL,
              payload jsonb NOT NULL DEFAULT '{}'::jsonb,
              created_at timestamptz NOT NULL DEFAULT now()
            );
            """
        )
    )


def _log_reject(conn: Connection, summary: Dict[str, Any], table: str, reason: str, payload: Mapping[str, Any]) -> None:
    _ensure_import_rejets(conn)
    summary["rejected_rows"].append({"table": table, "reason": reason, "payload": payload})
    summary["flags"].append({"table": table, "reason": reason, "payload": payload})
    conn.execute(
        text(
            """
            INSERT INTO import_rejets (table_name, reason, payload)
            VALUES (:table_name, :reason, :payload::jsonb)
            """
        ),
        {"table_name": table, "reason": reason, "payload": json.dumps(payload)},
    )


def _normalize_barcode(value: str | None) -> str:
    if value is None:  # Valeur absente
        return ""  # Retourne chaîne vide
    text_value = str(value)  # Convertit en chaîne
    digits = re.sub(r"\D", "", text_value)  # Garde uniquement les chiffres
    if 8 <= len(digits) <= 15:  # Longueur standard EAN/UPC
        return digits  # Retourne la version digits-only
    return re.sub(r"\s+", "", text_value).upper()  # Nettoie espaces et majuscules


def _normalize_name(value: str | None) -> str:
    if value is None:  # Aucun nom
        return ""  # Retourne vide
    normalized = unicodedata.normalize("NFKC", str(value))  # Normalise Unicode
    normalized = normalized.replace("’", "'")  # Remplace apostrophe typographique
    normalized = re.sub(r"\s+", " ", normalized)  # Compacte les espaces
    return normalized.strip()  # Supprime bords


def _to_float(value: Any, default: float | None = 0.0) -> float | None:
    if value is None:  # Absence de valeur
        return default  # Retourne défaut

    if isinstance(value, (int, float)):  # Si déjà numérique
        numeric = float(value)  # Conversion en float
        if math.isnan(numeric):  # Si NaN
            return default  # Retourne défaut
        return numeric  # Retourne la valeur

    if isinstance(value, str):  # Si chaîne
        cleaned = (
            value.replace("\xa0", " ")  # Remplace espace insécable
            .replace("€", "")  # Supprime symbole euro
            .replace("EUR", "")  # Supprime devise
            .replace("%", "")  # Supprime pourcentage
            .replace(",", ".")  # Remplace virgule
            .strip()  # Trim
        )
        cleaned = re.sub(r"[^\d\.\-]", "", cleaned)  # Retire tout caractère non numérique
        if not cleaned:  # Si vide
            return default  # Retourne défaut
        try:
            return float(cleaned)  # Conversion en float
        except ValueError:
            return default  # Défaut en cas d'erreur

    try:
        return float(value)  # type: ignore[arg-type]  # Essaye de caster en float
    except (TypeError, ValueError):
        return default  # Défaut en cas d'échec


def insert_or_update_barcode(
    conn: Connection,
    produit_id: int,
    barcode: str,
    tenant_id: float | int | None = None,
) -> str:
    """Insère un code-barres et renvoie *added*, *skipped* ou *conflict*."""  # Docstring action code-barres

    # On vérifie d’abord si le code existe déjà pour un produit différent.
    # Cela protège contre l'écrasement d'un code partagé par deux produits.

    normalized = _normalize_barcode(barcode)  # Code nettoyé
    if not normalized:  # Si vide
        return "skipped"  # On ignore

    existing = conn.execute(
        text(
            """
            SELECT produit_id
            FROM produits_barcodes
            WHERE lower(code) = lower(:code)
            LIMIT 1
            """
        ),
        {"code": normalized},
    ).fetchone()  # Cherche un code existant

    if existing:  # Si un code existe
        return "skipped" if int(existing.produit_id) == int(produit_id) else "conflict"  # Conflit ou ignoré

    if tenant_id is None:  # Si tenant non fourni
        tenant_row = conn.execute(
            text("SELECT tenant_id FROM produits WHERE id = :pid"),
            {"pid": produit_id},
        ).fetchone()  # Récupère le tenant du produit
        tenant_id = tenant_row.tenant_id if tenant_row else 1  # Par défaut 1

    conn.execute(
        text(
            """
            INSERT INTO produits_barcodes (produit_id, tenant_id, code)
            VALUES (:pid, :tenant_id, :code)
            """
        ),
        {"pid": produit_id, "tenant_id": tenant_id, "code": normalized},
    )  # Insert le nouveau code-barres
    return "added"  # Indique l'ajout


def exec_sql_return_id_with_conn(conn: Connection, sql: str, params=None):
    """Exécute une requête SQL et retourne l'ID (colonne 0) en utilisant une connexion ouverte."""  # Docstring helper SQL

    result = conn.execute(text(sql), params)  # Exécute la requête
    row = result.fetchone()  # Récupère la première ligne
    return row[0] if row else None  # Retourne la première colonne


# Mapping des catégories METRO par mots-clés
CATEGORY_KEYWORDS = {
    # Boissons
    "Softs / Énergisants": ["COCA", "FANTA", "SPRITE", "PEPSI", "ORANGINA", "SCHWEPPES", "RED BULL",
                           "MONSTER", "ENERGY", "SODA", "LIMONADE", "TONIC", "GINGER", "VIMTO",
                           "MALTA", "DJINO", "CAPRI", "JUS", "NECTAR", "SIROP", "THE GLACE"],
    "Eaux": ["EAU ", "EVIAN", "VITTEL", "CRISTALINE", "PERRIER", "BADOIT", "SAN PELLEGRINO", "VOLVIC"],
    "Bières": ["BIERE", "BIÈRE", "BEER", "HEINEKEN", "KRONENBOURG", "LEFFE", "GRIMBERGEN", "1664"],
    "Vins rouges": ["VIN ROUGE", "BORDEAUX ROUGE", "COTES DU RHONE ROUGE", "MERLOT", "CABERNET"],
    "Vins blancs": ["VIN BLANC", "CHARDONNAY", "SAUVIGNON", "CHABLIS", "MUSCADET", "RIESLING"],
    "Vins rosés": ["VIN ROSE", "ROSÉ", "PROVENCE ROSE"],
    "Spiritueux": ["WHISKY", "RHUM", "VODKA", "GIN ", "TEQUILA", "COGNAC", "ARMAGNAC", "LIQUEUR",
                   "PASTIS", "RICARD", "PORTO", "MARTINI", "BAILEYS", "COINTREAU", "ABSINTHE"],
    "Effervescents / Champagne": ["CHAMPAGNE", "CREMANT", "PROSECCO", "MOUSSEUX", "CAVA"],
    "Apéritifs / Fortifiés": ["APERITIF", "VERMOUTH", "CAMPARI", "APEROL", "BYRRH", "DUBONNET"],

    # Épicerie
    "Épicerie sucrée": ["SUCRE", "CONFITURE", "MIEL", "NUTELLA", "CHOCOLAT", "BISCUIT", "GATEAU",
                        "CEREALE", "FARINE", "ARACHIDE", "BANKU", "FUFU", "GARI", "ATTIEKE",
                        "FONIO", "DATTE", "HARICOT", "LENTILLE", "POIS", "MAIS", "SEMOULE",
                        "FLOCON", "KOKONTE", "POUNDO", "THIACRY", "COUSCOUS"],
    "Épices / Herbes / Bouillons": ["EPICE", "ÉPICE", "BOUILLON", "MAGGI", "JUMBO", "ADJA", "CUBE",
                                     "POIVRE", "SEL ", "CURRY", "CUMIN", "CURCUMA", "PAPRIKA",
                                     "PIMENT", "AIL ", "OIGNON", "GINGEMBRE", "CANNELLE", "CLOU",
                                     "LAURIER", "THYM", "PERSIL", "CORIANDRE", "BASILIC", "MENTHE",
                                     "MUSCADE", "SAFRAN", "COLOMBO", "MASSALE", "TANDORI", "HARISSA",
                                     "KINKELIBA", "BISSAP", "MORINGA", "NDOLE", "GOMBO", "AKPI",
                                     "SOUMARA", "DJEKA", "PISTACHE", "CAFE TOUBA"],
    "Conserves / Tomates": ["CONSERVE", "TOMATE", "SAUCE TOMATE", "CONCENTRE", "PUREE TOMATE",
                            "PILCHARD", "SARDINE", "THON BOITE", "CORNED BEEF", "PATE", "PRAISE",
                            "GHANAFRESH", "MAINGOURD"],
    "Huiles / Condiments": ["HUILE", "VINAIGRE", "MAYONNAISE", "MOUTARDE", "KETCHUP", "SAUCE",
                            "PALME", "TOURNESOL", "OLIVE", "ARACHIDE", "COCO", "DAKATINE",
                            "PINDAKA", "BONMAFE", "ZOMI", "GUINEA PALM", "MAMA FUTA"],
    "Pâtes / Riz / Semoule / Farine": ["PATE ", "PATES", "SPAGHETTI", "TAGLIATELLE", "FUSILLI",
                                        "RIZ ", "BASMATI", "TILDA", "PARFUME", "CASSE", "ORCHIDEE",
                                        "SEMOULE", "FARINE"],
    "Apéro salé / Graines": ["CHIPS", "CACAHUETE", "PISTACHE", "NOIX", "AMANDE", "GRAINE",
                              "APERO", "BRETZEL", "BISCUIT SALE", "RAMEN", "INDOMIE", "NOUGAT"],
    "Café / Thé / Infusion": ["CAFE", "NESCAFE", "EXPRESSO", "THE ", "INFUSION", "TISANE",
                               "STARLING", "FOSTER CLARK"],
    "Confiserie / Desserts": ["BONBON", "CARAMEL", "CONFISERIE", "REGLISSE", "CHEWING", "MENTOS",
                               "HARIBO", "DESSERT", "CREME DESSERT", "FLAN", "MOUSSE"],

    # Frais
    "Laits / Crèmes": ["LAIT", "CREME", "NIDO", "PEAK", "CERELAC", "MILO", "NESTLE", "QUAKER",
                       "CONCENTRE", "BONNET ROUGE"],
    "Frais laitier / Fromages": ["FROMAGE", "YAOURT", "YOGOURT", "BEURRE", "MARGARINE"],
    "Fruits / Légumes frais": ["FRUIT", "LEGUME", "SALADE", "TOMATE FRAIS", "OIGNON FRAIS",
                                "CAROTTE", "POMME DE TERRE", "BANANE", "MANGUE", "ANANAS"],
    "Boulangerie / Viennoiserie": ["PAIN ", "BAGUETTE", "CROISSANT", "BRIOCHE", "VIENNOISERIE"],

    # Viandes / Poissons
    "Mer / Viandes base": ["POISSON", "TILAPIA", "CAPITAINE", "BARRACUDA", "DORADE", "MEROU",
                           "MAQUEREAU", "SOLE", "CREVETTE", "CRABE", "CALAMAR", "POULPE", "LAMBI",
                           "THON ", "SAUMON", "CABILLAUD", "COLIN", "SARDINE FRAIS", "ANCHOIS",
                           "CHINCHARD", "COURBINE", "OMBRINE", "VIVANEAU", "PANGASIUS", "REQUIN",
                           "CARANGUE", "MACHOIRON", "PLAT PLAT", "DARNE"],
    "Viandes / Poisson / Charcut": ["VIANDE", "BOEUF", "POULET", "POULE", "DINDE", "CANARD",
                                     "PORC", "AGNEAU", "MOUTON", "SAUCISSE", "JAMBON", "BACON",
                                     "LARD", "CHORIZO", "MERGUEZ", "ANDOUILLE", "BOUDIN",
                                     "FUME", "FUMEE", "FUMÉ", "FUMÉE", "COQ", "CUISSE", "AILE",
                                     "PILON", "AILERON", "CROUPION", "KEBAB", "CORDON BLEU"],
    "Panés / Apéro salé": ["PANE", "NUGGETS", "TENDERS", "NEMS", "SAMOUSSA", "SPRING ROLL",
                           "FRITE", "PAROTTA", "STEAK HACHE", "BOULETTE", "PREPARE", "TANDOORI"],
    "Surgelés légumes": ["SURGELE", "CONGELE", "LEGUME SURGELE", "CHIKWANGUE", "BOBOLO",
                          "MIONDO", "MANIOC", "IGNAME", "TARO", "PLANTAIN", "ATTIEKE", "PLACALI",
                          "SAKA SAKA", "FUMBWA", "MATEMBELE", "BITEKU", "NDOLE SURGELE"],

    # Autres
    "Emballages / Jetables": ["EMBALLAGE", "BARQUETTE", "GOBELET", "COUVERTS", "SERVIETTE",
                               "PAPIER", "FILM", "ALUMINIUM", "SAC ", "PALETTE"],
    "Hygiène / Entretien": ["HYGIENE", "SAVON", "SHAMPOOING", "GEL DOUCHE", "DENTIFRICE",
                            "DEODORANT", "LESSIVE", "LIQUIDE VAISSELLE", "JAVEL", "NETTOYANT"],
}

# Mapping code produit -> catégorie pour EUROCIEL (préfixe 1xxxx)
EUROCIEL_CODE_CATEGORIES = {
    "10": "Mer / Viandes base",      # Poissons entiers
    "11": "Mer / Viandes base",      # Darnes
    "12": "Viandes / Poisson / Charcut",  # Volailles/Fumés
    "13": "Mer / Viandes base",      # Divers poissons
    "14": "Mer / Viandes base",      # Crustacés
    "15": "Panés / Apéro salé",      # Nems/Viandes
    "16": "Mer / Viandes base",      # Maquereau
    "17": "Panés / Apéro salé",      # Samoussa
    "18": "Surgelés légumes",        # Légumes
    "19": "Mer / Viandes base",      # Plat plat
}

# Mapping code produit -> catégorie pour TAIYAT (préfixe 2xxxx)
TAIYAT_CODE_CATEGORIES = {
    "20": "Softs / Énergisants",     # Boissons
    "21": "Épicerie sucrée",         # Légumes secs/Farines
    "22": "Épices / Herbes / Bouillons",  # Épices
    "23": "Conserves / Tomates",     # Conserves
    "24": "Laits / Crèmes",          # Laits
    "25": "Huiles / Condiments",     # Huiles
    "26": "Pâtes / Riz / Semoule / Farine",  # Riz
    "27": "Apéro salé / Graines",    # Snacks
    "28": "Surgelés légumes",        # Surgelés
    "29": "Épicerie sucrée",         # Divers
}


def determine_categorie(nom_produit: Any, fournisseur: str | None = None, code: str | None = None) -> str:
    """Détermine la catégorie METRO à partir du nom, fournisseur ou code du produit."""

    nom = str(nom_produit).upper() if nom_produit else ""
    fournisseur_upper = str(fournisseur).upper() if fournisseur else ""
    code_str = str(code) if code else ""

    # 1. Si code EUROCIEL (5 chiffres commençant par 1)
    if code_str and len(code_str) == 5 and code_str.startswith("1"):
        prefix = code_str[:2]
        if prefix in EUROCIEL_CODE_CATEGORIES:
            return EUROCIEL_CODE_CATEGORIES[prefix]

    # 2. Si code TAIYAT (5 chiffres commençant par 2)
    if code_str and len(code_str) == 5 and code_str.startswith("2"):
        prefix = code_str[:2]
        if prefix in TAIYAT_CODE_CATEGORIES:
            return TAIYAT_CODE_CATEGORIES[prefix]

    # 3. Détection par fournisseur + mots-clés spécifiques
    if "EUROCIEL" in fournisseur_upper:
        # Catégorisation spécifique EUROCIEL basée sur le nom
        if any(k in nom for k in ["POISSON", "TILAPIA", "CAPITAINE", "BARRACUDA", "DORADE",
                                   "CREVETTE", "CRABE", "DARNE", "SOLE", "MAQUEREAU"]):
            return "Mer / Viandes base"
        if any(k in nom for k in ["POULET", "POULE", "DINDE", "FUME", "COQ", "CUISSE", "AILE"]):
            return "Viandes / Poisson / Charcut"
        if any(k in nom for k in ["NEMS", "SAMOUSSA", "NUGGETS", "FRITE", "PANE"]):
            return "Panés / Apéro salé"
        if any(k in nom for k in ["LEGUME", "MANIOC", "NDOLE", "GOMBO", "IGNAME", "TARO"]):
            return "Surgelés légumes"
        if any(k in nom for k in ["RIZ"]):
            return "Pâtes / Riz / Semoule / Farine"
        return "Mer / Viandes base"  # Défaut EUROCIEL

    if "TAIYAT" in fournisseur_upper or "TAI YAT" in fournisseur_upper:
        # Catégorisation spécifique TAIYAT basée sur le nom
        if any(k in nom for k in ["FANTA", "COCA", "SODA", "JUS", "BOISSON", "MALTA", "ENERGY"]):
            return "Softs / Énergisants"
        if any(k in nom for k in ["EPICE", "BOUILLON", "MAGGI", "JUMBO", "ADJA", "PIMENT"]):
            return "Épices / Herbes / Bouillons"
        if any(k in nom for k in ["HUILE", "PALME", "MAYONNAISE", "MOUTARDE"]):
            return "Huiles / Condiments"
        if any(k in nom for k in ["LAIT", "NIDO", "PEAK", "CERELAC"]):
            return "Laits / Crèmes"
        if any(k in nom for k in ["RIZ", "SEMOULE"]):
            return "Pâtes / Riz / Semoule / Farine"
        if any(k in nom for k in ["CONSERVE", "SARDINE", "PILCHARD", "CORNED"]):
            return "Conserves / Tomates"
        return "Épicerie sucrée"  # Défaut TAIYAT

    # 4. Recherche par mots-clés dans le nom (pour METRO et autres)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in nom for keyword in keywords):
            return category

    # 5. Catégorie par défaut
    return "Épicerie sucrée"



def ensure_barcode_constraints() -> None:
    """Crée un index d'unicité sur (tenant_id, lower(code)) pour sécuriser les codes-barres."""

    eng = get_engine()
    dialect = eng.url.get_backend_name()
    if dialect == "sqlite":
        index_sql = (
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_produits_barcodes_code_tenant\n"
            "ON produits_barcodes (tenant_id, lower(code));"
        )
    else:
        index_sql = (
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_produits_barcodes_code_tenant\n"
            "ON produits_barcodes (tenant_id, lower(code));"
        )

    try:
        with eng.begin() as conn:
            conn.exec_driver_sql(index_sql)
    except Exception as exc:  # pragma: no cover - best effort
        import logging
        logging.getLogger(__name__).warning(
            "Impossible de créer l'index unique sur produits_barcodes: %s", exc
        )



def create_initial_stock(
    conn: Connection,
    produit_id: int,
    quantite: float,
    *,
    source: str = "Inventaire Initial",
    tenant_id: int = 1,
    date_mvt: datetime | None = None,
) -> bool:
    """Insère un mouvement de stock positif et renvoie ``True`` s'il est créé."""  # Docstring stock initial

    try:
        qty = float(quantite)  # Convertit en float
    except (TypeError, ValueError):
        return False  # Échec de conversion

    if qty <= 0:  # Quantité non positive
        return False  # N'insère rien

    sql = text(
        """
        INSERT INTO mouvements_stock (produit_id, type, quantite, source, tenant_id, date_mvt)
        VALUES (:produit_id, 'ENTREE', :quantite, :source, :tenant_id, COALESCE(:date_mvt, now()))
        """
    )  # Requête d'insertion mouvement d'entrée
    conn.execute(
        sql,
        {"produit_id": produit_id, "quantite": qty, "source": source, "tenant_id": int(tenant_id), "date_mvt": date_mvt},
    )  # Exécute l'insertion
    return True  # Indique succès


def _find_existing_product_by_barcode(
    conn: Connection,
    codes: List[str],
    *,
    tenant_id: int = 1,
) -> tuple[int | None, str | None]:
    """Recherche un produit par ses codes-barres et renvoie l'ID et le code associé."""  # Docstring recherche code

    # Utilisée avant de créer un produit pour éviter les doublons de référence.

    for code in codes:  # Parcourt les codes candidats
        normalized = (code or "").strip()  # Nettoie
        if not normalized:  # Si vide
            continue  # Ignore

        row = conn.execute(
            text(
                """
                SELECT produit_id
                FROM produits_barcodes
                WHERE lower(code) = lower(:code)
                  AND tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"code": normalized, "tenant_id": int(tenant_id)},
        ).fetchone()  # Cherche un produit via code

        if row:  # Si trouvé
            if hasattr(row, "produit_id"):  # Selon type de ligne
                produit_id = getattr(row, "produit_id")  # Accès attr
            elif isinstance(row, dict):  # Dict
                produit_id = row.get("produit_id")  # Accès clé
            else:
                produit_id = row[0]  # Tuple/list
            if produit_id is not None:  # Si ID valide
                return int(produit_id), normalized  # Retourne l'ID et le code

    return None, None  # Aucun produit trouvé


def _clean_codes(raw_codes: Any) -> List[str]:
    if raw_codes is None:  # Si pas de codes
        return []  # Retourne liste vide

    if isinstance(raw_codes, list):  # Si déjà liste
        iterator = raw_codes  # Utilise tel quel
    else:
        iterator = str(raw_codes).replace("\n", " ").split(";")  # Transforme la chaîne en liste

    cleaned: List[str] = []  # Liste des codes nettoyés
    for chunk in iterator:  # Parcourt chaque segment
        raw = str(chunk).replace(",", " ")  # Remplace virgule par espace
        for item in raw.split():  # Découpe par espace
            code = _normalize_barcode(item.strip())  # Normalise
            if code:  # Si code valide
                cleaned.append(code)  # Ajoute à la liste
    return cleaned  # Retourne les codes nettoyés


def _row_as_dict(row: Any, columns: Sequence[str]) -> Dict[str, Any]:
    if row is None:  # Ligne vide
        return {}  # Retourne dict vide
    if hasattr(row, "_mapping"):  # RowMapping SQLAlchemy
        return dict(row._mapping)  # Convertit en dict
    if isinstance(row, Mapping):  # Déjà un mapping
        return dict(row)  # Retourne dict

    result: Dict[str, Any] = {}  # Dictionnaire résultat
    for index, column in enumerate(columns):  # Parcourt les colonnes attendues
        if hasattr(row, column):  # Si attribut présent
            result[column] = getattr(row, column)  # Ajoute au dict
        else:
            try:
                result[column] = row[index]  # Essaye via index
            except (IndexError, TypeError):
                continue  # Ignore si pas accessible
    return result  # Retourne le dict final


def _fetch_product_snapshot(conn: Connection, produit_id: int | None, *, tenant_id: int = 1) -> Dict[str, Any]:
    if produit_id in (None, ""):  # Si identifiant invalide
        return {}  # Retourne dict vide
    row = conn.execute(
        text(
            """
            SELECT id, prix_achat, prix_vente, categorie
            FROM produits
            WHERE id = :pid AND tenant_id = :tenant_id
            LIMIT 1
            """
        ),
        {"pid": int(produit_id), "tenant_id": int(tenant_id)},
    ).fetchone()  # Récupère un snapshot produit
    return _row_as_dict(row, ["id", "prix_achat", "prix_vente", "categorie"])  # Convertit en dict


def _fetch_product_by_name(conn: Connection, nom: str, *, tenant_id: int = 1) -> Dict[str, Any]:
    cleaned = _normalize_name(nom)  # Nom normalisé
    if not cleaned:  # Si vide
        return {}  # Retourne dict vide
    row = conn.execute(
        text(
            """
            SELECT id, prix_achat, prix_vente, categorie
            FROM produits
            WHERE lower(nom) = lower(:nom)
              AND tenant_id = :tenant_id
            LIMIT 1
            """
        ),
        {"nom": cleaned, "tenant_id": int(tenant_id)},
    ).fetchone()  # Cherche par nom exact
    return _row_as_dict(row, ["id", "prix_achat", "prix_vente", "categorie"])  # Retourne snapshot


def _apply_margin(purchase: float | None, sale_candidate: float | None, *, margin: float) -> float | None:
    if purchase is None:  # Pas de prix d'achat
        return sale_candidate  # Retourne le candidat
    baseline = round(float(purchase) * (1.0 + margin), 2)  # Calcule prix avec marge
    if sale_candidate is None:  # Aucun prix de vente proposé
        return baseline  # Utilise baseline
    return round(sale_candidate if sale_candidate >= baseline else baseline, 2)  # Choisit le max


def _has_significant_delta(old: Any, new: Any, *, threshold: float) -> bool:
    new_value = _to_float(new, default=None)  # Nouveau en float
    if new_value is None:  # Si nouveau absent
        return False  # Pas de delta significatif
    old_value = _to_float(old, default=None)  # Ancien en float
    if old_value is None or abs(old_value) < 1e-9:  # Ancien absent ou quasi nul
        return True  # Considéré comme delta
    diff = abs(new_value - old_value)  # Différence absolue
    if diff < 0.01:  # Variation minime
        return False  # Pas significatif
    return diff / abs(old_value) >= threshold  # Compare au seuil relatif


def _resolve_purchase_price(candidate: float | None, existing: Any) -> float:
    """Détermine le prix d'achat à persister en tenant compte de l'inflation."""  # Docstring prix achat

    # En priorité on prend le nouveau prix d'achat si significativement plus élevé.
    candidate_value = _to_float(candidate, default=None)  # Nouveau prix
    existing_value = _to_float(existing, default=None)  # Ancien prix

    if candidate_value is None or candidate_value <= 0:  # Candidat invalide
        return existing_value or 0.0  # Retourne ancien ou 0
    if existing_value is None or existing_value <= 0:  # Ancien invalide
        return candidate_value  # Retourne candidat

    # Les prix augmentent régulièrement dans les factures METRO : même une hausse
    # minime doit être retenue pour refléter l'inflation.
    if candidate_value > existing_value:  # Hausse
        return candidate_value  # Prend le nouveau prix

    if _has_significant_delta(existing_value, candidate_value, threshold=PRICE_DELTA_THRESHOLD):  # Delta notable
        return candidate_value  # Prend le nouveau prix
    return existing_value  # Sinon conserve l'ancien


def _resolve_sale_price(
    candidate_sale: float | None,
    existing_sale: Any,
    *,
    purchase_price: float,
    tva_rate: float,
    margin: float,
    threshold: float,
    force_when_purchase_increases: bool = False,
) -> float:
    safe_purchase = max(purchase_price, 0.0)  # Prix achat >= 0
    safe_margin = max(margin, 0.0)  # Marge >= 0
    tva_multiplier = 1 + max(tva_rate, 0.0) / 100.0  # Multiplicateur TVA
    baseline_ttc = round(safe_purchase * (1 + safe_margin) * tva_multiplier, 4)  # Prix TTC avec marge minimale
    target_sale = baseline_ttc  # Cible initiale
    candidate_value = _to_float(candidate_sale, default=None)  # Prix vente proposé
    # Pour éviter de baisser les prix, on n’accepte un candidate supérieur au minimum qu’en cas d’augmentation claire.
    if candidate_value is not None and candidate_value > target_sale:  # Si candidat supérieur
        target_sale = candidate_value  # Ajuste la cible
    existing_value = _to_float(existing_sale, default=None)  # Prix vente existant

    if existing_value is None or existing_value <= 0:  # Aucun prix existant
        return target_sale  # Utilise la cible

    if existing_value < baseline_ttc:  # Prix existant sous le minimum
        return max(target_sale, baseline_ttc)  # Remonte au minimum

    if force_when_purchase_increases and target_sale > existing_value:  # Si hausse achat, on force la hausse
        return target_sale  # Utilise la cible

    if _has_significant_delta(existing_value, target_sale, threshold=threshold):  # Variation notable
        return target_sale  # Adopte la nouvelle valeur

    return existing_value  # Sinon conserve l'existant


def _resolve_category(
    row: Mapping[str, Any],
    existing: Mapping[str, Any] | None,
    nom: str,
    fournisseur: str | None = None,
    code: str | None = None,
) -> str:
    """Détermine la catégorie d'un produit en fonction de la ligne, du produit existant, ou par détection automatique."""

    # 1. Cherche une catégorie explicite dans la ligne
    for key in ("categorie", "category", "Categorie", "CAT", "TYPE"):
        value = row.get(key) if isinstance(row, Mapping) else None
        if isinstance(value, str) and value.strip():
            return value.strip()

    # 2. Extrait le fournisseur depuis la ligne si non fourni
    if fournisseur is None:
        for key in ("fournisseur", "supplier", "Fournisseur", "FOURNISSEUR"):
            value = row.get(key) if isinstance(row, Mapping) else None
            if isinstance(value, str) and value.strip():
                fournisseur = value.strip()
                break

    # 3. Extrait le premier code depuis la ligne si non fourni
    if code is None:
        code_candidates = (
            row.get("codes")
            or row.get("codes_barres")
            or row.get("EAN")
            or row.get("ean")
            or row.get("ean13")
            or row.get("code")
            or row.get("code_produit")
        )
        if code_candidates:
            codes_list = _clean_codes(code_candidates)
            if codes_list:
                code = codes_list[0]

    # 4. Utilise la détection automatique basée sur fournisseur + code + nom
    detected = determine_categorie(nom, fournisseur=fournisseur, code=code)

    # 5. Si pas de détection concluante et catégorie existante valide, la conserver
    if detected == "Épicerie sucrée" and existing and existing.get("categorie"):
        existing_value = existing.get("categorie")
        if isinstance(existing_value, str) and existing_value.strip():
            return existing_value.strip()

    return detected


def _resolve_tva_value(row: Mapping[str, Any]) -> float | None:
    raw_value = row.get("tva")  # Tente la colonne tva
    numeric = _to_float(raw_value, default=None)  # Convertit
    if numeric is not None:  # Si conversion ok
        return numeric  # Retourne la valeur

    candidate = row.get("tva_code") or row.get("code_tva") or raw_value  # Fallback code TVA
    if isinstance(candidate, str):  # Si texte
        code = candidate.strip().upper()  # Normalise
        if len(code) == 1 and code in DEFAULT_TVA_CODE_MAP:  # Code court
            return float(DEFAULT_TVA_CODE_MAP[code])  # Retourne le mapping
    return None  # Aucun taux trouvé


def load_products_from_df(
    df: pd.DataFrame,
    *,
    initialize_stock: bool = True,
    tenant_id: int = 1,
) -> Dict[str, Any]:
    """Charge les produits à partir d'un DataFrame et retourne un résumé détaillé."""  # Docstring import produits

    # Étapes :
    # 1. Normalisation (nom, codes, prix, TVA, seuil, quantités).
    # 2. Détection : soit par code-barres existants, soit par nom exact.
    # 3. Application des règles de marge et catégories.
    # 4. Insertion/MAJ produits + codes.
    # 5. Optionnel : création d’un mouvement de stock initial (`initialize_stock`).

    summary = _empty_summary(rows_received=int(len(df)))  # Initialisation du résumé

    if df.empty:  # Si DataFrame vide
        return summary  # Retourne le résumé

    engine = get_engine()  # Récupère le moteur SQL
    with engine.begin() as conn:  # Démarre une transaction
        for idx, row in df.iterrows():  # Parcourt chaque ligne
            summary["rows_processed"] += 1  # Incrémente le compteur
            nom = _normalize_name(row.get("nom", ""))  # Nom normalisé

            try:
                # --- Normalisation des entrées minimales (nom, prix, TVA, seuils, quantités) ---
                if not nom:  # Nom manquant
                    raise ValueError("Nom du produit manquant")  # Erreur

                raw_purchase = _to_float(row.get("prix_achat"), default=None)  # Prix achat candidat
                raw_sale = _to_float(row.get("prix_vente"), default=None)  # Prix vente candidat

                tva = _resolve_tva_value(row)  # Taux de TVA
                if tva is None:  # TVA absente
                    raise ValueError("TVA manquante ou invalide")  # Erreur

                seuil_alerte = _to_float(
                    row.get("seuil_alerte_defaut", row.get("seuil_alerte")),
                    default=0.0,
                ) or 0.0  # Seuil d'alerte
                qte_init = _to_float(
                    row.get("quantite_initiale", row.get("qte_init")),
                    default=0.0,
                ) or 0.0  # Quantité initiale
                code_candidates = (
                    row.get("codes")
                    or row.get("codes_barres")
                    or row.get("EAN")
                    or row.get("ean")
                    or row.get("ean13")
                    or row.get("EAN13")
                    or row.get("code_ean")
                    or row.get("CodeEAN")
                )  # Recherche des colonnes de codes
                codes_list = _clean_codes(code_candidates)  # Normalise les codes

                # Génère un code placeholder si aucun code EAN n'est fourni
                if not codes_list and nom:
                    import hashlib
                    # Génère un code à 10 chiffres basé sur le hash du nom
                    nom_hash = hashlib.md5(nom.upper().encode()).hexdigest()[:10]
                    placeholder_code = f"PLH{nom_hash.upper()}"
                    codes_list = [placeholder_code]

                # --- Identification du produit : barcodes en priorité, puis fallback sur le nom exact ---
                produit_id: int | None = None  # ID produit éventuel
                matched_code: str | None = None  # Code ayant servi à matcher
                existing_snapshot: Dict[str, Any] | None = None  # Snapshot existant
                if codes_list:  # Si des codes sont fournis
                    produit_id, matched_code = _find_existing_product_by_barcode(
                        conn,
                        codes_list,
                        tenant_id=tenant_id,
                    )  # Recherche par code
                    existing_snapshot = _fetch_product_snapshot(conn, produit_id, tenant_id=tenant_id)  # Snapshot actuel

                if produit_id is None:  # Si aucun produit via code
                    snapshot_by_name = _fetch_product_by_name(conn, nom, tenant_id=tenant_id)  # Cherche par nom
                    if snapshot_by_name.get("id") is not None:  # Si trouvé
                        produit_id = int(snapshot_by_name.get("id"))  # Récupère l'ID
                        existing_snapshot = snapshot_by_name  # Utilise ce snapshot

                # --- Construction/ajustement des attributs métier (catégorie, prix achat/vente, marge, seuils) ---
                first_code = codes_list[0] if codes_list else None  # Premier code pour catégorisation
                categorie = _resolve_category(row, existing_snapshot, nom, code=first_code)  # Catégorie retenue

                existing_purchase = (existing_snapshot or {}).get("prix_achat")  # Prix achat existant
                purchase_price = _resolve_purchase_price(
                    raw_purchase, existing_purchase
                )  # Prix achat final
                if purchase_price is None or purchase_price <= 0:
                    _log_reject(
                        conn,
                        summary,
                        "produits",
                        "prix_achat_manquant",
                        {"nom": nom, "codes": codes_list, "source_row": dict(row)},
                    )
                    continue

                existing_purchase_value = _to_float(existing_snapshot.get("prix_achat") if existing_snapshot else None, default=None)  # Ancien prix achat en float
                purchase_increased = (
                    existing_purchase_value is not None
                    and purchase_price is not None
                    and purchase_price > existing_purchase_value
                )  # Indique une hausse

                sale_price = _resolve_sale_price(
                    raw_sale,
                    (existing_snapshot or {}).get("prix_vente"),
                    purchase_price=purchase_price,
                    tva_rate=tva,
                    margin=DEFAULT_MARGIN_RATE,
                    threshold=PRICE_DELTA_THRESHOLD,
                    force_when_purchase_increases=purchase_increased,
                )  # Prix vente final

                if sale_price is None or sale_price <= 0:
                    _log_reject(
                        conn,
                        summary,
                        "produits",
                        "prix_vente_manquant",
                        {"nom": nom, "codes": codes_list, "source_row": dict(row)},
                    )
                    continue

                purchase_price = round(float(purchase_price), 2) if purchase_price is not None else 0.0  # Arrondi achat
                sale_price = round(float(sale_price), 2) if sale_price is not None else 0.0  # Arrondi vente

                params_common = {
                    "prix_achat": purchase_price,
                    "prix_vente": sale_price,
                    "tva": tva,
                    "seuil_alerte": seuil_alerte,
                    "categorie": categorie,
                }  # Paramètres communs d'update/insert

                created_new = False  # Flag création

                if produit_id is not None:  # Si produit existant
                    conn.execute(
                        text(
                            """
                            UPDATE produits
                            SET prix_achat = :prix_achat,
                                prix_vente = :prix_vente,
                                tva = :tva,
                                seuil_alerte = :seuil_alerte,
                                categorie = :categorie,
                                updated_at = now()
                            WHERE id = :pid AND tenant_id = :tenant_id
                            """
                        ),
                        {**params_common, "pid": produit_id, "tenant_id": int(tenant_id)},
                    )  # Met à jour le produit
                    summary["updated"] += 1  # Incrémente compteur mise à jour
                else:  # Sinon créer le produit
                    params_with_name = {"nom": nom, **params_common}  # Paramètres avec nom
                    insert_result = conn.execute(
                        text(
                            """
                            INSERT INTO produits (
                                nom,
                                prix_achat,
                                prix_vente,
                                tva,
                                seuil_alerte,
                                categorie,
                                tenant_id
                            )
                            VALUES (:nom, :prix_achat, :prix_vente, :tva, :seuil_alerte, :categorie, :tenant_id)
                            RETURNING id
                            """
                        ),
                        {**params_with_name, "tenant_id": int(tenant_id)},
                    )  # Insertion

                    inserted_row = insert_result.fetchone()  # Récupère la ligne insérée
                    if inserted_row is None:  # Sécurité ID absent
                        raise RuntimeError("Insertion du produit sans ID retourné")  # Erreur
                    inserted_data = _row_as_dict(inserted_row, ["id"])  # Convertit la ligne
                    inserted_id = inserted_data.get("id")  # ID extrait
                    if inserted_id is None:  # Si ID absent
                        raise RuntimeError("Insertion du produit sans identifiant valide")  # Erreur
                    produit_id = int(inserted_id)  # ID final
                    summary["created"] += 1  # Compte les créations
                    created_new = True  # Marque création

                movement_source = "Import facture"  # Source de mouvement par défaut
                if created_new:  # Si création
                    movement_source = "Import facture - création"  # Label adapté
                elif matched_code:  # Si match par code
                    movement_source = f"Import facture - code {matched_code}"  # Label contextualisé

                # Extraction de la date de facture pour le mouvement
                line_date = row.get("facture_date")
                parsed_line_date = None
                if line_date and pd.notna(line_date):
                    if isinstance(line_date, str) and line_date.strip():
                        import re as re_mod
                        match = re_mod.match(r"^(\d{2})[-/](\d{2})[-/](\d{4})", line_date)
                        if match:
                            parsed_line_date = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                    elif isinstance(line_date, datetime):
                        parsed_line_date = line_date

                if initialize_stock and produit_id is not None and create_initial_stock(
                    conn,
                    produit_id,
                    qte_init,
                    source=movement_source,
                    tenant_id=tenant_id,
                    date_mvt=parsed_line_date,
                ):  # Crée éventuellement le stock initial
                    summary["stock_initialized"] += 1  # Incrémente le compteur

                for code in codes_list:  # Parcourt les codes normalisés
                    try:
                        status = insert_or_update_barcode(
                            conn,
                            produit_id,
                            code,
                            tenant_id=tenant_id,
                        )  # Insère ou met à jour le code-barres
                    except sa_exc.IntegrityError:  # Conflit DB
                        summary["barcode"]["conflicts"] += 1  # Note le conflit
                    except Exception:  # Autres erreurs
                        summary["barcode"]["skipped"] += 1  # Note le skip
                        raise  # Propagation
                    else:
                        if status == "added":  # Code ajouté
                            summary["barcode"]["added"] += 1  # Incrémente ajout
                        elif status == "conflict":  # Conflit détecté
                            summary["barcode"]["conflicts"] += 1  # Incrémente conflits
                        else:  # Sinon skip
                            summary["barcode"]["skipped"] += 1  # Incrémente skip

            except Exception as exc:  # Gestion des erreurs par ligne
                summary["errors"].append(
                    {
                        "ligne": int(idx) + 2,  # 1-based index + header
                        "nom": nom or "<inconnu>",
                        "erreur": str(exc),
                    }
                )  # Enregistre l'erreur
                try:
                    summary["rejected_rows"].append(row.to_dict())  # Ajoute la ligne rejetée
                except Exception:
                    summary["rejected_rows"].append({"nom": nom or "<inconnu>"})  # Fallback simple
    if summary["rejected_rows"]:  # Si des rejets existent
        try:
            rejected_df = pd.DataFrame(summary["rejected_rows"])  # DataFrame des rejets
            buffer = io.StringIO()  # Buffer CSV
            rejected_df.to_csv(buffer, index=False)  # Écrit le CSV
            summary["rejected_csv"] = buffer.getvalue()  # Stocke le contenu
        except Exception:
            summary["rejected_csv"] = None  # En cas d'échec

    return summary  # Retourne le résumé global


def process_products_file(csv_path: str) -> Dict[str, Any]:
    """Lit un fichier CSV puis délègue le traitement à :func:`load_products_from_df`."""  # Docstring traitement fichier

    try:
        df = pd.read_csv(csv_path)  # Lit le CSV
    except FileNotFoundError:
        summary = _empty_summary()  # Résumé vide
        summary["errors"].append(
            {"ligne": 0, "nom": "", "erreur": f"Fichier introuvable: {csv_path}"}
        )  # Ajoute erreur
        return summary  # Retourne
    except Exception as exc:
        summary = _empty_summary()  # Résumé vide
        summary["errors"].append(
            {"ligne": 0, "nom": "", "erreur": str(exc)}
        )  # Ajoute erreur
        return summary  # Retourne

    return load_products_from_df(df)  # Délègue au chargement DataFrame


if __name__ == "__main__":  # Exécution directe
    import sys  # Accès aux arguments CLI

    default_csv = Path("docs/invoices/Produit.csv")  # Chemin par défaut
    csv_source = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_csv  # Source choisie
    results = process_products_file(str(csv_source))  # Lance le traitement

    print("--- RÉSULTATS DE L'IMPORTATION ---")  # Affiche l'en-tête
    print(
        f"Total de lignes reçues : {results['rows_received']} | "
        f"Traitées : {results['rows_processed']}"
    )  # Statistiques de base
    print(
        f"Produits créés : {results['created']} | "
        f"Mis à jour : {results['updated']}"
    )  # Statistiques produits

    if results["errors"]:  # S'il y a des erreurs
        print(f"\n🚨 {len(results['errors'])} erreur(s) rencontrée(s) lors de l'import.")  # Avertissement
        for error in results["errors"][:5]:  # Affiche les premières erreurs
            print(f"  Ligne {error['ligne']} ({error['nom']}): {error['erreur']}")  # Détail
    else:
        print("✅ Importation terminée sans erreur bloquante.")  # Succès
