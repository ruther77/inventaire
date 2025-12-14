"""
Comptabilité analytique multi-axes.

Fonctionnalités:
- Axes d'analyse configurables (activité, rayon, projet, centre de coût)
- Affectation des dépenses sur plusieurs axes
- Répartition automatique et manuelle
- Rapports multi-dimensionnels
- Comparaison budgétaire
"""

from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal

from sqlalchemy import text
from core.data_repository import get_engine


class AxisType(str, Enum):
    """Types d'axes analytiques."""
    ACTIVITY = "activity"  # Épicerie, Restaurant
    DEPARTMENT = "department"  # Rayon, Section
    PROJECT = "project"  # Menu spécial, Événement
    COST_CENTER = "cost_center"  # Cuisine, Livraison, Stockage
    PRODUCT_CATEGORY = "product_category"
    SUPPLIER = "supplier"
    CUSTOM = "custom"


@dataclass
class AnalyticAxis:
    """Représentation d'un axe analytique."""
    id: int
    tenant_id: int
    axis_type: AxisType
    code: str
    name: str
    parent_id: Optional[int] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticAssignment:
    """Affectation d'un montant sur un axe."""
    id: int
    source_type: str  # expense, invoice, transaction
    source_id: int
    axis_id: int
    amount: float
    percentage: float  # % du montant source
    assignment_date: date
    auto_assigned: bool


@dataclass
class AnalyticReport:
    """Rapport analytique."""
    axis_type: AxisType
    period_start: date
    period_end: date
    breakdown: List[Dict[str, Any]]
    totals: Dict[str, float]
    comparisons: Optional[Dict[str, Any]] = None


