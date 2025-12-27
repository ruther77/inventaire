"""Utilitaires de calcul pour la gestion d'inventaire.

Ce module fournit des fonctions de calcul pour:
- PAMP (Prix d'Achat Moyen Pondéré)
- EOQ (Economic Order Quantity - Quantité Économique de Commande)
- Stock de sécurité
- Point de réapprovisionnement
- Calculs de marges

Basé sur les principes de gestion d'inventaire et de finance.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from math import sqrt
from statistics import NormalDist


def calculate_pamp(purchases: List[dict]) -> Decimal:
    """Calcule le Prix d'Achat Moyen Pondéré.

    Le PAMP est calculé en divisant la valeur totale des achats par la quantité totale.
    C'est une méthode de valorisation du stock qui prend en compte les différents
    prix d'achat pour calculer un coût moyen.

    Args:
        purchases: Liste de dictionnaires contenant 'quantity' et 'unit_price'
                  Exemple: [{'quantity': 10, 'unit_price': 5.50}, ...]

    Returns:
        Prix d'achat moyen pondéré (Decimal)

    Examples:
        >>> purchases = [
        ...     {'quantity': 10, 'unit_price': 5.00},
        ...     {'quantity': 20, 'unit_price': 6.00}
        ... ]
        >>> calculate_pamp(purchases)
        Decimal('5.67')

    Raises:
        ValueError: Si la liste est vide ou si la quantité totale est nulle
    """
    if not purchases:
        raise ValueError("La liste d'achats ne peut pas être vide")

    total_value = Decimal('0')
    total_quantity = Decimal('0')

    for purchase in purchases:
        quantity = Decimal(str(purchase.get('quantity', 0)))
        unit_price = Decimal(str(purchase.get('unit_price', 0)))

        total_value += quantity * unit_price
        total_quantity += quantity

    if total_quantity == 0:
        raise ValueError("La quantité totale ne peut pas être nulle")

    pamp = total_value / total_quantity
    return pamp.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_eoq(
    annual_demand: float,
    order_cost: float,
    holding_cost: float
) -> float:
    """Calcule la Quantité Économique de Commande (Economic Order Quantity).

    L'EOQ détermine la quantité optimale à commander pour minimiser les coûts
    totaux de gestion des stocks (coûts de commande + coûts de stockage).

    Formule de Wilson: EOQ = sqrt((2 * D * S) / H)
    où:
    - D = Demande annuelle
    - S = Coût par commande (order_cost)
    - H = Coût de possession unitaire annuel (holding_cost)

    Args:
        annual_demand: Demande annuelle en unités
        order_cost: Coût fixe par commande (frais administratifs, transport, etc.)
        holding_cost: Coût de possession par unité par an (stockage, assurance, etc.)

    Returns:
        Quantité économique de commande (arrondie à l'entier supérieur)

    Examples:
        >>> calculate_eoq(annual_demand=1200, order_cost=50, holding_cost=2)
        245.0

    Raises:
        ValueError: Si l'un des paramètres est négatif ou nul
    """
    if annual_demand <= 0:
        raise ValueError("La demande annuelle doit être positive")
    if order_cost <= 0:
        raise ValueError("Le coût de commande doit être positif")
    if holding_cost <= 0:
        raise ValueError("Le coût de possession doit être positif")

    eoq = sqrt((2 * annual_demand * order_cost) / holding_cost)
    return round(eoq, 2)


def calculate_safety_stock(
    avg_demand: float,
    demand_std: float,
    lead_time: float,
    service_level: float = 0.95
) -> float:
    """Calcule le stock de sécurité pour un niveau de service donné.

    Le stock de sécurité permet de se protéger contre les variations de la demande
    et les délais de livraison pour maintenir un niveau de service client souhaité.

    Formule simplifiée: SS = Z * σd * sqrt(LT)
    où:
    - Z = Z-score pour le niveau de service (loi normale)
    - σd = Écart-type de la demande quotidienne
    - LT = Lead time (délai de livraison en jours)

    Args:
        avg_demand: Demande moyenne quotidienne
        demand_std: Écart-type de la demande quotidienne
        lead_time: Délai de livraison moyen en jours
        service_level: Niveau de service souhaité (entre 0 et 1)
                      0.95 = 95% de satisfaction client

    Returns:
        Quantité de stock de sécurité (arrondie à l'entier supérieur)

    Examples:
        >>> calculate_safety_stock(avg_demand=50, demand_std=10, lead_time=5, service_level=0.95)
        37.0

    Notes:
        Niveaux de service courants:
        - 0.90 (90%) -> Z = 1.28
        - 0.95 (95%) -> Z = 1.65
        - 0.99 (99%) -> Z = 2.33

    Raises:
        ValueError: Si les paramètres sont invalides
    """
    if avg_demand < 0:
        raise ValueError("La demande moyenne ne peut pas être négative")
    if demand_std < 0:
        raise ValueError("L'écart-type ne peut pas être négatif")
    if lead_time <= 0:
        raise ValueError("Le lead time doit être positif")
    if not 0 < service_level < 1:
        raise ValueError("Le niveau de service doit être entre 0 et 1")

    # Calcul du Z-score à partir du niveau de service (loi normale)
    z_score = NormalDist().inv_cdf(service_level)

    # Stock de sécurité = Z * écart-type de la demande * racine(lead time)
    safety_stock = z_score * demand_std * sqrt(lead_time)

    return round(safety_stock, 2)


def calculate_reorder_point(
    avg_demand: float,
    lead_time: float,
    safety_stock: float
) -> float:
    """Calcule le point de réapprovisionnement.

    Le point de réapprovisionnement indique le niveau de stock auquel il faut
    passer une nouvelle commande pour éviter les ruptures.

    Formule: ROP = (Demande moyenne * Lead time) + Stock de sécurité

    Args:
        avg_demand: Demande moyenne quotidienne
        lead_time: Délai de livraison en jours
        safety_stock: Stock de sécurité calculé

    Returns:
        Point de réapprovisionnement (arrondi à l'entier supérieur)

    Examples:
        >>> calculate_reorder_point(avg_demand=50, lead_time=5, safety_stock=37)
        287.0

    Notes:
        Lorsque le stock atteint ce niveau, une commande doit être passée.
        La quantité à commander est généralement l'EOQ.

    Raises:
        ValueError: Si les paramètres sont invalides
    """
    if avg_demand < 0:
        raise ValueError("La demande moyenne ne peut pas être négative")
    if lead_time <= 0:
        raise ValueError("Le lead time doit être positif")
    if safety_stock < 0:
        raise ValueError("Le stock de sécurité ne peut pas être négatif")

    # Demande pendant le lead time + stock de sécurité
    reorder_point = (avg_demand * lead_time) + safety_stock

    return round(reorder_point, 2)


def calculate_margin(revenue: Decimal, cost: Decimal) -> dict:
    """Calcule la marge (montant et pourcentage).

    La marge représente la différence entre le prix de vente et le coût d'achat.
    Elle peut être exprimée en valeur absolue ou en pourcentage.

    Args:
        revenue: Prix de vente HT (chiffre d'affaires)
        cost: Coût d'achat HT

    Returns:
        Dictionnaire contenant:
        - margin_amount: Montant de la marge en valeur absolue
        - margin_percent: Pourcentage de marge par rapport au prix de vente

    Examples:
        >>> from decimal import Decimal
        >>> calculate_margin(Decimal('100'), Decimal('60'))
        {'margin_amount': Decimal('40.00'), 'margin_percent': Decimal('40.00')}

    Notes:
        - Marge brute (%) = ((Prix de vente - Coût) / Prix de vente) × 100
        - Ne pas confondre avec le taux de marque qui est basé sur le coût
        - Une marge de 40% signifie que 40% du prix de vente est du bénéfice

    Raises:
        ValueError: Si le chiffre d'affaires est négatif
    """
    if revenue < 0:
        raise ValueError("Le chiffre d'affaires ne peut pas être négatif")
    if cost < 0:
        raise ValueError("Le coût ne peut pas être négatif")

    # Calcul de la marge en valeur absolue
    margin_amount = revenue - cost

    # Calcul du pourcentage de marge
    if revenue > 0:
        margin_percent = (margin_amount / revenue * Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    else:
        margin_percent = Decimal('0.00')

    margin_amount = margin_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        'margin_amount': margin_amount,
        'margin_percent': margin_percent
    }
