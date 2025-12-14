"""
API Router pour le Cockpit Unifie.

Consolide les donnees de tous les domaines metier en un seul appel:
- Stock & Inventaire
- Restaurant & Marges
- Tresorerie & Finance
- Intelligence & Anomalies

Evite les multiples appels frontend en fournissant une vue unifiee.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df, exec_sql

router = APIRouter(prefix="/cockpit", tags=["cockpit"])


# =============================================================================
# SCHEMAS
# =============================================================================

class KPIValue(BaseModel):
    """Valeur KPI avec metadata."""
    value: float
    label: str
    unit: Optional[str] = None
    trend: Optional[float] = None
    trend_direction: Optional[str] = None  # up, down, stable
    status: str = "info"  # success, warning, error, info
    description: Optional[str] = None


class AlertItem(BaseModel):
    """Alerte individuelle."""
    id: str
    severity: str  # critical, warning, info
    category: str  # stock, finance, margin, anomaly
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: datetime
    acknowledged: bool = False
    action_url: Optional[str] = None


class StockSummary(BaseModel):
    """Resume du stock."""
    total_products: int
    total_value_ht: float
    low_stock_count: int
    out_of_stock_count: int
    reorder_needed: int
    dead_stock_count: int
    dead_stock_value: float


class MarginSummary(BaseModel):
    """Resume des marges."""
    avg_margin_pct: float
    total_revenue: float
    total_cost: float
    gross_margin: float
    margin_alerts: int
    top_margin_product: Optional[str] = None
    worst_margin_product: Optional[str] = None


class TreasurySummary(BaseModel):
    """Resume tresorerie."""
    cash_in_7d: float
    cash_out_7d: float
    net_flow_7d: float
    unmatched_transactions: int
    match_rate: float
    pending_invoices: int
    pending_invoices_amount: float


class IntelligenceSummary(BaseModel):
    """Resume intelligence."""
    total_anomalies: int
    critical_anomalies: int
    forecast_trend: str  # up, down, stable
    forecast_confidence: float
    reorder_suggestions: int
    optimization_score: float


class CockpitOverview(BaseModel):
    """Vue consolidee complete du cockpit."""
    timestamp: datetime
    tenant_id: int
    tenant_name: str

    # KPIs principaux (6 max pour le dashboard)
    kpis: List[KPIValue]

    # Alertes actives
    alerts: List[AlertItem]
    alerts_count: int
    critical_count: int

    # Resumes par domaine
    stock: StockSummary
    margins: MarginSummary
    treasury: TreasurySummary
    intelligence: IntelligenceSummary

    # Sante globale
    health_score: float  # 0-100
    health_status: str  # healthy, warning, critical


class LiveKPIs(BaseModel):
    """KPIs temps reel pour refresh rapide."""
    timestamp: datetime
    kpis: List[KPIValue]
    alerts_count: int
    critical_count: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_stock_summary(tenant_id: int) -> StockSummary:
    """Calcule le resume stock."""
    sql = """
        SELECT
            COUNT(*) as total_products,
            COALESCE(SUM(stock_actuel * prix_achat), 0) as total_value_ht,
            COUNT(*) FILTER (WHERE stock_actuel > 0 AND stock_actuel < seuil_alerte) as low_stock,
            COUNT(*) FILTER (WHERE stock_actuel <= 0) as out_of_stock
        FROM produits
        WHERE tenant_id = :tenant_id AND actif = true
    """
    df = query_df(sql, params={"tenant_id": tenant_id})

    if df.empty:
        return StockSummary(
            total_products=0, total_value_ht=0, low_stock_count=0,
            out_of_stock_count=0, reorder_needed=0, dead_stock_count=0, dead_stock_value=0
        )

    row = df.iloc[0]

    # Dead stock (pas de mouvement depuis 90 jours)
    dead_sql = """
        SELECT COUNT(*) as count, COALESCE(SUM(p.stock_actuel * p.prix_achat), 0) as value
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
          AND p.stock_actuel > 0
          AND NOT EXISTS (
              SELECT 1 FROM mouvements_stock m
              WHERE m.produit_id = p.id
                AND m.date_mvt > CURRENT_DATE - INTERVAL '90 days'
          )
    """
    dead_df = query_df(dead_sql, params={"tenant_id": tenant_id})
    dead_count = int(dead_df.iloc[0]['count'] or 0) if not dead_df.empty else 0
    dead_value = float(dead_df.iloc[0]['value'] or 0) if not dead_df.empty else 0

    return StockSummary(
        total_products=int(row['total_products'] or 0),
        total_value_ht=float(row['total_value_ht'] or 0),
        low_stock_count=int(row['low_stock'] or 0),
        out_of_stock_count=int(row['out_of_stock'] or 0),
        reorder_needed=int(row['low_stock'] or 0) + int(row['out_of_stock'] or 0),
        dead_stock_count=dead_count,
        dead_stock_value=dead_value
    )


def _get_margin_summary(tenant_id: int, days: int = 30) -> MarginSummary:
    """Calcule le resume des marges basé sur les produits."""
    # Calcul des marges basé sur le catalogue produits
    try:
        margin_sql = """
            SELECT
                COALESCE(AVG(CASE WHEN prix_vente > 0 AND prix_achat > 0
                    THEN ((prix_vente - prix_achat) / prix_vente * 100) END), 0) as avg_margin,
                COALESCE(SUM(stock_actuel * prix_vente), 0) as total_revenue_potential,
                COALESCE(SUM(stock_actuel * prix_achat), 0) as total_cost
            FROM produits
            WHERE tenant_id = :tenant_id
              AND actif = true
              AND prix_vente > 0
        """
        df = query_df(margin_sql, params={"tenant_id": tenant_id})

        avg_margin_pct = float(df.iloc[0]['avg_margin'] or 0) if not df.empty else 0
        total_revenue = float(df.iloc[0]['total_revenue_potential'] or 0) if not df.empty else 0
        total_cost = float(df.iloc[0]['total_cost'] or 0) if not df.empty else 0
    except Exception:
        avg_margin_pct = 0
        total_revenue = 0
        total_cost = 0

    gross_margin = total_revenue - total_cost

    # Alertes marge (produits avec marge < 20%)
    try:
        alerts_sql = """
            SELECT COUNT(*) as count
            FROM produits
            WHERE tenant_id = :tenant_id
              AND actif = true
              AND prix_vente > 0
              AND prix_achat > 0
              AND ((prix_vente - prix_achat) / prix_vente * 100) < 20
        """
        alerts_df = query_df(alerts_sql, params={"tenant_id": tenant_id})
        margin_alerts = int(alerts_df.iloc[0]['count'] or 0) if not alerts_df.empty else 0
    except Exception:
        margin_alerts = 0

    return MarginSummary(
        avg_margin_pct=round(avg_margin_pct, 1),
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_margin=gross_margin,
        margin_alerts=margin_alerts,
        top_margin_product=None,
        worst_margin_product=None
    )


def _get_treasury_summary(tenant_id: int) -> TreasurySummary:
    """Calcule le resume tresorerie."""
    cash_in = 0.0
    cash_out = 0.0
    total_tx = 0
    matched_tx = 0
    pending_count = 0
    pending_amount = 0.0

    # Flux 7 derniers jours - utilise finance_transactions
    try:
        cash_sql = """
            SELECT
                COALESCE(SUM(CASE WHEN montant > 0 THEN montant ELSE 0 END), 0) as cash_in,
                COALESCE(SUM(CASE WHEN montant < 0 THEN ABS(montant) ELSE 0 END), 0) as cash_out
            FROM finance_transactions
            WHERE tenant_id = :tenant_id
              AND date_transaction >= CURRENT_DATE - INTERVAL '7 days'
        """
        cash_df = query_df(cash_sql, params={"tenant_id": tenant_id})
        cash_in = float(cash_df.iloc[0]['cash_in'] or 0) if not cash_df.empty else 0
        cash_out = float(cash_df.iloc[0]['cash_out'] or 0) if not cash_df.empty else 0
    except Exception:
        pass

    # Transactions non rapprochees
    try:
        unmatched_sql = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE rapproche = true) as matched
            FROM finance_transactions
            WHERE tenant_id = :tenant_id
              AND date_transaction >= CURRENT_DATE - INTERVAL '60 days'
              AND montant < 0
        """
        unmatched_df = query_df(unmatched_sql, params={"tenant_id": tenant_id})
        total_tx = int(unmatched_df.iloc[0]['total'] or 0) if not unmatched_df.empty else 0
        matched_tx = int(unmatched_df.iloc[0]['matched'] or 0) if not unmatched_df.empty else 0
    except Exception:
        pass

    unmatched = total_tx - matched_tx
    match_rate = (matched_tx / total_tx * 100) if total_tx > 0 else 100

    # Factures en attente - utilise processed_invoices
    try:
        pending_sql = """
            SELECT COUNT(*) as count, COALESCE(SUM(total_ttc), 0) as amount
            FROM processed_invoices
            WHERE tenant_id = :tenant_id
              AND created_at >= CURRENT_DATE - INTERVAL '90 days'
        """
        pending_df = query_df(pending_sql, params={"tenant_id": tenant_id})
        pending_count = int(pending_df.iloc[0]['count'] or 0) if not pending_df.empty else 0
        pending_amount = float(pending_df.iloc[0]['amount'] or 0) if not pending_df.empty else 0
    except Exception:
        pass

    return TreasurySummary(
        cash_in_7d=cash_in,
        cash_out_7d=cash_out,
        net_flow_7d=cash_in - cash_out,
        unmatched_transactions=unmatched,
        match_rate=round(match_rate, 1),
        pending_invoices=pending_count,
        pending_invoices_amount=pending_amount
    )


