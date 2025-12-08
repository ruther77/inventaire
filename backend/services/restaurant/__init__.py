"""
Restaurant services module - refactored from monolithic restaurant.py

This module is organized into the following sub-modules:
- constants: Category rules, regex patterns, presets
- utils: Helper functions (_safe_float, _normalize_amount, etc.)
- pdf_parser: Bank statement PDF parsing (LCL, SumUp)
- expenses: Expense management (depenses, cost centers, fournisseurs)
- ingredients: Ingredient and plat management
- bank_statements: Bank statement operations and summaries
- dashboard: Dashboard overview and forecast
- mappings: Epicerie-Restaurant mappings and sync
"""

# Re-export all public functions for backwards compatibility
from backend.services.restaurant.constants import (
    CATEGORY_RULES,
    CATEGORY_GROUP_PRESETS,
)
from backend.services.restaurant.utils import (
    _safe_float,
    _normalize_amount,
    _get_restaurant_entity_id,
)
from backend.services.restaurant.pdf_parser import (
    parse_bank_statement_pdf,
)
from backend.services.restaurant.expenses import (
    list_depense_categories,
    create_depense_category,
    list_cost_centers,
    create_cost_center,
    list_fournisseurs,
    create_fournisseur,
    list_expenses,
    get_expense_detail,
    create_expense,
    expense_summary_by_month,
    expense_summary_by_cost_center,
    expense_summary_by_tva,
)
from backend.services.restaurant.ingredients import (
    list_ingredients,
    create_ingredient,
    update_ingredient_price,
    list_plats,
    refresh_plat_costs,
    list_plat_alerts,
    create_plat,
    attach_ingredient_to_plat,
    update_plat_price,
    list_ingredient_price_history,
    list_plat_price_history,
    list_recent_price_changes,
)
from backend.services.restaurant.bank_statements import (
    list_bank_statements,
    list_bank_accounts_overview,
    create_bank_statement,
    update_bank_statement,
    import_bank_statements_from_pdf,
    create_expense_from_bank_statement,
    get_bank_statement_summary,
    transfer_from_epicerie,
)
from backend.services.restaurant.dashboard import (
    build_dashboard_overview,
    build_forecast_overview,
)
from backend.services.restaurant.mappings import (
    list_sales_consumptions,
    sync_ingredients_from_mappings,
    list_combined_price_history,
    list_plat_epicerie_links,
    upsert_plat_epicerie_mapping,
    delete_plat_epicerie_mapping,
    list_epicerie_products,
)

__all__ = [
    # Constants
    "CATEGORY_RULES",
    "CATEGORY_GROUP_PRESETS",
    # Utils
    "_safe_float",
    "_normalize_amount",
    "_get_restaurant_entity_id",
    # PDF Parser
    "parse_bank_statement_pdf",
    # Expenses
    "list_depense_categories",
    "create_depense_category",
    "list_cost_centers",
    "create_cost_center",
    "list_fournisseurs",
    "create_fournisseur",
    "list_expenses",
    "get_expense_detail",
    "create_expense",
    "expense_summary_by_month",
    "expense_summary_by_cost_center",
    "expense_summary_by_tva",
    # Ingredients
    "list_ingredients",
    "create_ingredient",
    "update_ingredient_price",
    "list_plats",
    "refresh_plat_costs",
    "list_plat_alerts",
    "create_plat",
    "attach_ingredient_to_plat",
    "update_plat_price",
    "list_ingredient_price_history",
    "list_plat_price_history",
    "list_recent_price_changes",
    # Bank Statements
    "list_bank_statements",
    "list_bank_accounts_overview",
    "create_bank_statement",
    "update_bank_statement",
    "import_bank_statements_from_pdf",
    "create_expense_from_bank_statement",
    "get_bank_statement_summary",
    "transfer_from_epicerie",
    # Dashboard
    "build_dashboard_overview",
    "build_forecast_overview",
    # Mappings
    "list_sales_consumptions",
    "sync_ingredients_from_mappings",
    "list_combined_price_history",
    "list_plat_epicerie_links",
    "upsert_plat_epicerie_mapping",
    "delete_plat_epicerie_mapping",
    "list_epicerie_products",
]
