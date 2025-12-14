"""
Calcul automatique des marges brutes et opérationnelles.

Fonctionnalités:
- Marge brute par produit/catégorie/période
- Marge opérationnelle avec charges
- PAMP (Prix d'Achat Moyen Pondéré)
- Valorisation des pertes/vols
- Snapshots journalisés
- Analyse par menu restaurant
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean

from sqlalchemy import text
from core.data_repository import get_engine


class MarginType(str, Enum):
    """Types de marge."""
    GROSS = "gross"  # Marge brute (vente - achat)
    OPERATIONAL = "operational"  # Marge opérationnelle (- charges variables)
    NET = "net"  # Marge nette (- charges fixes)


class PeriodType(str, Enum):
    """Types de période."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class MarginResult:
    """Résultat de calcul de marge."""
    entity_type: str  # product, category, menu, total
    entity_id: Optional[int]
    entity_name: str
    period_start: date
    period_end: date

    # Montants
    revenue: float  # Chiffre d'affaires HT
    cost_of_goods: float  # Coût matière
    gross_margin: float  # Marge brute
    gross_margin_pct: float  # % marge brute

    variable_costs: float  # Charges variables
    operational_margin: float  # Marge opérationnelle
    operational_margin_pct: float

    fixed_costs: float  # Charges fixes (pro-rata)
    net_margin: float  # Marge nette
    net_margin_pct: float

    # Détails
    quantity_sold: float
    average_selling_price: float
    average_cost_price: float
    pamp: float  # Prix d'Achat Moyen Pondéré

    loss_value: float  # Valorisation pertes/vols
    wastage_pct: float

    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PAMPHistory:
    """Historique du PAMP."""
    product_id: int
    pamp: float
    quantity_in_stock: float
    last_purchase_price: float
    last_purchase_date: date
    history: List[Dict[str, Any]]


