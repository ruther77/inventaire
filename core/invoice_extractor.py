from __future__ import annotations  # Active les annotations différées

# Ce module est le point d’entrée de l’extraction de factures fournisseurs : il
# détecte les formats (PDF, DOCX, texte), neutralise les caractères spéciaux,
# résout les codes-barres et les codes TVA, puis émet un ensemble de lignes
# standardisées (nom, EAN, quantités, prix, TVA, régie, etc.). Le reste du
# backend s’appuie sur ce jeu de données pour alimenter les imports de stock.
import io  # Manipulation de flux mémoire
import re  # Expressions régulières pour le parsing
from pathlib import Path  # Gestion des chemins de fichiers
from typing import Callable, Iterable, Mapping, Sequence  # Typage utilitaire

import pandas as pd  # DataFrame pour la sortie structurée
import unicodedata  # Normalisation Unicode

try:  # pragma: no cover - import pypdf prioritaire
    from pypdf import PdfReader  # type: ignore[import]  # Lecteur PDF principal
except ImportError:  # pragma: no cover - compatibilité PyPDF2
    try:
        from PyPDF2 import PdfReader  # type: ignore[import]  # Fallback PyPDF2
    except ImportError:  # pragma: no cover - absence de dépendance
        class PdfReader:  # type: ignore
            """Substitut minimal rappelant d'installer pypdf/PyPDF2."""  # Message d'installation

            def __init__(self, *_args, **_kwargs):  # Constructeur factice
                raise ImportError(  # Lève explicitement l'erreur de dépendance manquante
                    "Une dépendance de lecture PDF est requise (pypdf ou PyPDF2). "
                    "Ajoutez-la via `pip install pypdf`."
                )
from docx import Document  # Lecture des fichiers DOCX

try:  # pragma: no cover - dépendance optionnelle pour la rétrocompatibilité
    from pdfminer.high_level import extract_text as pdfminer_extract_text  # type: ignore  # Extraction texte PDF
except ImportError:  # pragma: no cover - pdfminer n'est pas toujours installé
    pdfminer_extract_text = None  # Fallback à None si pdfminer absent

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
    (20.0, ("A", "C", "D", "F", "J", "K")),  # Groupe taux 20%
    (10.0, ("B", "H", "N", "T")),  # Groupe taux 10%
    (5.5, ("E", "I", "L", "P", "Q", "R", "S", "U", "V", "W", "Y")),  # Groupe taux 5.5%
    (2.1, ("M",)),  # Groupe taux 2.1%
    (0.0, ("G", "O", "X", "Z")),  # Groupe taux 0%
)  # Tableau des groupes TVA

DEFAULT_TVA_CODE_MAP: dict[str, float] = {
    code: rate  # Associe chaque code à son taux
    for rate, codes in _METRO_TVA_CODE_GROUPS  # Parcourt les groupes
    for code in codes  # Détaille les codes
}  # Mapping code -> taux

# Ce mapping est réutilisé par les extracteurs de lignes (ex. `_parse_detail_line`)
# pour attribuer automatiquement un taux de TVA lorsqu'un code METRO est trouvé.

DEFAULT_MARGIN_RATE = 0.0  # Marge par défaut (utilisable pour calcul prix de vente)


def _normalize_product_name(value: str | None) -> str:
    """Nettoie le nom produit (NFKC, apostrophes, espaces multiples)."""  # Docstring nettoyage nom
    if not value:  # Si aucun nom
        return ""  # Retourne vide
    text = unicodedata.normalize("NFKC", value)  # Normalise Unicode
    text = text.replace("’", "'")  # Remplace apostrophe typographique
    text = re.sub(r"\s+", " ", text)  # Compacte les espaces multiples
    return text.strip()  # Supprime espaces de bord


START_PATTERN = re.compile(r"^(?P<ean>\d{10,14})\s+(?P<article>\d{4,10})\s*(?P<label>.*)")  # Détecte début ligne produit
_INLINE_PRODUCT_SPLIT = re.compile(r"(?<!\n)(?:\s{2,})(?=\d{10,14}\s+\d{4,10}\s)")  # Rupture forcée pour PDF compact
SECTION_HEADER = re.compile(r"^\*{3}\s*(?P<section>[A-Z0-9ÉÈÀÂÊÎÔÛÇ\s]+)\s+Total\s*:", re.IGNORECASE)  # Sections
DATE_FACTURE_PATTERN = re.compile(
    r"date\s+facture\s*:\s*(?P<facture_date>\d{2}-\d{2}-\d{4}(?:\s+\d{2}:\d{2})?)",
    re.IGNORECASE,
)  # Date facture (DD-MM-YYYY)
FINAL_INVOICE_PATTERN = re.compile(r"FIN\s+DE\s+LA\s+FACTURE", re.IGNORECASE)  # Marque fin de facture
_TRAILING_ALPHA = re.compile(r"[A-Za-z]$")  # Lettre en fin de token (code TVA)
_METADATA_PATTERNS = (
    re.compile(r"⑨:.*", re.IGNORECASE),  # Lignes à ignorer
    re.compile(r"N°\s+GTIN.*", re.IGNORECASE),
    re.compile(r"PRIX AU KG OU AU LITRE:.*", re.IGNORECASE),
    re.compile(r"Plus\s*:\s*.*", re.IGNORECASE),
    re.compile(r"_BEST_BEFORE_DATE.*", re.IGNORECASE),
)  # Patterns de métadonnées à retirer

ParserHandler = Callable[[str], pd.DataFrame]  # Type de parseur
_PARSER_REGISTRY: dict[str, Callable[..., pd.DataFrame]] = {}  # Registre des parseurs


