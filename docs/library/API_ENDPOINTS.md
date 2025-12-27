# Endpoints API

Documentation des endpoints FastAPI extraits du code

---

## Module: `admin`

**Fichier**: `backend/api/admin.py`

### `GET` /overview

**Fonction**: `admin_overview`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def admin_overview(tenant: Tenant = Depends(get_current_tenant)):
```

---

### `GET` /users

**Fonction**: `list_users`

```python
def list_users():
```

---

### `POST` /users/{user_id}/role

**Fonction**: `change_user_role`

**Paramètres**:
- `user_id`: `int`
- `payload`: `UpdateRolePayload`

```python
def change_user_role(user_id: int, payload: UpdateRolePayload):
```

---

### `POST` /users/{user_id}/reset-password

**Fonction**: `reset_user_password`

**Paramètres**:
- `user_id`: `int`
- `payload`: `ResetPasswordPayload | None` (défaut: `None`)

```python
def reset_user_password(user_id: int, payload: ResetPasswordPayload | None = None):
```

---

### `POST` /backups

**Fonction**: `create_backup`

**Paramètres**:
- `payload`: `BackupCreationPayload | None` (défaut: `None`)

```python
def create_backup(payload: BackupCreationPayload | None = None):
```

---

### `POST` /backups/{filename}/restore

**Fonction**: `restore_backup`

**Paramètres**:
- `filename`: `str`

```python
def restore_backup(filename: str):
```

---

### `DELETE` /backups/{filename}

**Fonction**: `delete_backup`

**Paramètres**:
- `filename`: `str`

```python
def delete_backup(filename: str):
```

---

### `GET` /backups/integrity

**Fonction**: `get_integrity_report`

```python
def get_integrity_report():
```

---

### `GET` /settings

**Fonction**: `get_backup_settings`

```python
def get_backup_settings():
```

---

### `PUT` /settings

**Fonction**: `update_backup_settings`

**Paramètres**:
- `payload`: `BackupSettingsModel`

```python
def update_backup_settings(payload: BackupSettingsModel):
```

---


## Module: `analytics`

**Fichier**: `backend/api/analytics.py`

### `GET` /summary

**Fonction**: `get_summary`

Retourne quelques KPI agrégés (stock et mouvements récents) pour le tenant courant.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

**Retour**: `AnalyticsSummary`

```python
def get_summary(tenant: Tenant = Depends(get_current_tenant)) -> AnalyticsSummary:
```

---


## Module: `anomaly_detection`

**Fichier**: `backend/api/anomaly_detection.py`

### `GET` /scan

**Fonction**: `scan_for_anomalies`

Scanne les données pour détecter des anomalies.

**Paramètres**:
- `entity_types`: `str` (défaut: `Query(default='transactions,invoices')`)
- `severity_threshold`: `str` (défaut: `Query(default='LOW')`)
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def scan_for_anomalies( entity_types: str = Query(default="transactions,invoices"),
```

---

### `GET` /transactions/outliers

**Fonction**: `detect_transaction_outliers`

