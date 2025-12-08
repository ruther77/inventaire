"""
Finance services package.

Ce package centralise toute la logique métier liée à la trésorerie :
- Comptes (accounts)
- Transactions (transactions)
- Relevés bancaires (bank_statements)
- Catégories (categories)
- Règles de catégorisation (rules)
- Factures et fournisseurs (invoices)
- Rapprochement (reconciliation)
- Statistiques et dashboard (stats, dashboard)
- Métriques (metrics)
- Imports (imports)
"""

from backend.services.finance.accounts import (
    create_account,
    list_accounts,
)

from backend.services.finance.transactions import (
    create_transaction,
    list_transactions,
    search_transactions,
    update_transaction,
    lock_transaction,
    suggest_autre_top,
    autocomplete_categories,
    batch_categorize,
)

from backend.services.finance.bank_statements import (
    search_bank_statements,
)

from backend.services.finance.categories import (
    list_categories,
)

from backend.services.finance.rules import (
    list_rules,
    create_rule,
    update_rule,
    delete_rule,
    record_import,
)

from backend.services.finance.invoices import (
    create_vendor,
    list_vendors,
    create_invoice,
    search_invoices,
    create_payment,
)

from backend.services.finance.reconciliation import (
    create_reconciliation,
    delete_reconciliation,
)

from backend.services.finance.stats import (
    categories_stats,
    accounts_overview,
    timeline_stats,
    category_breakdown,
    treasury_summary,
    refresh_materialized_views,
)

from backend.services.finance.dashboard import (
    dashboard_summary,
)

from backend.services.finance.metrics import (
    record_import_metrics,
    record_reco_run,
)

from backend.services.finance.imports import (
    list_imports,
)

from backend.services.finance.core import (
    run_reconciliation,
    list_matches,
    update_match_status,
    refresh_recurring,
    list_recurring,
    refresh_anomalies,
    list_anomalies,
)

__all__ = [
    # accounts
    "create_account",
    "list_accounts",
    # transactions
    "create_transaction",
    "list_transactions",
    "search_transactions",
    "update_transaction",
    "lock_transaction",
    "suggest_autre_top",
    "autocomplete_categories",
    "batch_categorize",
    # bank_statements
    "search_bank_statements",
    # categories
    "list_categories",
    # rules
    "list_rules",
    "create_rule",
    "update_rule",
    "delete_rule",
    "record_import",
    # invoices
    "create_vendor",
    "list_vendors",
    "create_invoice",
    "search_invoices",
    "create_payment",
    # reconciliation
    "create_reconciliation",
    "delete_reconciliation",
    # stats
    "categories_stats",
    "accounts_overview",
    "timeline_stats",
    "category_breakdown",
    "treasury_summary",
    "refresh_materialized_views",
    # dashboard
    "dashboard_summary",
    # metrics
    "record_import_metrics",
    "record_reco_run",
    # imports
    "list_imports",
    # core
    "run_reconciliation",
    "list_matches",
    "update_match_status",
    "refresh_recurring",
    "list_recurring",
    "refresh_anomalies",
    "list_anomalies",
]