def register_invoice_parser(name: str, handler: Callable[..., pd.DataFrame]) -> None:
    """Expose un parseur supplémentaire (permet d'ajouter d'autres fournisseurs)."""  # Docstring enregistrement

    if not name or not callable(handler):  # Valide nom et handler
        return  # Ignore si invalide
    _PARSER_REGISTRY[name.strip().lower()] = handler  # Enregistre le parseur


def detect_invoice_format(raw_text: str, supplier_hint: str | None = None) -> str:
    """Détermine le parseur à utiliser selon le hint ou des heuristiques."""  # Docstring détection format

    if supplier_hint:  # Si un hint est fourni
        key = supplier_hint.strip().lower()  # Normalise le hint
        if key in _PARSER_REGISTRY:  # Si parseur enregistré
            return key  # Utilise ce parseur
    lowered = (raw_text or "").lower()  # Texte en minuscules pour heuristiques
    if "metro" in lowered:  # Détection Metro
        return "metro"
    if "pomona" in lowered or "passionfroid" in lowered:  # Détection Pomona
        return "pomona"
    if "transgourmet" in lowered:  # Détection Transgourmet
        return "transgourmet"
    return "generic"  # Fallback générique


def extract_products(
    raw_product_text: str,
    *,
    supplier_hint: str | None = None,
    margin_rate: float = 0.0,
) -> pd.DataFrame:
    """Route vers le parseur détecté (fallback générique)."""  # Docstring extraction principale

    parser_key = detect_invoice_format(raw_product_text, supplier_hint)  # Choisit le parseur
    handler = _PARSER_REGISTRY.get(parser_key)  # Récupère le handler
    if handler is None:  # Si aucun parseur trouvé
        handler = _PARSER_REGISTRY.get("generic", extract_products_from_metro_invoice)  # Fallback générique
    return handler(
        raw_product_text,
        margin_rate=margin_rate,
    )  # Exécute le parseur retenu


def clean_data(value):
    """Nettoie une valeur numérique (remplace la virgule par le point)."""  # Docstring nettoyage numérique
    if isinstance(value, str):  # Si valeur texte
        # Remplace la virgule par le point et supprime tout caractère non numérique/point/espace
        return value.replace(',', '.').replace('-', '').strip()  # Nettoie la chaîne
    return value  # Retourne la valeur brute sinon


def extract_text_from_file(uploaded_file):
    """Extrait le texte brut d'un fichier téléversé (PDF, DOCX, TXT, etc.)."""  # Docstring extraction texte

    # Le texte produit est ensuite parsé en lignes structurées par les fonctions
    # `_parse_detail_line` et `_parse_inline_summary`.

    # --- Préparation des métadonnées du fichier (nom, type, suffixe) ---
    file_name = str(getattr(uploaded_file, "name", "") or "")  # Nom de fichier
    file_type = str(getattr(uploaded_file, "type", "") or "").lower()  # Type MIME en minuscule
    file_suffix = Path(file_name).suffix.lower()  # Suffixe de fichier
    lowered_name = file_name.lower()  # Nom en minuscule

    # --- Lecture tolérante des bytes (supporte les fichiers-like et buffers mémoire) ---
    raw_bytes_data: bytes | bytearray | None = None  # Initialise les données brutes
    getvalue = getattr(uploaded_file, "getvalue", None)  # Méthode getvalue éventuelle
    if callable(getvalue):  # Si disponible
        try:
            raw_bytes_data = getvalue()  # Essaye de récupérer les bytes
        except Exception:  # Ignore erreurs
            raw_bytes_data = None

    if raw_bytes_data is None and hasattr(uploaded_file, "read"):  # Si pas de getvalue mais read dispo
        try:
            current_pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else None  # Position courante
            raw_bytes_data = uploaded_file.read()  # Lit le contenu
            if current_pos is not None and hasattr(uploaded_file, "seek"):  # Si reposition possible
                uploaded_file.seek(current_pos)  # Replace le curseur
        except Exception:  # Ignore erreurs
            raw_bytes_data = None

    raw_bytes = bytes(raw_bytes_data or b"")  # Cast en bytes (fallback vide)

    if hasattr(uploaded_file, "seek"):  # Si seek dispo
        try:
            uploaded_file.seek(0)  # Retourne au début
        except Exception:
            pass

    def _make_stream() -> io.BytesIO:  # Fabrique un flux mémoire réutilisable
        stream = io.BytesIO(raw_bytes)  # Crée le buffer
        stream.name = file_name  # type: ignore[attr-defined]  # Définit un nom pour compatibilité
        return stream  # Retourne le flux

    def _decode_bytes() -> str:  # Décodage tolérant du buffer
        if not raw_bytes:  # Si vide
            return ""  # Retourne chaîne vide
        try:
            return raw_bytes.decode("utf-8")  # Tente UTF-8
        except UnicodeDecodeError:
            return raw_bytes.decode("latin-1", errors="ignore")  # Fallback latin-1

    generic_types = {"application/octet-stream", "binary/octet-stream", ""}  # Types génériques
    is_text = (
        "text" in file_type
        or file_suffix in {".txt", ".csv"}
        or (file_type in generic_types and lowered_name.endswith((".txt", ".csv")))
    )  # Détection fichier texte
    is_docx = (
        "word" in file_type
        or "document" in file_type
        or "officedocument" in file_type
        or file_suffix in {".doc", ".docx"}
        or (file_type in generic_types and lowered_name.endswith(".docx"))
    )  # Détection DOCX
    is_pdf = False  # Flag PDF
    if "pdf" in file_type or file_suffix == ".pdf":  # MIME PDF ou suffixe
        is_pdf = True
    elif file_type in generic_types:  # Type générique
        is_pdf = lowered_name.endswith(".pdf") or raw_bytes.startswith(b"%PDF")  # Heuristique PDF

    if is_text:  # Cas texte
        return _decode_bytes()  # Retourne le texte décodé

    if is_pdf:  # Cas PDF
        try:
            pdf_reader = PdfReader(_make_stream())  # Lit le PDF
            text = "".join(page.extract_text() or "" for page in pdf_reader.pages)  # Concatène le texte des pages
            if text.strip():  # Si non vide
                return text  # Retourne le texte
        except Exception:  # pragma: no cover - tolérance erreurs PDF
            pass

        if pdfminer_extract_text is not None:  # Si pdfminer dispo
            try:
                text = pdfminer_extract_text(_make_stream())  # Extraction via pdfminer
                if text and text.strip():  # Si non vide
                    return text  # Retourne
            except Exception:  # pragma: no cover - tolérance
                pass

        decoded = _decode_bytes()  # Fallback décodage brut
        if decoded.strip():  # Si du texte lisible
            return decoded  # Retourne
        return "Erreur lors de la lecture du PDF."  # Message d'erreur générique

    if is_docx:  # Cas DOCX
        try:
            document = Document(_make_stream())  # Ouvre le DOCX
            return "\n".join(paragraph.text for paragraph in document.paragraphs)  # Concatène les paragraphes
        except Exception:  # pragma: no cover - tolérance erreurs docx
            return "Erreur lors de la lecture du fichier Word (.docx)."  # Message d'erreur

    return _decode_bytes()  # Fallback : décodage brut pour types inconnus