def _get_intelligence_summary(tenant_id: int) -> IntelligenceSummary:
    """Calcule le resume intelligence."""
    # Anomalies detectees
    anomaly_sql = """
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical
        FROM detected_anomalies
        WHERE tenant_id = :tenant_id
          AND resolved = false
          AND detected_at >= CURRENT_DATE - INTERVAL '30 days'
    """
    try:
        anomaly_df = query_df(anomaly_sql, params={"tenant_id": tenant_id})
        total_anomalies = int(anomaly_df.iloc[0]['total'] or 0) if not anomaly_df.empty else 0
        critical_anomalies = int(anomaly_df.iloc[0]['critical'] or 0) if not anomaly_df.empty else 0
    except Exception:
        total_anomalies = 0
        critical_anomalies = 0

    # Tendance ventes - utilise finance_transactions
    recent = 0.0
    previous = 0.0
    try:
        trend_sql = """
            SELECT
                COALESCE(SUM(CASE WHEN date_transaction >= CURRENT_DATE - INTERVAL '7 days' THEN ABS(montant) ELSE 0 END), 0) as recent,
                COALESCE(SUM(CASE WHEN date_transaction >= CURRENT_DATE - INTERVAL '14 days'
                                  AND date_transaction < CURRENT_DATE - INTERVAL '7 days' THEN ABS(montant) ELSE 0 END), 0) as previous
            FROM finance_transactions
            WHERE tenant_id = :tenant_id
              AND date_transaction >= CURRENT_DATE - INTERVAL '14 days'
        """
        trend_df = query_df(trend_sql, params={"tenant_id": tenant_id})
        recent = float(trend_df.iloc[0]['recent'] or 0) if not trend_df.empty else 0
        previous = float(trend_df.iloc[0]['previous'] or 0) if not trend_df.empty else 0
    except Exception:
        pass

    if previous > 0:
        trend_pct = ((recent - previous) / previous) * 100
        trend = "up" if trend_pct > 5 else "down" if trend_pct < -5 else "stable"
    else:
        trend = "stable"
        trend_pct = 0

    # Score optimisation (base sur plusieurs facteurs)
    stock_summary = _get_stock_summary(tenant_id)
    dead_ratio = stock_summary.dead_stock_count / max(stock_summary.total_products, 1)
    reorder_ratio = stock_summary.reorder_needed / max(stock_summary.total_products, 1)

    optimization_score = 100 - (dead_ratio * 30) - (reorder_ratio * 20) - (total_anomalies * 2)
    optimization_score = max(0, min(100, optimization_score))

    return IntelligenceSummary(
        total_anomalies=total_anomalies,
        critical_anomalies=critical_anomalies,
        forecast_trend=trend,
        forecast_confidence=0.75,
        reorder_suggestions=stock_summary.reorder_needed,
        optimization_score=round(optimization_score, 1)
    )