class AnalyticAccountingEngine:
    """Moteur de comptabilité analytique."""

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._ensure_tables()
        self._axes_cache: Dict[int, AnalyticAxis] = {}

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analytic_axes (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    axis_type VARCHAR(50) NOT NULL,
                    code VARCHAR(50) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    parent_id INTEGER REFERENCES analytic_axes(id),
                    active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(tenant_id, axis_type, code)
                );

                CREATE INDEX IF NOT EXISTS idx_analytic_axes_tenant
                    ON analytic_axes(tenant_id, axis_type, active);

                CREATE TABLE IF NOT EXISTS analytic_assignments (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    source_type VARCHAR(50) NOT NULL,
                    source_id INTEGER NOT NULL,
                    axis_id INTEGER NOT NULL REFERENCES analytic_axes(id),
                    amount NUMERIC(12,2) NOT NULL,
                    percentage NUMERIC(5,2) NOT NULL,
                    assignment_date DATE NOT NULL,
                    auto_assigned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    created_by VARCHAR(100)
                );

                CREATE INDEX IF NOT EXISTS idx_assignments_source
                    ON analytic_assignments(tenant_id, source_type, source_id);
                CREATE INDEX IF NOT EXISTS idx_assignments_axis
                    ON analytic_assignments(axis_id, assignment_date);

                CREATE TABLE IF NOT EXISTS analytic_budgets (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    axis_id INTEGER NOT NULL REFERENCES analytic_axes(id),
                    period_year INTEGER NOT NULL,
                    period_month INTEGER,  -- NULL pour budget annuel
                    budget_amount NUMERIC(12,2) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(tenant_id, axis_id, period_year, period_month)
                );

                CREATE TABLE IF NOT EXISTS analytic_rules (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    priority INTEGER DEFAULT 0,
                    conditions JSONB NOT NULL,
                    assignments JSONB NOT NULL, -- [{axis_id, percentage}]
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

    def create_axis(
        self,
        axis_type: AxisType,
        code: str,
        name: str,
        parent_id: Optional[int] = None,
        metadata: Dict = None
    ) -> int:
        """Crée un nouvel axe analytique."""
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO analytic_axes
                    (tenant_id, axis_type, code, name, parent_id, metadata)
                    VALUES (:tenant_id, :axis_type, :code, :name, :parent_id, :metadata)
                    ON CONFLICT (tenant_id, axis_type, code) DO UPDATE SET
                        name = EXCLUDED.name,
                        parent_id = EXCLUDED.parent_id,
                        metadata = EXCLUDED.metadata
                    RETURNING id
                """),
                {
                    "tenant_id": self.tenant_id,
                    "axis_type": axis_type.value,
                    "code": code,
                    "name": name,
                    "parent_id": parent_id,
                    "metadata": json.dumps(metadata or {}),
                }
            )
            row = result.fetchone()
            return row.id

    def get_axes(self, axis_type: Optional[AxisType] = None) -> List[AnalyticAxis]:
        """Récupère les axes analytiques."""
        engine = get_engine()
        query = """
            SELECT id, tenant_id, axis_type, code, name, parent_id, active, metadata
            FROM analytic_axes
            WHERE tenant_id = :tenant_id AND active = TRUE
        """
        params = {"tenant_id": self.tenant_id}

        if axis_type:
            query += " AND axis_type = :axis_type"
            params["axis_type"] = axis_type.value

        query += " ORDER BY axis_type, code"

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [
                AnalyticAxis(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    axis_type=AxisType(row.axis_type),
                    code=row.code,
                    name=row.name,
                    parent_id=row.parent_id,
                    active=row.active,
                    metadata=row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}"),
                )
                for row in result
            ]

    def assign_expense(
        self,
        source_type: str,
        source_id: int,
        total_amount: float,
        assignments: List[Tuple[int, float]],  # [(axis_id, percentage), ...]
        assignment_date: date = None,
        auto: bool = False,
        user: str = None
    ):
        """Affecte une dépense sur plusieurs axes."""
        if not assignments:
            return

        # Valider que les pourcentages totalisent 100%
        total_pct = sum(a[1] for a in assignments)
        if abs(total_pct - 100) > 0.01:
            # Normaliser
            assignments = [(a[0], a[1] / total_pct * 100) for a in assignments]

        assignment_date = assignment_date or date.today()
        engine = get_engine()

        with engine.begin() as conn:
            # Supprimer les anciennes affectations
            conn.execute(
                text("""
                    DELETE FROM analytic_assignments
                    WHERE tenant_id = :tenant_id
                      AND source_type = :source_type
                      AND source_id = :source_id
                """),
                {
                    "tenant_id": self.tenant_id,
                    "source_type": source_type,
                    "source_id": source_id,
                }
            )

            # Créer les nouvelles
            for axis_id, percentage in assignments:
                amount = total_amount * percentage / 100
                conn.execute(
                    text("""
                        INSERT INTO analytic_assignments
                        (tenant_id, source_type, source_id, axis_id, amount, percentage, assignment_date, auto_assigned, created_by)
                        VALUES (:tenant_id, :source_type, :source_id, :axis_id, :amount, :percentage, :date, :auto, :user)
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "source_type": source_type,
                        "source_id": source_id,
                        "axis_id": axis_id,
                        "amount": amount,
                        "percentage": percentage,
                        "date": assignment_date,
                        "auto": auto,
                        "user": user,
                    }
                )

    def auto_assign(
        self,
        source_type: str,
        source_id: int,
        total_amount: float,
        context: Dict[str, Any]
    ) -> bool:
        """Affecte automatiquement selon les règles définies."""
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, conditions, assignments
                    FROM analytic_rules
                    WHERE tenant_id = :tenant_id AND active = TRUE
                    ORDER BY priority DESC
                """),
                {"tenant_id": self.tenant_id}
            )

            for row in result:
                conditions = row.conditions if isinstance(row.conditions, dict) else json.loads(row.conditions)
                if self._match_conditions(conditions, context):
                    assignments_config = row.assignments if isinstance(row.assignments, list) else json.loads(row.assignments)
                    assignments = [(a["axis_id"], a["percentage"]) for a in assignments_config]
                    self.assign_expense(
                        source_type, source_id, total_amount, assignments,
                        auto=True
                    )
                    return True

        # Fallback: affecter à l'axe par défaut selon le type
        default_axis = self._get_default_axis(context)
        if default_axis:
            self.assign_expense(
                source_type, source_id, total_amount,
                [(default_axis, 100.0)],
                auto=True
            )
            return True

        return False

    def _match_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Vérifie si les conditions sont remplies."""
        for key, expected in conditions.items():
            actual = context.get(key)
            if actual is None:
                return False

            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif isinstance(expected, dict):
                if "min" in expected and actual < expected["min"]:
                    return False
                if "max" in expected and actual > expected["max"]:
                    return False
                if "contains" in expected and expected["contains"] not in str(actual).lower():
                    return False
            else:
                if actual != expected:
                    return False

        return True

    def _get_default_axis(self, context: Dict) -> Optional[int]:
        """Retourne l'axe par défaut selon le contexte."""
        # Logique simple: chercher un axe correspondant à la catégorie
        category = context.get("category", "").lower()
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id FROM analytic_axes
                    WHERE tenant_id = :tenant_id
                      AND active = TRUE
                      AND (LOWER(code) = :category OR LOWER(name) LIKE :pattern)
                    LIMIT 1
                """),
                {
                    "tenant_id": self.tenant_id,
                    "category": category,
                    "pattern": f"%{category}%",
                }
            )
            row = result.fetchone()
            return row.id if row else None

    def get_report(
        self,
        axis_type: AxisType,
        period_start: date,
        period_end: date,
        compare_with_budget: bool = True,
        compare_with_previous: bool = True
    ) -> AnalyticReport:
        """Génère un rapport analytique."""
        engine = get_engine()

        with engine.connect() as conn:
            # Récupérer les montants par axe
            result = conn.execute(
                text("""
                    SELECT
                        aa.id as axis_id,
                        aa.code,
                        aa.name,
                        COALESCE(SUM(asg.amount), 0) as total_amount,
                        COUNT(DISTINCT asg.source_id) as transaction_count
                    FROM analytic_axes aa
                    LEFT JOIN analytic_assignments asg ON aa.id = asg.axis_id
                        AND asg.assignment_date BETWEEN :start AND :end
                        AND asg.tenant_id = :tenant_id
                    WHERE aa.tenant_id = :tenant_id
                      AND aa.axis_type = :axis_type
                      AND aa.active = TRUE
                    GROUP BY aa.id, aa.code, aa.name
                    ORDER BY total_amount DESC
                """),
                {
                    "tenant_id": self.tenant_id,
                    "axis_type": axis_type.value,
                    "start": period_start,
                    "end": period_end,
                }
            )

            breakdown = []
            total_amount = 0

            for row in result:
                amount = float(row.total_amount or 0)
                total_amount += amount

                item = {
                    "axis_id": row.axis_id,
                    "code": row.code,
                    "name": row.name,
                    "amount": round(amount, 2),
                    "transaction_count": row.transaction_count,
                }

                # Budget
                if compare_with_budget:
                    budget = self._get_budget(row.axis_id, period_start, period_end)
                    item["budget"] = budget
                    item["budget_variance"] = round(budget - amount, 2) if budget else None
                    item["budget_variance_pct"] = round((budget - amount) / budget * 100, 1) if budget else None

                # Période précédente
                if compare_with_previous:
                    period_days = (period_end - period_start).days
                    prev_start = period_start - timedelta(days=period_days + 1)
                    prev_end = period_start - timedelta(days=1)
                    prev_amount = self._get_period_amount(row.axis_id, prev_start, prev_end)
                    item["previous_amount"] = round(prev_amount, 2)
                    item["change_pct"] = round((amount - prev_amount) / prev_amount * 100, 1) if prev_amount else None

                breakdown.append(item)

            # Calculer les pourcentages
            for item in breakdown:
                item["percentage"] = round(item["amount"] / total_amount * 100, 1) if total_amount > 0 else 0

            comparisons = None
            if compare_with_budget or compare_with_previous:
                comparisons = {
                    "total_budget": sum(i.get("budget") or 0 for i in breakdown),
                    "total_previous": sum(i.get("previous_amount") or 0 for i in breakdown),
                }

            return AnalyticReport(
                axis_type=axis_type,
                period_start=period_start,
                period_end=period_end,
                breakdown=breakdown,
                totals={"amount": round(total_amount, 2)},
                comparisons=comparisons,
            )

    def _get_budget(self, axis_id: int, period_start: date, period_end: date) -> Optional[float]:
        """Récupère le budget pour un axe et une période."""
        engine = get_engine()
        with engine.connect() as conn:
            # Budget mensuel ou annuel
            result = conn.execute(
                text("""
                    SELECT SUM(budget_amount) as total
                    FROM analytic_budgets
                    WHERE tenant_id = :tenant_id
                      AND axis_id = :axis_id
                      AND (
                          (period_month IS NULL AND period_year = :year)
                          OR (period_year = :year AND period_month BETWEEN :month_start AND :month_end)
                      )
                """),
                {
                    "tenant_id": self.tenant_id,
                    "axis_id": axis_id,
                    "year": period_start.year,
                    "month_start": period_start.month,
                    "month_end": period_end.month,
                }
            )
            row = result.fetchone()
            return float(row.total) if row and row.total else None

    def _get_period_amount(self, axis_id: int, period_start: date, period_end: date) -> float:
        """Récupère le montant total pour un axe et une période."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM analytic_assignments
                    WHERE tenant_id = :tenant_id
                      AND axis_id = :axis_id
                      AND assignment_date BETWEEN :start AND :end
                """),
                {
                    "tenant_id": self.tenant_id,
                    "axis_id": axis_id,
                    "start": period_start,
                    "end": period_end,
                }
            )
            row = result.fetchone()
            return float(row.total or 0)

    def set_budget(
        self,
        axis_id: int,
        year: int,
        amount: float,
        month: Optional[int] = None,
        notes: str = None
    ):
        """Définit le budget pour un axe."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO analytic_budgets
                    (tenant_id, axis_id, period_year, period_month, budget_amount, notes)
                    VALUES (:tenant_id, :axis_id, :year, :month, :amount, :notes)
                    ON CONFLICT (tenant_id, axis_id, period_year, period_month)
                    DO UPDATE SET budget_amount = EXCLUDED.budget_amount, notes = EXCLUDED.notes
                """),
                {
                    "tenant_id": self.tenant_id,
                    "axis_id": axis_id,
                    "year": year,
                    "month": month,
                    "amount": amount,
                    "notes": notes,
                }
            )

    def create_rule(
        self,
        name: str,
        conditions: Dict[str, Any],
        assignments: List[Dict[str, Any]],  # [{"axis_id": 1, "percentage": 60}, ...]
        priority: int = 0
    ) -> int:
        """Crée une règle d'affectation automatique."""
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO analytic_rules
                    (tenant_id, name, conditions, assignments, priority)
                    VALUES (:tenant_id, :name, :conditions, :assignments, :priority)
                    RETURNING id
                """),
                {
                    "tenant_id": self.tenant_id,
                    "name": name,
                    "conditions": json.dumps(conditions),
                    "assignments": json.dumps(assignments),
                    "priority": priority,
                }
            )
            row = result.fetchone()
            return row.id

    def get_cross_analysis(
        self,
        axis_type_1: AxisType,
        axis_type_2: AxisType,
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """Analyse croisée entre deux axes."""
        engine = get_engine()

        with engine.connect() as conn:
            # Récupérer les combinaisons
            result = conn.execute(
                text("""
                    SELECT
                        a1.name as axis1_name,
                        a2.name as axis2_name,
                        SUM(asg.amount) as total
                    FROM analytic_assignments asg
                    JOIN analytic_axes a1 ON asg.axis_id = a1.id AND a1.axis_type = :type1
                    JOIN analytic_assignments asg2 ON asg.source_type = asg2.source_type
                        AND asg.source_id = asg2.source_id
                        AND asg.id != asg2.id
                    JOIN analytic_axes a2 ON asg2.axis_id = a2.id AND a2.axis_type = :type2
                    WHERE asg.tenant_id = :tenant_id
                      AND asg.assignment_date BETWEEN :start AND :end
                    GROUP BY a1.name, a2.name
                    ORDER BY total DESC
                """),
                {
                    "tenant_id": self.tenant_id,
                    "type1": axis_type_1.value,
                    "type2": axis_type_2.value,
                    "start": period_start,
                    "end": period_end,
                }
            )

            matrix = {}
            for row in result:
                if row.axis1_name not in matrix:
                    matrix[row.axis1_name] = {}
                matrix[row.axis1_name][row.axis2_name] = round(float(row.total or 0), 2)

            return {
                "axis1_type": axis_type_1.value,
                "axis2_type": axis_type_2.value,
                "matrix": matrix,
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat(),
                },
            }

    def get_top_expenses_by_axis(
        self,
        axis_id: int,
        period_start: date,
        period_end: date,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Top des dépenses pour un axe donné."""
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        asg.source_type,
                        asg.source_id,
                        asg.amount,
                        asg.assignment_date,
                        asg.percentage
                    FROM analytic_assignments asg
                    WHERE asg.tenant_id = :tenant_id
                      AND asg.axis_id = :axis_id
                      AND asg.assignment_date BETWEEN :start AND :end
                    ORDER BY asg.amount DESC
                    LIMIT :limit
                """),
                {
                    "tenant_id": self.tenant_id,
                    "axis_id": axis_id,
                    "start": period_start,
                    "end": period_end,
                    "limit": limit,
                }
            )

            return [
                {
                    "source_type": row.source_type,
                    "source_id": row.source_id,
                    "amount": float(row.amount),
                    "date": row.assignment_date.isoformat() if row.assignment_date else None,
                    "percentage": float(row.percentage),
                }
                for row in result
            ]


# Bootstrap des axes par défaut
def bootstrap_default_axes(tenant_id: int):
    """Initialise les axes par défaut."""
    engine = AnalyticAccountingEngine(tenant_id)

    # Activités
    engine.create_axis(AxisType.ACTIVITY, "EPICERIE", "Épicerie")
    engine.create_axis(AxisType.ACTIVITY, "RESTAURANT", "Restaurant")

    # Centres de coût
    engine.create_axis(AxisType.COST_CENTER, "CUISINE", "Cuisine")
    engine.create_axis(AxisType.COST_CENTER, "SALLE", "Salle / Service")
    engine.create_axis(AxisType.COST_CENTER, "STOCKAGE", "Stockage / Réserve")
    engine.create_axis(AxisType.COST_CENTER, "LIVRAISON", "Livraison")
    engine.create_axis(AxisType.COST_CENTER, "ADMIN", "Administration")

    # Rayons
    engine.create_axis(AxisType.DEPARTMENT, "FRAIS", "Produits frais")
    engine.create_axis(AxisType.DEPARTMENT, "SEC", "Épicerie sèche")
    engine.create_axis(AxisType.DEPARTMENT, "BOISSONS", "Boissons")
    engine.create_axis(AxisType.DEPARTMENT, "SURGELES", "Surgelés")
    engine.create_axis(AxisType.DEPARTMENT, "VIANDES", "Viandes / Poissons")