def _normalize_barcode(value: str | None) -> str:
    """Filtre les caractères non numériques, accepte 8–15 chiffres sinon compact uppercase."""  # Docstring normalisation code
    if not value:  # Si aucune valeur
        return ""  # Retourne vide
    digits = re.sub(r"\D", "", str(value))  # Supprime les non chiffres
    if 8 <= len(digits) <= 15:  # Longueur acceptable
        return digits  # Retourne la version digits-only
    compact = re.sub(r"\s+", "", str(value)).upper()  # Compacte et uppercase
    # Évite de renvoyer des codes TVA courts (ex: C2/C07) en guise d'EAN
    if len(compact) <= 3 and not compact.isdigit():
        return ""
    return compact  # Retourne la version compacte


def _normalise_tva_code(code: str | None) -> str | None:
    """Uniformise un code TVA (trim + upper)."""  # Docstring code TVA
    if not code:  # Pas de code
        return None  # Retourne None
    cleaned = str(code).strip().upper()  # Nettoie et uppercase
    return cleaned or None  # Retourne le code ou None si vide


def _resolve_tva_value(code: str | None, tva_lookup: Mapping[str, float], default_tva: float) -> float:
    """Retourne le taux de TVA correspondant à un code (fallback sur default_tva)."""  # Docstring résolution TVA
    if code is None:  # Aucun code fourni
        return default_tva  # Utilise la TVA par défaut
    if code in tva_lookup:  # Si code connu
        return float(tva_lookup[code])  # Retourne le taux associé
    return default_tva  # Sinon fallback défaut


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
)  # Mots-clés à ignorer dans les désignations


def _normalise_whitespace(value: str) -> str:
    """Compacte tous les espaces/retours à la ligne en espace unique."""  # Docstring compactage espaces
    return re.sub(r"\s+", " ", value or "").strip()  # Remplace séquences d'espaces par un simple et trim


def _should_skip_line(line: str) -> bool:
    """Filtre les lignes descriptives décoratives (duplicata, total, page…)."""  # Docstring filtrage lignes
    lowered = line.lower()  # Minuscule pour comparaison
    return any(keyword in lowered for keyword in _IGNORED_DESIGNATION_KEYWORDS)  # Vérifie présence de mots-clés


def _parse_decimal(value: str | None) -> float | None:
    """Parse un décimal tolérant (espaces insécables, virgule, signes)."""  # Docstring parse décimal
    if value is None:  # Aucun input
        return None  # Retourne None
    cleaned = (
        str(value)
        .replace("\u202f", "")
        .replace("\xa0", "")
        .replace(",", ".")
        .strip()
    )  # Nettoie espaces insécables et virgules
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)  # Retire tout sauf chiffres/point/signe
    if not cleaned:  # Si vide
        return None  # Retourne None
    try:
        return float(cleaned)  # Convertit en float
    except ValueError:  # En cas d'échec
        return None  # Retourne None


def _parse_int(value: str | None) -> int | None:
    """Parse un entier en s’appuyant sur _parse_decimal (arrondi)."""  # Docstring parse entier
    decimal = _parse_decimal(value)  # Parse en décimal
    if decimal is None:  # Si absent
        return None  # Retourne None
    return int(round(decimal))  # Arrondi puis converti en int


def _parse_detail_tail_candidate(tokens: list[str]) -> dict[str, object] | None:
    """Tente de décoder la fin d'une ligne détaillée (PU, quantité, colisage, montant, TVA)."""  # Docstring parsing queue
    working = tokens[:]  # Copie des tokens
    if not working:  # Si vide
        return None  # Aucun résultat

    tva_code: str | None = None  # Code TVA éventuellement présent
    if _TRAILING_ALPHA.fullmatch(working[-1]):  # Dernier token = lettre
        tva_code = working.pop().upper()  # Extrait code TVA

    if len(working) != 8:  # Doit rester 8 tokens numériques attendus
        return None  # Sinon pattern non reconnu

    regie = working[0]  # Première lettre = régie
    if not re.fullmatch(r"[A-Za-z]", regie):  # Vérifie une lettre
        return None  # Échec si pas une lettre

    volume = _parse_decimal(working[1])  # Volume en litres
    vap = _parse_decimal(working[2])  # VAP
    poids_unitaire = _parse_decimal(working[3])  # Poids unitaire
    unit_price = _parse_decimal(working[4])  # Prix unitaire
    quantity = _parse_int(working[5])  # Quantité colis
    colisage = _parse_int(working[6])  # Colisage
    total_amount = _parse_decimal(working[7])  # Montant total

    if unit_price is None or quantity is None or total_amount is None:  # Champs indispensables
        return None  # Échec si manquants

    detail: dict[str, object] = {
        "regie": regie.upper(),
        "volume_litre": volume or 0.0,
        "vap": vap or 0.0,
        "poids_unitaire": poids_unitaire or 0.0,
        "prix_unitaire": round(unit_price, 2),
        "quantite_colis": max(quantity, 0),
        "colisage": max(colisage or 1, 1),
        "montant_total": round(total_amount, 2),
    }  # Détails extraits de la queue

    if tva_code:  # Si code TVA présent
        detail["tva_code"] = tva_code  # Ajoute le code
    return detail  # Retourne le dictionnaire


