"""Configuration pytest pour les tests de la bibliothèque maison."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ajouter le répertoire parent au path pour les imports
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_transactions():
    """Transactions d'exemple pour les tests de doublons."""
    from datetime import date
    from decimal import Decimal

    return [
        {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR MARKET",
            "montant": Decimal("50.00"),
            "direction": "OUT",
        },
        {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
            "direction": "OUT",
        },
        {
            "date": date(2025, 1, 20),
            "libelle": "LIDL",
            "montant": Decimal("35.50"),
            "direction": "OUT",
        },
        {
            "date": date(2025, 1, 25),
            "libelle": "VIREMENT SALAIRE",
            "montant": Decimal("2500.00"),
            "direction": "IN",
        },
    ]


@pytest.fixture
def sample_periods():
    """Périodes d'exemple pour les tests de couverture."""
    from datetime import date

    return {
        "compte_A": [
            (date(2025, 1, 1), date(2025, 1, 15)),
            (date(2025, 1, 20), date(2025, 1, 31)),
        ],
        "compte_B": [
            (date(2025, 1, 1), date(2025, 1, 31)),
        ],
    }


@pytest.fixture
def sample_products():
    """Produits d'exemple pour les tests de catégorisation."""
    return [
        "WHISKY JACK DANIELS 70CL",
        "COCA COLA 33CL",
        "RIZ BASMATI 1KG",
        "CHAMPAGNE MOËT",
        "BIÈRE HEINEKEN 25CL",
    ]