Détecte les transactions avec des montants anormalement élevés ou bas

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `z_score_threshold`: `float` (défaut: `Query(default=2.5, ge=1.5, le=5.0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def detect_transaction_outliers( days_back: int = Query(default=30, ge=1, le=365),
```

---

### `GET` /invoices/duplicates

**Fonction**: `detect_duplicate_invoices`

Détecte les factures potentiellement en double.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=90, ge=1, le=365)`)
- `similarity_threshold`: `float` (défaut: `Query(default=0.9, ge=0.7, le=1.0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def detect_duplicate_invoices( days_back: int = Query(default=90, ge=1, le=365),
```

---

### `GET` /invoices/sequence-gaps

**Fonction**: `detect_invoice_sequence_gaps`

Détecte les trous dans les séquences de numéros de factures.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=90, ge=1, le=365)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def detect_invoice_sequence_gaps( days_back: int = Query(default=90, ge=1, le=365),
```

---

### `GET` /transactions/round-amounts

**Fonction**: `detect_round_amounts`

Détecte les transactions avec des montants ronds suspects.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `min_amount`: `float` (défaut: `Query(default=100.0, ge=0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def detect_round_amounts( days_back: int = Query(default=30, ge=1, le=365),
```

---

### `GET` /summary

**Fonction**: `get_anomaly_summary`

Résumé des anomalies détectées avec filtrage optionnel.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `severity`: `Optional[str]` (défaut: `Query(default=None, description='Filtrer par sévérité (critical, high, medium, low)')`)
- `type`: `Optional[str]` (défaut: `Query(default=None, description="Filtrer par type d'anomalie")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_anomaly_summary( days_back: int = Query(default=30, ge=1, le=365),
```

---

### `POST` /resolve/{anomaly_id}

**Fonction**: `resolve_anomaly`

Marque une anomalie comme résolue avec une note explicative.

**Paramètres**:
- `anomaly_id`: `str`
- `resolution_note`: `str` (défaut: `Query(..., min_length=5)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def resolve_anomaly( anomaly_id: str,
```

---


## Module: `audit`

**Fichier**: `backend/api/audit.py`

### `GET` /diagnostics

**Fonction**: `get_diagnostics`

**Paramètres**:
- `categories`: `Optional[List[str]]` (défaut: `Query(default=None, description='Répéter le paramètre pour filtrer par catégorie.')`)
- `levels`: `Optional[List[str]]` (défaut: `Query(default=None, description="Filtrer par niveau d'écart.")`)
- `min_abs`: `Optional[float]` (défaut: `Query(default=None, ge=0.0)`)
- `max_abs`: `Optional[float]` (défaut: `Query(default=None, ge=0.0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_diagnostics( categories: Optional[List[str]] = Query(
```

---

### `GET` /actions

**Fonction**: `get_actions`

**Paramètres**:
- `include_closed`: `bool` (défaut: `Query(default=False)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_actions( include_closed: bool = Query(default=False),
```

---

### `GET` /resolutions

**Fonction**: `get_resolution_log`

**Paramètres**:
- `limit`: `int` (défaut: `Query(default=100, ge=1, le=500)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_resolution_log( limit: int = Query(default=100, ge=1, le=500),
```

---

### `POST` /assignments

**Fonction**: `create_assignment`

**Paramètres**:
- `payload`: `AuditAssignmentRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def create_assignment(payload: AuditAssignmentRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /actions/{action_id}/status

**Fonction**: `update_action_status`

**Paramètres**:
- `action_id`: `int`
- `payload`: `AuditResolutionRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def update_action_status( action_id: int,
```

---


## Module: `audit_trail`

**Fichier**: `backend/api/audit_trail.py`

### `GET` /entries

**Fonction**: `list_audit_entries`

Liste les entrées d'audit avec filtres optionnels.

**Paramètres**:
- `start_date`: `Optional[datetime]` (défaut: `Query(default=None)`)
- `end_date`: `Optional[datetime]` (défaut: `Query(default=None)`)
- `action`: `Optional[str]` (défaut: `Query(default=None)`)
- `entity`: `Optional[str]` (défaut: `Query(default=None)`)
- `entity_id`: `Optional[int]` (défaut: `Query(default=None)`)
- `user_id`: `Optional[int]` (défaut: `Query(default=None)`)
- `severity`: `Optional[str]` (défaut: `Query(default=None)`)
- `search`: `Optional[str]` (défaut: `Query(default=None)`)
- `limit`: `int` (défaut: `Query(default=100, le=1000)`)
- `offset`: `int` (défaut: `Query(default=0, ge=0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def list_audit_entries( start_date: Optional[datetime] = Query(default=None),
```

---

### `POST` /search

**Fonction**: `search_audit_entries`

Recherche avancée dans l'audit log avec critères multiples.

**Paramètres**:
- `request`: `AuditSearchRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def search_audit_entries( request: AuditSearchRequest,
```

---

### `GET` /entity/{entity}/{entity_id}

**Fonction**: `get_entity_history`

Retourne l'historique complet des modifications d'une entité.

**Paramètres**:
- `entity`: `str`
- `entity_id`: `int`
- `limit`: `int` (défaut: `Query(default=50, le=500)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_entity_history( entity: str,
```

---

### `GET` /user/{user_id}

**Fonction**: `get_user_activity`

Retourne l'activité d'un utilisateur spécifique.

**Paramètres**:
- `user_id`: `int`
- `start_date`: `Optional[datetime]` (défaut: `Query(default=None)`)
- `limit`: `int` (défaut: `Query(default=100, le=500)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_user_activity( user_id: int,
```

---

### `GET` /report

**Fonction**: `generate_audit_report`

Génère un rapport d'audit agrégé pour une période donnée.

**Paramètres**:
- `start_date`: `datetime` (défaut: `Query(default=None, description='Start date for report (defaults to 30 days ago)')`)
- `end_date`: `datetime` (défaut: `Query(default=None, description='End date for report (defaults to now)')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def generate_audit_report( start_date: datetime = Query(default=None, description="Start date for report (defaults to 30 days ago)"),
```

---

### `GET` /security-events

**Fonction**: `get_security_events`

Retourne les événements de sécurité récents.

**Paramètres**:
- `days`: `int` (défaut: `Query(default=7, ge=1, le=90)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_security_events( days: int = Query(default=7, ge=1, le=90),
```

---

### `GET` /recent-changes

**Fonction**: `get_recent_changes`

Retourne les modifications récentes (dernières N heures).

**Paramètres**:
- `entity`: `Optional[str]` (défaut: `Query(default=None)`)
- `hours`: `int` (défaut: `Query(default=24, ge=1, le=168)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_recent_changes( entity: Optional[str] = Query(default=None),
```

---

### `GET` /rgpd/export/{user_id}

**Fonction**: `export_user_data_rgpd`

Export RGPD: Retourne toutes les données d'audit d'un utilisateur.

**Paramètres**:
- `user_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def export_user_data_rgpd( user_id: int,
```

---

### `DELETE` /rgpd/anonymize/{user_id}

**Fonction**: `anonymize_user_data_rgpd`

RGPD: Anonymise les données d'un utilisateur dans l'audit log.

**Paramètres**:
- `user_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def anonymize_user_data_rgpd( user_id: int,
```

---

### `GET` /summary

**Fonction**: `get_audit_summary`

Résumé de l'activité d'audit:

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_audit_summary( tenant: Tenant = Depends(get_current_tenant)
```

---


## Module: `auth`

**Fichier**: `backend/api/auth.py`

### `GET` N/A

**Fonction**: `__init__`

**Paramètres**:
- `self`
- `grant_type`: `str | None` (défaut: `Form(default=None, pattern='password')`)
- `username`: `str` (défaut: `Form(...)`)
- `password`: `str` (défaut: `Form(...)`)
- `scope`: `str` (défaut: `Form(default='')`)
- `client_id`: `str | None` (défaut: `Form(default=None)`)
- `client_secret`: `str | None` (défaut: `Form(default=None)`)
- `tenant`: `str` (défaut: `Form(default=DEFAULT_TENANT.code)`)

**Retour**: `None`

```python
def __init__( self, grant_type: str | None = Form(default=None, pattern="password"),
```

---

### `POST` /token

**Fonction**: `issue_token`

Émet un token bearer OAuth2 (pour les clients API).

**Paramètres**:
- `form_data`: `OAuth2TenantRequestForm` (défaut: `Depends()`)

**Retour**: `TokenResponse`

```python
def issue_token(form_data: OAuth2TenantRequestForm = Depends()) -> TokenResponse:
```

---

### `POST` /login

**Fonction**: `login_with_cookies`

Connexion et pose des cookies httpOnly (recommandé pour les clients navigateur).

**Paramètres**:
- `response`: `Response`
- `form_data`: `OAuth2TenantRequestForm` (défaut: `Depends()`)

**Retour**: `CookieTokenResponse`

```python
def login_with_cookies( response: Response,
```

---

### `POST` /refresh

**Fonction**: `refresh_access_token`

Rafraîchit le token d'accès en utilisant le cookie de refresh.

**Paramètres**:
- `request`: `Request`
- `response`: `Response`

**Retour**: `RefreshResponse`

```python
def refresh_access_token(request: Request, response: Response) -> RefreshResponse:
```

---

### `POST` /logout

**Fonction**: `logout`

Déconnecte et supprime les cookies d'authentification.

**Paramètres**:
- `request`: `Request`
- `response`: `Response`

**Retour**: `dict[str, str]`

```python
def logout(request: Request, response: Response) -> dict[str, str]:
```

---


## Module: `bank_reconciliation`

**Fichier**: `backend/api/bank_reconciliation.py`

### `POST` /run

**Fonction**: `run_reconciliation`

Lance le rapprochement bancaire automatique.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=60, ge=1, le=180)`)
- `auto_confirm_threshold`: `float` (défaut: `Query(default=0.95, ge=0.5, le=1.0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def run_reconciliation( days_back: int = Query(default=60, ge=1, le=180),
```

---

### `GET` /unmatched/transactions

**Fonction**: `get_unmatched_transactions`

Retourne les transactions non rapprochées AVEC FACTURES.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=365, ge=1, le=730)`)
- `min_amount`: `float` (défaut: `Query(default=0, ge=0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_unmatched_transactions( days_back: int = Query(default=365, ge=1, le=730),
```

---

### `GET` /unmatched/invoices

**Fonction**: `get_unmatched_invoices`

Retourne les factures non payées/non rapprochées.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=365, ge=1, le=730)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_unmatched_invoices( days_back: int = Query(default=365, ge=1, le=730),
```

---

### `POST` /match/manual

**Fonction**: `create_manual_match`

Crée un rapprochement manuel entre une transaction et une ou plusieurs factures.

**Paramètres**:
- `request`: `ManualMatchRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def create_manual_match( request: ManualMatchRequest,
```

---

### `GET` /aliases

**Fonction**: `get_supplier_aliases`

Retourne les alias fournisseurs appris pour le rapprochement automatique.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_supplier_aliases( tenant: Tenant = Depends(get_current_tenant_or_default)
```

---

### `POST` /aliases

**Fonction**: `create_supplier_alias`

Crée un nouvel alias fournisseur pour le rapprochement automatique.

**Paramètres**:
- `request`: `CreateAliasRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def create_supplier_alias( request: CreateAliasRequest,
```

---

### `DELETE` /aliases/{alias_id}

**Fonction**: `delete_supplier_alias`

Supprime un alias fournisseur.

**Paramètres**:
- `alias_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def delete_supplier_alias( alias_id: int,
```

---

### `GET` /summary

**Fonction**: `get_reconciliation_summary`

Résumé du rapprochement bancaire avec FACTURES.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=180)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_reconciliation_summary( days_back: int = Query(default=30, ge=1, le=180),
```

---


## Module: `capital`

**Fichier**: `backend/api/capital.py`

### `GET` /overview

**Fonction**: `get_capital_overview`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_capital_overview(tenant: Tenant = Depends(get_current_tenant)):
```

---


## Module: `catalog`

**Fichier**: `backend/api/catalog.py`

### `GET` /products

**Fonction**: `list_products`

Liste les produits avec pagination stricte.

**Paramètres**:
- `search`: `str | None` (défaut: `None`)
- `category`: `str | None` (défaut: `None`)
- `status`: `str | None` (défaut: `None`)
- `page`: `int` (défaut: `Query(default=1, ge=1, le=10000, description='Numéro de page')`)
- `per_page`: `int` (défaut: `Query(default=25, ge=1, le=100, description='Éléments par page (max 100)')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def list_products( search: str | None = None,
```

---

### `GET` /products/{product_id}

**Fonction**: `get_product`

**Paramètres**:
- `product_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /products

**Fonction**: `create_product`

**Paramètres**:
- `payload`: `ProductCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def create_product(payload: ProductCreate, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `PATCH` /products/{product_id}

**Fonction**: `update_product`

**Paramètres**:
- `product_id`: `int`
- `payload`: `ProductUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def update_product(product_id: int, payload: ProductUpdate, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `DELETE` /products/{product_id}

**Fonction**: `delete_product`

**Paramètres**:
- `product_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def delete_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `GET` /products/barcode/{barcode}

**Fonction**: `get_product_by_barcode`

**Paramètres**:
- `barcode`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_product_by_barcode(barcode: str, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `GET` /categories

**Fonction**: `list_categories`

Liste toutes les categories de produits.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def list_categories(tenant: Tenant = Depends(get_current_tenant)):
```

---

### `GET` /vendors

**Fonction**: `list_vendors`

Liste tous les fournisseurs.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def list_vendors(tenant: Tenant = Depends(get_current_tenant)):
```

---


## Module: `cockpit`

**Fichier**: `backend/api/cockpit.py`

### `GET` /overview

**Fonction**: `get_cockpit_overview`

Retourne la vue consolidee complete du cockpit.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_cockpit_overview( tenant: Tenant = Depends(get_current_tenant)
```

---

### `GET` /kpis/live

**Fonction**: `get_live_kpis`

Retourne les KPIs en temps reel pour refresh rapide.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_live_kpis( tenant: Tenant = Depends(get_current_tenant)
```

---

### `GET` /alerts

**Fonction**: `get_alerts`

Retourne les alertes actives.

**Paramètres**:
- `severity`: `Optional[str]` (défaut: `Query(None, description='Filtrer par severite: critical, warning, info')`)
- `category`: `Optional[str]` (défaut: `Query(None, description='Filtrer par categorie: stock, finance, margin, anomaly')`)
- `limit`: `int` (défaut: `Query(20, ge=1, le=100)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_alerts( severity: Optional[str] = Query(None, description="Filtrer par severite: critical, warning, info"),
```

---

### `POST` /alerts/{alert_id}/acknowledge

**Fonction**: `acknowledge_alert`

Marque une alerte comme acquittee.

**Paramètres**:
- `alert_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def acknowledge_alert( alert_id: str,
```

---

### `GET` /health

**Fonction**: `get_health_status`

Retourne le statut de sante global.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_health_status( tenant: Tenant = Depends(get_current_tenant)
```

---


## Module: `dashboard`

**Fichier**: `backend/api/dashboard.py`

### `GET` /metrics

**Fonction**: `get_dashboard_metrics`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_dashboard_metrics(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

---


## Module: `data_quality`

**Fichier**: `backend/api/data_quality.py`

### `GET` /categorization/coverage

**Fonction**: `categorization_coverage`

Analyse la couverture de catégorisation des transactions bancaires.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=90, ge=1, le=365)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

**Retour**: `dict`

```python
def categorization_coverage( days_back: int = Query(default=90, ge=1, le=365),
```

---

### `GET` /flags

**Fonction**: `list_flags`

**Paramètres**:
- `table`: `str | None` (défaut: `Query(default=None, description='Table ciblée (ex: produits, finance_transactions)')`)
- `limit`: `int` (défaut: `Query(default=200, ge=1, le=2000)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

**Retour**: `dict`

```python
def list_flags( table: str | None = Query(default=None, description="Table ciblée (ex: produits, finance_transactions)"),
```

---


## Module: `eurociel`

**Fichier**: `backend/api/eurociel.py`

### `POST` /import

**Fonction**: `import_eurociel_invoice`

Import direct d'une facture Eurociel : extraction + import catalogue en une seule étape.

**Paramètres**:
- `file`: `UploadFile` (défaut: `File(...)`)
- `margin_percent`: `float` (défaut: `Form(40.0)`)
- `initialize_stock`: `bool` (défaut: `Form(False)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

**Retour**: `dict[str, Any]`

```python
async def import_eurociel_invoice( file: UploadFile = File(...),
```

---

### `GET` /status

**Fonction**: `eurociel_status`

Retourne le statut des imports Eurociel pour ce tenant.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

**Retour**: `dict[str, Any]`

```python
def eurociel_status(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, Any]:
```

---


## Module: `finance`

**Fichier**: `backend/api/finance.py`

### `POST` /accounts

**Fonction**: `create_account`

**Paramètres**:
- `payload`: `FinanceAccountCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_account( payload: FinanceAccountCreate,
```

---

### `GET` /accounts

**Fonction**: `list_accounts`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `is_active`: `bool | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def list_accounts( entity_id: int | None = Query(default=None),
```

---

### `GET` /accounts/overview

**Fonction**: `accounts_overview`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def accounts_overview( entity_id: int | None = Query(default=None),
```

---

### `GET` /accounts/{account_id}

**Fonction**: `get_account`

**Paramètres**:
- `account_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def get_account( account_id: int,
```

---

### `PUT` /accounts/{account_id}

**Fonction**: `update_account`

**Paramètres**:
- `account_id`: `int`
- `payload`: `dict`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def update_account( account_id: int,
```

---

### `DELETE` /accounts/{account_id}

**Fonction**: `delete_account`

**Paramètres**:
- `account_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def delete_account( account_id: int,
```

---

### `POST` /transactions

**Fonction**: `create_transaction`

**Paramètres**:
- `payload`: `FinanceTransactionCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_transaction( payload: FinanceTransactionCreate,
```

---

### `GET` /transactions

**Fonction**: `list_transactions`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `account_id`: `int | None` (défaut: `Query(default=None)`)
- `status_filter`: `str | None` (défaut: `Query(default=None, alias='status')`)
- `date_from`: `str | None` (défaut: `Query(default=None)`)
- `date_to`: `str | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def list_transactions( entity_id: int | None = Query(default=None),
```

---

### `GET` /transactions/search

**Fonction**: `search_transactions`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `account_id`: `int | None` (défaut: `Query(default=None)`)
- `category_id`: `int | None` (défaut: `Query(default=None)`)
- `date_from`: `str | None` (défaut: `Query(default=None)`)
- `date_to`: `str | None` (défaut: `Query(default=None)`)
- `amount_min`: `float | None` (défaut: `Query(default=None)`)
- `amount_max`: `float | None` (défaut: `Query(default=None)`)
- `q`: `str | None` (défaut: `Query(default=None, description='Recherche texte sur libellé/note')`)
- `page`: `int` (défaut: `Query(default=1, ge=1)`)
- `size`: `int` (défaut: `Query(default=50, ge=1, le=500)`)
- `sort`: `str` (défaut: `Query(default='-date_operation', description='date_operation|amount|category|account avec - pour desc')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceTransactionSearchResponse`

```python
async def search_transactions( entity_id: int | None = Query(default=None),
```

---

### `PATCH` /transactions/{transaction_id}

**Fonction**: `update_transaction`

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `FinanceTransactionUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def update_transaction( transaction_id: int,
```

---

### `POST` /transactions/{transaction_id}/lock

**Fonction**: `lock_transaction`

**Paramètres**:
- `transaction_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def lock_transaction( transaction_id: int,
```

---

### `POST` /vendors

**Fonction**: `create_vendor`

**Paramètres**:
- `payload`: `FinanceVendorCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_vendor( payload: FinanceVendorCreate,
```

---

### `GET` /vendors

**Fonction**: `list_vendors`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `is_active`: `bool | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def list_vendors( entity_id: int | None = Query(default=None),
```

---

### `POST` /invoices

**Fonction**: `create_invoice`

**Paramètres**:
- `payload`: `FinanceInvoiceCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_invoice( payload: FinanceInvoiceCreate,
```

---

### `GET` /invoices/search

**Fonction**: `search_invoices`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `vendor_id`: `int | None` (défaut: `Query(default=None)`)
- `status_filter`: `str | None` (défaut: `Query(default=None, alias='status')`)
- `date_from`: `str | None` (défaut: `Query(default=None)`)
- `date_to`: `str | None` (défaut: `Query(default=None)`)
- `page`: `int` (défaut: `Query(default=1, ge=1)`)
- `size`: `int` (défaut: `Query(default=50, ge=1, le=500)`)
- `sort`: `str` (défaut: `Query(default='-date_invoice', description='date_invoice|date_due|montant_ttc|vendor|status avec - pour desc')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceInvoiceSearchResponse`

```python
def search_invoices( entity_id: int | None = Query(default=None),
```

---

### `POST` /payments

**Fonction**: `create_payment`

**Paramètres**:
- `payload`: `FinancePaymentCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_payment( payload: FinancePaymentCreate,
```

---

### `GET` /categories/suggestions/autre-top

**Fonction**: `suggest_autre_top`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `limit`: `int` (défaut: `Query(default=50, ge=1, le=200)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceAutreSuggestion]`

```python
def suggest_autre_top( entity_id: int | None = Query(default=None),
```

---

### `GET` /categories

**Fonction**: `list_categories`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `is_active`: `bool | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def list_categories( entity_id: int | None = Query(default=None),
```

---

### `POST` /categories

**Fonction**: `create_category`

**Paramètres**:
- `payload`: `FinanceCategoryCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_category( payload: FinanceCategoryCreate,
```

---

### `GET` /cost-centers

**Fonction**: `list_cost_centers`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `is_active`: `bool | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def list_cost_centers( entity_id: int | None = Query(default=None),
```

---

### `POST` /cost-centers

**Fonction**: `create_cost_center`

**Paramètres**:
- `payload`: `FinanceCostCenterCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_cost_center( payload: FinanceCostCenterCreate,
```

---

### `GET` /categories/suggestions/complete

**Fonction**: `autocomplete_categories`

**Paramètres**:
- `q`: `str` (défaut: `Query(default='', description='Search query for category suggestions')`)
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `limit`: `int` (défaut: `Query(default=20, ge=1, le=100)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def autocomplete_categories( q: str = Query(default="", description="Search query for category suggestions"),
```

---

### `POST` /transactions/batch-categorize

**Fonction**: `batch_categorize_transactions`

**Paramètres**:
- `payload`: `FinanceBatchCategorizeRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def batch_categorize_transactions( payload: FinanceBatchCategorizeRequest,
```

---

### `GET` /rules

**Fonction**: `list_rules`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `is_active`: `bool | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceRule]`

```python
def list_rules( entity_id: int | None = Query(default=None),
```

---

### `POST` /rules

**Fonction**: `create_rule`

**Paramètres**:
- `payload`: `FinanceRuleCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceRule`

```python
def create_rule(payload: FinanceRuleCreate, tenant: Tenant = Depends(get_current_tenant_or_default)) -> FinanceRule:
```

---

### `PATCH` /rules/{rule_id}

**Fonction**: `update_rule`

**Paramètres**:
- `rule_id`: `int`
- `payload`: `dict`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceRule`

```python
def update_rule( rule_id: int,
```

---

### `DELETE` /rules/{rule_id}

**Fonction**: `delete_rule`

**Paramètres**:
- `rule_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def delete_rule(rule_id: int, tenant: Tenant = Depends(get_current_tenant_or_default)) -> dict:
```

---

### `GET` /imports

**Fonction**: `list_imports`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def list_imports(tenant: Tenant = Depends(get_current_tenant_or_default)) -> list[dict]:
```

---

### `POST` /deduplicate

**Fonction**: `deduplicate_finance`

Supprime les doublons (date+montant) sur transactions et lignes de relevés.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def deduplicate_finance(tenant: Tenant = Depends(get_current_tenant_or_default)) -> dict:
```

---

### `POST` /transactions/mark-incomplete

**Fonction**: `mark_transactions_incomplete`

Crée des transaction_lines par défaut et marque les transactions comme 'incomplètes' (data_quality_flags).

**Paramètres**:
- `transaction_ids`: `list[int]`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def mark_transactions_incomplete( transaction_ids: list[int],
```

---

### `GET` /categories/stats

**Fonction**: `categories_stats`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def categories_stats( entity_id: int | None = Query(default=None),
```

---

### `GET` /dashboard/summary

**Fonction**: `finance_dashboard_summary`

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def finance_dashboard_summary( entity_id: int | None = Query(default=None),
```

---

### `POST` /stats/refresh

**Fonction**: `refresh_stats_cache`

Rafraîchit les vues matérialisées des stats finance.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def refresh_stats_cache( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `GET` /stats/timeline

**Fonction**: `get_timeline_stats`

Retourne la chronologie agrégée des flux pour les graphiques.

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `months`: `int | None` (défaut: `Query(default=12, description='Nombre de mois (null=tout)')`)
- `granularity`: `str` (défaut: `Query(default='monthly', description='daily|weekly|monthly')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def get_timeline_stats( entity_id: int | None = Query(default=None),
```

---

### `GET` /stats/category-breakdown

**Fonction**: `get_category_breakdown`

Retourne la répartition par catégorie pour les pie/bar charts.

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `months`: `int | None` (défaut: `Query(default=12, description='Nombre de mois (null=tout)')`)
- `direction`: `str | None` (défaut: `Query(default=None, description='IN|OUT|null pour les deux')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def get_category_breakdown( entity_id: int | None = Query(default=None),
```

---

### `GET` /stats/treasury

**Fonction**: `get_treasury_summary`

Retourne un résumé de trésorerie (totaux, solde, période).

**Paramètres**:
- `entity_id`: `int | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def get_treasury_summary( entity_id: int | None = Query(default=None),
```

---

### `POST` /reconciliations

**Fonction**: `create_reconciliation`

**Paramètres**:
- `payload`: `FinanceReconciliationCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_reconciliation( payload: FinanceReconciliationCreate,
```

---

### `DELETE` /reconciliations/{reconciliation_id}

**Fonction**: `delete_reconciliation`

**Paramètres**:
- `reconciliation_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def delete_reconciliation( reconciliation_id: int,
```

---

### `GET` /bank-statements/search

**Fonction**: `search_bank_statements`

**Paramètres**:
- `account_id`: `int | None` (défaut: `Query(default=None)`)
- `period_start`: `str | None` (défaut: `Query(default=None)`)
- `period_end`: `str | None` (défaut: `Query(default=None)`)
- `status_filter`: `str | None` (défaut: `Query(default=None, alias='status')`)
- `page`: `int` (défaut: `Query(default=1, ge=1)`)
- `size`: `int` (défaut: `Query(default=50, ge=1, le=500)`)
- `sort`: `str` (défaut: `Query(default='-imported_at', description='imported_at|period_start|period_end|account avec - pour desc')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceBankStatementSearchResponse`

```python
def search_bank_statements( account_id: int | None = Query(default=None),
```

---

### `POST` /bank-statements/import

**Fonction**: `import_bank_statements`

**Paramètres**:
- `account_id`: `int` (défaut: `Query(..., description='ID du compte finance_accounts')`)
- `file`: `UploadFile` (défaut: `File(...)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
async def import_bank_statements( account_id: int = Query(..., description="ID du compte finance_accounts"),
```

---

### `POST` /bank-statements/import-pdf

**Fonction**: `import_bank_statements_pdf`

Import best-effort d'un relevé PDF (parse minimal) dans finance_bank_statements/lines.

**Paramètres**:
- `account_id`: `int` (défaut: `Query(..., description='ID du compte finance_accounts')`)
- `file`: `UploadFile` (défaut: `File(...)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
async def import_bank_statements_pdf( account_id: int = Query(..., description="ID du compte finance_accounts"),
```

---

### `POST` /reconciliation/run

**Fonction**: `run_reconciliation`

**Paramètres**:
- `payload`: `FinanceRunRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceRunResponse`

```python
def run_reconciliation( payload: FinanceRunRequest,
```

---

### `GET` /reconciliation/matches

**Fonction**: `list_matches`

**Paramètres**:
- `status`: `str | None` (défaut: `Query(default='pending', description='Filtrer par statut.')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceMatch]`

```python
def list_matches( status: str | None = Query(default="pending", description="Filtrer par statut."),
```

---

### `POST` /reconciliation/{match_id}/status

**Fonction**: `update_match_status`

**Paramètres**:
- `match_id`: `int`
- `payload`: `FinanceMatchStatusRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceMatch`

```python
def update_match_status( match_id: int,
```

---

### `POST` /recurring/refresh

**Fonction**: `refresh_recurring`

**Paramètres**:
- `payload`: `RecurringRefreshRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `RecurringRefreshResponse`

```python
def refresh_recurring( payload: RecurringRefreshRequest,
```

---

### `GET` /recurring

**Fonction**: `list_recurring`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceRecurringExpense]`

```python
def list_recurring( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `POST` /anomalies/refresh

**Fonction**: `refresh_anomalies`

**Paramètres**:
- `payload`: `AnomalyRefreshRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `AnomalyRefreshResponse`

```python
def refresh_anomalies( payload: AnomalyRefreshRequest,
```

---

### `GET` /anomalies

**Fonction**: `list_anomalies`

**Paramètres**:
- `severity`: `str | None` (défaut: `Query(default=None, description='Filtrer par sévérité.')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceAnomaly]`

```python
def list_anomalies( severity: str | None = Query(default=None, description="Filtrer par sévérité."),
```

---

### `GET` /reconciliation/runs/{run_id}/anomalies

**Fonction**: `get_reconciliation_run_anomalies`

Retourne les anomalies détectées pour un run de rapprochement spécifique.

**Paramètres**:
- `run_id`: `int`
- `severity`: `str | None` (défaut: `Query(default=None, description='Filtrer par sévérité.')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceAnomaly]`

```python
def get_reconciliation_run_anomalies( run_id: int,
```

---

### `POST` /transactions/{transaction_id}/feedback

**Fonction**: `record_category_feedback`

Enregistre une correction de catégorie faite par l'utilisateur.

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `CategoryFeedbackPayload`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def record_category_feedback( transaction_id: int,
```

---

### `GET` /categorization/feedback/stats

**Fonction**: `get_categorization_feedback_stats`

Retourne les statistiques globales sur le feedback de catégorisation.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def get_categorization_feedback_stats( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `GET` /categorization/feedback/common-corrections

**Fonction**: `get_common_category_corrections`

Retourne les corrections de catégories les plus fréquentes.

**Paramètres**:
- `limit`: `int` (défaut: `Query(default=20, ge=1, le=100)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[dict]`

```python
def get_common_category_corrections( limit: int = Query(default=20, ge=1, le=100),
```

---


## Module: `forecasting`

**Fichier**: `backend/api/forecasting.py`

### `POST` /sales

**Fonction**: `forecast_sales`

Prévision des ventes avec plusieurs algorithmes disponibles:

**Paramètres**:
- `request`: `SalesForecastRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def forecast_sales( request: SalesForecastRequest,
```

---

### `GET` /stock-depletion

**Fonction**: `forecast_stock_depletion`

Prévoit la date d'épuisement du stock pour chaque produit.

**Paramètres**:
- `days_horizon`: `int` (défaut: `Query(default=60, ge=1, le=180)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def forecast_stock_depletion( days_horizon: int = Query(default=60, ge=1, le=180),
```

---

### `GET` /cash-flow

**Fonction**: `forecast_cash_flow`

Prévision de trésorerie basée sur:

**Paramètres**:
- `horizon_days`: `int` (défaut: `Query(default=30, ge=7, le=90)`)
- `starting_balance`: `float` (défaut: `Query(default=0.0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def forecast_cash_flow( horizon_days: int = Query(default=30, ge=7, le=90),
```

---

### `GET` /price-trend/{product_id}

**Fonction**: `forecast_price_trend`

Prévision de l'évolution des prix d'un produit.

**Paramètres**:
- `product_id`: `int`
- `horizon_days`: `int` (défaut: `Query(default=30, ge=7, le=90)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def forecast_price_trend( product_id: int,
```

---

### `GET` /summary

**Fonction**: `get_forecasting_summary`

Résumé des prévisions:

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_forecasting_summary( tenant: Tenant = Depends(get_current_tenant)
```

---


## Module: `inventory_intelligence`

**Fichier**: `backend/api/inventory_intelligence.py`

### `POST` /eoq

**Fonction**: `calculate_eoq`

Calcule la quantité économique de commande (EOQ) avec la formule de Wilson.

**Paramètres**:
- `request`: `EOQRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def calculate_eoq( request: EOQRequest,
```

---

### `POST` /safety-stock

**Fonction**: `calculate_safety_stock`

Calcule le stock de sécurité pour un niveau de service donné.

**Paramètres**:
- `request`: `SafetyStockRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def calculate_safety_stock( request: SafetyStockRequest,
```

---

### `GET` /reorder-points

**Fonction**: `get_reorder_points`

Retourne les points de réapprovisionnement pour tous les produits.

**Paramètres**:
- `lead_time_days`: `float` (défaut: `Query(default=3.0, gt=0)`)
- `service_level`: `str` (défaut: `Query(default='STANDARD')`)
- `only_needs_reorder`: `bool` (défaut: `Query(default=False)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_reorder_points( lead_time_days: float = Query(default=3.0, gt=0),
```

---

### `GET` /stockout-predictions

**Fonction**: `predict_stockouts`

Prédit les ruptures de stock dans les N prochains jours.

**Paramètres**:
- `horizon_days`: `int` (défaut: `Query(default=30, ge=1, le=90)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def predict_stockouts( horizon_days: int = Query(default=30, ge=1, le=90),
```

---

### `GET` /dead-stock

**Fonction**: `get_dead_stock`

Détecte les produits en stock mort (rotation < seuil/mois).

**Paramètres**:
- `rotation_threshold`: `float` (défaut: `Query(default=0.3, ge=0, le=1)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_dead_stock( rotation_threshold: float = Query(default=0.3, ge=0, le=1),
```

---

### `GET` /abc-xyz

**Fonction**: `get_abc_xyz_classification`

Classification ABC-XYZ des produits.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_abc_xyz_classification( tenant: Tenant = Depends(get_current_tenant)
```

---

### `GET` /reorder-suggestions

**Fonction**: `get_reorder_suggestions`

Génère des suggestions de réapprovisionnement automatiques.

**Paramètres**:
- `lead_time_days`: `float` (défaut: `Query(default=3.0, gt=0)`)
- `service_level`: `str` (défaut: `Query(default='STANDARD')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_reorder_suggestions( lead_time_days: float = Query(default=3.0, gt=0),
```

---

### `GET` /summary

**Fonction**: `get_inventory_intelligence_summary`

Résumé de l'intelligence d'inventaire:

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_inventory_intelligence_summary( tenant: Tenant = Depends(get_current_tenant)
```

---


## Module: `invoices`

**Fichier**: `backend/api/invoices.py`

### `POST` /extract

**Fonction**: `extract_invoice`

**Paramètres**:
- `payload`: `InvoiceExtractRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def extract_invoice(payload: InvoiceExtractRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /extract/file

**Fonction**: `extract_invoice_from_file`

**Paramètres**:
- `file`: `UploadFile` (défaut: `File(...)`)
- `margin_percent`: `float` (défaut: `Form(40.0)`)
- `supplier_hint`: `str | None` (défaut: `Form(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def extract_invoice_from_file( file: UploadFile = File(...),
```

---

### `POST` /import

**Fonction**: `import_invoice`

**Paramètres**:
- `payload`: `InvoiceImportRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def import_invoice(payload: InvoiceImportRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /catalog/import

**Fonction**: `import_catalog`

**Paramètres**:
- `payload`: `InvoiceCatalogImportRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def import_catalog(payload: InvoiceCatalogImportRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /lines/link

**Fonction**: `link_invoice_line`

Associe une ligne extraite à un produit existant et renvoie la ligne enrichie.

**Paramètres**:
- `payload`: `InvoiceLineLinkRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def link_invoice_line(payload: InvoiceLineLinkRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /lines/create-product

**Fonction**: `create_product_from_line`

Crée un produit à partir d'une ligne de facture, optionnellement avec stock initial.

**Paramètres**:
- `payload`: `InvoiceLineCreateProductRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def create_product_from_line(payload: InvoiceLineCreateProductRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /lines/confirm-stock

**Fonction**: `confirm_invoice_stock`

Valide les mouvements de stock pour des lignes sélectionnées.

**Paramètres**:
- `payload`: `InvoiceStockConfirmRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def confirm_invoice_stock(payload: InvoiceStockConfirmRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /zero-click

**Fonction**: `zero_click_import`

**Paramètres**:
- `file`: `UploadFile` (défaut: `File(...)`)
- `margin_percent`: `float` (défaut: `Form(40.0)`)
- `supplier_hint`: `str | None` (défaut: `Form(default=None)`)
- `auto_confirm`: `bool` (défaut: `Form(default=True)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def zero_click_import( file: UploadFile = File(...),
```

---

### `POST` /zero-click/jobs

**Fonction**: `zero_click_job`

Lance un job zero-click async et retourne immédiatement le job_id pour polling.

**Paramètres**:
- `file`: `UploadFile` (défaut: `File(...)`)
- `margin_percent`: `float` (défaut: `Form(40.0)`)
- `supplier_hint`: `str | None` (défaut: `Form(default=None)`)
- `auto_confirm`: `bool` (défaut: `Form(default=True)`)
- `session_id`: `str | None` (défaut: `Form(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def zero_click_job( file: UploadFile = File(...),
```

---

### `GET` /zero-click/jobs

**Fonction**: `list_zero_click_jobs`

Liste les jobs zero-click récents pour le tenant courant.

**Paramètres**:
- `status`: `str | None` (défaut: `None`)
- `session_id`: `str | None` (défaut: `None`)
- `limit`: `int` (défaut: `50`)
- `offset`: `int` (défaut: `0`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def list_zero_click_jobs( status: str | None = None,
```

---

### `GET` /zero-click/jobs/{job_id}

**Fonction**: `get_zero_click_job`

Récupère le statut d'un job zero-click par son ID.

**Paramètres**:
- `job_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_zero_click_job(job_id: str, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `GET` /match-suggestions

**Fonction**: `get_product_match_suggestions`

Retourne des suggestions de matching flou pour un nom de produit.

**Paramètres**:
- `query`: `str`
- `max_results`: `int` (défaut: `5`)
- `min_score`: `float` (défaut: `60.0`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_product_match_suggestions( query: str,
```

---

### `GET` /sessions

**Fonction**: `list_import_sessions`

Liste les sessions d'import avec statistiques agrégées.

**Paramètres**:
- `limit`: `int` (défaut: `50`)
- `offset`: `int` (défaut: `0`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def list_import_sessions( limit: int = 50,
```

---

### `GET` /sessions/{session_id}

**Fonction**: `get_import_session_details`

Récupère les détails d'une session d'import avec tous ses imports.

**Paramètres**:
- `session_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_import_session_details( session_id: str,
```

---

### `GET` /history

**Fonction**: `get_invoice_history`

**Paramètres**:
- `supplier`: `str | None` (défaut: `None`)
- `invoice_id`: `str | None` (défaut: `None`)
- `date_start`: `str | None` (défaut: `None`)
- `date_end`: `str | None` (défaut: `None`)
- `limit`: `int` (défaut: `100`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_invoice_history( supplier: str | None = None,
```

---

### `GET` /history/{invoice_id}/file

**Fonction**: `download_invoice_file`

**Paramètres**:
- `invoice_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def download_invoice_file(invoice_id: str, tenant: Tenant = Depends(get_current_tenant)):
```

---


## Module: `maintenance`

**Fichier**: `backend/api/maintenance.py`

### `GET` /backups

**Fonction**: `list_backups`

**Paramètres**:
- `limit`: `int` (défaut: `Query(default=100, ge=1, le=1000)`)

```python
def list_backups(limit: int = Query(default=100, ge=1, le=1000)):
```

---

### `GET` /backups/{filename}

**Fonction**: `download_backup`

**Paramètres**:
- `filename`: `str`

```python
def download_backup(filename: str):
```

---


## Module: `margins`

**Fichier**: `backend/api/margins.py`

### `POST` /calculate

**Fonction**: `calculate_margin`

Calcule les marges brute, opérationnelle et nette.

**Paramètres**:
- `request`: `MarginRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def calculate_margin( request: MarginRequest,
```

---

### `GET` /products

**Fonction**: `get_product_margins`

Retourne les marges par produit avec:

**Paramètres**:
- `category`: `Optional[str]` (défaut: `Query(default=None)`)
- `min_margin_pct`: `Optional[float]` (défaut: `Query(default=None)`)
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `sort_by`: `str` (défaut: `Query(default='total_margin', regex='^(gross_margin_pct|total_margin|volume_sold)$')`)
- `limit`: `int` (défaut: `Query(default=100, le=500)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_product_margins( category: Optional[str] = Query(default=None),
```

---

### `GET` /categories

**Fonction**: `get_category_margins`

Retourne les marges agrégées par catégorie de produits.

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_category_margins( days_back: int = Query(default=30, ge=1, le=365),
```

---

### `GET` /pamp/{product_id}

**Fonction**: `get_product_pamp`

Retourne le PAMP (Prix d'Achat Moyen Pondéré) d'un produit

**Paramètres**:
- `product_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_product_pamp( product_id: int,
```

---

### `GET` /dishes

**Fonction**: `get_dish_margins`

Retourne les marges des plats du restaurant avec détail des ingrédients.

**Paramètres**:
- `min_margin_pct`: `Optional[float]` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_dish_margins( min_margin_pct: Optional[float] = Query(default=None),
```

---

### `GET` /alerts

**Fonction**: `get_margin_alerts`

Retourne les alertes pour les produits avec des marges problématiques:

**Paramètres**:
- `threshold_pct`: `float` (défaut: `Query(default=20.0, ge=0, le=100)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_margin_alerts( threshold_pct: float = Query(default=20.0, ge=0, le=100),
```

---

### `GET` /summary

**Fonction**: `get_margin_summary`

Résumé des marges:

**Paramètres**:
- `days_back`: `int` (défaut: `Query(default=30, ge=1, le=365)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_margin_summary( days_back: int = Query(default=30, ge=1, le=365),
```

---


## Module: `newcms.cockpit`

**Fichier**: `backend/api/newcms/cockpit.py`

### `GET` N/A

**Fonction**: `get_morning_brief_cockpit`

**Morning Brief Cockpit - Vue agrégée complète**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)
- `days_forecast`: `int` (défaut: `Query(default=7, ge=1, le=30, description='Horizon de prevision en jours')`)
- `top_anomalies_limit`: `int` (défaut: `Query(default=5, ge=1, le=20, description="Nombre d'anomalies a afficher")`)

```python
async def get_morning_brief_cockpit( tenant: Tenant = Depends(get_current_tenant),
```

---

### `GET` /actions

**Fonction**: `get_cockpit_actions`

**Call-to-Actions - Liste des actions actionnables**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)
- `category`: `Optional[str]` (défaut: `Query(default=None, description='Filtrer par categorie: urgent, important, suggested')`)

```python
async def get_cockpit_actions( tenant: Tenant = Depends(get_current_tenant),
```

---


## Module: `newcms.finance`

**Fichier**: `backend/api/newcms/finance.py`

### `GET` /overview

**Fonction**: `get_finance_overview`

**Finance Overview - Vue d'ensemble financière complète**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `FinanceOverviewResponse`

```python
def get_finance_overview( tenant: Tenant = Depends(get_current_tenant_or_default)
```

---

### `GET` /transactions

**Fonction**: `get_transactions`

**Liste paginée des transactions bancaires**

**Paramètres**:
- `q`: `Optional[str]` (défaut: `Query(None, description='Recherche texte sur libellé')`)
- `date_from`: `Optional[date]` (défaut: `Query(None, description='Date de début')`)
- `date_to`: `Optional[date]` (défaut: `Query(None, description='Date de fin')`)
- `amount_min`: `Optional[float]` (défaut: `Query(None, ge=0, description='Montant minimum')`)
- `amount_max`: `Optional[float]` (défaut: `Query(None, ge=0, description='Montant maximum')`)
- `direction`: `Optional[str]` (défaut: `Query(None, description='Direction (IN/OUT/TRANSFER)')`)
- `category`: `Optional[str]` (défaut: `Query(None, description='Catégorie')`)
- `page`: `int` (défaut: `Query(1, ge=1, description='Numéro de page')`)
- `per_page`: `int` (défaut: `Query(50, ge=1, le=100, description="Nombre d'items par page")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `TransactionListResponse`

```python
def get_transactions( q: Optional[str] = Query(None, description="Recherche texte sur libellé"),
```

---

### `POST` /reconciliation/apply

**Fonction**: `apply_reconciliation_suggestion`

**Appliquer une suggestion de rapprochement IA**

**Paramètres**:
- `request`: `ApplyReconciliationRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `ApplyReconciliationResponse`

```python
def apply_reconciliation_suggestion( request: ApplyReconciliationRequest,
```

---

### `POST` /transactions/{transaction_id}/categorize

**Fonction**: `categorize_transaction`

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `CategorizeRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def categorize_transaction( transaction_id: int,
```

---

### `POST` /transactions/{transaction_id}/ignore

**Fonction**: `ignore_transaction`

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `IgnoreRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def ignore_transaction( transaction_id: int,
```

---

### `POST` /transactions/{transaction_id}/reconcile-manual

**Fonction**: `manual_reconcile_transaction`

**Paramètres**:
- `transaction_id`: `int`
- `payload`: `ManualReconcileRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def manual_reconcile_transaction( transaction_id: int,
```

---

### `POST` /transactions/bulk-export

**Fonction**: `export_transactions`

**Paramètres**:
- `filters`: `ExportFilter`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def export_transactions( filters: ExportFilter,
```

---

### `GET` /rules

**Fonction**: `list_finance_rules`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def list_finance_rules( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `POST` /rules

**Fonction**: `create_finance_rule`

**Paramètres**:
- `payload`: `FinanceRuleCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def create_finance_rule( payload: FinanceRuleCreate,
```

---

### `PUT` /rules/{rule_id}

**Fonction**: `update_finance_rule`

**Paramètres**:
- `rule_id`: `str`
- `payload`: `FinanceRuleCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def update_finance_rule( rule_id: str,
```

---

### `DELETE` /rules/{rule_id}

**Fonction**: `delete_finance_rule`

**Paramètres**:
- `rule_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def delete_finance_rule( rule_id: str,
```

---

### `POST` /rules/apply

**Fonction**: `apply_finance_rules`

**Paramètres**:
- `payload`: `ApplyRulesRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def apply_finance_rules( payload: ApplyRulesRequest,
```

---

### `GET` /accounts

**Fonction**: `list_accounts`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def list_accounts( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `POST` /accounts/refresh

**Fonction**: `refresh_accounts`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def refresh_accounts( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `POST` /accounts/simulate-cashflow

**Fonction**: `simulate_cashflow`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict`

```python
def simulate_cashflow( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `GET` /categories

**Fonction**: `list_finance_categories`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `list[FinanceCategoryResponse]`

```python
def list_finance_categories( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---


## Module: `newcms.intelligence`

**Fichier**: `backend/api/newcms/intelligence.py`

### `GET` /overview

**Fonction**: `get_intelligence_overview`

**Intelligence Overview - IA & Analytics**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_intelligence_overview( tenant: Tenant = Depends(get_current_tenant)
```

---

### `GET` /recommendations

**Fonction**: `get_recommendations`

**Liste complète des recommandations IA**

**Paramètres**:
- `priority`: `Optional[PriorityLevel]` (défaut: `Query(default=None)`)
- `type`: `Optional[RecommendationType]` (défaut: `Query(default=None)`)
- `limit`: `int` (défaut: `Query(default=20, le=100)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_recommendations( priority: Optional[PriorityLevel] = Query(default=None),
```

---

### `POST` /recommendations/{recommendation_id}/apply

**Fonction**: `apply_recommendation`

**Appliquer une recommandation IA**

**Paramètres**:
- `recommendation_id`: `str`
- `action_index`: `int` (défaut: `Query(default=0, ge=0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def apply_recommendation( recommendation_id: str,
```

---

### `GET` /health-score

**Fonction**: `get_health_score`

**Score de santé global - Note unique (0-10)**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_health_score( tenant: Tenant = Depends(get_current_tenant)
```

---

### `GET` /metrics/summary

**Fonction**: `get_metrics_summary`

**Résumé des métriques - Pour graphiques dashboard**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_metrics_summary( tenant: Tenant = Depends(get_current_tenant)
```

---


## Module: `newcms.operations`

**Fichier**: `backend/api/newcms/operations.py`

### `GET` /overview

**Fonction**: `get_operations_overview`

**Operations Overview - Vue d'ensemble opérationnelle**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `OperationsOverviewResponse`

```python
async def get_operations_overview( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `GET` /catalog

**Fonction**: `get_catalog_proxy`

**Catalogue produits - Liste paginée**

**Paramètres**:
- `page`: `int` (défaut: `Query(default=1, ge=1, le=10000, description='Numéro de page')`)
- `per_page`: `int` (défaut: `Query(default=20, ge=1, le=100, description='Éléments par page (max 100)')`)
- `q`: `str | None` (défaut: `Query(default=None, description='Recherche textuelle (nom produit)')`)
- `category`: `str | None` (défaut: `Query(default=None, description='Filtrer par catégorie')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `CatalogProxyResponse`

```python
async def get_catalog_proxy( page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
```

---

### `GET` /stock

**Fonction**: `get_stock_proxy`

**Stock produits - Liste paginée avec statuts**

**Paramètres**:
- `page`: `int` (défaut: `Query(default=1, ge=1, le=10000, description='Numéro de page')`)
- `per_page`: `int` (défaut: `Query(default=20, ge=1, le=100, description='Éléments par page (max 100)')`)
- `q`: `str | None` (défaut: `Query(default=None, description='Recherche textuelle')`)
- `status`: `str | None` (défaut: `Query(default=None, description='Filtrer par statut: critical, low, ok')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `StockProxyResponse`

```python
async def get_stock_proxy( page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
```

---

### `GET` /invoices

**Fonction**: `get_invoices_proxy`

**Factures traitées - Liste paginée**

**Paramètres**:
- `page`: `int` (défaut: `Query(default=1, ge=1, le=10000, description='Numéro de page')`)
- `per_page`: `int` (défaut: `Query(default=20, ge=1, le=100, description='Éléments par page (max 100)')`)
- `status`: `str | None` (défaut: `Query(default=None, description='Statut (non implémenté)')`)
- `date_from`: `str | None` (défaut: `Query(default=None, description='Date début (YYYY-MM-DD)')`)
- `date_to`: `str | None` (défaut: `Query(default=None, description='Date fin (YYYY-MM-DD)')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `InvoicesProxyResponse`

```python
async def get_invoices_proxy( page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
```

---

### `POST` /invoices/import

**Fonction**: `create_invoice_import`

Reçoit un fichier (base64) et crée un job d'import dans un stockage léger.

**Paramètres**:
- `payload`: `InvoiceImportUploadRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `InvoiceImportStatusResponse`

```python
async def create_invoice_import( payload: InvoiceImportUploadRequest,
```

---

### `GET` /invoices/import/{job_id}

**Fonction**: `get_invoice_import_status`

**Paramètres**:
- `job_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `InvoiceImportStatusResponse`

```python
async def get_invoice_import_status( job_id: str,
```

---

### `POST` /invoices/import/{job_id}/lines/{line_id}

**Fonction**: `update_invoice_import_line`

**Paramètres**:
- `job_id`: `str`
- `line_id`: `str`
- `payload`: `InvoiceImportLineUpdateRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `InvoiceImportActionResponse`

```python
async def update_invoice_import_line( job_id: str,
```

---

### `POST` /invoices/import/{job_id}/confirm

**Fonction**: `confirm_invoice_import`

**Paramètres**:
- `job_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `InvoiceImportActionResponse`

```python
async def confirm_invoice_import( job_id: str,
```

---

### `POST` /invoices/import/{job_id}/cancel

**Fonction**: `cancel_invoice_import`

**Paramètres**:
- `job_id`: `str`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `InvoiceImportActionResponse`

```python
async def cancel_invoice_import( job_id: str,
```

---

### `POST` /invoices/email-webhook

**Fonction**: `email_webhook_import`

**Paramètres**:
- `payload`: `EmailWebhookPayload`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `dict[str, Any]`

```python
async def email_webhook_import( payload: EmailWebhookPayload,
```

---

### `POST` /price-anomalies/{product_id}/resolve

**Fonction**: `resolve_price_anomaly`

**Paramètres**:
- `product_id`: `int`
- `payload`: `PriceAnomalyResolveRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `PriceAnomalyResolveResponse`

```python
async def resolve_price_anomaly( product_id: int,
```

---

### `POST` /orders

**Fonction**: `create_supplier_order`

**Paramètres**:
- `payload`: `CreateOrderRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `CreateOrderResponse`

```python
async def create_supplier_order( payload: CreateOrderRequest,
```

---


## Module: `newcms.restaurant`

**Fichier**: `backend/api/newcms/restaurant.py`

### `GET` /overview

**Fonction**: `get_restaurant_overview`

**Restaurant Overview - Vue d'ensemble restaurant**

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_restaurant_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

---

### `GET` /menus/overview

**Fonction**: `get_menus_overview`

Vue d'ensemble Menus & Coûts (food cost, marges, alertes ingrédients)

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_menus_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

---

### `GET` /plat/{plat_id}

**Fonction**: `get_plat_detail`

Détail d'un plat restaurant (fiche technique, prix, marge).

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_plat_detail( plat_id: int,
```

---

### `GET` /inventory

**Fonction**: `get_mobile_inventory`

**Inventaire mobile - Liste paginée**

**Paramètres**:
- `page`: `int` (défaut: `Query(1, ge=1)`)
- `page_size`: `int` (défaut: `Query(50, ge=1, le=200)`)
- `search`: `Optional[str]` (défaut: `None`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def get_mobile_inventory( page: int = Query(1, ge=1),
```

---

### `POST` /scan

**Fonction**: `scan_barcode`

**Scan code-barres - Recherche par EAN**

**Paramètres**:
- `payload`: `MobileScanRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def scan_barcode( payload: MobileScanRequest,
```

---

### `POST` /adjust

**Fonction**: `adjust_stock`

**Ajustement stock - Correction depuis mobile**

**Paramètres**:
- `payload`: `MobileAdjustRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

```python
def adjust_stock( payload: MobileAdjustRequest,
```

---


## Module: `prices`

**Fichier**: `backend/api/prices.py`

### `GET` /history

**Fonction**: `get_price_history`

**Paramètres**:
- `product_id`: `Optional[int]` (défaut: `Query(default=None, alias='product_id')`)
- `code`: `Optional[str]` (défaut: `None`)
- `supplier`: `Optional[str]` (défaut: `None`)
- `search`: `Optional[str]` (défaut: `None`)
- `date_start`: `Optional[datetime]` (défaut: `Query(default=None)`)
- `date_end`: `Optional[datetime]` (défaut: `Query(default=None)`)
- `limit`: `int` (défaut: `Query(default=500, ge=1, le=2000)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_price_history( product_id: Optional[int] = Query(default=None, alias="product_id"),
```

---

### `GET` /latest

**Fonction**: `get_latest_price_history`

**Paramètres**:
- `codes`: `list[str] | None` (défaut: `Query(default=None, description='Filtrer sur une liste de codes (répéter le param).')`)
- `limit`: `int` (défaut: `Query(default=100, ge=1, le=500)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_latest_price_history( codes: list[str] | None = Query(default=None, description="Filtrer sur une liste de codes (répéter le param)."),
```

---

### `POST` /bulk-fill

**Fonction**: `bulk_fill_prices`

Met à jour en masse les prix manquants à partir d'une liste (product_id ou code).

**Paramètres**:
- `payload`: `BulkPriceCorrectionRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def bulk_fill_prices(payload: BulkPriceCorrectionRequest, tenant: Tenant = Depends(get_current_tenant)):
```

---

### `POST` /fill-from-history

**Fonction**: `fill_prices_from_history`

Tente de remplir prix_achat/prix_vente manquants depuis l'historique produits_price_history.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

**Retour**: `dict`

```python
def fill_prices_from_history(tenant: Tenant = Depends(get_current_tenant)) -> dict:
```

---


## Module: `reports`

**Fichier**: `backend/api/reports.py`

### `GET` /overview

**Fonction**: `get_reports_overview`

Retourne les analytics agrégées pour l'espace rapports.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_reports_overview(tenant: Tenant = Depends(get_current_tenant)):
```

---

### `GET` /export/{report_type}

**Fonction**: `export_report_dataset`

Diffuse un export CSV pour le dataset demandé.

**Paramètres**:
- `report_type`: `str`
- `limit`: `int` (défaut: `Query(default=5000, ge=10, le=50000)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def export_report_dataset( report_type: str,
```

---


## Module: `restaurant`

**Fichier**: `backend/api/restaurant.py`

### `GET` /charges/categories

**Fonction**: `list_categories`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_categories(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /charges/categories

**Fonction**: `create_category`

**Paramètres**:
- `payload`: `RestaurantCategoryCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def create_category(payload: RestaurantCategoryCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /charges/cost-centers

**Fonction**: `list_cost_centers`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_cost_centers(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /charges/cost-centers

**Fonction**: `create_cost_center`

**Paramètres**:
- `payload`: `RestaurantCostCenterCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def create_cost_center(payload: RestaurantCostCenterCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /charges/expenses

**Fonction**: `list_expenses`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_expenses(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /charges/expenses

**Fonction**: `create_expense`

**Paramètres**:
- `payload`: `RestaurantExpenseCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def create_expense(payload: RestaurantExpenseCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /charges/summary

**Fonction**: `expense_summary`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def expense_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /charges/tva-summary

**Fonction**: `tva_summary`

**Paramètres**:
- `months`: `int` (défaut: `Query(6, ge=1, le=24)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def tva_summary( months: int = Query(6, ge=1, le=24),
```

---

### `GET` /ingredients

**Fonction**: `list_ingredients`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_ingredients(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /ingredients

**Fonction**: `create_ingredient`

**Paramètres**:
- `payload`: `RestaurantIngredientCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def create_ingredient(payload: RestaurantIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `PUT` /ingredients/{ingredient_id}

**Fonction**: `update_ingredient`

Mettre à jour un ingrédient (nom, unité, coût, stock, catégorie, fournisseur).

**Paramètres**:
- `ingredient_id`: `int`
- `payload`: `RestaurantIngredientUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def update_ingredient( ingredient_id: int,
```

---

### `DELETE` /ingredients/{ingredient_id}

**Fonction**: `delete_ingredient`

Supprimer un ingrédient. Échoue si l'ingrédient est utilisé dans des plats.

**Paramètres**:
- `ingredient_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def delete_ingredient( ingredient_id: int,
```

---

### `PATCH` /ingredients/{ingredient_id}/price

**Fonction**: `update_ingredient_price`

**Paramètres**:
- `ingredient_id`: `int`
- `payload`: `RestaurantIngredientPriceUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def update_ingredient_price( ingredient_id: int,
```

---

### `GET` /ingredients/{ingredient_id}/price-history

**Fonction**: `ingredient_price_history`

**Paramètres**:
- `ingredient_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def ingredient_price_history( ingredient_id: int,
```

---

### `PUT` /ingredients/{ingredient_id}/link-epicerie

**Fonction**: `link_ingredient_to_epicerie`

Lier un ingrédient à un produit épicerie pour synchroniser catégorie/fournisseur.

**Paramètres**:
- `ingredient_id`: `int`
- `payload`: `RestaurantIngredientEpicerieLink`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def link_ingredient_to_epicerie( ingredient_id: int,
```

---

### `PATCH` /ingredients/{ingredient_id}/ratio

**Fonction**: `update_ingredient_ratio`

Mettre à jour le ratio de conversion ingrédient-épicerie.

**Paramètres**:
- `ingredient_id`: `int`
- `payload`: `RestaurantIngredientRatioUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def update_ingredient_ratio( ingredient_id: int,
```

---

### `DELETE` /ingredients/{ingredient_id}/link-epicerie

**Fonction**: `unlink_ingredient_from_epicerie`

Supprimer le lien entre un ingrédient et un produit épicerie.

**Paramètres**:
- `ingredient_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def unlink_ingredient_from_epicerie( ingredient_id: int,
```

---

### `POST` /ingredients/sync-prices

**Fonction**: `sync_ingredient_prices`

Synchronise les prix des ingrédients à partir des produits épicerie liés.

**Paramètres**:
- `force_update`: `bool` (défaut: `Query(False, description='Force update all linked ingredients')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def sync_ingredient_prices( force_update: bool = Query(False, description="Force update all linked ingredients"),
```

---

### `GET` /ingredients/price-sync-status

**Fonction**: `get_price_sync_status`

Retourne le statut de synchronisation des prix pour tous les ingrédients.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_price_sync_status(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /ingredients/audit-epicerie-links

**Fonction**: `audit_ingredient_epicerie_links`

Audit des liens incohérents ingrédients ↔ épicerie (ex: ail lié à un whisky).

**Paramètres**:
- `dry_run`: `bool` (défaut: `Query(True, description='Ne pas modifier; uniquement lister les liens incohérents.')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def audit_ingredient_epicerie_links( dry_run: bool = Query(True, description="Ne pas modifier; uniquement lister les liens incohérents."),
```

---

### `GET` /ingredients/with-price-source

**Fonction**: `list_ingredients_with_price_source`

Liste les ingrédients avec indication explicite de la source de prix.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_ingredients_with_price_source(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /stock/movements

**Fonction**: `list_stock_movements`

Liste les mouvements de stock restaurant avec filtres.

**Paramètres**:
- `ingredient_id`: `Optional[int]` (défaut: `None`)
- `source`: `Optional[str]` (défaut: `None`)
- `type_mouvement`: `Optional[str]` (défaut: `None`)
- `date_from`: `Optional[date]` (défaut: `None`)
- `date_to`: `Optional[date]` (défaut: `None`)
- `limit`: `int` (défaut: `Query(100, ge=1, le=50000)`)
- `offset`: `int` (défaut: `Query(0, ge=0)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_stock_movements( ingredient_id: Optional[int] = None,
```

---

### `GET` /stock/movements/daily-by-category

**Fonction**: `get_daily_movements_by_category`

Agrégation des mouvements par jour et catégorie pour graphiques.

**Paramètres**:
- `date_from`: `Optional[date]` (défaut: `None`)
- `date_to`: `Optional[date]` (défaut: `None`)
- `type_mouvement`: `str` (défaut: `Query('sortie', description='Type de mouvement à agréger')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_daily_movements_by_category( date_from: Optional[date] = None,
```

---

### `GET` /stock/movements/daily-by-plat

**Fonction**: `get_daily_consumption_by_plat`

Agrégation des consommations (sorties) par jour et par plat pour graphiques.

**Paramètres**:
- `date_from`: `Optional[date]` (défaut: `None`)
- `date_to`: `Optional[date]` (défaut: `None`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_daily_consumption_by_plat( date_from: Optional[date] = None,
```

---

### `GET` /stock/summary

**Fonction**: `get_stock_summary`

Résumé du stock actuel par ingrédient.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_stock_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /stock/analytics

**Fonction**: `get_stock_analytics`

Statistiques de stock sur une période.

**Paramètres**:
- `days`: `int` (défaut: `Query(30, ge=1, le=365)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_stock_analytics( days: int = Query(30, ge=1, le=365),
```

---

### `POST` /stock/movements

**Fonction**: `create_stock_movement`

Crée un mouvement de stock.

**Paramètres**:
- `ingredient_id`: `int` (défaut: `Body(...)`)
- `type_mouvement`: `str` (défaut: `Body(...)`)
- `quantite`: `float` (défaut: `Body(...)`)
- `source`: `str` (défaut: `Body(...)`)
- `unite`: `Optional[str]` (défaut: `Body(None)`)
- `cout_unitaire`: `Optional[float]` (défaut: `Body(None)`)
- `facture_id`: `Optional[int]` (défaut: `Body(None)`)
- `facture_ref`: `Optional[str]` (défaut: `Body(None)`)
- `fournisseur`: `Optional[str]` (défaut: `Body(None)`)
- `produit_epicerie_id`: `Optional[int]` (défaut: `Body(None)`)
- `commentaire`: `Optional[str]` (défaut: `Body(None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def create_stock_movement( ingredient_id: int = Body(...),
```

---

### `POST` /stock/transfer-from-epicerie

**Fonction**: `transfer_from_epicerie`

Transfère du stock depuis un produit épicerie.

**Paramètres**:
- `ingredient_id`: `int` (défaut: `Body(...)`)
- `produit_epicerie_id`: `int` (défaut: `Body(...)`)
- `quantite`: `float` (défaut: `Body(...)`)
- `commentaire`: `Optional[str]` (défaut: `Body(None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def transfer_from_epicerie( ingredient_id: int = Body(...),
```

---

### `POST` /stock/adjustment

**Fonction**: `adjust_stock`

Ajuste le stock à une nouvelle quantité (inventaire).

**Paramètres**:
- `ingredient_id`: `int` (défaut: `Body(...)`)
- `new_quantity`: `float` (défaut: `Body(...)`)
- `commentaire`: `Optional[str]` (défaut: `Body(None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def adjust_stock( ingredient_id: int = Body(...),
```

---

### `POST` /stock/consumption

**Fonction**: `record_consumption`

Enregistre une sortie de stock pour consommation.

**Paramètres**:
- `ingredient_id`: `int` (défaut: `Body(...)`)
- `quantite`: `float` (défaut: `Body(...)`)
- `commentaire`: `Optional[str]` (défaut: `Body(None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def record_consumption( ingredient_id: int = Body(...),
```

---

### `GET` /plats

**Fonction**: `list_plats`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_plats(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /plats

**Fonction**: `create_plat`

**Paramètres**:
- `payload`: `RestaurantPlatCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def create_plat(payload: RestaurantPlatCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `DELETE` /plats/{plat_id}

**Fonction**: `delete_plat`

Supprimer un plat et ses ingrédients associés.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def delete_plat(plat_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `POST` /plats/{plat_id}/ingredients

**Fonction**: `attach_ingredient`

**Paramètres**:
- `plat_id`: `int`
- `payload`: `RestaurantPlatIngredientCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def attach_ingredient(plat_id: int, payload: RestaurantPlatIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `DELETE` /plats/{plat_id}/ingredients/{ingredient_id}

**Fonction**: `remove_ingredient`

**Paramètres**:
- `plat_id`: `int`
- `ingredient_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def remove_ingredient(plat_id: int, ingredient_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `PATCH` /plats/{plat_id}/ingredients/{ingredient_id}

**Fonction**: `update_ingredient_on_plat`

Met à jour la quantité/unité d'un ingrédient sur un plat.

**Paramètres**:
- `plat_id`: `int`
- `ingredient_id`: `int`
- `payload`: `RestaurantPlatIngredientUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def update_ingredient_on_plat( plat_id: int,
```

---

### `PATCH` /plats/{plat_id}/price

**Fonction**: `update_plat_price`

**Paramètres**:
- `plat_id`: `int`
- `payload`: `RestaurantPlatPriceUpdate`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def update_plat_price( plat_id: int,
```

---

### `GET` /plats/{plat_id}/price-history

**Fonction**: `plat_price_history`

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def plat_price_history( plat_id: int,
```

---

### `POST` /plats/recompute-costs

**Fonction**: `recompute_plat_costs`

**Paramètres**:
- `margin_threshold`: `float` (défaut: `Body(35.0, ge=1.0, description='Seuil de marge (%) pour générer des alertes.')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def recompute_plat_costs( margin_threshold: float = Body(35.0, ge=1.0, description="Seuil de marge (%) pour générer des alertes."),
```

---

### `GET` /plats/{plat_id}/composition

**Fonction**: `plat_composition`

Retourne la composition d'un plat avec coûts par ingrédient et pourcentage.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def plat_composition( plat_id: int,
```

---

### `POST` /transfer

**Fonction**: `transfer_from_epicerie`

Transfère du stock depuis l'épicerie vers le restaurant via la fonction SQL transfer_from_epicerie.

**Paramètres**:
- `produit_restaurant_id`: `int` (défaut: `Body(..., embed=True)`)
- `quantite`: `float` (défaut: `Body(1.0, ge=0.0001, embed=True)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def transfer_from_epicerie( produit_restaurant_id: int = Body(..., embed=True),
```

---

### `GET` /consumptions

**Fonction**: `list_consumptions`

Liste des consommations avec filtre de période optionnel.

**Paramètres**:
- `period`: `str` (défaut: `Query('all', description='Période: 7d, 30d, 90d, 1y, all')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_consumptions( period: str = Query("all", description="Période: 7d, 30d, 90d, 1y, all"),
```

---

### `GET` /price-history/comparison

**Fonction**: `list_price_history_comparison`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_price_history_comparison(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /epicerie/products

**Fonction**: `list_epicerie_products`

List all epicerie products available for mapping.

```python
def list_epicerie_products():
```

---

### `GET` /epicerie/products/search

**Fonction**: `search_epicerie_products`

Fast search endpoint for epicerie products.

**Paramètres**:
- `q`: `str` (défaut: `Query('', description='Search query')`)
- `limit`: `int` (défaut: `Query(20, ge=1, le=100)`)
- `suggest_for`: `str` (défaut: `Query(None, description='Ingredient name to get smart suggestions')`)

```python
def search_epicerie_products( q: str = Query("", description="Search query"),
```

---

### `GET` /alerts

**Fonction**: `list_restaurant_alerts`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_restaurant_alerts(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /dashboard/overview

**Fonction**: `restaurant_dashboard_overview`

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def restaurant_dashboard_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /forecasts/overview

**Fonction**: `restaurant_forecast_overview`

**Paramètres**:
- `horizon_days`: `int` (défaut: `Query(30, ge=1, le=180)`)
- `granularity`: `str` (défaut: `Query('weekly')`)
- `top`: `int` (défaut: `Query(8, ge=1, le=50)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def restaurant_forecast_overview( horizon_days: int = Query(30, ge=1, le=180),
```

---

### `GET` /prices/history

**Fonction**: `price_history_overview`

**Paramètres**:
- `limit`: `int` (défaut: `Query(12, ge=1, le=200)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def price_history_overview( limit: int = Query(12, ge=1, le=200),
```

---

### `GET` /overview

**Fonction**: `get_restaurant_overview`

Vue d'ensemble du restaurant.

**Paramètres**:
- `period`: `str` (défaut: `Query('30d', description='Période: 7d, 30d, 90d, 1y')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_restaurant_overview( period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
```

---

### `GET` /plats/list

**Fonction**: `list_plats_paginated`

Liste paginée des plats avec filtres et tri.

**Paramètres**:
- `page`: `int` (défaut: `Query(1, ge=1)`)
- `page_size`: `int` (défaut: `Query(50, ge=1, le=200)`)
- `categorie`: `str | None` (défaut: `Query(None)`)
- `actif`: `bool | None` (défaut: `Query(None)`)
- `min_margin_pct`: `float | None` (défaut: `Query(None)`)
- `sort_by`: `str` (défaut: `Query('nom', description='nom, margin_pct, sales_count, prix_vente_ttc')`)
- `sort_desc`: `bool` (défaut: `Query(False)`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_plats_paginated( page: int = Query(1, ge=1),
```

---

### `GET` /plats/{plat_id}/detail

**Fonction**: `get_plat_detail`

Détails complets d'un plat.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_plat_detail( plat_id: int,
```

---

### `GET` /plats/{plat_id}/cost-breakdown

**Fonction**: `get_plat_cost_breakdown`

Décomposition détaillée du coût d'un plat.

**Paramètres**:
- `plat_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_plat_cost_breakdown( plat_id: int,
```

---

### `GET` /ingredients/list

**Fonction**: `list_ingredients_enhanced`

Liste enrichie des ingrédients.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_ingredients_enhanced(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---

### `GET` /ingredients/{ingredient_id}/price-history-detail

**Fonction**: `get_ingredient_price_history_detail`

Historique détaillé des prix d'un ingrédient.

**Paramètres**:
- `ingredient_id`: `int`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_ingredient_price_history_detail( ingredient_id: int,
```

---

### `GET` /food-cost/analysis

**Fonction**: `get_food_cost_analysis`

Analyse complète du food cost.

**Paramètres**:
- `period`: `str` (défaut: `Query('30d', description='Période: 7d, 30d, 90d, 1y')`)
- `target_food_cost`: `float` (défaut: `Query(30.0, ge=0, le=100, description='Food cost cible en %')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_food_cost_analysis( period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
```

---

### `POST` /plats/{plat_id}/simulate-price

**Fonction**: `simulate_plat_price_change`

Simulation de changement de prix.

**Paramètres**:
- `plat_id`: `int`
- `payload`: `PriceSimulationInput`
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def simulate_plat_price_change( plat_id: int,
```

---

### `GET` /alerts/detailed

**Fonction**: `list_restaurant_alerts_detailed`

Liste détaillée des alertes restaurant.

**Paramètres**:
- `alert_type`: `str | None` (défaut: `Query(None, description='plat_margin, ingredient_price, stock_rupture')`)
- `severity`: `str | None` (défaut: `Query(None, description='critical, warning, info')`)
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def list_restaurant_alerts_detailed( alert_type: str | None = Query(None, description="plat_margin, ingredient_price, stock_rupture"),
```

---

### `GET` /menus/overview

**Fonction**: `get_restaurant_menus_overview`

Vue d'ensemble des menus : coûts matière, food cost, alertes ingrédients.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_restaurant_tenant)`)

```python
def get_restaurant_menus_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
```

---


## Module: `routes`

**Fichier**: `backend/api/routes.py`

### `GET` N/A

**Fonction**: `include_routes`

**Paramètres**:
- `app`: `FastAPI`

**Retour**: `None`

```python
def include_routes(app: FastAPI) -> None:
```

---


## Module: `rules_engine`

**Fichier**: `backend/api/rules_engine.py`

### `POST` /classify

**Fonction**: `classify_transaction`

Classifie une transaction unique.

**Paramètres**:
- `transaction`: `TransactionInput`
- `detect_anomalies`: `bool` (défaut: `Query(True, description='Détecter les anomalies')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def classify_transaction( transaction: TransactionInput,
```

---

### `POST` /classify/batch

**Fonction**: `classify_batch`

Classifie un lot de transactions.

**Paramètres**:
- `request`: `BatchClassificationRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def classify_batch( request: BatchClassificationRequest,
```

---

### `GET` /rules

**Fonction**: `list_rules`

Liste toutes les règles de catégorisation.

**Paramètres**:
- `active_only`: `bool` (défaut: `Query(True, description='Uniquement les règles actives')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def list_rules( active_only: bool = Query(True, description="Uniquement les règles actives"),
```

---

### `POST` /rules

**Fonction**: `create_rule`

Crée une nouvelle règle de catégorisation.

**Paramètres**:
- `rule`: `RuleCreate`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def create_rule( rule: RuleCreate,
```

---

### `POST` /feedback

**Fonction**: `record_feedback`

Enregistre un feedback sur une classification.

**Paramètres**:
- `feedback`: `FeedbackRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def record_feedback( feedback: FeedbackRequest,
```

---

### `POST` /bootstrap

**Fonction**: `bootstrap_rules`

Initialise les règles par défaut pour le tenant.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def bootstrap_rules( tenant: Tenant = Depends(get_current_tenant),
```

---

### `GET` /stats

**Fonction**: `get_classification_stats`

Retourne des statistiques sur les classifications.

**Paramètres**:
- `days`: `int` (défaut: `Query(30, description="Nombre de jours d'historique")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def get_classification_stats( days: int = Query(30, description="Nombre de jours d'historique"),
```

---

### `GET` /suggest

**Fonction**: `suggest_category`

Suggère une catégorie pour une transaction (endpoint léger).

**Paramètres**:
- `description`: `str` (défaut: `Query(..., description='Description de la transaction')`)
- `amount`: `Optional[float]` (défaut: `Query(None, description='Montant')`)
- `supplier`: `Optional[str]` (défaut: `Query(None, description='Fournisseur')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
async def suggest_category( description: str = Query(..., description="Description de la transaction"),
```

---


## Module: `stock`

**Fichier**: `backend/api/stock.py`

### `GET` /movements/timeseries

**Fonction**: `get_movement_timeseries`

**Paramètres**:
- `window_days`: `int` (défaut: `Query(30, ge=1, le=365)`)
- `product_id`: `int | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_movement_timeseries( window_days: int = Query(30, ge=1, le=365),
```

---

### `GET` /movements/recent

**Fonction**: `get_recent_movements`

**Paramètres**:
- `limit`: `int` (défaut: `Query(50, ge=1, le=500)`)
- `product_id`: `int | None` (défaut: `Query(default=None)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_recent_movements( limit: int = Query(50, ge=1, le=500),
```

---

### `POST` /adjustments

**Fonction**: `create_stock_adjustment`

**Paramètres**:
- `payload`: `StockAdjustmentRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def create_stock_adjustment( payload: StockAdjustmentRequest,
```

---


## Module: `supplier_scoring`

**Fichier**: `backend/api/supplier_scoring.py`

### `GET` /overview

**Fonction**: `get_suppliers_overview`

Vue d'ensemble des scores fournisseurs.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_suppliers_overview( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `GET` N/A

**Fonction**: `to_supplier_score`

**Paramètres**:
- `item`: `Dict[str, Any]`
- `rank`: `int`

**Retour**: `SupplierScore`

```python
def to_supplier_score(item: Dict[str, Any], rank: int) -> SupplierScore:
```

---

### `GET` /suppliers

**Fonction**: `get_suppliers_list`

Liste paginée des fournisseurs avec scores.

**Paramètres**:
- `page`: `int` (défaut: `Query(1, ge=1, description='Numéro de page')`)
- `per_page`: `int` (défaut: `Query(20, ge=1, le=100, description='Résultats par page')`)
- `sort_by`: `str` (défaut: `Query('score', description='Tri: score, name, grade')`)
- `order`: `str` (défaut: `Query('desc', description='Ordre: asc, desc')`)
- `min_score`: `Optional[float]` (défaut: `Query(None, ge=0, le=100, description='Score minimum')`)
- `grade_filter`: `Optional[str]` (défaut: `Query(None, description='Filtrer par grade (A, B, C, D, F)')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_suppliers_list( page: int = Query(1, ge=1, description="Numéro de page"),
```

---

### `GET` /suppliers/{supplier_id}

**Fonction**: `get_supplier_details`

Détails complets d'un fournisseur.

**Paramètres**:
- `supplier_id`: `int` (défaut: `Path(..., description='ID du fournisseur')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_supplier_details( supplier_id: int = Path(..., description="ID du fournisseur"),
```

---

### `GET` /suppliers/{supplier_id}/history

**Fonction**: `get_supplier_history`

Historique des scores d'un fournisseur.

**Paramètres**:
- `supplier_id`: `int` (défaut: `Path(..., description='ID du fournisseur')`)
- `limit`: `int` (défaut: `Query(20, ge=1, le=100, description="Nombre d'entrées")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_supplier_history( supplier_id: int = Path(..., description="ID du fournisseur"),
```

---

### `GET` /criteria

**Fonction**: `get_scoring_criteria`

Critères de scoring configurables.

**Retour**: `Dict[str, Any]`

```python
async def get_scoring_criteria() -> Dict[str, Any]:
```

---

### `PUT` /criteria

**Fonction**: `update_scoring_criteria`

Mettre à jour les pondérations des critères de scoring.

**Paramètres**:
- `request`: `UpdateScoringCriteriaRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def update_scoring_criteria( request: UpdateScoringCriteriaRequest,
```

---

### `GET` /alerts

**Fonction**: `get_supplier_alerts`

Alertes sur les scores fournisseurs dégradés.

**Paramètres**:
- `severity`: `Optional[str]` (défaut: `Query(None, description='Filtrer par sévérité: info, warning, critical')`)
- `acknowledged`: `Optional[bool]` (défaut: `Query(None, description="Filtrer par état d'acquittement")`)
- `limit`: `int` (défaut: `Query(50, ge=1, le=200, description="Nombre maximum d'alertes")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_supplier_alerts( severity: Optional[str] = Query(None, description="Filtrer par sévérité: info, warning, critical"),
```

---

### `POST` /alerts/{alert_id}/acknowledge

**Fonction**: `acknowledge_supplier_alert`

Acquitter une alerte fournisseur.

**Paramètres**:
- `alert_id`: `str` (défaut: `Path(..., description="ID de l'alerte à acquitter")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def acknowledge_supplier_alert( alert_id: str = Path(..., description="ID de l'alerte à acquitter"),
```

---

### `POST` /recalculate

**Fonction**: `recalculate_supplier_scores`

Recalculer tous les scores fournisseurs.

**Paramètres**:
- `request`: `RecalculateScoresRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def recalculate_supplier_scores( request: RecalculateScoresRequest,
```

---

### `GET` /score/{supplier_name}

**Fonction**: `get_supplier_score_legacy`

[LEGACY] Calcule et retourne le score complet d'un fournisseur.

**Paramètres**:
- `supplier_name`: `str`
- `period_days`: `int` (défaut: `Query(90, ge=7, le=365, description="Période d'analyse en jours")`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_supplier_score_legacy( supplier_name: str,
```

---

### `GET` /ranking

**Fonction**: `get_suppliers_ranking_legacy`

[LEGACY] Retourne le classement de tous les fournisseurs.

**Paramètres**:
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_suppliers_ranking_legacy( tenant: Tenant = Depends(get_current_tenant_or_default),
```

---

### `POST` /compare

**Fonction**: `compare_suppliers`

Compare plusieurs fournisseurs sur toutes les dimensions.

**Paramètres**:
- `request`: `SupplierComparisonRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def compare_suppliers( request: SupplierComparisonRequest,
```

---

### `POST` /delivery

**Fonction**: `record_delivery`

Enregistre une livraison pour le suivi de ponctualité.

**Paramètres**:
- `request`: `DeliveryRecordRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def record_delivery( request: DeliveryRecordRequest,
```

---

### `POST` /issue

**Fonction**: `record_invoice_issue`

Enregistre un problème de facture.

**Paramètres**:
- `request`: `InvoiceIssueRequest`
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def record_invoice_issue( request: InvoiceIssueRequest,
```

---

### `GET` /dimensions

**Fonction**: `list_dimensions`

[LEGACY] Liste les dimensions de scoring avec leurs poids.

**Retour**: `Dict[str, Any]`

```python
async def list_dimensions() -> Dict[str, Any]:
```

---

### `GET` /history/{supplier_name}

**Fonction**: `get_supplier_history_by_name`

[LEGACY] Retourne l'historique des scores d'un fournisseur par nom.

**Paramètres**:
- `supplier_name`: `str`
- `limit`: `int` (défaut: `Query(20, ge=1, le=100)`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant_or_default)`)

**Retour**: `Dict[str, Any]`

```python
async def get_supplier_history_by_name( supplier_name: str,
```

---


## Module: `supply`

**Fichier**: `backend/api/supply.py`

### `GET` /plan

**Fonction**: `get_supply_plan`

Expose the dynamic supply planning data structure.

**Paramètres**:
- `target_coverage`: `int` (défaut: `Query(21, ge=1, le=120, description='Nombre de jours de stock visés.')`)
- `alert_threshold`: `int` (défaut: `Query(7, ge=1, le=120, description='Seuil d’alerte en jours.')`)
- `min_daily_sales`: `float` (défaut: `Query(0.0, ge=0, le=100, description='Filtre sur les ventes quotidiennes minimales.')`)
- `categories`: `Optional[List[str]]` (défaut: `Query(default=None, description='Liste optionnelle de catégories à inclure (répéter le paramètre).')`)
- `search`: `Optional[str]` (défaut: `Query(default=None, max_length=120, description='Terme de recherche appliqué côté serveur.')`)
- `tenant`: `Tenant` (défaut: `Depends(get_current_tenant)`)

```python
def get_supply_plan( target_coverage: int = Query(21, ge=1, le=120, description="Nombre de jours de stock visés."),
```

---


## Module: `backend.main`

**Fichier**: `backend/main.py`

### `GET` /metrics/performance

**Fonction**: `performance_metrics`

Retourne les statistiques de performance des endpoints.

```python
def performance_metrics():
```

---


## Module: `backend.tests.conftest`

**Fichier**: `backend/tests/conftest.py`

### `GET` N/A

**Fonction**: `client`

Crée une instance TestClient pour l'app FastAPI.

**Retour**: `TestClient`

```python
def client() -> TestClient:
```

---