def _parse_detail_tail_tokens(tokens: list[str]) -> tuple[dict[str, object], int] | None:
    """Balaye la fin de ligne pour extraire le bloc numérique + TVA et retourne aussi le nombre de tokens consommés."""  # Docstring scan queue
    for window in (9, 8):  # Essaye fenêtre 9 puis 8 tokens
        if len(tokens) < window:  # Si pas assez long
            continue  # Passe à la suivante
        candidate = tokens[-window:]  # Sélectionne la fenêtre de fin
        detail = _parse_detail_tail_candidate(candidate)  # Tente le parsing
        if detail:  # Si réussi
            consumed = window  # Tokens consommés
            if "tva_code" not in detail and window == 9:  # Si pas de code TVA mais fenêtre 9
                consumed = 8  # Considère 8 tokens consommés
            return detail, consumed  # Retourne le détail et la fenêtre utilisée
    return None  # Aucun pattern reconnu


def _parse_detail_line(line: str) -> dict[str, object] | None:
    """Parse une ligne produit METRO “densifiée” (regie, volume, prix, quantité, TVA)."""  # Docstring parse ligne compacte
    tokens = _normalise_whitespace(line).split()  # Tokenise la ligne nettoyée
    if len(tokens) >= 8 and re.fullmatch(r"[A-Za-z]", tokens[0]):  # Vérifie structure minimale
        working = tokens[:]  # Copie de travail
        tva_code: str | None = None  # Code TVA éventuel
        if re.fullmatch(r"[A-Za-z]", working[-1]):  # Dernier token lettre
            tva_code = working[-1].upper()  # Sauvegarde le code TVA
            working = working[:-1]  # Retire le code des tokens

        if len(working) >= 8:  # Besoin d'au moins 8 tokens restants
            regie = working[0]  # Régie
            volume = _parse_decimal(working[1])  # Volume
            vap = _parse_decimal(working[2])  # VAP
            poids_unitaire = _parse_decimal(working[3])  # Poids unitaire
            unit_price = _parse_decimal(working[4])  # Prix unitaire
            quantity = _parse_int(working[5])  # Quantité colis
            colisage = _parse_int(working[6])  # Colisage
            total_amount = _parse_decimal(working[7])  # Montant total

            if unit_price is not None and quantity is not None and total_amount is not None:  # Validation
                detail: dict[str, object] = {
                    "regie": regie.upper(),
                    "volume_litre": volume or 0.0,
                    "vap": vap or 0.0,
                    "poids_unitaire": poids_unitaire or 0.0,
                    "prix_unitaire": round(unit_price, 2),
                    "quantite_colis": max(quantity, 0),
                    "colisage": max(colisage or 1, 1),
                    "montant_total": round(total_amount, 2),
                }  # Détail extrait

                if tva_code:  # Si code TVA existe
                    detail["tva_code"] = tva_code  # Ajoute au résultat

                if len(working) > 8:  # S'il reste des tokens supplémentaires
                    extras = working[8:]  # Récupère les tokens restants
                    if extras:  # Si non vide
                        detail["extra"] = " ".join(extras)  # Stocke les extras

                return detail  # Retourne le détail

    # Si aucune d’entre elles ne correspond, on déclenche la détection des queues
    # en utilisant `_parse_detail_tail_tokens`.
    tail_probe = _parse_detail_tail_tokens(tokens)  # Tente le parsing de queue
    if tail_probe:  # Si succès
        return tail_probe[0]  # Retourne le détail trouvé
    return None  # Aucun parsing réussi


