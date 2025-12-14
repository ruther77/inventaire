#!/usr/bin/env python
"""Test script to validate newcms finance endpoint compilation."""

import sys

try:
    # Test imports
    from backend.api.newcms import finance
    print("✓ Module backend.api.newcms.finance importé avec succès")

    # Vérifier que le router existe
    assert hasattr(finance, 'router'), "Router non trouvé dans le module finance"
    print("✓ Router finance existe")

    # Vérifier les endpoints
    routes = [route.path for route in finance.router.routes]
    expected_routes = [
        '/newcms/finance/overview',
        '/newcms/finance/transactions',
        '/newcms/finance/reconciliation/apply'
    ]

    print(f"\nRoutes disponibles:")
    for route in routes:
        print(f"  - {route}")

    for expected in expected_routes:
        if expected not in routes:
            print(f"✗ Route manquante: {expected}")
            sys.exit(1)
        print(f"✓ Route {expected} trouvée")

    # Vérifier les schemas
    from backend.api.newcms.finance import (
        FinanceOverviewResponse,
        TransactionListResponse,
        ApplyReconciliationRequest,
        ApplyReconciliationResponse,
        ReconciliationStats,
        CashFlowPeriod,
        ReconciliationSuggestion,
        RecentTransaction,
    )
    print("\n✓ Tous les schémas Pydantic sont importables")

    print("\n✅ Tous les tests réussis!")
    sys.exit(0)

except Exception as e:
    print(f"\n✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
