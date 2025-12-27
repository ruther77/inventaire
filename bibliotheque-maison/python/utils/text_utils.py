"""Utilitaires de traitement de texte.

Ce module fournit des fonctions pures pour le traitement de texte,
la comparaison de chaînes et la normalisation.

Fonctions principales:
- fuzzy_match: Calcule la similarité entre deux chaînes
- normalize_text: Normalise le texte (espaces, casse)
- normalize_product_name: Normalise un nom de produit avec synonymes
- split_paragraphs: Découpe un texte en paragraphes
- chunk_with_overlap: Découpe un texte en chunks avec chevauchement

Exemples:
    >>> fuzzy_match("BIERE BLONDE", "BIÈRE BLONDE")
    0.923...

    >>> normalize_text("  Hello   World  ")
    "Hello World"
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple


def fuzzy_match(str1: str, str2: str, case_sensitive: bool = False) -> float:
    """Calcule la similarité entre deux chaînes (ratio de Levenshtein).

    Utilise l'algorithme SequenceMatcher de difflib qui calcule le ratio
    de similarité basé sur les sous-séquences communes les plus longues.

    Args:
        str1: Première chaîne
        str2: Deuxième chaîne
        case_sensitive: Si False, compare en ignorant la casse (défaut: False)

    Returns:
        Score de similarité entre 0.0 (différent) et 1.0 (identique)

    Examples:
        >>> fuzzy_match("Hello", "hello")
        1.0

        >>> fuzzy_match("Hello", "hello", case_sensitive=True)
        0.6

        >>> fuzzy_match("BIERE BLONDE", "BIÈRE BLONDE")
        0.923...

        >>> fuzzy_match("abc", "xyz")
        0.0
    """
    s1 = str1.strip()
    s2 = str2.strip()

    if not case_sensitive:
        s1 = s1.upper()
        s2 = s2.upper()

    return SequenceMatcher(None, s1, s2).ratio()


def normalize_text(text: str) -> str:
    """Normalise le texte en simplifiant les espaces.

    Cette fonction:
    - Supprime les espaces en début/fin
    - Remplace les séquences d'espaces multiples par un seul espace
    - Gère les tabulations et retours à la ligne

    Args:
        text: Texte à normaliser

    Returns:
        Texte normalisé

    Examples:
        >>> normalize_text("  Hello   World  ")
        "Hello World"

        >>> normalize_text("Line1\\n\\nLine2")
        "Line1 Line2"
    """
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_product_name(
    name: str,
    synonyms: Optional[Dict[str, str]] = None,
    uppercase: bool = True,
) -> str:
    """Normalise un nom de produit avec application de synonymes.

    Cette fonction:
    1. Supprime les espaces en début/fin
    2. Applique les synonymes si définis
    3. Convertit en majuscules (optionnel)

    Args:
        name: Nom du produit à normaliser
        synonyms: Dictionnaire de synonymes {nom_original: nom_normalisé}
        uppercase: Convertir en majuscules (défaut: True)

    Returns:
        Nom normalisé

    Examples:
        >>> normalize_product_name("  bière blonde  ")
        "BIÈRE BLONDE"

        >>> synonyms = {"HEINEKEIN": "HEINEKEN"}
        >>> normalize_product_name("HEINEKEIN", synonyms=synonyms)
        "HEINEKEN"
    """
    name = name.strip()

    if synonyms and name in synonyms:
        name = synonyms[name]

    if uppercase:
        name = name.upper().strip()

    return name


def split_paragraphs(text: str, normalize: bool = True) -> List[str]:
    """Découpe un texte en paragraphes (séparés par lignes vides).

    Args:
        text: Texte à découper
        normalize: Si True, normalise chaque paragraphe (défaut: True)

    Returns:
        Liste des paragraphes non vides

    Examples:
        >>> split_paragraphs("Para1\\n\\nPara2\\n\\nPara3")
        ["Para1", "Para2", "Para3"]
    """
    parts = re.split(r"\n{2,}", text)

    if normalize:
        cleaned = [normalize_text(p) for p in parts if normalize_text(p)]
    else:
        cleaned = [p.strip() for p in parts if p.strip()]

    return cleaned


def chunk_with_overlap(
    paragraphs: List[str],
    target_tokens: int = 220,
    overlap: int = 40,
    chunk_id_prefix: str = "chunk",
) -> List[Tuple[str, str]]:
    """Crée des chunks avec chevauchement à partir de paragraphes.

    Cette fonction est utile pour:
    - Découper des documents pour embeddings ML
    - Préparer du texte pour la recherche sémantique
    - Créer des contextes pour LLM

    Args:
        paragraphs: Liste de paragraphes à découper
        target_tokens: Nombre de tokens cible par chunk (défaut: 220)
        overlap: Nombre de tokens de chevauchement entre chunks (défaut: 40)
        chunk_id_prefix: Préfixe pour les identifiants de chunk

    Returns:
        Liste de tuples (chunk_id, texte)

    Examples:
        >>> paras = ["Premier paragraphe...", "Second paragraphe très long..."]
        >>> chunks = chunk_with_overlap(paras, target_tokens=50, overlap=10)
        >>> len(chunks) > 0
        True
    """
    chunks: List[Tuple[str, str]] = []
    buffer: List[str] = []
    token_count = 0
    chunk_idx = 0

    def flush():
        nonlocal buffer, token_count, chunk_idx
        if not buffer:
            return
        text = " ".join(buffer).strip()
        if text:
            chunks.append((f"{chunk_id_prefix}_{chunk_idx:04d}", text))
            chunk_idx += 1
        # Recule pour l'overlap
        if overlap > 0:
            tokens = " ".join(buffer).split()
            buffer = tokens[-overlap:] if len(tokens) > overlap else tokens[:]
            token_count = len(buffer)
        else:
            buffer = []
            token_count = 0

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        # Les titres (commençant par #) forcent un flush
        if words[0].startswith("#"):
            flush()

        buffer.extend(words)
        token_count += len(words)

        if token_count >= target_tokens:
            flush()

    # Flush final
    flush()

    return chunks


def extract_keywords(
    text: str,
    min_length: int = 3,
    max_keywords: int = 20,
    stopwords: Optional[set] = None,
) -> List[str]:
    """Extrait les mots-clés d'un texte.

    Args:
        text: Texte source
        min_length: Longueur minimale des mots (défaut: 3)
        max_keywords: Nombre maximum de mots-clés (défaut: 20)
        stopwords: Ensemble de mots à ignorer (optionnel)

    Returns:
        Liste des mots-clés uniques, triés par fréquence

    Examples:
        >>> extract_keywords("Python est un langage Python populaire")
        ["python", "langage", "populaire"]
    """
    from collections import Counter

    if stopwords is None:
        stopwords = set()

    # Nettoyer et tokeniser
    words = re.findall(r"\b\w+\b", text.lower())

    # Filtrer
    filtered = [
        w for w in words
        if len(w) >= min_length and w not in stopwords
    ]

    # Compter et trier
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(max_keywords)]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcule la distance de Levenshtein entre deux chaînes.

    La distance de Levenshtein est le nombre minimum d'opérations
    (insertion, suppression, substitution) pour transformer s1 en s2.

    Args:
        s1: Première chaîne
        s2: Deuxième chaîne

    Returns:
        Distance de Levenshtein (entier >= 0)

    Examples:
        >>> levenshtein_distance("chat", "chats")
        1

        >>> levenshtein_distance("abc", "abc")
        0
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]