def _parse_inline_summary(label: str) -> dict[str, object] | None:
    """Parse une ligne “compacte” (nom + bloc numérique en fin de ligne)."""  # Docstring parsing inline
    tokens = _normalise_whitespace(label).split()  # Tokenise la ligne
    if len(tokens) < 4:  # Trop court
        return None  # Échec

    tail_probe = _parse_detail_tail_tokens(tokens)  # Tente parsing queue numérique
    if tail_probe:  # Si succès
        detail, consumed = tail_probe  # Détail et tokens consommés
        designation = " ".join(tokens[:-consumed]).strip()  # Reste = désignation
        if designation:  # Si libellé non vide
            detail["nom"] = designation  # Ajoute le nom
            return detail  # Retourne le détail complet

    tva_code = None  # Code TVA éventuel
    if re.fullmatch(r"[A-Za-z]", tokens[-1]):  # Dernier token lettre
        tva_code = tokens.pop().upper()  # Extrait code TVA

    tail_values: list[float] = []  # Valeurs numériques extraites
    tail_indices: list[int] = []  # Indices correspondants
    idx = len(tokens) - 1  # Index de parcours inversé
    while idx >= 0 and len(tail_values) < 4:  # Parcourt jusqu'à 4 valeurs
        value = _parse_decimal(tokens[idx])  # Tente parse décimal
        if value is None:  # Arrêt si non numérique
            break
        tail_values.append(value)  # Ajoute valeur
        tail_indices.append(idx)  # Stocke l'indice
        idx -= 1  # Décrémente l'index

    if len(tail_values) < 2:  # Besoin au moins 2 valeurs (montant, quantité)
        return None  # Échec

    for remove_index in sorted(tail_indices, reverse=True):  # Supprime les tokens numériques identifiés
        tokens.pop(remove_index)

    montant_total = tail_values[0]  # Première valeur = montant total
    quantity_value = tail_values[1]  # Deuxième = quantité
    colisage_value = tail_values[2] if len(tail_values) >= 3 and len(tail_values) != 3 else None  # Colisage éventuel
    unit_price_value = tail_values[3] if len(tail_values) == 4 else (
        tail_values[2] if len(tail_values) == 3 else tail_values[1]
    )  # Prix unitaire déduit

    price = float(unit_price_value)  # Prix unitaire en float
    quantity = _parse_int(str(quantity_value))  # Quantité en int

    if quantity is None:  # Quantité invalide
        return None  # Échec

    colisage = _parse_int(str(colisage_value)) if colisage_value is not None else 1  # Colisage en int
    if colisage is None or colisage <= 0:  # Si invalide
        colisage = 1  # Fallback à 1

    regie = None  # Régie éventuelle
    volume = vap = poids = None  # Mesures éventuelles
    regie_idx = len(tokens) - 1  # Index de recherche
    regie_numbers: list[float] = []  # Valeurs numériques associées à la régie
    probe_idx = regie_idx  # Position de sondage
    while probe_idx >= 0 and len(regie_numbers) < 3:  # Parcours arrière pour récupérer volume/vap/poids
        candidate_value = _parse_decimal(tokens[probe_idx])  # Valeur numérique potentielle
        if candidate_value is None:  # Arrêt si non numérique
            break
        regie_numbers.append(candidate_value)  # Ajoute
        probe_idx -= 1  # Recule d'un token
    if (
        probe_idx >= 0
        and regie_numbers
        and re.fullmatch(r"[A-Za-z]", tokens[probe_idx])
    ):  # Si une lettre précède les valeurs
        regie = tokens[probe_idx].upper()  # Régie détectée
        tokens = tokens[:probe_idx]  # Tronque les tokens avant la régie
        regie_numbers = list(reversed(regie_numbers))  # Remet les valeurs dans l'ordre
        if regie_numbers:  # Affecte volume
            volume = regie_numbers[0]
        if len(regie_numbers) >= 2:  # Affecte vap
            vap = regie_numbers[1]
        if len(regie_numbers) >= 3:  # Affecte poids
            poids = regie_numbers[2]

    designation = " ".join(tokens).strip()  # Recompose la désignation
    if not designation:  # Si vide
        return None  # Échec

    detail: dict[str, object] = {
        "nom": designation,
        "prix_unitaire": round(price, 2),
        "quantite_colis": max(quantity, 0),
        "colisage": colisage,
        "montant_total": round(
            montant_total if montant_total is not None else price * max(quantity, 0) * colisage,
            2,
        ),
    }  # Détail construit

    if tva_code:  # Ajoute le code TVA si présent
        detail["tva_code"] = tva_code
    if regie:  # Ajoute la régie si trouvée
        detail["regie"] = regie
    if volume is not None:  # Ajoute volume
        detail["volume_litre"] = float(volume)
    if vap is not None:  # Ajoute VAP
        detail["vap"] = float(vap)
    if poids is not None:  # Ajoute poids
        detail["poids_unitaire"] = float(poids)

    return detail  # Retourne le détail final


def _join_designation(parts: Sequence[str]) -> str:
    """Assemble proprement les lignes descriptives (supprime bruit et mots-clés ignorés)."""  # Docstring assemblage designation
    cleaned: list[str] = []  # Lignes retenues
    for part in parts:  # Parcourt chaque morceau
        normalised = _normalise_whitespace(part)  # Nettoie la ligne
        if not normalised or _should_skip_line(normalised):  # Ignore lignes vides/bruit
            continue
        cleaned.append(normalised)  # Ajoute la ligne utile
    return " ".join(cleaned).strip()  # Concatène et trim


def _ensure_margin(purchase: float | None, sale: float | None, margin: float) -> float | None:
    """Garantit un prix de vente minimum (prix achat + marge) si la vente est manquante/inférieure."""  # Docstring marge
    if purchase is None:  # Si pas de prix d'achat
        return sale  # Retourne le prix de vente fourni
    safe_margin = max(0.0, float(margin))  # Marge non négative
    baseline = round(float(purchase) * (1.0 + safe_margin), 2)  # Prix minimal
    if sale is None:  # Si pas de vente fournie
        return baseline  # Utilise baseline
    return round(sale if sale >= baseline else baseline, 2)  # Choisit max(baseline, sale)


def _segment_invoice_lines(raw_product_text: str) -> list[str]:
    """Retourne des lignes exploitables même si le PDF compacte tout sur une seule ligne."""  # Docstring segmentation

    normalised_text = (raw_product_text or "").replace("\r", "")  # Retire CR
    raw_lines = normalised_text.splitlines()  # Découpe sur LF
    if any(START_PATTERN.match(line.strip()) for line in raw_lines):  # Si lignes déjà découpées
        return raw_lines  # Retourne tel quel
    # Certains PDF Metro n'incluent pas de retours chariot entre les produits.
    # Dans ce cas on force une rupture dès que l'on détecte un EAN suivi d'un numéro d'article.
    injected = _INLINE_PRODUCT_SPLIT.sub("\n", normalised_text)  # Insère des retours via regex
    injected = re.sub(r"(?<!\n)(?=\d{10,14}\s+\d{4,10}\s)", "\n", injected)  # Autre heuristique de rupture
    return injected.splitlines()  # Retourne les lignes injectées


