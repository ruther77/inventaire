"""Parsers pour les formats français (nombres, dates).

Ce module fournit des fonctions pures pour parser les formats français
couramment utilisés dans les applications comptables et commerciales.

Fonctions principales:
- parse_french_decimal: Parse un nombre au format français (virgule décimale)
- parse_french_datetime: Parse une date au format français/ISO

Exemples:
    >>> parse_french_decimal("1 234,56")
    Decimal('1234.56')

    >>> parse_french_datetime("2025-01-15 14:30:00")
    datetime(2025, 1, 15, 14, 30, 0)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Union


def parse_french_decimal(
    value: Union[str, int, float, Decimal, None],
    default: Decimal = Decimal("0"),
) -> Decimal:
    """Parse un nombre au format français (virgule comme séparateur décimal).

    Cette fonction gère les formats courants:
    - Virgule comme séparateur décimal: "1,50"
    - Espaces comme séparateur de milliers: "1 234,56"
    - Espaces insécables: "1\xa0234,56"
    - Suffixes monétaires: "5,00 EUR", "5,00€"
    - Suffixes pourcentage: "20,00%", "20 %"

    Args:
        value: Valeur à parser (str, int, float, Decimal ou None)
        default: Valeur par défaut si le parsing échoue (défaut: Decimal("0"))

    Returns:
        Decimal représentant la valeur numérique

    Examples:
        >>> parse_french_decimal("1,50")
        Decimal('1.50')

        >>> parse_french_decimal("1 234,56")
        Decimal('1234.56')

        >>> parse_french_decimal("5,00 EUR")
        Decimal('5.00')

        >>> parse_french_decimal("20%")
        Decimal('20')

        >>> parse_french_decimal(None)
        Decimal('0')

        >>> parse_french_decimal("invalid", default=Decimal("-1"))
        Decimal('-1')
    """
    # Gestion des types non-string
    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return default

    # Conversion en string
    if not isinstance(value, str):
        value = str(value)

    # Nettoyage
    value = value.strip()
    if not value:
        return default

    # Suppression des suffixes monétaires et pourcentages
    suffixes_to_remove = ["EUR", "€", "%", "EUROS", "EURO"]
    for suffix in suffixes_to_remove:
        if value.upper().endswith(suffix):
            value = value[:-len(suffix)]

    # Nettoyage des espaces (normaux et insécables)
    value = value.strip()
    value = value.replace(" ", "").replace("\xa0", "").replace("\u202f", "")

    # Remplacement virgule -> point
    value = value.replace(",", ".")

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return default


def parse_french_datetime(
    value: Union[str, datetime, None],
    default: Optional[datetime] = None,
) -> Optional[datetime]:
    """Parse une date au format français ou ISO.

    Cette fonction gère les formats courants:
    - ISO avec heure: "2025-01-15 14:30:00"
    - ISO date seule: "2025-01-15"
    - Français avec heure: "15/01/2025 14:30:00"
    - Français date seule: "15/01/2025"
    - Français court: "15/01/25"

    Args:
        value: Date à parser (str, datetime ou None)
        default: Valeur par défaut si le parsing échoue (défaut: None)

    Returns:
        datetime ou None si le parsing échoue

    Examples:
        >>> parse_french_datetime("2025-01-15 14:30:00")
        datetime(2025, 1, 15, 14, 30, 0)

        >>> parse_french_datetime("2025-01-15")
        datetime(2025, 1, 15, 0, 0, 0)

        >>> parse_french_datetime("15/01/2025")
        datetime(2025, 1, 15, 0, 0, 0)

        >>> parse_french_datetime(None)
        None
    """
    if value is None:
        return default

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()
    if not value:
        return default

    # Liste des formats à essayer (du plus spécifique au plus général)
    formats = [
        # ISO
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        # Français
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d/%m/%y",
        # Variantes avec tirets
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return default


def format_french_decimal(
    value: Union[Decimal, float, int, None],
    decimals: int = 2,
    use_thousand_separator: bool = True,
) -> str:
    """Formate un nombre au format français.

    Args:
        value: Nombre à formater (Decimal, float, int ou None)
        decimals: Nombre de décimales (défaut: 2)
        use_thousand_separator: Utiliser un espace comme séparateur de milliers

    Returns:
        Chaîne formatée au format français

    Examples:
        >>> format_french_decimal(1234.56)
        "1 234,56"

        >>> format_french_decimal(1234.56, use_thousand_separator=False)
        "1234,56"

        >>> format_french_decimal(Decimal("1234.567"), decimals=3)
        "1 234,567"

        >>> format_french_decimal(None)
        "0,00"

        >>> format_french_decimal(-1234.56)
        "-1 234,56"
    """
    # Gestion de None
    if value is None:
        value = Decimal("0")

    # Conversion en Decimal pour une précision maximale
    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    # Arrondir
    rounded = round(value, decimals)

    # Formater avec le bon nombre de décimales
    format_str = f"{{:.{decimals}f}}"
    formatted = format_str.format(float(rounded))
    parts = formatted.split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "0" * decimals

    # Ajouter séparateur de milliers
    if use_thousand_separator:
        # Gérer le signe
        sign = ""
        if integer_part.startswith("-"):
            sign = "-"
            integer_part = integer_part[1:]

        # Grouper par 3 chiffres
        groups = []
        while integer_part:
            groups.append(integer_part[-3:])
            integer_part = integer_part[:-3]
        integer_part = sign + " ".join(reversed(groups))

    return f"{integer_part},{decimal_part}"
