from fastapi import FastAPI

from backend.api import (
    admin,
    analytics,
    anomaly_detection,
    audit,
    audit_trail,
    auth,
    bank_reconciliation,
    capital,
    catalog,
    cockpit,
    dashboard,
    data_quality,
    eurociel,
    finance,
    forecasting,
    inventory_intelligence,
    invoices,
    maintenance,
    margins,
    newcms,
    prices,
    reports,
    restaurant,
    rules_engine,
    stock,
    supplier_scoring,
    suppliers,
    supply,
)


def include_routes(app: FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(catalog.router)
    app.include_router(stock.router)
    app.include_router(prices.router)
    app.include_router(invoices.router)
    app.include_router(eurociel.router)
    app.include_router(maintenance.router)
    app.include_router(forecasting.router)
    app.include_router(inventory_intelligence.router)
    app.include_router(anomaly_detection.router)
    app.include_router(margins.router)
    app.include_router(supplier_scoring.router)
    app.include_router(suppliers.router)
    app.include_router(analytics.router)
    app.include_router(dashboard.router)
    app.include_router(cockpit.router)
    app.include_router(restaurant.router)
    app.include_router(finance.router)
    app.include_router(bank_reconciliation.router)
    app.include_router(audit.router)
    app.include_router(audit_trail.router)
    app.include_router(capital.router)
    app.include_router(rules_engine.router)
    app.include_router(reports.router)
    app.include_router(admin.router)
    app.include_router(data_quality.router)
    app.include_router(supply.router)
    app.include_router(newcms.router)
