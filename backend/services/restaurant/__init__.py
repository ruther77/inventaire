"""
Module des services Restaurant - refactorisé depuis le monolithe restaurant.py

Le module est organisé en sous-modules :
- constants : règles de catégories, motifs regex, préréglages
- utils : fonctions utilitaires (_safe_float, _normalize_amount, etc.)
- expenses : gestion des dépenses (dépenses, centres de coût, fournisseurs)
- ingredients : gestion des ingrédients et des plats
- bank_statements : opérations et synthèses des relevés bancaires
- dashboard : vue d'ensemble et prévisions du tableau de bord
- mappings : correspondances et synchronisation Épicerie-Restaurant

Remarque : le parsing PDF a été migré vers le module core/bank_import/.
"""

# Ré-exporte toutes les fonctions publiques pour la rétrocompatibilité
from backend.services.restaurant.constants import (
    CATEGORY_RULES,
    CATEGORY_GROUP_PRESETS,
)
from backend.services.restaurant.utils import (
    _safe_float,
    _normalize_amount,
    _get_restaurant_entity_id,
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
    update_ingredient,
    delete_ingredient,
    update_ingredient_price,
    update_ingredient_ratio,
    link_ingredient_to_epicerie,
    unlink_ingredient_from_epicerie,
    list_plats,
    refresh_plat_costs,
    list_plat_alerts,
    create_plat,
    delete_plat,
    attach_ingredient_to_plat,
    remove_ingredient_from_plat,
    update_plat_ingredient,
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
    list_combined_price_history,
    list_epicerie_products,
    search_epicerie_products,
)
from backend.services.restaurant.price_sync import audit_epicerie_links
from backend.services.restaurant.overview import (
    get_restaurant_overview,
    list_plats_paginated,
    get_plat_detail,
    get_plat_cost_breakdown,
    list_ingredients_enhanced,
    get_ingredient_price_history_detail,
    analyze_food_cost,
    simulate_price_change,
    list_alerts_detailed,
)

__all__ = [
    # Constants
    "CATEGORY_RULES",
    "CATEGORY_GROUP_PRESETS",
    # Utils
    "_safe_float",
    "_normalize_amount",
    "_get_restaurant_entity_id",
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
    "update_ingredient",
    "delete_ingredient",
    "update_ingredient_price",
    "update_ingredient_ratio",
    "link_ingredient_to_epicerie",
    "unlink_ingredient_from_epicerie",
    "list_plats",
    "refresh_plat_costs",
    "list_plat_alerts",
    "create_plat",
    "delete_plat",
    "attach_ingredient_to_plat",
    "remove_ingredient_from_plat",
    "update_plat_ingredient",
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
    # Mappings (ingredient→epicerie link utilities)
    "list_sales_consumptions",
    "list_combined_price_history",
    "list_epicerie_products",
    "search_epicerie_products",
    "audit_epicerie_links",
    # Overview & Food Cost (UX 4.7)
    "get_restaurant_overview",
    "list_plats_paginated",
    "get_plat_detail",
    "get_plat_cost_breakdown",
    "list_ingredients_enhanced",
    "get_ingredient_price_history_detail",
    "analyze_food_cost",
    "simulate_price_change",
    "list_alerts_detailed",
]
