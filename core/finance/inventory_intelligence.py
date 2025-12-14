"""
Inventaire Intelligent - Algorithmes EOQ, Safety Stock, Reorder Point
=====================================================================

Module d'optimisation des stocks avec:
- EOQ (Economic Order Quantity) - Formule de Wilson
- Safety Stock avec service level
- Reorder Point dynamique
- Detection dead stock (rotation < 0.3/mois)
- Prediction rupture de stock
- Suggestions de reapprovisionnement automatiques
- Classification ABC/XYZ
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import math
import statistics


class StockClassification(Enum):
    """Classification ABC pour valeur et XYZ pour variabilité"""
    A = "A"  # 80% valeur, top 20% produits
    B = "B"  # 15% valeur, next 30% produits
    C = "C"  # 5% valeur, remaining 50% produits

    X = "X"  # Demande stable (CV < 0.5)
    Y = "Y"  # Demande variable (0.5 <= CV < 1.0)
    Z = "Z"  # Demande erratique (CV >= 1.0)


class ServiceLevel(Enum):
    """Niveau de service pour calcul safety stock"""
    LOW = 0.90       # 90% - Z = 1.28
    STANDARD = 0.95  # 95% - Z = 1.65
    HIGH = 0.98      # 98% - Z = 2.05
    CRITICAL = 0.99  # 99% - Z = 2.33


# Z-scores pour les niveaux de service
SERVICE_LEVEL_Z = {
    ServiceLevel.LOW: 1.28,
    ServiceLevel.STANDARD: 1.65,
    ServiceLevel.HIGH: 2.05,
    ServiceLevel.CRITICAL: 2.33,
}


@dataclass
class DemandAnalysis:
    """Analyse de la demande d'un produit"""
    product_id: int
    period_days: int
    total_demand: Decimal
    average_daily_demand: Decimal
    demand_std_dev: Decimal
    coefficient_variation: float  # CV = std_dev / mean
    demand_pattern: StockClassification  # X, Y, or Z
    trend: str  # "increasing", "stable", "decreasing"
    seasonality_detected: bool
    peak_days: List[int]  # Jours de la semaine avec pic (0=lundi)


@dataclass
class EOQResult:
    """Résultat du calcul EOQ"""
    product_id: int
    annual_demand: Decimal
    ordering_cost: Decimal  # Coût par commande
    holding_cost_rate: float  # % du coût par an
    unit_cost: Decimal

    # Résultats
    eoq: int  # Quantité économique de commande
    orders_per_year: float
    total_ordering_cost: Decimal
    total_holding_cost: Decimal
    total_cost: Decimal

    # Avec contraintes
    adjusted_eoq: Optional[int] = None  # Si MOQ ou contraintes fournisseur
    adjustment_reason: Optional[str] = None


@dataclass
class SafetyStockResult:
    """Résultat du calcul du stock de sécurité"""
    product_id: int
    service_level: ServiceLevel
    z_score: float

    # Inputs
    average_lead_time_days: float
    lead_time_std_dev: float
    average_daily_demand: Decimal
    demand_std_dev: Decimal

    # Résultats
    safety_stock: int
    safety_stock_value: Decimal
    safety_stock_days: float  # En jours de stock


@dataclass
class ReorderPoint:
    """Point de réapprovisionnement"""
    product_id: int
    reorder_level: int  # Niveau déclencheur
    safety_stock: int
    lead_time_demand: int  # Demande pendant délai
    current_stock: int

    # Statut
    needs_reorder: bool
    days_until_stockout: Optional[float]
    urgency: str  # "critical", "urgent", "normal", "ok"
    suggested_order_qty: int


@dataclass
class DeadStockItem:
    """Produit identifié comme stock mort"""
    product_id: int
    product_name: str
    current_stock: int
    stock_value: Decimal
    last_movement_date: Optional[datetime]
    days_without_movement: int
    monthly_rotation: float  # < 0.3 = dead stock
    recommendation: str
    potential_loss: Decimal


@dataclass
class StockoutPrediction:
    """Prédiction de rupture de stock"""
    product_id: int
    product_name: str
    current_stock: int
    average_daily_consumption: Decimal
    predicted_stockout_date: datetime
    days_until_stockout: float
    confidence: float
    risk_level: str  # "critical", "high", "medium", "low"
    recommended_action: str


