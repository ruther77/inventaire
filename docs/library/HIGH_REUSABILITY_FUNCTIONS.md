# Fonctions Hautement Réutilisables

Liste des fonctions avec une haute réutilisabilité (pures, bien typées, peu de dépendances)

---

**Total: 504 fonctions**

## API (129)

### `__init__`

**Fichier**: `backend/api/auth.py:39`

```python
def __init__( self, grant_type: str | None = Form(default=None, pattern="password"),
```

**Paramètres**:
- `self`
- `grant_type`: `str | None`
- `username`: `str`
- `password`: `str`
- `scope`: `str`
- `client_id`: `str | None`
- `client_secret`: `str | None`
- `tenant`: `str`

**Retour**: `None`

---

### `accounts_overview`

**Fichier**: `backend/api/finance.py:85`

```python
def accounts_overview( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `acknowledge_alert`

**Fichier**: `backend/api/cockpit.py:670`

```python
def acknowledge_alert( alert_id: str,
```

Marque une alerte comme acquittee.

**Paramètres**:
- `alert_id`: `str`
- `tenant`: `Tenant`

---

### `adjust_stock`

**Fichier**: `backend/api/restaurant.py:375`

```python
def adjust_stock( ingredient_id: int = Body(...),
```

Ajuste le stock à une nouvelle quantité (inventaire).

**Paramètres**:
- `ingredient_id`: `int`
- `new_quantity`: `float`
- `commentaire`: `Optional[str]`
- `tenant`: `Tenant`

---

### `admin_overview`

**Fichier**: `backend/api/admin.py:29`

```python
def admin_overview(tenant: Tenant = Depends(get_current_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `attach_ingredient`

**Fichier**: `backend/api/restaurant.py:426`

```python
def attach_ingredient(plat_id: int, payload: RestaurantPlatIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `plat_id`: `int`
- `payload`: `RestaurantPlatIngredientCreate`
- `tenant`: `Tenant`

---

### `audit_ingredient_epicerie_links`

**Fichier**: `backend/api/restaurant.py:229`

```python
def audit_ingredient_epicerie_links( dry_run: bool = Query(True, description="Ne pas modifier; uniquement lister les liens incohérents."),
```

Audit des liens incohérents ingrédients ↔ épicerie (ex: ail lié à un whisky).

**Paramètres**:
- `dry_run`: `bool`
- `tenant`: `Tenant`

---

### `autocomplete_categories`

**Fichier**: `backend/api/finance.py:348`

```python
def autocomplete_categories( q: str = Query(default="", description="Search query for category suggestions"),
```

**Paramètres**:
- `q`: `str`
- `entity_id`: `int | None`
- `limit`: `int`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `batch_categorize_transactions`

**Fichier**: `backend/api/finance.py:360`

```python
def batch_categorize_transactions( payload: FinanceBatchCategorizeRequest,
```

**Paramètres**:
- `payload`: `FinanceBatchCategorizeRequest`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `cancel_invoice_import`

**Fichier**: `backend/api/newcms/operations.py:771`

```python
async def cancel_invoice_import( job_id: str,
```

**Paramètres**:
- `job_id`: `str`
- `tenant`: `Tenant`

**Retour**: `InvoiceImportActionResponse`

---

### `categories_stats`

**Fichier**: `backend/api/finance.py:433`

```python
def categories_stats( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `categorize_transaction`

**Fichier**: `backend/api/newcms/finance.py:897`

```python
def categorize_transaction( transaction_id: int,
```

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `CategorizeRequest`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `change_user_role`

**Fichier**: `backend/api/admin.py:41`

```python
def change_user_role(user_id: int, payload: UpdateRolePayload):
```

**Paramètres**:
- `user_id`: `int`
- `payload`: `UpdateRolePayload`

---

### `client`

**Fichier**: `backend/tests/conftest.py:18`

```python
def client() -> TestClient:
```

Crée une instance TestClient pour l'app FastAPI.

**Retour**: `TestClient`

---

### `create_account`

**Fichier**: `backend/api/finance.py:65`

```python
def create_account( payload: FinanceAccountCreate,
```

**Paramètres**:
- `payload`: `FinanceAccountCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_backup`

**Fichier**: `backend/api/admin.py:59`

```python
def create_backup(payload: BackupCreationPayload | None = None):
```

**Paramètres**:
- `payload`: `BackupCreationPayload | None`

---

### `create_category`

**Fichier**: `backend/api/finance.py:305`

```python
def create_category( payload: FinanceCategoryCreate,
```

**Paramètres**:
- `payload`: `FinanceCategoryCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_category`

**Fichier**: `backend/api/restaurant.py:70`

```python
def create_category(payload: RestaurantCategoryCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `payload`: `RestaurantCategoryCreate`
- `tenant`: `Tenant`

---

### `create_cost_center`

**Fichier**: `backend/api/finance.py:333`

```python
def create_cost_center( payload: FinanceCostCenterCreate,
```

**Paramètres**:
- `payload`: `FinanceCostCenterCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_cost_center`

**Fichier**: `backend/api/restaurant.py:80`

```python
def create_cost_center(payload: RestaurantCostCenterCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `payload`: `RestaurantCostCenterCreate`
- `tenant`: `Tenant`

---

### `create_finance_rule`

**Fichier**: `backend/api/newcms/finance.py:1106`

```python
def create_finance_rule( payload: FinanceRuleCreate,
```

**Paramètres**:
- `payload`: `FinanceRuleCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_invoice`

**Fichier**: `backend/api/finance.py:237`

```python
def create_invoice( payload: FinanceInvoiceCreate,
```

**Paramètres**:
- `payload`: `FinanceInvoiceCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_payment`

**Fichier**: `backend/api/finance.py:273`

```python
def create_payment( payload: FinancePaymentCreate,
```

**Paramètres**:
- `payload`: `FinancePaymentCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_reconciliation`

**Fichier**: `backend/api/finance.py:502`

```python
def create_reconciliation( payload: FinanceReconciliationCreate,
```

**Paramètres**:
- `payload`: `FinanceReconciliationCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_rule`

**Fichier**: `backend/api/finance.py:383`

```python
def create_rule(payload: FinanceRuleCreate, tenant: Tenant = Depends(get_current_tenant_or_default)) -> FinanceRule:
```

**Paramètres**:
- `payload`: `FinanceRuleCreate`
- `tenant`: `Tenant`

**Retour**: `FinanceRule`

---

### `create_supplier_order`

**Fichier**: `backend/api/newcms/operations.py:826`

```python
async def create_supplier_order( payload: CreateOrderRequest,
```

**Paramètres**:
- `payload`: `CreateOrderRequest`
- `tenant`: `Tenant`

**Retour**: `CreateOrderResponse`

---

### `create_transaction`

**Fichier**: `backend/api/finance.py:132`

```python
def create_transaction( payload: FinanceTransactionCreate,
```

**Paramètres**:
- `payload`: `FinanceTransactionCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `create_vendor`

**Fichier**: `backend/api/finance.py:217`

```python
def create_vendor( payload: FinanceVendorCreate,
```

**Paramètres**:
- `payload`: `FinanceVendorCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `deduplicate_finance`

**Fichier**: `backend/api/finance.py:413`

```python
def deduplicate_finance(tenant: Tenant = Depends(get_current_tenant_or_default)) -> dict:
```

Supprime les doublons (date+montant) sur transactions et lignes de relevés.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `delete_account`

**Fichier**: `backend/api/finance.py:117`

```python
def delete_account( account_id: int,
```

**Paramètres**:
- `account_id`: `int`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `delete_backup`

**Fichier**: `backend/api/admin.py:77`

```python
def delete_backup(filename: str):
```

**Paramètres**:
- `filename`: `str`

---

### `delete_finance_rule`

**Fichier**: `backend/api/newcms/finance.py:1145`

```python
def delete_finance_rule( rule_id: str,
```

**Paramètres**:
- `rule_id`: `str`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `delete_product`

**Fichier**: `backend/api/catalog.py:76`

```python
def delete_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
```

**Paramètres**:
- `product_id`: `int`
- `tenant`: `Tenant`

---

### `delete_reconciliation`

**Fichier**: `backend/api/finance.py:518`

```python
def delete_reconciliation( reconciliation_id: int,
```

**Paramètres**:
- `reconciliation_id`: `int`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `delete_rule`

**Fichier**: `backend/api/finance.py:400`

```python
def delete_rule(rule_id: int, tenant: Tenant = Depends(get_current_tenant_or_default)) -> dict:
```

**Paramètres**:
- `rule_id`: `int`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `delete_supplier_alias`

**Fichier**: `backend/api/bank_reconciliation.py:637`

```python
def delete_supplier_alias( alias_id: int,
```

Supprime un alias fournisseur.

**Paramètres**:
- `alias_id`: `int`
- `tenant`: `Tenant`

---

### `download_backup`

**Fichier**: `backend/api/maintenance.py:23`

```python
def download_backup(filename: str):
```

**Paramètres**:
- `filename`: `str`

---

### `download_invoice_file`

**Fichier**: `backend/api/invoices.py:801`

```python
def download_invoice_file(invoice_id: str, tenant: Tenant = Depends(get_current_tenant)):
```

**Paramètres**:
- `invoice_id`: `str`
- `tenant`: `Tenant`

---

### `email_webhook_import`

**Fichier**: `backend/api/newcms/operations.py:787`

```python
async def email_webhook_import( payload: EmailWebhookPayload,
```

**Paramètres**:
- `payload`: `EmailWebhookPayload`
- `tenant`: `Tenant`

**Retour**: `dict[str, Any]`

---

### `eurociel_status`

**Fichier**: `backend/api/eurociel.py:118`

```python
def eurociel_status(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, Any]:
```

Retourne le statut des imports Eurociel pour ce tenant.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict[str, Any]`

---

### `expense_summary`

**Fichier**: `backend/api/restaurant.py:101`

```python
def expense_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `fill_prices_from_history`

**Fichier**: `backend/api/prices.py:72`

```python
def fill_prices_from_history(tenant: Tenant = Depends(get_current_tenant)) -> dict:
```

Tente de remplir prix_achat/prix_vente manquants depuis l'historique produits_price_history.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `finance_dashboard_summary`

**Fichier**: `backend/api/finance.py:441`

```python
def finance_dashboard_summary( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `get_account`

**Fichier**: `backend/api/finance.py:94`

```python
def get_account( account_id: int,
```

**Paramètres**:
- `account_id`: `int`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `get_actions`

**Fichier**: `backend/api/audit.py:44`

```python
def get_actions( include_closed: bool = Query(default=False),
```

**Paramètres**:
- `include_closed`: `bool`
- `tenant`: `Tenant`

---

### `get_capital_overview`

**Fichier**: `backend/api/capital.py:13`

```python
def get_capital_overview(tenant: Tenant = Depends(get_current_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_categorization_feedback_stats`

**Fichier**: `backend/api/finance.py:864`

```python
def get_categorization_feedback_stats( tenant: Tenant = Depends(get_current_tenant_or_default),
```

Retourne les statistiques globales sur le feedback de catégorisation.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `get_category_breakdown`

**Fichier**: `backend/api/finance.py:473`

```python
def get_category_breakdown( entity_id: int | None = Query(default=None),
```

Retourne la répartition par catégorie pour les pie/bar charts.

**Paramètres**:
- `entity_id`: `int | None`
- `months`: `int | None`
- `direction`: `str | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `get_dashboard_metrics`

**Fichier**: `backend/api/dashboard.py:15`

```python
def get_dashboard_metrics(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_food_cost_analysis`

**Fichier**: `backend/api/restaurant.py:692`

```python
def get_food_cost_analysis( period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
```

Analyse complète du food cost.

**Paramètres**:
- `period`: `str`
- `target_food_cost`: `float`
- `tenant`: `Tenant`

---

### `get_ingredient_price_history_detail`

**Fichier**: `backend/api/restaurant.py:680`

```python
def get_ingredient_price_history_detail( ingredient_id: int,
```

Historique détaillé des prix d'un ingrédient.

**Paramètres**:
- `ingredient_id`: `int`
- `tenant`: `Tenant`

---

### `get_invoice_history`

**Fichier**: `backend/api/invoices.py:779`

```python
def get_invoice_history( supplier: str | None = None,
```

**Paramètres**:
- `supplier`: `str | None`
- `invoice_id`: `str | None`
- `date_start`: `str | None`
- `date_end`: `str | None`
- `limit`: `int`
- `tenant`: `Tenant`

---

### `get_invoice_import_status`

**Fichier**: `backend/api/newcms/operations.py:648`

```python
async def get_invoice_import_status( job_id: str,
```

**Paramètres**:
- `job_id`: `str`
- `tenant`: `Tenant`

**Retour**: `InvoiceImportStatusResponse`

---

### `get_menus_overview`

**Fichier**: `backend/api/newcms/restaurant.py:292`

```python
def get_menus_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

Vue d'ensemble Menus & Coûts (food cost, marges, alertes ingrédients)

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_movement_timeseries`

**Fichier**: `backend/api/stock.py:20`

```python
def get_movement_timeseries( window_days: int = Query(30, ge=1, le=365),
```

**Paramètres**:
- `window_days`: `int`
- `product_id`: `int | None`
- `tenant`: `Tenant`

---

### `get_plat_cost_breakdown`

**Fichier**: `backend/api/restaurant.py:648`

```python
def get_plat_cost_breakdown( plat_id: int,
```

Décomposition détaillée du coût d'un plat.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant`

---

### `get_plat_detail`

**Fichier**: `backend/api/newcms/restaurant.py:298`

```python
def get_plat_detail( plat_id: int,
```

Détail d'un plat restaurant (fiche technique, prix, marge).

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant`

---

### `get_plat_detail`

**Fichier**: `backend/api/restaurant.py:630`

```python
def get_plat_detail( plat_id: int,
```

Détails complets d'un plat.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant`

---

### `get_price_sync_status`

**Fichier**: `backend/api/restaurant.py:218`

```python
def get_price_sync_status(tenant: Tenant = Depends(get_restaurant_tenant)):
```

Retourne le statut de synchronisation des prix pour tous les ingrédients.

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_recent_movements`

**Fichier**: `backend/api/stock.py:35`

```python
def get_recent_movements( limit: int = Query(50, ge=1, le=500),
```

**Paramètres**:
- `limit`: `int`
- `product_id`: `int | None`
- `tenant`: `Tenant`

---

### `get_reports_overview`

**Fichier**: `backend/api/reports.py:16`

```python
def get_reports_overview(tenant: Tenant = Depends(get_current_tenant)):
```

Retourne les analytics agrégées pour l'espace rapports.

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_resolution_log`

**Fichier**: `backend/api/audit.py:53`

```python
def get_resolution_log( limit: int = Query(default=100, ge=1, le=500),
```

**Paramètres**:
- `limit`: `int`
- `tenant`: `Tenant`

---

### `get_restaurant_menus_overview`

**Fichier**: `backend/api/restaurant.py:768`

```python
def get_restaurant_menus_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
```

Vue d'ensemble des menus : coûts matière, food cost, alertes ingrédients.

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_restaurant_overview`

**Fichier**: `backend/api/restaurant.py:575`

```python
def get_restaurant_overview( period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
```

Vue d'ensemble du restaurant.

**Paramètres**:
- `period`: `str`
- `tenant`: `Tenant`

---

### `get_stock_analytics`

**Fichier**: `backend/api/restaurant.py:316`

```python
def get_stock_analytics( days: int = Query(30, ge=1, le=365),
```

Statistiques de stock sur une période.

**Paramètres**:
- `days`: `int`
- `tenant`: `Tenant`

---

### `get_stock_summary`

**Fichier**: `backend/api/restaurant.py:310`

```python
def get_stock_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
```

Résumé du stock actuel par ingrédient.

**Paramètres**:
- `tenant`: `Tenant`

---

### `get_summary`

**Fichier**: `backend/api/analytics.py:164`

```python
def get_summary(tenant: Tenant = Depends(get_current_tenant)) -> AnalyticsSummary:
```

Retourne quelques KPI agrégés (stock et mouvements récents) pour le tenant courant.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `AnalyticsSummary`

---

### `get_suppliers_ranking_legacy`

**Fichier**: `backend/api/supplier_scoring.py:921`

```python
async def get_suppliers_ranking_legacy( tenant: Tenant = Depends(get_current_tenant_or_default),
```

[LEGACY] Retourne le classement de tous les fournisseurs.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `Dict[str, Any]`

---

### `get_timeline_stats`

**Fichier**: `backend/api/finance.py:457`

```python
def get_timeline_stats( entity_id: int | None = Query(default=None),
```

Retourne la chronologie agrégée des flux pour les graphiques.

**Paramètres**:
- `entity_id`: `int | None`
- `months`: `int | None`
- `granularity`: `str`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `get_treasury_summary`

**Fichier**: `backend/api/finance.py:489`

```python
def get_treasury_summary( entity_id: int | None = Query(default=None),
```

Retourne un résumé de trésorerie (totaux, solde, période).

**Paramètres**:
- `entity_id`: `int | None`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `ignore_transaction`

**Fichier**: `backend/api/newcms/finance.py:924`

```python
def ignore_transaction( transaction_id: int,
```

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `IgnoreRequest`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `ingredient_price_history`

**Fichier**: `backend/api/restaurant.py:158`

```python
def ingredient_price_history( ingredient_id: int,
```

**Paramètres**:
- `ingredient_id`: `int`
- `tenant`: `Tenant`

---

### `list_accounts`

**Fichier**: `backend/api/finance.py:76`

```python
def list_accounts( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `list_backups`

**Fichier**: `backend/api/maintenance.py:17`

```python
def list_backups(limit: int = Query(default=100, ge=1, le=1000)):
```

**Paramètres**:
- `limit`: `int`

---

### `list_categories`

**Fichier**: `backend/api/catalog.py:92`

```python
def list_categories(tenant: Tenant = Depends(get_current_tenant)):
```

Liste toutes les categories de produits.

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_categories`

**Fichier**: `backend/api/finance.py:296`

```python
def list_categories( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `list_categories`

**Fichier**: `backend/api/restaurant.py:65`

```python
def list_categories(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_consumptions`

**Fichier**: `backend/api/restaurant.py:495`

```python
def list_consumptions( period: str = Query("all", description="Période: 7d, 30d, 90d, 1y, all"),
```

Liste des consommations avec filtre de période optionnel.

**Paramètres**:
- `period`: `str`
- `tenant`: `Tenant`

---

### `list_cost_centers`

**Fichier**: `backend/api/finance.py:324`

```python
def list_cost_centers( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `list_cost_centers`

**Fichier**: `backend/api/restaurant.py:75`

```python
def list_cost_centers(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_finance_categories`

**Fichier**: `backend/api/newcms/finance.py:1336`

```python
def list_finance_categories( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `list[FinanceCategoryResponse]`

---

### `list_finance_rules`

**Fichier**: `backend/api/newcms/finance.py:1097`

```python
def list_finance_rules( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `list_flags`

**Fichier**: `backend/api/data_quality.py:130`

```python
def list_flags( table: str | None = Query(default=None, description="Table ciblée (ex: produits, finance_transactions)"),
```

**Paramètres**:
- `table`: `str | None`
- `limit`: `int`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `list_imports`

**Fichier**: `backend/api/finance.py:408`

```python
def list_imports(tenant: Tenant = Depends(get_current_tenant_or_default)) -> list[dict]:
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `list_ingredients_with_price_source`

**Fichier**: `backend/api/restaurant.py:239`

```python
def list_ingredients_with_price_source(tenant: Tenant = Depends(get_restaurant_tenant)):
```

Liste les ingrédients avec indication explicite de la source de prix.

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_matches`

**Fichier**: `backend/api/finance.py:666`

```python
def list_matches( status: str | None = Query(default="pending", description="Filtrer par statut."),
```

**Paramètres**:
- `status`: `str | None`
- `tenant`: `Tenant`

**Retour**: `list[FinanceMatch]`

---

### `list_price_history_comparison`

**Fichier**: `backend/api/restaurant.py:504`

```python
def list_price_history_comparison(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_recurring`

**Fichier**: `backend/api/finance.py:706`

```python
def list_recurring( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `list[FinanceRecurringExpense]`

---

### `list_restaurant_alerts`

**Fichier**: `backend/api/restaurant.py:536`

```python
def list_restaurant_alerts(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_rules`

**Fichier**: `backend/api/finance.py:374`

```python
def list_rules( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`
- `tenant`: `Tenant`

**Retour**: `list[FinanceRule]`

---

### `list_transactions`

**Fichier**: `backend/api/finance.py:143`

```python
def list_transactions( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `account_id`: `int | None`
- `status_filter`: `str | None`
- `date_from`: `str | None`
- `date_to`: `str | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `list_vendors`

**Fichier**: `backend/api/catalog.py:100`

```python
def list_vendors(tenant: Tenant = Depends(get_current_tenant)):
```

Liste tous les fournisseurs.

**Paramètres**:
- `tenant`: `Tenant`

---

### `list_vendors`

**Fichier**: `backend/api/finance.py:228`

```python
def list_vendors( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`
- `tenant`: `Tenant`

**Retour**: `list[dict]`

---

### `lock_transaction`

**Fichier**: `backend/api/finance.py:203`

```python
def lock_transaction( transaction_id: int,
```

**Paramètres**:
- `transaction_id`: `int`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `logout`

**Fichier**: `backend/api/auth.py:212`

```python
def logout(request: Request, response: Response) -> dict[str, str]:
```

Déconnecte et supprime les cookies d'authentification.

**Paramètres**:
- `request`: `Request`
- `response`: `Response`

**Retour**: `dict[str, str]`

---

### `manual_reconcile_transaction`

**Fichier**: `backend/api/newcms/finance.py:950`

```python
def manual_reconcile_transaction( transaction_id: int,
```

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `ManualReconcileRequest`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `mark_transactions_incomplete`

**Fichier**: `backend/api/finance.py:421`

```python
def mark_transactions_incomplete( transaction_ids: list[int],
```

Crée des transaction_lines par défaut et marque les transactions comme 'incomplètes' (data_quality_flags).

**Paramètres**:
- `transaction_ids`: `list[int]`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `plat_composition`

**Fichier**: `backend/api/restaurant.py:472`

```python
def plat_composition( plat_id: int,
```

Retourne la composition d'un plat avec coûts par ingrédient et pourcentage.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant`

---

### `plat_price_history`

**Fichier**: `backend/api/restaurant.py:456`

```python
def plat_price_history( plat_id: int,
```

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant`

---

### `price_history_overview`

**Fichier**: `backend/api/restaurant.py:563`

```python
def price_history_overview( limit: int = Query(12, ge=1, le=200),
```

**Paramètres**:
- `limit`: `int`
- `tenant`: `Tenant`

---

### `recompute_plat_costs`

**Fichier**: `backend/api/restaurant.py:464`

```python
def recompute_plat_costs( margin_threshold: float = Body(35.0, ge=1.0, description="Seuil de marge (%) pour générer des alertes."),
```

**Paramètres**:
- `margin_threshold`: `float`
- `tenant`: `Tenant`

---

### `record_consumption`

**Fichier**: `backend/api/restaurant.py:391`

```python
def record_consumption( ingredient_id: int = Body(...),
```

Enregistre une sortie de stock pour consommation.

**Paramètres**:
- `ingredient_id`: `int`
- `quantite`: `float`
- `commentaire`: `Optional[str]`
- `tenant`: `Tenant`

---

### `refresh_accounts`

**Fichier**: `backend/api/newcms/finance.py:1304`

```python
def refresh_accounts( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `refresh_anomalies`

**Fichier**: `backend/api/finance.py:714`

```python
def refresh_anomalies( payload: AnomalyRefreshRequest,
```

**Paramètres**:
- `payload`: `AnomalyRefreshRequest`
- `tenant`: `Tenant`

**Retour**: `AnomalyRefreshResponse`

---

### `refresh_recurring`

**Fichier**: `backend/api/finance.py:697`

```python
def refresh_recurring( payload: RecurringRefreshRequest,
```

**Paramètres**:
- `payload`: `RecurringRefreshRequest`
- `tenant`: `Tenant`

**Retour**: `RecurringRefreshResponse`

---

### `refresh_stats_cache`

**Fichier**: `backend/api/finance.py:449`

```python
def refresh_stats_cache( tenant: Tenant = Depends(get_current_tenant_or_default),
```

Rafraîchit les vues matérialisées des stats finance.

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `remove_ingredient`

**Fichier**: `backend/api/restaurant.py:431`

```python
def remove_ingredient(plat_id: int, ingredient_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `plat_id`: `int`
- `ingredient_id`: `int`
- `tenant`: `Tenant`

---

### `reset_user_password`

**Fichier**: `backend/api/admin.py:50`

```python
def reset_user_password(user_id: int, payload: ResetPasswordPayload | None = None):
```

**Paramètres**:
- `user_id`: `int`
- `payload`: `ResetPasswordPayload | None`

---

### `resolve_price_anomaly`

**Fichier**: `backend/api/newcms/operations.py:808`

```python
async def resolve_price_anomaly( product_id: int,
```

**Paramètres**:
- `product_id`: `int`
- `payload`: `PriceAnomalyResolveRequest`
- `tenant`: `Tenant`

**Retour**: `PriceAnomalyResolveResponse`

---

### `restaurant_dashboard_overview`

**Fichier**: `backend/api/restaurant.py:541`

```python
def restaurant_dashboard_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Paramètres**:
- `tenant`: `Tenant`

---

### `restaurant_forecast_overview`

**Fichier**: `backend/api/restaurant.py:547`

```python
def restaurant_forecast_overview( horizon_days: int = Query(30, ge=1, le=180),
```

**Paramètres**:
- `horizon_days`: `int`
- `granularity`: `str`
- `top`: `int`
- `tenant`: `Tenant`

---

### `restore_backup`

**Fichier**: `backend/api/admin.py:68`

```python
def restore_backup(filename: str):
```

**Paramètres**:
- `filename`: `str`

---

### `run_reconciliation`

**Fichier**: `backend/api/finance.py:620`

```python
def run_reconciliation( payload: FinanceRunRequest,
```

**Paramètres**:
- `payload`: `FinanceRunRequest`
- `tenant`: `Tenant`

**Retour**: `FinanceRunResponse`

---

### `search_bank_statements`

**Fichier**: `backend/api/finance.py:530`

```python
def search_bank_statements( account_id: int | None = Query(default=None),
```

**Paramètres**:
- `account_id`: `int | None`
- `period_start`: `str | None`
- `period_end`: `str | None`
- `status_filter`: `str | None`
- `page`: `int`
- `size`: `int`
- `sort`: `str`
- `tenant`: `Tenant`

**Retour**: `FinanceBankStatementSearchResponse`

---

### `search_epicerie_products`

**Fichier**: `backend/api/restaurant.py:515`

```python
def search_epicerie_products( q: str = Query("", description="Search query"),
```

Fast search endpoint for epicerie products.

**Paramètres**:
- `q`: `str`
- `limit`: `int`
- `suggest_for`: `str`

---

### `search_invoices`

**Fichier**: `backend/api/finance.py:248`

```python
def search_invoices( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `vendor_id`: `int | None`
- `status_filter`: `str | None`
- `date_from`: `str | None`
- `date_to`: `str | None`
- `page`: `int`
- `size`: `int`
- `sort`: `str`
- `tenant`: `Tenant`

**Retour**: `FinanceInvoiceSearchResponse`

---

### `suggest_autre_top`

**Fichier**: `backend/api/finance.py:287`

```python
def suggest_autre_top( entity_id: int | None = Query(default=None),
```

**Paramètres**:
- `entity_id`: `int | None`
- `limit`: `int`
- `tenant`: `Tenant`

**Retour**: `list[FinanceAutreSuggestion]`

---

### `sync_ingredient_prices`

**Fichier**: `backend/api/restaurant.py:197`

```python
def sync_ingredient_prices( force_update: bool = Query(False, description="Force update all linked ingredients"),
```

Synchronise les prix des ingrédients à partir des produits épicerie liés.

**Paramètres**:
- `force_update`: `bool`
- `tenant`: `Tenant`

---

### `to_supplier_score`

**Fichier**: `backend/api/supplier_scoring.py:113`

```python
def to_supplier_score(item: Dict[str, Any], rank: int) -> SupplierScore:
```

**Paramètres**:
- `item`: `Dict[str, Any]`
- `rank`: `int`

**Retour**: `SupplierScore`

---

### `transfer_from_epicerie`

**Fichier**: `backend/api/restaurant.py:357`

```python
def transfer_from_epicerie( ingredient_id: int = Body(...),
```

Transfère du stock depuis un produit épicerie.

**Paramètres**:
- `ingredient_id`: `int`
- `produit_epicerie_id`: `int`
- `quantite`: `float`
- `commentaire`: `Optional[str]`
- `tenant`: `Tenant`

---

### `transfer_from_epicerie`

**Fichier**: `backend/api/restaurant.py:483`

```python
def transfer_from_epicerie( produit_restaurant_id: int = Body(..., embed=True),
```

Transfère du stock depuis l'épicerie vers le restaurant via la fonction SQL transfer_from_epicerie.

**Paramètres**:
- `produit_restaurant_id`: `int`
- `quantite`: `float`
- `tenant`: `Tenant`

---

### `tva_summary`

**Fichier**: `backend/api/restaurant.py:106`

```python
def tva_summary( months: int = Query(6, ge=1, le=24),
```

**Paramètres**:
- `months`: `int`
- `tenant`: `Tenant`

---

### `update_account`

**Fichier**: `backend/api/finance.py:105`

```python
def update_account( account_id: int,
```

**Paramètres**:
- `account_id`: `int`
- `payload`: `dict`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `update_backup_settings`

**Fichier**: `backend/api/admin.py:98`

```python
def update_backup_settings(payload: BackupSettingsModel):
```

**Paramètres**:
- `payload`: `BackupSettingsModel`

---

### `update_finance_rule`

**Fichier**: `backend/api/newcms/finance.py:1131`

```python
def update_finance_rule( rule_id: str,
```

**Paramètres**:
- `rule_id`: `str`
- `payload`: `FinanceRuleCreate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

### `update_ingredient_on_plat`

**Fichier**: `backend/api/restaurant.py:436`

```python
def update_ingredient_on_plat( plat_id: int,
```

Met à jour la quantité/unité d'un ingrédient sur un plat.

**Paramètres**:
- `plat_id`: `int`
- `ingredient_id`: `int`
- `payload`: `RestaurantPlatIngredientUpdate`
- `tenant`: `Tenant`

---

### `update_match_status`

**Fichier**: `backend/api/finance.py:679`

```python
def update_match_status( match_id: int,
```

**Paramètres**:
- `match_id`: `int`
- `payload`: `FinanceMatchStatusRequest`
- `tenant`: `Tenant`

**Retour**: `FinanceMatch`

---

### `update_rule`

**Fichier**: `backend/api/finance.py:388`

```python
def update_rule( rule_id: int,
```

**Paramètres**:
- `rule_id`: `int`
- `payload`: `dict`
- `tenant`: `Tenant`

**Retour**: `FinanceRule`

---

### `update_transaction`

**Fichier**: `backend/api/finance.py:191`

```python
def update_transaction( transaction_id: int,
```

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `FinanceTransactionUpdate`
- `tenant`: `Tenant`

**Retour**: `dict`

---

## Authentication (6)

### `clear_auth_cookies`

**Fichier**: `backend/dependencies/security.py:157`

```python
def clear_auth_cookies(response: Response) -> None:
```

Supprime les cookies d'authentification (logout).

**Paramètres**:
- `response`: `Response`

**Retour**: `None`

---

### `decode_refresh_token`

**Fichier**: `backend/dependencies/security.py:284`

```python
def decode_refresh_token(token: str) -> dict[str, Any]:
```

Décode et valide un refresh token.

**Paramètres**:
- `token`: `str`

**Retour**: `dict[str, Any]`

---

### `optional_api_key`

**Fichier**: `backend/dependencies/auth.py:33`

```python
def optional_api_key(api_key: str | None = Depends(require_api_key)) -> None:
```

Déclenche la vérification mais ne retourne rien.

**Paramètres**:
- `api_key`: `str | None`

**Retour**: `None`

---

### `require_api_key`

**Fichier**: `backend/dependencies/auth.py:13`

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
```

Valide l'en-tête `X-API-KEY` si une clé est configurée.

**Paramètres**:
- `x_api_key`: `str | None`

**Retour**: `str | None`

---

### `revoke_token`

**Fichier**: `backend/dependencies/security.py:336`

```python
def revoke_token(token: str) -> None:
```

Ajoute le jti d'un token à la liste de révocation jusqu'à expiration.

**Paramètres**:
- `token`: `str`

**Retour**: `None`

---

### `set_auth_cookies`

**Fichier**: `backend/dependencies/security.py:125`

```python
def set_auth_cookies( response: Response,
```

Définit les cookies httpOnly pour les tokens d'accès et de rafraîchissement.

**Paramètres**:
- `response`: `Response`
- `access_token`: `str`
- `refresh_token`: `str`
- `access_max_age`: `int | None`
- `refresh_max_age`: `int | None`

**Retour**: `None`

---

## Background Tasks (8)

### `cancel_task`

**Fichier**: `backend/worker.py:248`

```python
def cancel_task(task_id: str) -> bool:
```

Annule une tâche en attente ou en cours.

**Paramètres**:
- `task_id`: `str`

**Retour**: `bool`

---

### `generate_daily_summary`

**Fichier**: `backend/tasks/reports.py:20`

```python
def generate_daily_summary(tenant_id: int):
```

Génère un rapport quotidien de synthèse.

**Paramètres**:
- `tenant_id`: `int`

---

### `generate_monthly_report`

**Fichier**: `backend/tasks/reports.py:26`

```python
def generate_monthly_report(tenant_id: int, month: int, year: int):
```

Génère un rapport financier mensuel.

**Paramètres**:
- `tenant_id`: `int`
- `month`: `int`
- `year`: `int`

---

### `generate_report`

**Fichier**: `backend/tasks/reports.py:6`

```python
def generate_report(self, report_type: str, params: dict, tenant_id: int):
```

Génère un rapport de manière asynchrone.

**Paramètres**:
- `self`
- `report_type`: `str`
- `params`: `dict`
- `tenant_id`: `int`

---

### `generate_report_async`

**Fichier**: `backend/worker.py:129`

```python
def generate_report_async(self, report_type: str, params: dict, tenant_id: int):
```

Génère un rapport en tâche de fond.

**Paramètres**:
- `self`
- `report_type`: `str`
- `params`: `dict`
- `tenant_id`: `int`

---

### `get_task_status`

**Fichier**: `backend/worker.py:238`

```python
def get_task_status(task_id: str) -> dict:
```

Récupère le statut d'une tâche en arrière-plan.

**Paramètres**:
- `task_id`: `str`

**Retour**: `dict`

---

### `process_invoice_async`

**Fichier**: `backend/worker.py:108`

```python
def process_invoice_async(self, invoice_id: int, tenant_id: int):
```

Traite une facture en tâche de fond (OCR, parsing, validation).

**Paramètres**:
- `self`
- `invoice_id`: `int`
- `tenant_id`: `int`

---

### `send_notification_async`

**Fichier**: `backend/worker.py:221`

```python
def send_notification_async(self, notification_type: str, recipient: str, data: dict):
```

Envoie une notification en tâche de fond (email, SMS, push).

**Paramètres**:
- `self`
- `notification_type`: `str`
- `recipient`: `str`
- `data`: `dict`

---

## Business Logic (45)

### `adjust_stock_level`

**Fichier**: `backend/services/stock.py:90`

```python
def adjust_stock_level( product_id: int,
```

**Paramètres**:
- `product_id`: `int`
- `target_quantity`: `float`

**Retour**: `dict[str, object]`

---

### `authenticate_user`

**Fichier**: `core/user_service.py:143`

```python
def authenticate_user(identifier: str, password: str) -> Optional[dict]:
```

Valide les identifiants et retourne l'utilisateur sans le hash.

**Paramètres**:
- `identifier`: `str`
- `password`: `str`

**Retour**: `Optional[dict]`

---

### `build_overview`

**Fichier**: `backend/services/reports.py:219`

```python
def build_overview(*, tenant_id: int) -> dict[str, Any]:
```

Assemble toutes les sections du rapport consolidé consommé par la SPA.

**Retour**: `dict[str, Any]`

---

### `create_backup_now`

**Fichier**: `backend/services/admin.py:214`

```python
def create_backup_now(label: str | None = None) -> dict[str, Any]:
```

**Paramètres**:
- `label`: `str | None`

**Retour**: `dict[str, Any]`

---

### `create_job`

**Fichier**: `backend/services/zero_click_jobs.py:16`

```python
def create_job( job_id: str,
```

Crée un nouveau job zero-click en base de données.

**Paramètres**:
- `job_id`: `str`
- `tenant_id`: `int`
- `filename`: `str | None`
- `supplier_hint`: `str | None`
- `margin_percent`: `float`
- `auto_confirm`: `bool`
- `session_id`: `str | None`

**Retour**: `dict[str, Any]`

---

### `delete_backup_file`

**Fichier**: `backend/services/admin.py:223`

```python
def delete_backup_file(filename: str) -> None:
```

**Paramètres**:
- `filename`: `str`

**Retour**: `None`

---

### `delete_old_jobs`

**Fichier**: `backend/services/zero_click_jobs.py:215`

```python
def delete_old_jobs(days: int = 30) -> int:
```

Supprime les jobs terminés de plus de N jours.

**Paramètres**:
- `days`: `int`

**Retour**: `int`

---

### `delete_product`

**Fichier**: `backend/services/catalog.py:204`

```python
def delete_product(product_id: int, *, tenant_id: int) -> None:
```

**Paramètres**:
- `product_id`: `int`

**Retour**: `None`

---

### `enrich_lines_with_fuzzy_matches`

**Fichier**: `backend/services/product_matching.py:162`

```python
def enrich_lines_with_fuzzy_matches( lines: list[dict[str, Any]],
```

Enrichit les lignes de facture avec des suggestions de matching flou.

**Paramètres**:
- `lines`: `list[dict[str, Any]]`

**Retour**: `list[dict[str, Any]]`

---

### `export_dataset`

**Fichier**: `backend/services/reports.py:337`

```python
def export_dataset(report_type: str, limit: int, *, tenant_id: int) -> Tuple[str, bytes]:
```

Retourne (filename, csv_bytes) pour le dataset sélectionné.

**Paramètres**:
- `report_type`: `str`
- `limit`: `int`

**Retour**: `Tuple[str, bytes]`

---

### `fetch_admin_overview`

**Fichier**: `backend/services/admin.py:170`

```python
def fetch_admin_overview(*, tenant_id: int) -> dict[str, Any]:
```

**Retour**: `dict[str, Any]`

---

### `fetch_category_breakdown`

**Fichier**: `backend/services/reports.py:64`

```python
def fetch_category_breakdown(*, tenant_id: int, limit: int = 50) -> list[dict[str, Any]]:
```

Agrège le stock par catégorie pour prioriser les familles les plus valorisées.

**Retour**: `list[dict[str, Any]]`

---

### `fetch_dashboard_metrics`

**Fichier**: `backend/services/dashboard.py:164`

```python
def fetch_dashboard_metrics(*, tenant_id: int) -> dict[str, Any]:
```

**Retour**: `dict[str, Any]`

---

### `fetch_kpis`

**Fichier**: `backend/services/dashboard.py:13`

```python
def fetch_kpis(tenant_id: int) -> dict[str, float | int]:
```

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `dict[str, float | int]`

---

### `fetch_low_stock`

**Fichier**: `backend/services/reports.py:102`

```python
def fetch_low_stock(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
```

Liste les produits passés sous leur seuil d'alerte.

**Retour**: `list[dict[str, Any]]`

---

### `fetch_movement_timeseries`

**Fichier**: `backend/services/stock.py:13`

```python
def fetch_movement_timeseries( window_days: int = 30,
```

Récupère les mouvements de stock groupés par jour.

**Paramètres**:
- `window_days`: `int`
- `product_id`: `Optional[int]`

**Retour**: `pd.DataFrame`

---

### `fetch_negative_stock`

**Fichier**: `backend/services/reports.py:122`

```python
def fetch_negative_stock(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
```

Identifie les stocks négatifs, symptôme d'écarts ou de ventes non comptabilisées.

**Retour**: `list[dict[str, Any]]`

---

### `fetch_price_history_for_product`

**Fichier**: `core/price_history_service.py:597`

```python
def fetch_price_history_for_product( *, produit_id: int | None = None,
```

Retourne l'historique pour un produit ou un code spécifique.

**Retour**: `pd.DataFrame`

---

### `fetch_recent_movements`

**Fichier**: `backend/services/stock.py:57`

```python
def fetch_recent_movements( limit: int = 100,
```

**Paramètres**:
- `limit`: `int`
- `product_id`: `Optional[int]`

**Retour**: `pd.DataFrame`

---

### `fetch_recent_suppliers`

**Fichier**: `backend/services/catalog_data.py:135`

```python
def fetch_recent_suppliers(*, tenant_id: int = 1) -> pd.DataFrame:
```

Retourne la dernière source de mouvement entrant par produit.

**Retour**: `pd.DataFrame`

---

### `fetch_table_preview`

**Fichier**: `backend/services/admin.py:103`

```python
def fetch_table_preview(table_name: str, limit: int = 50) -> list[dict[str, Any]]:
```

**Paramètres**:
- `table_name`: `str`
- `limit`: `int`

**Retour**: `list[dict[str, Any]]`

---

### `fetch_top_value`

**Fichier**: `backend/services/reports.py:83`

```python
def fetch_top_value(*, tenant_id: int, limit: int = 10) -> list[dict[str, Any]]:
```

Retourne les articles les plus coûteux en valeur d'achat immobilisée.

**Retour**: `list[dict[str, Any]]`

---

### `fill_missing_prices_from_history`

**Fichier**: `core/price_history_service.py:168`

```python
def fill_missing_prices_from_history(tenant_id: int = 1, margin_multiplier: float | None = None) -> dict:
```

Remplit les prix_achat/prix_vente manquants depuis l'historique produits_price_history.

**Paramètres**:
- `tenant_id`: `int`
- `margin_multiplier`: `float | None`

**Retour**: `dict`

---

### `generate_secure_password`

**Fichier**: `core/user_service.py:77`

```python
def generate_secure_password(length: int = 14) -> str:
```

Génère un mot de passe robuste conforme à la politique de l’entreprise.

**Paramètres**:
- `length`: `int`

**Retour**: `str`

---

### `get_best_product_match`

**Fichier**: `backend/services/product_matching.py:133`

```python
def get_best_product_match( query: str,
```

Retourne le meilleur match flou pour une requête produit.

**Paramètres**:
- `query`: `str`

**Retour**: `dict[str, Any] | None`

---

### `get_job`

**Fichier**: `backend/services/zero_click_jobs.py:103`

```python
def get_job(job_id: str, tenant_id: int | None = None) -> dict[str, Any] | None:
```

Récupère un job par son ID.

**Paramètres**:
- `job_id`: `str`
- `tenant_id`: `int | None`

**Retour**: `dict[str, Any] | None`

---

### `get_product`

**Fichier**: `backend/services/catalog.py:118`

```python
def get_product(product_id: int, tenant_id: int) -> dict[str, Any]:
```

**Paramètres**:
- `product_id`: `int`
- `tenant_id`: `int`

**Retour**: `dict[str, Any]`

---

### `get_product_by_barcode`

**Fichier**: `backend/services/catalog.py:214`

```python
def get_product_by_barcode(barcode: str, *, tenant_id: int) -> dict[str, Any]:
```

**Paramètres**:
- `barcode`: `str`

**Retour**: `dict[str, Any]`

---

### `get_session_details`

**Fichier**: `backend/services/zero_click_jobs.py:310`

```python
def get_session_details( session_id: str,
```

Récupère tous les imports d'une session donnée.

**Paramètres**:
- `session_id`: `str`
- `tenant_id`: `int`

**Retour**: `dict[str, Any] | None`

---

### `get_user_by_id`

**Fichier**: `core/user_service.py:115`

```python
def get_user_by_id(user_id: int) -> Optional[dict]:
```

**Paramètres**:
- `user_id`: `int`

**Retour**: `Optional[dict]`

---

### `get_user_by_login`

**Fichier**: `core/user_service.py:97`

```python
def get_user_by_login(identifier: str) -> Optional[dict]:
```

Retourne un utilisateur à partir de son email ou nom d'utilisateur.

**Paramètres**:
- `identifier`: `str`

**Retour**: `Optional[dict]`

---

### `list_backups`

**Fichier**: `backend/services/maintenance.py:11`

```python
def list_backups(limit: int | None = None) -> list[dict[str, object]]:
```

**Paramètres**:
- `limit`: `int | None`

**Retour**: `list[dict[str, object]]`

---

### `list_resolution_log`

**Fichier**: `backend/services/audit.py:242`

```python
def list_resolution_log(limit: int = 100, *, tenant_id: int = 1) -> list[dict[str, object]]:
```

**Paramètres**:
- `limit`: `int`

**Retour**: `list[dict[str, object]]`

---

### `parse_barcode_input`

**Fichier**: `core/product_service.py:53`

```python
def parse_barcode_input(raw_codes: str | Iterable[str] | None) -> list[str]:
```

Normalise une entrée utilisateur en liste de codes-barres uniques.

**Paramètres**:
- `raw_codes`: `str | Iterable[str] | None`

**Retour**: `list[str]`

---

### `parse_csv`

**Fichier**: `backend/services/importers/bank_statement_csv.py:58`

```python
def parse_csv(content: bytes | str) -> list[dict[str, Any]]:
```

Parse un contenu CSV en liste de mouvements normalisés.

**Paramètres**:
- `content`: `bytes | str`

**Retour**: `list[dict[str, Any]]`

---

### `persist_daily_snapshot`

**Fichier**: `backend/services/capital.py:222`

```python
def persist_daily_snapshot(snapshot_date: datetime | None = None) -> None:
```

**Paramètres**:
- `snapshot_date`: `datetime | None`

**Retour**: `None`

---

### `reset_password`

**Fichier**: `backend/services/admin.py:193`

```python
def reset_password(user_id: int, new_password: str | None = None) -> str:
```

**Paramètres**:
- `user_id`: `int`
- `new_password`: `str | None`

**Retour**: `str`

---

### `reset_user_password`

**Fichier**: `core/user_service.py:253`

```python
def reset_user_password(user_id: int, new_password: Optional[str] = None) -> str:
```

Réinitialise le mot de passe et retourne sa valeur en clair.

**Paramètres**:
- `user_id`: `int`
- `new_password`: `Optional[str]`

**Retour**: `str`

---

### `restore_backup_file`

**Fichier**: `backend/services/admin.py:219`

```python
def restore_backup_file(filename: str) -> None:
```

**Paramètres**:
- `filename`: `str`

**Retour**: `None`

---

### `save_settings`

**Fichier**: `backend/services/admin.py:197`

```python
def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
```

**Paramètres**:
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `serialize_backup`

**Fichier**: `backend/services/admin.py:110`

```python
def serialize_backup(metadata) -> dict[str, Any]:
```

**Paramètres**:
- `metadata`

**Retour**: `dict[str, Any]`

---

### `serialize_binary_status`

**Fichier**: `backend/services/admin.py:119`

```python
def serialize_binary_status(status: BinaryStatus) -> dict[str, Any]:
```

**Paramètres**:
- `status`: `BinaryStatus`

**Retour**: `dict[str, Any]`

---

### `update_job_status`

**Fichier**: `backend/services/zero_click_jobs.py:62`

```python
def update_job_status( job_id: str,
```

Met à jour le statut d'un job.

**Paramètres**:
- `job_id`: `str`
- `status`: `str`
- `result`: `dict[str, Any] | None`
- `error`: `str | None`

**Retour**: `None`

---

### `update_role`

**Fichier**: `backend/services/admin.py:189`

```python
def update_role(user_id: int, role: str) -> None:
```

**Paramètres**:
- `user_id`: `int`
- `role`: `str`

**Retour**: `None`

---

### `update_user_role`

**Fichier**: `core/user_service.py:228`

```python
def update_user_role(user_id: int, role: str) -> None:
```

Modifie le rôle d'un utilisateur tout en protégeant le dernier admin.

**Paramètres**:
- `user_id`: `int`
- `role`: `str`

**Retour**: `None`

---

## Cache (9)

### `__init__`

**Fichier**: `backend/cache.py:173`

```python
def __init__(self, prefix: str = "app"):
```

**Paramètres**:
- `self`
- `prefix`: `str`

---

### `_key`

**Fichier**: `backend/cache.py:183`

```python
def _key(self, key: str) -> str:
```

**Paramètres**:
- `self`
- `key`: `str`

**Retour**: `str`

---

### `asyncio_available`

**Fichier**: `backend/cache.py:155`

```python
def asyncio_available(func: Callable) -> bool:
```

Vérifie si la fonction est asynchrone.

**Paramètres**:
- `func`: `Callable`

**Retour**: `bool`

---

### `decorator`

**Fichier**: `backend/cache.py:280`

```python
def decorator(func: Callable) -> Callable:
```

**Paramètres**:
- `func`: `Callable`

**Retour**: `Callable`

---

### `delete`

**Fichier**: `backend/cache.py:209`

```python
def delete(self, key: str) -> bool:
```

Supprime une clé du cache.

**Paramètres**:
- `self`
- `key`: `str`

**Retour**: `bool`

---

### `get`

**Fichier**: `backend/cache.py:186`

```python
def get(self, key: str) -> Optional[Any]:
```

Récupère une valeur depuis le cache.

**Paramètres**:
- `self`
- `key`: `str`

**Retour**: `Optional[Any]`

---

### `invalidate_pattern`

**Fichier**: `backend/cache.py:218`

```python
def invalidate_pattern(self, pattern: str) -> int:
```

Invalide toutes les clés correspondant au motif.

**Paramètres**:
- `self`
- `pattern`: `str`

**Retour**: `int`

---

### `invalidate_tenant`

**Fichier**: `backend/cache.py:248`

```python
def invalidate_tenant(self, tenant_id: int) -> int:
```

Invalide tout le cache pour un tenant donné.

**Paramètres**:
- `self`
- `tenant_id`: `int`

**Retour**: `int`

---

### `set`

**Fichier**: `backend/cache.py:196`

```python
def set(self, key: str, value: Any, ttl: int = 300) -> bool:
```

Enregistre une valeur dans le cache avec TTL.

**Paramètres**:
- `self`
- `key`: `str`
- `value`: `Any`
- `ttl`: `int`

**Retour**: `bool`

---

## Calculation (2)

### `_calculate_quality_score`

**Fichier**: `core/import_analyzer.py:318`

```python
def _calculate_quality_score(self, report: ImportAnalysisReport) -> float:
```

Calcule un score de qualité global (0-100).

**Paramètres**:
- `self`
- `report`: `ImportAnalysisReport`

**Retour**: `float`

---

### `compute_backup_statistics`

**Fichier**: `core/backup_manager.py:294`

```python
def compute_backup_statistics(backups: Iterable[BackupMetadata]) -> Dict[str, float]:
```

Calcule des statistiques agrégées (min/max/moyenne/taille totale).

**Paramètres**:
- `backups`: `Iterable[BackupMetadata]`

**Retour**: `Dict[str, float]`

---

## Data Creation (12)

### `_add_pattern`

**Fichier**: `core/bank_import/categorizer.py:188`

```python
def _add_pattern(self, keyword: str) -> None:
```

Add a regex pattern for a keyword.

**Paramètres**:
- `self`
- `keyword`: `str`

**Retour**: `None`

---

### `add_custom_rule`

**Fichier**: `core/bank_import/categorizer.py:389`

```python
def add_custom_rule(self, libelle_pattern: str, category_code: str) -> None:
```

Add a custom categorization rule.

**Paramètres**:
- `self`
- `libelle_pattern`: `str`
- `category_code`: `str`

**Retour**: `None`

---

### `add_error`

**Fichier**: `core/bank_import/models.py:228`

```python
def add_error(self, msg: str) -> None:
```

Add an error message.

**Paramètres**:
- `self`
- `msg`: `str`

**Retour**: `None`

---

### `add_warning`

**Fichier**: `core/bank_import/models.py:232`

```python
def add_warning(self, msg: str) -> None:
```

Add a warning message.

**Paramètres**:
- `self`
- `msg`: `str`

**Retour**: `None`

---

### `create_access_token`

**Fichier**: `backend/dependencies/security.py:98`

```python
def create_access_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
```

Sérialise les claims fournis dans un JWT signé avec des claims adaptés à la rotation.

**Paramètres**:
- `claims`: `dict[str, Any]`
- `expires_delta`: `timedelta | None`

**Retour**: `str`

---

### `create_initial_stock`

**Fichier**: `core/products_loader.py:400`

```python
def create_initial_stock( conn: Connection,
```

Insère un mouvement de stock positif et renvoie ``True`` s'il est créé.

**Paramètres**:
- `conn`: `Connection`
- `produit_id`: `int`
- `quantite`: `float`

**Retour**: `bool`

---

### `create_refresh_token`

**Fichier**: `backend/dependencies/security.py:109`

```python
def create_refresh_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
```

Crée un refresh token avec une durée d'expiration plus longue.

**Paramètres**:
- `claims`: `dict[str, Any]`
- `expires_delta`: `timedelta | None`

**Retour**: `str`

---

### `insert_or_update_barcode`

**Fichier**: `core/products_loader.py:150`

```python
def insert_or_update_barcode( conn: Connection,
```

Insère un code-barres et renvoie *added*, *skipped* ou *conflict*.

**Paramètres**:
- `conn`: `Connection`
- `produit_id`: `int`
- `barcode`: `str`
- `tenant_id`: `float | int | None`

**Retour**: `str`

---

### `restore_backup`

**Fichier**: `core/backup_manager.py:505`

```python
def restore_backup( filename: str,
```

Restaure la base de données à partir du fichier de sauvegarde fourni.

**Paramètres**:
- `filename`: `str`

**Retour**: `None`

---

### `save_backup_settings`

**Fichier**: `core/backup_manager.py:110`

```python
def save_backup_settings( settings: Dict[str, object],
```

Persiste les paramètres d'automatisation des sauvegardes sur disque.

**Paramètres**:
- `settings`: `Dict[str, object]`
- `directory`: `str | os.PathLike[str] | None`

**Retour**: `None`

---

### `save_report`

**Fichier**: `core/import_analyzer.py:361`

```python
def save_report(self, report: ImportAnalysisReport, output_path: str | Path) -> None:
```

Sauvegarde un rapport en JSON.

**Paramètres**:
- `self`
- `report`: `ImportAnalysisReport`
- `output_path`: `str | Path`

**Retour**: `None`

---

### `save_summary_csv`

**Fichier**: `core/import_analyzer.py:366`

```python
def save_summary_csv(self, output_path: str | Path) -> None:
```

Sauvegarde un résumé en CSV.

**Paramètres**:
- `self`
- `output_path`: `str | Path`

**Retour**: `None`

---

## Data Deletion (1)

### `delete_backup`

**Fichier**: `core/backup_manager.py:494`

```python
def delete_backup( filename: str,
```

Supprime un fichier de sauvegarde existant.

**Paramètres**:
- `filename`: `str`

**Retour**: `None`

---

## Data Normalization (1)

### `clean_lines`

**Fichier**: `core/bank_import/extractor.py:340`

```python
def clean_lines( self, lines: List[str],
```

Remove header/footer lines and noise.

**Paramètres**:
- `self`
- `lines`: `List[str]`
- `bank_type`: `BankType`

**Retour**: `List[str]`

---

## Data Retrieval (16)

### `_get_columns`

**Fichier**: `core/bank_import/parser.py:353`

```python
def _get_columns(self, bank_type: BankType) -> ColumnPositions:
```

Retourne les positions de colonnes selon le type de banque.

**Paramètres**:
- `self`
- `bank_type`: `BankType`

**Retour**: `ColumnPositions`

---

### `get_backup_directory`

**Fichier**: `core/backup_manager.py:122`

```python
def get_backup_directory( directory: str | os.PathLike[str] | None = None,
```

Retourne le répertoire utilisé pour stocker les fichiers de sauvegarde.

**Paramètres**:
- `directory`: `str | os.PathLike[str] | None`

**Retour**: `Path`

---

### `get_categories_for_direction`

**Fichier**: `core/bank_import/categories.py:361`

```python
def get_categories_for_direction(direction: str) -> List[CategoryDefinition]:
```

Get categories matching a direction (IN, OUT, or BOTH).

**Paramètres**:
- `direction`: `str`

**Retour**: `List[CategoryDefinition]`

---

### `get_category`

**Fichier**: `core/bank_import/categories.py:347`

```python
def get_category(code: str) -> Optional[CategoryDefinition]:
```

Get category definition by code.

**Paramètres**:
- `code`: `str`

**Retour**: `Optional[CategoryDefinition]`

---

### `get_common_corrections`

**Fichier**: `core/bank_import/categorizer.py:526`

```python
def get_common_corrections(limit: int = 20) -> List[Dict]:
```

Get the most common categorization corrections.

**Paramètres**:
- `limit`: `int`

**Retour**: `List[Dict]`

---

### `get_current_tenant`

**Fichier**: `backend/dependencies/tenant.py:76`

```python
async def get_current_tenant(request: Request) -> Tenant:
```

Récupère le tenant courant depuis l'utilisateur authentifié (cookies ou bearer).

**Paramètres**:
- `request`: `Request`

**Retour**: `Tenant`

---

### `get_current_user`

**Fichier**: `backend/dependencies/security.py:243`

```python
def get_current_user(token: str | None = Depends(oauth2_scheme)) -> AuthenticatedUser:
```

Héritage : récupère l'utilisateur depuis un token Bearer OAuth2.

**Paramètres**:
- `token`: `str | None`

**Retour**: `AuthenticatedUser`

---

### `get_current_user_from_request`

**Fichier**: `backend/dependencies/security.py:200`

```python
def get_current_user_from_request(request: Request) -> AuthenticatedUser:
```

Récupère l'utilisateur courant depuis le cookie HTTP-Only.

**Paramètres**:
- `request`: `Request`

**Retour**: `AuthenticatedUser`

---

### `get_epicerie_tenant`

**Fichier**: `backend/dependencies/tenant.py:159`

```python
async def get_epicerie_tenant(request: Request) -> Tenant:
```

Dépendance pour le module épicerie (operations, catalogue, etc.).

**Paramètres**:
- `request`: `Request`

**Retour**: `Tenant`

---

### `get_intelligence_tenant`

**Fichier**: `backend/dependencies/tenant.py:150`

```python
async def get_intelligence_tenant(request: Request) -> Tenant:
```

Dépendance pour le module intelligence/scoring.

**Paramètres**:
- `request`: `Request`

**Retour**: `Tenant`

---

### `get_parser`

**Fichier**: `core/bank_import/parser.py:1146`

```python
def get_parser(self, bank_type: BankType) -> UnifiedBankParser:
```

Récupère une instance de parseur pour un type de banque.

**Paramètres**:
- `self`
- `bank_type`: `BankType`

**Retour**: `UnifiedBankParser`

---

### `get_parser`

**Fichier**: `core/bank_import/parser.py:1160`

```python
def get_parser(bank_type: BankType) -> UnifiedBankParser:
```

Fonction fabrique pour obtenir le parseur adapté à un type de banque.

**Paramètres**:
- `bank_type`: `BankType`

**Retour**: `UnifiedBankParser`

---

### `get_restaurant_tenant`

**Fichier**: `backend/dependencies/tenant.py:131`

```python
async def get_restaurant_tenant(request: Request) -> Tenant:
```

Dépendance pour le module restaurant.

**Paramètres**:
- `request`: `Request`

**Retour**: `Tenant`

---

### `get_restaurant_tenant_strict`

**Fichier**: `backend/dependencies/tenant.py:141`

```python
async def get_restaurant_tenant_strict(request: Request) -> Tenant:
```

Dépendance pour le module restaurant avec authentification obligatoire.

**Paramètres**:
- `request`: `Request`

**Retour**: `Tenant`

---

### `load_backup_settings`

**Fichier**: `core/backup_manager.py:85`

```python
def load_backup_settings( directory: str | os.PathLike[str] | None = None,
```

Retourne les paramètres d'automatisation de sauvegarde persistés.

**Paramètres**:
- `directory`: `str | os.PathLike[str] | None`

**Retour**: `Dict[str, object]`

---

### `load_vendor_category_rules`

**Fichier**: `core/vendor_categories.py:25`

```python
def load_vendor_category_rules() -> tuple[tuple[tuple[str, ...], str, Sequence[str] | None], ...]:
```

Charge la table `data/vendor_category_mapping.csv` pour étendre les règles.

**Retour**: `tuple[tuple[tuple[str, ...], str, Sequence[str] | None], ...]`

---

## Data Schema (6)

### `nom_not_empty`

**Fichier**: `backend/schemas/catalog.py:23`

```python
def nom_not_empty(cls, v: str) -> str:
```

**Paramètres**:
- `cls`
- `v`: `str`

**Retour**: `str`

---

### `validate_grade`

**Fichier**: `backend/schemas/supplier_scoring.py:88`

```python
def validate_grade(cls, v: str) -> str:
```

Valide que le grade est A, B, C, D ou F.

**Paramètres**:
- `cls`
- `v`: `str`

**Retour**: `str`

---

### `validate_issue_type`

**Fichier**: `backend/schemas/supplier_scoring.py:299`

```python
def validate_issue_type(cls, v: str) -> str:
```

Valide le type de problème.

**Paramètres**:
- `cls`
- `v`: `str`

**Retour**: `str`

---

### `validate_severity`

**Fichier**: `backend/schemas/supplier_scoring.py:308`

```python
def validate_severity(cls, v: str) -> str:
```

Valide la sévérité.

**Paramètres**:
- `cls`
- `v`: `str`

**Retour**: `str`

---

### `validate_total_weight`

**Fichier**: `backend/schemas/supplier_scoring.py:137`

```python
def validate_total_weight(cls, v: float) -> float:
```

Valide que le poids total est proche de 1.0.

**Paramètres**:
- `cls`
- `v`: `float`

**Retour**: `float`

---

### `validate_weights`

**Fichier**: `backend/schemas/supplier_scoring.py:153`

```python
def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
```

Valide que tous les poids sont entre 0 et 1 et que leur somme fait ~1.0.

**Paramètres**:
- `cls`
- `v`: `Dict[str, float]`

**Retour**: `Dict[str, float]`

---

## Database (28)

### `__init__`

**Fichier**: `core/repositories/base.py:121`

```python
def __init__(self, engine: Engine):
```

**Paramètres**:
- `self`
- `engine`: `Engine`

---

### `_row_to_movement`

**Fichier**: `core/repositories/stock_movements.py:225`

```python
def _row_to_movement(self, row: dict) -> StockMovement:
```

**Paramètres**:
- `self`
- `row`: `dict`

**Retour**: `StockMovement`

---

### `_row_to_user`

**Fichier**: `core/repositories/users.py:203`

```python
def _row_to_user(self, row: dict) -> User:
```

**Paramètres**:
- `self`
- `row`: `dict`

**Retour**: `User`

---

### `add`

**Fichier**: `core/repositories/base.py:45`

```python
def add(self, entity: T, *, tenant_id: int) -> T:
```

Add new entity and return it with generated ID.

**Paramètres**:
- `self`
- `entity`: `T`

**Retour**: `T`

---

### `add`

**Fichier**: `core/repositories/stock_movements.py:65`

```python
def add(self, movement: StockMovement) -> StockMovement:
```

**Paramètres**:
- `self`
- `movement`: `StockMovement`

**Retour**: `StockMovement`

---

### `add`

**Fichier**: `core/repositories/users.py:48`

```python
def add(self, user: User, password_hash: str) -> User:
```

**Paramètres**:
- `self`
- `user`: `User`
- `password_hash`: `str`

**Retour**: `User`

---

### `deactivate`

**Fichier**: `core/repositories/users.py:57`

```python
def deactivate(self, user_id: int, *, tenant_id: int) -> bool:
```

**Paramètres**:
- `self`
- `user_id`: `int`

**Retour**: `bool`

---

### `deactivate`

**Fichier**: `core/repositories/users.py:189`

```python
def deactivate(self, user_id: int, *, tenant_id: int) -> bool:
```

**Paramètres**:
- `self`
- `user_id`: `int`

**Retour**: `bool`

---

### `delete`

**Fichier**: `core/repositories/base.py:55`

```python
def delete(self, id: ID, *, tenant_id: int) -> bool:
```

Delete entity by ID. Returns True if deleted.

**Paramètres**:
- `self`
- `id`: `ID`

**Retour**: `bool`

---

### `exec_sql_return_id_with_conn`

**Fichier**: `core/products_loader.py:199`

```python
def exec_sql_return_id_with_conn(conn: Connection, sql: str, params=None):
```

Exécute une requête SQL et retourne l'ID (colonne 0) en utilisant une connexion ouverte.

**Paramètres**:
- `conn`: `Connection`
- `sql`: `str`
- `params`

---

### `execute_raw_sql`

**Fichier**: `core/data_repository.py:114`

```python
def execute_raw_sql(sql: str | ClauseElement, params=None, fetch: bool = False):
```

Compat: exécute une requête SQL et peut retourner les lignes si fetch=True.

**Paramètres**:
- `sql`: `str | ClauseElement`
- `params`
- `fetch`: `bool`

---

### `get_by_email`

**Fichier**: `core/repositories/users.py:39`

```python
def get_by_email(self, email: str, *, tenant_id: int) -> User | None:
```

**Paramètres**:
- `self`
- `email`: `str`

**Retour**: `User | None`

---

### `get_by_email`

**Fichier**: `core/repositories/users.py:93`

```python
def get_by_email(self, email: str, *, tenant_id: int) -> User | None:
```

**Paramètres**:
- `self`
- `email`: `str`

**Retour**: `User | None`

---

### `get_by_id`

**Fichier**: `core/repositories/base.py:26`

```python
def get_by_id(self, id: ID, *, tenant_id: int) -> T | None:
```

Get entity by ID.

**Paramètres**:
- `self`
- `id`: `ID`

**Retour**: `T | None`

---

### `get_by_id`

**Fichier**: `core/repositories/stock_movements.py:52`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> StockMovement | None:
```

**Paramètres**:
- `self`
- `id`: `int`

**Retour**: `StockMovement | None`

---

### `get_by_id`

**Fichier**: `core/repositories/stock_movements.py:85`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> StockMovement | None:
```

**Paramètres**:
- `self`
- `id`: `int`

**Retour**: `StockMovement | None`

---

### `get_by_id`

**Fichier**: `core/repositories/users.py:33`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> User | None:
```

**Paramètres**:
- `self`
- `id`: `int`

**Retour**: `User | None`

---

### `get_by_id`

**Fichier**: `core/repositories/users.py:67`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> User | None:
```

**Paramètres**:
- `self`
- `id`: `int`

**Retour**: `User | None`

---

### `get_by_username`

**Fichier**: `core/repositories/users.py:36`

```python
def get_by_username(self, username: str, *, tenant_id: int) -> User | None:
```

**Paramètres**:
- `self`
- `username`: `str`

**Retour**: `User | None`

---

### `get_by_username`

**Fichier**: `core/repositories/users.py:80`

```python
def get_by_username(self, username: str, *, tenant_id: int) -> User | None:
```

**Paramètres**:
- `self`
- `username`: `str`

**Retour**: `User | None`

---

### `import_bank_pdf`

**Fichier**: `core/bank_import/orchestrator.py:633`

```python
def import_bank_pdf( pdf_path: Path,
```

Convenience function for importing a bank PDF.

**Paramètres**:
- `pdf_path`: `Path`
- `entity_code`: `str`
- `account_label`: `str`
- `dry_run`: `bool`
- `strict_validation`: `bool`

**Retour**: `ImportResult`

---

### `list_by_product`

**Fichier**: `core/repositories/stock_movements.py:55`

```python
def list_by_product( self, produit_id: int, *, tenant_id: int, limit: int = 100
```

**Paramètres**:
- `self`
- `produit_id`: `int`

**Retour**: `Sequence[StockMovement]`

---

### `list_by_product`

**Fichier**: `core/repositories/stock_movements.py:98`

```python
def list_by_product( self, produit_id: int, *, tenant_id: int, limit: int = 100
```

**Paramètres**:
- `self`
- `produit_id`: `int`

**Retour**: `Sequence[StockMovement]`

---

### `update`

**Fichier**: `core/repositories/base.py:50`

```python
def update(self, entity: T, *, tenant_id: int) -> T:
```

Update existing entity.

**Paramètres**:
- `self`
- `entity`: `T`

**Retour**: `T`

---

### `update`

**Fichier**: `core/repositories/users.py:51`

```python
def update(self, user: User) -> User:
```

**Paramètres**:
- `self`
- `user`: `User`

**Retour**: `User`

---

### `update`

**Fichier**: `core/repositories/users.py:158`

```python
def update(self, user: User) -> User:
```

**Paramètres**:
- `self`
- `user`: `User`

**Retour**: `User`

---

### `update_last_login`

**Fichier**: `core/repositories/users.py:54`

```python
def update_last_login(self, user_id: int, *, tenant_id: int) -> None:
```

**Paramètres**:
- `self`
- `user_id`: `int`

**Retour**: `None`

---

### `update_last_login`

**Fichier**: `core/repositories/users.py:179`

```python
def update_last_login(self, user_id: int, *, tenant_id: int) -> None:
```

**Paramètres**:
- `self`
- `user_id`: `int`

**Retour**: `None`

---

## Document Processing (14)

### `can_parse`

**Fichier**: `core/bank_import/USAGE_EXAMPLES.py:89`

```python
def can_parse(self, text: str) -> bool:
```

Vérifie si ce parser peut traiter le texte donné.

**Paramètres**:
- `self`
- `text`: `str`

**Retour**: `bool`

---

### `can_parse`

**Fichier**: `core/bank_import/parser.py:66`

```python
def can_parse(self, text: str) -> bool:
```

Vérifie si ce parseur peut gérer le texte fourni.

**Paramètres**:
- `self`
- `text`: `str`

**Retour**: `bool`

---

### `can_parse`

**Fichier**: `core/bank_import/parser.py:130`

```python
def can_parse(self, text: str) -> bool:
```

Vérifie si ce parseur peut gérer le texte fourni.

**Paramètres**:
- `self`
- `text`: `str`

**Retour**: `bool`

---

### `detect_bank_full`

**Fichier**: `core/bank_import/detector.py:360`

```python
def detect_bank_full(text: str) -> DetectionResult:
```

Convenience function for full bank detection with IBAN extraction.

**Paramètres**:
- `text`: `str`

**Retour**: `DetectionResult`

---

### `detect_bank_type`

**Fichier**: `core/bank_import/detector.py:315`

```python
def detect_bank_type(text: str) -> Tuple[BankType, float, Optional[str]]:
```

Enhanced bank type detection with confidence and IBAN.

**Paramètres**:
- `text`: `str`

**Retour**: `Tuple[BankType, float, Optional[str]]`

---

### `detect_bank_type_simple`

**Fichier**: `core/bank_import/detector.py:342`

```python
def detect_bank_type_simple(text: str) -> BankType:
```

Simple bank type detection (backward compatibility).

**Paramètres**:
- `text`: `str`

**Retour**: `BankType`

---

### `detect_full`

**Fichier**: `core/bank_import/detector.py:231`

```python
def detect_full(self, text: str) -> DetectionResult:
```

Perform full detection with IBAN and BIC extraction.

**Paramètres**:
- `self`
- `text`: `str`

**Retour**: `DetectionResult`

---

### `extract`

**Fichier**: `core/bank_import/extractor.py:125`

```python
def extract(self, pdf_path: Path) -> ExtractionResult:
```

Extract and preprocess PDF content.

**Paramètres**:
- `self`
- `pdf_path`: `Path`

**Retour**: `ExtractionResult`

---

### `extract_account_number`

**Fichier**: `core/bank_import/detector.py:205`

```python
def extract_account_number(self, text: str, bank_type: BankType) -> Optional[str]:
```

Extract account number based on bank type.

**Paramètres**:
- `self`
- `text`: `str`
- `bank_type`: `BankType`

**Retour**: `Optional[str]`

---

### `extract_bic`

**Fichier**: `core/bank_import/detector.py:300`

```python
def extract_bic(self, text: str) -> Optional[str]:
```

Extract BIC/SWIFT code from text.

**Paramètres**:
- `self`
- `text`: `str`

**Retour**: `Optional[str]`

---

### `extract_iban`

**Fichier**: `core/bank_import/detector.py:272`

```python
def extract_iban(self, text: str, bank_type: Optional[BankType] = None) -> Optional[str]:
```

Extract IBAN from text.

**Paramètres**:
- `self`
- `text`: `str`
- `bank_type`: `Optional[BankType]`

**Retour**: `Optional[str]`

---

### `extract_pdf_text`

**Fichier**: `core/bank_import/extractor.py:414`

```python
def extract_pdf_text(pdf_path: Path) -> str:
```

Convenience function to extract PDF text.

**Paramètres**:
- `pdf_path`: `Path`

**Retour**: `str`

---

### `parse`

**Fichier**: `core/bank_import/parser.py:50`

```python
def parse( self, lines: List[str],
```

Analyse les lignes du relevé en données structurées.

**Paramètres**:
- `self`
- `lines`: `List[str]`
- `period`: `StatementPeriod`

**Retour**: `ParsedStatement`

---

### `parse`

**Fichier**: `core/bank_import/parser.py:110`

```python
def parse( self, lines: List[str],
```

Analyse les lignes du relevé en données structurées.

**Paramètres**:
- `self`
- `lines`: `List[str]`
- `period`: `StatementPeriod`

**Retour**: `ParsedStatement`

---

## Finance (90)

### `__init__`

**Fichier**: `core/finance/analytic_accounting.py:76`

```python
def __init__(self, tenant_id: int):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

---

### `__init__`

**Fichier**: `core/finance/anomaly_detection.py:81`

```python
def __init__(self, tenant_id: int):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

---

### `__init__`

**Fichier**: `core/finance/audit_trail.py:233`

```python
def __init__(self, db_pool=None, retention_days: int = 365):
```

**Paramètres**:
- `self`
- `db_pool`
- `retention_days`: `int`

---

### `__init__`

**Fichier**: `core/finance/bank_reconciliation.py:83`

```python
def __init__(self, tenant_id: int):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

---

### `__init__`

**Fichier**: `core/finance/event_sourcing.py:343`

```python
def __init__(self, tenant_id: int, user_id: Optional[int] = None):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`
- `user_id`: `Optional[int]`

---

### `__init__`

**Fichier**: `core/finance/forecasting.py:80`

```python
def __init__(self, tenant_id: int):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

---

### `__init__`

**Fichier**: `core/finance/margin_calculator.py:96`

```python
def __init__(self, tenant_id: int):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

---

### `__init__`

**Fichier**: `core/finance/supplier_scoring.py:78`

```python
def __init__(self, tenant_id: int):
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

---

### `_calculate_grade`

**Fichier**: `core/finance/supplier_scoring.py:493`

```python
def _calculate_grade(self, score: float) -> str:
```

Convertit un score en grade.

**Paramètres**:
- `self`
- `score`: `float`

**Retour**: `str`

---

### `_calculate_similarity`

**Fichier**: `core/finance/rules_engine.py:359`

```python
def _calculate_similarity(self, text: str, terms: List[str]) -> float:
```

Calcule un score de similarité fuzzy.

**Paramètres**:
- `self`
- `text`: `str`
- `terms`: `List[str]`

**Retour**: `float`

---

### `_calculate_supplier_match`

**Fichier**: `core/finance/bank_reconciliation.py:524`

```python
def _calculate_supplier_match( self, invoice_supplier: str,
```

Calcule le score de correspondance fournisseur.

**Paramètres**:
- `self`
- `invoice_supplier`: `str`
- `potential_suppliers`: `List[str]`
- `libelle`: `str`

**Retour**: `float`

---

### `_compute_invoice_signature`

**Fichier**: `core/finance/anomaly_detection.py:483`

```python
def _compute_invoice_signature(self, inv: Dict) -> str:
```

Calcule une signature unique pour détecter les doublons.

**Paramètres**:
- `self`
- `inv`: `Dict`

**Retour**: `str`

---

### `_dates_are_close`

**Fichier**: `core/finance/anomaly_detection.py:781`

```python
def _dates_are_close(self, date1: Any, date2: Any, days: int) -> bool:
```

Vérifie si deux dates sont proches.

**Paramètres**:
- `self`
- `date1`: `Any`
- `date2`: `Any`
- `days`: `int`

**Retour**: `bool`

---

### `_detect_trend`

**Fichier**: `core/finance/inventory_intelligence.py:298`

```python
def _detect_trend(self, demands: List[Decimal]) -> str:
```

Détecte la tendance via régression linéaire simple

**Paramètres**:
- `self`
- `demands`: `List[Decimal]`

**Retour**: `str`

---

### `_detect_type`

**Fichier**: `core/finance/audit_trail.py:473`

```python
def _detect_type(self, value: Any) -> str:
```

Détecte le type d'une valeur

**Paramètres**:
- `self`
- `value`: `Any`

**Retour**: `str`

---

### `_empty_forecast`

**Fichier**: `core/finance/forecasting.py:773`

```python
def _empty_forecast( self, forecast_type: ForecastType,
```

Prévision vide.

**Paramètres**:
- `self`
- `forecast_type`: `ForecastType`
- `entity_id`: `Optional[int]`
- `entity_name`: `str`
- `horizon`: `int`

**Retour**: `ForecastResult`

---

### `_get_price_history`

**Fichier**: `core/finance/forecasting.py:462`

```python
def _get_price_history(self, product_id: int, days: int) -> List[Dict[str, Any]]:
```

Récupère l'historique des prix.

**Paramètres**:
- `self`
- `product_id`: `int`
- `days`: `int`

**Retour**: `List[Dict[str, Any]]`

---

### `_get_total_revenue`

**Fichier**: `core/finance/margin_calculator.py:628`

```python
def _get_total_revenue(self, period_start: date, period_end: date) -> float:
```

Récupère le CA total sur la période.

**Paramètres**:
- `self`
- `period_start`: `date`
- `period_end`: `date`

**Retour**: `float`

---

### `_is_suspicious_round_amount`

**Fichier**: `core/finance/anomaly_detection.py:364`

```python
def _is_suspicious_round_amount(self, amount: float) -> bool:
```

Vérifie si un montant est suspecteusement rond.

**Paramètres**:
- `self`
- `amount`: `float`

**Retour**: `bool`

---

### `_is_unusual_time`

**Fichier**: `core/finance/anomaly_detection.py:377`

```python
def _is_unusual_time(self, tx_date: Any) -> bool:
```

Vérifie si l'heure est inhabituelle.

**Paramètres**:
- `self`
- `tx_date`: `Any`

**Retour**: `bool`

---

### `_mask_sensitive`

**Fichier**: `core/finance/audit_trail.py:421`

```python
def _mask_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
```

Masque les champs sensibles

**Paramètres**:
- `self`
- `data`: `Dict[str, Any]`

**Retour**: `Dict[str, Any]`

---

### `_match_conditions`

**Fichier**: `core/finance/analytic_accounting.py:316`

```python
def _match_conditions(self, conditions: Dict, context: Dict) -> bool:
```

Vérifie si les conditions sont remplies.

**Paramètres**:
- `self`
- `conditions`: `Dict`
- `context`: `Dict`

**Retour**: `bool`

---

### `_search_buffer`

**Fichier**: `core/finance/audit_trail.py:637`

```python
def _search_buffer(self, criteria: AuditSearchCriteria) -> List[AuditEntry]:
```

Recherche dans le buffer mémoire

**Paramètres**:
- `self`
- `criteria`: `AuditSearchCriteria`

**Retour**: `List[AuditEntry]`

---

### `_validate_currency`

**Fichier**: `backend/schemas/finance.py:155`

```python
def _validate_currency(cls, value: str) -> str:
```

**Paramètres**:
- `cls`
- `value`: `str`

**Retour**: `str`

---

### `_validate_direction`

**Fichier**: `backend/schemas/finance.py:147`

```python
def _validate_direction(cls, value: str) -> str:
```

**Paramètres**:
- `cls`
- `value`: `str`

**Retour**: `str`

---

### `auto_categorize`

**Fichier**: `backend/services/finance_categorization.py:459`

```python
def auto_categorize(direction: str, label: str) -> Tuple[Optional[str], str]:
```

Categorise automatiquement une transaction.

**Paramètres**:
- `direction`: `str`
- `label`: `str`

**Retour**: `Tuple[Optional[str], str]`

---

### `bootstrap_default_axes`

**Fichier**: `core/finance/analytic_accounting.py:663`

```python
def bootstrap_default_axes(tenant_id: int):
```

Initialise les axes par défaut.

**Paramètres**:
- `tenant_id`: `int`

---

### `bootstrap_default_rules`

**Fichier**: `core/finance/rules_engine.py:765`

```python
def bootstrap_default_rules(tenant_id: int):
```

Initialise les règles par défaut pour un tenant.

**Paramètres**:
- `tenant_id`: `int`

---

### `canonical`

**Fichier**: `backend/services/finance_categorization.py:352`

```python
def canonical(label: str) -> str:
```

Forme canonique pour regrouper des libelles similaires.

**Paramètres**:
- `label`: `str`

**Retour**: `str`

---

### `classify_batch`

**Fichier**: `core/finance/rules_engine.py:474`

```python
def classify_batch( self, transactions: List[Dict[str, Any]]
```

Classifie un lot de transactions.

**Paramètres**:
- `self`
- `transactions`: `List[Dict[str, Any]]`

**Retour**: `List[ClassificationResult]`

---

### `create_account`

**Fichier**: `backend/services/finance/accounts.py:24`

```python
def create_account(payload: FinanceAccountCreate) -> dict[str, Any]:
```

Crée un compte financier en validant la cohérence devise/entité.

**Paramètres**:
- `payload`: `FinanceAccountCreate`

**Retour**: `dict[str, Any]`

---

### `create_audit_trail`

**Fichier**: `core/finance/audit_trail.py:1083`

```python
def create_audit_trail(db_pool=None, retention_days: int = 365) -> AuditTrail:
```

Factory function pour créer un AuditTrail

**Paramètres**:
- `db_pool`
- `retention_days`: `int`

**Retour**: `AuditTrail`

---

### `create_category`

**Fichier**: `backend/services/finance/categories.py:12`

```python
def create_category(entity_id: int, code: str, name: str, type_: str = "EXPENSE") -> dict:
```

Crée une nouvelle catégorie finance et la retourne.

**Paramètres**:
- `entity_id`: `int`
- `code`: `str`
- `name`: `str`
- `type_`: `str`

**Retour**: `dict`

---

### `create_cost_center`

**Fichier**: `backend/services/finance/cost_centers.py:12`

```python
def create_cost_center(entity_id: int, code: str, name: str) -> dict:
```

Crée un nouveau centre de coûts finance et le retourne.

**Paramètres**:
- `entity_id`: `int`
- `code`: `str`
- `name`: `str`

**Retour**: `dict`

---

### `create_inventory_intelligence`

**Fichier**: `core/finance/inventory_intelligence.py:1049`

```python
def create_inventory_intelligence(db_pool=None) -> InventoryIntelligence:
```

Factory function pour créer une instance

**Paramètres**:
- `db_pool`

**Retour**: `InventoryIntelligence`

---

### `create_payment`

**Fichier**: `backend/services/finance/invoices.py:201`

```python
def create_payment(payload: FinancePaymentCreate) -> dict[str, Any]:
```

**Paramètres**:
- `payload`: `FinancePaymentCreate`

**Retour**: `dict[str, Any]`

---

### `create_reconciliation`

**Fichier**: `backend/services/finance/reconciliation.py:12`

```python
def create_reconciliation( statement_line_id: int,
```

**Paramètres**:
- `statement_line_id`: `int`
- `transaction_id`: `int`

**Retour**: `dict[str, Any]`

---

### `create_rule`

**Fichier**: `backend/services/finance/rules.py:66`

```python
def create_rule(payload: FinanceRuleCreate) -> dict:
```

**Paramètres**:
- `payload`: `FinanceRuleCreate`

**Retour**: `dict`

---

### `create_vendor`

**Fichier**: `backend/services/finance/invoices.py:13`

```python
def create_vendor(payload: FinanceVendorCreate) -> dict[str, Any]:
```

**Paramètres**:
- `payload`: `FinanceVendorCreate`

**Retour**: `dict[str, Any]`

---

### `delete_account`

**Fichier**: `backend/services/finance/accounts.py:152`

```python
def delete_account(account_id: int) -> bool:
```

Supprime un compte financier (soft delete via is_active=false, ou hard delete si pas de données).

**Paramètres**:
- `account_id`: `int`

**Retour**: `bool`

---

### `delete_reconciliation`

**Fichier**: `backend/services/finance/reconciliation.py:46`

```python
def delete_reconciliation(reconciliation_id: int) -> None:
```

**Paramètres**:
- `reconciliation_id`: `int`

**Retour**: `None`

---

### `delete_rule`

**Fichier**: `backend/services/finance/rules.py:118`

```python
def delete_rule(rule_id: int) -> dict:
```

**Paramètres**:
- `rule_id`: `int`

**Retour**: `dict`

---

### `detect_from_history`

**Fichier**: `core/finance/anomaly_detection.py:236`

```python
def detect_from_history(self, period_days: int = 30) -> List[DetectedAnomaly]:
```

Détecte les anomalies basées sur l'historique DB.

**Paramètres**:
- `self`
- `period_days`: `int`

**Retour**: `List[DetectedAnomaly]`

---

### `emit_bank_transaction_categorized`

**Fichier**: `core/finance/event_sourcing.py:471`

```python
def emit_bank_transaction_categorized( tenant_id: int,
```

Émet un événement de catégorisation de transaction.

**Paramètres**:
- `tenant_id`: `int`
- `transaction_id`: `str`
- `category`: `str`
- `confidence`: `float`
- `method`: `str`
- `user_id`: `Optional[int]`

**Retour**: `Event`

---

### `emit_invoice_imported`

**Fichier**: `core/finance/event_sourcing.py:396`

```python
def emit_invoice_imported( tenant_id: int,
```

Émet un événement d'import de facture.

**Paramètres**:
- `tenant_id`: `int`
- `invoice_id`: `str`
- `filename`: `str`
- `supplier`: `str`
- `total`: `float`
- `items_count`: `int`
- `user_id`: `Optional[int]`

**Retour**: `Event`

---

### `emit_price_updated`

**Fichier**: `core/finance/event_sourcing.py:420`

```python
def emit_price_updated( tenant_id: int,
```

Émet un événement de mise à jour de prix.

**Paramètres**:
- `tenant_id`: `int`
- `product_id`: `int`
- `old_price`: `float`
- `new_price`: `float`
- `supplier`: `str`
- `source`: `str`
- `user_id`: `Optional[int]`

**Retour**: `Event`

---

### `emit_stock_movement`

**Fichier**: `core/finance/event_sourcing.py:447`

```python
def emit_stock_movement( tenant_id: int,
```

Émet un événement de mouvement de stock.

**Paramètres**:
- `tenant_id`: `int`
- `product_id`: `int`
- `movement_type`: `str`
- `quantity`: `float`
- `reason`: `str`
- `reference`: `Optional[str]`
- `user_id`: `Optional[int]`

**Retour**: `Event`

---

### `export_user_data`

**Fichier**: `core/finance/audit_trail.py:934`

```python
async def export_user_data(self, user_id: int, tenant_id: int) -> List[Dict[str, Any]]:
```

Exporte toutes les données d'audit d'un utilisateur (RGPD)

**Paramètres**:
- `self`
- `user_id`: `int`
- `tenant_id`: `int`

**Retour**: `List[Dict[str, Any]]`

---

### `fetch_matches`

**Fichier**: `core/finance/reconciliation.py:515`

```python
def fetch_matches(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
```

Return reconciliation matches for manual review.

**Paramètres**:
- `tenant_id`: `int`
- `status`: `str | None`

**Retour**: `list[dict[str, Any]]`

---

### `get_account`

**Fichier**: `backend/services/finance/accounts.py:101`

```python
def get_account(account_id: int) -> dict[str, Any] | None:
```

Récupère un compte par son ID.

**Paramètres**:
- `account_id`: `int`

**Retour**: `dict[str, Any] | None`

---

### `get_aggregate_history`

**Fichier**: `core/finance/event_sourcing.py:493`

```python
def get_aggregate_history( tenant_id: int,
```

Retourne l'historique complet d'un agrégat.

**Paramètres**:
- `tenant_id`: `int`
- `aggregate_type`: `str`
- `aggregate_id`: `str`

**Retour**: `List[Dict[str, Any]]`

---

### `get_entity_history`

**Fichier**: `core/finance/audit_trail.py:825`

```python
async def get_entity_history( self, entity: AuditEntity,
```

Récupère l'historique complet d'une entité

**Paramètres**:
- `self`
- `entity`: `AuditEntity`
- `entity_id`: `int`
- `tenant_id`: `Optional[int]`
- `limit`: `int`

**Retour**: `List[AuditEntry]`

---

### `get_latest_version`

**Fichier**: `core/finance/event_sourcing.py:297`

```python
def get_latest_version( self, aggregate_type: str,
```

Retourne la dernière version d'un agrégat.

**Paramètres**:
- `self`
- `aggregate_type`: `str`
- `aggregate_id`: `str`
- `tenant_id`: `int`

**Retour**: `int`

---

### `get_user_activity`

**Fichier**: `core/finance/audit_trail.py:841`

```python
async def get_user_activity( self, user_id: int,
```

Récupère l'activité d'un utilisateur

**Paramètres**:
- `self`
- `user_id`: `int`
- `tenant_id`: `Optional[int]`
- `start_date`: `Optional[datetime]`
- `limit`: `int`

**Retour**: `List[AuditEntry]`

---

### `import_summary`

**Fichier**: `backend/services/finance/stats.py:516`

```python
def import_summary( account_id: int | None = None,
```

Retourne le résumé des importations par compte et période.

**Paramètres**:
- `account_id`: `int | None`
- `months`: `int | None`

**Retour**: `List[dict]`

---

### `increment_import_progress`

**Fichier**: `backend/services/finance/metrics.py:23`

```python
def increment_import_progress(import_id: int, inserted: int, total: int) -> None:
```

**Paramètres**:
- `import_id`: `int`
- `inserted`: `int`
- `total`: `int`

**Retour**: `None`

---

### `infer_target_category`

**Fichier**: `backend/services/finance_categorization.py:406`

```python
def infer_target_category(category_name: str, entry_type: str = "Sortie") -> str:
```

Infere la categorie cible (taxonomie 12 postes) a partir d'un nom de categorie source.

**Paramètres**:
- `category_name`: `str`
- `entry_type`: `str`

**Retour**: `str`

---

### `list_accounts`

**Fichier**: `backend/services/finance/accounts.py:69`

```python
def list_accounts(entity_id: Optional[int] = None, is_active: Optional[bool] = None) -> list[dict[str, Any]]:
```

Liste les comptes avec filtres simples.

**Paramètres**:
- `entity_id`: `Optional[int]`
- `is_active`: `Optional[bool]`

**Retour**: `list[dict[str, Any]]`

---

### `list_anomalies`

**Fichier**: `backend/services/finance/core.py:62`

```python
def list_anomalies(tenant_id: int, severity: str | None = None) -> list[dict[str, Any]]:
```

Liste les anomalies référencées en base, filtrables par sévérité.

**Paramètres**:
- `tenant_id`: `int`
- `severity`: `str | None`

**Retour**: `list[dict[str, Any]]`

---

### `list_anomaly_flags`

**Fichier**: `core/finance/insights.py:297`

```python
def list_anomaly_flags(tenant_id: int, severity: str | None = None) -> list[dict[str, Any]]:
```

**Paramètres**:
- `tenant_id`: `int`
- `severity`: `str | None`

**Retour**: `list[dict[str, Any]]`

---

### `list_categories`

**Fichier**: `backend/services/finance/categories.py:30`

```python
def list_categories(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
```

Retourne les catégories finance disponibles, optionnellement filtrées.

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`

**Retour**: `List[dict]`

---

### `list_cost_centers`

**Fichier**: `backend/services/finance/cost_centers.py:30`

```python
def list_cost_centers(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
```

Retourne les centres de coûts finance disponibles, optionnellement filtrés.

**Paramètres**:
- `entity_id`: `int | None`
- `is_active`: `bool | None`

**Retour**: `List[dict]`

---

### `list_matches`

**Fichier**: `backend/services/finance/core.py:28`

```python
def list_matches(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
```

Expose les correspondances relevés/factures générées par le job de rapprochement.

**Paramètres**:
- `tenant_id`: `int`
- `status`: `str | None`

**Retour**: `list[dict[str, Any]]`

---

### `list_recurring`

**Fichier**: `backend/services/finance/core.py:46`

```python
def list_recurring(tenant_id: int) -> list[dict[str, Any]]:
```

Retourne les dépenses identifiées comme récurrentes.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `list[dict[str, Any]]`

---

### `list_recurring_expenses`

**Fichier**: `core/finance/insights.py:272`

```python
def list_recurring_expenses(tenant_id: int) -> list[dict[str, Any]]:
```

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `list[dict[str, Any]]`

---

### `list_vendors`

**Fichier**: `backend/services/finance/invoices.py:48`

```python
def list_vendors(entity_id: Optional[int] = None, is_active: Optional[bool] = None) -> list[dict[str, Any]]:
```

**Paramètres**:
- `entity_id`: `Optional[int]`
- `is_active`: `Optional[bool]`

**Retour**: `list[dict[str, Any]]`

---

### `lock_transaction`

**Fichier**: `backend/services/finance/transactions.py:227`

```python
def lock_transaction(transaction_id: int) -> dict[str, Any]:
```

Verrouille une transaction après rapprochement.

**Paramètres**:
- `transaction_id`: `int`

**Retour**: `dict[str, Any]`

---

### `log_update`

**Fichier**: `core/finance/audit_trail.py:327`

```python
async def log_update( self, entity: AuditEntity,
```

Shortcut pour mise à jour

**Paramètres**:
- `self`
- `entity`: `AuditEntity`
- `entity_id`: `int`
- `before`: `Dict[str, Any]`
- `after`: `Dict[str, Any]`
- `context`: `AuditContext`
- `entity_name`: `Optional[str]`

**Retour**: `AuditEntry`

---

### `match_category_rules`

**Fichier**: `backend/services/finance_categorization.py:377`

```python
def match_category_rules( direction: str,
```

Applique les regles de categorisation sur un libelle.

**Paramètres**:
- `direction`: `str`
- `label`: `str`
- `rules`: `Tuple[Tuple[Tuple[str, ...], str, Tuple[str, ...] | None], ...]`

**Retour**: `Optional[str]`

---

### `normalize_label`

**Fichier**: `backend/services/finance_categorization.py:332`

```python
def normalize_label(label: str) -> str:
```

Normalisation legere : upper + espaces condenses.

**Paramètres**:
- `label`: `str`

**Retour**: `str`

---

### `reconciliation_dashboard`

**Fichier**: `backend/services/finance/stats.py:566`

```python
def reconciliation_dashboard(entity_id: int | None = None) -> List[dict]:
```

Retourne le dashboard de rapprochement par compte.

**Paramètres**:
- `entity_id`: `int | None`

**Retour**: `List[dict]`

---

### `record_import`

**Fichier**: `backend/services/finance/rules.py:132`

```python
def record_import(account_id: int, file_name: str, summary: dict | None, error: str | None) -> None:
```

Enregistre un import (succès/échec) dans finance_imports.

**Paramètres**:
- `account_id`: `int`
- `file_name`: `str`
- `summary`: `dict | None`
- `error`: `str | None`

**Retour**: `None`

---

### `record_import_metrics`

**Fichier**: `backend/services/finance/metrics.py:19`

```python
def record_import_metrics(account_id: int, inserted: int | None, total: int | None, status: str, error: str | None) -> None:
```

**Paramètres**:
- `account_id`: `int`
- `inserted`: `int | None`
- `total`: `int | None`
- `status`: `str`
- `error`: `str | None`

**Retour**: `None`

---

### `record_reco_run`

**Fichier**: `backend/services/finance/metrics.py:15`

```python
def record_reco_run(summary: Dict[str, Any]) -> None:
```

**Paramètres**:
- `summary`: `Dict[str, Any]`

**Retour**: `None`

---

### `refresh_anomalies`

**Fichier**: `backend/services/finance/core.py:52`

```python
def refresh_anomalies(tenant_id: int, *, zscore_threshold: float = 2.5, min_occurrences: int = 3) -> dict[str, Any]:
```

Marque les anomalies de dépenses via détection statistique (z-score).

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `dict[str, Any]`

---

### `refresh_materialized_views`

**Fichier**: `backend/services/finance/stats.py:163`

```python
def refresh_materialized_views() -> dict:
```

Rafraîchit les vues matérialisées de stats finance.

**Retour**: `dict`

---

### `refresh_recurring`

**Fichier**: `backend/services/finance/core.py:40`

```python
def refresh_recurring(tenant_id: int, *, min_occurrences: int = 3) -> dict[str, Any]:
```

Recalcule les dépenses récurrentes à partir des relevés existants.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `dict[str, Any]`

---

### `refresh_single_view`

**Fichier**: `backend/services/finance/views.py:80`

```python
def refresh_single_view(view_name: str, concurrent: bool = True) -> RefreshResult:
```

Rafraîchit une seule vue matérialisée.

**Paramètres**:
- `view_name`: `str`
- `concurrent`: `bool`

**Retour**: `RefreshResult`

---

### `replay`

**Fichier**: `core/finance/event_sourcing.py:376`

```python
def replay( self, aggregate_type: str,
```

Rejoue tous les événements pour reconstruire l'état.

**Paramètres**:
- `self`
- `aggregate_type`: `str`
- `aggregate_id`: `str`
- `projector`: `Callable[[Any, Event], Any]`
- `initial_state`: `Any`

**Retour**: `Any`

---

### `run_reconciliation`

**Fichier**: `backend/services/finance/core.py:11`

```python
def run_reconciliation( tenant_id: int,
```

Lance le job de rapprochement en configurant les marges de tolérance.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `dict[str, Any]`

---

### `stem_label`

**Fichier**: `backend/services/finance_categorization.py:339`

```python
def stem_label(label: str) -> str:
```

Forme tronquee pour regrouper les variantes (dates, montants, refs numeriques).

**Paramètres**:
- `label`: `str`

**Retour**: `str`

---

### `strip_accents`

**Fichier**: `backend/services/finance_categorization.py:324`

```python
def strip_accents(text: str) -> str:
```

Supprime les accents d'une chaine.

**Paramètres**:
- `text`: `str`

**Retour**: `str`

---

### `subscribe`

**Fichier**: `core/finance/event_sourcing.py:323`

```python
def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
```

Abonne un handler à un type d'événement.

**Paramètres**:
- `self`
- `event_type`: `EventType`
- `handler`: `Callable[[Event], None]`

---

### `suggest_category`

**Fichier**: `backend/services/finance_categorization.py:506`

```python
def suggest_category(label: str) -> Optional[str]:
```

Suggere une categorie basee sur les mots-cles simples.

**Paramètres**:
- `label`: `str`

**Retour**: `Optional[str]`

---

### `update_account`

**Fichier**: `backend/services/finance/accounts.py:118`

```python
def update_account(account_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Met à jour un compte financier.

**Paramètres**:
- `account_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `update_import_progress`

**Fichier**: `backend/services/finance/imports.py:38`

```python
def update_import_progress(import_id: int, inserted: int, total: int | None = None, status: str | None = None) -> None:
```

**Paramètres**:
- `import_id`: `int`
- `inserted`: `int`
- `total`: `int | None`
- `status`: `str | None`

**Retour**: `None`

---

### `update_match_status`

**Fichier**: `backend/services/finance/core.py:34`

```python
def update_match_status(tenant_id: int, match_id: int, *, status: str, note: str | None = None) -> dict[str, Any]:
```

Met à jour le statut manuel d'une correspondance (validée, rejetée...).

**Paramètres**:
- `tenant_id`: `int`
- `match_id`: `int`

**Retour**: `dict[str, Any]`

---

### `update_match_status`

**Fichier**: `core/finance/reconciliation.py:562`

```python
def update_match_status(tenant_id: int, match_id: int, *, status: str, note: str | None = None) -> dict[str, Any]:
```

**Paramètres**:
- `tenant_id`: `int`
- `match_id`: `int`

**Retour**: `dict[str, Any]`

---

### `update_rule`

**Fichier**: `backend/services/finance/rules.py:92`

```python
def update_rule(rule_id: int, fields: Dict[str, Any]) -> dict:
```

**Paramètres**:
- `rule_id`: `int`
- `fields`: `Dict[str, Any]`

**Retour**: `dict`

---

### `update_transaction`

**Fichier**: `backend/services/finance/transactions.py:194`

```python
def update_transaction(transaction_id: int, payload: FinanceTransactionUpdate) -> dict[str, Any]:
```

Mise à jour note/statut si la transaction n'est pas verrouillée.

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `FinanceTransactionUpdate`

**Retour**: `dict[str, Any]`

---

## Formatting (6)

### `parse_eurociel`

**Fichier**: `core/parsers/__init__.py:105`

```python
def parse_eurociel(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

**Paramètres**:
- `text`: `str`
- `margin_rate`: `float`
- `start_sequence`: `int`

**Retour**: `pd.DataFrame`

---

### `parse_invoice`

**Fichier**: `core/parsers/__init__.py:130`

```python
def parse_invoice(text: str, supplier_hint: str | None, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

**Paramètres**:
- `text`: `str`
- `supplier_hint`: `str | None`
- `margin_rate`: `float`
- `start_sequence`: `int`

**Retour**: `pd.DataFrame`

---

### `parse_lcl_statement`

**Fichier**: `core/bank_import/parser.py:972`

```python
def parse_lcl_statement( lines: List[str],
```

Fonction utilitaire pour parser un relevé LCL.

**Paramètres**:
- `lines`: `List[str]`
- `period`: `StatementPeriod`

**Retour**: `ParsedStatement`

---

### `parse_metro`

**Fichier**: `core/parsers/__init__.py:96`

```python
def parse_metro(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

**Paramètres**:
- `text`: `str`
- `margin_rate`: `float`
- `start_sequence`: `int`

**Retour**: `pd.DataFrame`

---

### `parse_statement`

**Fichier**: `core/bank_import/parser.py:1176`

```python
def parse_statement( lines: List[str],
```

Fonction utilitaire pour parser un relevé.

**Paramètres**:
- `lines`: `List[str]`
- `period`: `StatementPeriod`
- `bank_type`: `BankType`

**Retour**: `ParsedStatement`

---

### `parse_taiyat`

**Fichier**: `core/parsers/__init__.py:114`

```python
def parse_taiyat(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

**Paramètres**:
- `text`: `str`
- `margin_rate`: `float`
- `start_sequence`: `int`

**Retour**: `pd.DataFrame`

---

## General (43)

### `__init__`

**Fichier**: `core/bank_import/extractor.py:90`

```python
def __init__(self, pdftotext_path: str = "pdftotext"):
```

**Paramètres**:
- `self`
- `pdftotext_path`: `str`

---

### `_analyze_field_coverage`

**Fichier**: `core/import_analyzer.py:243`

```python
def _analyze_field_coverage(self, df: pd.DataFrame, column: str) -> FieldCoverage:
```

Analyse la couverture d'un champ.

**Paramètres**:
- `self`
- `df`: `pd.DataFrame`
- `column`: `str`

**Retour**: `FieldCoverage`

---

### `_finalize_result`

**Fichier**: `core/bank_import/orchestrator.py:546`

```python
def _finalize_result(self, result: ImportResult) -> ImportResult:
```

Finalize import result.

**Paramètres**:
- `self`
- `result`: `ImportResult`

**Retour**: `ImportResult`

---

### `_is_header_line`

**Fichier**: `core/bank_import/parser.py:940`

```python
def _is_header_line(self, line: str) -> bool:
```

Vérifie si la ligne correspond à un en-tête ou des métadonnées.

**Paramètres**:
- `self`
- `line`: `str`

**Retour**: `bool`

---

### `_is_transaction_line`

**Fichier**: `core/bank_import/USAGE_EXAMPLES.py:149`

```python
def _is_transaction_line(self, line: str) -> bool:
```

Vérifie si une ligne est une transaction.

**Paramètres**:
- `self`
- `line`: `str`

**Retour**: `bool`

---

### `_similar_libelle`

**Fichier**: `core/bank_import/deduplicator.py:302`

```python
def _similar_libelle(self, lib1: str, lib2: str) -> bool:
```

Check if two libelles are similar.

**Paramètres**:
- `self`
- `lib1`: `str`
- `lib2`: `str`

**Retour**: `bool`

---

### `_split_pages`

**Fichier**: `core/bank_import/extractor.py:299`

```python
def _split_pages(self, lines: List[str]) -> List[ExtractedPage]:
```

Split text into pages based on form feed characters.

**Paramètres**:
- `self`
- `lines`: `List[str]`

**Retour**: `List[ExtractedPage]`

---

### `_strip_name`

**Fichier**: `backend/main.py:88`

```python
def _strip_name(cls, value: str | None) -> str | None:
```

**Paramètres**:
- `cls`
- `value`: `str | None`

**Retour**: `str | None`

---

### `analyze_bank_import`

**Fichier**: `core/import_analyzer.py:410`

```python
def analyze_bank_import( df: pd.DataFrame,
```

Fonction helper pour analyser un import bancaire.

**Paramètres**:
- `df`: `pd.DataFrame`
- `source_file`: `str`
- `categorizer_func`

**Retour**: `ImportAnalysisReport`

---

### `analyze_bank_transactions`

**Fichier**: `core/import_analyzer.py:204`

```python
def analyze_bank_transactions( self, df: pd.DataFrame,
```

Analyse des transactions bancaires avec catégorisation.

**Paramètres**:
- `self`
- `df`: `pd.DataFrame`
- `source_file`: `str`
- `categorizer_func`

**Retour**: `ImportAnalysisReport`

---

### `analyze_invoice_import`

**Fichier**: `core/import_analyzer.py:388`

```python
def analyze_invoice_import( df: pd.DataFrame,
```

Fonction helper pour analyser un import de facture.

**Paramètres**:
- `df`: `pd.DataFrame`
- `source_file`: `str`

**Retour**: `ImportAnalysisReport`

---

### `build_backup_timeline`

**Fichier**: `core/backup_manager.py:281`

```python
def build_backup_timeline(backups: Iterable[BackupMetadata]) -> List[dict]:
```

Retourne une timeline sérialisable pour les visualisations.

**Paramètres**:
- `backups`: `Iterable[BackupMetadata]`

**Retour**: `List[dict]`

---

### `build_keyword_index`

**Fichier**: `core/bank_import/categories.py:327`

```python
def build_keyword_index() -> Dict[str, str]:
```

Build a keyword -> category_code index.

**Retour**: `Dict[str, str]`

---

### `can_parse`

**Fichier**: `core/bank_import/parser.py:258`

```python
def can_parse(self, text: str) -> bool:
```

Check if this parser can handle the given text.

**Paramètres**:
- `self`
- `text`: `str`

**Retour**: `bool`

---

### `categorize_transaction`

**Fichier**: `core/bank_import/categorizer.py:560`

```python
def categorize_transaction(libelle: str, direction: str = "OUT") -> str:
```

Convenience function to categorize a single transaction.

**Paramètres**:
- `libelle`: `str`
- `direction`: `str`

**Retour**: `str`

---

### `deduplicate_in_memory`

**Fichier**: `core/bank_import/deduplicator.py:211`

```python
def deduplicate_in_memory( self, transactions: List[ParsedTransaction],
```

Deduplicate against a provided set of checksums.

**Paramètres**:
- `self`
- `transactions`: `List[ParsedTransaction]`
- `existing_checksums`: `Set[str]`

**Retour**: `DeduplicationResult`

---

### `deduplicate_transactions`

**Fichier**: `core/bank_import/deduplicator.py:332`

```python
def deduplicate_transactions( transactions: List[ParsedTransaction],
```

Convenience function for deduplication.

**Paramètres**:
- `transactions`: `List[ParsedTransaction]`
- `existing_checksums`: `Set[str]`

**Retour**: `Tuple[List[ParsedTransaction], List[ParsedTransaction]]`

---

### `determine_categorie`

**Fichier**: `core/products_loader.py:312`

```python
def determine_categorie(nom_produit: Any, fournisseur: str | None = None, code: str | None = None) -> str:
```

Détermine la catégorie METRO à partir du nom, fournisseur ou code du produit.

**Paramètres**:
- `nom_produit`: `Any`
- `fournisseur`: `str | None`
- `code`: `str | None`

**Retour**: `str`

---

### `enforce_default_rbac`

**Fichier**: `backend/dependencies/security.py:319`

```python
async def enforce_default_rbac(request: Request) -> AuthenticatedUser:
```

Autorise toute personne authentifiée à lire ; managers/admins pour modifier.

**Paramètres**:
- `request`: `Request`

**Retour**: `AuthenticatedUser`

---

### `exec_sql`

**Fichier**: `core/data_repository.py:80`

```python
def exec_sql(sql: str | ClauseElement, params=None) -> None:
```

Exécute une requête d'écriture (INSERT, UPDATE, DELETE).

**Paramètres**:
- `sql`: `str | ClauseElement`
- `params`

**Retour**: `None`

---

### `exec_sql_return_id`

**Fichier**: `core/data_repository.py:97`

```python
def exec_sql_return_id(sql: str | ClauseElement, params=None):
```

Exécute une requête et retourne l'ID (via RETURNING id).

**Paramètres**:
- `sql`: `str | ClauseElement`
- `params`

---

### `find_product`

**Fichier**: `core/catalog_repository.py:20`

```python
def find_product(self, identifier: str | int, tenant_id: int) -> ProductSummary | None:
```

**Paramètres**:
- `self`
- `identifier`: `str | int`
- `tenant_id`: `int`

**Retour**: `ProductSummary | None`

---

### `find_product`

**Fichier**: `core/catalog_sql_repository.py:32`

```python
def find_product(self, identifier: str | int, tenant_id: int) -> ProductSummary | None:
```

**Paramètres**:
- `self`
- `identifier`: `str | int`
- `tenant_id`: `int`

**Retour**: `ProductSummary | None`

---

### `from_row`

**Fichier**: `core/product_input.py:33`

```python
def from_row(row: Dict[str, Any]) -> ProductInput:
```

**Paramètres**:
- `row`: `Dict[str, Any]`

**Retour**: `ProductInput`

---

### `generate_checksum`

**Fichier**: `core/bank_import/deduplicator.py:49`

```python
def generate_checksum(self, txn: ParsedTransaction) -> str:
```

Generate a unique checksum for a transaction.

**Paramètres**:
- `self`
- `txn`: `ParsedTransaction`

**Retour**: `str`

---

### `handle_bank_transaction_categorized`

**Fichier**: `core/event_handlers.py:291`

```python
def handle_bank_transaction_categorized(event: Event):
```

Handler: Transaction bancaire catégorisée

**Paramètres**:
- `event`: `Event`

---

### `handle_reconciliation_matched`

**Fichier**: `core/event_handlers.py:310`

```python
def handle_reconciliation_matched(event: Event):
```

Handler: Rapprochement bancaire réussi

**Paramètres**:
- `event`: `Event`

---

### `integrity_report`

**Fichier**: `core/backup_manager.py:407`

```python
def integrity_report(backups: Iterable[BackupMetadata]) -> List[dict]:
```

Retourne l'état d'intégrité pour chaque sauvegarde fournie.

**Paramètres**:
- `backups`: `Iterable[BackupMetadata]`

**Retour**: `List[dict]`

---

### `inventory_summary`

**Fichier**: `backend/main.py:431`

```python
def inventory_summary(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, float]:
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `dict[str, float]`

---

### `is_near_duplicate`

**Fichier**: `core/bank_import/deduplicator.py:281`

```python
def is_near_duplicate(self, txn: ParsedTransaction) -> bool:
```

Check if transaction is a near-duplicate.

**Paramètres**:
- `self`
- `txn`: `ParsedTransaction`

**Retour**: `bool`

---

### `list_active_products`

**Fichier**: `core/catalog_repository.py:17`

```python
def list_active_products(self, tenant_id: int) -> list[ProductSummary]:
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

**Retour**: `list[ProductSummary]`

---

### `list_active_products`

**Fichier**: `core/catalog_sql_repository.py:11`

```python
def list_active_products(self, tenant_id: int) -> list[ProductSummary]:
```

**Paramètres**:
- `self`
- `tenant_id`: `int`

**Retour**: `list[ProductSummary]`

---

### `list_products`

**Fichier**: `backend/main.py:427`

```python
def list_products(tenant: Tenant = Depends(get_current_tenant)) -> list[ProductPayload]:
```

**Paramètres**:
- `tenant`: `Tenant`

**Retour**: `list[ProductPayload]`

---

### `overlaps`

**Fichier**: `core/bank_import/models.py:57`

```python
def overlaps(self, other: "StatementPeriod") -> bool:
```

Check if this period overlaps with another.

**Paramètres**:
- `self`
- `other`: `'StatementPeriod'`

**Retour**: `bool`

---

### `plan_next_backup`

**Fichier**: `core/backup_manager.py:342`

```python
def plan_next_backup( settings: Dict[str, object],
```

Calcule la prochaine sauvegarde planifiée en horaire local.

**Paramètres**:
- `settings`: `Dict[str, object]`

**Retour**: `Optional[datetime]`

---

### `process_products_file`

**Fichier**: `core/products_loader.py:957`

```python
def process_products_file(csv_path: str) -> Dict[str, Any]:
```

Lit un fichier CSV puis délègue le traitement à :func:`load_products_from_df`.

**Paramètres**:
- `csv_path`: `str`

**Retour**: `Dict[str, Any]`

---

### `query_df`

**Fichier**: `core/data_repository.py:44`

```python
def query_df(sql: str | ClauseElement, params=None) -> pd.DataFrame:
```

Exécute une requête SELECT et retourne le résultat sous forme de DataFrame Pandas.

**Paramètres**:
- `sql`: `str | ClauseElement`
- `params`

**Retour**: `pd.DataFrame`

---

### `quick_check`

**Fichier**: `core/bank_import/validator.py:177`

```python
def quick_check(self, statement: ParsedStatement) -> bool:
```

Quick validation check without detailed results.

**Paramètres**:
- `self`
- `statement`: `ParsedStatement`

**Retour**: `bool`

---

### `record_categorization_feedback`

**Fichier**: `core/bank_import/categorizer.py:433`

```python
def record_categorization_feedback( transaction_id: int,
```

Record a categorization correction for ML learning.

**Paramètres**:
- `transaction_id`: `int`
- `predicted_category_id`: `Optional[int]`
- `actual_category_id`: `int`
- `confidence_score`: `Optional[float]`
- `user_id`: `Optional[int]`
- `correction_source`: `str`

**Retour**: `int`

---

### `register`

**Fichier**: `core/bank_import/parser.py:1142`

```python
def register(self, bank_type: BankType, parser_class: type) -> None:
```

Enregistre une classe de parseur pour un type de banque.

**Paramètres**:
- `self`
- `bank_type`: `BankType`
- `parser_class`: `type`

**Retour**: `None`

---

### `require_user`

**Fichier**: `backend/dependencies/security.py:298`

```python
async def require_user(request: Request) -> AuthenticatedUser:
```

Récupère l'utilisateur courant depuis le cookie HTTP-Only.

**Paramètres**:
- `request`: `Request`

**Retour**: `AuthenticatedUser`

---

### `resolve_tenant`

**Fichier**: `backend/dependencies/tenant.py:67`

```python
def resolve_tenant(identifier: Optional[str | int]) -> Tenant | None:
```

**Paramètres**:
- `identifier`: `Optional[str | int]`

**Retour**: `Tenant | None`

---

### `to_json`

**Fichier**: `core/import_analyzer.py:86`

```python
def to_json(self, indent: int = 2) -> str:
```

**Paramètres**:
- `self`
- `indent`: `int`

**Retour**: `str`

---

## Invoicing (16)

### `batch_import_invoices`

**Fichier**: `backend/tasks/invoices.py:22`

```python
def batch_import_invoices(self, file_path: str, tenant_id: int):
```

Importe des factures depuis un fichier batch.

**Paramètres**:
- `self`
- `file_path`: `str`
- `tenant_id`: `int`

---

### `detect_invoice_format`

**Fichier**: `core/invoice_extractor.py:109`

```python
def detect_invoice_format(raw_text: str, supplier_hint: str | None = None) -> str:
```

Détermine le parseur à utiliser selon le hint ou des heuristiques.

**Paramètres**:
- `raw_text`: `str`
- `supplier_hint`: `str | None`

**Retour**: `str`

---

### `detect_supplier_from_invoice`

**Fichier**: `backend/services/invoices.py:67`

```python
def detect_supplier_from_invoice(invoice_df: pd.DataFrame, raw_text: str | None = None) -> str:
```

Détecte automatiquement le fournisseur à partir des données de facture.

**Paramètres**:
- `invoice_df`: `pd.DataFrame`
- `raw_text`: `str | None`

**Retour**: `str`

---

### `extract_invoice_lines`

**Fichier**: `backend/services/invoices.py:132`

```python
def extract_invoice_lines( text: str,
```

Extrait des lignes structurées depuis le texte brut d'une facture.

**Paramètres**:
- `text`: `str`

**Retour**: `pd.DataFrame`

---

### `extract_products`

**Fichier**: `core/invoice_extractor.py:134`

```python
def extract_products( raw_product_text: str,
```

Route vers le parseur détecté (fallback générique).

**Paramètres**:
- `raw_product_text`: `str`

**Retour**: `pd.DataFrame`

---

### `extract_products_from_generic_invoice`

**Fichier**: `core/invoice_extractor.py:935`

```python
def extract_products_from_generic_invoice( raw_product_text: str,
```

Parseur générique - fallback vers le parseur Metro en attendant d'autres formats.

**Paramètres**:
- `raw_product_text`: `str`

**Retour**: `pd.DataFrame`

---

### `extract_products_from_pomona_invoice`

**Fichier**: `core/invoice_extractor.py:948`

```python
def extract_products_from_pomona_invoice(raw_product_text: str, *, margin_rate: float = 0.0, start_invoice_sequence: int = 0) -> pd.DataFrame:
```

Prétraitement Pomona (numerotation différente, colonnes séparées par tab).

**Paramètres**:
- `raw_product_text`: `str`

**Retour**: `pd.DataFrame`

---

### `extract_products_from_transgourmet_invoice`

**Fichier**: `core/invoice_extractor.py:956`

```python
def extract_products_from_transgourmet_invoice(raw_product_text: str, *, margin_rate: float = 0.0, start_invoice_sequence: int = 0) -> pd.DataFrame:
```

Transgourmet : colonnes alignées, suffixes 'HT'. Enlève mentions spécifiques.

**Paramètres**:
- `raw_product_text`: `str`

**Retour**: `pd.DataFrame`

---

### `find_processed_invoice_ids`

**Fichier**: `backend/services/invoices.py:757`

```python
def find_processed_invoice_ids(invoice_ids: set[str], *, tenant_id: int) -> set[str]:
```

**Paramètres**:
- `invoice_ids`: `set[str]`

**Retour**: `set[str]`

---

### `get_invoice_workflow_summary`

**Fichier**: `core/invoice_workflow.py:442`

```python
def get_invoice_workflow_summary(tenant_id: int, days: int = 30) -> Dict[str, Any]:
```

Retourne un résumé des imports de factures récents.

**Paramètres**:
- `tenant_id`: `int`
- `days`: `int`

**Retour**: `Dict[str, Any]`

---

### `get_last_invoice_sequence`

**Fichier**: `backend/services/invoices.py:110`

```python
def get_last_invoice_sequence(tenant_id: int = 1) -> int:
```

Récupère le dernier numéro de séquence INV-XXX depuis la base.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `int`

---

### `persist_invoice_documents`

**Fichier**: `backend/services/invoices.py:806`

```python
def persist_invoice_documents(pdf_bytes: bytes, *, tenant_id: int, supplier: str | None = None) -> dict[str, dict[str, str]]:
```

Découpe et stocke physiquement chaque facture détectée.

**Paramètres**:
- `pdf_bytes`: `bytes`

**Retour**: `dict[str, dict[str, str]]`

---

### `prepare_invoice_dataframe`

**Fichier**: `backend/services/invoice_utils.py:8`

```python
def prepare_invoice_dataframe(source_df: pd.DataFrame, margin_rate: float) -> pd.DataFrame:
```

Normalise les colonnes numériques et calcule marges/totaux pour les lignes de facture.

**Paramètres**:
- `source_df`: `pd.DataFrame`
- `margin_rate`: `float`

**Retour**: `pd.DataFrame`

---

### `process_invoice`

**Fichier**: `backend/tasks/invoices.py:6`

```python
def process_invoice(self, invoice_id: int, tenant_id: int):
```

Traite une facture (OCR, parsing, validation).

**Paramètres**:
- `self`
- `invoice_id`: `int`
- `tenant_id`: `int`

---

### `record_processed_invoices`

**Fichier**: `backend/services/invoices.py:612`

```python
def record_processed_invoices(invoice_df: pd.DataFrame, *, supplier: str | None, tenant_id: int) -> None:
```

**Paramètres**:
- `invoice_df`: `pd.DataFrame`

**Retour**: `None`

---

### `register_invoice_parser`

**Fichier**: `core/invoice_extractor.py:101`

```python
def register_invoice_parser(name: str, handler: Callable[..., pd.DataFrame]) -> None:
```

Expose un parseur supplémentaire (permet d'ajouter d'autres fournisseurs).

**Paramètres**:
- `name`: `str`
- `handler`: `Callable[..., pd.DataFrame]`

**Retour**: `None`

---

## Middleware (25)

### `__init__`

**Fichier**: `backend/middleware/performance.py:81`

```python
def __init__( self, failure_threshold: int = 5,
```

**Paramètres**:
- `self`
- `failure_threshold`: `int`
- `recovery_timeout`: `float`
- `success_threshold`: `int`

---

### `__init__`

**Fichier**: `backend/middleware/rate_limiter.py:58`

```python
def __init__(self, config: RateLimitConfig | None = None):
```

**Paramètres**:
- `self`
- `config`: `RateLimitConfig | None`

---

### `__init__`

**Fichier**: `backend/middleware/rate_limiter.py:235`

```python
def __init__( self, app, requests: int = 1000,
```

**Paramètres**:
- `self`
- `app`
- `requests`: `int`
- `window`: `int`
- `burst`: `int`
- `exclude_paths`: `list[str] | None`

---

### `_apply_cache_control`

**Fichier**: `backend/middleware/performance.py:233`

```python
def _apply_cache_control(self, response: Response, path: str) -> None:
```

Applique le Cache-Control approprié.

**Paramètres**:
- `self`
- `response`: `Response`
- `path`: `str`

**Retour**: `None`

---

### `_build_cache_key`

**Fichier**: `backend/middleware/idempotency.py:174`

```python
def _build_cache_key( self, idempotency_key: str,
```

Construit une clé de cache unique pour la requête idempotente.

**Paramètres**:
- `self`
- `idempotency_key`: `str`
- `path`: `str`
- `method`: `str`
- `tenant_id`: `Optional[int]`

**Retour**: `str`

---

### `_cleanup_expired`

**Fichier**: `backend/middleware/rate_limiter.py:96`

```python
def _cleanup_expired(self, now: float) -> None:
```

Supprime les entrées expirées pour éviter la surcharge mémoire.

**Paramètres**:
- `self`
- `now`: `float`

**Retour**: `None`

---

### `_get_client_ip`

**Fichier**: `backend/middleware/request_context.py:158`

```python
def _get_client_ip(self, request: Request) -> str:
```

Extrait l'IP client en tenant compte des proxies.

**Paramètres**:
- `self`
- `request`: `Request`

**Retour**: `str`

---

### `_get_client_key`

**Fichier**: `backend/middleware/rate_limiter.py:69`

```python
def _get_client_key(self, request: Request) -> str:
```

Extrait l'identifiant client depuis la requête.

**Paramètres**:
- `self`
- `request`: `Request`

**Retour**: `str`

---

### `_is_already_wrapped`

**Fichier**: `backend/middleware/response_wrapper.py:203`

```python
def _is_already_wrapped(self, data: Any) -> bool:
```

Vérifie si la réponse est déjà au format standardisé.

**Paramètres**:
- `self`
- `data`: `Any`

**Retour**: `bool`

---

### `_log_request`

**Fichier**: `backend/middleware/request_context.py:165`

```python
def _log_request(self, metrics: RequestMetrics) -> None:
```

Log structuré de la requête.

**Paramètres**:
- `self`
- `metrics`: `RequestMetrics`

**Retour**: `None`

---

### `_normalize_path`

**Fichier**: `backend/middleware/performance.py:218`

```python
def _normalize_path(self, path: str) -> str:
```

Normalise le path pour le groupement (remplace IDs par :id).

**Paramètres**:
- `self`
- `path`: `str`

**Retour**: `str`

---

### `_refill_tokens`

**Fichier**: `backend/middleware/rate_limiter.py:84`

```python
def _refill_tokens(self, entry: RateLimitEntry, now: float) -> None:
```

Recharge les jetons selon le temps écoulé.

**Paramètres**:
- `self`
- `entry`: `RateLimitEntry`
- `now`: `float`

**Retour**: `None`

---

### `build_error_response`

**Fichier**: `backend/middleware/response_wrapper.py:80`

```python
def build_error_response( code: str,
```

Construit une réponse d'erreur standardisée.

**Paramètres**:
- `code`: `str`
- `message`: `str`

**Retour**: `dict[str, Any]`

---

### `build_success_response`

**Fichier**: `backend/middleware/response_wrapper.py:60`

```python
def build_success_response( data: Any,
```

Construit une réponse de succès standardisée.

**Paramètres**:
- `data`: `Any`

**Retour**: `dict[str, Any]`

---

### `from_status`

**Fichier**: `backend/middleware/response_wrapper.py:43`

```python
def from_status(cls, status_code: int) -> tuple[str, str, str]:
```

Mappe un code HTTP vers un code d'erreur.

**Paramètres**:
- `cls`
- `status_code`: `int`

**Retour**: `tuple[str, str, str]`

---

### `get_elapsed_ms`

**Fichier**: `backend/middleware/request_context.py:67`

```python
def get_elapsed_ms() -> float:
```

Retourne le temps écoulé depuis le début de la requête.

**Retour**: `float`

---

### `get_idempotency_status`

**Fichier**: `backend/middleware/idempotency.py:278`

```python
async def get_idempotency_status(idempotency_key: str, tenant_id: Optional[int] = None) -> dict:
```

Récupère le statut d'une clé d'idempotence.

**Paramètres**:
- `idempotency_key`: `str`
- `tenant_id`: `Optional[int]`

**Retour**: `dict`

---

### `get_performance_stats`

**Fichier**: `backend/middleware/performance.py:248`

```python
def get_performance_stats() -> dict[str, EndpointStats]:
```

Récupère les statistiques de performance globales.

**Retour**: `dict[str, EndpointStats]`

---

### `get_rate_limiter`

**Fichier**: `backend/middleware/rate_limiter.py:161`

```python
def get_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
```

Obtient ou crée l'instance globale du rate limiter.

**Paramètres**:
- `config`: `RateLimitConfig | None`

**Retour**: `RateLimiter`

---

### `get_request_context`

**Fichier**: `backend/middleware/request_context.py:55`

```python
def get_request_context() -> dict[str, Any]:
```

Récupère le contexte complet de la requête courante.

**Retour**: `dict[str, Any]`

---

### `get_request_id`

**Fichier**: `backend/middleware/request_context.py:50`

```python
def get_request_id() -> str:
```

Récupère l'ID de requête courant (utilisable partout).

**Retour**: `str`

---

### `has_idempotency_key`

**Fichier**: `backend/middleware/idempotency.py:272`

```python
def has_idempotency_key(request: Request) -> bool:
```

Vérifie si la requête possède une clé d'idempotence.

**Paramètres**:
- `request`: `Request`

**Retour**: `bool`

---

### `record`

**Fichier**: `backend/middleware/performance.py:58`

```python
def record(self, duration_ms: float, is_error: bool, slow_threshold: float) -> None:
```

**Paramètres**:
- `self`
- `duration_ms`: `float`
- `is_error`: `bool`
- `slow_threshold`: `float`

**Retour**: `None`

---

### `require_idempotency_key`

**Fichier**: `backend/middleware/idempotency.py:246`

```python
def require_idempotency_key(request: Request) -> str:
```

Dépendance FastAPI imposant une clé d'idempotence pour les opérations critiques.

**Paramètres**:
- `request`: `Request`

**Retour**: `str`

---

### `set_context_value`

**Fichier**: `backend/middleware/request_context.py:60`

```python
def set_context_value(key: str, value: Any) -> None:
```

Ajoute une valeur au contexte de la requête courante.

**Paramètres**:
- `key`: `str`
- `value`: `Any`

**Retour**: `None`

---

## Restaurant (38)

### `attach_ingredient_to_plat`

**Fichier**: `backend/services/restaurant/ingredients.py:462`

```python
def attach_ingredient_to_plat(tenant_id: int, plat_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Associe un ingrédient à un plat avec recalcul des coûts.

**Paramètres**:
- `tenant_id`: `int`
- `plat_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `create_bank_statement`

**Fichier**: `backend/services/restaurant/bank_statements.py:130`

```python
def create_bank_statement(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Insère une ligne de relevé bancaire importée/éditée.

**Paramètres**:
- `tenant_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `create_cost_center`

**Fichier**: `backend/services/restaurant/expenses.py:61`

```python
def create_cost_center(tenant_id: int, nom: str) -> dict[str, Any]:
```

Crée un nouveau centre de coûts.

**Paramètres**:
- `tenant_id`: `int`
- `nom`: `str`

**Retour**: `dict[str, Any]`

---

### `create_depense_category`

**Fichier**: `backend/services/restaurant/expenses.py:29`

```python
def create_depense_category(tenant_id: int, nom: str) -> dict[str, Any]:
```

Crée une nouvelle catégorie de dépense.

**Paramètres**:
- `tenant_id`: `int`
- `nom`: `str`

**Retour**: `dict[str, Any]`

---

### `create_expense`

**Fichier**: `backend/services/restaurant/expenses.py:155`

```python
def create_expense(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Insère une dépense et renvoie l'enregistrement enrichi.

**Paramètres**:
- `tenant_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `create_fournisseur`

**Fichier**: `backend/services/restaurant/expenses.py:93`

```python
def create_fournisseur(tenant_id: int, nom: str) -> dict[str, Any]:
```

Crée un nouveau fournisseur.

**Paramètres**:
- `tenant_id`: `int`
- `nom`: `str`

**Retour**: `dict[str, Any]`

---

### `create_plat`

**Fichier**: `backend/services/restaurant/ingredients.py:426`

```python
def create_plat(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Crée un plat et initialise totaux/marges depuis les ingrédients liés.

**Paramètres**:
- `tenant_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `delete_ingredient`

**Fichier**: `backend/services/restaurant/ingredients.py:739`

```python
def delete_ingredient(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
```

Supprime un ingrédient. Échoue si l'ingrédient est utilisé dans un plat.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`

**Retour**: `dict[str, Any]`

---

### `delete_plat`

**Fichier**: `backend/services/restaurant/ingredients.py:777`

```python
def delete_plat(tenant_id: int, plat_id: int) -> dict[str, Any]:
```

Supprime un plat et cascade sur restaurant_plat_ingredients.

**Paramètres**:
- `tenant_id`: `int`
- `plat_id`: `int`

**Retour**: `dict[str, Any]`

---

### `delete_plat_epicerie_mapping`

**Fichier**: `backend/services/restaurant/mappings.py:343`

```python
def delete_plat_epicerie_mapping(tenant_restaurant: int, plat_id: int) -> bool:
```

Supprime un mapping plat-épicerie.

**Paramètres**:
- `tenant_restaurant`: `int`
- `plat_id`: `int`

**Retour**: `bool`

---

### `expense_summary_by_cost_center`

**Fichier**: `backend/services/restaurant/expenses.py:196`

```python
def expense_summary_by_cost_center(tenant_id: int, months: int = 3) -> List[dict[str, Any]]:
```

Répartit les dépenses par centre de coûts sur la période récente.

**Paramètres**:
- `tenant_id`: `int`
- `months`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `expense_summary_by_month`

**Fichier**: `backend/services/restaurant/expenses.py:181`

```python
def expense_summary_by_month(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
```

Agrège les dépenses par mois sur la période demandée.

**Paramètres**:
- `tenant_id`: `int`
- `months`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `expense_summary_by_tva`

**Fichier**: `backend/services/restaurant/expenses.py:215`

```python
def expense_summary_by_tva(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
```

Résume les montants HT/TVA/TTC pour la déclaration fiscale.

**Paramètres**:
- `tenant_id`: `int`
- `months`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `get_expense_detail`

**Fichier**: `backend/services/restaurant/expenses.py:131`

```python
def get_expense_detail(tenant_id: int, expense_id: int) -> dict[str, Any] | None:
```

Récupère le détail d'une dépense donnée.

**Paramètres**:
- `tenant_id`: `int`
- `expense_id`: `int`

**Retour**: `dict[str, Any] | None`

---

### `get_stock_analytics`

**Fichier**: `backend/services/restaurant/stock.py:480`

```python
def get_stock_analytics( tenant_id: int,
```

Statistiques de stock sur une période.

**Paramètres**:
- `tenant_id`: `int`
- `days`: `int`

**Retour**: `Dict[str, Any]`

---

### `get_stock_summary`

**Fichier**: `backend/services/restaurant/stock.py:105`

```python
def get_stock_summary(tenant_id: int) -> List[Dict[str, Any]]:
```

Retourne le résumé du stock actuel par ingrédient avec dernier mouvement.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `List[Dict[str, Any]]`

---

### `guess_unit`

**Fichier**: `backend/services/restaurant/mappings.py:117`

```python
def guess_unit(category: str | None) -> str:
```

**Paramètres**:
- `category`: `str | None`

**Retour**: `str`

---

### `list_cost_centers`

**Fichier**: `backend/services/restaurant/expenses.py:45`

```python
def list_cost_centers(tenant_id: int) -> List[dict[str, Any]]:
```

Liste tous les centres de coûts pour un tenant.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `list_depense_categories`

**Fichier**: `backend/services/restaurant/expenses.py:13`

```python
def list_depense_categories(tenant_id: int) -> List[dict[str, Any]]:
```

Liste toutes les catégories de dépense pour un tenant.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `list_expenses`

**Fichier**: `backend/services/restaurant/expenses.py:109`

```python
def list_expenses(tenant_id: int) -> List[dict[str, Any]]:
```

Liste toutes les dépenses d'un tenant avec données enrichies.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `list_fournisseurs`

**Fichier**: `backend/services/restaurant/expenses.py:77`

```python
def list_fournisseurs(tenant_id: int) -> List[dict[str, Any]]:
```

Liste tous les fournisseurs pour un tenant.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `list_plat_alerts`

**Fichier**: `backend/services/restaurant/ingredients.py:421`

```python
def list_plat_alerts(tenant_id: int) -> List[dict[str, Any]]:
```

Retourne les alertes de marge générées par le recalcul précédent.

**Paramètres**:
- `tenant_id`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `list_plat_price_history`

**Fichier**: `backend/services/restaurant/ingredients.py:651`

```python
def list_plat_price_history(tenant_id: int, plat_id: int) -> List[dict[str, Any]]:
```

Affiche l'historique des prix pour un plat donné.

**Paramètres**:
- `tenant_id`: `int`
- `plat_id`: `int`

**Retour**: `List[dict[str, Any]]`

---

### `list_recent_price_changes`

**Fichier**: `backend/services/restaurant/ingredients.py:668`

```python
def list_recent_price_changes(tenant_id: int, limit: int = 12) -> dict[str, list[dict[str, Any]]]:
```

Retourne les dernières modifications de prix pour ingrédients et plats.

**Paramètres**:
- `tenant_id`: `int`
- `limit`: `int`

**Retour**: `dict[str, list[dict[str, Any]]]`

---

### `record_adjustment`

**Fichier**: `backend/services/restaurant/stock.py:375`

```python
def record_adjustment( tenant_id: int,
```

Ajuste le stock à une nouvelle quantité (inventaire).

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `new_quantity`: `float`
- `commentaire`: `Optional[str]`
- `created_by`: `Optional[str]`

**Retour**: `Dict[str, Any]`

---

### `record_consumption`

**Fichier**: `backend/services/restaurant/stock.py:354`

```python
def record_consumption( tenant_id: int,
```

Enregistre une sortie de stock pour consommation.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `quantite`: `float`
- `commentaire`: `Optional[str]`
- `created_by`: `Optional[str]`

**Retour**: `Dict[str, Any]`

---

### `record_invoice_entry`

**Fichier**: `backend/services/restaurant/stock.py:323`

```python
def record_invoice_entry( tenant_id: int,
```

Enregistre une entrée de stock depuis une facture.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `quantite`: `float`
- `cout_unitaire`: `float`
- `facture_id`: `int`
- `facture_ref`: `str`
- `fournisseur`: `str`
- `unite`: `Optional[str]`
- `date_mouvement`: `Optional[datetime]`
- `created_by`: `Optional[str]`

**Retour**: `Dict[str, Any]`

---

### `refresh_plat_costs`

**Fichier**: `backend/services/restaurant/ingredients.py:416`

```python
def refresh_plat_costs(tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
```

Délègue le recalcul des coûts/marges aux utilitaires partagés.

**Paramètres**:
- `tenant_id`: `int`
- `margin_threshold`: `float`

**Retour**: `dict[str, Any]`

---

### `remove_ingredient_from_plat`

**Fichier**: `backend/services/restaurant/ingredients.py:491`

```python
def remove_ingredient_from_plat(tenant_id: int, plat_id: int, ingredient_id: int) -> dict[str, Any]:
```

Retire un ingrédient d'un plat et rafraîchit les coûts.

**Paramètres**:
- `tenant_id`: `int`
- `plat_id`: `int`
- `ingredient_id`: `int`

**Retour**: `dict[str, Any]`

---

### `transfer_from_epicerie`

**Fichier**: `backend/services/restaurant/bank_statements.py:302`

```python
def transfer_from_epicerie(tenant_id: int, produit_restaurant_id: int, quantite: float = 1.0) -> Dict[str, Any]:
```

Appelle la fonction SQL transfer_from_epicerie pour les mouvements épicerie -> restaurant.

**Paramètres**:
- `tenant_id`: `int`
- `produit_restaurant_id`: `int`
- `quantite`: `float`

**Retour**: `Dict[str, Any]`

---

### `transfer_from_epicerie`

**Fichier**: `backend/services/restaurant/stock.py:283`

```python
def transfer_from_epicerie( tenant_id: int,
```

Transfère du stock depuis un produit épicerie vers un ingrédient restaurant.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `produit_epicerie_id`: `int`
- `quantite`: `float`
- `commentaire`: `Optional[str]`
- `created_by`: `Optional[str]`

**Retour**: `Dict[str, Any]`

---

### `unlink_ingredient_from_epicerie`

**Fichier**: `backend/services/restaurant/ingredients.py:205`

```python
def unlink_ingredient_from_epicerie(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
```

Retire le lien entre un ingrédient et un produit épicerie.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`

**Retour**: `dict[str, Any]`

---

### `update_bank_statement`

**Fichier**: `backend/services/restaurant/bank_statements.py:152`

```python
def update_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Met à jour un relevé existant et renvoie la version enrichie.

**Paramètres**:
- `tenant_id`: `int`
- `entry_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `update_ingredient`

**Fichier**: `backend/services/restaurant/ingredients.py:699`

```python
def update_ingredient(tenant_id: int, ingredient_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

Met à jour les détails d'un ingrédient (nom, unité, coût, stock, catégorie, fournisseur).

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `update_ingredient_price`

**Fichier**: `backend/services/restaurant/ingredients.py:263`

```python
def update_ingredient_price(tenant_id: int, ingredient_id: int, new_price: float) -> dict[str, Any]:
```

Met à jour le coût de l'ingrédient et recalcule les marges des plats.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `new_price`: `float`

**Retour**: `dict[str, Any]`

---

### `update_ingredient_ratio`

**Fichier**: `backend/services/restaurant/ingredients.py:229`

```python
def update_ingredient_ratio(tenant_id: int, ingredient_id: int, ratio: float) -> dict[str, Any]:
```

Met à jour le ratio de conversion ingrédient/épicerie.

**Paramètres**:
- `tenant_id`: `int`
- `ingredient_id`: `int`
- `ratio`: `float`

**Retour**: `dict[str, Any]`

---

### `update_plat_ingredient`

**Fichier**: `backend/services/restaurant/ingredients.py:509`

```python
def update_plat_ingredient( tenant_id: int,
```

Met à jour la quantité/unité d'un ingrédient du plat et rafraîchit les coûts.

**Paramètres**:
- `tenant_id`: `int`
- `plat_id`: `int`
- `ingredient_id`: `int`
- `payload`: `dict[str, Any]`

**Retour**: `dict[str, Any]`

---

### `update_plat_price`

**Fichier**: `backend/services/restaurant/ingredients.py:549`

```python
def update_plat_price(tenant_id: int, plat_id: int, new_price: float) -> dict[str, Any]:
```

Met à jour le prix TTC du plat et recalcule les marges liées.

**Paramètres**:
- `tenant_id`: `int`
- `plat_id`: `int`
- `new_price`: `float`

**Retour**: `dict[str, Any]`

---

## Utilities (4)

### `format_currency_line`

**Fichier**: `core/pdf_utils.py:100`

```python
def format_currency_line(label: str, amount: Decimal) -> str:
```

**Paramètres**:
- `label`: `str`
- `amount`: `Decimal`

**Retour**: `str`

---

### `format_quantity`

**Fichier**: `core/pdf_utils.py:105`

```python
def format_quantity(qty: Decimal) -> str:
```

**Paramètres**:
- `qty`: `Decimal`

**Retour**: `str`

---

### `render_receipt_pdf`

**Fichier**: `core/pdf_utils.py:113`

```python
def render_receipt_pdf(lines: list[str]) -> bytes:
```

Encode les lignes du ticket dans un PDF minimaliste.

**Paramètres**:
- `lines`: `list[str]`

**Retour**: `bytes`

---

### `sanitize_receipt_text`

**Fichier**: `core/pdf_utils.py:83`

```python
def sanitize_receipt_text(value: object) -> str:
```

Convertit un contenu en chaîne ASCII sans caractères spéciaux.

**Paramètres**:
- `value`: `object`

**Retour**: `str`

---

## Validation (5)

### `_ensure_account`

**Fichier**: `core/bank_import/orchestrator.py:296`

```python
def _ensure_account(self, entity_code: str, account_label: str) -> int:
```

Ensure account exists and return its ID.

**Paramètres**:
- `self`
- `entity_code`: `str`
- `account_label`: `str`

**Retour**: `int`

---

### `check_backup_integrity`

**Fichier**: `core/backup_manager.py:385`

```python
def check_backup_integrity( metadata: BackupMetadata,
```

Effectue des vérifications légères d'intégrité sur un fichier de sauvegarde.

**Paramètres**:
- `metadata`: `BackupMetadata`

**Retour**: `Tuple[bool, str]`

---

### `check_duplicate`

**Fichier**: `core/bank_import/deduplicator.py:115`

```python
def check_duplicate(self, txn: ParsedTransaction) -> bool:
```

Check if a transaction is a duplicate.

**Paramètres**:
- `self`
- `txn`: `ParsedTransaction`

**Retour**: `bool`

---

### `validate_statement`

**Fichier**: `core/bank_import/validator.py:190`

```python
def validate_statement(statement: ParsedStatement) -> ValidationResult:
```

Convenience function for validation.

**Paramètres**:
- `statement`: `ParsedStatement`

**Retour**: `ValidationResult`

---

### `validate_transaction`

**Fichier**: `core/bank_import/validator.py:151`

```python
def validate_transaction(self, txn: ParsedTransaction) -> List[str]:
```

Validate a single transaction.

**Paramètres**:
- `self`
- `txn`: `ParsedTransaction`

**Retour**: `List[str]`

---
