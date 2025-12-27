"""Tests pour le module utils.text_utils."""

from __future__ import annotations

import pytest

from utils.text_utils import (
    fuzzy_match,
    normalize_text,
    normalize_product_name,
    split_paragraphs,
    chunk_with_overlap,
    extract_keywords,
    levenshtein_distance,
)


class TestFuzzyMatch:
    """Tests pour fuzzy_match."""

    def test_identical_strings(self):
        """Teste les chaînes identiques."""
        assert fuzzy_match("hello", "hello") == 1.0
        assert fuzzy_match("HELLO", "HELLO") == 1.0

    def test_case_insensitive(self):
        """Teste l'insensibilité à la casse par défaut."""
        assert fuzzy_match("Hello", "hello") == 1.0
        assert fuzzy_match("HELLO", "hello") == 1.0

    def test_case_sensitive(self):
        """Teste la sensibilité à la casse."""
        assert fuzzy_match("Hello", "hello", case_sensitive=True) < 1.0
        assert fuzzy_match("Hello", "Hello", case_sensitive=True) == 1.0

    def test_completely_different(self):
        """Teste les chaînes complètement différentes."""
        assert fuzzy_match("abc", "xyz") == 0.0

    def test_similar_strings(self):
        """Teste les chaînes similaires."""
        similarity = fuzzy_match("CARREFOUR MARKET", "CARREFOUR")
        assert 0.7 < similarity < 1.0

    def test_with_accents(self):
        """Teste avec des accents."""
        similarity = fuzzy_match("BIERE BLONDE", "BIÈRE BLONDE")
        assert similarity > 0.9

    def test_whitespace_handling(self):
        """Teste la gestion des espaces."""
        assert fuzzy_match("  hello  ", "hello") == 1.0


class TestNormalizeText:
    """Tests pour normalize_text."""

    def test_multiple_spaces(self):
        """Teste la réduction des espaces multiples."""
        assert normalize_text("Hello   World") == "Hello World"
        assert normalize_text("A  B  C") == "A B C"

    def test_leading_trailing(self):
        """Teste la suppression des espaces en début/fin."""
        assert normalize_text("  Hello  ") == "Hello"

    def test_newlines_and_tabs(self):
        """Teste la conversion des retours à la ligne et tabulations."""
        assert normalize_text("Hello\n\nWorld") == "Hello World"
        assert normalize_text("Hello\t\tWorld") == "Hello World"

    def test_empty_string(self):
        """Teste les chaînes vides."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""


class TestNormalizeProductName:
    """Tests pour normalize_product_name."""

    def test_basic_normalization(self):
        """Teste la normalisation basique."""
        assert normalize_product_name("  bière blonde  ") == "BIÈRE BLONDE"

    def test_with_synonyms(self):
        """Teste avec des synonymes."""
        synonyms = {"HEINEKEIN": "HEINEKEN"}
        assert normalize_product_name("HEINEKEIN", synonyms=synonyms) == "HEINEKEN"

    def test_without_uppercase(self):
        """Teste sans conversion en majuscules."""
        assert normalize_product_name("Hello World", uppercase=False) == "Hello World"

    def test_empty_string(self):
        """Teste les chaînes vides."""
        assert normalize_product_name("") == ""


class TestSplitParagraphs:
    """Tests pour split_paragraphs."""

    def test_basic_split(self):
        """Teste le découpage basique."""
        text = "Para1\n\nPara2\n\nPara3"
        result = split_paragraphs(text)
        assert result == ["Para1", "Para2", "Para3"]

    def test_empty_paragraphs(self):
        """Teste l'exclusion des paragraphes vides."""
        text = "Para1\n\n\n\n\nPara2"
        result = split_paragraphs(text)
        assert result == ["Para1", "Para2"]

    def test_with_normalization(self):
        """Teste avec normalisation."""
        text = "  Hello   World  \n\n  Test  "
        result = split_paragraphs(text, normalize=True)
        assert result == ["Hello World", "Test"]

    def test_without_normalization(self):
        """Teste sans normalisation."""
        text = "  Para1  \n\n  Para2  "
        result = split_paragraphs(text, normalize=False)
        assert result == ["Para1", "Para2"]


class TestChunkWithOverlap:
    """Tests pour chunk_with_overlap."""

    def test_basic_chunking(self):
        """Teste le découpage basique."""
        paragraphs = ["Word " * 50, "More " * 50]
        chunks = chunk_with_overlap(paragraphs, target_tokens=30, overlap=5)
        assert len(chunks) > 0
        assert all(isinstance(c, tuple) and len(c) == 2 for c in chunks)

    def test_chunk_ids(self):
        """Teste les identifiants de chunk."""
        paragraphs = ["Word " * 100]
        chunks = chunk_with_overlap(paragraphs, target_tokens=30)
        assert chunks[0][0] == "chunk_0000"
        if len(chunks) > 1:
            assert chunks[1][0] == "chunk_0001"

    def test_custom_prefix(self):
        """Teste le préfixe personnalisé."""
        paragraphs = ["Word " * 50]
        chunks = chunk_with_overlap(paragraphs, target_tokens=30, chunk_id_prefix="doc")
        assert chunks[0][0].startswith("doc_")

    def test_title_handling(self):
        """Teste le traitement des titres (lignes commençant par #)."""
        paragraphs = ["# Title", "Content " * 20, "# Another Title", "More " * 20]
        chunks = chunk_with_overlap(paragraphs, target_tokens=30)
        # Les titres devraient forcer un flush
        assert len(chunks) >= 2


class TestExtractKeywords:
    """Tests pour extract_keywords."""

    def test_basic_extraction(self):
        """Teste l'extraction basique."""
        text = "Python est un langage Python populaire"
        keywords = extract_keywords(text)
        assert "python" in keywords
        assert "langage" in keywords

    def test_min_length(self):
        """Teste la longueur minimale."""
        text = "A B C de longue phrase"
        keywords = extract_keywords(text, min_length=4)
        assert "longue" in keywords
        assert "a" not in keywords

    def test_max_keywords(self):
        """Teste le nombre maximum de mots-clés."""
        text = " ".join(["word" + str(i) for i in range(100)])
        keywords = extract_keywords(text, max_keywords=5)
        assert len(keywords) <= 5

    def test_stopwords(self):
        """Teste l'exclusion des stopwords."""
        text = "Python est un langage"
        keywords = extract_keywords(text, stopwords={"est", "un"})
        assert "est" not in keywords


class TestLevenshteinDistance:
    """Tests pour levenshtein_distance."""

    def test_identical_strings(self):
        """Teste les chaînes identiques."""
        assert levenshtein_distance("hello", "hello") == 0
        assert levenshtein_distance("", "") == 0

    def test_insertions(self):
        """Teste les insertions."""
        assert levenshtein_distance("chat", "chats") == 1
        assert levenshtein_distance("ab", "abc") == 1

    def test_deletions(self):
        """Teste les suppressions."""
        assert levenshtein_distance("chats", "chat") == 1
        assert levenshtein_distance("abc", "ab") == 1

    def test_substitutions(self):
        """Teste les substitutions."""
        assert levenshtein_distance("chat", "chit") == 1
        assert levenshtein_distance("abc", "adc") == 1

    def test_empty_strings(self):
        """Teste les chaînes vides."""
        assert levenshtein_distance("", "hello") == 5
        assert levenshtein_distance("hello", "") == 5

    def test_symmetric(self):
        """Teste la symétrie."""
        assert levenshtein_distance("abc", "xyz") == levenshtein_distance("xyz", "abc")