def _strip_invoice_metadata(line: str) -> str:
    """Supprime les blocs répétitifs ou métadonnées non pertinentes."""  # Docstring nettoyage métadonnées
    cleaned = line or ""  # Copie la ligne
    for pattern in _METADATA_PATTERNS:  # Parcourt les patterns à supprimer
        cleaned = pattern.sub("", cleaned)  # Supprime les occurrences
    return cleaned.strip()  # Retourne la ligne épurée


def extract_products_from_metro_invoice(
    raw_product_text: str,
    *,
    tva_map: Mapping[str, float] | None = None,
    default_tva: float = 20.0,
    margin_rate: float = 0.0,
) -> pd.DataFrame:
    """Analyse une facture METRO : parse lignes, infère prix/quantités/TVA et construit un DataFrame standardisé."""  # Docstring parseur Metro
    overrides = {k.upper(): float(v) for k, v in (tva_map or {}).items()}  # Override éventuel des taux TVA
    lookup = {**DEFAULT_TVA_CODE_MAP, **overrides}  # Mapping TVA final
    margin = DEFAULT_MARGIN_RATE  # Marge par défaut (non utilisée ici)
    invoice_sequence = 0  # Compteur de factures dans le PDF
    current_invoice_id: str | None = None  # Identifiant facture en cours
    current_invoice_date: str | None = None  # Date facture en cours
    pending_invoice_date: str | None = None  # Date rencontrée en attente

    # --- Pré-segmentation et nettoyage des lignes brutes (couple original/normalisé) ---
    prepared_lines = [
        (
            chunk,  # Ligne originale
            _normalise_whitespace(_strip_invoice_metadata(chunk)),  # Ligne normalisée/épuree
        )
        for chunk in _segment_invoice_lines(raw_product_text)
    ]

    # accumulateurs d'état pour parcourir la facture
    records: list[dict[str, object]] = []  # Lignes collectées
    current_section: str | None = None  # Section courante (régie)
    current_invoice_date: str | None = None  # Date facture courante
    current: dict[str, object] | None = None  # Ligne en construction
    designation_parts: list[str] = []  # Fragments de désignation accumulés

    def _parse_vertical_detail(start_index: int) -> tuple[dict[str, object] | None, int]:
        """Interprète un bloc vertical sur 3-4 lignes (prix, quantité, montant, TVA)."""  # Docstring bloc vertical
        collected: list[str] = []  # Lignes collectées
        j = start_index  # Index courant
        total_lines = len(prepared_lines)  # Nombre de lignes total
        while j < total_lines and len(collected) < 4:  # Parcourt jusqu'à 4 lignes utiles
            raw, candidate = prepared_lines[j]  # Ligne brute et normalisée
            if not candidate:  # Ignore vides
                j += 1
                continue
            if START_PATTERN.match(candidate) or SECTION_HEADER.match(raw):  # Arrête si nouvelle section/ligne produit
                break
            cleaned = candidate.strip()  # Nettoie
            lowered = cleaned.lower()  # Minuscule pour tests
            numeric_discount = cleaned.endswith('-') and cleaned[:-1].replace(',', '').replace('.', '').isdigit()  # Remise numérique
            if lowered.startswith("offre ") or lowered.startswith("mention ") or cleaned.startswith("—") or numeric_discount:  # Ignore lignes d'offre/mention
                j += 1
                continue
            if cleaned in {"p", "promo", "offre"}:  # Ignore labels courts
                j += 1
                continue
            collected.append(cleaned)  # Ajoute la ligne utile
            j += 1  # Passe à la suivante

        if len(collected) < 3:  # Besoin d'au moins 3 lignes (prix/qty/montant)
            return None, start_index  # Échec, retourne l'index initial

        price = _parse_decimal(collected[0].split()[0])  # Prix unitaire
        qty_tokens = collected[1].split()  # Tokens quantité/colisage
        amount = _parse_decimal(collected[2].split()[0])  # Montant total
        tva_code = None  # Code TVA éventuel
        if len(collected) >= 4 and len(collected[3]) == 1 and collected[3].isalpha():  # Code TVA lettre seule
            tva_code = collected[3].upper()
        elif len(collected) >= 4 and len(collected[3].split()) == 1 and collected[3].split()[0].isalpha():  # Variante
            tva_code = collected[3].split()[0].upper()

        quantite = _parse_int(qty_tokens[0]) or 0  # Quantité colis
        colisage = _parse_int(qty_tokens[1]) if len(qty_tokens) >= 2 else 1  # Colisage (par défaut 1)

        if price is None:  # Prix indispensable
            return None, start_index  # Échec si manquant

        detail: dict[str, object] = {
            "prix_unitaire": round(price, 2),
            "quantite_colis": quantite,
            "colisage": max(colisage or 1, 1),
            "montant_total": round(amount if amount is not None else price * max(quantite, 0) * max(colisage or 1, 1), 2),
        }  # Détail de prix/quantité/montant
        if tva_code:  # Ajoute code TVA si trouvé
            detail["tva_code"] = tva_code
        return detail, j  # Retourne le détail et le nouvel index

    i = 0  # Index de boucle principale
    total = len(prepared_lines)  # Nombre total de lignes
    while i < total:  # Parcourt toutes les lignes préparées
        raw_line, line = prepared_lines[i]  # Ligne brute et normalisée
        i += 1  # Incrémente l'index principal
        # Capture/propagation de la date de facture tant qu'on reste dans le document
        date_match = DATE_FACTURE_PATTERN.search(raw_line)  # Cherche une date de facture
        if date_match:  # Si trouvée
            pending_invoice_date = date_match.group("facture_date").strip()  # Stocke la date en attente
            continue  # Passe à la ligne suivante
        if FINAL_INVOICE_PATTERN.search(raw_line):  # Si fin de facture détectée
            current_invoice_id = None  # Réinitialise l'ID facture
            current_invoice_date = None  # Réinitialise la date facture
            pending_invoice_date = None  # Réinitialise la date en attente
            continue  # Passe à la ligne suivante
        # Détection des blocs "*** SECTION Total :" (renseigne la régie/section courante)
        section_match = SECTION_HEADER.match(raw_line)  # Détecte un header de section
        if section_match:  # Si section trouvée
            current_section = _normalise_whitespace(section_match.group("section") or "")  # Mémorise la section
            continue  # Passe à la suite

        if not line:  # Ignore lignes vides
            continue

        start_match = START_PATTERN.match(line)  # Détecte une nouvelle ligne produit
        if start_match:  # Si match
            if pending_invoice_date is not None:  # Si une date était en attente
                needs_new_invoice = current_invoice_id is None or current_invoice_date != pending_invoice_date  # Nouveau document ?
                if needs_new_invoice:  # Si nouvelle facture
                    invoice_sequence += 1  # Incrémente le compteur
                    current_invoice_id = f"INV-{invoice_sequence:03d}"  # Génère un ID
                elif current_invoice_id is None:  # Cas de fallback
                    invoice_sequence += 1
                    current_invoice_id = f"INV-{invoice_sequence:03d}"
                current_invoice_date = pending_invoice_date  # Applique la date
                pending_invoice_date = None  # Vide la date en attente
            elif current_invoice_id is None:  # Pas de facture active
                invoice_sequence += 1  # Incrémente le compteur
                current_invoice_id = f"INV-{invoice_sequence:03d}"  # Crée un ID

            # Arrivée d'un nouvel article : flush du précédent si complet
            if current and "prix_unitaire" in current:  # Si une ligne précédente existait
                current.pop("__detail_complete", None)  # Retire le flag interne
                designation = _join_designation(designation_parts)  # Construit la désignation
                if designation:
                    current["nom"] = designation  # Affecte le nom
                if "montant_total" not in current:  # Calcule montant total si absent
                    qty = int(current.get("quantite_colis", 0))
                    colis = int(current.get("colisage", 1))
                    current["montant_total"] = round(
                        float(current["prix_unitaire"]) * max(qty, 0) * max(colis, 1),
                        2,
                    )
                if current_invoice_date and not current.get("facture_date"):
                    current["facture_date"] = current_invoice_date  # Ajoute la date facture
                if current_invoice_id and not current.get("invoice_id"):
                    current["invoice_id"] = current_invoice_id  # Ajoute l'ID facture
                records.append(current)  # Stocke la ligne finalisée

            current = {
                "codes": start_match.group("ean"),
                "numero_article": start_match.group("article"),
                "section": current_section,
                "__detail_complete": False,
                "invoice_id": current_invoice_id,
            }  # Nouvelle ligne courante
            if current_invoice_date:  # Ajoute la date si connue
                current["facture_date"] = current_invoice_date
            label = start_match.group("label").strip()  # Récupère la désignation brute

            inline_detail = _parse_inline_summary(label)  # Tente parse inline
            if inline_detail:  # Si réussi
                # Cas où tout est déjà sur la même ligne (designation + prix/qty/TVA)
                if "nom" in inline_detail:
                    current["nom"] = inline_detail.pop("nom")  # Affecte le nom et retire du dict
                current.update(inline_detail)  # Ajoute le reste des détails
                current["__detail_complete"] = True  # Marque comme complet
                designation_parts = []  # Réinitialise les fragments de nom
            else:  # Sinon, tente un bloc vertical ou queue numérique
                detail, new_index = _parse_vertical_detail(i)  # Parse les lignes suivantes
                if detail:  # Si bloc vertical trouvé
                    # Cas des blocs verticaux (prix/qty/montant/TVA sur les lignes suivantes)
                    current.update(detail)  # Ajoute détails
                    current["__detail_complete"] = True  # Marque complet
                    i = new_index  # Avance l'index principal
                    designation_parts = []  # Réinitialise fragments
                else:
                    inline_tokens = _normalise_whitespace(label).split()  # Tokenise la désignation
                    tail_probe = _parse_detail_tail_tokens(inline_tokens)  # Tente parsing queue numérique
                    if tail_probe:  # Si trouvé
                        # On récupère le bloc numérique en fin de ligne si présent
                        detail, consumed = tail_probe
                        current.update(detail)  # Ajoute détails
                        current["__detail_complete"] = True  # Marque complet
                        inline_tokens = inline_tokens[:-consumed]  # Retire la queue numérique de la désignation
                    designation_text = " ".join(inline_tokens).strip()  # Recompose le nom
                    designation_parts = [designation_text] if designation_text else []  # Initialise les fragments

            continue  # Passe à la prochaine ligne

        if current is None:  # Si aucun contexte courant
            continue  # Ignore la ligne

        if current.get("__detail_complete"):  # Si la ligne courante est déjà complète
            continue  # Ignore la ligne

        detail = _parse_detail_line(line)  # Tente de parse la ligne comme détail
        if detail:  # Si succès
            current.update(detail)  # Ajoute les détails
            current["__detail_complete"] = True  # Marque complet
            continue  # Passe à la suite

        if not _should_skip_line(line):  # Si la ligne n'est pas bruit
            designation_parts.append(line)  # Ajoute comme partie de désignation

    if current and "prix_unitaire" in current:  # Flush de la dernière ligne courante
        current.pop("__detail_complete", None)  # Retire le flag interne
        designation = _join_designation(designation_parts)  # Construit le nom
        if designation:
            current["nom"] = designation  # Affecte le nom
        if "montant_total" not in current:  # Calcule montant total si manquant
            qty = int(current.get("quantite_colis", 0))
            colis = int(current.get("colisage", 1))
            current["montant_total"] = round(
                float(current["prix_unitaire"]) * max(qty, 0) * max(colis, 1),
                2,
            )
        if current_invoice_date and not current.get("facture_date"):
            current["facture_date"] = current_invoice_date  # Associe la date facture
        if current_invoice_id and not current.get("invoice_id"):
            current["invoice_id"] = current_invoice_id  # Associe l'ID facture
        records.append(current)  # Ajoute la ligne finale

    if not records:  # Si aucune ligne extraite
        return pd.DataFrame(columns=[
            'nom',
            'codes',
            'numero_article',
            'section',
            'qte_init',
            'prix_achat',
            'prix_vente',
            'tva',
            'tva_code',
            'montant_total_facture',
            'facture_date',
        ])  # Retourne un DataFrame vide structuré

    normalised: list[dict[str, object]] = []  # Liste des lignes normalisées

    # Post-traitement : harmonisation des champs, calcul quantités, montants, TVA et marge
    for record in records:  # Parcourt chaque ligne brute
        designation = _normalize_product_name(record.get("nom", ""))  # Nom nettoyé
        if not designation:  # Ignore si vide
            continue

        ean = _normalize_barcode(record.get("codes"))  # Normalise le code EAN
        article = str(record.get("numero_article", "")).strip()  # Numéro article nettoyé
        unit_price = _parse_decimal(record.get("prix_unitaire"))  # Prix unitaire float
        qty = _parse_int(record.get("quantite_colis")) or 0  # Quantité colis int
        colis = _parse_int(record.get("colisage")) or 1  # Colisage int
        total_units = max(qty, 0) * max(colis, 1)  # Quantité totale d'unités
        amount = _parse_decimal(record.get("montant_total"))  # Montant total facturé
        tva_code = _normalise_tva_code(record.get("tva_code"))  # Code TVA normalisé
        tva_value = _resolve_tva_value(tva_code, lookup, default_tva)  # Taux TVA retenu

        if unit_price is None:  # Prix unitaire indispensable
            continue  # Ignore la ligne

        sale_price_ht = _ensure_margin(unit_price, None, margin_rate)  # Prix de vente HT avec marge minimale
        if sale_price_ht is None:  # Si None
            sale_price_ht = float(unit_price)  # Fallback au prix achat
        sale_price_ht = round(sale_price_ht, 2)  # Arrondi
        montant_ht = round(unit_price * total_units, 2)  # Montant HT
        montant_tva = round(montant_ht * (tva_value / 100.0), 2)  # TVA
        montant_ttc = round(montant_ht + montant_tva, 2)  # TTC

        # Assemblage final de la ligne normalisée (tous champs structurés)
        normalised.append(
            {
                "nom": designation,
                "codes": ean,
                "numero_article": article,
                "section": record.get("section"),
                "regie": record.get("regie"),
                "volume_litre": round(float(record.get("volume_litre", 0.0)), 3),
                "vap": round(float(record.get("vap", 0.0)), 3),
                "poids_unitaire": round(float(record.get("poids_unitaire", 0.0)), 3),
                "quantite_colis": qty,
                "colisage": colis,
                "qte_init": total_units,
                "prix_achat": round(unit_price, 2),
                "prix_vente": sale_price_ht,
                "prix_vente_minimum": sale_price_ht,
                "tva": round(tva_value, 2),
                "tva_code": tva_code,
                "montant_ht": montant_ht,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc,
                "montant_total_facture": round(
                    amount if amount is not None else unit_price * total_units,
                    2,
                ),
                "facture_date": record.get("facture_date"),
                "invoice_id": record.get("invoice_id") or f"INV-{max(invoice_sequence, 1):03d}",
            }
        )  # Ajoute la ligne normalisée

    df = pd.DataFrame(normalised)  # Crée le DataFrame final
    if df.empty:  # Si vide
        return df  # Retourne tel quel

    desired_order: Iterable[str] = (
        "nom",
        "codes",
        "numero_article",
        "section",
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
        "facture_date",
        "invoice_id",
    )  # Ordre souhaité des colonnes
    available = [col for col in desired_order if col in df.columns]  # Filtre les colonnes existantes
    return df.loc[:, available]  # Retourne les colonnes dans l'ordre