def _build_alerts(tenant_id: int, stock: StockSummary, margins: MarginSummary,
                  treasury: TreasurySummary, intelligence: IntelligenceSummary) -> List[AlertItem]:
    """Construit la liste des alertes basee sur les resumes."""
    alerts = []
    now = datetime.now()

    # Alertes stock
    if stock.out_of_stock_count > 0:
        alerts.append(AlertItem(
            id=f"stock-outage-{now.timestamp()}",
            severity="critical",
            category="stock",
            title="Ruptures de stock",
            message=f"{stock.out_of_stock_count} produits en rupture de stock",
            created_at=now,
            action_url="/inventory?status=critical"
        ))

    if stock.low_stock_count > 5:
        alerts.append(AlertItem(
            id=f"stock-low-{now.timestamp()}",
            severity="warning",
            category="stock",
            title="Stock bas",
            message=f"{stock.low_stock_count} produits en stock bas",
            created_at=now,
            action_url="/inventory?status=warning"
        ))

    if stock.dead_stock_value > 1000:
        alerts.append(AlertItem(
            id=f"stock-dead-{now.timestamp()}",
            severity="warning",
            category="stock",
            title="Stock mort",
            message=f"{stock.dead_stock_count} produits sans mouvement ({stock.dead_stock_value:.0f}€ immobilises)",
            created_at=now,
            action_url="/intelligence/inventory"
        ))

    # Alertes marges
    if margins.margin_alerts > 0:
        alerts.append(AlertItem(
            id=f"margin-low-{now.timestamp()}",
            severity="warning",
            category="margin",
            title="Marges faibles",
            message=f"{margins.margin_alerts} produits avec marge < 20%",
            created_at=now,
            action_url="/intelligence/margins"
        ))

    # Alertes tresorerie
    if treasury.unmatched_transactions > 20:
        alerts.append(AlertItem(
            id=f"treasury-unmatched-{now.timestamp()}",
            severity="warning",
            category="finance",
            title="Rapprochement en retard",
            message=f"{treasury.unmatched_transactions} transactions non rapprochees",
            created_at=now,
            action_url="/tresorerie/anomalies"
        ))

    if treasury.net_flow_7d < -5000:
        alerts.append(AlertItem(
            id=f"treasury-negative-{now.timestamp()}",
            severity="warning",
            category="finance",
            title="Flux negatif",
            message=f"Flux net negatif de {abs(treasury.net_flow_7d):.0f}€ sur 7 jours",
            created_at=now,
            action_url="/tresorerie"
        ))

    # Alertes intelligence
    if intelligence.critical_anomalies > 0:
        alerts.append(AlertItem(
            id=f"intel-critical-{now.timestamp()}",
            severity="critical",
            category="anomaly",
            title="Anomalies critiques",
            message=f"{intelligence.critical_anomalies} anomalies critiques detectees",
            created_at=now,
            action_url="/intelligence/anomalies"
        ))

    # Trier par severite
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda x: severity_order.get(x.severity, 3))

    return alerts