@dataclass
class ReorderSuggestion:
    """Suggestion de réapprovisionnement automatique"""
    product_id: int
    product_name: str
    supplier_id: Optional[int]
    supplier_name: Optional[str]

    suggested_quantity: int
    suggested_order_date: datetime
    expected_delivery_date: datetime

    reason: str
    priority: str  # "critical", "high", "normal", "low"
    estimated_cost: Decimal

    # Context
    current_stock: int
    reorder_point: int
    eoq: int
    safety_stock: int


@dataclass
class ABCXYZClassification:
    """Classification combinée ABC-XYZ"""
    product_id: int
    abc_class: StockClassification  # A, B, C
    xyz_class: StockClassification  # X, Y, Z
    combined_class: str  # ex: "AX", "BY", "CZ"

    annual_value: Decimal
    cumulative_value_pct: float
    coefficient_variation: float

    recommended_strategy: str
    review_frequency: str  # "daily", "weekly", "monthly"
    safety_stock_policy: str


class InventoryIntelligence:
    """
    Moteur d'intelligence d'inventaire avec algorithmes avancés
    """

    def __init__(self, db_pool=None):
        self.db_pool = db_pool

        # Paramètres par défaut
        self.default_ordering_cost = Decimal("25.00")  # Coût moyen par commande
        self.default_holding_cost_rate = 0.25  # 25% du coût par an
        self.default_service_level = ServiceLevel.STANDARD
        self.default_lead_time_days = 3
        self.dead_stock_threshold = 0.3  # Rotation < 0.3/mois

    # =========================================================================
    # ANALYSE DE LA DEMANDE
    # =========================================================================

    def analyze_demand(
        self,
        product_id: int,
        consumption_history: List[Dict[str, Any]],
        period_days: int = 90
    ) -> DemandAnalysis:
        """
        Analyse la demande d'un produit pour déterminer son pattern

        consumption_history: [{"date": datetime, "quantity": Decimal}, ...]
        """
        if not consumption_history:
            return DemandAnalysis(
                product_id=product_id,
                period_days=period_days,
                total_demand=Decimal("0"),
                average_daily_demand=Decimal("0"),
                demand_std_dev=Decimal("0"),
                coefficient_variation=0.0,
                demand_pattern=StockClassification.Z,
                trend="stable",
                seasonality_detected=False,
                peak_days=[]
            )

        # Agréger par jour
        daily_demand = {}
        for entry in consumption_history:
            date_key = entry["date"].date() if isinstance(entry["date"], datetime) else entry["date"]
            qty = Decimal(str(entry["quantity"]))
            daily_demand[date_key] = daily_demand.get(date_key, Decimal("0")) + qty

        # Remplir les jours sans demande avec 0
        if daily_demand:
            min_date = min(daily_demand.keys())
            max_date = max(daily_demand.keys())
            current = min_date
            while current <= max_date:
                if current not in daily_demand:
                    daily_demand[current] = Decimal("0")
                current += timedelta(days=1)

        demands = list(daily_demand.values())
        total = sum(demands)

        if len(demands) == 0:
            avg = Decimal("0")
            std_dev = Decimal("0")
            cv = 0.0
        else:
            avg = total / len(demands)

            if len(demands) > 1 and avg > 0:
                variance = sum((d - avg) ** 2 for d in demands) / len(demands)
                std_dev = Decimal(str(math.sqrt(float(variance))))
                cv = float(std_dev / avg)
            else:
                std_dev = Decimal("0")
                cv = 0.0

        # Classification XYZ basée sur CV
        if cv < 0.5:
            pattern = StockClassification.X
        elif cv < 1.0:
            pattern = StockClassification.Y
        else:
            pattern = StockClassification.Z

        # Détection tendance
        trend = self._detect_trend(demands)

        # Détection saisonnalité (pics par jour de semaine)
        peak_days = self._detect_weekly_peaks(daily_demand)
        seasonality = len(peak_days) > 0

        return DemandAnalysis(
            product_id=product_id,
            period_days=period_days,
            total_demand=total,
            average_daily_demand=avg,
            demand_std_dev=std_dev,
            coefficient_variation=cv,
            demand_pattern=pattern,
            trend=trend,
            seasonality_detected=seasonality,
            peak_days=peak_days
        )

    def _detect_trend(self, demands: List[Decimal]) -> str:
        """Détecte la tendance via régression linéaire simple"""
        if len(demands) < 7:
            return "stable"

        # Diviser en 3 périodes
        third = len(demands) // 3
        first_third = sum(demands[:third]) / third if third > 0 else Decimal("0")
        last_third = sum(demands[-third:]) / third if third > 0 else Decimal("0")

        if first_third == 0:
            return "stable" if last_third == 0 else "increasing"

        change_pct = float((last_third - first_third) / first_third)

        if change_pct > 0.15:
            return "increasing"
        elif change_pct < -0.15:
            return "decreasing"
        return "stable"

    def _detect_weekly_peaks(self, daily_demand: Dict[Any, Decimal]) -> List[int]:
        """Détecte les jours de la semaine avec demande significativement plus haute"""
        if not daily_demand:
            return []

        # Agréger par jour de semaine
        weekday_totals = {i: [] for i in range(7)}
        for date, qty in daily_demand.items():
            weekday = date.weekday()
            weekday_totals[weekday].append(float(qty))

        # Moyenne par jour
        weekday_avgs = {}
        for day, values in weekday_totals.items():
            if values:
                weekday_avgs[day] = statistics.mean(values)

        if not weekday_avgs:
            return []

        overall_avg = statistics.mean(weekday_avgs.values())
        if overall_avg == 0:
            return []

        # Jours avec demande > 1.5x la moyenne
        peak_days = [
            day for day, avg in weekday_avgs.items()
            if avg > overall_avg * 1.5
        ]

        return sorted(peak_days)

    # =========================================================================
    # EOQ - ECONOMIC ORDER QUANTITY (Formule de Wilson)
    # =========================================================================

    def calculate_eoq(
        self,
        product_id: int,
        annual_demand: Decimal,
        unit_cost: Decimal,
        ordering_cost: Optional[Decimal] = None,
        holding_cost_rate: Optional[float] = None,
        min_order_qty: Optional[int] = None,
        max_order_qty: Optional[int] = None,
        supplier_moq: Optional[int] = None
    ) -> EOQResult:
        """
        Calcule la quantité économique de commande (EOQ)

        Formule de Wilson: EOQ = sqrt((2 * D * S) / H)
        où:
          D = Demande annuelle
          S = Coût par commande
          H = Coût de stockage par unité par an = unit_cost * holding_rate
        """
        ordering_cost = ordering_cost or self.default_ordering_cost
        holding_cost_rate = holding_cost_rate or self.default_holding_cost_rate

        # Coût de stockage par unité
        holding_cost = unit_cost * Decimal(str(holding_cost_rate))

        if annual_demand <= 0 or holding_cost <= 0:
            eoq = 1
        else:
            # Formule EOQ
            eoq_float = math.sqrt(
                (2 * float(annual_demand) * float(ordering_cost)) / float(holding_cost)
            )
            eoq = max(1, round(eoq_float))

        # Calcul des coûts
        orders_per_year = float(annual_demand) / eoq if eoq > 0 else 0
        total_ordering = Decimal(str(orders_per_year)) * ordering_cost
        avg_inventory = Decimal(str(eoq)) / 2
        total_holding = avg_inventory * holding_cost
        total_cost = total_ordering + total_holding

        # Ajustements pour contraintes
        adjusted_eoq = None
        adjustment_reason = None

        final_eoq = eoq

        if supplier_moq and eoq < supplier_moq:
            final_eoq = supplier_moq
            adjusted_eoq = supplier_moq
            adjustment_reason = f"MOQ fournisseur: {supplier_moq}"

        if min_order_qty and final_eoq < min_order_qty:
            final_eoq = min_order_qty
            adjusted_eoq = min_order_qty
            adjustment_reason = f"Quantité minimum: {min_order_qty}"

        if max_order_qty and final_eoq > max_order_qty:
            final_eoq = max_order_qty
            adjusted_eoq = max_order_qty
            adjustment_reason = f"Quantité maximum: {max_order_qty}"

        return EOQResult(
            product_id=product_id,
            annual_demand=annual_demand,
            ordering_cost=ordering_cost,
            holding_cost_rate=holding_cost_rate,
            unit_cost=unit_cost,
            eoq=eoq,
            orders_per_year=orders_per_year,
            total_ordering_cost=total_ordering,
            total_holding_cost=total_holding,
            total_cost=total_cost,
            adjusted_eoq=adjusted_eoq,
            adjustment_reason=adjustment_reason
        )

    # =========================================================================
    # SAFETY STOCK
    # =========================================================================

    def calculate_safety_stock(
        self,
        product_id: int,
        average_daily_demand: Decimal,
        demand_std_dev: Decimal,
        average_lead_time_days: float,
        lead_time_std_dev: float = 0.0,
        service_level: ServiceLevel = None,
        unit_cost: Optional[Decimal] = None
    ) -> SafetyStockResult:
        """
        Calcule le stock de sécurité

        Formule avec variabilité demande ET délai:
        SS = Z * sqrt(LT * σd² + d² * σLT²)

        où:
          Z = Z-score pour le niveau de service
          LT = Lead time moyen
          σd = Écart-type demande
          d = Demande moyenne
          σLT = Écart-type lead time
        """
        service_level = service_level or self.default_service_level
        z_score = SERVICE_LEVEL_Z[service_level]

        # Calcul safety stock
        demand_variance = float(demand_std_dev) ** 2
        lt_variance = lead_time_std_dev ** 2
        avg_demand = float(average_daily_demand)

        # Formule combinée
        variance_combined = (
            average_lead_time_days * demand_variance +
            (avg_demand ** 2) * lt_variance
        )

        safety_stock = z_score * math.sqrt(variance_combined)
        safety_stock_int = max(0, math.ceil(safety_stock))

        # Valeur du safety stock
        ss_value = Decimal(str(safety_stock_int)) * (unit_cost or Decimal("0"))

        # En jours de stock
        ss_days = safety_stock_int / avg_demand if avg_demand > 0 else 0

        return SafetyStockResult(
            product_id=product_id,
            service_level=service_level,
            z_score=z_score,
            average_lead_time_days=average_lead_time_days,
            lead_time_std_dev=lead_time_std_dev,
            average_daily_demand=average_daily_demand,
            demand_std_dev=demand_std_dev,
            safety_stock=safety_stock_int,
            safety_stock_value=ss_value,
            safety_stock_days=ss_days
        )

    # =========================================================================
    # REORDER POINT
    # =========================================================================

    def calculate_reorder_point(
        self,
        product_id: int,
        current_stock: int,
        average_daily_demand: Decimal,
        lead_time_days: float,
        safety_stock: int,
        eoq: int,
        pending_orders_qty: int = 0
    ) -> ReorderPoint:
        """
        Calcule le point de réapprovisionnement et le statut actuel

        ROP = (Demande moyenne * Lead time) + Safety stock
        """
        lead_time_demand = math.ceil(float(average_daily_demand) * lead_time_days)
        reorder_level = lead_time_demand + safety_stock

        # Stock disponible (inclut commandes en cours)
        available_stock = current_stock + pending_orders_qty

        # Besoin de réapprovisionner?
        needs_reorder = available_stock <= reorder_level

        # Jours jusqu'à rupture
        avg_demand = float(average_daily_demand)
        if avg_demand > 0:
            days_until_stockout = current_stock / avg_demand
        else:
            days_until_stockout = None

        # Niveau d'urgence
        if days_until_stockout is not None:
            if days_until_stockout <= lead_time_days:
                urgency = "critical"
            elif days_until_stockout <= lead_time_days * 1.5:
                urgency = "urgent"
            elif needs_reorder:
                urgency = "normal"
            else:
                urgency = "ok"
        else:
            urgency = "ok" if not needs_reorder else "normal"

        # Quantité suggérée
        if needs_reorder:
            # Commander EOQ ou plus si stock très bas
            shortage = reorder_level - available_stock
            suggested_qty = max(eoq, shortage + safety_stock)
        else:
            suggested_qty = 0

        return ReorderPoint(
            product_id=product_id,
            reorder_level=reorder_level,
            safety_stock=safety_stock,
            lead_time_demand=lead_time_demand,
            current_stock=current_stock,
            needs_reorder=needs_reorder,
            days_until_stockout=days_until_stockout,
            urgency=urgency,
            suggested_order_qty=suggested_qty
        )

    # =========================================================================
    # DEAD STOCK DETECTION
    # =========================================================================

    def detect_dead_stock(
        self,
        products_with_stock: List[Dict[str, Any]],
        rotation_threshold: float = None
    ) -> List[DeadStockItem]:
        """
        Détecte les produits en stock mort (rotation < 0.3/mois)

        products_with_stock: [{
            "product_id": int,
            "product_name": str,
            "current_stock": int,
            "unit_cost": Decimal,
            "last_movement_date": datetime,
            "monthly_consumption": Decimal
        }, ...]
        """
        threshold = rotation_threshold or self.dead_stock_threshold
        dead_stock = []
        now = datetime.now()

        for product in products_with_stock:
            stock = product.get("current_stock", 0)
            if stock <= 0:
                continue

            monthly_consumption = Decimal(str(product.get("monthly_consumption", 0)))
            unit_cost = Decimal(str(product.get("unit_cost", 0)))
            stock_value = Decimal(str(stock)) * unit_cost

            # Calcul rotation mensuelle
            if stock > 0:
                rotation = float(monthly_consumption / Decimal(str(stock)))
            else:
                rotation = 0

            last_movement = product.get("last_movement_date")
            if last_movement:
                days_without = (now - last_movement).days
            else:
                days_without = 365  # Assume very old

            # Stock mort si rotation < seuil OU pas de mouvement > 90 jours
            is_dead = rotation < threshold or days_without > 90

            if is_dead:
                # Recommandation basée sur la situation
                if days_without > 180:
                    recommendation = "Liquider ou déprécier - aucun mouvement > 6 mois"
                    potential_loss = stock_value * Decimal("0.8")  # 80% de perte estimée
                elif days_without > 90:
                    recommendation = "Promotion agressive ou bundle"
                    potential_loss = stock_value * Decimal("0.5")
                elif rotation < 0.1:
                    recommendation = "Réduire prix ou offrir en lot"
                    potential_loss = stock_value * Decimal("0.3")
                else:
                    recommendation = "Surveiller - rotation faible"
                    potential_loss = stock_value * Decimal("0.1")

                dead_stock.append(DeadStockItem(
                    product_id=product["product_id"],
                    product_name=product.get("product_name", ""),
                    current_stock=stock,
                    stock_value=stock_value,
                    last_movement_date=last_movement,
                    days_without_movement=days_without,
                    monthly_rotation=rotation,
                    recommendation=recommendation,
                    potential_loss=potential_loss
                ))

        # Trier par perte potentielle décroissante
        dead_stock.sort(key=lambda x: x.potential_loss, reverse=True)

        return dead_stock

    # =========================================================================
    # STOCKOUT PREDICTION
    # =========================================================================

    def predict_stockouts(
        self,
        products: List[Dict[str, Any]],
        horizon_days: int = 30
    ) -> List[StockoutPrediction]:
        """
        Prédit les ruptures de stock dans les N prochains jours

        products: [{
            "product_id": int,
            "product_name": str,
            "current_stock": int,
            "average_daily_consumption": Decimal,
            "consumption_trend": str,  # "increasing", "stable", "decreasing"
            "lead_time_days": int
        }, ...]
        """
        predictions = []
        now = datetime.now()

        for product in products:
            stock = product.get("current_stock", 0)
            avg_consumption = Decimal(str(product.get("average_daily_consumption", 0)))
            trend = product.get("consumption_trend", "stable")
            lead_time = product.get("lead_time_days", self.default_lead_time_days)

            if avg_consumption <= 0:
                continue

            # Ajuster consommation selon tendance
            if trend == "increasing":
                adjusted_consumption = avg_consumption * Decimal("1.15")
                confidence = 0.75
            elif trend == "decreasing":
                adjusted_consumption = avg_consumption * Decimal("0.85")
                confidence = 0.80
            else:
                adjusted_consumption = avg_consumption
                confidence = 0.90

            # Jours jusqu'à rupture
            days_until = float(Decimal(str(stock)) / adjusted_consumption)

            # Ne garder que ceux dans l'horizon
            if days_until > horizon_days:
                continue

            stockout_date = now + timedelta(days=days_until)

            # Niveau de risque
            if days_until <= lead_time:
                risk_level = "critical"
                action = f"URGENT: Commander immédiatement - délai livraison {lead_time}j"
            elif days_until <= lead_time * 2:
                risk_level = "high"
                action = "Commander cette semaine"
            elif days_until <= 14:
                risk_level = "medium"
                action = "Planifier commande"
            else:
                risk_level = "low"
                action = "Surveiller"

            predictions.append(StockoutPrediction(
                product_id=product["product_id"],
                product_name=product.get("product_name", ""),
                current_stock=stock,
                average_daily_consumption=avg_consumption,
                predicted_stockout_date=stockout_date,
                days_until_stockout=days_until,
                confidence=confidence,
                risk_level=risk_level,
                recommended_action=action
            ))

        # Trier par urgence (jours jusqu'à rupture)
        predictions.sort(key=lambda x: x.days_until_stockout)

        return predictions

    # =========================================================================
    # AUTOMATIC REORDER SUGGESTIONS
    # =========================================================================

    def generate_reorder_suggestions(
        self,
        products: List[Dict[str, Any]],
        suppliers: Dict[int, Dict[str, Any]] = None
    ) -> List[ReorderSuggestion]:
        """
        Génère des suggestions de réapprovisionnement automatiques

        products: [{
            "product_id": int,
            "product_name": str,
            "supplier_id": int,
            "current_stock": int,
            "unit_cost": Decimal,
            "annual_demand": Decimal,
            "average_daily_demand": Decimal,
            "demand_std_dev": Decimal,
            "lead_time_days": int
        }, ...]

        suppliers: {supplier_id: {"name": str, "lead_time": int, "moq": int}}
        """
        suggestions = []
        suppliers = suppliers or {}
        now = datetime.now()

        for product in products:
            product_id = product["product_id"]

            # Paramètres produit
            current_stock = product.get("current_stock", 0)
            unit_cost = Decimal(str(product.get("unit_cost", 0)))
            annual_demand = Decimal(str(product.get("annual_demand", 0)))
            avg_daily = Decimal(str(product.get("average_daily_demand", 0)))
            demand_std = Decimal(str(product.get("demand_std_dev", 0)))

            # Info fournisseur
            supplier_id = product.get("supplier_id")
            supplier_info = suppliers.get(supplier_id, {})
            supplier_name = supplier_info.get("name")
            lead_time = product.get("lead_time_days") or supplier_info.get("lead_time", self.default_lead_time_days)
            moq = supplier_info.get("moq")

            # Calculs
            eoq_result = self.calculate_eoq(
                product_id=product_id,
                annual_demand=annual_demand,
                unit_cost=unit_cost,
                supplier_moq=moq
            )

            safety_result = self.calculate_safety_stock(
                product_id=product_id,
                average_daily_demand=avg_daily,
                demand_std_dev=demand_std,
                average_lead_time_days=lead_time,
                unit_cost=unit_cost
            )

            rop = self.calculate_reorder_point(
                product_id=product_id,
                current_stock=current_stock,
                average_daily_demand=avg_daily,
                lead_time_days=lead_time,
                safety_stock=safety_result.safety_stock,
                eoq=eoq_result.adjusted_eoq or eoq_result.eoq
            )

            if not rop.needs_reorder:
                continue

            # Quantité et dates
            qty = rop.suggested_order_qty
            if moq and qty < moq:
                qty = moq

            # Date de commande
            if rop.urgency == "critical":
                order_date = now
            elif rop.urgency == "urgent":
                order_date = now + timedelta(days=1)
            else:
                # Optimiser pour regrouper commandes
                order_date = now + timedelta(days=3)

            delivery_date = order_date + timedelta(days=lead_time)

            # Raison
            if rop.urgency == "critical":
                reason = f"Stock critique - {rop.days_until_stockout:.1f}j avant rupture"
                priority = "critical"
            elif rop.urgency == "urgent":
                reason = f"Stock bas - niveau de réapprovisionnement atteint"
                priority = "high"
            else:
                reason = "Réapprovisionnement préventif"
                priority = "normal"

            suggestions.append(ReorderSuggestion(
                product_id=product_id,
                product_name=product.get("product_name", ""),
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                suggested_quantity=qty,
                suggested_order_date=order_date,
                expected_delivery_date=delivery_date,
                reason=reason,
                priority=priority,
                estimated_cost=Decimal(str(qty)) * unit_cost,
                current_stock=current_stock,
                reorder_point=rop.reorder_level,
                eoq=eoq_result.adjusted_eoq or eoq_result.eoq,
                safety_stock=safety_result.safety_stock
            ))

        # Trier par priorité puis par coût
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        suggestions.sort(key=lambda x: (priority_order.get(x.priority, 9), -x.estimated_cost))

        return suggestions

    # =========================================================================
    # ABC-XYZ CLASSIFICATION
    # =========================================================================

    def classify_abc_xyz(
        self,
        products: List[Dict[str, Any]]
    ) -> List[ABCXYZClassification]:
        """
        Classification ABC (valeur) + XYZ (variabilité) combinée

        products: [{
            "product_id": int,
            "annual_value": Decimal,  # Valeur consommation annuelle
            "coefficient_variation": float
        }, ...]
        """
        if not products:
            return []

        # Trier par valeur décroissante pour ABC
        sorted_products = sorted(
            products,
            key=lambda x: Decimal(str(x.get("annual_value", 0))),
            reverse=True
        )

        total_value = sum(Decimal(str(p.get("annual_value", 0))) for p in sorted_products)

        classifications = []
        cumulative_value = Decimal("0")

        for product in sorted_products:
            annual_value = Decimal(str(product.get("annual_value", 0)))
            cv = product.get("coefficient_variation", 1.0)

            cumulative_value += annual_value
            cumulative_pct = float(cumulative_value / total_value) if total_value > 0 else 0

            # Classification ABC
            if cumulative_pct <= 0.80:
                abc_class = StockClassification.A
            elif cumulative_pct <= 0.95:
                abc_class = StockClassification.B
            else:
                abc_class = StockClassification.C

            # Classification XYZ
            if cv < 0.5:
                xyz_class = StockClassification.X
            elif cv < 1.0:
                xyz_class = StockClassification.Y
            else:
                xyz_class = StockClassification.Z

            combined = f"{abc_class.value}{xyz_class.value}"

            # Stratégies par classe combinée
            strategies = {
                "AX": ("Stock continu, prévision précise", "daily", "Minimum - demande prévisible"),
                "AY": ("Stock de sécurité modéré, révision fréquente", "daily", "Modéré"),
                "AZ": ("Stock de sécurité élevé, commande sur demande", "daily", "Élevé"),
                "BX": ("Stock périodique, EOQ", "weekly", "Faible"),
                "BY": ("Stock de sécurité standard", "weekly", "Modéré"),
                "BZ": ("Commande sur demande préférable", "weekly", "Élevé"),
                "CX": ("Kanban ou stock minimum", "monthly", "Minimum"),
                "CY": ("Stock minimum, tolérer ruptures", "monthly", "Faible"),
                "CZ": ("Commande uniquement sur besoin", "monthly", "Aucun - accepter ruptures"),
            }

            strategy, freq, ss_policy = strategies.get(
                combined,
                ("Standard", "weekly", "Standard")
            )

            classifications.append(ABCXYZClassification(
                product_id=product["product_id"],
                abc_class=abc_class,
                xyz_class=xyz_class,
                combined_class=combined,
                annual_value=annual_value,
                cumulative_value_pct=cumulative_pct,
                coefficient_variation=cv,
                recommended_strategy=strategy,
                review_frequency=freq,
                safety_stock_policy=ss_policy
            ))

        return classifications

    # =========================================================================
    # INTEGRATION AVEC BASE DE DONNÉES
    # =========================================================================

    async def get_product_inventory_analysis(
        self,
        tenant_id: int,
        product_id: int
    ) -> Dict[str, Any]:
        """
        Analyse complète d'inventaire pour un produit
        """
        if not self.db_pool:
            return {"error": "Database not configured"}

        async with self.db_pool.acquire() as conn:
            # Récupérer infos produit
            product = await conn.fetchrow("""
                SELECT id, name, supplier_id, unit_cost, current_stock
                FROM products
                WHERE id = $1 AND tenant_id = $2
            """, product_id, tenant_id)

            if not product:
                return {"error": "Product not found"}

            # Historique consommation (90 jours)
            consumption = await conn.fetch("""
                SELECT date, quantity
                FROM stock_movements
                WHERE product_id = $1
                  AND tenant_id = $2
                  AND movement_type = 'consumption'
                  AND date >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY date
            """, product_id, tenant_id)

            consumption_list = [
                {"date": row["date"], "quantity": row["quantity"]}
                for row in consumption
            ]

            # Analyse demande
            demand = self.analyze_demand(product_id, consumption_list)

            # EOQ
            annual_demand = demand.average_daily_demand * 365
            eoq = self.calculate_eoq(
                product_id=product_id,
                annual_demand=annual_demand,
                unit_cost=product["unit_cost"]
            )

            # Safety stock
            safety = self.calculate_safety_stock(
                product_id=product_id,
                average_daily_demand=demand.average_daily_demand,
                demand_std_dev=demand.demand_std_dev,
                average_lead_time_days=self.default_lead_time_days,
                unit_cost=product["unit_cost"]
            )

            # Reorder point
            rop = self.calculate_reorder_point(
                product_id=product_id,
                current_stock=product["current_stock"],
                average_daily_demand=demand.average_daily_demand,
                lead_time_days=self.default_lead_time_days,
                safety_stock=safety.safety_stock,
                eoq=eoq.adjusted_eoq or eoq.eoq
            )

            return {
                "product": dict(product),
                "demand_analysis": {
                    "average_daily": float(demand.average_daily_demand),
                    "std_dev": float(demand.demand_std_dev),
                    "cv": demand.coefficient_variation,
                    "pattern": demand.demand_pattern.value,
                    "trend": demand.trend
                },
                "eoq": {
                    "quantity": eoq.adjusted_eoq or eoq.eoq,
                    "orders_per_year": eoq.orders_per_year,
                    "total_cost": float(eoq.total_cost)
                },
                "safety_stock": {
                    "quantity": safety.safety_stock,
                    "value": float(safety.safety_stock_value),
                    "days_coverage": safety.safety_stock_days
                },
                "reorder_point": {
                    "level": rop.reorder_level,
                    "needs_reorder": rop.needs_reorder,
                    "urgency": rop.urgency,
                    "days_until_stockout": rop.days_until_stockout,
                    "suggested_qty": rop.suggested_order_qty
                }
            }


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def create_inventory_intelligence(db_pool=None) -> InventoryIntelligence:
    """Factory function pour créer une instance"""
    return InventoryIntelligence(db_pool=db_pool)