def extract_products_from_generic_invoice(
    raw_product_text: str,
    *,
    margin_rate: float = 0.0,
) -> pd.DataFrame:
    """Parseur générique - fallback vers le parseur Metro en attendant d'autres formats."""  # Docstring parseur générique

    return extract_products_from_metro_invoice(raw_product_text, margin_rate=margin_rate)  # Délègue au parseur Metro


# Parseurs spécifiques

def extract_products_from_pomona_invoice(raw_product_text: str, *, margin_rate: float = 0.0) -> pd.DataFrame:
    """Prétraitement Pomona (numerotation différente, colonnes séparées par tab)."""  # Docstring parseur Pomona

    normalized = raw_product_text.replace("\t", " ")  # Remplace tabs par espaces
    normalized = normalized.replace("FACTURE PASSIONFROID", "")  # Nettoie l'en-tête spécifique
    return extract_products_from_metro_invoice(normalized, margin_rate=margin_rate)  # Délègue au parseur Metro


def extract_products_from_transgourmet_invoice(raw_product_text: str, *, margin_rate: float = 0.0) -> pd.DataFrame:
    """Transgourmet : colonnes alignées, suffixes 'HT'. Enlève mentions spécifiques."""  # Docstring parseur Transgourmet

    normalized = raw_product_text.replace("HT", "")  # Supprime les suffixes HT
    normalized = normalized.replace("TTC", "")  # Supprime TTC
    return extract_products_from_metro_invoice(normalized, margin_rate=margin_rate)  # Délègue au parseur Metro


# Enregistre les parseurs connus
register_invoice_parser("metro", extract_products_from_metro_invoice)
register_invoice_parser("generic", extract_products_from_generic_invoice)
register_invoice_parser("pomona", extract_products_from_pomona_invoice)
register_invoice_parser("transgourmet", extract_products_from_transgourmet_invoice)
