"""Utilitaires de calcul de taxes (TVA).

Ce module fournit des fonctions pour le calcul et l'inférence
des taux de TVA français.

Fonctions principales:
- infer_tva: Déduit le taux de TVA à partir de montants TTC et HT
- infer_tva_from_category: Infère le taux de TVA à partir d'une catégorie
- calculate_ht_from_ttc: Calcule le prix HT à partir du TTC
- calculate_ttc_from_ht: Calcule le prix TTC à partir du HT
- calculate_tva_amount: Calcule le montant de TVA
- infer_category: Infère la catégorie d'un produit à partir de son nom
- categorize_product: Catégorise un produit et infère sa TVA

Taux de TVA français:
- 20% : Taux normal (boissons alcoolisées, la plupart des produits)
- 10% : Taux intermédiaire (restauration, transports)
- 5.5% : Taux réduit (alimentation, livres)
- 2.1% : Taux super-réduit (médicaments remboursables)
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Set, Tuple, Union


# Catégories par défaut avec TVA 20%
TVA_20_CATEGORIES: Set[str] = {
    "Spiritueux",
    "Effervescents / Champagne",
    "Vins rouges",
    "Vins blancs",
    "Vins rosés",
    "Bières",
    "Apéritifs / Fortifiés",
    "Softs / Énergisants",
    "Alcool",
    "Boissons alcoolisées",
}

# Catégories avec TVA 10%
TVA_10_CATEGORIES: Set[str] = {
    "Restauration",
    "Transport",
    "Hébergement",
}

# Catégories avec TVA 5.5%
TVA_5_5_CATEGORIES: Set[str] = {
    "Alimentation",
    "Épicerie",
    "Produits frais",
    "Livres",
}


def infer_tva(
    montant_ttc: Union[Decimal, float, str],
    montant_ht: Union[Decimal, float, None] = None,
    precision: int = 2,
    default_tva: float = 5.5,
    custom_mapping: Optional[Dict[str, float]] = None,
) -> Union[Decimal, float]:
    """Déduit le taux de TVA à partir des montants TTC et HT ou d'une catégorie.

    Formule: Taux TVA = ((TTC - HT) / HT) * 100

    Cette fonction inclut une protection contre la division par zéro.
    Si montant_ht est zéro ou très proche de zéro, retourne Decimal("0.00").

    Args:
        montant_ttc: Montant TTC ou nom de catégorie.
        montant_ht: Montant HT (obligatoire si montant_ttc est un montant).
        precision: Nombre de décimales pour l'arrondi (défaut: 2).
        default_tva: Taux par défaut si catégorie inconnue.
        custom_mapping: Mapping personnalisé catégorie -> taux.

    Returns:
        Taux de TVA (Decimal si calcul sur montants, float si inférence par catégorie).

    Examples:
        >>> infer_tva(Decimal("120.00"), Decimal("100.00"))
        Decimal('20.00')

        >>> infer_tva(Decimal("110.00"), Decimal("100.00"))
        Decimal('10.00')

        >>> infer_tva(Decimal("105.50"), Decimal("100.00"))
        Decimal('5.50')

        >>> infer_tva(Decimal("100.00"), Decimal("0.00"))
        Decimal('0.00')
    """
    if montant_ht is None and isinstance(montant_ttc, str):
        return infer_tva_from_category(
            montant_ttc,
            default_tva=default_tva,
            custom_mapping=custom_mapping,
        )

    if montant_ht is None:
        raise TypeError("montant_ht is required when inferring TVA from amounts")

    ttc = Decimal(str(montant_ttc))
    ht = Decimal(str(montant_ht))

    # Protection contre la division par zéro
    if ht == Decimal("0") or abs(ht) < Decimal("0.01"):
        return Decimal("0").quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)

    taux = ((ttc - ht) / ht) * Decimal("100")
    return taux.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)


def infer_tva_from_category(
    category: str,
    default_tva: float = 5.5,
    custom_mapping: Optional[Dict[str, float]] = None,
) -> float:
    """Infère le taux de TVA à partir d'une catégorie de produit.

    Cette fonction applique les règles de TVA françaises standard:
    - Boissons alcoolisées: 20%
    - Alimentation générale: 5.5%
    - Restauration: 10%

    Args:
        category: Nom de la catégorie
        default_tva: Taux par défaut si la catégorie est inconnue (défaut: 5.5)
        custom_mapping: Mapping personnalisé catégorie -> taux (optionnel)

    Returns:
        Taux de TVA en pourcentage (20.0, 10.0, 5.5, etc.)

    Examples:
        >>> infer_tva_from_category("Spiritueux")
        20.0

        >>> infer_tva_from_category("Épicerie")
        5.5

        >>> infer_tva_from_category("Restauration")
        10.0

        >>> infer_tva_from_category("Inconnu")
        5.5
    """
    # Appliquer le mapping personnalisé en priorité
    if custom_mapping and category in custom_mapping:
        return custom_mapping[category]

    # Vérifier les catégories à 20%
    if category in TVA_20_CATEGORIES:
        return 20.0

    # Vérifier les catégories à 10%
    if category in TVA_10_CATEGORIES:
        return 10.0

    # Vérifier les catégories à 5.5%
    if category in TVA_5_5_CATEGORIES:
        return 5.5

    return default_tva


def calculate_ht_from_ttc(
    ttc: Union[Decimal, float],
    tva_rate: float,
    precision: int = 2,
) -> Decimal:
    """Calcule le prix HT à partir du prix TTC.

    Formule: HT = TTC / (1 + TVA/100)

    Args:
        ttc: Prix TTC
        tva_rate: Taux de TVA en pourcentage (ex: 20.0 pour 20%)
        precision: Nombre de décimales (défaut: 2)

    Returns:
        Prix HT en Decimal

    Examples:
        >>> calculate_ht_from_ttc(Decimal("120.00"), 20.0)
        Decimal('100.00')

        >>> calculate_ht_from_ttc(Decimal("10.55"), 5.5)
        Decimal('10.00')
    """
    ttc = Decimal(str(ttc))
    tva_multiplier = Decimal("1") + Decimal(str(tva_rate)) / Decimal("100")
    ht = ttc / tva_multiplier
    return ht.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)


def calculate_ttc_from_ht(
    ht: Union[Decimal, float],
    tva_rate: float,
    precision: int = 2,
) -> Decimal:
    """Calcule le prix TTC à partir du prix HT.

    Formule: TTC = HT * (1 + TVA/100)

    Args:
        ht: Prix HT
        tva_rate: Taux de TVA en pourcentage (ex: 20.0 pour 20%)
        precision: Nombre de décimales (défaut: 2)

    Returns:
        Prix TTC en Decimal

    Examples:
        >>> calculate_ttc_from_ht(Decimal("100.00"), 20.0)
        Decimal('120.00')

        >>> calculate_ttc_from_ht(Decimal("10.00"), 5.5)
        Decimal('10.55')
    """
    ht = Decimal(str(ht))
    tva_multiplier = Decimal("1") + Decimal(str(tva_rate)) / Decimal("100")
    ttc = ht * tva_multiplier
    return ttc.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)


def calculate_tva_amount(
    montant: Union[Decimal, float],
    taux_tva: float,
    is_ttc: bool = True,
    precision: int = 2,
) -> Decimal:
    """Calcule le montant de TVA à partir d'un montant TTC ou HT.

    Si is_ttc=True (par défaut):
        Formule: TVA = TTC - HT = TTC - (TTC / (1 + taux/100))

    Si is_ttc=False:
        Formule: TVA = TTC - HT = (HT * (1 + taux/100)) - HT

    Args:
        montant: Prix TTC ou HT selon is_ttc
        taux_tva: Taux de TVA en pourcentage (ex: 20.0 pour 20%)
        is_ttc: True si montant est TTC, False si HT (défaut: True)
        precision: Nombre de décimales (défaut: 2)

    Returns:
        Montant de TVA en Decimal

    Examples:
        >>> calculate_tva_amount(Decimal("120.00"), 20.0, is_ttc=True)
        Decimal('20.00')

        >>> calculate_tva_amount(Decimal("100.00"), 20.0, is_ttc=False)
        Decimal('20.00')

        >>> calculate_tva_amount(Decimal("110.00"), 10.0, is_ttc=True)
        Decimal('10.00')
    """
    montant = Decimal(str(montant))

    if is_ttc:
        # Calculer depuis TTC
        ht = calculate_ht_from_ttc(montant, taux_tva, precision + 2)
        tva = montant - ht
    else:
        # Calculer depuis HT
        ttc = calculate_ttc_from_ht(montant, taux_tva, precision + 2)
        tva = ttc - montant

    return tva.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)


# Règles de catégorisation par mots-clés (ordre de priorité)
DEFAULT_CATEGORY_RULES: List[Tuple[str, List[str]]] = [
    ("Spiritueux", ["WHISKY", "VODKA", "RHUM", "RUM", "GIN", "TEQUILA", "COGNAC", "PASTIS"]),
    ("Effervescents / Champagne", ["CHAMPAGNE", "CREMANT", "PROSECCO", "BRUT", "MOËT", "VEUVE"]),
    ("Vins rouges", ["VIN ROUGE", "BORDEAUX", "MERLOT", "CABERNET", "MALBEC", "SYRAH"]),
    ("Vins blancs", ["VIN BLANC", "CHARDONNAY", "SAUVIGNON", "RIESLING"]),
    ("Vins rosés", ["ROSE", "ROSÉ"]),
    ("Bières", ["BIERE", "BIÈRE", "BEER", "LAGER", "IPA", "STOUT", "DESPERADOS", "HEINEKEN"]),
    ("Softs / Énergisants", ["COCA", "FANTA", "SPRITE", "PEPSI", "RED BULL", "MONSTER", "JUS", "SIROP"]),
    ("Eaux", ["EAU", "WATER", "PERRIER", "EVIAN", "VOLVIC", "CRISTALINE"]),
    ("Café / Thé", ["CAFE", "CAFÉ", "NESCAFE", "THE", "THÉ", "INFUSION"]),
    ("Boulangerie", ["PAIN", "BAGUETTE", "BRIOCHE", "CROISSANT"]),
    ("Confiserie", ["BONBON", "BISCUIT", "CHOCOLAT", "GATEAU", "GÂTEAU"]),
    ("Épicerie", ["PATES", "PÂTES", "RIZ", "FARINE", "SEMOULE"]),
    ("Conserves", ["CONSERVE", "TOMATE", "SARDINE", "THON"]),
    ("Hygiène", ["SAVON", "SHAMPOO", "DENTIFRICE", "LESSIVE"]),
    ("Frais", ["LEGUME", "LÉGUME", "FRUIT", "VIANDE", "POISSON"]),
]


def infer_category(
    product_name: str,
    rules: Optional[List[Tuple[str, List[str]]]] = None,
    default_category: str = "Épicerie",
) -> str:
    """Infère la catégorie d'un produit à partir de son nom.

    Parcourt les règles de catégorisation et retourne la première
    catégorie dont un mot-clé correspond au nom du produit.

    Args:
        product_name: Nom du produit
        rules: Liste de règles [(catégorie, [mots-clés])] (optionnel)
        default_category: Catégorie par défaut (défaut: "Épicerie")

    Returns:
        Nom de la catégorie

    Examples:
        >>> infer_category("WHISKY JACK DANIELS")
        "Spiritueux"

        >>> infer_category("COCA COLA 33CL")
        "Softs / Énergisants"

        >>> infer_category("ARTICLE INCONNU")
        "Épicerie"
    """
    if rules is None:
        rules = DEFAULT_CATEGORY_RULES

    upper_name = product_name.upper()

    for category, keywords in rules:
        if any(keyword in upper_name for keyword in keywords):
            return category

    return default_category


def categorize_product(
    product_name: str,
    rules: Optional[List[Tuple[str, List[str]]]] = None,
    default_category: str = "Épicerie",
) -> Tuple[str, float]:
    """Catégorise un produit et infère sa TVA.

    Combine infer_category et infer_tva_from_category pour retourner
    à la fois la catégorie et le taux de TVA.

    Args:
        product_name: Nom du produit
        rules: Règles de catégorisation (optionnel)
        default_category: Catégorie par défaut

    Returns:
        Tuple (catégorie, taux_tva)

    Examples:
        >>> categorize_product("WHISKY JACK DANIELS")
        ("Spiritueux", 20.0)

        >>> categorize_product("RIZ BASMATI")
        ("Épicerie", 5.5)
    """
    category = infer_category(product_name, rules, default_category)
    tva = infer_tva_from_category(category)
    return category, tva