# Exemple d'utilisation
if __name__ == "__main__":
    from datetime import date

    # Créer instance
    inv = InventoryIntelligence()

    # Test EOQ
    eoq = inv.calculate_eoq(
        product_id=1,
        annual_demand=Decimal("1200"),  # 1200 unités/an
        unit_cost=Decimal("10.00"),      # 10€/unité
        ordering_cost=Decimal("25.00"),  # 25€/commande
        holding_cost_rate=0.25           # 25%/an
    )
    print(f"EOQ: {eoq.eoq} unités")
    print(f"Commandes/an: {eoq.orders_per_year:.1f}")
    print(f"Coût total: {eoq.total_cost:.2f}€")

    # Test Safety Stock
    safety = inv.calculate_safety_stock(
        product_id=1,
        average_daily_demand=Decimal("10"),
        demand_std_dev=Decimal("3"),
        average_lead_time_days=5,
        lead_time_std_dev=1,
        service_level=ServiceLevel.STANDARD,
        unit_cost=Decimal("10.00")
    )
    print(f"\nSafety Stock: {safety.safety_stock} unités")
    print(f"Valeur: {safety.safety_stock_value:.2f}€")

    # Test Reorder Point
    rop = inv.calculate_reorder_point(
        product_id=1,
        current_stock=45,
        average_daily_demand=Decimal("10"),
        lead_time_days=5,
        safety_stock=safety.safety_stock,
        eoq=eoq.eoq
    )
    print(f"\nReorder Point: {rop.reorder_level}")
    print(f"Besoin réappro: {rop.needs_reorder}")
    print(f"Urgence: {rop.urgency}")