class MarginCalculator:
    """Calculateur de marges avancé."""

    # Répartition des charges par défaut
    DEFAULT_VARIABLE_COST_RATE = 0.15  # 15% des ventes
    DEFAULT_FIXED_COST_MONTHLY = 5000  # 5000€/mois par défaut

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._ensure_tables()
        self._config = self._load_config()

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS margin_snapshots (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    snapshot_date DATE NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id INTEGER,
                    entity_name VARCHAR(200),
                    period_type VARCHAR(20) NOT NULL,

                    revenue NUMERIC(12,2) DEFAULT 0,
                    cost_of_goods NUMERIC(12,2) DEFAULT 0,
                    gross_margin NUMERIC(12,2) DEFAULT 0,
                    gross_margin_pct NUMERIC(5,2) DEFAULT 0,

                    variable_costs NUMERIC(12,2) DEFAULT 0,
                    operational_margin NUMERIC(12,2) DEFAULT 0,
                    operational_margin_pct NUMERIC(5,2) DEFAULT 0,

                    fixed_costs NUMERIC(12,2) DEFAULT 0,
                    net_margin NUMERIC(12,2) DEFAULT 0,
                    net_margin_pct NUMERIC(5,2) DEFAULT 0,

                    quantity_sold NUMERIC(10,2) DEFAULT 0,
                    pamp NUMERIC(10,4) DEFAULT 0,
                    loss_value NUMERIC(10,2) DEFAULT 0,

                    details JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),

                    UNIQUE(tenant_id, snapshot_date, entity_type, entity_id, period_type)
                );

                CREATE INDEX IF NOT EXISTS idx_margin_snapshots_lookup
                    ON margin_snapshots(tenant_id, entity_type, snapshot_date);

                CREATE TABLE IF NOT EXISTS pamp_history (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    pamp NUMERIC(10,4) NOT NULL,
                    quantity NUMERIC(10,2) NOT NULL,
                    purchase_price NUMERIC(10,4),
                    purchase_quantity NUMERIC(10,2),
                    calculated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_pamp_history_product
                    ON pamp_history(tenant_id, product_id, calculated_at);

                CREATE TABLE IF NOT EXISTS margin_config (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER UNIQUE NOT NULL,
                    variable_cost_rate NUMERIC(5,4) DEFAULT 0.15,
                    fixed_cost_monthly NUMERIC(12,2) DEFAULT 5000,
                    target_gross_margin_pct NUMERIC(5,2) DEFAULT 30,
                    target_net_margin_pct NUMERIC(5,2) DEFAULT 10,
                    tva_rates JSONB DEFAULT '{"standard": 20, "reduced": 10, "super_reduced": 5.5}',
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration des marges."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT variable_cost_rate, fixed_cost_monthly,
                           target_gross_margin_pct, target_net_margin_pct, tva_rates
                    FROM margin_config
                    WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": self.tenant_id}
            )
            row = result.fetchone()

            if row:
                return {
                    "variable_cost_rate": float(row.variable_cost_rate or 0.15),
                    "fixed_cost_monthly": float(row.fixed_cost_monthly or 5000),
                    "target_gross_margin_pct": float(row.target_gross_margin_pct or 30),
                    "target_net_margin_pct": float(row.target_net_margin_pct or 10),
                    "tva_rates": row.tva_rates if isinstance(row.tva_rates, dict) else json.loads(row.tva_rates or "{}"),
                }

        return {
            "variable_cost_rate": self.DEFAULT_VARIABLE_COST_RATE,
            "fixed_cost_monthly": self.DEFAULT_FIXED_COST_MONTHLY,
            "target_gross_margin_pct": 30,
            "target_net_margin_pct": 10,
            "tva_rates": {"standard": 20, "reduced": 10, "super_reduced": 5.5},
        }

    def calculate_product_margin(
        self,
        product_id: int,
        period_start: date,
        period_end: date
    ) -> MarginResult:
        """Calcule la marge pour un produit."""
        engine = get_engine()

        with engine.connect() as conn:
            # Récupérer les ventes
            sales_result = conn.execute(
                text("""
                    SELECT
                        p.id,
                        p.nom,
                        COALESCE(SUM(v.quantite), 0) as quantity_sold,
                        COALESCE(SUM(v.quantite * v.prix_unitaire), 0) as revenue,
                        COALESCE(AVG(v.prix_unitaire), p.prix_vente) as avg_price
                    FROM produits p
                    LEFT JOIN ventes v ON p.id = v.product_id
                        AND v.date BETWEEN :start AND :end
                    WHERE p.id = :product_id
                      AND p.tenant_id = :tenant_id
                    GROUP BY p.id, p.nom, p.prix_vente
                """),
                {
                    "tenant_id": self.tenant_id,
                    "product_id": product_id,
                    "start": period_start,
                    "end": period_end,
                }
            )
            sales_row = sales_result.fetchone()

            if not sales_row:
                return self._empty_margin_result("product", product_id, "Inconnu", period_start, period_end)

            # Calculer le PAMP
            pamp = self.calculate_pamp(product_id)

            quantity_sold = float(sales_row.quantity_sold or 0)
            revenue = float(sales_row.revenue or 0)
            avg_price = float(sales_row.avg_price or 0)

            # Coût des marchandises vendues
            cost_of_goods = quantity_sold * pamp.pamp

            # Marge brute
            gross_margin = revenue - cost_of_goods
            gross_margin_pct = (gross_margin / revenue * 100) if revenue > 0 else 0

            # Charges variables (% du CA)
            variable_costs = revenue * self._config["variable_cost_rate"]
            operational_margin = gross_margin - variable_costs
            operational_margin_pct = (operational_margin / revenue * 100) if revenue > 0 else 0

            # Charges fixes (pro-rata basé sur le % des ventes)
            total_revenue = self._get_total_revenue(period_start, period_end)
            revenue_share = revenue / total_revenue if total_revenue > 0 else 0
            days_in_period = (period_end - period_start).days + 1
            fixed_costs = (self._config["fixed_cost_monthly"] / 30 * days_in_period) * revenue_share

            net_margin = operational_margin - fixed_costs
            net_margin_pct = (net_margin / revenue * 100) if revenue > 0 else 0

            # Pertes
            loss_value = self._calculate_loss_value(product_id, period_start, period_end, pamp.pamp)

            return MarginResult(
                entity_type="product",
                entity_id=product_id,
                entity_name=sales_row.nom,
                period_start=period_start,
                period_end=period_end,
                revenue=round(revenue, 2),
                cost_of_goods=round(cost_of_goods, 2),
                gross_margin=round(gross_margin, 2),
                gross_margin_pct=round(gross_margin_pct, 2),
                variable_costs=round(variable_costs, 2),
                operational_margin=round(operational_margin, 2),
                operational_margin_pct=round(operational_margin_pct, 2),
                fixed_costs=round(fixed_costs, 2),
                net_margin=round(net_margin, 2),
                net_margin_pct=round(net_margin_pct, 2),
                quantity_sold=round(quantity_sold, 2),
                average_selling_price=round(avg_price, 2),
                average_cost_price=round(pamp.pamp, 4),
                pamp=round(pamp.pamp, 4),
                loss_value=round(loss_value, 2),
                wastage_pct=round((loss_value / cost_of_goods * 100) if cost_of_goods > 0 else 0, 2),
                details={
                    "last_purchase_price": pamp.last_purchase_price,
                    "quantity_in_stock": pamp.quantity_in_stock,
                },
            )

    def calculate_category_margin(
        self,
        category: str,
        period_start: date,
        period_end: date
    ) -> MarginResult:
        """Calcule la marge pour une catégorie."""
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        COALESCE(SUM(v.quantite), 0) as quantity_sold,
                        COALESCE(SUM(v.quantite * v.prix_unitaire), 0) as revenue,
                        COALESCE(SUM(v.quantite * COALESCE(p.prix_achat, 0)), 0) as cost_of_goods
                    FROM produits p
                    LEFT JOIN ventes v ON p.id = v.product_id
                        AND v.date BETWEEN :start AND :end
                    WHERE p.categorie = :category
                      AND p.tenant_id = :tenant_id
                """),
                {
                    "tenant_id": self.tenant_id,
                    "category": category,
                    "start": period_start,
                    "end": period_end,
                }
            )
            row = result.fetchone()

            quantity_sold = float(row.quantity_sold or 0)
            revenue = float(row.revenue or 0)
            cost_of_goods = float(row.cost_of_goods or 0)

        return self._build_margin_result(
            entity_type="category",
            entity_id=None,
            entity_name=category,
            period_start=period_start,
            period_end=period_end,
            revenue=revenue,
            cost_of_goods=cost_of_goods,
            quantity_sold=quantity_sold,
        )

    def calculate_total_margin(
        self,
        period_start: date,
        period_end: date,
        include_restaurant: bool = True
    ) -> MarginResult:
        """Calcule la marge totale."""
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        COALESCE(SUM(v.quantite), 0) as quantity_sold,
                        COALESCE(SUM(v.quantite * v.prix_unitaire), 0) as revenue,
                        COALESCE(SUM(v.quantite * COALESCE(p.prix_achat, 0)), 0) as cost_of_goods
                    FROM produits p
                    LEFT JOIN ventes v ON p.id = v.product_id
                        AND v.date BETWEEN :start AND :end
                    WHERE p.tenant_id = :tenant_id
                """),
                {
                    "tenant_id": self.tenant_id,
                    "start": period_start,
                    "end": period_end,
                }
            )
            row = result.fetchone()

            revenue = float(row.revenue or 0)
            cost_of_goods = float(row.cost_of_goods or 0)
            quantity_sold = float(row.quantity_sold or 0)

            # Ajouter le restaurant si demandé
            if include_restaurant:
                restaurant_result = conn.execute(
                    text("""
                        SELECT
                            COALESCE(SUM(prix_vente), 0) as revenue,
                            COALESCE(SUM(cout_matiere), 0) as cost
                        FROM restaurant_ventes
                        WHERE tenant_id = :tenant_id
                          AND date BETWEEN :start AND :end
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "start": period_start,
                        "end": period_end,
                    }
                )
                rest_row = restaurant_result.fetchone()
                if rest_row:
                    revenue += float(rest_row.revenue or 0)
                    cost_of_goods += float(rest_row.cost or 0)

        return self._build_margin_result(
            entity_type="total",
            entity_id=None,
            entity_name="Total",
            period_start=period_start,
            period_end=period_end,
            revenue=revenue,
            cost_of_goods=cost_of_goods,
            quantity_sold=quantity_sold,
        )

    def calculate_menu_margin(
        self,
        menu_id: int,
        period_start: date,
        period_end: date
    ) -> MarginResult:
        """Calcule la marge pour un menu restaurant."""
        engine = get_engine()

        with engine.connect() as conn:
            # Récupérer les infos du menu
            menu_result = conn.execute(
                text("""
                    SELECT nom, prix_vente
                    FROM restaurant_menus
                    WHERE id = :menu_id AND tenant_id = :tenant_id
                """),
                {"menu_id": menu_id, "tenant_id": self.tenant_id}
            )
            menu_row = menu_result.fetchone()

            if not menu_row:
                return self._empty_margin_result("menu", menu_id, "Menu inconnu", period_start, period_end)

            # Calculer le coût matière du menu
            cost_result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(mi.quantite * COALESCE(p.prix_achat, 0)), 0) as cost
                    FROM restaurant_menu_ingredients mi
                    JOIN produits p ON mi.product_id = p.id
                    WHERE mi.menu_id = :menu_id
                """),
                {"menu_id": menu_id}
            )
            cost_row = cost_result.fetchone()

            # Ventes du menu
            sales_result = conn.execute(
                text("""
                    SELECT COUNT(*) as quantity, SUM(prix_vente) as revenue
                    FROM restaurant_ventes
                    WHERE menu_id = :menu_id
                      AND tenant_id = :tenant_id
                      AND date BETWEEN :start AND :end
                """),
                {
                    "menu_id": menu_id,
                    "tenant_id": self.tenant_id,
                    "start": period_start,
                    "end": period_end,
                }
            )
            sales_row = sales_result.fetchone()

            quantity_sold = float(sales_row.quantity or 0)
            revenue = float(sales_row.revenue or 0)
            cost_per_unit = float(cost_row.cost or 0)
            cost_of_goods = cost_per_unit * quantity_sold

        return self._build_margin_result(
            entity_type="menu",
            entity_id=menu_id,
            entity_name=menu_row.nom,
            period_start=period_start,
            period_end=period_end,
            revenue=revenue,
            cost_of_goods=cost_of_goods,
            quantity_sold=quantity_sold,
            extra_details={"cost_per_unit": round(cost_per_unit, 2)},
        )

    def calculate_pamp(self, product_id: int) -> PAMPHistory:
        """Calcule le Prix d'Achat Moyen Pondéré."""
        engine = get_engine()

        with engine.connect() as conn:
            # Récupérer l'historique des achats
            result = conn.execute(
                text("""
                    SELECT hp.prix, hp.quantite, hp.date
                    FROM historique_prix hp
                    WHERE hp.product_id = :product_id
                    ORDER BY hp.date DESC
                    LIMIT 20
                """),
                {"product_id": product_id}
            )

            purchases = [dict(row._mapping) for row in result]

            if not purchases:
                # Fallback sur le prix d'achat actuel
                prod_result = conn.execute(
                    text("SELECT prix_achat, stock_actuel FROM produits WHERE id = :id"),
                    {"id": product_id}
                )
                prod_row = prod_result.fetchone()
                if prod_row:
                    return PAMPHistory(
                        product_id=product_id,
                        pamp=float(prod_row.prix_achat or 0),
                        quantity_in_stock=float(prod_row.stock_actuel or 0),
                        last_purchase_price=float(prod_row.prix_achat or 0),
                        last_purchase_date=date.today(),
                        history=[],
                    )
                return PAMPHistory(product_id, 0, 0, 0, date.today(), [])

            # Calcul du PAMP
            total_value = 0
            total_quantity = 0

            for p in purchases:
                qty = float(p.get("quantite") or 1)
                price = float(p.get("prix") or 0)
                total_value += qty * price
                total_quantity += qty

            pamp = total_value / total_quantity if total_quantity > 0 else 0

            # Stock actuel
            stock_result = conn.execute(
                text("SELECT stock_actuel FROM produits WHERE id = :id"),
                {"id": product_id}
            )
            stock_row = stock_result.fetchone()

            return PAMPHistory(
                product_id=product_id,
                pamp=round(pamp, 4),
                quantity_in_stock=float(stock_row.stock_actuel or 0) if stock_row else 0,
                last_purchase_price=float(purchases[0]["prix"]),
                last_purchase_date=purchases[0]["date"] if isinstance(purchases[0]["date"], date) else date.today(),
                history=[
                    {"date": str(p["date"]), "price": float(p["prix"]), "quantity": float(p.get("quantite") or 1)}
                    for p in purchases[:5]
                ],
            )

    def _build_margin_result(
        self,
        entity_type: str,
        entity_id: Optional[int],
        entity_name: str,
        period_start: date,
        period_end: date,
        revenue: float,
        cost_of_goods: float,
        quantity_sold: float,
        extra_details: Dict = None
    ) -> MarginResult:
        """Construit un résultat de marge complet."""
        # Marge brute
        gross_margin = revenue - cost_of_goods
        gross_margin_pct = (gross_margin / revenue * 100) if revenue > 0 else 0

        # Charges variables
        variable_costs = revenue * self._config["variable_cost_rate"]
        operational_margin = gross_margin - variable_costs
        operational_margin_pct = (operational_margin / revenue * 100) if revenue > 0 else 0

        # Charges fixes (pro-rata)
        days_in_period = (period_end - period_start).days + 1
        fixed_costs = self._config["fixed_cost_monthly"] / 30 * days_in_period
        net_margin = operational_margin - fixed_costs
        net_margin_pct = (net_margin / revenue * 100) if revenue > 0 else 0

        # Prix moyens
        avg_selling_price = revenue / quantity_sold if quantity_sold > 0 else 0
        avg_cost_price = cost_of_goods / quantity_sold if quantity_sold > 0 else 0

        details = extra_details or {}

        return MarginResult(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            period_start=period_start,
            period_end=period_end,
            revenue=round(revenue, 2),
            cost_of_goods=round(cost_of_goods, 2),
            gross_margin=round(gross_margin, 2),
            gross_margin_pct=round(gross_margin_pct, 2),
            variable_costs=round(variable_costs, 2),
            operational_margin=round(operational_margin, 2),
            operational_margin_pct=round(operational_margin_pct, 2),
            fixed_costs=round(fixed_costs, 2),
            net_margin=round(net_margin, 2),
            net_margin_pct=round(net_margin_pct, 2),
            quantity_sold=round(quantity_sold, 2),
            average_selling_price=round(avg_selling_price, 2),
            average_cost_price=round(avg_cost_price, 4),
            pamp=round(avg_cost_price, 4),
            loss_value=0,
            wastage_pct=0,
            details=details,
        )

    def _empty_margin_result(
        self,
        entity_type: str,
        entity_id: Optional[int],
        entity_name: str,
        period_start: date,
        period_end: date
    ) -> MarginResult:
        """Retourne un résultat vide."""
        return MarginResult(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            period_start=period_start,
            period_end=period_end,
            revenue=0, cost_of_goods=0, gross_margin=0, gross_margin_pct=0,
            variable_costs=0, operational_margin=0, operational_margin_pct=0,
            fixed_costs=0, net_margin=0, net_margin_pct=0,
            quantity_sold=0, average_selling_price=0, average_cost_price=0,
            pamp=0, loss_value=0, wastage_pct=0,
        )

    def _get_total_revenue(self, period_start: date, period_end: date) -> float:
        """Récupère le CA total sur la période."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(quantite * prix_unitaire), 0) as total
                    FROM ventes v
                    JOIN produits p ON v.product_id = p.id
                    WHERE p.tenant_id = :tenant_id
                      AND v.date BETWEEN :start AND :end
                """),
                {"tenant_id": self.tenant_id, "start": period_start, "end": period_end}
            )
            row = result.fetchone()
            return float(row.total or 0)

    def _calculate_loss_value(
        self,
        product_id: int,
        period_start: date,
        period_end: date,
        pamp: float
    ) -> float:
        """Calcule la valeur des pertes/vols."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(ABS(quantite)), 0) as lost_quantity
                    FROM mouvements_stock
                    WHERE product_id = :product_id
                      AND type_mouvement IN ('perte', 'vol', 'casse', 'peremption')
                      AND date BETWEEN :start AND :end
                """),
                {"product_id": product_id, "start": period_start, "end": period_end}
            )
            row = result.fetchone()
            lost_qty = float(row.lost_quantity or 0)
            return lost_qty * pamp

    def save_snapshot(self, result: MarginResult, period_type: PeriodType = PeriodType.DAY):
        """Sauvegarde un snapshot de marge."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO margin_snapshots
                    (tenant_id, snapshot_date, entity_type, entity_id, entity_name, period_type,
                     revenue, cost_of_goods, gross_margin, gross_margin_pct,
                     variable_costs, operational_margin, operational_margin_pct,
                     fixed_costs, net_margin, net_margin_pct,
                     quantity_sold, pamp, loss_value, details)
                    VALUES
                    (:tenant_id, :date, :entity_type, :entity_id, :entity_name, :period_type,
                     :revenue, :cost_of_goods, :gross_margin, :gross_margin_pct,
                     :variable_costs, :operational_margin, :operational_margin_pct,
                     :fixed_costs, :net_margin, :net_margin_pct,
                     :quantity_sold, :pamp, :loss_value, :details)
                    ON CONFLICT (tenant_id, snapshot_date, entity_type, entity_id, period_type)
                    DO UPDATE SET
                        revenue = EXCLUDED.revenue,
                        cost_of_goods = EXCLUDED.cost_of_goods,
                        gross_margin = EXCLUDED.gross_margin,
                        gross_margin_pct = EXCLUDED.gross_margin_pct,
                        operational_margin = EXCLUDED.operational_margin,
                        operational_margin_pct = EXCLUDED.operational_margin_pct,
                        net_margin = EXCLUDED.net_margin,
                        net_margin_pct = EXCLUDED.net_margin_pct
                """),
                {
                    "tenant_id": self.tenant_id,
                    "date": result.period_end,
                    "entity_type": result.entity_type,
                    "entity_id": result.entity_id,
                    "entity_name": result.entity_name,
                    "period_type": period_type.value,
                    "revenue": result.revenue,
                    "cost_of_goods": result.cost_of_goods,
                    "gross_margin": result.gross_margin,
                    "gross_margin_pct": result.gross_margin_pct,
                    "variable_costs": result.variable_costs,
                    "operational_margin": result.operational_margin,
                    "operational_margin_pct": result.operational_margin_pct,
                    "fixed_costs": result.fixed_costs,
                    "net_margin": result.net_margin,
                    "net_margin_pct": result.net_margin_pct,
                    "quantity_sold": result.quantity_sold,
                    "pamp": result.pamp,
                    "loss_value": result.loss_value,
                    "details": json.dumps(result.details),
                }
            )

    def get_margin_history(
        self,
        entity_type: str,
        entity_id: Optional[int],
        period_type: PeriodType = PeriodType.DAY,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Récupère l'historique des marges."""
        engine = get_engine()
        with engine.connect() as conn:
            query = """
                SELECT snapshot_date, revenue, gross_margin, gross_margin_pct,
                       operational_margin, operational_margin_pct,
                       net_margin, net_margin_pct
                FROM margin_snapshots
                WHERE tenant_id = :tenant_id
                  AND entity_type = :entity_type
                  AND period_type = :period_type
            """
            params = {
                "tenant_id": self.tenant_id,
                "entity_type": entity_type,
                "period_type": period_type.value,
                "limit": limit,
            }

            if entity_id is not None:
                query += " AND entity_id = :entity_id"
                params["entity_id"] = entity_id

            query += " ORDER BY snapshot_date DESC LIMIT :limit"

            result = conn.execute(text(query), params)

            return [
                {
                    "date": row.snapshot_date.isoformat() if row.snapshot_date else None,
                    "revenue": float(row.revenue or 0),
                    "gross_margin": float(row.gross_margin or 0),
                    "gross_margin_pct": float(row.gross_margin_pct or 0),
                    "operational_margin": float(row.operational_margin or 0),
                    "operational_margin_pct": float(row.operational_margin_pct or 0),
                    "net_margin": float(row.net_margin or 0),
                    "net_margin_pct": float(row.net_margin_pct or 0),
                }
                for row in result
            ]

    def get_margin_alerts(self, threshold_pct: float = None) -> List[Dict[str, Any]]:
        """Identifie les produits/catégories avec marges sous le seuil."""
        threshold = threshold_pct or self._config["target_gross_margin_pct"]
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT entity_type, entity_id, entity_name, gross_margin_pct,
                           snapshot_date, revenue
                    FROM margin_snapshots
                    WHERE tenant_id = :tenant_id
                      AND gross_margin_pct < :threshold
                      AND revenue > 100
                      AND snapshot_date >= NOW() - INTERVAL '7 days'
                    ORDER BY gross_margin_pct ASC
                    LIMIT 20
                """),
                {"tenant_id": self.tenant_id, "threshold": threshold}
            )

            return [
                {
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "entity_name": row.entity_name,
                    "margin_pct": float(row.gross_margin_pct or 0),
                    "target_pct": threshold,
                    "gap": round(threshold - float(row.gross_margin_pct or 0), 2),
                    "date": row.snapshot_date.isoformat() if row.snapshot_date else None,
                }
                for row in result
            ]