def _calculate_health_score(stock: StockSummary, margins: MarginSummary,
                            treasury: TreasurySummary, intelligence: IntelligenceSummary) -> tuple:
    """Calcule le score de sante global."""
    score = 100.0

    # Stock (30 points max)
    if stock.total_products > 0:
        outage_ratio = stock.out_of_stock_count / stock.total_products
        score -= outage_ratio * 30

    # Marges (20 points max)
    if margins.avg_margin_pct < 20:
        score -= 20
    elif margins.avg_margin_pct < 30:
        score -= 10

    # Tresorerie (25 points max)
    if treasury.match_rate < 70:
        score -= 15
    elif treasury.match_rate < 85:
        score -= 5

    if treasury.net_flow_7d < 0:
        score -= 10

    # Intelligence (25 points max)
    score -= intelligence.critical_anomalies * 5
    score -= min(intelligence.total_anomalies, 10) * 1

    score = max(0, min(100, score))

    if score >= 80:
        status = "healthy"
    elif score >= 50:
        status = "warning"
    else:
        status = "critical"

    return round(score, 1), status


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/overview", response_model=CockpitOverview)
def get_cockpit_overview(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne la vue consolidee complete du cockpit.

    Un seul appel pour obtenir toutes les donnees necessaires au dashboard:
    - KPIs principaux
    - Alertes actives
    - Resumes par domaine (stock, marges, tresorerie, intelligence)
    - Score de sante global
    """
    # Calculer les resumes
    stock = _get_stock_summary(tenant.id)
    margins = _get_margin_summary(tenant.id)
    treasury = _get_treasury_summary(tenant.id)
    intelligence = _get_intelligence_summary(tenant.id)

    # Construire les alertes
    alerts = _build_alerts(tenant.id, stock, margins, treasury, intelligence)
    critical_count = len([a for a in alerts if a.severity == "critical"])

    # Calculer le score de sante
    health_score, health_status = _calculate_health_score(stock, margins, treasury, intelligence)

    # Construire les KPIs principaux
    kpis = [
        KPIValue(
            value=stock.total_value_ht,
            label="Valeur Stock",
            unit="€",
            status="info",
            description=f"{stock.total_products} references"
        ),
        KPIValue(
            value=stock.out_of_stock_count + stock.low_stock_count,
            label="Alertes Stock",
            status="error" if stock.out_of_stock_count > 0 else "warning" if stock.low_stock_count > 5 else "success",
            description=f"{stock.out_of_stock_count} ruptures, {stock.low_stock_count} bas"
        ),
        KPIValue(
            value=margins.avg_margin_pct,
            label="Marge Moyenne",
            unit="%",
            status="success" if margins.avg_margin_pct >= 30 else "warning" if margins.avg_margin_pct >= 20 else "error",
            description=f"{margins.margin_alerts} alertes"
        ),
        KPIValue(
            value=treasury.net_flow_7d,
            label="Flux Net 7j",
            unit="€",
            status="success" if treasury.net_flow_7d >= 0 else "error",
            description=f"Entrees: {treasury.cash_in_7d:.0f}€"
        ),
        KPIValue(
            value=intelligence.total_anomalies,
            label="Anomalies",
            status="error" if intelligence.critical_anomalies > 0 else "warning" if intelligence.total_anomalies > 5 else "success",
            description=f"{intelligence.critical_anomalies} critiques"
        ),
        KPIValue(
            value=treasury.match_rate,
            label="Rapprochement",
            unit="%",
            status="success" if treasury.match_rate >= 85 else "warning" if treasury.match_rate >= 70 else "error",
            description=f"{treasury.unmatched_transactions} en attente"
        ),
    ]

    return CockpitOverview(
        timestamp=datetime.now(),
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        kpis=kpis,
        alerts=alerts,
        alerts_count=len(alerts),
        critical_count=critical_count,
        stock=stock,
        margins=margins,
        treasury=treasury,
        intelligence=intelligence,
        health_score=health_score,
        health_status=health_status
    )


@router.get("/kpis/live", response_model=LiveKPIs)
def get_live_kpis(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les KPIs en temps reel pour refresh rapide.

    Endpoint leger pour polling frequent (toutes les 30s par exemple).
    """
    stock = _get_stock_summary(tenant.id)
    margins = _get_margin_summary(tenant.id)
    treasury = _get_treasury_summary(tenant.id)
    intelligence = _get_intelligence_summary(tenant.id)

    alerts = _build_alerts(tenant.id, stock, margins, treasury, intelligence)

    kpis = [
        KPIValue(value=stock.total_value_ht, label="Valeur Stock", unit="€", status="info"),
        KPIValue(
            value=stock.out_of_stock_count + stock.low_stock_count,
            label="Alertes Stock",
            status="error" if stock.out_of_stock_count > 0 else "warning" if stock.low_stock_count > 5 else "success"
        ),
        KPIValue(
            value=margins.avg_margin_pct,
            label="Marge",
            unit="%",
            status="success" if margins.avg_margin_pct >= 30 else "warning"
        ),
        KPIValue(
            value=treasury.net_flow_7d,
            label="Flux 7j",
            unit="€",
            status="success" if treasury.net_flow_7d >= 0 else "error"
        ),
    ]

    return LiveKPIs(
        timestamp=datetime.now(),
        kpis=kpis,
        alerts_count=len(alerts),
        critical_count=len([a for a in alerts if a.severity == "critical"])
    )


@router.get("/alerts", response_model=List[AlertItem])
def get_alerts(
    severity: Optional[str] = Query(None, description="Filtrer par severite: critical, warning, info"),
    category: Optional[str] = Query(None, description="Filtrer par categorie: stock, finance, margin, anomaly"),
    limit: int = Query(20, ge=1, le=100),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les alertes actives.
    """
    stock = _get_stock_summary(tenant.id)
    margins = _get_margin_summary(tenant.id)
    treasury = _get_treasury_summary(tenant.id)
    intelligence = _get_intelligence_summary(tenant.id)

    alerts = _build_alerts(tenant.id, stock, margins, treasury, intelligence)

    # Filtrer
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    if category:
        alerts = [a for a in alerts if a.category == category]

    return alerts[:limit]


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Marque une alerte comme acquittee.
    """
    # En production, ceci serait persiste en DB
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "acknowledged_at": datetime.now().isoformat()
    }


@router.get("/health")
def get_health_status(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne le statut de sante global.
    """
    stock = _get_stock_summary(tenant.id)
    margins = _get_margin_summary(tenant.id)
    treasury = _get_treasury_summary(tenant.id)
    intelligence = _get_intelligence_summary(tenant.id)

    health_score, health_status = _calculate_health_score(stock, margins, treasury, intelligence)

    return {
        "score": health_score,
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "stock": "healthy" if stock.out_of_stock_count == 0 else "warning" if stock.out_of_stock_count < 5 else "critical",
            "margins": "healthy" if margins.avg_margin_pct >= 30 else "warning" if margins.avg_margin_pct >= 20 else "critical",
            "treasury": "healthy" if treasury.match_rate >= 85 else "warning" if treasury.match_rate >= 70 else "critical",
            "intelligence": "healthy" if intelligence.critical_anomalies == 0 else "critical"
        }
    }
