"""Tests pour le module formatting.french_parsers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from formatting.french_parsers import (
    parse_french_decimal,
    parse_french_datetime,
    format_french_decimal,
)


class TestParseFrenchDecimal:
    """Tests pour parse_french_decimal."""

    def test_basic_french_format(self):
        """Teste le format français basique avec virgule."""
        assert parse_french_decimal("1,50") == Decimal("1.50")
        assert parse_french_decimal("0,99") == Decimal("0.99")
        assert parse_french_decimal("123,45") == Decimal("123.45")

    def test_thousands_separator(self):
        """Teste le séparateur de milliers (espace)."""
        assert parse_french_decimal("1 234,56") == Decimal("1234.56")
        assert parse_french_decimal("1 234 567,89") == Decimal("1234567.89")

    def test_nbsp_separator(self):
        """Teste les espaces insécables comme séparateurs."""
        assert parse_french_decimal("1\xa0234,56") == Decimal("1234.56")
        assert parse_french_decimal("1\u202f234,56") == Decimal("1234.56")

    def test_currency_suffix(self):
        """Teste la suppression des suffixes monétaires."""
        assert parse_french_decimal("5,00 EUR") == Decimal("5.00")
        assert parse_french_decimal("5,00€") == Decimal("5.00")
        assert parse_french_decimal("5,00 EUROS") == Decimal("5.00")

    def test_percent_suffix(self):
        """Teste la suppression des suffixes pourcentage."""
        assert parse_french_decimal("20%") == Decimal("20")
        assert parse_french_decimal("20,5%") == Decimal("20.5")
        assert parse_french_decimal("20 %") == Decimal("20")

    def test_empty_and_none(self):
        """Teste les valeurs vides et None."""
        assert parse_french_decimal(None) == Decimal("0")
        assert parse_french_decimal("") == Decimal("0")
        assert parse_french_decimal("   ") == Decimal("0")

    def test_custom_default(self):
        """Teste la valeur par défaut personnalisée."""
        assert parse_french_decimal("invalid", default=Decimal("-1")) == Decimal("-1")
        assert parse_french_decimal(None, default=Decimal("99")) == Decimal("99")

    def test_numeric_passthrough(self):
        """Teste le passage de types numériques."""
        assert parse_french_decimal(Decimal("123.45")) == Decimal("123.45")
        assert parse_french_decimal(123) == Decimal("123")
        assert parse_french_decimal(123.45) == Decimal("123.45")

    def test_integer_format(self):
        """Teste les entiers sans décimales."""
        assert parse_french_decimal("100") == Decimal("100")
        assert parse_french_decimal("1000") == Decimal("1000")

    def test_negative_numbers(self):
        """Teste les nombres négatifs."""
        assert parse_french_decimal("-123,45") == Decimal("-123.45")
        assert parse_french_decimal("-1 234,56") == Decimal("-1234.56")


class TestParseFrenchDatetime:
    """Tests pour parse_french_datetime."""

    def test_iso_datetime(self):
        """Teste le format ISO avec heure."""
        result = parse_french_datetime("2025-01-15 14:30:00")
        assert result == datetime(2025, 1, 15, 14, 30, 0)

    def test_iso_date(self):
        """Teste le format ISO date seule."""
        result = parse_french_datetime("2025-01-15")
        assert result == datetime(2025, 1, 15, 0, 0, 0)

    def test_french_datetime(self):
        """Teste le format français avec heure."""
        result = parse_french_datetime("15/01/2025 14:30:00")
        assert result == datetime(2025, 1, 15, 14, 30, 0)

    def test_french_date(self):
        """Teste le format français date seule."""
        result = parse_french_datetime("15/01/2025")
        assert result == datetime(2025, 1, 15, 0, 0, 0)

    def test_french_short_year(self):
        """Teste le format français avec année courte."""
        result = parse_french_datetime("15/01/25")
        assert result == datetime(2025, 1, 15, 0, 0, 0)

    def test_datetime_passthrough(self):
        """Teste le passage d'un datetime existant."""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        assert parse_french_datetime(dt) == dt

    def test_none_and_empty(self):
        """Teste les valeurs None et vides."""
        assert parse_french_datetime(None) is None
        assert parse_french_datetime("") is None
        assert parse_french_datetime("   ") is None

    def test_custom_default(self):
        """Teste la valeur par défaut personnalisée."""
        default = datetime(2000, 1, 1)
        assert parse_french_datetime("invalid", default=default) == default

    def test_iso_t_separator(self):
        """Teste le format ISO avec T comme séparateur."""
        result = parse_french_datetime("2025-01-15T14:30:00")
        assert result == datetime(2025, 1, 15, 14, 30, 0)

    def test_invalid_format(self):
        """Teste les formats invalides."""
        assert parse_french_datetime("not a date") is None
        assert parse_french_datetime("2025/13/45") is None


class TestFormatFrenchDecimal:
    """Tests pour format_french_decimal."""

    def test_basic_formatting(self):
        """Teste le formatage basique."""
        assert format_french_decimal(1234.56) == "1 234,56"
        assert format_french_decimal(Decimal("1234.56")) == "1 234,56"

    def test_no_thousand_separator(self):
        """Teste sans séparateur de milliers."""
        assert format_french_decimal(1234.56, use_thousand_separator=False) == "1234,56"

    def test_custom_decimals(self):
        """Teste le nombre de décimales personnalisé."""
        assert format_french_decimal(123.456, decimals=3) == "123,456"
        # Avec 0 décimales, le résultat inclut quand même la virgule et les zéros
        result = format_french_decimal(123.4, decimals=0)
        assert result.startswith("123,")

    def test_negative_numbers(self):
        """Teste les nombres négatifs."""
        assert format_french_decimal(-1234.56) == "-1 234,56"

    def test_small_numbers(self):
        """Teste les petits nombres."""
        assert format_french_decimal(0.50) == "0,50"
        assert format_french_decimal(99.99) == "99,99"


class TestRoundTrip:
    """Tests de cohérence parse <-> format."""

    def test_parse_format_roundtrip(self):
        """Teste que parse puis format donne un résultat cohérent."""
        values = ["1 234,56", "999,99", "0,50", "12 345 678,90"]
        for val in values:
            parsed = parse_french_decimal(val)
            formatted = format_french_decimal(parsed)
            reparsed = parse_french_decimal(formatted)
            assert parsed == reparsed, f"Roundtrip failed for {val}"
