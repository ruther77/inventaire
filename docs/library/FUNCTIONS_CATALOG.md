# Catalogue des Fonctions Python

Documentation générée automatiquement des fonctions dans `/backend` et `/core`

---

## Statistiques Globales

- **Fonctions totales**: 1149
- **Fichiers analysés**: 179
- **Catégories**: 22
- **Fonctions asynchrones**: 83
- **Méthodes de classe**: 407
- **Décorateurs**: 207
- **Haute réutilisabilité**: 504

## Distribution par Catégorie

| Catégorie | Nombre de Fonctions |
|-----------|---------------------|
| API | 293 |
| Finance | 265 |
| General | 114 |
| Business Logic | 96 |
| Restaurant | 77 |
| Database | 60 |
| Middleware | 50 |
| Invoicing | 32 |
| Data Retrieval | 31 |
| Document Processing | 24 |
| Cache | 22 |
| Background Tasks | 18 |
| Data Creation | 16 |
| Formatting | 15 |
| Validation | 8 |
| Authentication | 7 |
| Data Schema | 6 |
| Calculation | 5 |
| Utilities | 5 |
| Data Normalization | 3 |
| Data Update | 1 |
| Data Deletion | 1 |

## Index des Catégories

- [API](#api)
- [Finance](#finance)
- [General](#general)
- [Business Logic](#business-logic)
- [Restaurant](#restaurant)
- [Database](#database)
- [Middleware](#middleware)
- [Invoicing](#invoicing)
- [Data Retrieval](#data-retrieval)
- [Document Processing](#document-processing)
- [Cache](#cache)
- [Background Tasks](#background-tasks)
- [Data Creation](#data-creation)
- [Formatting](#formatting)
- [Validation](#validation)
- [Authentication](#authentication)
- [Data Schema](#data-schema)
- [Calculation](#calculation)
- [Utilities](#utilities)
- [Data Normalization](#data-normalization)
- [Data Update](#data-update)
- [Data Deletion](#data-deletion)

---

## API

**293 fonctions**

### `backend/api/admin.py`

#### 🔸 `admin_overview`

```python
def admin_overview(tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 29
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/overview', response_model=AdminOverviewResponse)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.admin.AdminOverviewResponse`
  - `fastapi.Depends`

#### 🔸 `list_users`

```python
def list_users():
```

- **Ligne**: 35
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/users', response_model=AdminUsersResponse)`
- **Dépendances**:
  - `backend.schemas.admin.AdminUsersResponse`

#### 🔸 `change_user_role`

```python
def change_user_role(user_id: int, payload: UpdateRolePayload):
```

- **Ligne**: 41
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/users/{user_id}/role')`
- **Paramètres**:
  - `user_id`: `int`
  - `payload`: `UpdateRolePayload`
- **Dépendances**:
  - `backend.schemas.admin.UpdateRolePayload`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `reset_user_password`

```python
def reset_user_password(user_id: int, payload: ResetPasswordPayload | None = None):
```

- **Ligne**: 50
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/users/{user_id}/reset-password')`
- **Paramètres**:
  - `user_id`: `int`
  - `payload`: `ResetPasswordPayload | None` = `None`
- **Dépendances**:
  - `backend.schemas.admin.ResetPasswordPayload`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `create_backup`

```python
def create_backup(payload: BackupCreationPayload | None = None):
```

- **Ligne**: 59
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/backups', response_model=BackupMetadataModel)`
- **Paramètres**:
  - `payload`: `BackupCreationPayload | None` = `None`
- **Dépendances**:
  - `backend.schemas.admin.BackupCreationPayload`
  - `backend.schemas.admin.BackupMetadataModel`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `restore_backup`

```python
def restore_backup(filename: str):
```

- **Ligne**: 68
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/backups/{filename}/restore')`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `delete_backup`

```python
def delete_backup(filename: str):
```

- **Ligne**: 77
- **Réutilisabilité**: High
- **Décorateurs**: `router.delete('/backups/{filename}')`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `get_integrity_report`

```python
def get_integrity_report():
```

- **Ligne**: 86
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/backups/integrity', response_model=list[IntegrityReportEntry])`
- **Dépendances**:
  - `backend.schemas.admin.BackupMetadataModel`
  - `backend.schemas.admin.IntegrityReportEntry`

#### 🔸 `get_backup_settings`

```python
def get_backup_settings():
```

- **Ligne**: 92
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/settings', response_model=BackupSettingsModel)`
- **Dépendances**:
  - `backend.schemas.admin.BackupSettingsModel`

#### 🔸 `update_backup_settings`

```python
def update_backup_settings(payload: BackupSettingsModel):
```

- **Ligne**: 98
- **Réutilisabilité**: High
- **Décorateurs**: `router.put('/settings', response_model=BackupSettingsModel)`
- **Paramètres**:
  - `payload`: `BackupSettingsModel`
- **Dépendances**:
  - `backend.schemas.admin.BackupSettingsModel`

### `backend/api/analytics.py`

#### 🔸 `get_summary`

```python
def get_summary(tenant: Tenant = Depends(get_current_tenant)) -> AnalyticsSummary:
```

**Description**: Retourne quelques KPI agrégés (stock et mouvements récents) pour le tenant courant.

- **Ligne**: 164
- **Réutilisabilité**: High
- **Type de retour**: `AnalyticsSummary`
- **Décorateurs**: `router.get('/summary', response_model=AnalyticsSummary)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`

### `backend/api/anomaly_detection.py`

#### 🔸 `scan_for_anomalies` 🎀

```python
def scan_for_anomalies( entity_types: str = Query(default="transactions,invoices"),
```

**Description**: Scanne les données pour détecter des anomalies.

- **Ligne**: 182
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/scan', response_model=List[AnomalyResponse])`
- **Paramètres**:
  - `entity_types`: `str` = `Query(default='transactions,invoices')`
  - `severity_threshold`: `str` = `Query(default='LOW')`
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - `core.finance.anomaly_detection.AnomalyType`
  - *... et 12 autres*

#### 🔸 `detect_transaction_outliers` 🎀

```python
def detect_transaction_outliers( days_back: int = Query(default=30, ge=1, le=365),
```

**Description**: Détecte les transactions avec des montants anormalement élevés ou bas

- **Ligne**: 266
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/transactions/outliers', response_model=List[AnomalyResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `z_score_threshold`: `float` = `Query(default=2.5, ge=1.5, le=5.0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - `core.finance.anomaly_detection.AnomalyType`
  - *... et 9 autres*

#### 🔸 `detect_duplicate_invoices` 🎀

```python
def detect_duplicate_invoices( days_back: int = Query(default=90, ge=1, le=365),
```

**Description**: Détecte les factures potentiellement en double.

- **Ligne**: 309
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/invoices/duplicates', response_model=List[DuplicateInvoiceResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=90, ge=1, le=365)`
  - `similarity_threshold`: `float` = `Query(default=0.9, ge=0.7, le=1.0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - `core.finance.anomaly_detection.AnomalyType`
  - *... et 13 autres*

#### 🔸 `detect_invoice_sequence_gaps` 🎀

```python
def detect_invoice_sequence_gaps( days_back: int = Query(default=90, ge=1, le=365),
```

**Description**: Détecte les trous dans les séquences de numéros de factures.

- **Ligne**: 374
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/invoices/sequence-gaps', response_model=List[SequenceGapResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=90, ge=1, le=365)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - `core.finance.anomaly_detection.AnomalyType`
  - *... et 13 autres*

#### 🔸 `detect_round_amounts` 🎀

```python
def detect_round_amounts( days_back: int = Query(default=30, ge=1, le=365),
```

**Description**: Détecte les transactions avec des montants ronds suspects.

- **Ligne**: 436
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/transactions/round-amounts', response_model=List[RoundAmountResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `min_amount`: `float` = `Query(default=100.0, ge=0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - `core.finance.anomaly_detection.AnomalyType`
  - *... et 5 autres*

#### 🔸 `get_anomaly_summary`

```python
def get_anomaly_summary( days_back: int = Query(default=30, ge=1, le=365),
```

**Description**: Résumé des anomalies détectées avec filtrage optionnel.

- **Ligne**: 500
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/summary', response_model=AnomalySummaryResponse)`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `severity`: `Optional[str]` = `Query(default=None, description='Filtrer par sévérité (critical, high, medium, low)')`
  - `type`: `Optional[str]` = `Query(default=None, description="Filtrer par type d'anomalie")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - `core.finance.anomaly_detection.AnomalyType`
  - *... et 11 autres*

#### 🔸 `resolve_anomaly`

```python
def resolve_anomaly( anomaly_id: str,
```

**Description**: Marque une anomalie comme résolue avec une note explicative.

- **Ligne**: 586
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/resolve/{anomaly_id}')`
- **Paramètres**:
  - `anomaly_id`: `str`
  - `resolution_note`: `str` = `Query(..., min_length=5)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `fastapi.Depends`
  - *... et 1 autres*

### `backend/api/audit.py`

#### 🔸 `get_diagnostics`

```python
def get_diagnostics( categories: Optional[List[str]] = Query(
```

- **Ligne**: 24
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/diagnostics', response_model=AuditDiagnosticsResponse)`
- **Paramètres**:
  - `categories`: `Optional[List[str]]` = `Query(default=None, description='Répéter le paramètre pour filtrer par catégorie.')`
  - `levels`: `Optional[List[str]]` = `Query(default=None, description="Filtrer par niveau d'écart.")`
  - `min_abs`: `Optional[float]` = `Query(default=None, ge=0.0)`
  - `max_abs`: `Optional[float]` = `Query(default=None, ge=0.0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.audit.AuditDiagnosticsResponse`
  - `fastapi.Depends`
  - `fastapi.Query`
  - *... et 2 autres*

#### 🔸 `get_actions`

```python
def get_actions( include_closed: bool = Query(default=False),
```

- **Ligne**: 44
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/actions', response_model=AuditActionsResponse)`
- **Paramètres**:
  - `include_closed`: `bool` = `Query(default=False)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.audit.AuditActionsResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_resolution_log`

```python
def get_resolution_log( limit: int = Query(default=100, ge=1, le=500),
```

- **Ligne**: 53
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/resolutions', response_model=AuditResolutionLogResponse)`
- **Paramètres**:
  - `limit`: `int` = `Query(default=100, ge=1, le=500)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.audit.AuditResolutionLogResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_assignment`

```python
def create_assignment(payload: AuditAssignmentRequest, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 62
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/assignments', response_model=AuditActionOut, status_code=201)`
- **Paramètres**:
  - `payload`: `AuditAssignmentRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.audit.AuditActionOut`
  - `backend.schemas.audit.AuditAssignmentRequest`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `update_action_status` 🎀

```python
def update_action_status( action_id: int,
```

- **Ligne**: 77
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/actions/{action_id}/status', response_model=AuditActionOut)`
- **Paramètres**:
  - `action_id`: `int`
  - `payload`: `AuditResolutionRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.audit.AuditActionOut`
  - `backend.schemas.audit.AuditResolutionRequest`
  - `fastapi.Depends`
  - *... et 1 autres*

### `backend/api/audit_trail.py`

#### 🔸 `list_audit_entries`

```python
def list_audit_entries( start_date: Optional[datetime] = Query(default=None),
```

**Description**: Liste les entrées d'audit avec filtres optionnels.

- **Ligne**: 145
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/entries', response_model=List[AuditEntryResponse])`
- **Paramètres**:
  - `start_date`: `Optional[datetime]` = `Query(default=None)`
  - `end_date`: `Optional[datetime]` = `Query(default=None)`
  - `action`: `Optional[str]` = `Query(default=None)`
  - `entity`: `Optional[str]` = `Query(default=None)`
  - `entity_id`: `Optional[int]` = `Query(default=None)`
  - `user_id`: `Optional[int]` = `Query(default=None)`
  - `severity`: `Optional[str]` = `Query(default=None)`
  - `search`: `Optional[str]` = `Query(default=None)`
  - `limit`: `int` = `Query(default=100, le=1000)`
  - `offset`: `int` = `Query(default=0, ge=0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 12 autres*

#### 🔸 `search_audit_entries`

```python
def search_audit_entries( request: AuditSearchRequest,
```

**Description**: Recherche avancée dans l'audit log avec critères multiples.

- **Ligne**: 213
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/search', response_model=List[AuditEntryResponse])`
- **Paramètres**:
  - `request`: `AuditSearchRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 8 autres*

#### 🔸 `get_entity_history`

```python
def get_entity_history( entity: str,
```

**Description**: Retourne l'historique complet des modifications d'une entité.

- **Ligne**: 280
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/entity/{entity}/{entity_id}', response_model=EntityHistoryResponse)`
- **Paramètres**:
  - `entity`: `str`
  - `entity_id`: `int`
  - `limit`: `int` = `Query(default=50, le=500)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 8 autres*

#### 🔸 `get_user_activity`

```python
def get_user_activity( user_id: int,
```

**Description**: Retourne l'activité d'un utilisateur spécifique.

- **Ligne**: 330
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/user/{user_id}', response_model=List[AuditEntryResponse])`
- **Paramètres**:
  - `user_id`: `int`
  - `start_date`: `Optional[datetime]` = `Query(default=None)`
  - `limit`: `int` = `Query(default=100, le=500)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 12 autres*

#### 🔸 `generate_audit_report`

```python
def generate_audit_report( start_date: datetime = Query(default=None, description="Start date for report (defaults to 30 days ago)"),
```

**Description**: Génère un rapport d'audit agrégé pour une période donnée.

- **Ligne**: 367
- **Réutilisabilité**: Low
- **Décorateurs**: `router.get('/report', response_model=AuditReportResponse)`
- **Paramètres**:
  - `start_date`: `datetime` = `Query(default=None, description='Start date for report (defaults to 30 days ago)')`
  - `end_date`: `datetime` = `Query(default=None, description='End date for report (defaults to now)')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 10 autres*

#### 🔸 `get_security_events`

```python
def get_security_events( days: int = Query(default=7, ge=1, le=90),
```

**Description**: Retourne les événements de sécurité récents.

- **Ligne**: 479
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/security-events', response_model=List[AuditEntryResponse])`
- **Paramètres**:
  - `days`: `int` = `Query(default=7, ge=1, le=90)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 9 autres*

#### 🔸 `get_recent_changes`

```python
def get_recent_changes( entity: Optional[str] = Query(default=None),
```

**Description**: Retourne les modifications récentes (dernières N heures).

- **Ligne**: 505
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/recent-changes', response_model=List[AuditEntryResponse])`
- **Paramètres**:
  - `entity`: `Optional[str]` = `Query(default=None)`
  - `hours`: `int` = `Query(default=24, ge=1, le=168)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 10 autres*

#### 🔸 `export_user_data_rgpd`

```python
def export_user_data_rgpd( user_id: int,
```

**Description**: Export RGPD: Retourne toutes les données d'audit d'un utilisateur.

- **Ligne**: 541
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/rgpd/export/{user_id}')`
- **Paramètres**:
  - `user_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - *... et 2 autres*

#### 🔸 `anonymize_user_data_rgpd`

```python
def anonymize_user_data_rgpd( user_id: int,
```

**Description**: RGPD: Anonymise les données d'un utilisateur dans l'audit log.

- **Ligne**: 575
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.delete('/rgpd/anonymize/{user_id}')`
- **Paramètres**:
  - `user_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 1 autres*

#### 🔸 `get_audit_summary`

```python
def get_audit_summary( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Résumé de l'activité d'audit:

- **Ligne**: 609
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/summary')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.audit_trail.AUDIT_LOG_SCHEMA`
  - *... et 7 autres*

### `backend/api/auth.py`

#### 🔹 `__init__`

```python
def __init__( self, grant_type: str | None = Form(default=None, pattern="password"),
```

- **Ligne**: 39
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `grant_type`: `str | None` = `Form(default=None, pattern='password')`
  - `username`: `str` = `Form(...)`
  - `password`: `str` = `Form(...)`
  - `scope`: `str` = `Form(default='')`
  - `client_id`: `str | None` = `Form(default=None)`
  - `client_secret`: `str | None` = `Form(default=None)`
  - `tenant`: `str` = `Form(default=DEFAULT_TENANT.code)`
- **Dépendances**:
  - `backend.dependencies.tenant.DEFAULT_TENANT`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.resolve_tenant`
  - `fastapi.Form`

#### 🔸 `issue_token`

```python
def issue_token(form_data: OAuth2TenantRequestForm = Depends()) -> TokenResponse:
```

**Description**: Émet un token bearer OAuth2 (pour les clients API).

- **Ligne**: 69
- **Réutilisabilité**: Medium
- **Type de retour**: `TokenResponse`
- **Décorateurs**: `router.post('/token', response_model=TokenResponse)`
- **Paramètres**:
  - `form_data`: `OAuth2TenantRequestForm` = `Depends()`
- **Dépendances**:
  - `backend.dependencies.security.ACCESS_TOKEN_EXPIRE_MINUTES`
  - `backend.dependencies.security.create_access_token`
  - `backend.dependencies.security.create_refresh_token`
  - `backend.dependencies.security.decode_refresh_token`
  - `backend.dependencies.security.revoke_token`
  - *... et 11 autres*

#### 🔸 `login_with_cookies`

```python
def login_with_cookies( response: Response,
```

**Description**: Connexion et pose des cookies httpOnly (recommandé pour les clients navigateur).

- **Ligne**: 103
- **Réutilisabilité**: Medium
- **Type de retour**: `CookieTokenResponse`
- **Décorateurs**: `router.post('/login', response_model=CookieTokenResponse)`
- **Paramètres**:
  - `response`: `Response`
  - `form_data`: `OAuth2TenantRequestForm` = `Depends()`
- **Dépendances**:
  - `backend.dependencies.security.ACCESS_TOKEN_EXPIRE_MINUTES`
  - `backend.dependencies.security.create_access_token`
  - `backend.dependencies.security.create_refresh_token`
  - `backend.dependencies.security.decode_refresh_token`
  - `backend.dependencies.security.set_auth_cookies`
  - *... et 13 autres*

#### 🔸 `refresh_access_token`

```python
def refresh_access_token(request: Request, response: Response) -> RefreshResponse:
```

**Description**: Rafraîchit le token d'accès en utilisant le cookie de refresh.

- **Ligne**: 154
- **Réutilisabilité**: Medium
- **Type de retour**: `RefreshResponse`
- **Décorateurs**: `router.post('/refresh', response_model=RefreshResponse)`
- **Paramètres**:
  - `request`: `Request`
  - `response`: `Response`
- **Dépendances**:
  - `backend.dependencies.security.ACCESS_TOKEN_EXPIRE_MINUTES`
  - `backend.dependencies.security.COOKIE_NAME_REFRESH`
  - `backend.dependencies.security.create_access_token`
  - `backend.dependencies.security.create_refresh_token`
  - `backend.dependencies.security.decode_refresh_token`
  - *... et 14 autres*

#### 🔸 `logout`

```python
def logout(request: Request, response: Response) -> dict[str, str]:
```

**Description**: Déconnecte et supprime les cookies d'authentification.

- **Ligne**: 212
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, str]`
- **Décorateurs**: `router.post('/logout')`
- **Paramètres**:
  - `request`: `Request`
  - `response`: `Response`
- **Dépendances**:
  - `backend.dependencies.security.COOKIE_NAME_REFRESH`
  - `backend.dependencies.security.clear_auth_cookies`
  - `backend.dependencies.security.create_refresh_token`
  - `backend.dependencies.security.decode_refresh_token`
  - `backend.dependencies.security.revoke_token`
  - *... et 5 autres*

### `backend/api/bank_reconciliation.py`

#### 🔸 `run_reconciliation` 🎀

```python
def run_reconciliation( days_back: int = Query(default=60, ge=1, le=180),
```

**Description**: Lance le rapprochement bancaire automatique.

- **Ligne**: 191
- **Réutilisabilité**: Low
- **Décorateurs**: `router.post('/run', response_model=List[ReconciliationMatchResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=60, ge=1, le=180)`
  - `auto_confirm_threshold`: `float` = `Query(default=0.95, ge=0.5, le=1.0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - *... et 16 autres*

#### 🔸 `get_unmatched_transactions` 🎀

```python
def get_unmatched_transactions( days_back: int = Query(default=365, ge=1, le=730),
```

**Description**: Retourne les transactions non rapprochées AVEC FACTURES.

- **Ligne**: 358
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/unmatched/transactions', response_model=List[UnmatchedTransactionResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=365, ge=1, le=730)`
  - `min_amount`: `float` = `Query(default=0, ge=0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - *... et 7 autres*

#### 🔸 `get_unmatched_invoices` 🎀

```python
def get_unmatched_invoices( days_back: int = Query(default=365, ge=1, le=730),
```

**Description**: Retourne les factures non payées/non rapprochées.

- **Ligne**: 437
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/unmatched/invoices', response_model=List[UnmatchedInvoiceResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=365, ge=1, le=730)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - *... et 7 autres*

#### 🔸 `create_manual_match`

```python
def create_manual_match( request: ManualMatchRequest,
```

**Description**: Crée un rapprochement manuel entre une transaction et une ou plusieurs factures.

- **Ligne**: 501
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/match/manual')`
- **Paramètres**:
  - `request`: `ManualMatchRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `datetime.date`
  - *... et 4 autres*

#### 🔸 `get_supplier_aliases`

```python
def get_supplier_aliases( tenant: Tenant = Depends(get_current_tenant_or_default)
```

**Description**: Retourne les alias fournisseurs appris pour le rapprochement automatique.

- **Ligne**: 559
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/aliases', response_model=List[SupplierAliasResponse])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - *... et 6 autres*

#### 🔸 `create_supplier_alias`

```python
def create_supplier_alias( request: CreateAliasRequest,
```

**Description**: Crée un nouvel alias fournisseur pour le rapprochement automatique.

- **Ligne**: 605
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/aliases')`
- **Paramètres**:
  - `request`: `CreateAliasRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - *... et 14 autres*

#### 🔸 `delete_supplier_alias`

```python
def delete_supplier_alias( alias_id: int,
```

**Description**: Supprime un alias fournisseur.

- **Ligne**: 637
- **Réutilisabilité**: High
- **Décorateurs**: `router.delete('/aliases/{alias_id}')`
- **Paramètres**:
  - `alias_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `fastapi.Depends`

#### 🔸 `get_reconciliation_summary`

```python
def get_reconciliation_summary( days_back: int = Query(default=30, ge=1, le=180),
```

**Description**: Résumé du rapprochement bancaire avec FACTURES.

- **Ligne**: 654
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/summary', response_model=ReconciliationSummaryResponse)`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=30, ge=1, le=180)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 3 autres*

### `backend/api/capital.py`

#### 🔸 `get_capital_overview`

```python
def get_capital_overview(tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 13
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/overview', response_model=CapitalOverviewResponse)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.capital.CapitalOverviewResponse`
  - `fastapi.Depends`

### `backend/api/catalog.py`

#### 🔸 `list_products`

```python
def list_products( search: str | None = None,
```

**Description**: Liste les produits avec pagination stricte.

- **Ligne**: 18
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/products', response_model=ProductPage)`
- **Paramètres**:
  - `search`: `str | None` = `None`
  - `category`: `str | None` = `None`
  - `status`: `str | None` = `None`
  - `page`: `int` = `Query(default=1, ge=1, le=10000, description='Numéro de page')`
  - `per_page`: `int` = `Query(default=25, ge=1, le=100, description='Éléments par page (max 100)')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.catalog.ProductPage`
  - `fastapi.Depends`
  - `fastapi.Query`
  - *... et 1 autres*

#### 🔸 `get_product`

```python
def get_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 42
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/products/{product_id}', response_model=ProductOut)`
- **Paramètres**:
  - `product_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.catalog.ProductOut`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `create_product` 🎀

```python
def create_product(payload: ProductCreate, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 50
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/products', response_model=ProductOut, status_code=status.HTTP_201_CREATED)`
- **Paramètres**:
  - `payload`: `ProductCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.catalog.ProductCreate`
  - `backend.schemas.catalog.ProductOut`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `update_product`

```python
def update_product(product_id: int, payload: ProductUpdate, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 60
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.patch('/products/{product_id}', response_model=ProductOut)`
- **Paramètres**:
  - `product_id`: `int`
  - `payload`: `ProductUpdate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.catalog.ProductOut`
  - `backend.schemas.catalog.ProductUpdate`
  - `fastapi.Depends`
  - *... et 2 autres*

#### 🔸 `delete_product`

```python
def delete_product(product_id: int, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 76
- **Réutilisabilité**: High
- **Décorateurs**: `router.delete('/products/{product_id}', status_code=status.HTTP_204_NO_CONTENT)`
- **Paramètres**:
  - `product_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `get_product_by_barcode`

```python
def get_product_by_barcode(barcode: str, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 84
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/products/barcode/{barcode}', response_model=ProductOut)`
- **Paramètres**:
  - `barcode`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.catalog.ProductOut`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `list_categories`

```python
def list_categories(tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Liste toutes les categories de produits.

- **Ligne**: 92
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/categories')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`

#### 🔸 `list_vendors`

```python
def list_vendors(tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Liste tous les fournisseurs.

- **Ligne**: 100
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/vendors')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`

### `backend/api/cockpit.py`

#### 🔸 `get_cockpit_overview`

```python
def get_cockpit_overview( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Retourne la vue consolidee complete du cockpit.

- **Ligne**: 512
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/overview', response_model=CockpitOverview)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - *... et 8 autres*

#### 🔸 `get_live_kpis`

```python
def get_live_kpis( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Retourne les KPIs en temps reel pour refresh rapide.

- **Ligne**: 599
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/kpis/live', response_model=LiveKPIs)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - *... et 8 autres*

#### 🔸 `get_alerts`

```python
def get_alerts( severity: Optional[str] = Query(None, description="Filtrer par severite: critical, warning, info"),
```

**Description**: Retourne les alertes actives.

- **Ligne**: 644
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/alerts', response_model=List[AlertItem])`
- **Paramètres**:
  - `severity`: `Optional[str]` = `Query(None, description='Filtrer par severite: critical, warning, info')`
  - `category`: `Optional[str]` = `Query(None, description='Filtrer par categorie: stock, finance, margin, anomaly')`
  - `limit`: `int` = `Query(20, ge=1, le=100)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - *... et 9 autres*

#### 🔸 `acknowledge_alert`

```python
def acknowledge_alert( alert_id: str,
```

**Description**: Marque une alerte comme acquittee.

- **Ligne**: 670
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/alerts/{alert_id}/acknowledge')`
- **Paramètres**:
  - `alert_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `fastapi.Depends`

#### 🔸 `get_health_status`

```python
def get_health_status( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Retourne le statut de sante global.

- **Ligne**: 686
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/health')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `fastapi.Depends`

### `backend/api/dashboard.py`

#### 🔸 `get_dashboard_metrics`

```python
def get_dashboard_metrics(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

- **Ligne**: 15
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/metrics', response_model=DashboardResponse)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.dashboard.DashboardResponse`
  - `fastapi.Depends`

### `backend/api/data_quality.py`

#### 🔸 `categorization_coverage`

```python
def categorization_coverage( days_back: int = Query(default=90, ge=1, le=365),
```

**Description**: Analyse la couverture de catégorisation des transactions bancaires.

- **Ligne**: 12
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/categorization/coverage')`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=90, ge=1, le=365)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `fastapi.APIRouter`
  - *... et 3 autres*

#### 🔸 `list_flags`

```python
def list_flags( table: str | None = Query(default=None, description="Table ciblée (ex: produits, finance_transactions)"),
```

- **Ligne**: 130
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/flags')`
- **Paramètres**:
  - `table`: `str | None` = `Query(default=None, description='Table ciblée (ex: produits, finance_transactions)')`
  - `limit`: `int` = `Query(default=200, ge=1, le=2000)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `fastapi.Depends`
  - `fastapi.Query`
  - *... et 1 autres*

### `backend/api/eurociel.py`

#### 🔸 `async import_eurociel_invoice`

```python
async def import_eurociel_invoice( file: UploadFile = File(...),
```

**Description**: Import direct d'une facture Eurociel : extraction + import catalogue en une seule étape.

- **Ligne**: 28
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Décorateurs**: `router.post('/import')`
- **Paramètres**:
  - `file`: `UploadFile` = `File(...)`
  - `margin_percent`: `float` = `Form(40.0)`
  - `initialize_stock`: `bool` = `Form(False)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.invoice_extractor.extract_text_from_file`
  - `fastapi.Depends`
  - *... et 6 autres*

#### 🔸 `eurociel_status`

```python
def eurociel_status(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, Any]:
```

**Description**: Retourne le statut des imports Eurociel pour ce tenant.

- **Ligne**: 118
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Décorateurs**: `router.get('/status')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`
  - `typing.Any`

### `backend/api/finance.py`

#### 🔸 `create_account`

```python
def create_account( payload: FinanceAccountCreate,
```

- **Ligne**: 65
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/accounts')`
- **Paramètres**:
  - `payload`: `FinanceAccountCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceAccountCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `list_accounts`

```python
def list_accounts( entity_id: int | None = Query(default=None),
```

- **Ligne**: 76
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/accounts')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `is_active`: `bool | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `accounts_overview`

```python
def accounts_overview( entity_id: int | None = Query(default=None),
```

- **Ligne**: 85
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/accounts/overview')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_account` 🎀

```python
def get_account( account_id: int,
```

- **Ligne**: 94
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/accounts/{account_id}')`
- **Paramètres**:
  - `account_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.services.finance.accounts`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `update_account`

```python
def update_account( account_id: int,
```

- **Ligne**: 105
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.put('/accounts/{account_id}')`
- **Paramètres**:
  - `account_id`: `int`
  - `payload`: `dict`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `delete_account`

```python
def delete_account( account_id: int,
```

- **Ligne**: 117
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.delete('/accounts/{account_id}')`
- **Paramètres**:
  - `account_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `create_transaction`

```python
def create_transaction( payload: FinanceTransactionCreate,
```

- **Ligne**: 132
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions')`
- **Paramètres**:
  - `payload`: `FinanceTransactionCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceTransactionCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `list_transactions`

```python
def list_transactions( entity_id: int | None = Query(default=None),
```

- **Ligne**: 143
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/transactions')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `account_id`: `int | None` = `Query(default=None)`
  - `status_filter`: `str | None` = `Query(default=None, alias='status')`
  - `date_from`: `str | None` = `Query(default=None)`
  - `date_to`: `str | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `async search_transactions`

```python
async def search_transactions( entity_id: int | None = Query(default=None),
```

- **Ligne**: 161
- **Réutilisabilité**: Medium
- **Type de retour**: `FinanceTransactionSearchResponse`
- **Décorateurs**: `router.get('/transactions/search', response_model=FinanceTransactionSearchResponse)`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `account_id`: `int | None` = `Query(default=None)`
  - `category_id`: `int | None` = `Query(default=None)`
  - `date_from`: `str | None` = `Query(default=None)`
  - `date_to`: `str | None` = `Query(default=None)`
  - `amount_min`: `float | None` = `Query(default=None)`
  - `amount_max`: `float | None` = `Query(default=None)`
  - `q`: `str | None` = `Query(default=None, description='Recherche texte sur libellé/note')`
  - `page`: `int` = `Query(default=1, ge=1)`
  - `size`: `int` = `Query(default=50, ge=1, le=500)`
  - `sort`: `str` = `Query(default='-date_operation', description='date_operation|amount|category|account avec - pour desc')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.AnomalyRefreshRequest`
  - `backend.schemas.finance.FinanceBatchCategorizeRequest`
  - `backend.schemas.finance.FinanceMatchStatusRequest`
  - *... et 5 autres*

#### 🔸 `update_transaction`

```python
def update_transaction( transaction_id: int,
```

- **Ligne**: 191
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.patch('/transactions/{transaction_id}')`
- **Paramètres**:
  - `transaction_id`: `int`
  - `payload`: `FinanceTransactionUpdate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceTransactionUpdate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `lock_transaction`

```python
def lock_transaction( transaction_id: int,
```

- **Ligne**: 203
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/{transaction_id}/lock')`
- **Paramètres**:
  - `transaction_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `create_vendor`

```python
def create_vendor( payload: FinanceVendorCreate,
```

- **Ligne**: 217
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/vendors')`
- **Paramètres**:
  - `payload`: `FinanceVendorCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceVendorCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `list_vendors`

```python
def list_vendors( entity_id: int | None = Query(default=None),
```

- **Ligne**: 228
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/vendors')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `is_active`: `bool | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_invoice`

```python
def create_invoice( payload: FinanceInvoiceCreate,
```

- **Ligne**: 237
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/invoices')`
- **Paramètres**:
  - `payload`: `FinanceInvoiceCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceInvoiceCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `search_invoices`

```python
def search_invoices( entity_id: int | None = Query(default=None),
```

- **Ligne**: 248
- **Réutilisabilité**: High
- **Type de retour**: `FinanceInvoiceSearchResponse`
- **Décorateurs**: `router.get('/invoices/search', response_model=FinanceInvoiceSearchResponse)`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `vendor_id`: `int | None` = `Query(default=None)`
  - `status_filter`: `str | None` = `Query(default=None, alias='status')`
  - `date_from`: `str | None` = `Query(default=None)`
  - `date_to`: `str | None` = `Query(default=None)`
  - `page`: `int` = `Query(default=1, ge=1)`
  - `size`: `int` = `Query(default=50, ge=1, le=500)`
  - `sort`: `str` = `Query(default='-date_invoice', description='date_invoice|date_due|montant_ttc|vendor|status avec - pour desc')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceInvoiceSearchResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_payment`

```python
def create_payment( payload: FinancePaymentCreate,
```

- **Ligne**: 273
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/payments')`
- **Paramètres**:
  - `payload`: `FinancePaymentCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinancePaymentCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `suggest_autre_top`

```python
def suggest_autre_top( entity_id: int | None = Query(default=None),
```

- **Ligne**: 287
- **Réutilisabilité**: High
- **Type de retour**: `list[FinanceAutreSuggestion]`
- **Décorateurs**: `router.get('/categories/suggestions/autre-top', response_model=list[FinanceAutreSuggestion])`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `limit`: `int` = `Query(default=50, ge=1, le=200)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceAutreSuggestion`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `list_categories`

```python
def list_categories( entity_id: int | None = Query(default=None),
```

- **Ligne**: 296
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/categories')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `is_active`: `bool | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_category`

```python
def create_category( payload: FinanceCategoryCreate,
```

- **Ligne**: 305
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/categories')`
- **Paramètres**:
  - `payload`: `FinanceCategoryCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceCategoryCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `list_cost_centers`

```python
def list_cost_centers( entity_id: int | None = Query(default=None),
```

- **Ligne**: 324
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/cost-centers')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `is_active`: `bool | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_cost_center`

```python
def create_cost_center( payload: FinanceCostCenterCreate,
```

- **Ligne**: 333
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/cost-centers')`
- **Paramètres**:
  - `payload`: `FinanceCostCenterCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceCostCenterCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `autocomplete_categories`

```python
def autocomplete_categories( q: str = Query(default="", description="Search query for category suggestions"),
```

- **Ligne**: 348
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/categories/suggestions/complete')`
- **Paramètres**:
  - `q`: `str` = `Query(default='', description='Search query for category suggestions')`
  - `entity_id`: `int | None` = `Query(default=None)`
  - `limit`: `int` = `Query(default=20, ge=1, le=100)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.AnomalyRefreshRequest`
  - `backend.schemas.finance.FinanceBatchCategorizeRequest`
  - `backend.schemas.finance.FinanceMatchStatusRequest`
  - *... et 4 autres*

#### 🔸 `batch_categorize_transactions`

```python
def batch_categorize_transactions( payload: FinanceBatchCategorizeRequest,
```

- **Ligne**: 360
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/batch-categorize')`
- **Paramètres**:
  - `payload`: `FinanceBatchCategorizeRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceBatchCategorizeRequest`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `list_rules`

```python
def list_rules( entity_id: int | None = Query(default=None),
```

- **Ligne**: 374
- **Réutilisabilité**: High
- **Type de retour**: `list[FinanceRule]`
- **Décorateurs**: `router.get('/rules', response_model=list[FinanceRule])`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `is_active`: `bool | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRule`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `create_rule`

```python
def create_rule(payload: FinanceRuleCreate, tenant: Tenant = Depends(get_current_tenant_or_default)) -> FinanceRule:
```

- **Ligne**: 383
- **Réutilisabilité**: High
- **Type de retour**: `FinanceRule`
- **Décorateurs**: `router.post('/rules', response_model=FinanceRule)`
- **Paramètres**:
  - `payload`: `FinanceRuleCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRule`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`

#### 🔸 `update_rule`

```python
def update_rule( rule_id: int,
```

- **Ligne**: 388
- **Réutilisabilité**: High
- **Type de retour**: `FinanceRule`
- **Décorateurs**: `router.patch('/rules/{rule_id}', response_model=FinanceRule)`
- **Paramètres**:
  - `rule_id`: `int`
  - `payload`: `dict`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRule`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`
  - *... et 2 autres*

#### 🔸 `delete_rule`

```python
def delete_rule(rule_id: int, tenant: Tenant = Depends(get_current_tenant_or_default)) -> dict:
```

- **Ligne**: 400
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.delete('/rules/{rule_id}')`
- **Paramètres**:
  - `rule_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRule`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`
  - *... et 2 autres*

#### 🔸 `list_imports`

```python
def list_imports(tenant: Tenant = Depends(get_current_tenant_or_default)) -> list[dict]:
```

- **Ligne**: 408
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/imports')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`

#### 🔸 `deduplicate_finance`

```python
def deduplicate_finance(tenant: Tenant = Depends(get_current_tenant_or_default)) -> dict:
```

**Description**: Supprime les doublons (date+montant) sur transactions et lignes de relevés.

- **Ligne**: 413
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/deduplicate')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`

#### 🔸 `mark_transactions_incomplete`

```python
def mark_transactions_incomplete( transaction_ids: list[int],
```

**Description**: Crée des transaction_lines par défaut et marque les transactions comme 'incomplètes' (data_quality_flags).

- **Ligne**: 421
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/mark-incomplete')`
- **Paramètres**:
  - `transaction_ids`: `list[int]`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`

#### 🔸 `categories_stats`

```python
def categories_stats( entity_id: int | None = Query(default=None),
```

- **Ligne**: 433
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/categories/stats')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `finance_dashboard_summary`

```python
def finance_dashboard_summary( entity_id: int | None = Query(default=None),
```

- **Ligne**: 441
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/dashboard/summary')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `refresh_stats_cache`

```python
def refresh_stats_cache( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Description**: Rafraîchit les vues matérialisées des stats finance.

- **Ligne**: 449
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/stats/refresh')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`

#### 🔸 `get_timeline_stats`

```python
def get_timeline_stats( entity_id: int | None = Query(default=None),
```

**Description**: Retourne la chronologie agrégée des flux pour les graphiques.

- **Ligne**: 457
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/stats/timeline')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `months`: `int | None` = `Query(default=12, description='Nombre de mois (null=tout)')`
  - `granularity`: `str` = `Query(default='monthly', description='daily|weekly|monthly')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_category_breakdown`

```python
def get_category_breakdown( entity_id: int | None = Query(default=None),
```

**Description**: Retourne la répartition par catégorie pour les pie/bar charts.

- **Ligne**: 473
- **Réutilisabilité**: High
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/stats/category-breakdown')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `months`: `int | None` = `Query(default=12, description='Nombre de mois (null=tout)')`
  - `direction`: `str | None` = `Query(default=None, description='IN|OUT|null pour les deux')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_treasury_summary`

```python
def get_treasury_summary( entity_id: int | None = Query(default=None),
```

**Description**: Retourne un résumé de trésorerie (totaux, solde, période).

- **Ligne**: 489
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/stats/treasury')`
- **Paramètres**:
  - `entity_id`: `int | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_reconciliation`

```python
def create_reconciliation( payload: FinanceReconciliationCreate,
```

- **Ligne**: 502
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/reconciliations')`
- **Paramètres**:
  - `payload`: `FinanceReconciliationCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceReconciliationCreate`
  - `fastapi.Depends`
  - *... et 2 autres*

#### 🔸 `delete_reconciliation`

```python
def delete_reconciliation( reconciliation_id: int,
```

- **Ligne**: 518
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.delete('/reconciliations/{reconciliation_id}')`
- **Paramètres**:
  - `reconciliation_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `search_bank_statements`

```python
def search_bank_statements( account_id: int | None = Query(default=None),
```

- **Ligne**: 530
- **Réutilisabilité**: High
- **Type de retour**: `FinanceBankStatementSearchResponse`
- **Décorateurs**: `router.get('/bank-statements/search', response_model=FinanceBankStatementSearchResponse)`
- **Paramètres**:
  - `account_id`: `int | None` = `Query(default=None)`
  - `period_start`: `str | None` = `Query(default=None)`
  - `period_end`: `str | None` = `Query(default=None)`
  - `status_filter`: `str | None` = `Query(default=None, alias='status')`
  - `page`: `int` = `Query(default=1, ge=1)`
  - `size`: `int` = `Query(default=50, ge=1, le=500)`
  - `sort`: `str` = `Query(default='-imported_at', description='imported_at|period_start|period_end|account avec - pour desc')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceBankStatementSearchResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `async import_bank_statements` 🎀

```python
async def import_bank_statements( account_id: int = Query(..., description="ID du compte finance_accounts"),
```

- **Ligne**: 553
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/bank-statements/import')`
- **Paramètres**:
  - `account_id`: `int` = `Query(..., description='ID du compte finance_accounts')`
  - `file`: `UploadFile` = `File(...)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRule`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `backend.services.importers.bank_statement_csv`
  - *... et 6 autres*

#### 🔸 `async import_bank_statements_pdf` 🎀

```python
async def import_bank_statements_pdf( account_id: int = Query(..., description="ID du compte finance_accounts"),
```

**Description**: Import best-effort d'un relevé PDF (parse minimal) dans finance_bank_statements/lines.

- **Ligne**: 583
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/bank-statements/import-pdf')`
- **Paramètres**:
  - `account_id`: `int` = `Query(..., description='ID du compte finance_accounts')`
  - `file`: `UploadFile` = `File(...)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRule`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `backend.services.importers.bank_statement_csv`
  - *... et 6 autres*

#### 🔸 `run_reconciliation`

```python
def run_reconciliation( payload: FinanceRunRequest,
```

- **Ligne**: 620
- **Réutilisabilité**: High
- **Type de retour**: `FinanceRunResponse`
- **Décorateurs**: `router.post('/reconciliation/run', response_model=FinanceRunResponse)`
- **Paramètres**:
  - `payload`: `FinanceRunRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceRunRequest`
  - `backend.schemas.finance.FinanceRunResponse`
  - *... et 1 autres*

#### 🔸 `list_matches`

```python
def list_matches( status: str | None = Query(default="pending", description="Filtrer par statut."),
```

- **Ligne**: 666
- **Réutilisabilité**: High
- **Type de retour**: `list[FinanceMatch]`
- **Décorateurs**: `router.get('/reconciliation/matches', response_model=list[FinanceMatch])`
- **Paramètres**:
  - `status`: `str | None` = `Query(default='pending', description='Filtrer par statut.')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceMatch`
  - `backend.schemas.finance.FinanceMatchStatusRequest`
  - *... et 4 autres*

#### 🔸 `update_match_status`

```python
def update_match_status( match_id: int,
```

- **Ligne**: 679
- **Réutilisabilité**: High
- **Type de retour**: `FinanceMatch`
- **Décorateurs**: `router.post('/reconciliation/{match_id}/status', response_model=FinanceMatch)`
- **Paramètres**:
  - `match_id`: `int`
  - `payload`: `FinanceMatchStatusRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceMatch`
  - `backend.schemas.finance.FinanceMatchStatusRequest`
  - *... et 2 autres*

#### 🔸 `refresh_recurring`

```python
def refresh_recurring( payload: RecurringRefreshRequest,
```

- **Ligne**: 697
- **Réutilisabilité**: High
- **Type de retour**: `RecurringRefreshResponse`
- **Décorateurs**: `router.post('/recurring/refresh', response_model=RecurringRefreshResponse)`
- **Paramètres**:
  - `payload`: `RecurringRefreshRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.RecurringRefreshRequest`
  - `backend.schemas.finance.RecurringRefreshResponse`
  - *... et 1 autres*

#### 🔸 `list_recurring`

```python
def list_recurring( tenant: Tenant = Depends(get_current_tenant_or_default),
```

- **Ligne**: 706
- **Réutilisabilité**: High
- **Type de retour**: `list[FinanceRecurringExpense]`
- **Décorateurs**: `router.get('/recurring', response_model=list[FinanceRecurringExpense])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceRecurringExpense`
  - `fastapi.Depends`

#### 🔸 `refresh_anomalies`

```python
def refresh_anomalies( payload: AnomalyRefreshRequest,
```

- **Ligne**: 714
- **Réutilisabilité**: High
- **Type de retour**: `AnomalyRefreshResponse`
- **Décorateurs**: `router.post('/anomalies/refresh', response_model=AnomalyRefreshResponse)`
- **Paramètres**:
  - `payload`: `AnomalyRefreshRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.AnomalyRefreshRequest`
  - `backend.schemas.finance.AnomalyRefreshResponse`
  - *... et 1 autres*

#### 🔸 `list_anomalies`

```python
def list_anomalies( severity: str | None = Query(default=None, description="Filtrer par sévérité."),
```

- **Ligne**: 727
- **Réutilisabilité**: Medium
- **Type de retour**: `list[FinanceAnomaly]`
- **Décorateurs**: `router.get('/anomalies', response_model=list[FinanceAnomaly])`
- **Paramètres**:
  - `severity`: `str | None` = `Query(default=None, description='Filtrer par sévérité.')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceAnomaly`
  - `fastapi.Depends`
  - *... et 2 autres*

#### 🔸 `get_reconciliation_run_anomalies`

```python
def get_reconciliation_run_anomalies( run_id: int,
```

**Description**: Retourne les anomalies détectées pour un run de rapprochement spécifique.

- **Ligne**: 756
- **Réutilisabilité**: Medium
- **Type de retour**: `list[FinanceAnomaly]`
- **Décorateurs**: `router.get('/reconciliation/runs/{run_id}/anomalies', response_model=list[FinanceAnomaly])`
- **Paramètres**:
  - `run_id`: `int`
  - `severity`: `str | None` = `Query(default=None, description='Filtrer par sévérité.')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance.FinanceAnomaly`
  - `fastapi.Depends`
  - *... et 2 autres*

#### 🔸 `record_category_feedback`

```python
def record_category_feedback( transaction_id: int,
```

**Description**: Enregistre une correction de catégorie faite par l'utilisateur.

- **Ligne**: 806
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/{transaction_id}/feedback')`
- **Paramètres**:
  - `transaction_id`: `int`
  - `payload`: `CategoryFeedbackPayload`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 1 autres*

#### 🔸 `get_categorization_feedback_stats`

```python
def get_categorization_feedback_stats( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Description**: Retourne les statistiques globales sur le feedback de catégorisation.

- **Ligne**: 864
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/categorization/feedback/stats')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

#### 🔸 `get_common_category_corrections`

```python
def get_common_category_corrections( limit: int = Query(default=20, ge=1, le=100),
```

**Description**: Retourne les corrections de catégories les plus fréquentes.

- **Ligne**: 911
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict]`
- **Décorateurs**: `router.get('/categorization/feedback/common-corrections')`
- **Paramètres**:
  - `limit`: `int` = `Query(default=20, ge=1, le=100)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.Query`
  - *... et 1 autres*

### `backend/api/forecasting.py`

#### 🔸 `forecast_sales`

```python
def forecast_sales( request: SalesForecastRequest,
```

**Description**: Prévision des ventes avec plusieurs algorithmes disponibles:

- **Ligne**: 199
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/sales', response_model=SalesForecastResponse)`
- **Paramètres**:
  - `request`: `SalesForecastRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.forecasting.ForecastMethod`
  - `core.finance.forecasting.ForecastType`
  - *... et 13 autres*

#### 🔸 `forecast_stock_depletion` 🎀

```python
def forecast_stock_depletion( days_horizon: int = Query(default=60, ge=1, le=180),
```

**Description**: Prévoit la date d'épuisement du stock pour chaque produit.

- **Ligne**: 250
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/stock-depletion', response_model=List[ProductForecastResponse])`
- **Paramètres**:
  - `days_horizon`: `int` = `Query(default=60, ge=1, le=180)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 5 autres*

#### 🔸 `forecast_cash_flow`

```python
def forecast_cash_flow( horizon_days: int = Query(default=30, ge=7, le=90),
```

**Description**: Prévision de trésorerie basée sur:

- **Ligne**: 314
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/cash-flow', response_model=CashFlowForecastResponse)`
- **Paramètres**:
  - `horizon_days`: `int` = `Query(default=30, ge=7, le=90)`
  - `starting_balance`: `float` = `Query(default=0.0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.forecasting.ForecastMethod`
  - `core.finance.forecasting.ForecastType`
  - *... et 11 autres*

#### 🔸 `forecast_price_trend`

```python
def forecast_price_trend( product_id: int,
```

**Description**: Prévision de l'évolution des prix d'un produit.

- **Ligne**: 378
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/price-trend/{product_id}', response_model=PriceTrendResponse)`
- **Paramètres**:
  - `product_id`: `int`
  - `horizon_days`: `int` = `Query(default=30, ge=7, le=90)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.forecasting.ForecastMethod`
  - `core.finance.forecasting.ForecastType`
  - *... et 14 autres*

#### 🔸 `get_forecasting_summary`

```python
def get_forecasting_summary( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Résumé des prévisions:

- **Ligne**: 469
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/summary')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `fastapi.Depends`

### `backend/api/inventory_intelligence.py`

#### 🔸 `calculate_eoq`

```python
def calculate_eoq( request: EOQRequest,
```

**Description**: Calcule la quantité économique de commande (EOQ) avec la formule de Wilson.

- **Ligne**: 219
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/eoq', response_model=EOQResponse)`
- **Paramètres**:
  - `request`: `EOQRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - `core.finance.inventory_intelligence.StockClassification`
  - *... et 2 autres*

#### 🔸 `calculate_safety_stock`

```python
def calculate_safety_stock( request: SafetyStockRequest,
```

**Description**: Calcule le stock de sécurité pour un niveau de service donné.

- **Ligne**: 257
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/safety-stock', response_model=SafetyStockResponse)`
- **Paramètres**:
  - `request`: `SafetyStockRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - `core.finance.inventory_intelligence.StockClassification`
  - *... et 2 autres*

#### 🔸 `get_reorder_points` 🎀

```python
def get_reorder_points( lead_time_days: float = Query(default=3.0, gt=0),
```

**Description**: Retourne les points de réapprovisionnement pour tous les produits.

- **Ligne**: 295
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/reorder-points', response_model=List[ReorderPointResponse])`
- **Paramètres**:
  - `lead_time_days`: `float` = `Query(default=3.0, gt=0)`
  - `service_level`: `str` = `Query(default='STANDARD')`
  - `only_needs_reorder`: `bool` = `Query(default=False)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - *... et 10 autres*

#### 🔸 `predict_stockouts`

```python
def predict_stockouts( horizon_days: int = Query(default=30, ge=1, le=90),
```

**Description**: Prédit les ruptures de stock dans les N prochains jours.

- **Ligne**: 365
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/stockout-predictions', response_model=List[StockoutPredictionResponse])`
- **Paramètres**:
  - `horizon_days`: `int` = `Query(default=30, ge=1, le=90)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - *... et 10 autres*

#### 🔸 `get_dead_stock`

```python
def get_dead_stock( rotation_threshold: float = Query(default=0.3, ge=0, le=1),
```

**Description**: Détecte les produits en stock mort (rotation < seuil/mois).

- **Ligne**: 409
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/dead-stock', response_model=List[DeadStockResponse])`
- **Paramètres**:
  - `rotation_threshold`: `float` = `Query(default=0.3, ge=0, le=1)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - *... et 10 autres*

#### 🔸 `get_abc_xyz_classification`

```python
def get_abc_xyz_classification( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Classification ABC-XYZ des produits.

- **Ligne**: 452
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/abc-xyz', response_model=List[ABCXYZResponse])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - *... et 10 autres*

#### 🔸 `get_reorder_suggestions`

```python
def get_reorder_suggestions( lead_time_days: float = Query(default=3.0, gt=0),
```

**Description**: Génère des suggestions de réapprovisionnement automatiques.

- **Ligne**: 507
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/reorder-suggestions', response_model=List[ReorderSuggestionResponse])`
- **Paramètres**:
  - `lead_time_days`: `float` = `Query(default=3.0, gt=0)`
  - `service_level`: `str` = `Query(default='STANDARD')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - *... et 10 autres*

#### 🔸 `get_inventory_intelligence_summary`

```python
def get_inventory_intelligence_summary( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: Résumé de l'intelligence d'inventaire:

- **Ligne**: 571
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/summary')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `core.finance.inventory_intelligence.InventoryIntelligence`
  - `core.finance.inventory_intelligence.ServiceLevel`
  - *... et 10 autres*

### `backend/api/invoices.py`

#### 🔸 `extract_invoice`

```python
def extract_invoice(payload: InvoiceExtractRequest, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 332
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/extract', response_model=InvoiceExtractResponse)`
- **Paramètres**:
  - `payload`: `InvoiceExtractRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceExtractRequest`
  - `backend.schemas.invoices.InvoiceExtractResponse`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `async extract_invoice_from_file`

```python
async def extract_invoice_from_file( file: UploadFile = File(...),
```

- **Ligne**: 356
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/extract/file', response_model=InvoiceExtractResponse)`
- **Paramètres**:
  - `file`: `UploadFile` = `File(...)`
  - `margin_percent`: `float` = `Form(40.0)`
  - `supplier_hint`: `str | None` = `Form(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.ImportSession`
  - `backend.schemas.invoices.ImportSessionDetails`
  - *... et 11 autres*

#### 🔸 `import_invoice`

```python
def import_invoice(payload: InvoiceImportRequest, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 394
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/import', response_model=InvoiceImportSummary)`
- **Paramètres**:
  - `payload`: `InvoiceImportRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceImportRequest`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `import_catalog`

```python
def import_catalog(payload: InvoiceCatalogImportRequest, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 417
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/catalog/import', response_model=InvoiceCatalogImportSummary)`
- **Paramètres**:
  - `payload`: `InvoiceCatalogImportRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceCatalogImportRequest`
  - `backend.schemas.invoices.InvoiceCatalogImportSummary`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `link_invoice_line`

```python
def link_invoice_line(payload: InvoiceLineLinkRequest, tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Associe une ligne extraite à un produit existant et renvoie la ligne enrichie.

- **Ligne**: 440
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/lines/link', response_model=InvoiceLineLinkResponse)`
- **Paramètres**:
  - `payload`: `InvoiceLineLinkRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceLine`
  - `backend.schemas.invoices.InvoiceLineCreateProductRequest`
  - `backend.schemas.invoices.InvoiceLineCreateProductResponse`
  - *... et 4 autres*

#### 🔸 `create_product_from_line`

```python
def create_product_from_line(payload: InvoiceLineCreateProductRequest, tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Crée un produit à partir d'une ligne de facture, optionnellement avec stock initial.

- **Ligne**: 452
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/lines/create-product', response_model=InvoiceLineCreateProductResponse)`
- **Paramètres**:
  - `payload`: `InvoiceLineCreateProductRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceCatalogImportSummary`
  - `backend.schemas.invoices.InvoiceLineCreateProductRequest`
  - `backend.schemas.invoices.InvoiceLineCreateProductResponse`
  - *... et 1 autres*

#### 🔸 `confirm_invoice_stock`

```python
def confirm_invoice_stock(payload: InvoiceStockConfirmRequest, tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Valide les mouvements de stock pour des lignes sélectionnées.

- **Ligne**: 466
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/lines/confirm-stock', response_model=InvoiceImportSummary)`
- **Paramètres**:
  - `payload`: `InvoiceStockConfirmRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `backend.schemas.invoices.InvoiceStockConfirmRequest`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `async zero_click_import`

```python
async def zero_click_import( file: UploadFile = File(...),
```

- **Ligne**: 485
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/zero-click', response_model=InvoiceImportSummary)`
- **Paramètres**:
  - `file`: `UploadFile` = `File(...)`
  - `margin_percent`: `float` = `Form(40.0)`
  - `supplier_hint`: `str | None` = `Form(default=None)`
  - `auto_confirm`: `bool` = `Form(default=True)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `core.invoice_extractor.extract_text_from_file`
  - `fastapi.Depends`
  - *... et 5 autres*

#### 🔸 `async zero_click_job`

```python
async def zero_click_job( file: UploadFile = File(...),
```

**Description**: Lance un job zero-click async et retourne immédiatement le job_id pour polling.

- **Ligne**: 510
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/zero-click/jobs', response_model=ZeroClickJobStatus)`
- **Paramètres**:
  - `file`: `UploadFile` = `File(...)`
  - `margin_percent`: `float` = `Form(40.0)`
  - `supplier_hint`: `str | None` = `Form(default=None)`
  - `auto_confirm`: `bool` = `Form(default=True)`
  - `session_id`: `str | None` = `Form(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `backend.schemas.invoices.ZeroClickJobStatus`
  - `core.invoice_extractor.extract_text_from_file`
  - *... et 7 autres*

#### 🔸 `list_zero_click_jobs`

```python
def list_zero_click_jobs( status: str | None = None,
```

**Description**: Liste les jobs zero-click récents pour le tenant courant.

- **Ligne**: 595
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/zero-click/jobs', response_model=ZeroClickJobListResponse)`
- **Paramètres**:
  - `status`: `str | None` = `None`
  - `session_id`: `str | None` = `None`
  - `limit`: `int` = `50`
  - `offset`: `int` = `0`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `backend.schemas.invoices.ZeroClickJobListResponse`
  - `backend.schemas.invoices.ZeroClickJobStatus`
  - *... et 2 autres*

#### 🔸 `get_zero_click_job`

```python
def get_zero_click_job(job_id: str, tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Récupère le statut d'un job zero-click par son ID.

- **Ligne**: 641
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/zero-click/jobs/{job_id}', response_model=ZeroClickJobStatus)`
- **Paramètres**:
  - `job_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `backend.schemas.invoices.ZeroClickJobStatus`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `get_product_match_suggestions`

```python
def get_product_match_suggestions( query: str,
```

**Description**: Retourne des suggestions de matching flou pour un nom de produit.

- **Ligne**: 672
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/match-suggestions')`
- **Paramètres**:
  - `query`: `str`
  - `max_results`: `int` = `5`
  - `min_score`: `float` = `60.0`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.services.product_matching`
  - `fastapi.Depends`

#### 🔸 `list_import_sessions`

```python
def list_import_sessions( limit: int = 50,
```

**Description**: Liste les sessions d'import avec statistiques agrégées.

- **Ligne**: 703
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/sessions', response_model=ImportSessionListResponse)`
- **Paramètres**:
  - `limit`: `int` = `50`
  - `offset`: `int` = `0`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.ImportSession`
  - `backend.schemas.invoices.ImportSessionDetails`
  - `backend.schemas.invoices.ImportSessionListResponse`
  - *... et 1 autres*

#### 🔸 `get_import_session_details`

```python
def get_import_session_details( session_id: str,
```

**Description**: Récupère les détails d'une session d'import avec tous ses imports.

- **Ligne**: 723
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/sessions/{session_id}', response_model=ImportSessionDetails)`
- **Paramètres**:
  - `session_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.ImportSessionDetails`
  - `backend.schemas.invoices.InvoiceImportSummary`
  - `backend.schemas.invoices.ZeroClickJobStatus`
  - *... et 2 autres*

#### 🔸 `get_invoice_history`

```python
def get_invoice_history( supplier: str | None = None,
```

- **Ligne**: 779
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/history', response_model=InvoiceHistoryResponse)`
- **Paramètres**:
  - `supplier`: `str | None` = `None`
  - `invoice_id`: `str | None` = `None`
  - `date_start`: `str | None` = `None`
  - `date_end`: `str | None` = `None`
  - `limit`: `int` = `100`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.invoices.InvoiceHistoryEntry`
  - `backend.schemas.invoices.InvoiceHistoryResponse`
  - `fastapi.Depends`

#### 🔸 `download_invoice_file`

```python
def download_invoice_file(invoice_id: str, tenant: Tenant = Depends(get_current_tenant)):
```

- **Ligne**: 801
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/history/{invoice_id}/file')`
- **Paramètres**:
  - `invoice_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.responses.FileResponse`

### `backend/api/maintenance.py`

#### 🔸 `list_backups`

```python
def list_backups(limit: int = Query(default=100, ge=1, le=1000)):
```

- **Ligne**: 17
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/backups', response_model=BackupListResponse)`
- **Paramètres**:
  - `limit`: `int` = `Query(default=100, ge=1, le=1000)`
- **Dépendances**:
  - `backend.schemas.maintenance.BackupListResponse`
  - `backend.services.maintenance`
  - `fastapi.Query`

#### 🔸 `download_backup`

```python
def download_backup(filename: str):
```

- **Ligne**: 23
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/backups/{filename}')`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.responses.FileResponse`
  - `pathlib.Path`

### `backend/api/margins.py`

#### 🔸 `calculate_margin`

```python
def calculate_margin( request: MarginRequest,
```

**Description**: Calcule les marges brute, opérationnelle et nette.

- **Ligne**: 148
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/calculate', response_model=MarginResponse)`
- **Paramètres**:
  - `request`: `MarginRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `decimal.Decimal`
  - `fastapi.Depends`

#### 🔸 `get_product_margins`

```python
def get_product_margins( category: Optional[str] = Query(default=None),
```

**Description**: Retourne les marges par produit avec:

- **Ligne**: 187
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/products', response_model=List[ProductMarginResponse])`
- **Paramètres**:
  - `category`: `Optional[str]` = `Query(default=None)`
  - `min_margin_pct`: `Optional[float]` = `Query(default=None)`
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `sort_by`: `str` = `Query(default='total_margin', regex='^(gross_margin_pct|total_margin|volume_sold)$')`
  - `limit`: `int` = `Query(default=100, le=500)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.margin_calculator.MarginCalculator`
  - *... et 6 autres*

#### 🔸 `get_category_margins`

```python
def get_category_margins( days_back: int = Query(default=30, ge=1, le=365),
```

**Description**: Retourne les marges agrégées par catégorie de produits.

- **Ligne**: 281
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/categories', response_model=List[CategoryMarginResponse])`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.margin_calculator.MarginCalculator`
  - *... et 5 autres*

#### 🔸 `get_product_pamp`

```python
def get_product_pamp( product_id: int,
```

**Description**: Retourne le PAMP (Prix d'Achat Moyen Pondéré) d'un produit

- **Ligne**: 338
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/pamp/{product_id}', response_model=PAMPResponse)`
- **Paramètres**:
  - `product_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.margin_calculator.MarginCalculator`
  - *... et 10 autres*

#### 🔸 `get_dish_margins` 🎀

```python
def get_dish_margins( min_margin_pct: Optional[float] = Query(default=None),
```

**Description**: Retourne les marges des plats du restaurant avec détail des ingrédients.

- **Ligne**: 416
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/dishes', response_model=List[DishMarginResponse])`
- **Paramètres**:
  - `min_margin_pct`: `Optional[float]` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.margin_calculator.MarginCalculator`
  - *... et 6 autres*

#### 🔸 `get_margin_alerts` 🎀

```python
def get_margin_alerts( threshold_pct: float = Query(default=20.0, ge=0, le=100),
```

**Description**: Retourne les alertes pour les produits avec des marges problématiques:

- **Ligne**: 483
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/alerts', response_model=List[MarginAlertResponse])`
- **Paramètres**:
  - `threshold_pct`: `float` = `Query(default=20.0, ge=0, le=100)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.margin_calculator.MarginCalculator`
  - *... et 5 autres*

#### 🔸 `get_margin_summary`

```python
def get_margin_summary( days_back: int = Query(default=30, ge=1, le=365),
```

**Description**: Résumé des marges:

- **Ligne**: 543
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/summary')`
- **Paramètres**:
  - `days_back`: `int` = `Query(default=30, ge=1, le=365)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.query_df`
  - `fastapi.Depends`
  - `fastapi.Query`

### `backend/api/newcms/cockpit.py`

#### 🔸 `async get_morning_brief_cockpit`

```python
async def get_morning_brief_cockpit( tenant: Tenant = Depends(get_current_tenant),
```

**Description**: **Morning Brief Cockpit - Vue agrégée complète**

- **Ligne**: 400
- **Réutilisabilité**: Low
- **Décorateurs**: `router.get('', response_model=MorningBriefCockpitResponse, summary='Morning Brief Cockpit', tags=['newcms-cockpit'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
  - `days_forecast`: `int` = `Query(default=7, ge=1, le=30, description='Horizon de prevision en jours')`
  - `top_anomalies_limit`: `int` = `Query(default=5, ge=1, le=20, description="Nombre d'anomalies a afficher")`
- **Dépendances**:
  - `backend.api.anomaly_detection.scan_for_anomalies`
  - `backend.api.cockpit._build_alerts`
  - `backend.api.cockpit._calculate_health_score`
  - `backend.api.cockpit._get_intelligence_summary`
  - `backend.api.cockpit._get_margin_summary`
  - *... et 25 autres*

#### 🔸 `async get_cockpit_actions`

```python
async def get_cockpit_actions( tenant: Tenant = Depends(get_current_tenant),
```

**Description**: **Call-to-Actions - Liste des actions actionnables**

- **Ligne**: 521
- **Réutilisabilité**: Low
- **Décorateurs**: `router.get('/actions', response_model=ActionsResponse, summary='Call-to-Actions du cockpit', tags=['newcms-cockpit'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
  - `category`: `Optional[str]` = `Query(default=None, description='Filtrer par categorie: urgent, important, suggested')`
- **Dépendances**:
  - `backend.api.anomaly_detection.scan_for_anomalies`
  - `backend.api.cockpit._build_alerts`
  - `backend.api.cockpit._calculate_health_score`
  - `backend.api.cockpit._get_intelligence_summary`
  - `backend.api.cockpit._get_margin_summary`
  - *... et 25 autres*

### `backend/api/newcms/finance.py`

#### 🔸 `get_finance_overview`

```python
def get_finance_overview( tenant: Tenant = Depends(get_current_tenant_or_default)
```

**Description**: **Finance Overview - Vue d'ensemble financière complète**

- **Ligne**: 520
- **Réutilisabilité**: Medium
- **Type de retour**: `FinanceOverviewResponse`
- **Décorateurs**: `router.get('/overview', response_model=FinanceOverviewResponse, summary='Overview Finance', tags=['newcms-finance'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 3 autres*

#### 🔸 `get_transactions`

```python
def get_transactions( q: Optional[str] = Query(None, description="Recherche texte sur libellé"),
```

**Description**: **Liste paginée des transactions bancaires**

- **Ligne**: 598
- **Réutilisabilité**: Medium
- **Type de retour**: `TransactionListResponse`
- **Décorateurs**: `router.get('/transactions', response_model=TransactionListResponse, summary='Liste des transactions', tags=['newcms-finance'])`
- **Paramètres**:
  - `q`: `Optional[str]` = `Query(None, description='Recherche texte sur libellé')`
  - `date_from`: `Optional[date]` = `Query(None, description='Date de début')`
  - `date_to`: `Optional[date]` = `Query(None, description='Date de fin')`
  - `amount_min`: `Optional[float]` = `Query(None, ge=0, description='Montant minimum')`
  - `amount_max`: `Optional[float]` = `Query(None, ge=0, description='Montant maximum')`
  - `direction`: `Optional[str]` = `Query(None, description='Direction (IN/OUT/TRANSFER)')`
  - `category`: `Optional[str]` = `Query(None, description='Catégorie')`
  - `page`: `int` = `Query(1, ge=1, description='Numéro de page')`
  - `per_page`: `int` = `Query(50, ge=1, le=100, description="Nombre d'items par page")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `core.data_repository.exec_sql`
  - *... et 10 autres*

#### 🔸 `apply_reconciliation_suggestion`

```python
def apply_reconciliation_suggestion( request: ApplyReconciliationRequest,
```

**Description**: **Appliquer une suggestion de rapprochement IA**

- **Ligne**: 748
- **Réutilisabilité**: Medium
- **Type de retour**: `ApplyReconciliationResponse`
- **Décorateurs**: `router.post('/reconciliation/apply', response_model=ApplyReconciliationResponse, summary='Appliquer un rapprochement', tags=['newcms-finance'])`
- **Paramètres**:
  - `request`: `ApplyReconciliationRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `datetime.date`
  - *... et 5 autres*

#### 🔸 `categorize_transaction`

```python
def categorize_transaction( transaction_id: int,
```

- **Ligne**: 897
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/{transaction_id}/categorize', summary='Catégoriser une transaction', tags=['newcms-finance'])`
- **Paramètres**:
  - `transaction_id`: `int`
  - `payload`: `CategorizeRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`

#### 🔸 `ignore_transaction`

```python
def ignore_transaction( transaction_id: int,
```

- **Ligne**: 924
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/{transaction_id}/ignore', summary='Ignorer une transaction', tags=['newcms-finance'])`
- **Paramètres**:
  - `transaction_id`: `int`
  - `payload`: `IgnoreRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`

#### 🔸 `manual_reconcile_transaction`

```python
def manual_reconcile_transaction( transaction_id: int,
```

- **Ligne**: 950
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/{transaction_id}/reconcile-manual', summary='Rapprochement manuel', tags=['newcms-finance'])`
- **Paramètres**:
  - `transaction_id`: `int`
  - `payload`: `ManualReconcileRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `fastapi.HTTPException`

#### 🔸 `export_transactions`

```python
def export_transactions( filters: ExportFilter,
```

- **Ligne**: 980
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/transactions/bulk-export', summary='Export CSV filtré', tags=['newcms-finance'])`
- **Paramètres**:
  - `filters`: `ExportFilter`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `backend.services.finance.rules`
  - *... et 8 autres*

#### 🔸 `list_finance_rules`

```python
def list_finance_rules( tenant: Tenant = Depends(get_current_tenant_or_default),
```

- **Ligne**: 1097
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/rules', summary='Lister les règles finance', tags=['newcms-finance'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `backend.services.finance.rules`
  - `fastapi.Depends`

#### 🔸 `create_finance_rule`

```python
def create_finance_rule( payload: FinanceRuleCreate,
```

- **Ligne**: 1106
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/rules', summary='Créer une règle finance', tags=['newcms-finance'])`
- **Paramètres**:
  - `payload`: `FinanceRuleCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`

#### 🔸 `update_finance_rule`

```python
def update_finance_rule( rule_id: str,
```

- **Ligne**: 1131
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.put('/rules/{rule_id}', summary='Mettre à jour une règle', tags=['newcms-finance'])`
- **Paramètres**:
  - `rule_id`: `str`
  - `payload`: `FinanceRuleCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`

#### 🔸 `delete_finance_rule`

```python
def delete_finance_rule( rule_id: str,
```

- **Ligne**: 1145
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.delete('/rules/{rule_id}', summary='Supprimer une règle', tags=['newcms-finance'])`
- **Paramètres**:
  - `rule_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `fastapi.Depends`
  - `fastapi.HTTPException`

#### 🔸 `apply_finance_rules`

```python
def apply_finance_rules( payload: ApplyRulesRequest,
```

- **Ligne**: 1157
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/rules/apply', summary='Appliquer des règles de catégorisation', tags=['newcms-finance'])`
- **Paramètres**:
  - `payload`: `ApplyRulesRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `backend.services.finance.rules`
  - *... et 8 autres*

#### 🔸 `list_accounts`

```python
def list_accounts( tenant: Tenant = Depends(get_current_tenant_or_default),
```

- **Ligne**: 1260
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.get('/accounts', summary='Lister les comptes bancaires', tags=['newcms-finance'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `core.data_repository.exec_sql`
  - *... et 3 autres*

#### 🔸 `refresh_accounts`

```python
def refresh_accounts( tenant: Tenant = Depends(get_current_tenant_or_default),
```

- **Ligne**: 1304
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/accounts/refresh', summary='Rafraîchir la synchro comptes', tags=['newcms-finance'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`

#### 🔸 `simulate_cashflow`

```python
def simulate_cashflow( tenant: Tenant = Depends(get_current_tenant_or_default),
```

- **Ligne**: 1312
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/accounts/simulate-cashflow', summary='Simuler un cashflow', tags=['newcms-finance'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `core.data_repository.exec_sql`
  - *... et 3 autres*

#### 🔸 `list_finance_categories`

```python
def list_finance_categories( tenant: Tenant = Depends(get_current_tenant_or_default),
```

- **Ligne**: 1336
- **Réutilisabilité**: High
- **Type de retour**: `list[FinanceCategoryResponse]`
- **Décorateurs**: `router.get('/categories', summary='Lister les catégories finance', tags=['newcms-finance'], response_model=list[FinanceCategoryResponse])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.query_df`
  - `fastapi.Depends`

### `backend/api/newcms/intelligence.py`

#### 🔸 `get_intelligence_overview`

```python
def get_intelligence_overview( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: **Intelligence Overview - IA & Analytics**

- **Ligne**: 729
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/overview', response_model=IntelligenceOverviewResponse, summary='Intelligence Overview', tags=['newcms-intelligence'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.supplier_scoring.SupplierScoreCalculator`
  - `fastapi.Depends`

#### 🔸 `get_recommendations`

```python
def get_recommendations( priority: Optional[PriorityLevel] = Query(default=None),
```

**Description**: **Liste complète des recommandations IA**

- **Ligne**: 805
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/recommendations', response_model=List[RecommendationResponse], summary='Liste des recommandations IA', tags=['newcms-intelligence'])`
- **Paramètres**:
  - `priority`: `Optional[PriorityLevel]` = `Query(default=None)`
  - `type`: `Optional[RecommendationType]` = `Query(default=None)`
  - `limit`: `int` = `Query(default=20, le=100)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - *... et 10 autres*

#### 🔸 `apply_recommendation`

```python
def apply_recommendation( recommendation_id: str,
```

**Description**: **Appliquer une recommandation IA**

- **Ligne**: 846
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/recommendations/{recommendation_id}/apply', response_model=ApplyRecommendationResponse, summary='Appliquer une recommandation', tags=['newcms-intelligence'])`
- **Paramètres**:
  - `recommendation_id`: `str`
  - `action_index`: `int` = `Query(default=0, ge=0)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - *... et 9 autres*

#### 🔸 `get_health_score`

```python
def get_health_score( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: **Score de santé global - Note unique (0-10)**

- **Ligne**: 914
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/health-score', response_model=HealthScoreResponse, summary='Score de santé global', tags=['newcms-intelligence'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`

#### 🔸 `get_metrics_summary`

```python
def get_metrics_summary( tenant: Tenant = Depends(get_current_tenant)
```

**Description**: **Résumé des métriques - Pour graphiques dashboard**

- **Ligne**: 952
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/metrics/summary', summary='Résumé des métriques', tags=['newcms-intelligence'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.finance.anomaly_detection.AnomalyDetector`
  - *... et 16 autres*

### `backend/api/newcms/operations.py`

#### 🔸 `async get_operations_overview`

```python
async def get_operations_overview( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Description**: **Operations Overview - Vue d'ensemble opérationnelle**

- **Ligne**: 283
- **Réutilisabilité**: Medium
- **Type de retour**: `OperationsOverviewResponse`
- **Décorateurs**: `router.get('/overview', response_model=OperationsOverviewResponse, summary='Overview Opérations', tags=['newcms-operations'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.OperationsOverviewResponse`
  - `core.data_repository.query_df`
  - `datetime.date`
  - *... et 5 autres*

#### 🔸 `async get_catalog_proxy`

```python
async def get_catalog_proxy( page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
```

**Description**: **Catalogue produits - Liste paginée**

- **Ligne**: 443
- **Réutilisabilité**: Medium
- **Type de retour**: `CatalogProxyResponse`
- **Décorateurs**: `router.get('/catalog', response_model=CatalogProxyResponse, summary='Catalogue produits paginé', tags=['newcms-operations'])`
- **Paramètres**:
  - `page`: `int` = `Query(default=1, ge=1, le=10000, description='Numéro de page')`
  - `per_page`: `int` = `Query(default=20, ge=1, le=100, description='Éléments par page (max 100)')`
  - `q`: `str | None` = `Query(default=None, description='Recherche textuelle (nom produit)')`
  - `category`: `str | None` = `Query(default=None, description='Filtrer par catégorie')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.CatalogProxyResponse`
  - `backend.schemas.newcms.CreateOrderRequest`
  - `backend.schemas.newcms.InvoiceImportLineUpdateRequest`
  - *... et 7 autres*

#### 🔸 `async get_stock_proxy`

```python
async def get_stock_proxy( page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
```

**Description**: **Stock produits - Liste paginée avec statuts**

- **Ligne**: 487
- **Réutilisabilité**: Medium
- **Type de retour**: `StockProxyResponse`
- **Décorateurs**: `router.get('/stock', response_model=StockProxyResponse, summary='Stock produits paginé', tags=['newcms-operations'])`
- **Paramètres**:
  - `page`: `int` = `Query(default=1, ge=1, le=10000, description='Numéro de page')`
  - `per_page`: `int` = `Query(default=20, ge=1, le=100, description='Éléments par page (max 100)')`
  - `q`: `str | None` = `Query(default=None, description='Recherche textuelle')`
  - `status`: `str | None` = `Query(default=None, description='Filtrer par statut: critical, low, ok')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.CreateOrderRequest`
  - `backend.schemas.newcms.InvoiceImportLineUpdateRequest`
  - `backend.schemas.newcms.InvoiceImportUploadRequest`
  - *... et 7 autres*

#### 🔸 `async get_invoices_proxy`

```python
async def get_invoices_proxy( page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
```

**Description**: **Factures traitées - Liste paginée**

- **Ligne**: 551
- **Réutilisabilité**: Medium
- **Type de retour**: `InvoicesProxyResponse`
- **Décorateurs**: `router.get('/invoices', response_model=InvoicesProxyResponse, summary='Factures traitées paginées', tags=['newcms-operations'])`
- **Paramètres**:
  - `page`: `int` = `Query(default=1, ge=1, le=10000, description='Numéro de page')`
  - `per_page`: `int` = `Query(default=20, ge=1, le=100, description='Éléments par page (max 100)')`
  - `status`: `str | None` = `Query(default=None, description='Statut (non implémenté)')`
  - `date_from`: `str | None` = `Query(default=None, description='Date début (YYYY-MM-DD)')`
  - `date_to`: `str | None` = `Query(default=None, description='Date fin (YYYY-MM-DD)')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.InvoicesProxyResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `async create_invoice_import`

```python
async def create_invoice_import( payload: InvoiceImportUploadRequest,
```

**Description**: Reçoit un fichier (base64) et crée un job d'import dans un stockage léger.

- **Ligne**: 615
- **Réutilisabilité**: Medium
- **Type de retour**: `InvoiceImportStatusResponse`
- **Décorateurs**: `router.post('/invoices/import', response_model=InvoiceImportStatusResponse, summary="Créer un job d'import facture")`
- **Paramètres**:
  - `payload`: `InvoiceImportUploadRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.InvoiceImportStatusResponse`
  - `backend.schemas.newcms.InvoiceImportUploadRequest`
  - `base64`
  - *... et 6 autres*

#### 🔸 `async get_invoice_import_status`

```python
async def get_invoice_import_status( job_id: str,
```

- **Ligne**: 648
- **Réutilisabilité**: High
- **Type de retour**: `InvoiceImportStatusResponse`
- **Décorateurs**: `router.get('/invoices/import/{job_id}', response_model=InvoiceImportStatusResponse, summary="Statut d'un import facture")`
- **Paramètres**:
  - `job_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.InvoiceImportStatusResponse`
  - `fastapi.Depends`
  - `fastapi.HTTPException`

#### 🔸 `async update_invoice_import_line`

```python
async def update_invoice_import_line( job_id: str,
```

- **Ligne**: 663
- **Réutilisabilité**: Medium
- **Type de retour**: `InvoiceImportActionResponse`
- **Décorateurs**: `router.post('/invoices/import/{job_id}/lines/{line_id}', response_model=InvoiceImportActionResponse, summary="Corriger une ligne d'import")`
- **Paramètres**:
  - `job_id`: `str`
  - `line_id`: `str`
  - `payload`: `InvoiceImportLineUpdateRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.InvoiceImportActionResponse`
  - `backend.schemas.newcms.InvoiceImportLineUpdateRequest`
  - `datetime.date`
  - *... et 5 autres*

#### 🔸 `async confirm_invoice_import`

```python
async def confirm_invoice_import( job_id: str,
```

- **Ligne**: 692
- **Réutilisabilité**: Medium
- **Type de retour**: `InvoiceImportActionResponse`
- **Décorateurs**: `router.post('/invoices/import/{job_id}/confirm', response_model=InvoiceImportActionResponse, summary='Confirmer un import')`
- **Paramètres**:
  - `job_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.InvoiceImportActionResponse`
  - `backend.schemas.newcms.InvoiceImportLineUpdateRequest`
  - `datetime.date`
  - *... et 4 autres*

#### 🔸 `async cancel_invoice_import`

```python
async def cancel_invoice_import( job_id: str,
```

- **Ligne**: 771
- **Réutilisabilité**: High
- **Type de retour**: `InvoiceImportActionResponse`
- **Décorateurs**: `router.post('/invoices/import/{job_id}/cancel', response_model=InvoiceImportActionResponse, summary='Annuler un import')`
- **Paramètres**:
  - `job_id`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.InvoiceImportActionResponse`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 2 autres*

#### 🔸 `async email_webhook_import`

```python
async def email_webhook_import( payload: EmailWebhookPayload,
```

- **Ligne**: 787
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Décorateurs**: `router.post('/invoices/email-webhook', summary='Webhook email factures', tags=['internal'])`
- **Paramètres**:
  - `payload`: `EmailWebhookPayload`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `fastapi.Depends`
  - `typing.Any`

#### 🔸 `async resolve_price_anomaly`

```python
async def resolve_price_anomaly( product_id: int,
```

- **Ligne**: 808
- **Réutilisabilité**: High
- **Type de retour**: `PriceAnomalyResolveResponse`
- **Décorateurs**: `router.post('/price-anomalies/{product_id}/resolve', response_model=PriceAnomalyResolveResponse, summary='Résoudre une anomalie de prix')`
- **Paramètres**:
  - `product_id`: `int`
  - `payload`: `PriceAnomalyResolveRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.PriceAnomalyResolveRequest`
  - `backend.schemas.newcms.PriceAnomalyResolveResponse`
  - `fastapi.Depends`

#### 🔸 `async create_supplier_order`

```python
async def create_supplier_order( payload: CreateOrderRequest,
```

- **Ligne**: 826
- **Réutilisabilité**: High
- **Type de retour**: `CreateOrderResponse`
- **Décorateurs**: `router.post('/orders', response_model=CreateOrderResponse, summary='Créer une commande fournisseur')`
- **Paramètres**:
  - `payload`: `CreateOrderRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.newcms.CreateOrderRequest`
  - `backend.schemas.newcms.CreateOrderResponse`
  - `fastapi.Depends`
  - *... et 1 autres*

### `backend/api/newcms/restaurant.py`

#### 🔸 `get_restaurant_overview`

```python
def get_restaurant_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

**Description**: **Restaurant Overview - Vue d'ensemble restaurant**

- **Ligne**: 134
- **Réutilisabilité**: Low
- **Décorateurs**: `router.get('/overview', response_model=RestaurantOverviewResponse, summary='Overview Restaurant', tags=['newcms-restaurant'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `fastapi.APIRouter`
  - *... et 7 autres*

#### 🔸 `get_menus_overview`

```python
def get_menus_overview(tenant: Tenant = Depends(get_current_tenant_or_default)):
```

**Description**: Vue d'ensemble Menus & Coûts (food cost, marges, alertes ingrédients)

- **Ligne**: 292
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/menus/overview', response_model=RestaurantMenuOverview, summary='Menus & Coûts', tags=['newcms-restaurant'])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.restaurant.RestaurantMenuOverview`
  - `fastapi.Depends`

#### 🔸 `get_plat_detail`

```python
def get_plat_detail( plat_id: int,
```

**Description**: Détail d'un plat restaurant (fiche technique, prix, marge).

- **Ligne**: 298
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/plat/{plat_id}', response_model=PlatDetail, summary='Détail plat (restaurant)', tags=['newcms-restaurant'])`
- **Paramètres**:
  - `plat_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.schemas.restaurant.PlatDetail`
  - `fastapi.Depends`

#### 🔸 `get_mobile_inventory`

```python
def get_mobile_inventory( page: int = Query(1, ge=1),
```

**Description**: **Inventaire mobile - Liste paginée**

- **Ligne**: 315
- **Réutilisabilité**: Medium
- **Décorateurs**: `mobile_router.get('/inventory', response_model=MobileInventoryListResponse, summary='Inventaire mobile', tags=['newcms-mobile'])`
- **Paramètres**:
  - `page`: `int` = `Query(1, ge=1)`
  - `page_size`: `int` = `Query(50, ge=1, le=200)`
  - `search`: `Optional[str]` = `None`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.query_df`
  - `fastapi.Depends`
  - `fastapi.Query`
  - *... et 2 autres*

#### 🔸 `scan_barcode`

```python
def scan_barcode( payload: MobileScanRequest,
```

**Description**: **Scan code-barres - Recherche par EAN**

- **Ligne**: 405
- **Réutilisabilité**: Medium
- **Décorateurs**: `mobile_router.post('/scan', response_model=MobileScanResponse, summary='Scan code-barres', tags=['newcms-mobile'])`
- **Paramètres**:
  - `payload`: `MobileScanRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.query_df`
  - `fastapi.Depends`
  - `sqlalchemy.text`

#### 🔸 `adjust_stock`

```python
def adjust_stock( payload: MobileAdjustRequest,
```

**Description**: **Ajustement stock - Correction depuis mobile**

- **Ligne**: 474
- **Réutilisabilité**: Low
- **Décorateurs**: `mobile_router.post('/adjust', response_model=MobileAdjustResponse, summary='Ajustement stock mobile', tags=['newcms-mobile'])`
- **Paramètres**:
  - `payload`: `MobileAdjustRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `fastapi.Depends`
  - *... et 2 autres*

### `backend/api/prices.py`

#### 🔸 `get_price_history`

```python
def get_price_history( product_id: Optional[int] = Query(default=None, alias="product_id"),
```

- **Ligne**: 23
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/history')`
- **Paramètres**:
  - `product_id`: `Optional[int]` = `Query(default=None, alias='product_id')`
  - `code`: `Optional[str]` = `None`
  - `supplier`: `Optional[str]` = `None`
  - `search`: `Optional[str]` = `None`
  - `date_start`: `Optional[datetime]` = `Query(default=None)`
  - `date_end`: `Optional[datetime]` = `Query(default=None)`
  - `limit`: `int` = `Query(default=500, ge=1, le=2000)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.price_history_service.fetch_latest_price_per_code`
  - `core.price_history_service.fetch_price_history`
  - `datetime.datetime`
  - *... et 3 autres*

#### 🔸 `get_latest_price_history`

```python
def get_latest_price_history( codes: list[str] | None = Query(default=None, description="Filtrer sur une liste de codes (répéter le param)."),
```

- **Ligne**: 51
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/latest', response_model=LatestPriceResponse)`
- **Paramètres**:
  - `codes`: `list[str] | None` = `Query(default=None, description='Filtrer sur une liste de codes (répéter le param).')`
  - `limit`: `int` = `Query(default=100, ge=1, le=500)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.prices.LatestPriceResponse`
  - `core.price_history_service.fetch_latest_price_per_code`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `bulk_fill_prices`

```python
def bulk_fill_prices(payload: BulkPriceCorrectionRequest, tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Met à jour en masse les prix manquants à partir d'une liste (product_id ou code).

- **Ligne**: 65
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/bulk-fill', response_model=BulkPriceCorrectionResponse)`
- **Paramètres**:
  - `payload`: `BulkPriceCorrectionRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.prices.BulkPriceCorrectionRequest`
  - `backend.schemas.prices.BulkPriceCorrectionResponse`
  - `core.price_correction_service.apply_price_corrections`
  - *... et 1 autres*

#### 🔸 `fill_prices_from_history`

```python
def fill_prices_from_history(tenant: Tenant = Depends(get_current_tenant)) -> dict:
```

**Description**: Tente de remplir prix_achat/prix_vente manquants depuis l'historique produits_price_history.

- **Ligne**: 72
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Décorateurs**: `router.post('/fill-from-history')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.price_history_service.fill_missing_prices_from_history`
  - `fastapi.Depends`

### `backend/api/reports.py`

#### 🔸 `get_reports_overview`

```python
def get_reports_overview(tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Retourne les analytics agrégées pour l'espace rapports.

- **Ligne**: 16
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/overview', response_model=ReportsOverview)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.reports.ReportsOverview`
  - `fastapi.Depends`

#### 🔸 `export_report_dataset`

```python
def export_report_dataset( report_type: str,
```

**Description**: Diffuse un export CSV pour le dataset demandé.

- **Ligne**: 24
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/export/{report_type}')`
- **Paramètres**:
  - `report_type`: `str`
  - `limit`: `int` = `Query(default=5000, ge=10, le=50000)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.Query`
  - *... et 1 autres*

### `backend/api/restaurant.py`

#### 🔸 `list_categories`

```python
def list_categories(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 65
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/charges/categories', response_model=list[RestaurantCategory])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantCategory`
  - `backend.schemas.restaurant.RestaurantCategoryCreate`
  - `fastapi.Depends`

#### 🔸 `create_category`

```python
def create_category(payload: RestaurantCategoryCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 70
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/charges/categories', response_model=RestaurantCategory)`
- **Paramètres**:
  - `payload`: `RestaurantCategoryCreate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantCategory`
  - `backend.schemas.restaurant.RestaurantCategoryCreate`
  - `fastapi.Depends`

#### 🔸 `list_cost_centers`

```python
def list_cost_centers(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 75
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/charges/cost-centers', response_model=list[RestaurantCostCenter])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantCostCenter`
  - `backend.schemas.restaurant.RestaurantCostCenterCreate`
  - `fastapi.Depends`

#### 🔸 `create_cost_center`

```python
def create_cost_center(payload: RestaurantCostCenterCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 80
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/charges/cost-centers', response_model=RestaurantCostCenter)`
- **Paramètres**:
  - `payload`: `RestaurantCostCenterCreate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantCostCenter`
  - `backend.schemas.restaurant.RestaurantCostCenterCreate`
  - `fastapi.Depends`

#### 🔸 `list_expenses`

```python
def list_expenses(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 85
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/charges/expenses', response_model=list[RestaurantExpense])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantExpense`
  - `backend.schemas.restaurant.RestaurantExpenseCreate`
  - `backend.schemas.restaurant.RestaurantExpenseSummary`
  - *... et 1 autres*

#### 🔸 `create_expense`

```python
def create_expense(payload: RestaurantExpenseCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 90
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/charges/expenses', response_model=RestaurantExpense)`
- **Paramètres**:
  - `payload`: `RestaurantExpenseCreate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantExpense`
  - `backend.schemas.restaurant.RestaurantExpenseCreate`
  - `backend.schemas.restaurant.RestaurantExpenseSummary`
  - *... et 1 autres*

#### 🔸 `expense_summary`

```python
def expense_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 101
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/charges/summary', response_model=list[RestaurantExpenseSummary])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantExpenseSummary`
  - `fastapi.Depends`

#### 🔸 `tva_summary`

```python
def tva_summary( months: int = Query(6, ge=1, le=24),
```

- **Ligne**: 106
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/charges/tva-summary', response_model=list[RestaurantTvaSummaryEntry])`
- **Paramètres**:
  - `months`: `int` = `Query(6, ge=1, le=24)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantTvaSummaryEntry`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `list_ingredients`

```python
def list_ingredients(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 114
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/ingredients', response_model=list[RestaurantIngredient])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredient`
  - `backend.schemas.restaurant.RestaurantIngredientCreate`
  - `backend.schemas.restaurant.RestaurantIngredientEpicerieLink`
  - *... et 5 autres*

#### 🔸 `create_ingredient`

```python
def create_ingredient(payload: RestaurantIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 119
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/ingredients', response_model=RestaurantIngredient)`
- **Paramètres**:
  - `payload`: `RestaurantIngredientCreate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredient`
  - `backend.schemas.restaurant.RestaurantIngredientCreate`
  - `backend.schemas.restaurant.RestaurantIngredientEpicerieLink`
  - *... et 5 autres*

#### 🔸 `update_ingredient`

```python
def update_ingredient( ingredient_id: int,
```

**Description**: Mettre à jour un ingrédient (nom, unité, coût, stock, catégorie, fournisseur).

- **Ligne**: 124
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.put('/ingredients/{ingredient_id}', response_model=RestaurantIngredient)`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `payload`: `RestaurantIngredientUpdate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.CostBreakdownResponse`
  - `backend.schemas.restaurant.FoodCostAnalysis`
  - *... et 47 autres*

#### 🔸 `delete_ingredient`

```python
def delete_ingredient( ingredient_id: int,
```

**Description**: Supprimer un ingrédient. Échoue si l'ingrédient est utilisé dans des plats.

- **Ligne**: 137
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.delete('/ingredients/{ingredient_id}')`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.CostBreakdownResponse`
  - `backend.schemas.restaurant.FoodCostAnalysis`
  - *... et 47 autres*

#### 🔸 `update_ingredient_price`

```python
def update_ingredient_price( ingredient_id: int,
```

- **Ligne**: 149
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.patch('/ingredients/{ingredient_id}/price', response_model=RestaurantIngredient)`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `payload`: `RestaurantIngredientPriceUpdate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredient`
  - `backend.schemas.restaurant.RestaurantIngredientCreate`
  - `backend.schemas.restaurant.RestaurantIngredientEpicerieLink`
  - *... et 5 autres*

#### 🔸 `ingredient_price_history`

```python
def ingredient_price_history( ingredient_id: int,
```

- **Ligne**: 158
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/ingredients/{ingredient_id}/price-history', response_model=list[RestaurantIngredientPriceHistoryEntry])`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredientPriceHistoryEntry`
  - `fastapi.Depends`

#### 🔸 `link_ingredient_to_epicerie`

```python
def link_ingredient_to_epicerie( ingredient_id: int,
```

**Description**: Lier un ingrédient à un produit épicerie pour synchroniser catégorie/fournisseur.

- **Ligne**: 166
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.put('/ingredients/{ingredient_id}/link-epicerie', response_model=RestaurantIngredient)`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `payload`: `RestaurantIngredientEpicerieLink`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredient`
  - `backend.schemas.restaurant.RestaurantIngredientCreate`
  - `backend.schemas.restaurant.RestaurantIngredientEpicerieLink`
  - *... et 5 autres*

#### 🔸 `update_ingredient_ratio`

```python
def update_ingredient_ratio( ingredient_id: int,
```

**Description**: Mettre à jour le ratio de conversion ingrédient-épicerie.

- **Ligne**: 178
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.patch('/ingredients/{ingredient_id}/ratio', response_model=RestaurantIngredient)`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `payload`: `RestaurantIngredientRatioUpdate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredient`
  - `backend.schemas.restaurant.RestaurantIngredientCreate`
  - `backend.schemas.restaurant.RestaurantIngredientEpicerieLink`
  - *... et 5 autres*

#### 🔸 `unlink_ingredient_from_epicerie`

```python
def unlink_ingredient_from_epicerie( ingredient_id: int,
```

**Description**: Supprimer le lien entre un ingrédient et un produit épicerie.

- **Ligne**: 188
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.delete('/ingredients/{ingredient_id}/link-epicerie', response_model=RestaurantIngredient)`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredient`
  - `backend.schemas.restaurant.RestaurantIngredientCreate`
  - `backend.schemas.restaurant.RestaurantIngredientEpicerieLink`
  - *... et 5 autres*

#### 🔸 `sync_ingredient_prices`

```python
def sync_ingredient_prices( force_update: bool = Query(False, description="Force update all linked ingredients"),
```

**Description**: Synchronise les prix des ingrédients à partir des produits épicerie liés.

- **Ligne**: 197
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/ingredients/sync-prices')`
- **Paramètres**:
  - `force_update`: `bool` = `Query(False, description='Force update all linked ingredients')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_price_sync_status`

```python
def get_price_sync_status(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Description**: Retourne le statut de synchronisation des prix pour tous les ingrédients.

- **Ligne**: 218
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/ingredients/price-sync-status')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`

#### 🔸 `audit_ingredient_epicerie_links`

```python
def audit_ingredient_epicerie_links( dry_run: bool = Query(True, description="Ne pas modifier; uniquement lister les liens incohérents."),
```

**Description**: Audit des liens incohérents ingrédients ↔ épicerie (ex: ail lié à un whisky).

- **Ligne**: 229
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/ingredients/audit-epicerie-links')`
- **Paramètres**:
  - `dry_run`: `bool` = `Query(True, description='Ne pas modifier; uniquement lister les liens incohérents.')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `list_ingredients_with_price_source`

```python
def list_ingredients_with_price_source(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Description**: Liste les ingrédients avec indication explicite de la source de prix.

- **Ligne**: 239
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/ingredients/with-price-source', response_model=list[dict])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`

#### 🔸 `list_stock_movements`

```python
def list_stock_movements( ingredient_id: Optional[int] = None,
```

**Description**: Liste les mouvements de stock restaurant avec filtres.

- **Ligne**: 256
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/stock/movements')`
- **Paramètres**:
  - `ingredient_id`: `Optional[int]` = `None`
  - `source`: `Optional[str]` = `None`
  - `type_mouvement`: `Optional[str]` = `None`
  - `date_from`: `Optional[date]` = `None`
  - `date_to`: `Optional[date]` = `None`
  - `limit`: `int` = `Query(100, ge=1, le=50000)`
  - `offset`: `int` = `Query(0, ge=0)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredientPriceUpdate`
  - `backend.schemas.restaurant.RestaurantIngredientRatioUpdate`
  - `backend.schemas.restaurant.RestaurantIngredientUpdate`
  - *... et 7 autres*

#### 🔸 `get_daily_movements_by_category`

```python
def get_daily_movements_by_category( date_from: Optional[date] = None,
```

**Description**: Agrégation des mouvements par jour et catégorie pour graphiques.

- **Ligne**: 280
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/stock/movements/daily-by-category')`
- **Paramètres**:
  - `date_from`: `Optional[date]` = `None`
  - `date_to`: `Optional[date]` = `None`
  - `type_mouvement`: `str` = `Query('sortie', description='Type de mouvement à agréger')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredientPriceUpdate`
  - `backend.schemas.restaurant.RestaurantIngredientRatioUpdate`
  - `backend.schemas.restaurant.RestaurantIngredientUpdate`
  - *... et 6 autres*

#### 🔸 `get_daily_consumption_by_plat`

```python
def get_daily_consumption_by_plat( date_from: Optional[date] = None,
```

**Description**: Agrégation des consommations (sorties) par jour et par plat pour graphiques.

- **Ligne**: 296
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/stock/movements/daily-by-plat')`
- **Paramètres**:
  - `date_from`: `Optional[date]` = `None`
  - `date_to`: `Optional[date]` = `None`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantIngredientPriceUpdate`
  - `backend.schemas.restaurant.RestaurantIngredientRatioUpdate`
  - `backend.schemas.restaurant.RestaurantIngredientUpdate`
  - *... et 5 autres*

#### 🔸 `get_stock_summary`

```python
def get_stock_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Description**: Résumé du stock actuel par ingrédient.

- **Ligne**: 310
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/stock/summary')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`

#### 🔸 `get_stock_analytics`

```python
def get_stock_analytics( days: int = Query(30, ge=1, le=365),
```

**Description**: Statistiques de stock sur une période.

- **Ligne**: 316
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/stock/analytics')`
- **Paramètres**:
  - `days`: `int` = `Query(30, ge=1, le=365)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_stock_movement`

```python
def create_stock_movement( ingredient_id: int = Body(...),
```

**Description**: Crée un mouvement de stock.

- **Ligne**: 325
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/stock/movements')`
- **Paramètres**:
  - `ingredient_id`: `int` = `Body(...)`
  - `type_mouvement`: `str` = `Body(...)`
  - `quantite`: `float` = `Body(...)`
  - `source`: `str` = `Body(...)`
  - `unite`: `Optional[str]` = `Body(None)`
  - `cout_unitaire`: `Optional[float]` = `Body(None)`
  - `facture_id`: `Optional[int]` = `Body(None)`
  - `facture_ref`: `Optional[str]` = `Body(None)`
  - `fournisseur`: `Optional[str]` = `Body(None)`
  - `produit_epicerie_id`: `Optional[int]` = `Body(None)`
  - `commentaire`: `Optional[str]` = `Body(None)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.services.restaurant.price_sync.get_ingredients_with_price_source`
  - `fastapi.Body`
  - `fastapi.Depends`
  - *... et 1 autres*

#### 🔸 `transfer_from_epicerie`

```python
def transfer_from_epicerie( ingredient_id: int = Body(...),
```

**Description**: Transfère du stock depuis un produit épicerie.

- **Ligne**: 357
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/stock/transfer-from-epicerie')`
- **Paramètres**:
  - `ingredient_id`: `int` = `Body(...)`
  - `produit_epicerie_id`: `int` = `Body(...)`
  - `quantite`: `float` = `Body(...)`
  - `commentaire`: `Optional[str]` = `Body(None)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Body`
  - `fastapi.Depends`
  - `typing.Optional`

#### 🔸 `adjust_stock`

```python
def adjust_stock( ingredient_id: int = Body(...),
```

**Description**: Ajuste le stock à une nouvelle quantité (inventaire).

- **Ligne**: 375
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/stock/adjustment')`
- **Paramètres**:
  - `ingredient_id`: `int` = `Body(...)`
  - `new_quantity`: `float` = `Body(...)`
  - `commentaire`: `Optional[str]` = `Body(None)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Body`
  - `fastapi.Depends`
  - `typing.Optional`

#### 🔸 `record_consumption`

```python
def record_consumption( ingredient_id: int = Body(...),
```

**Description**: Enregistre une sortie de stock pour consommation.

- **Ligne**: 391
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/stock/consumption')`
- **Paramètres**:
  - `ingredient_id`: `int` = `Body(...)`
  - `quantite`: `float` = `Body(...)`
  - `commentaire`: `Optional[str]` = `Body(None)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Body`
  - `fastapi.Depends`
  - `typing.Optional`

#### 🔸 `list_plats`

```python
def list_plats(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 407
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/plats', response_model=list[RestaurantPlat])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPlat`
  - `backend.schemas.restaurant.RestaurantPlatCreate`
  - `backend.schemas.restaurant.RestaurantPlatIngredientCreate`
  - *... et 4 autres*

#### 🔸 `create_plat`

```python
def create_plat(payload: RestaurantPlatCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 412
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/plats', response_model=RestaurantPlat)`
- **Paramètres**:
  - `payload`: `RestaurantPlatCreate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPlat`
  - `backend.schemas.restaurant.RestaurantPlatCreate`
  - `backend.schemas.restaurant.RestaurantPlatIngredientCreate`
  - *... et 4 autres*

#### 🔸 `delete_plat`

```python
def delete_plat(plat_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Description**: Supprimer un plat et ses ingrédients associés.

- **Ligne**: 417
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.delete('/plats/{plat_id}')`
- **Paramètres**:
  - `plat_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.CostBreakdownResponse`
  - `backend.schemas.restaurant.FoodCostAnalysis`
  - *... et 51 autres*

#### 🔸 `attach_ingredient`

```python
def attach_ingredient(plat_id: int, payload: RestaurantPlatIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 426
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/plats/{plat_id}/ingredients')`
- **Paramètres**:
  - `plat_id`: `int`
  - `payload`: `RestaurantPlatIngredientCreate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPlatIngredientCreate`
  - `fastapi.Depends`

#### 🔸 `remove_ingredient`

```python
def remove_ingredient(plat_id: int, ingredient_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 431
- **Réutilisabilité**: High
- **Décorateurs**: `router.delete('/plats/{plat_id}/ingredients/{ingredient_id}')`
- **Paramètres**:
  - `plat_id`: `int`
  - `ingredient_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`

#### 🔸 `update_ingredient_on_plat`

```python
def update_ingredient_on_plat( plat_id: int,
```

**Description**: Met à jour la quantité/unité d'un ingrédient sur un plat.

- **Ligne**: 436
- **Réutilisabilité**: High
- **Décorateurs**: `router.patch('/plats/{plat_id}/ingredients/{ingredient_id}')`
- **Paramètres**:
  - `plat_id`: `int`
  - `ingredient_id`: `int`
  - `payload`: `RestaurantPlatIngredientUpdate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPlatIngredientUpdate`
  - `fastapi.Depends`

#### 🔸 `update_plat_price`

```python
def update_plat_price( plat_id: int,
```

- **Ligne**: 447
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.patch('/plats/{plat_id}/price', response_model=RestaurantPlat)`
- **Paramètres**:
  - `plat_id`: `int`
  - `payload`: `RestaurantPlatPriceUpdate`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPlat`
  - `backend.schemas.restaurant.RestaurantPlatCreate`
  - `backend.schemas.restaurant.RestaurantPlatIngredientCreate`
  - *... et 4 autres*

#### 🔸 `plat_price_history`

```python
def plat_price_history( plat_id: int,
```

- **Ligne**: 456
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/plats/{plat_id}/price-history', response_model=list[RestaurantPlatPriceHistoryEntry])`
- **Paramètres**:
  - `plat_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPlatPriceHistoryEntry`
  - `fastapi.Depends`

#### 🔸 `recompute_plat_costs`

```python
def recompute_plat_costs( margin_threshold: float = Body(35.0, ge=1.0, description="Seuil de marge (%) pour générer des alertes."),
```

- **Ligne**: 464
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/plats/recompute-costs')`
- **Paramètres**:
  - `margin_threshold`: `float` = `Body(35.0, ge=1.0, description='Seuil de marge (%) pour générer des alertes.')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Body`
  - `fastapi.Depends`

#### 🔸 `plat_composition`

```python
def plat_composition( plat_id: int,
```

**Description**: Retourne la composition d'un plat avec coûts par ingrédient et pourcentage.

- **Ligne**: 472
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/plats/{plat_id}/composition')`
- **Paramètres**:
  - `plat_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Depends`

#### 🔸 `transfer_from_epicerie`

```python
def transfer_from_epicerie( produit_restaurant_id: int = Body(..., embed=True),
```

**Description**: Transfère du stock depuis l'épicerie vers le restaurant via la fonction SQL transfer_from_epicerie.

- **Ligne**: 483
- **Réutilisabilité**: High
- **Décorateurs**: `router.post('/transfer')`
- **Paramètres**:
  - `produit_restaurant_id`: `int` = `Body(..., embed=True)`
  - `quantite`: `float` = `Body(1.0, ge=0.0001, embed=True)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `fastapi.Body`
  - `fastapi.Depends`

#### 🔸 `list_consumptions`

```python
def list_consumptions( period: str = Query("all", description="Période: 7d, 30d, 90d, 1y, all"),
```

**Description**: Liste des consommations avec filtre de période optionnel.

- **Ligne**: 495
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/consumptions', response_model=list[RestaurantConsumptionEntry])`
- **Paramètres**:
  - `period`: `str` = `Query('all', description='Période: 7d, 30d, 90d, 1y, all')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantConsumptionEntry`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `list_price_history_comparison`

```python
def list_price_history_comparison(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 504
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/price-history/comparison', response_model=list[RestaurantPriceHistoryComparisonEntry])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPriceHistoryComparisonEntry`
  - `fastapi.Depends`

#### 🔸 `list_epicerie_products`

```python
def list_epicerie_products():
```

**Description**: List all epicerie products available for mapping.

- **Ligne**: 509
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/epicerie/products')`

#### 🔸 `search_epicerie_products`

```python
def search_epicerie_products( q: str = Query("", description="Search query"),
```

**Description**: Fast search endpoint for epicerie products.

- **Ligne**: 515
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/epicerie/products/search')`
- **Paramètres**:
  - `q`: `str` = `Query('', description='Search query')`
  - `limit`: `int` = `Query(20, ge=1, le=100)`
  - `suggest_for`: `str` = `Query(None, description='Ingredient name to get smart suggestions')`
- **Dépendances**:
  - `fastapi.Query`

#### 🔸 `list_restaurant_alerts`

```python
def list_restaurant_alerts(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 536
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/alerts', response_model=list[RestaurantAlert])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantAlert`
  - `backend.schemas.restaurant.RestaurantAlertDetail`
  - `fastapi.Depends`

#### 🔸 `restaurant_dashboard_overview`

```python
def restaurant_dashboard_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
```

- **Ligne**: 541
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/dashboard/overview', response_model=RestaurantDashboardOverview)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantDashboardOverview`
  - `fastapi.Depends`

#### 🔸 `restaurant_forecast_overview`

```python
def restaurant_forecast_overview( horizon_days: int = Query(30, ge=1, le=180),
```

- **Ligne**: 547
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/forecasts/overview', response_model=RestaurantForecastOverview)`
- **Paramètres**:
  - `horizon_days`: `int` = `Query(30, ge=1, le=180)`
  - `granularity`: `str` = `Query('weekly')`
  - `top`: `int` = `Query(8, ge=1, le=50)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantForecastOverview`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `price_history_overview`

```python
def price_history_overview( limit: int = Query(12, ge=1, le=200),
```

- **Ligne**: 563
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/prices/history', response_model=RestaurantPriceHistoryOverview)`
- **Paramètres**:
  - `limit`: `int` = `Query(12, ge=1, le=200)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantPriceHistoryOverview`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_restaurant_overview`

```python
def get_restaurant_overview( period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
```

**Description**: Vue d'ensemble du restaurant.

- **Ligne**: 575
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/overview', response_model=RestaurantOverview)`
- **Paramètres**:
  - `period`: `str` = `Query('30d', description='Période: 7d, 30d, 90d, 1y')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantOverview`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `list_plats_paginated`

```python
def list_plats_paginated( page: int = Query(1, ge=1),
```

**Description**: Liste paginée des plats avec filtres et tri.

- **Ligne**: 594
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/plats/list', response_model=PlatListResponse)`
- **Paramètres**:
  - `page`: `int` = `Query(1, ge=1)`
  - `page_size`: `int` = `Query(50, ge=1, le=200)`
  - `categorie`: `str | None` = `Query(None)`
  - `actif`: `bool | None` = `Query(None)`
  - `min_margin_pct`: `float | None` = `Query(None)`
  - `sort_by`: `str` = `Query('nom', description='nom, margin_pct, sales_count, prix_vente_ttc')`
  - `sort_desc`: `bool` = `Query(False)`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.PlatListResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_plat_detail`

```python
def get_plat_detail( plat_id: int,
```

**Description**: Détails complets d'un plat.

- **Ligne**: 630
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/plats/{plat_id}/detail', response_model=PlatDetail)`
- **Paramètres**:
  - `plat_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.PlatDetail`
  - `fastapi.Depends`

#### 🔸 `get_plat_cost_breakdown`

```python
def get_plat_cost_breakdown( plat_id: int,
```

**Description**: Décomposition détaillée du coût d'un plat.

- **Ligne**: 648
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/plats/{plat_id}/cost-breakdown', response_model=CostBreakdownResponse)`
- **Paramètres**:
  - `plat_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.CostBreakdownResponse`
  - `fastapi.Depends`

#### 🔸 `list_ingredients_enhanced`

```python
def list_ingredients_enhanced(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Description**: Liste enrichie des ingrédients.

- **Ligne**: 665
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/ingredients/list', response_model=list[IngredientListItem])`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.IngredientListItem`
  - `backend.services.restaurant.price_sync.get_ingredients_with_price_source`
  - `backend.services.restaurant.price_sync.sync_ingredient_prices_from_epicerie`
  - *... et 3 autres*

#### 🔸 `get_ingredient_price_history_detail`

```python
def get_ingredient_price_history_detail( ingredient_id: int,
```

**Description**: Historique détaillé des prix d'un ingrédient.

- **Ligne**: 680
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/ingredients/{ingredient_id}/price-history-detail', response_model=IngredientPriceHistoryResponse)`
- **Paramètres**:
  - `ingredient_id`: `int`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.IngredientPriceHistoryResponse`
  - `fastapi.Depends`

#### 🔸 `get_food_cost_analysis`

```python
def get_food_cost_analysis( period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
```

**Description**: Analyse complète du food cost.

- **Ligne**: 692
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/food-cost/analysis', response_model=FoodCostAnalysis)`
- **Paramètres**:
  - `period`: `str` = `Query('30d', description='Période: 7d, 30d, 90d, 1y')`
  - `target_food_cost`: `float` = `Query(30.0, ge=0, le=100, description='Food cost cible en %')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.FoodCostAnalysis`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `simulate_plat_price_change`

```python
def simulate_plat_price_change( plat_id: int,
```

**Description**: Simulation de changement de prix.

- **Ligne**: 711
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/plats/{plat_id}/simulate-price', response_model=PriceSimulation)`
- **Paramètres**:
  - `plat_id`: `int`
  - `payload`: `PriceSimulationInput`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.PriceSimulation`
  - `backend.schemas.restaurant.PriceSimulationInput`
  - `fastapi.Depends`

#### 🔸 `list_restaurant_alerts_detailed`

```python
def list_restaurant_alerts_detailed( alert_type: str | None = Query(None, description="plat_margin, ingredient_price, stock_rupture"),
```

**Description**: Liste détaillée des alertes restaurant.

- **Ligne**: 738
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/alerts/detailed', response_model=list[RestaurantAlertDetail])`
- **Paramètres**:
  - `alert_type`: `str | None` = `Query(None, description='plat_margin, ingredient_price, stock_rupture')`
  - `severity`: `str | None` = `Query(None, description='critical, warning, info')`
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantAlertDetail`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_restaurant_menus_overview`

```python
def get_restaurant_menus_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
```

**Description**: Vue d'ensemble des menus : coûts matière, food cost, alertes ingrédients.

- **Ligne**: 768
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/menus/overview', response_model=RestaurantMenuOverview)`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_restaurant_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_restaurant_tenant`
  - `backend.schemas.restaurant.RestaurantMenuOverview`
  - `fastapi.Depends`

### `backend/api/routes.py`

#### 🔸 `include_routes`

```python
def include_routes(app: FastAPI) -> None:
```

- **Ligne**: 34
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `app`: `FastAPI`
- **Dépendances**:
  - `backend.api.admin`
  - `backend.api.analytics`
  - `backend.api.anomaly_detection`
  - `backend.api.audit`
  - `backend.api.audit_trail`
  - *... et 23 autres*

### `backend/api/rules_engine.py`

#### 🔸 `async classify_transaction`

```python
async def classify_transaction( transaction: TransactionInput,
```

**Description**: Classifie une transaction unique.

- **Ligne**: 108
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/classify', response_model=ClassificationResponse)`
- **Paramètres**:
  - `transaction`: `TransactionInput`
  - `detect_anomalies`: `bool` = `Query(True, description='Détecter les anomalies')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - `core.finance.rules_engine.bootstrap_default_rules`
  - *... et 2 autres*

#### 🔸 `async classify_batch`

```python
async def classify_batch( request: BatchClassificationRequest,
```

**Description**: Classifie un lot de transactions.

- **Ligne**: 148
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/classify/batch', response_model=BatchClassificationResponse)`
- **Paramètres**:
  - `request`: `BatchClassificationRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - `core.finance.rules_engine.bootstrap_default_rules`
  - *... et 1 autres*

#### 🔸 `async list_rules` 🎀

```python
async def list_rules( active_only: bool = Query(True, description="Uniquement les règles actives"),
```

**Description**: Liste toutes les règles de catégorisation.

- **Ligne**: 200
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/rules', response_model=List[RuleResponse])`
- **Paramètres**:
  - `active_only`: `bool` = `Query(True, description='Uniquement les règles actives')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - `core.finance.rules_engine.bootstrap_default_rules`
  - *... et 4 autres*

#### 🔸 `async create_rule` 🎀

```python
async def create_rule( rule: RuleCreate,
```

**Description**: Crée une nouvelle règle de catégorisation.

- **Ligne**: 217
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/rules', response_model=RuleResponse)`
- **Paramètres**:
  - `rule`: `RuleCreate`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - `core.finance.rules_engine.bootstrap_default_rules`
  - *... et 11 autres*

#### 🔸 `async record_feedback`

```python
async def record_feedback( feedback: FeedbackRequest,
```

**Description**: Enregistre un feedback sur une classification.

- **Ligne**: 261
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/feedback')`
- **Paramètres**:
  - `feedback`: `FeedbackRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - `core.finance.rules_engine.bootstrap_default_rules`
  - *... et 1 autres*

#### 🔸 `async bootstrap_rules`

```python
async def bootstrap_rules( tenant: Tenant = Depends(get_current_tenant),
```

**Description**: Initialise les règles par défaut pour le tenant.

- **Ligne**: 288
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/bootstrap')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - `core.finance.rules_engine.bootstrap_default_rules`
  - *... et 1 autres*

#### 🔸 `async get_classification_stats`

```python
async def get_classification_stats( days: int = Query(30, description="Nombre de jours d'historique"),
```

**Description**: Retourne des statistiques sur les classifications.

- **Ligne**: 318
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/stats')`
- **Paramètres**:
  - `days`: `int` = `Query(30, description="Nombre de jours d'historique")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `async suggest_category`

```python
async def suggest_category( description: str = Query(..., description="Description de la transaction"),
```

**Description**: Suggère une catégorie pour une transaction (endpoint léger).

- **Ligne**: 386
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/suggest')`
- **Paramètres**:
  - `description`: `str` = `Query(..., description='Description de la transaction')`
  - `amount`: `Optional[float]` = `Query(None, description='Montant')`
  - `supplier`: `Optional[str]` = `Query(None, description='Fournisseur')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `core.data_repository.get_engine`
  - `core.finance.rules_engine.FinancialRulesEngine`
  - `core.finance.rules_engine.RuleType`
  - *... et 4 autres*

### `backend/api/stock.py`

#### 🔸 `get_movement_timeseries`

```python
def get_movement_timeseries( window_days: int = Query(30, ge=1, le=365),
```

- **Ligne**: 20
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/movements/timeseries', response_model=MovementTimeseriesResponse)`
- **Paramètres**:
  - `window_days`: `int` = `Query(30, ge=1, le=365)`
  - `product_id`: `int | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.stock.MovementTimeseriesResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `get_recent_movements`

```python
def get_recent_movements( limit: int = Query(50, ge=1, le=500),
```

- **Ligne**: 35
- **Réutilisabilité**: High
- **Décorateurs**: `router.get('/movements/recent', response_model=RecentMovementsResponse)`
- **Paramètres**:
  - `limit`: `int` = `Query(50, ge=1, le=500)`
  - `product_id`: `int | None` = `Query(default=None)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.stock.RecentMovementsResponse`
  - `fastapi.Depends`
  - `fastapi.Query`

#### 🔸 `create_stock_adjustment`

```python
def create_stock_adjustment( payload: StockAdjustmentRequest,
```

- **Ligne**: 50
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.post('/adjustments', response_model=StockAdjustmentResponse)`
- **Paramètres**:
  - `payload`: `StockAdjustmentRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.stock.StockAdjustmentRequest`
  - `backend.schemas.stock.StockAdjustmentResponse`
  - `fastapi.Depends`
  - *... et 1 autres*

### `backend/api/supplier_scoring.py`

#### 🔸 `async get_suppliers_overview`

```python
async def get_suppliers_overview( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Description**: Vue d'ensemble des scores fournisseurs.

- **Ligne**: 61
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/overview')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 36 autres*

#### 🔸 `to_supplier_score`

```python
def to_supplier_score(item: Dict[str, Any], rank: int) -> SupplierScore:
```

- **Ligne**: 113
- **Réutilisabilité**: High
- **Type de retour**: `SupplierScore`
- **Paramètres**:
  - `item`: `Dict[str, Any]`
  - `rank`: `int`
- **Dépendances**:
  - `backend.schemas.supplier_scoring.SupplierScore`
  - `backend.schemas.supplier_scoring.TrendEnum`
  - `core.finance.supplier_scoring.SupplierScoreCalculator`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 3 autres*

#### 🔸 `async get_suppliers_list`

```python
async def get_suppliers_list( page: int = Query(1, ge=1, description="Numéro de page"),
```

**Description**: Liste paginée des fournisseurs avec scores.

- **Ligne**: 174
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/suppliers')`
- **Paramètres**:
  - `page`: `int` = `Query(1, ge=1, description='Numéro de page')`
  - `per_page`: `int` = `Query(20, ge=1, le=100, description='Résultats par page')`
  - `sort_by`: `str` = `Query('score', description='Tri: score, name, grade')`
  - `order`: `str` = `Query('desc', description='Ordre: asc, desc')`
  - `min_score`: `Optional[float]` = `Query(None, ge=0, le=100, description='Score minimum')`
  - `grade_filter`: `Optional[str]` = `Query(None, description='Filtrer par grade (A, B, C, D, F)')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 35 autres*

#### 🔸 `async get_supplier_details`

```python
async def get_supplier_details( supplier_id: int = Path(..., description="ID du fournisseur"),
```

**Description**: Détails complets d'un fournisseur.

- **Ligne**: 273
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/suppliers/{supplier_id}')`
- **Paramètres**:
  - `supplier_id`: `int` = `Path(..., description='ID du fournisseur')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 36 autres*

#### 🔸 `async get_supplier_history`

```python
async def get_supplier_history( supplier_id: int = Path(..., description="ID du fournisseur"),
```

**Description**: Historique des scores d'un fournisseur.

- **Ligne**: 412
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/suppliers/{supplier_id}/history')`
- **Paramètres**:
  - `supplier_id`: `int` = `Path(..., description='ID du fournisseur')`
  - `limit`: `int` = `Query(20, ge=1, le=100, description="Nombre d'entrées")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async get_scoring_criteria`

```python
async def get_scoring_criteria() -> Dict[str, Any]:
```

**Description**: Critères de scoring configurables.

- **Ligne**: 485
- **Réutilisabilité**: Low
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/criteria')`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 32 autres*

#### 🔸 `async update_scoring_criteria`

```python
async def update_scoring_criteria( request: UpdateScoringCriteriaRequest,
```

**Description**: Mettre à jour les pondérations des critères de scoring.

- **Ligne**: 569
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.put('/criteria')`
- **Paramètres**:
  - `request`: `UpdateScoringCriteriaRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 32 autres*

#### 🔸 `async get_supplier_alerts`

```python
async def get_supplier_alerts( severity: Optional[str] = Query(None, description="Filtrer par sévérité: info, warning, critical"),
```

**Description**: Alertes sur les scores fournisseurs dégradés.

- **Ligne**: 654
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/alerts')`
- **Paramètres**:
  - `severity`: `Optional[str]` = `Query(None, description='Filtrer par sévérité: info, warning, critical')`
  - `acknowledged`: `Optional[bool]` = `Query(None, description="Filtrer par état d'acquittement")`
  - `limit`: `int` = `Query(50, ge=1, le=200, description="Nombre maximum d'alertes")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 34 autres*

#### 🔸 `async acknowledge_supplier_alert`

```python
async def acknowledge_supplier_alert( alert_id: str = Path(..., description="ID de l'alerte à acquitter"),
```

**Description**: Acquitter une alerte fournisseur.

- **Ligne**: 760
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.post('/alerts/{alert_id}/acknowledge')`
- **Paramètres**:
  - `alert_id`: `str` = `Path(..., description="ID de l'alerte à acquitter")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async recalculate_supplier_scores`

```python
async def recalculate_supplier_scores( request: RecalculateScoresRequest,
```

**Description**: Recalculer tous les scores fournisseurs.

- **Ligne**: 803
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.post('/recalculate')`
- **Paramètres**:
  - `request`: `RecalculateScoresRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 34 autres*

#### 🔸 `async get_supplier_score_legacy`

```python
async def get_supplier_score_legacy( supplier_name: str,
```

**Description**: [LEGACY] Calcule et retourne le score complet d'un fournisseur.

- **Ligne**: 883
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/score/{supplier_name}')`
- **Paramètres**:
  - `supplier_name`: `str`
  - `period_days`: `int` = `Query(90, ge=7, le=365, description="Période d'analyse en jours")`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async get_suppliers_ranking_legacy`

```python
async def get_suppliers_ranking_legacy( tenant: Tenant = Depends(get_current_tenant_or_default),
```

**Description**: [LEGACY] Retourne le classement de tous les fournisseurs.

- **Ligne**: 921
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/ranking')`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async compare_suppliers`

```python
async def compare_suppliers( request: SupplierComparisonRequest,
```

**Description**: Compare plusieurs fournisseurs sur toutes les dimensions.

- **Ligne**: 944
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.post('/compare')`
- **Paramètres**:
  - `request`: `SupplierComparisonRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 35 autres*

#### 🔸 `async record_delivery`

```python
async def record_delivery( request: DeliveryRecordRequest,
```

**Description**: Enregistre une livraison pour le suivi de ponctualité.

- **Ligne**: 1000
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.post('/delivery')`
- **Paramètres**:
  - `request`: `DeliveryRecordRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async record_invoice_issue`

```python
async def record_invoice_issue( request: InvoiceIssueRequest,
```

**Description**: Enregistre un problème de facture.

- **Ligne**: 1043
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.post('/issue')`
- **Paramètres**:
  - `request`: `InvoiceIssueRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async list_dimensions`

```python
async def list_dimensions() -> Dict[str, Any]:
```

**Description**: [LEGACY] Liste les dimensions de scoring avec leurs poids.

- **Ligne**: 1082
- **Réutilisabilité**: Low
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/dimensions')`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

#### 🔸 `async get_supplier_history_by_name`

```python
async def get_supplier_history_by_name( supplier_name: str,
```

**Description**: [LEGACY] Retourne l'historique des scores d'un fournisseur par nom.

- **Ligne**: 1145
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Décorateurs**: `router.get('/history/{supplier_name}')`
- **Paramètres**:
  - `supplier_name`: `str`
  - `limit`: `int` = `Query(20, ge=1, le=100)`
  - `tenant`: `Tenant` = `Depends(get_current_tenant_or_default)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.dependencies.tenant.get_current_tenant_or_default`
  - `backend.middleware.response_wrapper.build_error_response`
  - `backend.middleware.response_wrapper.build_success_response`
  - *... et 33 autres*

### `backend/api/supply.py`

#### 🔸 `get_supply_plan`

```python
def get_supply_plan( target_coverage: int = Query(21, ge=1, le=120, description="Nombre de jours de stock visés."),
```

**Description**: Expose the dynamic supply planning data structure.

- **Ligne**: 18
- **Réutilisabilité**: Medium
- **Décorateurs**: `router.get('/plan', response_model=SupplyPlanResponseSchema)`
- **Paramètres**:
  - `target_coverage`: `int` = `Query(21, ge=1, le=120, description='Nombre de jours de stock visés.')`
  - `alert_threshold`: `int` = `Query(7, ge=1, le=120, description='Seuil d’alerte en jours.')`
  - `min_daily_sales`: `float` = `Query(0.0, ge=0, le=100, description='Filtre sur les ventes quotidiennes minimales.')`
  - `categories`: `Optional[List[str]]` = `Query(default=None, description='Liste optionnelle de catégories à inclure (répéter le paramètre).')`
  - `search`: `Optional[str]` = `Query(default=None, max_length=120, description='Terme de recherche appliqué côté serveur.')`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.schemas.supply.SupplyPlanResponseSchema`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - *... et 3 autres*

### `backend/main.py`

#### 🔸 `performance_metrics`

```python
def performance_metrics():
```

**Description**: Retourne les statistiques de performance des endpoints.

- **Ligne**: 384
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.get('/metrics/performance', dependencies=_security_dependencies())`
- **Dépendances**:
  - `backend.middleware.ResponseWrapperMiddleware`
  - `backend.middleware.get_performance_stats`

### `backend/tests/conftest.py`

#### 🔸 `client`

```python
def client() -> TestClient:
```

**Description**: Crée une instance TestClient pour l'app FastAPI.

- **Ligne**: 18
- **Réutilisabilité**: High
- **Type de retour**: `TestClient`
- **Décorateurs**: `pytest.fixture`
- **Dépendances**:
  - `fastapi.testclient.TestClient`
  - `pytest`

---

## Finance

**265 fonctions**

### `backend/schemas/finance.py`

#### 🔹 `_validate_direction` 🎀

```python
def _validate_direction(cls, value: str) -> str:
```

- **Ligne**: 147
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Décorateurs**: `field_validator('direction')`
- **Paramètres**:
  - `cls`
  - `value`: `str`
- **Dépendances**:
  - `pydantic.field_validator`

#### 🔹 `_validate_currency` 🎀

```python
def _validate_currency(cls, value: str) -> str:
```

- **Ligne**: 155
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Décorateurs**: `field_validator('currency')`
- **Paramètres**:
  - `cls`
  - `value`: `str`
- **Dépendances**:
  - `pydantic.field_validator`

### `backend/services/finance/accounts.py`

#### 🔸 `create_account`

```python
def create_account(payload: FinanceAccountCreate) -> dict[str, Any]:
```

**Description**: Crée un compte financier en validant la cohérence devise/entité.

- **Ligne**: 24
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `FinanceAccountCreate`
- **Dépendances**:
  - `backend.schemas.finance.FinanceAccountCreate`
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_accounts`

```python
def list_accounts(entity_id: Optional[int] = None, is_active: Optional[bool] = None) -> list[dict[str, Any]]:
```

**Description**: Liste les comptes avec filtres simples.

- **Ligne**: 69
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `entity_id`: `Optional[int]` = `None`
  - `is_active`: `Optional[bool]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Optional`

#### 🔸 `get_account`

```python
def get_account(account_id: int) -> dict[str, Any] | None:
```

**Description**: Récupère un compte par son ID.

- **Ligne**: 101
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any] | None`
- **Paramètres**:
  - `account_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_account` 🎀

```python
def update_account(account_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Met à jour un compte financier.

- **Ligne**: 118
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `account_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `delete_account`

```python
def delete_account(account_id: int) -> bool:
```

**Description**: Supprime un compte financier (soft delete via is_active=false, ou hard delete si pas de données).

- **Ligne**: 152
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `account_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/finance/bank_statements.py`

#### 🔸 `search_bank_statements`

```python
def search_bank_statements( *, account_id: Optional[int] = None,
```

**Description**: Recherche paginée sur les relevés bancaires.

- **Ligne**: 12
- **Réutilisabilité**: Low
- **Type de retour**: `Dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

### `backend/services/finance/categories.py`

#### 🔸 `create_category`

```python
def create_category(entity_id: int, code: str, name: str, type_: str = "EXPENSE") -> dict:
```

**Description**: Crée une nouvelle catégorie finance et la retourne.

- **Ligne**: 12
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `entity_id`: `int`
  - `code`: `str`
  - `name`: `str`
  - `type_`: `str` = `'EXPENSE'`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔸 `list_categories`

```python
def list_categories(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
```

**Description**: Retourne les catégories finance disponibles, optionnellement filtrées.

- **Ligne**: 30
- **Réutilisabilité**: High
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
  - `is_active`: `bool | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

### `backend/services/finance/core.py`

#### 🔸 `run_reconciliation`

```python
def run_reconciliation( tenant_id: int,
```

**Description**: Lance le job de rapprochement en configurant les marges de tolérance.

- **Ligne**: 11
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `list_matches`

```python
def list_matches(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
```

**Description**: Expose les correspondances relevés/factures générées par le job de rapprochement.

- **Ligne**: 28
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `status`: `str | None` = `None`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `update_match_status`

```python
def update_match_status(tenant_id: int, match_id: int, *, status: str, note: str | None = None) -> dict[str, Any]:
```

**Description**: Met à jour le statut manuel d'une correspondance (validée, rejetée...).

- **Ligne**: 34
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `match_id`: `int`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `refresh_recurring`

```python
def refresh_recurring(tenant_id: int, *, min_occurrences: int = 3) -> dict[str, Any]:
```

**Description**: Recalcule les dépenses récurrentes à partir des relevés existants.

- **Ligne**: 40
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `list_recurring`

```python
def list_recurring(tenant_id: int) -> list[dict[str, Any]]:
```

**Description**: Retourne les dépenses identifiées comme récurrentes.

- **Ligne**: 46
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `refresh_anomalies`

```python
def refresh_anomalies(tenant_id: int, *, zscore_threshold: float = 2.5, min_occurrences: int = 3) -> dict[str, Any]:
```

**Description**: Marque les anomalies de dépenses via détection statistique (z-score).

- **Ligne**: 52
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `list_anomalies`

```python
def list_anomalies(tenant_id: int, severity: str | None = None) -> list[dict[str, Any]]:
```

**Description**: Liste les anomalies référencées en base, filtrables par sévérité.

- **Ligne**: 62
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `severity`: `str | None` = `None`
- **Dépendances**:
  - `typing.Any`

### `backend/services/finance/cost_centers.py`

#### 🔸 `create_cost_center`

```python
def create_cost_center(entity_id: int, code: str, name: str) -> dict:
```

**Description**: Crée un nouveau centre de coûts finance et le retourne.

- **Ligne**: 12
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `entity_id`: `int`
  - `code`: `str`
  - `name`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔸 `list_cost_centers`

```python
def list_cost_centers(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
```

**Description**: Retourne les centres de coûts finance disponibles, optionnellement filtrés.

- **Ligne**: 30
- **Réutilisabilité**: High
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
  - `is_active`: `bool | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

### `backend/services/finance/dashboard.py`

#### 🔸 `dashboard_summary`

```python
def dashboard_summary(entity_id: int | None = None) -> Dict[str, Any]:
```

- **Ligne**: 12
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

### `backend/services/finance/dedupe.py`

#### 🔸 `dedupe_transactions`

```python
def dedupe_transactions() -> Dict[str, List[int]]:
```

**Description**: Supprime les doublons finance_transactions (date_operation+amount) en gardant le plus petit id.

- **Ligne**: 8
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, List[int]]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `dedupe_statement_lines`

```python
def dedupe_statement_lines() -> Dict[str, List[int]]:
```

**Description**: Supprime les doublons finance_bank_statement_lines (date_operation+montant) en gardant le plus petit id.

- **Ligne**: 32
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, List[int]]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Dict`
  - `typing.List`

### `backend/services/finance/imports.py`

#### 🔸 `list_imports`

```python
def list_imports() -> List[dict]:
```

- **Ligne**: 12
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔸 `update_import_progress`

```python
def update_import_progress(import_id: int, inserted: int, total: int | None = None, status: str | None = None) -> None:
```

- **Ligne**: 38
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `import_id`: `int`
  - `inserted`: `int`
  - `total`: `int | None` = `None`
  - `status`: `str | None` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/finance/invoices.py`

#### 🔸 `create_vendor`

```python
def create_vendor(payload: FinanceVendorCreate) -> dict[str, Any]:
```

- **Ligne**: 13
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `FinanceVendorCreate`
- **Dépendances**:
  - `backend.schemas.finance.FinanceVendorCreate`
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_vendors`

```python
def list_vendors(entity_id: Optional[int] = None, is_active: Optional[bool] = None) -> list[dict[str, Any]]:
```

- **Ligne**: 48
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `entity_id`: `Optional[int]` = `None`
  - `is_active`: `Optional[bool]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Optional`

#### 🔸 `create_invoice`

```python
def create_invoice(payload: FinanceInvoiceCreate) -> dict[str, Any]:
```

- **Ligne**: 89
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `FinanceInvoiceCreate`
- **Dépendances**:
  - `backend.schemas.finance.FinanceInvoiceCreate`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `create_payment`

```python
def create_payment(payload: FinancePaymentCreate) -> dict[str, Any]:
```

- **Ligne**: 201
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `FinancePaymentCreate`
- **Dépendances**:
  - `backend.schemas.finance.FinancePaymentCreate`
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `search_invoices`

```python
def search_invoices( *, entity_id: Optional[int] = None,
```

**Description**: Recherche paginée sur les factures fournisseurs.

- **Ligne**: 228
- **Réutilisabilité**: Low
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Optional`

### `backend/services/finance/metrics.py`

#### 🔸 `record_reco_run`

```python
def record_reco_run(summary: Dict[str, Any]) -> None:
```

- **Ligne**: 15
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `summary`: `Dict[str, Any]`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

#### 🔸 `record_import_metrics`

```python
def record_import_metrics(account_id: int, inserted: int | None, total: int | None, status: str, error: str | None) -> None:
```

- **Ligne**: 19
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `account_id`: `int`
  - `inserted`: `int | None`
  - `total`: `int | None`
  - `status`: `str`
  - `error`: `str | None`

#### 🔸 `increment_import_progress`

```python
def increment_import_progress(import_id: int, inserted: int, total: int) -> None:
```

- **Ligne**: 23
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `import_id`: `int`
  - `inserted`: `int`
  - `total`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/finance/reconciliation.py`

#### 🔸 `create_reconciliation`

```python
def create_reconciliation( statement_line_id: int,
```

- **Ligne**: 12
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `statement_line_id`: `int`
  - `transaction_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `delete_reconciliation`

```python
def delete_reconciliation(reconciliation_id: int) -> None:
```

- **Ligne**: 46
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `reconciliation_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/finance/rules.py`

#### 🔸 `list_rules`

```python
def list_rules(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
```

**Description**: Liste les règles de catégorisation.

- **Ligne**: 13
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
  - `is_active`: `bool | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `create_rule`

```python
def create_rule(payload: FinanceRuleCreate) -> dict:
```

- **Ligne**: 66
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `payload`: `FinanceRuleCreate`
- **Dépendances**:
  - `backend.schemas.finance_rules.FinanceRuleCreate`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔸 `update_rule`

```python
def update_rule(rule_id: int, fields: Dict[str, Any]) -> dict:
```

- **Ligne**: 92
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `rule_id`: `int`
  - `fields`: `Dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

#### 🔸 `delete_rule`

```python
def delete_rule(rule_id: int) -> dict:
```

- **Ligne**: 118
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `rule_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔸 `record_import`

```python
def record_import(account_id: int, file_name: str, summary: dict | None, error: str | None) -> None:
```

**Description**: Enregistre un import (succès/échec) dans finance_imports.

- **Ligne**: 132
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `account_id`: `int`
  - `file_name`: `str`
  - `summary`: `dict | None`
  - `error`: `str | None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/finance/stats.py`

#### 🔸 `categories_stats`

```python
def categories_stats(entity_id: int | None = None) -> List[dict]:
```

**Description**: Retourne les stats par catégorie (inflow/outflow/count).

- **Ligne**: 27
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `accounts_overview` 🎀

```python
def accounts_overview(entity_id: int | None = None) -> List[dict]:
```

**Description**: Retourne un aperçu de chaque compte (inflow/outflow/balance/match_rate).

- **Ligne**: 93
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔸 `refresh_materialized_views`

```python
def refresh_materialized_views() -> dict:
```

**Description**: Rafraîchit les vues matérialisées de stats finance.

- **Ligne**: 163
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.query_df`

#### 🔸 `timeline_stats` 🎀

```python
def timeline_stats( entity_id: int | None = None,
```

**Description**: Retourne la chronologie agrégée des flux (inflow/outflow) par période.

- **Ligne**: 181
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
  - `months`: `int | None` = `12`
  - `granularity`: `str` = `'monthly'`
  - `account_id`: `int | None` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.finance.views.refresh_materialized_views`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 2 autres*

#### 🔸 `category_breakdown` 🎀

```python
def category_breakdown( entity_id: int | None = None,
```

**Description**: Retourne la répartition par catégorie pour les graphiques (pie/bar charts).

- **Ligne**: 300
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
  - `months`: `int | None` = `12`
  - `direction`: `str | None` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.finance.views.refresh_materialized_views`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 2 autres*

#### 🔸 `treasury_summary`

```python
def treasury_summary(entity_id: int | None = None) -> dict:
```

**Description**: Retourne un résumé de trésorerie: totaux, solde, alertes.

- **Ligne**: 410
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `top_vendors`

```python
def top_vendors( entity_id: int | None = None,
```

**Description**: Retourne les principaux fournisseurs par montant.

- **Ligne**: 463
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
  - `months`: `int | None` = `12`
  - `limit`: `int` = `20`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `import_summary`

```python
def import_summary( account_id: int | None = None,
```

**Description**: Retourne le résumé des importations par compte et période.

- **Ligne**: 516
- **Réutilisabilité**: High
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `account_id`: `int | None` = `None`
  - `months`: `int | None` = `12`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `reconciliation_dashboard`

```python
def reconciliation_dashboard(entity_id: int | None = None) -> List[dict]:
```

**Description**: Retourne le dashboard de rapprochement par compte.

- **Ligne**: 566
- **Réutilisabilité**: High
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `entity_id`: `int | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

### `backend/services/finance/transaction_lines.py`

#### 🔸 `mark_incomplete`

```python
def mark_incomplete(transaction_ids: Iterable[int]) -> Dict[str, Any]:
```

**Description**: Crée des lignes par défaut et marque les transactions comme incompletes via data_quality_flags.

- **Ligne**: 9
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `transaction_ids`: `Iterable[int]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.finance.transaction_line_defaults.fill_missing_transaction_lines`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

### `backend/services/finance/transactions.py`

#### 🔸 `create_transaction`

```python
def create_transaction(payload: FinanceTransactionCreate) -> dict[str, Any]:
```

**Description**: Crée une transaction et ses lignes dans une transaction DB unique.

- **Ligne**: 27
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `FinanceTransactionCreate`
- **Dépendances**:
  - `backend.schemas.finance.FinanceTransactionCreate`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_transactions`

```python
def list_transactions( *, entity_id: Optional[int] = None,
```

**Description**: Filtre basique des transactions pour l'API.

- **Ligne**: 137
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Optional`

#### 🔸 `update_transaction`

```python
def update_transaction(transaction_id: int, payload: FinanceTransactionUpdate) -> dict[str, Any]:
```

**Description**: Mise à jour note/statut si la transaction n'est pas verrouillée.

- **Ligne**: 194
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `transaction_id`: `int`
  - `payload`: `FinanceTransactionUpdate`
- **Dépendances**:
  - `backend.schemas.finance.FinanceTransactionUpdate`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `lock_transaction`

```python
def lock_transaction(transaction_id: int) -> dict[str, Any]:
```

**Description**: Verrouille une transaction après rapprochement.

- **Ligne**: 227
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `transaction_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `search_transactions`

```python
def search_transactions( *, entity_id: Optional[int] = None,
```

**Description**: Recherche paginée sur les lignes de transaction (avec catégorie et libellé).

- **Ligne**: 251
- **Réutilisabilité**: Low
- **Type de retour**: `FinanceTransactionSearchResponse`
- **Dépendances**:
  - `backend.schemas.finance.FinanceBatchCategorizeRequest`
  - `backend.schemas.finance.FinanceTransactionSearchResponse`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 2 autres*

#### 🔸 `batch_categorize`

```python
def batch_categorize(payload: FinanceBatchCategorizeRequest) -> Dict[str, Any]:
```

**Description**: Applique une catégorie à une liste d'IDs ou à un motif (keywords).

- **Ligne**: 401
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `payload`: `FinanceBatchCategorizeRequest`
- **Dépendances**:
  - `backend.schemas.finance.FinanceBatchCategorizeRequest`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔸 `suggest_autre_top` 🎀

```python
def suggest_autre_top(entity_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
```

**Description**: Retourne les libellés fréquents restés en fourre-tout (ici frais_generaux).

- **Ligne**: 457
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `entity_id`: `Optional[int]` = `None`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - *... et 1 autres*

#### 🔸 `autocomplete_categories`

```python
def autocomplete_categories(q: str, entity_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
```

**Description**: Autocomplete sur les catégories (code/nom).

- **Ligne**: 500
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `q`: `str`
  - `entity_id`: `Optional[int]` = `None`
  - `limit`: `int` = `20`
- **Dépendances**:
  - `backend.schemas.finance.FinanceBatchCategorizeRequest`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 2 autres*

### `backend/services/finance/views.py`

#### 🔸 `refresh_materialized_views` 🎀

```python
def refresh_materialized_views(concurrent: bool = True) -> List[RefreshResult]:
```

**Description**: Rafraîchit toutes les vues matérialisées.

- **Ligne**: 38
- **Réutilisabilité**: Medium
- **Type de retour**: `List[RefreshResult]`
- **Paramètres**:
  - `concurrent`: `bool` = `True`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `datetime.datetime`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `refresh_single_view`

```python
def refresh_single_view(view_name: str, concurrent: bool = True) -> RefreshResult:
```

**Description**: Rafraîchit une seule vue matérialisée.

- **Ligne**: 80
- **Réutilisabilité**: High
- **Type de retour**: `RefreshResult`
- **Paramètres**:
  - `view_name`: `str`
  - `concurrent`: `bool` = `True`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `datetime.datetime`
  - `sqlalchemy.text`

#### 🔸 `get_view_status` 🎀

```python
def get_view_status() -> dict:
```

**Description**: Récupère le statut de chaque vue matérialisée.

- **Ligne**: 125
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `datetime.datetime`
  - `sqlalchemy.text`

### `backend/services/finance_categorization.py`

#### 🔸 `strip_accents`

```python
def strip_accents(text: str) -> str:
```

**Description**: Supprime les accents d'une chaine.

- **Ligne**: 324
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `text`: `str`
- **Dépendances**:
  - `typing.Dict`
  - `unicodedata`

#### 🔸 `normalize_label` 🎀

```python
def normalize_label(label: str) -> str:
```

**Description**: Normalisation legere : upper + espaces condenses.

- **Ligne**: 332
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `label`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `re`

#### 🔸 `stem_label` 🎀

```python
def stem_label(label: str) -> str:
```

**Description**: Forme tronquee pour regrouper les variantes (dates, montants, refs numeriques).

- **Ligne**: 339
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `label`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `re`

#### 🔸 `canonical`

```python
def canonical(label: str) -> str:
```

**Description**: Forme canonique pour regrouper des libelles similaires.

- **Ligne**: 352
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `label`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `re`

#### 🔸 `match_category_rules` 🎀

```python
def match_category_rules( direction: str,
```

**Description**: Applique les regles de categorisation sur un libelle.

- **Ligne**: 377
- **Réutilisabilité**: High
- **Type de retour**: `Optional[str]`
- **Paramètres**:
  - `direction`: `str`
  - `label`: `str`
  - `rules`: `Tuple[Tuple[Tuple[str, ...], str, Tuple[str, ...] | None], ...]` = `BASE_CATEGORY_RULES`
- **Dépendances**:
  - `typing.Optional`
  - `typing.Tuple`

#### 🔸 `infer_target_category`

```python
def infer_target_category(category_name: str, entry_type: str = "Sortie") -> str:
```

**Description**: Infere la categorie cible (taxonomie 12 postes) a partir d'un nom de categorie source.

- **Ligne**: 406
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `category_name`: `str`
  - `entry_type`: `str` = `'Sortie'`

#### 🔸 `auto_categorize`

```python
def auto_categorize(direction: str, label: str) -> Tuple[Optional[str], str]:
```

**Description**: Categorise automatiquement une transaction.

- **Ligne**: 459
- **Réutilisabilité**: High
- **Type de retour**: `Tuple[Optional[str], str]`
- **Paramètres**:
  - `direction`: `str`
  - `label`: `str`
- **Dépendances**:
  - `typing.Optional`
  - `typing.Tuple`

#### 🔸 `suggest_category` 🎀

```python
def suggest_category(label: str) -> Optional[str]:
```

**Description**: Suggere une categorie basee sur les mots-cles simples.

- **Ligne**: 506
- **Réutilisabilité**: High
- **Type de retour**: `Optional[str]`
- **Paramètres**:
  - `label`: `str`
- **Dépendances**:
  - `typing.Optional`

### `core/finance/analytic_accounting.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 76
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Dict`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 81
- **Réutilisabilité**: Low
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `create_axis`

```python
def create_axis( self, axis_type: AxisType,
```

**Description**: Crée un nouvel axe analytique.

- **Ligne**: 145
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `axis_type`: `AxisType`
  - `code`: `str`
  - `name`: `str`
  - `parent_id`: `Optional[int]` = `None`
  - `metadata`: `Dict` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Dict`
  - `typing.Optional`

#### 🔹 `get_axes`

```python
def get_axes(self, axis_type: Optional[AxisType] = None) -> List[AnalyticAxis]:
```

**Description**: Récupère les axes analytiques.

- **Ligne**: 179
- **Réutilisabilité**: Medium
- **Type de retour**: `List[AnalyticAxis]`
- **Paramètres**:
  - `self`
  - `axis_type`: `Optional[AxisType]` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `assign_expense`

```python
def assign_expense( self, source_type: str,
```

**Description**: Affecte une dépense sur plusieurs axes.

- **Ligne**: 211
- **Réutilisabilité**: Low
- **Paramètres**:
  - `self`
  - `source_type`: `str`
  - `source_id`: `int`
  - `total_amount`: `float`
  - `assignments`: `List[Tuple[int, float]]`
  - `assignment_date`: `date` = `None`
  - `auto`: `bool` = `False`
  - `user`: `str` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 7 autres*

#### 🔹 `auto_assign`

```python
def auto_assign( self, source_type: str,
```

**Description**: Affecte automatiquement selon les règles définies.

- **Ligne**: 272
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `source_type`: `str`
  - `source_id`: `int`
  - `total_amount`: `float`
  - `context`: `Dict[str, Any]`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 8 autres*

#### 🔹 `_match_conditions`

```python
def _match_conditions(self, conditions: Dict, context: Dict) -> bool:
```

**Description**: Vérifie si les conditions sont remplies.

- **Ligne**: 316
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `conditions`: `Dict`
  - `context`: `Dict`
- **Dépendances**:
  - `typing.Dict`

#### 🔹 `_get_default_axis`

```python
def _get_default_axis(self, context: Dict) -> Optional[int]:
```

**Description**: Retourne l'axe par défaut selon le contexte.

- **Ligne**: 339
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[int]`
- **Paramètres**:
  - `self`
  - `context`: `Dict`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Dict`
  - `typing.Optional`

#### 🔹 `get_report`

```python
def get_report( self, axis_type: AxisType,
```

**Description**: Génère un rapport analytique.

- **Ligne**: 363
- **Réutilisabilité**: Medium
- **Type de retour**: `AnalyticReport`
- **Paramètres**:
  - `self`
  - `axis_type`: `AxisType`
  - `period_start`: `date`
  - `period_end`: `date`
  - `compare_with_budget`: `bool` = `True`
  - `compare_with_previous`: `bool` = `True`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 8 autres*

#### 🔹 `_get_budget`

```python
def _get_budget(self, axis_id: int, period_start: date, period_end: date) -> Optional[float]:
```

**Description**: Récupère le budget pour un axe et une période.

- **Ligne**: 455
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[float]`
- **Paramètres**:
  - `self`
  - `axis_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔹 `_get_period_amount`

```python
def _get_period_amount(self, axis_id: int, period_start: date, period_end: date) -> float:
```

**Description**: Récupère le montant total pour un axe et une période.

- **Ligne**: 482
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `axis_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `set_budget`

```python
def set_budget( self, axis_id: int,
```

**Description**: Définit le budget pour un axe.

- **Ligne**: 504
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `axis_id`: `int`
  - `year`: `int`
  - `amount`: `float`
  - `month`: `Optional[int]` = `None`
  - `notes`: `str` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔹 `create_rule`

```python
def create_rule( self, name: str,
```

**Description**: Crée une règle d'affectation automatique.

- **Ligne**: 533
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `name`: `str`
  - `conditions`: `Dict[str, Any]`
  - `assignments`: `List[Dict[str, Any]]`
  - `priority`: `int` = `0`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `get_cross_analysis`

```python
def get_cross_analysis( self, axis_type_1: AxisType,
```

**Description**: Analyse croisée entre deux axes.

- **Ligne**: 561
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `axis_type_1`: `AxisType`
  - `axis_type_2`: `AxisType`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔹 `get_top_expenses_by_axis`

```python
def get_top_expenses_by_axis( self, axis_id: int,
```

**Description**: Top des dépenses pour un axe donné.

- **Ligne**: 615
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `axis_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
  - `limit`: `int` = `10`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - *... et 3 autres*

#### 🔸 `bootstrap_default_axes`

```python
def bootstrap_default_axes(tenant_id: int):
```

**Description**: Initialise les axes par défaut.

- **Ligne**: 663
- **Réutilisabilité**: High
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`

### `core/finance/anomaly_detection.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 81
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Dict`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 86
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `detect_all` 🎀

```python
def detect_all( self, transactions: Optional[List[Dict]] = None,
```

**Description**: Lance toutes les détections.

- **Ligne**: 120
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `transactions`: `Optional[List[Dict]]` = `None`
  - `invoices`: `Optional[List[Dict]]` = `None`
  - `period_days`: `int` = `30`
- **Dépendances**:
  - `typing.Dict`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `detect_transaction_anomalies` 🎀

```python
def detect_transaction_anomalies( self, transactions: List[Dict[str, Any]]
```

**Description**: Détecte les anomalies dans les transactions.

- **Ligne**: 144
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `transactions`: `List[Dict[str, Any]]`
- **Dépendances**:
  - `collections.defaultdict`
  - `statistics.mean`
  - `statistics.median`
  - `statistics.stdev`
  - `typing.Any`
  - *... et 2 autres*

#### 🔹 `detect_invoice_anomalies` 🎀

```python
def detect_invoice_anomalies( self, invoices: List[Dict[str, Any]]
```

**Description**: Détecte les anomalies dans les factures.

- **Ligne**: 207
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `invoices`: `List[Dict[str, Any]]`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `detect_from_history` 🎀

```python
def detect_from_history(self, period_days: int = 30) -> List[DetectedAnomaly]:
```

**Description**: Détecte les anomalies basées sur l'historique DB.

- **Ligne**: 236
- **Réutilisabilité**: High
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `period_days`: `int` = `30`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.List`

#### 🔹 `_create_amount_outlier_anomaly`

```python
def _create_amount_outlier_anomaly( self, tx: Dict,
```

**Description**: Crée une anomalie de montant anormal.

- **Ligne**: 252
- **Réutilisabilité**: Medium
- **Type de retour**: `DetectedAnomaly`
- **Paramètres**:
  - `self`
  - `tx`: `Dict`
  - `z_score`: `float`
  - `stats`: `Dict`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`

#### 🔹 `_create_round_amount_anomaly`

```python
def _create_round_amount_anomaly( self, tx: Dict,
```

**Description**: Crée une anomalie de montant rond suspect.

- **Ligne**: 287
- **Réutilisabilité**: Medium
- **Type de retour**: `DetectedAnomaly`
- **Paramètres**:
  - `self`
  - `tx`: `Dict`
  - `amount`: `float`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`

#### 🔹 `_create_unusual_time_anomaly`

```python
def _create_unusual_time_anomaly( self, tx: Dict,
```

**Description**: Crée une anomalie d'horaire inhabituel.

- **Ligne**: 311
- **Réutilisabilité**: Medium
- **Type de retour**: `DetectedAnomaly`
- **Paramètres**:
  - `self`
  - `tx`: `Dict`
  - `tx_date`: `Any`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `_create_duplicate_invoice_anomaly`

```python
def _create_duplicate_invoice_anomaly( self, inv: Dict,
```

**Description**: Crée une anomalie de facture dupliquée.

- **Ligne**: 338
- **Réutilisabilité**: Medium
- **Type de retour**: `DetectedAnomaly`
- **Paramètres**:
  - `self`
  - `inv`: `Dict`
  - `original`: `Dict`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`

#### 🔹 `_is_suspicious_round_amount`

```python
def _is_suspicious_round_amount(self, amount: float) -> bool:
```

**Description**: Vérifie si un montant est suspecteusement rond.

- **Ligne**: 364
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `amount`: `float`

#### 🔹 `_is_unusual_time`

```python
def _is_unusual_time(self, tx_date: Any) -> bool:
```

**Description**: Vérifie si l'heure est inhabituelle.

- **Ligne**: 377
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `tx_date`: `Any`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Any`

#### 🔹 `_detect_duplicate_transactions` 🎀

```python
def _detect_duplicate_transactions( self, transactions: List[Dict]
```

**Description**: Détecte les transactions dupliquées.

- **Ligne**: 391
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `transactions`: `List[Dict]`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_detect_velocity_spike`

```python
def _detect_velocity_spike( self, transactions: List[Dict]
```

**Description**: Détecte un pic soudain de transactions.

- **Ligne**: 433
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `transactions`: `List[Dict]`
- **Dépendances**:
  - `collections.defaultdict`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `statistics.mean`
  - `statistics.stdev`
  - *... et 3 autres*

#### 🔹 `_compute_invoice_signature`

```python
def _compute_invoice_signature(self, inv: Dict) -> str:
```

**Description**: Calcule une signature unique pour détecter les doublons.

- **Ligne**: 483
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `inv`: `Dict`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`

#### 🔹 `_detect_price_discrepancies` 🎀

```python
def _detect_price_discrepancies(self, inv: Dict) -> List[DetectedAnomaly]:
```

**Description**: Détecte les écarts de prix par rapport aux attendus.

- **Ligne**: 491
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `inv`: `Dict`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `_detect_sequence_gaps` 🎀

```python
def _detect_sequence_gaps(self, invoices: List[Dict]) -> List[DetectedAnomaly]:
```

**Description**: Détecte les trous dans les séquences de numéros de facture.

- **Ligne**: 545
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `invoices`: `List[Dict]`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.datetime`
  - *... et 11 autres*

#### 🔹 `_detect_missing_bank_transactions` 🎀

```python
def _detect_missing_bank_transactions(self, since: datetime) -> List[DetectedAnomaly]:
```

**Description**: Détecte les factures sans transaction bancaire correspondante.

- **Ligne**: 597
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `_detect_missing_invoices` 🎀

```python
def _detect_missing_invoices(self, since: datetime) -> List[DetectedAnomaly]:
```

**Description**: Détecte les transactions sans facture correspondante.

- **Ligne**: 656
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `_detect_frequency_changes` 🎀

```python
def _detect_frequency_changes(self, since: datetime) -> List[DetectedAnomaly]:
```

**Description**: Détecte les changements de fréquence inhabituels.

- **Ligne**: 713
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DetectedAnomaly]`
- **Paramètres**:
  - `self`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `_dates_are_close`

```python
def _dates_are_close(self, date1: Any, date2: Any, days: int) -> bool:
```

**Description**: Vérifie si deux dates sont proches.

- **Ligne**: 781
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `date1`: `Any`
  - `date2`: `Any`
  - `days`: `int`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Any`

#### 🔹 `_save_anomaly`

```python
def _save_anomaly(self, anomaly: DetectedAnomaly):
```

**Description**: Sauvegarde une anomalie en base.

- **Ligne**: 798
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `anomaly`: `DetectedAnomaly`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`

#### 🔹 `get_unresolved_anomalies`

```python
def get_unresolved_anomalies( self, severity: Optional[Severity] = None,
```

**Description**: Récupère les anomalies non résolues.

- **Ligne**: 827
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `severity`: `Optional[Severity]` = `None`
  - `anomaly_type`: `Optional[AnomalyType]` = `None`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 3 autres*

#### 🔹 `resolve_anomaly`

```python
def resolve_anomaly( self, anomaly_id: str,
```

**Description**: Marque une anomalie comme résolue.

- **Ligne**: 874
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `anomaly_id`: `str`
  - `resolved_by`: `str`
  - `false_positive`: `bool` = `False`
  - `notes`: `Optional[str]` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Optional`

### `core/finance/audit_trail.py`

#### 🔹 `calculate_checksum`

```python
def calculate_checksum(self) -> str:
```

**Description**: Calcule un checksum pour garantir l'intégrité

- **Ligne**: 163
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `hashlib`
  - `json`

#### 🔹 `__init__`

```python
def __init__(self, db_pool=None, retention_days: int = 365):
```

- **Ligne**: 233
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `db_pool` = `None`
  - `retention_days`: `int` = `365`
- **Dépendances**:
  - `typing.List`

#### 🔹 `async log` 🎀

```python
async def log( self, action: AuditAction,
```

**Description**: Enregistre une entrée d'audit

- **Ligne**: 247
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `action`: `AuditAction`
  - `entity`: `AuditEntity`
  - `entity_id`: `Optional[int]` = `None`
  - `entity_name`: `Optional[str]` = `None`
  - `context`: `Optional[AuditContext]` = `None`
  - `before_state`: `Optional[Dict[str, Any]]` = `None`
  - `after_state`: `Optional[Dict[str, Any]]` = `None`
  - `description`: `Optional[str]` = `None`
  - `metadata`: `Optional[Dict[str, Any]]` = `None`
  - `severity`: `AuditSeverity` = `AuditSeverity.INFO`
  - `tags`: `Optional[List[str]]` = `None`
  - `parent_audit_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - *... et 1 autres*

#### 🔹 `async log_create`

```python
async def log_create( self, entity: AuditEntity,
```

**Description**: Shortcut pour création

- **Ligne**: 308
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `entity`: `AuditEntity`
  - `entity_id`: `int`
  - `data`: `Dict[str, Any]`
  - `context`: `AuditContext`
  - `entity_name`: `Optional[str]` = `None`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `async log_update`

```python
async def log_update( self, entity: AuditEntity,
```

**Description**: Shortcut pour mise à jour

- **Ligne**: 327
- **Réutilisabilité**: High
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `entity`: `AuditEntity`
  - `entity_id`: `int`
  - `before`: `Dict[str, Any]`
  - `after`: `Dict[str, Any]`
  - `context`: `AuditContext`
  - `entity_name`: `Optional[str]` = `None`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

#### 🔹 `async log_delete`

```python
async def log_delete( self, entity: AuditEntity,
```

**Description**: Shortcut pour suppression

- **Ligne**: 348
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `entity`: `AuditEntity`
  - `entity_id`: `int`
  - `data`: `Dict[str, Any]`
  - `context`: `AuditContext`
  - `entity_name`: `Optional[str]` = `None`
  - `soft_delete`: `bool` = `False`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `async log_security_event`

```python
async def log_security_event( self, action: AuditAction,
```

**Description**: Log événement de sécurité

- **Ligne**: 370
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `action`: `AuditAction`
  - `context`: `AuditContext`
  - `description`: `str`
  - `success`: `bool` = `True`
  - `metadata`: `Optional[Dict[str, Any]]` = `None`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

#### 🔹 `async log_bulk_operation`

```python
async def log_bulk_operation( self, action: AuditAction,
```

**Description**: Log opération en masse

- **Ligne**: 392
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `action`: `AuditAction`
  - `entity`: `AuditEntity`
  - `entity_ids`: `List[int]`
  - `context`: `AuditContext`
  - `description`: `str`
  - `metadata`: `Optional[Dict[str, Any]]` = `None`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `_mask_sensitive` 🎀

```python
def _mask_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
```

**Description**: Masque les champs sensibles

- **Ligne**: 421
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `data`: `Dict[str, Any]`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `_calculate_diff` 🎀

```python
def _calculate_diff( self, before: Dict[str, Any],
```

**Description**: Calcule les différences entre deux états

- **Ligne**: 434
- **Réutilisabilité**: Medium
- **Type de retour**: `List[AuditDiff]`
- **Paramètres**:
  - `self`
  - `before`: `Dict[str, Any]`
  - `after`: `Dict[str, Any]`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_normalize_value`

```python
def _normalize_value(self, value: Any) -> str:
```

**Description**: Normalise une valeur pour comparaison

- **Ligne**: 461
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `value`: `Any`
- **Dépendances**:
  - `dataclasses.asdict`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `json`
  - *... et 1 autres*

#### 🔹 `_detect_type`

```python
def _detect_type(self, value: Any) -> str:
```

**Description**: Détecte le type d'une valeur

- **Ligne**: 473
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `value`: `Any`
- **Dépendances**:
  - `dataclasses.asdict`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `typing.Any`

#### 🔹 `async _persist_entry`

```python
async def _persist_entry(self, entry: AuditEntry) -> int:
```

**Description**: Persiste une entrée d'audit dans la base

- **Ligne**: 493
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `entry`: `AuditEntry`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 2 autres*

#### 🔹 `async search`

```python
async def search(self, criteria: AuditSearchCriteria) -> List[AuditEntry]:
```

**Description**: Recherche dans l'audit log

- **Ligne**: 548
- **Réutilisabilité**: Medium
- **Type de retour**: `List[AuditEntry]`
- **Paramètres**:
  - `self`
  - `criteria`: `AuditSearchCriteria`
- **Dépendances**:
  - `asyncio`
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - *... et 11 autres*

#### 🔹 `_search_buffer`

```python
def _search_buffer(self, criteria: AuditSearchCriteria) -> List[AuditEntry]:
```

**Description**: Recherche dans le buffer mémoire

- **Ligne**: 637
- **Réutilisabilité**: High
- **Type de retour**: `List[AuditEntry]`
- **Paramètres**:
  - `self`
  - `criteria`: `AuditSearchCriteria`
- **Dépendances**:
  - `typing.List`

#### 🔹 `_row_to_entry`

```python
def _row_to_entry(self, row: Dict[str, Any]) -> AuditEntry:
```

**Description**: Convertit une ligne DB en AuditEntry

- **Ligne**: 660
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditEntry`
- **Paramètres**:
  - `self`
  - `row`: `Dict[str, Any]`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 4 autres*

#### 🔹 `async generate_report`

```python
async def generate_report( self, tenant_id: int,
```

**Description**: Génère un rapport d'audit pour une période

- **Ligne**: 725
- **Réutilisabilité**: Medium
- **Type de retour**: `AuditReport`
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
  - `start_date`: `datetime`
  - `end_date`: `datetime`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`

#### 🔹 `async get_entity_history`

```python
async def get_entity_history( self, entity: AuditEntity,
```

**Description**: Récupère l'historique complet d'une entité

- **Ligne**: 825
- **Réutilisabilité**: High
- **Type de retour**: `List[AuditEntry]`
- **Paramètres**:
  - `self`
  - `entity`: `AuditEntity`
  - `entity_id`: `int`
  - `tenant_id`: `Optional[int]` = `None`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `typing.List`
  - `typing.Optional`

#### 🔹 `async get_user_activity`

```python
async def get_user_activity( self, user_id: int,
```

**Description**: Récupère l'activité d'un utilisateur

- **Ligne**: 841
- **Réutilisabilité**: High
- **Type de retour**: `List[AuditEntry]`
- **Paramètres**:
  - `self`
  - `user_id`: `int`
  - `tenant_id`: `Optional[int]` = `None`
  - `start_date`: `Optional[datetime]` = `None`
  - `limit`: `int` = `100`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `async purge_old_entries`

```python
async def purge_old_entries(self, before_date: Optional[datetime] = None):
```

**Description**: Purge les entrées anciennes selon la rétention

- **Ligne**: 861
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `before_date`: `Optional[datetime]` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Optional`

#### 🔹 `async archive_entries`

```python
async def archive_entries( self, before_date: datetime,
```

**Description**: Archive les entrées vers une table archive

- **Ligne**: 878
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `before_date`: `datetime`
  - `archive_table`: `str` = `'audit_log_archive'`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`

#### 🔹 `async anonymize_user_data`

```python
async def anonymize_user_data(self, user_id: int, tenant_id: int):
```

**Description**: Anonymise les données d'un utilisateur (RGPD)

- **Ligne**: 905
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `user_id`: `int`
  - `tenant_id`: `int`

#### 🔹 `async export_user_data`

```python
async def export_user_data(self, user_id: int, tenant_id: int) -> List[Dict[str, Any]]:
```

**Description**: Exporte toutes les données d'audit d'un utilisateur (RGPD)

- **Ligne**: 934
- **Réutilisabilité**: High
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `user_id`: `int`
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `audit_action` 🎀

```python
def audit_action( action: AuditAction,
```

**Description**: Décorateur pour auditer automatiquement une fonction

- **Ligne**: 954
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `action`: `AuditAction`
  - `entity`: `AuditEntity`
  - `get_entity_id` = `None`
  - `get_before_state` = `None`
  - `get_after_state` = `None`
  - `severity`: `AuditSeverity` = `AuditSeverity.INFO`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 3 autres*

#### 🔸 `decorator` 🎀

```python
def decorator(func):
```

- **Ligne**: 970
- **Réutilisabilité**: Low
- **Paramètres**:
  - `func`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 3 autres*

#### 🔸 `async wrapper` 🎀

```python
async def wrapper(*args, **kwargs):
```

- **Ligne**: 972
- **Réutilisabilité**: Low
- **Décorateurs**: `wraps(func)`
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 3 autres*

#### 🔸 `create_audit_trail`

```python
def create_audit_trail(db_pool=None, retention_days: int = 365) -> AuditTrail:
```

**Description**: Factory function pour créer un AuditTrail

- **Ligne**: 1083
- **Réutilisabilité**: High
- **Type de retour**: `AuditTrail`
- **Paramètres**:
  - `db_pool` = `None`
  - `retention_days`: `int` = `365`

#### 🔸 `async demo`

```python
async def demo():
```

- **Ligne**: 1090
- **Réutilisabilité**: Low
- **Dépendances**:
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - *... et 1 autres*

### `core/finance/bank_reconciliation.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 83
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
- **Dépendances**:
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 90
- **Réutilisabilité**: Low
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `_load_aliases`

```python
def _load_aliases(self):
```

**Description**: Charge les alias fournisseurs.

- **Ligne**: 151
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `reconcile_batch` 🎀

```python
def reconcile_batch( self, transaction_ids: Optional[List[int]] = None,
```

**Description**: Rapproche un lot de transactions.

- **Ligne**: 170
- **Réutilisabilité**: Medium
- **Type de retour**: `List[ReconciliationResult]`
- **Paramètres**:
  - `self`
  - `transaction_ids`: `Optional[List[int]]` = `None`
  - `auto_apply`: `bool` = `False`
  - `min_confidence`: `float` = `0.7`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `reconcile_single`

```python
def reconcile_single( self, transaction: Dict[str, Any],
```

**Description**: Rapproche une seule transaction.

- **Ligne**: 217
- **Réutilisabilité**: Medium
- **Type de retour**: `ReconciliationResult`
- **Paramètres**:
  - `self`
  - `transaction`: `Dict[str, Any]`
  - `auto_apply`: `bool` = `False`
  - `min_confidence`: `float` = `0.7`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔹 `_find_candidates` 🎀

```python
def _find_candidates( self, amount: float,
```

**Description**: Trouve les factures candidates.

- **Ligne**: 293
- **Réutilisabilité**: Medium
- **Type de retour**: `List[MatchCandidate]`
- **Paramètres**:
  - `self`
  - `amount`: `float`
  - `date`: `datetime`
  - `libelle`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `_find_multi_line_candidates` 🎀

```python
def _find_multi_line_candidates( self, amount: float,
```

**Description**: Trouve des combinaisons de factures pour le matching multi-lignes.

- **Ligne**: 387
- **Réutilisabilité**: Medium
- **Type de retour**: `List[MatchCandidate]`
- **Paramètres**:
  - `self`
  - `amount`: `float`
  - `date`: `datetime`
  - `libelle`: `str`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔹 `_find_best_combination` 🎀

```python
def _find_best_combination( self, invoices: List[Dict],
```

**Description**: Trouve la meilleure combinaison de factures pour atteindre le montant cible.

- **Ligne**: 457
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[List[Dict]]`
- **Paramètres**:
  - `self`
  - `invoices`: `List[Dict]`
  - `target`: `float`
  - `max_items`: `int` = `4`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.datetime`
  - *... et 7 autres*

#### 🔹 `search` 🎀

```python
def search(remaining: float, start: int, current: List[Dict], depth: int) -> Optional[List[Dict]]:
```

- **Ligne**: 467
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[List[Dict]]`
- **Paramètres**:
  - `remaining`: `float`
  - `start`: `int`
  - `current`: `List[Dict]`
  - `depth`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.datetime`
  - *... et 6 autres*

#### 🔹 `_extract_suppliers`

```python
def _extract_suppliers(self, libelle: str) -> List[str]:
```

**Description**: Extrait les noms de fournisseurs potentiels du libellé.

- **Ligne**: 495
- **Réutilisabilité**: Medium
- **Type de retour**: `List[str]`
- **Paramètres**:
  - `self`
  - `libelle`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `re`
  - `typing.List`

#### 🔹 `_calculate_supplier_match`

```python
def _calculate_supplier_match( self, invoice_supplier: str,
```

**Description**: Calcule le score de correspondance fournisseur.

- **Ligne**: 524
- **Réutilisabilité**: High
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `invoice_supplier`: `str`
  - `potential_suppliers`: `List[str]`
  - `libelle`: `str`
- **Dépendances**:
  - `typing.List`

#### 🔹 `_apply_reconciliation`

```python
def _apply_reconciliation(self, transaction_id: int, candidate: MatchCandidate):
```

**Description**: Applique un rapprochement.

- **Ligne**: 561
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `transaction_id`: `int`
  - `candidate`: `MatchCandidate`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`

#### 🔹 `_learn_from_match`

```python
def _learn_from_match(self, transaction_id: int, candidate: MatchCandidate):
```

**Description**: Apprend de ce rapprochement pour améliorer les futurs.

- **Ligne**: 591
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `transaction_id`: `int`
  - `candidate`: `MatchCandidate`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `_create_alert`

```python
def _create_alert( self, alert_type: str,
```

**Description**: Crée une alerte de rapprochement.

- **Ligne**: 631
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `alert_type`: `str`
  - `entity_type`: `str`
  - `entity_id`: `int`
  - `message`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `add_supplier_alias`

```python
def add_supplier_alias(self, supplier_name: str, alias: str):
```

**Description**: Ajoute un alias fournisseur manuellement.

- **Ligne**: 656
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `alias`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `manual_reconcile`

```python
def manual_reconcile( self, transaction_id: int,
```

**Description**: Rapprochement manuel.

- **Ligne**: 680
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `transaction_id`: `int`
  - `invoice_ids`: `List[int]`
  - `user`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `get_reconciliation_status`

```python
def get_reconciliation_status(self) -> Dict[str, Any]:
```

**Description**: Retourne le statut global du rapprochement.

- **Ligne**: 711
- **Réutilisabilité**: Low
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `get_unmatched_transactions`

```python
def get_unmatched_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
```

**Description**: Retourne les transactions non rapprochées.

- **Ligne**: 771
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `get_alerts`

```python
def get_alerts(self, resolved: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
```

**Description**: Retourne les alertes de rapprochement.

- **Ligne**: 807
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `resolved`: `bool` = `False`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

### `core/finance/event_sourcing.py`

#### 🔹 `__post_init__`

```python
def __post_init__(self):
```

- **Ligne**: 91
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`

#### 🔹 `_compute_checksum`

```python
def _compute_checksum(self) -> str:
```

**Description**: Calcule un checksum pour garantir l'intégrité.

- **Ligne**: 95
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `hashlib`
  - *... et 1 autres*

#### 🔹 `to_dict` 🎀

```python
def to_dict(self) -> Dict[str, Any]:
```

- **Ligne**: 100
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `dataclasses.asdict`
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `from_dict`

```python
def from_dict(cls, data: Dict[str, Any]) -> Event:
```

- **Ligne**: 107
- **Réutilisabilité**: Medium
- **Type de retour**: `Event`
- **Décorateurs**: `classmethod`
- **Paramètres**:
  - `cls`
  - `data`: `Dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - *... et 2 autres*

#### 🔹 `__new__`

```python
def __new__(cls):
```

- **Ligne**: 121
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `cls`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 129
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Callable`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_ensure_table`

```python
def _ensure_table(self):
```

**Description**: Crée la table event_log si nécessaire.

- **Ligne**: 136
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `append` 🎀

```python
def append(self, event: Event) -> Event:
```

**Description**: Ajoute un événement au store (immuable).

- **Ligne**: 167
- **Réutilisabilité**: Medium
- **Type de retour**: `Event`
- **Paramètres**:
  - `self`
  - `event`: `Event`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`

#### 🔹 `get_events` 🎀

```python
def get_events( self, aggregate_type: str,
```

**Description**: Récupère tous les événements d'un agrégat.

- **Ligne**: 200
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Event]`
- **Paramètres**:
  - `self`
  - `aggregate_type`: `str`
  - `aggregate_id`: `str`
  - `tenant_id`: `int`
  - `from_version`: `int` = `0`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `json`
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `get_events_by_type` 🎀

```python
def get_events_by_type( self, event_type: EventType,
```

**Description**: Récupère les événements d'un type donné.

- **Ligne**: 247
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Event]`
- **Paramètres**:
  - `self`
  - `event_type`: `EventType`
  - `tenant_id`: `int`
  - `since`: `Optional[datetime]` = `None`
  - `limit`: `int` = `100`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `datetime.datetime`
  - `json`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔹 `get_latest_version`

```python
def get_latest_version( self, aggregate_type: str,
```

**Description**: Retourne la dernière version d'un agrégat.

- **Ligne**: 297
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `aggregate_type`: `str`
  - `aggregate_id`: `str`
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `subscribe`

```python
def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
```

**Description**: Abonne un handler à un type d'événement.

- **Ligne**: 323
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `event_type`: `EventType`
  - `handler`: `Callable[[Event], None]`
- **Dépendances**:
  - `typing.Callable`

#### 🔹 `_dispatch`

```python
def _dispatch(self, event: Event):
```

**Description**: Dispatch l'événement aux handlers abonnés.

- **Ligne**: 329
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `event`: `Event`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - *... et 5 autres*

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int, user_id: Optional[int] = None):
```

- **Ligne**: 343
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
  - `user_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `typing.Optional`

#### 🔹 `emit`

```python
def emit( self, event_type: EventType,
```

**Description**: Émet un nouvel événement.

- **Ligne**: 348
- **Réutilisabilité**: Medium
- **Type de retour**: `Event`
- **Paramètres**:
  - `self`
  - `event_type`: `EventType`
  - `aggregate_type`: `str`
  - `aggregate_id`: `str`
  - `payload`: `Dict[str, Any]`
  - `metadata`: `Optional[Dict[str, Any]]` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`
  - `uuid.uuid4`

#### 🔹 `replay` 🎀

```python
def replay( self, aggregate_type: str,
```

**Description**: Rejoue tous les événements pour reconstruire l'état.

- **Ligne**: 376
- **Réutilisabilité**: High
- **Type de retour**: `Any`
- **Paramètres**:
  - `self`
  - `aggregate_type`: `str`
  - `aggregate_id`: `str`
  - `projector`: `Callable[[Any, Event], Any]`
  - `initial_state`: `Any` = `None`
- **Dépendances**:
  - `typing.Any`
  - `typing.Callable`

#### 🔸 `emit_invoice_imported`

```python
def emit_invoice_imported( tenant_id: int,
```

**Description**: Émet un événement d'import de facture.

- **Ligne**: 396
- **Réutilisabilité**: High
- **Type de retour**: `Event`
- **Paramètres**:
  - `tenant_id`: `int`
  - `invoice_id`: `str`
  - `filename`: `str`
  - `supplier`: `str`
  - `total`: `float`
  - `items_count`: `int`
  - `user_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `typing.Optional`

#### 🔸 `emit_price_updated`

```python
def emit_price_updated( tenant_id: int,
```

**Description**: Émet un événement de mise à jour de prix.

- **Ligne**: 420
- **Réutilisabilité**: High
- **Type de retour**: `Event`
- **Paramètres**:
  - `tenant_id`: `int`
  - `product_id`: `int`
  - `old_price`: `float`
  - `new_price`: `float`
  - `supplier`: `str`
  - `source`: `str`
  - `user_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `typing.Optional`

#### 🔸 `emit_stock_movement`

```python
def emit_stock_movement( tenant_id: int,
```

**Description**: Émet un événement de mouvement de stock.

- **Ligne**: 447
- **Réutilisabilité**: High
- **Type de retour**: `Event`
- **Paramètres**:
  - `tenant_id`: `int`
  - `product_id`: `int`
  - `movement_type`: `str`
  - `quantity`: `float`
  - `reason`: `str`
  - `reference`: `Optional[str]` = `None`
  - `user_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `typing.Optional`

#### 🔸 `emit_bank_transaction_categorized`

```python
def emit_bank_transaction_categorized( tenant_id: int,
```

**Description**: Émet un événement de catégorisation de transaction.

- **Ligne**: 471
- **Réutilisabilité**: High
- **Type de retour**: `Event`
- **Paramètres**:
  - `tenant_id`: `int`
  - `transaction_id`: `str`
  - `category`: `str`
  - `confidence`: `float`
  - `method`: `str`
  - `user_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `typing.Optional`

#### 🔸 `get_aggregate_history`

```python
def get_aggregate_history( tenant_id: int,
```

**Description**: Retourne l'historique complet d'un agrégat.

- **Ligne**: 493
- **Réutilisabilité**: High
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `aggregate_type`: `str`
  - `aggregate_id`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - *... et 8 autres*

#### 🔸 `get_recent_events` 🎀

```python
def get_recent_events( tenant_id: int,
```

**Description**: Retourne les événements récents.

- **Ligne**: 504
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `event_type`: `Optional[EventType]` = `None`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `dataclasses.asdict`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 3 autres*

### `core/finance/forecasting.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 80
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 84
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `forecast_sales` 🎀

```python
def forecast_sales( self, product_id: Optional[int] = None,
```

**Description**: Prévoit les ventes.

- **Ligne**: 120
- **Réutilisabilité**: Medium
- **Type de retour**: `ForecastResult`
- **Paramètres**:
  - `self`
  - `product_id`: `Optional[int]` = `None`
  - `category`: `Optional[str]` = `None`
  - `horizon_days`: `int` = `30`
  - `method`: `ForecastMethod` = `ForecastMethod.HOLT_WINTERS`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Optional`

#### 🔹 `forecast_stock`

```python
def forecast_stock( self, product_id: int,
```

**Description**: Prévoit l'épuisement du stock.

- **Ligne**: 173
- **Réutilisabilité**: Medium
- **Type de retour**: `ForecastResult`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `horizon_days`: `int` = `30`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 11 autres*

#### 🔹 `forecast_cashflow`

```python
def forecast_cashflow( self, horizon_days: int = 30,
```

**Description**: Prévoit la trésorerie.

- **Ligne**: 251
- **Réutilisabilité**: Medium
- **Type de retour**: `CashFlowForecast`
- **Paramètres**:
  - `self`
  - `horizon_days`: `int` = `30`
  - `include_recurring`: `bool` = `True`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 11 autres*

#### 🔹 `forecast_price`

```python
def forecast_price( self, product_id: int,
```

**Description**: Prévoit l'évolution des prix fournisseur.

- **Ligne**: 348
- **Réutilisabilité**: Medium
- **Type de retour**: `ForecastResult`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `horizon_days`: `int` = `90`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `math`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔹 `_get_sales_history`

```python
def _get_sales_history( self, product_id: Optional[int],
```

**Description**: Récupère l'historique des ventes.

- **Ligne**: 398
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `product_id`: `Optional[int]`
  - `category`: `Optional[str]`
  - `days`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - *... et 1 autres*

#### 🔹 `_get_cashflow_history`

```python
def _get_cashflow_history(self, tx_type: str, days: int) -> List[Dict[str, Any]]:
```

**Description**: Récupère l'historique des flux de trésorerie.

- **Ligne**: 435
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `tx_type`: `str`
  - `days`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_get_price_history`

```python
def _get_price_history(self, product_id: int, days: int) -> List[Dict[str, Any]]:
```

**Description**: Récupère l'historique des prix.

- **Ligne**: 462
- **Réutilisabilité**: High
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `days`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_get_recurring_expenses`

```python
def _get_recurring_expenses(self) -> List[Dict[str, Any]]:
```

**Description**: Identifie les charges récurrentes.

- **Ligne**: 483
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_holt_winters_forecast` 🎀

```python
def _holt_winters_forecast( self, history: List[Dict],
```

**Description**: Prévision Holt-Winters (triple exponential smoothing).

- **Ligne**: 518
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `history`: `List[Dict]`
  - `horizon`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 13 autres*

#### 🔹 `_exponential_smoothing` 🎀

```python
def _exponential_smoothing( self, history: List[Dict],
```

**Description**: Lissage exponentiel simple.

- **Ligne**: 572
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `history`: `List[Dict]`
  - `horizon`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 11 autres*

#### 🔹 `_linear_regression_forecast` 🎀

```python
def _linear_regression_forecast( self, history: List[Dict],
```

**Description**: Régression linéaire simple.

- **Ligne**: 599
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `history`: `List[Dict]`
  - `horizon`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 13 autres*

#### 🔹 `_moving_average_forecast` 🎀

```python
def _moving_average_forecast( self, history: List[Dict],
```

**Description**: Moyenne mobile simple.

- **Ligne**: 641
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `history`: `List[Dict]`
  - `horizon`: `int`
  - `window`: `int` = `7`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 11 autres*

#### 🔹 `_get_weekday_factor`

```python
def _get_weekday_factor(self, weekday: int, history: List[Dict]) -> float:
```

**Description**: Calcule le facteur saisonnier par jour de la semaine.

- **Ligne**: 669
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `weekday`: `int`
  - `history`: `List[Dict]`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 8 autres*

#### 🔹 `_add_confidence_intervals` 🎀

```python
def _add_confidence_intervals( self, predictions: List[Dict],
```

**Description**: Ajoute les intervalles de confiance.

- **Ligne**: 687
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `predictions`: `List[Dict]`
  - `history`: `List[Dict]`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 11 autres*

#### 🔹 `_calculate_metrics`

```python
def _calculate_metrics( self, actual: List[Dict],
```

**Description**: Calcule les métriques de qualité.

- **Ligne**: 710
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, float]`
- **Paramètres**:
  - `self`
  - `actual`: `List[Dict]`
  - `predicted`: `List[Dict]`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - *... et 14 autres*

#### 🔹 `_naive_forecast`

```python
def _naive_forecast( self, forecast_type: ForecastType,
```

**Description**: Prévision naïve quand pas assez de données.

- **Ligne**: 739
- **Réutilisabilité**: Medium
- **Type de retour**: `ForecastResult`
- **Paramètres**:
  - `self`
  - `forecast_type`: `ForecastType`
  - `entity_id`: `Optional[int]`
  - `entity_name`: `str`
  - `horizon`: `int`
  - `history`: `List[Dict]`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 9 autres*

#### 🔹 `_empty_forecast`

```python
def _empty_forecast( self, forecast_type: ForecastType,
```

**Description**: Prévision vide.

- **Ligne**: 773
- **Réutilisabilité**: High
- **Type de retour**: `ForecastResult`
- **Paramètres**:
  - `self`
  - `forecast_type`: `ForecastType`
  - `entity_id`: `Optional[int]`
  - `entity_name`: `str`
  - `horizon`: `int`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Optional`

#### 🔹 `_cache_forecast`

```python
def _cache_forecast(self, result: ForecastResult):
```

**Description**: Met en cache une prévision.

- **Ligne**: 793
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `result`: `ForecastResult`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `json`
  - *... et 1 autres*

#### 🔹 `get_cached_forecast`

```python
def get_cached_forecast( self, forecast_type: ForecastType,
```

**Description**: Récupère une prévision en cache.

- **Ligne**: 822
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[ForecastResult]`
- **Paramètres**:
  - `self`
  - `forecast_type`: `ForecastType`
  - `entity_id`: `Optional[int]`
  - `horizon_days`: `int`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Optional`

### `core/finance/insights.py`

#### 🔸 `refresh_recurring_expenses`

```python
def refresh_recurring_expenses(tenant_id: int, *, min_occurrences: int = 3) -> dict[str, Any]:
```

**Description**: Analyse les écritures bancaires pour détecter les charges récurrentes.

- **Ligne**: 24
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `refresh_anomaly_flags`

```python
def refresh_anomaly_flags( tenant_id: int,
```

**Description**: Détecte les écritures suspectes (montant hors bande).

- **Ligne**: 153
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_recurring_expenses`

```python
def list_recurring_expenses(tenant_id: int) -> list[dict[str, Any]]:
```

- **Ligne**: 272
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_anomaly_flags`

```python
def list_anomaly_flags(tenant_id: int, severity: str | None = None) -> list[dict[str, Any]]:
```

- **Ligne**: 297
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `severity`: `str | None` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

### `core/finance/inventory_intelligence.py`

#### 🔹 `__init__`

```python
def __init__(self, db_pool=None):
```

- **Ligne**: 196
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `db_pool` = `None`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔹 `analyze_demand`

```python
def analyze_demand( self, product_id: int,
```

**Description**: Analyse la demande d'un produit pour déterminer son pattern

- **Ligne**: 210
- **Réutilisabilité**: Medium
- **Type de retour**: `DemandAnalysis`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `consumption_history`: `List[Dict[str, Any]]`
  - `period_days`: `int` = `90`
- **Dépendances**:
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - *... et 4 autres*

#### 🔹 `_detect_trend`

```python
def _detect_trend(self, demands: List[Decimal]) -> str:
```

**Description**: Détecte la tendance via régression linéaire simple

- **Ligne**: 298
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `demands`: `List[Decimal]`
- **Dépendances**:
  - `decimal.Decimal`
  - `typing.List`

#### 🔹 `_detect_weekly_peaks`

```python
def _detect_weekly_peaks(self, daily_demand: Dict[Any, Decimal]) -> List[int]:
```

**Description**: Détecte les jours de la semaine avec demande significativement plus haute

- **Ligne**: 319
- **Réutilisabilité**: Medium
- **Type de retour**: `List[int]`
- **Paramètres**:
  - `self`
  - `daily_demand`: `Dict[Any, Decimal]`
- **Dépendances**:
  - `dataclasses.field`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `statistics`
  - *... et 5 autres*

#### 🔹 `calculate_eoq`

```python
def calculate_eoq( self, product_id: int,
```

**Description**: Calcule la quantité économique de commande (EOQ)

- **Ligne**: 355
- **Réutilisabilité**: Medium
- **Type de retour**: `EOQResult`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `annual_demand`: `Decimal`
  - `unit_cost`: `Decimal`
  - `ordering_cost`: `Optional[Decimal]` = `None`
  - `holding_cost_rate`: `Optional[float]` = `None`
  - `min_order_qty`: `Optional[int]` = `None`
  - `max_order_qty`: `Optional[int]` = `None`
  - `supplier_moq`: `Optional[int]` = `None`
- **Dépendances**:
  - `decimal.Decimal`
  - `math`
  - `typing.Optional`

#### 🔹 `calculate_safety_stock`

```python
def calculate_safety_stock( self, product_id: int,
```

**Description**: Calcule le stock de sécurité

- **Ligne**: 437
- **Réutilisabilité**: Medium
- **Type de retour**: `SafetyStockResult`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `average_daily_demand`: `Decimal`
  - `demand_std_dev`: `Decimal`
  - `average_lead_time_days`: `float`
  - `lead_time_std_dev`: `float` = `0.0`
  - `service_level`: `ServiceLevel` = `None`
  - `unit_cost`: `Optional[Decimal]` = `None`
- **Dépendances**:
  - `decimal.Decimal`
  - `math`
  - `typing.Optional`

#### 🔹 `calculate_reorder_point`

```python
def calculate_reorder_point( self, product_id: int,
```

**Description**: Calcule le point de réapprovisionnement et le statut actuel

- **Ligne**: 500
- **Réutilisabilité**: Medium
- **Type de retour**: `ReorderPoint`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `current_stock`: `int`
  - `average_daily_demand`: `Decimal`
  - `lead_time_days`: `float`
  - `safety_stock`: `int`
  - `eoq`: `int`
  - `pending_orders_qty`: `int` = `0`
- **Dépendances**:
  - `decimal.Decimal`
  - `math`

#### 🔹 `detect_dead_stock` 🎀

```python
def detect_dead_stock( self, products_with_stock: List[Dict[str, Any]],
```

**Description**: Détecte les produits en stock mort (rotation < 0.3/mois)

- **Ligne**: 568
- **Réutilisabilité**: Medium
- **Type de retour**: `List[DeadStockItem]`
- **Paramètres**:
  - `self`
  - `products_with_stock`: `List[Dict[str, Any]]`
  - `rotation_threshold`: `float` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `predict_stockouts` 🎀

```python
def predict_stockouts( self, products: List[Dict[str, Any]],
```

**Description**: Prédit les ruptures de stock dans les N prochains jours

- **Ligne**: 649
- **Réutilisabilité**: Medium
- **Type de retour**: `List[StockoutPrediction]`
- **Paramètres**:
  - `self`
  - `products`: `List[Dict[str, Any]]`
  - `horizon_days`: `int` = `30`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `generate_reorder_suggestions` 🎀

```python
def generate_reorder_suggestions( self, products: List[Dict[str, Any]],
```

**Description**: Génère des suggestions de réapprovisionnement automatiques

- **Ligne**: 733
- **Réutilisabilité**: Low
- **Type de retour**: `List[ReorderSuggestion]`
- **Paramètres**:
  - `self`
  - `products`: `List[Dict[str, Any]]`
  - `suppliers`: `Dict[int, Dict[str, Any]]` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `classify_abc_xyz` 🎀

```python
def classify_abc_xyz( self, products: List[Dict[str, Any]]
```

**Description**: Classification ABC (valeur) + XYZ (variabilité) combinée

- **Ligne**: 858
- **Réutilisabilité**: Medium
- **Type de retour**: `List[ABCXYZClassification]`
- **Paramètres**:
  - `self`
  - `products`: `List[Dict[str, Any]]`
- **Dépendances**:
  - `decimal.Decimal`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - `typing.Optional`
  - *... et 1 autres*

#### 🔹 `async get_product_inventory_analysis`

```python
async def get_product_inventory_analysis( self, tenant_id: int,
```

**Description**: Analyse complète d'inventaire pour un produit

- **Ligne**: 948
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
  - `product_id`: `int`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

#### 🔸 `create_inventory_intelligence`

```python
def create_inventory_intelligence(db_pool=None) -> InventoryIntelligence:
```

**Description**: Factory function pour créer une instance

- **Ligne**: 1049
- **Réutilisabilité**: High
- **Type de retour**: `InventoryIntelligence`
- **Paramètres**:
  - `db_pool` = `None`

### `core/finance/margin_calculator.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 96
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 101
- **Réutilisabilité**: Low
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `_load_config`

```python
def _load_config(self) -> Dict[str, Any]:
```

**Description**: Charge la configuration des marges.

- **Ligne**: 167
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `calculate_product_margin`

```python
def calculate_product_margin( self, product_id: int,
```

**Description**: Calcule la marge pour un produit.

- **Ligne**: 199
- **Réutilisabilité**: Medium
- **Type de retour**: `MarginResult`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `calculate_category_margin`

```python
def calculate_category_margin( self, category: str,
```

**Description**: Calcule la marge pour une catégorie.

- **Ligne**: 296
- **Réutilisabilité**: Medium
- **Type de retour**: `MarginResult`
- **Paramètres**:
  - `self`
  - `category`: `str`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `calculate_total_margin`

```python
def calculate_total_margin( self, period_start: date,
```

**Description**: Calcule la marge totale.

- **Ligne**: 342
- **Réutilisabilité**: Medium
- **Type de retour**: `MarginResult`
- **Paramètres**:
  - `self`
  - `period_start`: `date`
  - `period_end`: `date`
  - `include_restaurant`: `bool` = `True`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `calculate_menu_margin`

```python
def calculate_menu_margin( self, menu_id: int,
```

**Description**: Calcule la marge pour un menu restaurant.

- **Ligne**: 408
- **Réutilisabilité**: Medium
- **Type de retour**: `MarginResult`
- **Paramètres**:
  - `self`
  - `menu_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `calculate_pamp`

```python
def calculate_pamp(self, product_id: int) -> PAMPHistory:
```

**Description**: Calcule le Prix d'Achat Moyen Pondéré.

- **Ligne**: 479
- **Réutilisabilité**: Medium
- **Type de retour**: `PAMPHistory`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - *... et 5 autres*

#### 🔹 `_build_margin_result`

```python
def _build_margin_result( self, entity_type: str,
```

**Description**: Construit un résultat de marge complet.

- **Ligne**: 547
- **Réutilisabilité**: Medium
- **Type de retour**: `MarginResult`
- **Paramètres**:
  - `self`
  - `entity_type`: `str`
  - `entity_id`: `Optional[int]`
  - `entity_name`: `str`
  - `period_start`: `date`
  - `period_end`: `date`
  - `revenue`: `float`
  - `cost_of_goods`: `float`
  - `quantity_sold`: `float`
  - `extra_details`: `Dict` = `None`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`
  - `typing.Optional`

#### 🔹 `_empty_margin_result`

```python
def _empty_margin_result( self, entity_type: str,
```

**Description**: Retourne un résultat vide.

- **Ligne**: 606
- **Réutilisabilité**: Medium
- **Type de retour**: `MarginResult`
- **Paramètres**:
  - `self`
  - `entity_type`: `str`
  - `entity_id`: `Optional[int]`
  - `entity_name`: `str`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Optional`

#### 🔹 `_get_total_revenue`

```python
def _get_total_revenue(self, period_start: date, period_end: date) -> float:
```

**Description**: Récupère le CA total sur la période.

- **Ligne**: 628
- **Réutilisabilité**: High
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `_calculate_loss_value`

```python
def _calculate_loss_value( self, product_id: int,
```

**Description**: Calcule la valeur des pertes/vols.

- **Ligne**: 645
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `product_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
  - `pamp`: `float`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`

#### 🔹 `save_snapshot`

```python
def save_snapshot(self, result: MarginResult, period_type: PeriodType = PeriodType.DAY):
```

**Description**: Sauvegarde un snapshot de marge.

- **Ligne**: 669
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `result`: `MarginResult`
  - `period_type`: `PeriodType` = `PeriodType.DAY`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`

#### 🔹 `get_margin_history`

```python
def get_margin_history( self, entity_type: str,
```

**Description**: Récupère l'historique des marges.

- **Ligne**: 722
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `entity_type`: `str`
  - `entity_id`: `Optional[int]`
  - `period_type`: `PeriodType` = `PeriodType.DAY`
  - `limit`: `int` = `30`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - *... et 1 autres*

#### 🔹 `get_margin_alerts`

```python
def get_margin_alerts(self, threshold_pct: float = None) -> List[Dict[str, Any]]:
```

**Description**: Identifie les produits/catégories avec marges sous le seuil.

- **Ligne**: 770
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `threshold_pct`: `float` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

### `core/finance/reconciliation.py`

#### 🔸 `run_reconciliation_job`

```python
def run_reconciliation_job( tenant_id: int,
```

**Description**: Execute the heuristic reconciliation job and persist suggestions.

- **Ligne**: 242
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `decimal.Decimal`
  - `difflib.SequenceMatcher`
  - `json`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `fetch_matches`

```python
def fetch_matches(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
```

**Description**: Return reconciliation matches for manual review.

- **Ligne**: 515
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `status`: `str | None` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_match_status` 🎀

```python
def update_match_status(tenant_id: int, match_id: int, *, status: str, note: str | None = None) -> dict[str, Any]:
```

- **Ligne**: 562
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `match_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

### `core/finance/rules_engine.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 90
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Dict`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 97
- **Réutilisabilité**: Low
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `_load_rules` 🎀

```python
def _load_rules(self) -> List[Rule]:
```

**Description**: Charge les règles depuis la DB avec cache.

- **Ligne**: 155
- **Réutilisabilité**: Low
- **Type de retour**: `List[Rule]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `json`
  - *... et 2 autres*

#### 🔹 `_load_category_stats` 🎀

```python
def _load_category_stats(self, category: str, supplier: Optional[str] = None) -> Dict[str, float]:
```

**Description**: Charge les statistiques d'une catégorie.

- **Ligne**: 198
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, float]`
- **Paramètres**:
  - `self`
  - `category`: `str`
  - `supplier`: `Optional[str]` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Dict`
  - `typing.Optional`

#### 🔹 `classify`

```python
def classify( self, transaction: Dict[str, Any],
```

**Description**: Classifie une transaction.

- **Ligne**: 236
- **Réutilisabilité**: Medium
- **Type de retour**: `ClassificationResult`
- **Paramètres**:
  - `self`
  - `transaction`: `Dict[str, Any]`
  - `detect_anomalies`: `bool` = `True`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - *... et 10 autres*

#### 🔹 `_evaluate_rule`

```python
def _evaluate_rule( self, rule: Rule,
```

**Description**: Évalue une règle et retourne un score.

- **Ligne**: 295
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `rule`: `Rule`
  - `description`: `str`
  - `amount`: `float`
  - `supplier`: `str`
  - `date`: `Any`
- **Dépendances**:
  - `__future__.annotations`
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - *... et 5 autres*

#### 🔹 `_calculate_similarity` 🎀

```python
def _calculate_similarity(self, text: str, terms: List[str]) -> float:
```

**Description**: Calcule un score de similarité fuzzy.

- **Ligne**: 359
- **Réutilisabilité**: High
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `text`: `str`
  - `terms`: `List[str]`
- **Dépendances**:
  - `sqlalchemy.text`
  - `typing.List`

#### 🔹 `_ml_classify`

```python
def _ml_classify( self, description: str,
```

**Description**: Classification par apprentissage (basée sur l'historique).

- **Ligne**: 385
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[Tuple[str, float]]`
- **Paramètres**:
  - `self`
  - `description`: `str`
  - `amount`: `float`
  - `supplier`: `str`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `sqlalchemy.text`
  - *... et 3 autres*

#### 🔹 `_detect_anomalies` 🎀

```python
def _detect_anomalies( self, transaction: Dict[str, Any],
```

**Description**: Détecte les anomalies dans une transaction.

- **Ligne**: 421
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Anomaly]`
- **Paramètres**:
  - `self`
  - `transaction`: `Dict[str, Any]`
  - `matches`: `List[Tuple[Rule, float]]`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`
  - *... et 1 autres*

#### 🔹 `classify_batch`

```python
def classify_batch( self, transactions: List[Dict[str, Any]]
```

**Description**: Classifie un lot de transactions.

- **Ligne**: 474
- **Réutilisabilité**: High
- **Type de retour**: `List[ClassificationResult]`
- **Paramètres**:
  - `self`
  - `transactions`: `List[Dict[str, Any]]`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `add_rule`

```python
def add_rule( self, name: str,
```

**Description**: Ajoute une nouvelle règle.

- **Ligne**: 481
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `name`: `str`
  - `rule_type`: `RuleType`
  - `category`: `str`
  - `conditions`: `Dict[str, Any]`
  - `priority`: `int` = `0`
  - `weight`: `float` = `1.0`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `record_feedback`

```python
def record_feedback( self, transaction_id: str,
```

**Description**: Enregistre le feedback pour améliorer l'apprentissage.

- **Ligne**: 521
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `transaction_id`: `str`
  - `predicted_category`: `str`
  - `actual_category`: `str`
  - `feedback`: `str`
  - `rule_id`: `Optional[int]` = `None`
  - `confidence`: `float` = `0.0`
  - `method`: `str` = `'rule'`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔹 `update_category_stats`

```python
def update_category_stats(self, category: str, supplier: Optional[str], amount: float):
```

**Description**: Met à jour les statistiques d'une catégorie.

- **Ligne**: 583
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `category`: `str`
  - `supplier`: `Optional[str]`
  - `amount`: `float`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔹 `get_rules`

```python
def get_rules(self) -> List[Dict[str, Any]]:
```

**Description**: Retourne toutes les règles.

- **Ligne**: 612
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `re`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `detect_duplicate_payments`

```python
def detect_duplicate_payments( self, transaction: Dict[str, Any],
```

**Description**: Détecte les paiements en double potentiels.

- **Ligne**: 631
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[Anomaly]`
- **Paramètres**:
  - `self`
  - `transaction`: `Dict[str, Any]`
  - `tolerance_days`: `int` = `7`
  - `tolerance_amount`: `float` = `0.02`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.datetime`
  - *... et 5 autres*

#### 🔸 `bootstrap_default_rules`

```python
def bootstrap_default_rules(tenant_id: int):
```

**Description**: Initialise les règles par défaut pour un tenant.

- **Ligne**: 765
- **Réutilisabilité**: High
- **Paramètres**:
  - `tenant_id`: `int`

### `core/finance/supplier_scoring.py`

#### 🔹 `__init__`

```python
def __init__(self, tenant_id: int):
```

- **Ligne**: 78
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`

#### 🔹 `_ensure_tables`

```python
def _ensure_tables(self):
```

**Description**: Crée les tables nécessaires.

- **Ligne**: 82
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `calculate_score` 🎀

```python
def calculate_score( self, supplier_name: str,
```

**Description**: Calcule le score complet d'un fournisseur.

- **Ligne**: 127
- **Réutilisabilité**: Medium
- **Type de retour**: `SupplierScore`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `supplier_id`: `Optional[int]` = `None`
  - `period_days`: `int` = `90`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `statistics.stdev`
  - `typing.Optional`

#### 🔹 `_calculate_price_stability`

```python
def _calculate_price_stability( self, supplier_name: str,
```

**Description**: Calcule le score de stabilité des prix.

- **Ligne**: 203
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `statistics.mean`
  - *... et 3 autres*

#### 🔹 `_calculate_delivery_reliability`

```python
def _calculate_delivery_reliability( self, supplier_name: str,
```

**Description**: Calcule le score de fiabilité des livraisons.

- **Ligne**: 293
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔹 `_calculate_invoice_accuracy`

```python
def _calculate_invoice_accuracy( self, supplier_name: str,
```

**Description**: Calcule le score d'exactitude des factures.

- **Ligne**: 345
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔹 `_calculate_stock_accuracy`

```python
def _calculate_stock_accuracy( self, supplier_name: str,
```

**Description**: Calcule le score d'exactitude du stock.

- **Ligne**: 428
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `since`: `datetime`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔹 `_calculate_grade`

```python
def _calculate_grade(self, score: float) -> str:
```

**Description**: Convertit un score en grade.

- **Ligne**: 493
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `score`: `float`

#### 🔹 `_calculate_trend`

```python
def _calculate_trend(self, supplier_name: str) -> str:
```

**Description**: Calcule la tendance du score.

- **Ligne**: 506
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `statistics.mean`

#### 🔹 `_get_score_history`

```python
def _get_score_history( self, supplier_name: str,
```

**Description**: Récupère l'historique des scores.

- **Ligne**: 541
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `limit`: `int` = `10`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔹 `_save_score`

```python
def _save_score(self, score: SupplierScore):
```

**Description**: Sauvegarde le score calculé.

- **Ligne**: 574
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `score`: `SupplierScore`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `statistics.stdev`

#### 🔹 `get_all_suppliers_ranking`

```python
def get_all_suppliers_ranking(self) -> List[Dict[str, Any]]:
```

**Description**: Retourne le classement de tous les fournisseurs.

- **Ligne**: 595
- **Réutilisabilité**: Low
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔹 `get_supplier_comparison`

```python
def get_supplier_comparison( self, suppliers: List[str]
```

**Description**: Compare plusieurs fournisseurs.

- **Ligne**: 629
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
  - `suppliers`: `List[str]`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `json`
  - *... et 6 autres*

#### 🔹 `record_delivery`

```python
def record_delivery( self, supplier_name: str,
```

**Description**: Enregistre une livraison pour le suivi.

- **Ligne**: 660
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `expected_date`: `datetime`
  - `actual_date`: `datetime`
  - `invoice_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔹 `record_invoice_issue`

```python
def record_invoice_issue( self, supplier_name: str,
```

**Description**: Enregistre un problème de facture.

- **Ligne**: 688
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `supplier_name`: `str`
  - `issue_type`: `str`
  - `severity`: `str`
  - `invoice_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Optional`

### `core/finance/transaction_line_defaults.py`

#### 🔸 `fill_missing_transaction_lines`

```python
def fill_missing_transaction_lines(tx_ids: Iterable[int]) -> Dict[str, Any]:
```

**Description**: Crée des transaction_lines vides pour les transactions données (si absents).

- **Ligne**: 8
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tx_ids`: `Iterable[int]`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

---

## General

**114 fonctions**

### `backend/dependencies/security.py`

#### 🔸 `async require_user`

```python
async def require_user(request: Request) -> AuthenticatedUser:
```

**Description**: Récupère l'utilisateur courant depuis le cookie HTTP-Only.

- **Ligne**: 298
- **Réutilisabilité**: High
- **Type de retour**: `AuthenticatedUser`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `fastapi.Request`

#### 🔸 `require_roles` 🎀

```python
def require_roles(*roles: str) -> Callable:
```

**Description**: Exige des rôles spécifiques pour accéder à la ressource.

- **Ligne**: 303
- **Réutilisabilité**: Medium
- **Type de retour**: `Callable`
- **Dépendances**:
  - `backend.settings.Settings`
  - `core.user_service.ALLOWED_ROLES`
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`
  - *... et 1 autres*

#### 🔸 `async enforce_default_rbac` 🎀

```python
async def enforce_default_rbac(request: Request) -> AuthenticatedUser:
```

**Description**: Autorise toute personne authentifiée à lire ; managers/admins pour modifier.

- **Ligne**: 319
- **Réutilisabilité**: High
- **Type de retour**: `AuthenticatedUser`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `core.user_service.ALLOWED_ROLES`
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`

### `backend/dependencies/tenant.py`

#### 🔸 `bootstrap_tenants_if_enabled`

```python
def bootstrap_tenants_if_enabled() -> None:
```

**Description**: Initialise la table des tenants seulement si l'environnement l'autorise.

- **Ligne**: 38
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.tenant_service.ensure_tenants_table`
  - `fastapi.HTTPException`
  - `os`

#### 🔸 `resolve_tenant`

```python
def resolve_tenant(identifier: Optional[str | int]) -> Tenant | None:
```

- **Ligne**: 67
- **Réutilisabilité**: High
- **Type de retour**: `Tenant | None`
- **Paramètres**:
  - `identifier`: `Optional[str | int]`
- **Dépendances**:
  - `typing.Optional`

### `backend/main.py`

#### 🔹 `_strip_name`

```python
def _strip_name(cls, value: str | None) -> str | None:
```

- **Ligne**: 88
- **Réutilisabilité**: High
- **Type de retour**: `str | None`
- **Décorateurs**: `field_validator('nom', mode='before')`
- **Paramètres**:
  - `cls`
  - `value`: `str | None`
- **Dépendances**:
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `core.products_loader.ensure_barcode_constraints`
  - `core.user_service.bootstrap_users_if_enabled`
  - `pydantic.field_validator`

#### 🔸 `healthcheck`

```python
def healthcheck() -> dict[str, str]:
```

- **Ligne**: 380
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, str]`
- **Décorateurs**: `app.get('/health')`
- **Dépendances**:
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `backend.middleware.ResponseWrapperMiddleware`
  - `core.products_loader.ensure_barcode_constraints`
  - `core.user_service.bootstrap_users_if_enabled`

#### 🔸 `vscode_tuto`

```python
def vscode_tuto() -> dict[str, str]:
```

- **Ligne**: 415
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, str]`
- **Décorateurs**: `app.get('/vscode/tuto')`
- **Dépendances**:
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `backend.middleware.ResponseWrapperMiddleware`
  - `core.products_loader.ensure_barcode_constraints`
  - `core.user_service.bootstrap_users_if_enabled`

#### 🔸 `list_products`

```python
def list_products(tenant: Tenant = Depends(get_current_tenant)) -> list[ProductPayload]:
```

- **Ligne**: 427
- **Réutilisabilité**: High
- **Type de retour**: `list[ProductPayload]`
- **Décorateurs**: `app.get('/products', response_model=list[ProductPayload], dependencies=_security_dependencies())`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.middleware.ResponseWrapperMiddleware`
  - `fastapi.Depends`

#### 🔸 `inventory_summary`

```python
def inventory_summary(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, float]:
```

- **Ligne**: 431
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, float]`
- **Décorateurs**: `app.get('/inventory/summary', dependencies=_security_dependencies())`
- **Paramètres**:
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.middleware.ResponseWrapperMiddleware`
  - `core.products_loader.ensure_barcode_constraints`
  - *... et 2 autres*

#### 🔸 `checkout`

```python
def checkout(payload: CheckoutRequest, tenant: Tenant = Depends(get_current_tenant)) -> CheckoutResponse:
```

- **Ligne**: 435
- **Réutilisabilité**: Medium
- **Type de retour**: `CheckoutResponse`
- **Décorateurs**: `app.post('/pos/checkout', response_model=CheckoutResponse, dependencies=_security_dependencies())`
- **Paramètres**:
  - `payload`: `CheckoutRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `backend.dependencies.tenant.get_current_tenant`
  - `backend.middleware.ResponseWrapperMiddleware`
  - `base64`
  - *... et 2 autres*

### `backend/settings.py`

#### 🔹 `load` 🎀

```python
def load() -> "Settings":
```

- **Ligne**: 15
- **Réutilisabilité**: Medium
- **Type de retour**: `'Settings'`
- **Décorateurs**: `staticmethod`
- **Dépendances**:
  - `core.settings.AppSettings`
  - `os`

### `backend/tests/conftest.py`

#### 🔸 `mock_tenant`

```python
def mock_tenant():
```

**Description**: Tenant fictif pour les tests.

- **Ligne**: 26
- **Réutilisabilité**: Medium
- **Décorateurs**: `pytest.fixture`
- **Dépendances**:
  - `pytest`

#### 🔸 `mock_user`

```python
def mock_user():
```

**Description**: Utilisateur fictif pour les tests.

- **Ligne**: 34
- **Réutilisabilité**: Medium
- **Décorateurs**: `pytest.fixture`
- **Dépendances**:
  - `pytest`

### `core/backup_manager.py`

#### 🔹 `size_mb`

```python
def size_mb(self) -> float:
```

**Description**: Représentation lisible en mégaoctets.

- **Ligne**: 41
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `available`

```python
def available(self) -> bool:
```

- **Ligne**: 77
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔸 `list_backups` 🎀

```python
def list_backups( directory: str | os.PathLike[str] | None = None,
```

**Description**: Retourne les métadonnées de sauvegarde triées du plus récent au plus ancien.

- **Ligne**: 248
- **Réutilisabilité**: Medium
- **Type de retour**: `List[BackupMetadata]`
- **Paramètres**:
  - `directory`: `str | os.PathLike[str] | None` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - `os`
  - `statistics.mean`
  - *... et 1 autres*

#### 🔸 `build_backup_timeline`

```python
def build_backup_timeline(backups: Iterable[BackupMetadata]) -> List[dict]:
```

**Description**: Retourne une timeline sérialisable pour les visualisations.

- **Ligne**: 281
- **Réutilisabilité**: High
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `backups`: `Iterable[BackupMetadata]`
- **Dépendances**:
  - `typing.Iterable`
  - `typing.List`

#### 🔸 `suggest_retention_cleanup` 🎀

```python
def suggest_retention_cleanup( backups: Iterable[BackupMetadata],
```

**Description**: Retourne les sauvegardes à purger selon les règles de rétention.

- **Ligne**: 309
- **Réutilisabilité**: Medium
- **Type de retour**: `List[BackupMetadata]`
- **Paramètres**:
  - `backups`: `Iterable[BackupMetadata]`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - `pathlib.Path`
  - `subprocess`
  - *... et 2 autres*

#### 🔸 `plan_next_backup` 🎀

```python
def plan_next_backup( settings: Dict[str, object],
```

**Description**: Calcule la prochaine sauvegarde planifiée en horaire local.

- **Ligne**: 342
- **Réutilisabilité**: High
- **Type de retour**: `Optional[datetime]`
- **Paramètres**:
  - `settings`: `Dict[str, object]`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - `typing.Dict`
  - `typing.Optional`

#### 🔸 `integrity_report` 🎀

```python
def integrity_report(backups: Iterable[BackupMetadata]) -> List[dict]:
```

**Description**: Retourne l'état d'intégrité pour chaque sauvegarde fournie.

- **Ligne**: 407
- **Réutilisabilité**: High
- **Type de retour**: `List[dict]`
- **Paramètres**:
  - `backups`: `Iterable[BackupMetadata]`
- **Dépendances**:
  - `typing.Iterable`
  - `typing.List`

### `core/bank_import/USAGE_EXAMPLES.py`

#### 🔸 `example_enhanced_detection`

```python
def example_enhanced_detection():
```

**Description**: Utiliser la détection enrichie avec IBAN et confidence score.

- **Ligne**: 23
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.bank_import.detect_bank_type`

#### 🔸 `example_full_detection`

```python
def example_full_detection():
```

**Description**: Utiliser la détection complète avec tous les détails.

- **Ligne**: 47
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.bank_import.detect_bank_full`

#### 🔹 `bank_type`

```python
def bank_type(self) -> BankType:
```

**Description**: Type de banque géré par ce parser.

- **Ligne**: 85
- **Réutilisabilité**: Medium
- **Type de retour**: `BankType`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.bank_import.BankType`

#### 🔹 `_is_transaction_line`

```python
def _is_transaction_line(self, line: str) -> bool:
```

**Description**: Vérifie si une ligne est une transaction.

- **Ligne**: 149
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `line`: `str`

#### 🔸 `example_custom_parser`

```python
def example_custom_parser():
```

**Description**: Utiliser un parser custom.

- **Ligne**: 160
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.bank_import.StatementPeriod`
  - `core.bank_import.get_parser`
  - `datetime.date`

#### 🔸 `example_factory_pattern`

```python
def example_factory_pattern():
```

**Description**: Utiliser get_parser() pour obtenir le bon parser.

- **Ligne**: 187
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.bank_import.StatementPeriod`
  - `core.bank_import.detect_bank_type`
  - `core.bank_import.get_parser`
  - `datetime.date`

#### 🔸 `example_complete_workflow`

```python
def example_complete_workflow():
```

**Description**: Workflow complet de détection et parsing.

- **Ligne**: 215
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.bank_import.detect_bank_full`
  - `core.bank_import.detect_bank_type`
  - `core.bank_import.get_parser`

#### 🔸 `example_register_parser`

```python
def example_register_parser():
```

**Description**: Enregistrer un nouveau parser dans le registry.

- **Ligne**: 258
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.bank_import.BankType`
  - `core.bank_import.BaseBankParser`
  - `core.bank_import.ParsedStatement`
  - `core.bank_import.ParsedTransaction`
  - `core.bank_import.StatementPeriod`
  - *... et 4 autres*

#### 🔸 `example_error_handling`

```python
def example_error_handling():
```

**Description**: Gérer les erreurs et cas limites.

- **Ligne**: 279
- **Réutilisabilité**: Low
- **Dépendances**:
  - `core.bank_import.BankType`
  - `core.bank_import.BaseBankParser`
  - `core.bank_import.ParsedStatement`
  - `core.bank_import.ParsedTransaction`
  - `core.bank_import.StatementPeriod`
  - *... et 7 autres*

### `core/bank_import/categories.py`

#### 🔸 `build_keyword_index` 🎀

```python
def build_keyword_index() -> Dict[str, str]:
```

**Description**: Build a keyword -> category_code index.

- **Ligne**: 327
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, str]`
- **Dépendances**:
  - `typing.Dict`

### `core/bank_import/categorizer.py`

#### 🔹 `__init__`

```python
def __init__(self, bank_type: Optional[BankType] = None, load_db_rules: bool = True):
```

**Description**: Initialize categorizer.

- **Ligne**: 66
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `bank_type`: `Optional[BankType]` = `None`
  - `load_db_rules`: `bool` = `True`
- **Dépendances**:
  - `__future__.annotations`
  - `models.BankType`
  - `models.TransactionDirection`
  - `re`
  - `typing.Dict`
  - *... et 2 autres*

#### 🔹 `_match_db_rules`

```python
def _match_db_rules(self, libelle: str) -> Optional[CategorizationResult]:
```

**Description**: Try to match against DB rules first.

- **Ligne**: 137
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[CategorizationResult]`
- **Paramètres**:
  - `self`
  - `libelle`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.query_df`
  - `models.TransactionDirection`
  - `re`
  - `typing.Optional`

#### 🔹 `_build_patterns`

```python
def _build_patterns(self) -> None:
```

**Description**: Build regex patterns for word boundary matching.

- **Ligne**: 175
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `categories.CATEGORIES`
  - `categories.CategoryDefinition`
  - `categories.KEYWORD_INDEX`
  - `categories.get_all_categories`

#### 🔹 `categorize` 🎀

```python
def categorize( self, transaction: ParsedTransaction,
```

**Description**: Categorize a single transaction.

- **Ligne**: 223
- **Réutilisabilité**: Medium
- **Type de retour**: `CategorizationResult`
- **Paramètres**:
  - `self`
  - `transaction`: `ParsedTransaction`
  - `bank_type`: `Optional[BankType]` = `None`
- **Dépendances**:
  - `categories.CATEGORIES`
  - `categories.CategoryDefinition`
  - `categories.KEYWORD_INDEX`
  - `categories.get_all_categories`
  - `core.data_repository.query_df`
  - *... et 4 autres*

#### 🔹 `_match_keyword`

```python
def _match_keyword( self, libelle: str,
```

**Description**: Try to match a keyword in libelle.

- **Ligne**: 297
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[Tuple[float, int]]`
- **Paramètres**:
  - `self`
  - `libelle`: `str`
  - `keyword`: `str`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Optional`
  - `typing.Tuple`

#### 🔹 `categorize_batch`

```python
def categorize_batch( self, transactions: List[ParsedTransaction],
```

**Description**: Categorize multiple transactions.

- **Ligne**: 331
- **Réutilisabilité**: Medium
- **Type de retour**: `List[CategorizationResult]`
- **Paramètres**:
  - `self`
  - `transactions`: `List[ParsedTransaction]`
  - `bank_type`: `Optional[BankType]` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `categories.CATEGORIES`
  - `categories.CategoryDefinition`
  - `categories.KEYWORD_INDEX`
  - `categories.get_all_categories`
  - *... et 11 autres*

#### 🔹 `apply_categories`

```python
def apply_categories( self, transactions: List[ParsedTransaction],
```

**Description**: Apply categories to transactions in-place.

- **Ligne**: 347
- **Réutilisabilité**: Medium
- **Type de retour**: `Tuple[int, int]`
- **Paramètres**:
  - `self`
  - `transactions`: `List[ParsedTransaction]`
  - `bank_type`: `Optional[BankType]` = `None`
- **Dépendances**:
  - `models.BankType`
  - `models.ParsedTransaction`
  - `typing.List`
  - `typing.Optional`
  - `typing.Tuple`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 384
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Dict`

#### 🔹 `categorize`

```python
def categorize( self, transaction: ParsedTransaction
```

**Description**: Categorize with custom rules first.

- **Ligne**: 399
- **Réutilisabilité**: Medium
- **Type de retour**: `CategorizationResult`
- **Paramètres**:
  - `self`
  - `transaction`: `ParsedTransaction`
- **Dépendances**:
  - `categories.CATEGORIES`
  - `categories.CategoryDefinition`
  - `categories.KEYWORD_INDEX`
  - `categories.get_all_categories`
  - `models.ParsedTransaction`

#### 🔸 `record_categorization_feedback`

```python
def record_categorization_feedback( transaction_id: int,
```

**Description**: Record a categorization correction for ML learning.

- **Ligne**: 433
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `transaction_id`: `int`
  - `predicted_category_id`: `Optional[int]`
  - `actual_category_id`: `int`
  - `confidence_score`: `Optional[float]` = `None`
  - `user_id`: `Optional[int]` = `None`
  - `correction_source`: `str` = `'manual'`
- **Dépendances**:
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔸 `categorize_transaction`

```python
def categorize_transaction(libelle: str, direction: str = "OUT") -> str:
```

**Description**: Convenience function to categorize a single transaction.

- **Ligne**: 560
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `libelle`: `str`
  - `direction`: `str` = `'OUT'`
- **Dépendances**:
  - `models.ParsedTransaction`
  - `models.TransactionDirection`

### `core/bank_import/deduplicator.py`

#### 🔹 `__init__`

```python
def __init__(self, engine: Optional[Engine] = None, allow_batch_duplicates: bool = True):
```

- **Ligne**: 42
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `engine`: `Optional[Engine]` = `None`
  - `allow_batch_duplicates`: `bool` = `True`
- **Dépendances**:
  - `logging`
  - `sqlalchemy.engine.Engine`
  - `typing.Optional`
  - `typing.Set`

#### 🔹 `generate_checksum`

```python
def generate_checksum(self, txn: ParsedTransaction) -> str:
```

**Description**: Generate a unique checksum for a transaction.

- **Ligne**: 49
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `txn`: `ParsedTransaction`
- **Dépendances**:
  - `dataclasses.dataclass`
  - `decimal.Decimal`
  - `hashlib`
  - `models.ParsedTransaction`

#### 🔹 `deduplicate`

```python
def deduplicate( self, transactions: List[ParsedTransaction],
```

**Description**: Deduplicate a list of transactions.

- **Ligne**: 127
- **Réutilisabilité**: Medium
- **Type de retour**: `DeduplicationResult`
- **Paramètres**:
  - `self`
  - `transactions`: `List[ParsedTransaction]`
  - `account_id`: `Optional[int]` = `None`
  - `period_start`: `Optional[date]` = `None`
  - `period_end`: `Optional[date]` = `None`
- **Dépendances**:
  - `datetime.date`
  - `datetime.timedelta`
  - `models.ParsedTransaction`
  - `typing.List`
  - `typing.Optional`

#### 🔹 `deduplicate_in_memory`

```python
def deduplicate_in_memory( self, transactions: List[ParsedTransaction],
```

**Description**: Deduplicate against a provided set of checksums.

- **Ligne**: 211
- **Réutilisabilité**: High
- **Type de retour**: `DeduplicationResult`
- **Paramètres**:
  - `self`
  - `transactions`: `List[ParsedTransaction]`
  - `existing_checksums`: `Set[str]`
- **Dépendances**:
  - `models.ParsedTransaction`
  - `typing.List`
  - `typing.Set`

#### 🔹 `__init__`

```python
def __init__(self, engine: Optional[Engine] = None):
```

- **Ligne**: 240
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `engine`: `Optional[Engine]` = `None`
- **Dépendances**:
  - `datetime.date`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `sqlalchemy.engine.Engine`
  - `typing.List`
  - *... et 2 autres*

#### 🔹 `is_near_duplicate`

```python
def is_near_duplicate(self, txn: ParsedTransaction) -> bool:
```

**Description**: Check if transaction is a near-duplicate.

- **Ligne**: 281
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `txn`: `ParsedTransaction`
- **Dépendances**:
  - `models.ParsedTransaction`

#### 🔹 `_similar_libelle`

```python
def _similar_libelle(self, lib1: str, lib2: str) -> bool:
```

**Description**: Check if two libelles are similar.

- **Ligne**: 302
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `lib1`: `str`
  - `lib2`: `str`

#### 🔸 `deduplicate_transactions`

```python
def deduplicate_transactions( transactions: List[ParsedTransaction],
```

**Description**: Convenience function for deduplication.

- **Ligne**: 332
- **Réutilisabilité**: High
- **Type de retour**: `Tuple[List[ParsedTransaction], List[ParsedTransaction]]`
- **Paramètres**:
  - `transactions`: `List[ParsedTransaction]`
  - `existing_checksums`: `Set[str]`
- **Dépendances**:
  - `models.ParsedTransaction`
  - `typing.List`
  - `typing.Set`
  - `typing.Tuple`

### `core/bank_import/detector.py`

#### 🔹 `is_confident`

```python
def is_confident(self) -> bool:
```

**Description**: Return True if detection confidence is high enough.

- **Ligne**: 36
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `to_dict`

```python
def to_dict(self) -> dict:
```

**Description**: Convert to dictionary for JSON serialization.

- **Ligne**: 40
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `self`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 143
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `models.BankType`

### `core/bank_import/extractor.py`

#### 🔹 `__init__`

```python
def __init__(self, pdftotext_path: str = "pdftotext"):
```

- **Ligne**: 90
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `pdftotext_path`: `str` = `'pdftotext'`

#### 🔹 `_make_date`

```python
def _make_date(d: str, m: str, y: str) -> date:
```

- **Ligne**: 286
- **Réutilisabilité**: Medium
- **Type de retour**: `date`
- **Paramètres**:
  - `d`: `str`
  - `m`: `str`
  - `y`: `str`
- **Dépendances**:
  - `dataclasses.dataclass`
  - `datetime.date`
  - `models.BankType`
  - `models.StatementPeriod`
  - `sys`
  - *... et 3 autres*

#### 🔹 `_split_pages` 🎀

```python
def _split_pages(self, lines: List[str]) -> List[ExtractedPage]:
```

**Description**: Split text into pages based on form feed characters.

- **Ligne**: 299
- **Réutilisabilité**: High
- **Type de retour**: `List[ExtractedPage]`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
- **Dépendances**:
  - `typing.List`

### `core/bank_import/models.py`

#### 🔹 `__str__`

```python
def __str__(self) -> str:
```

- **Ligne**: 54
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`

#### 🔹 `overlaps`

```python
def overlaps(self, other: "StatementPeriod") -> bool:
```

**Description**: Check if this period overlaps with another.

- **Ligne**: 57
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `other`: `'StatementPeriod'`

#### 🔹 `is_valid`

```python
def is_valid(self) -> bool:
```

**Description**: Verify balance equation: opening + credits - debits = closing.

- **Ligne**: 88
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔹 `net_movement`

```python
def net_movement(self) -> Decimal:
```

**Description**: Net movement during the period.

- **Ligne**: 94
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔹 `montant_signe`

```python
def montant_signe(self) -> Decimal:
```

**Description**: Signed amount (positive for IN, negative for OUT).

- **Ligne**: 147
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔹 `transaction_count`

```python
def transaction_count(self) -> int:
```

**Description**: Number of transactions.

- **Ligne**: 197
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `has_errors`

```python
def has_errors(self) -> bool:
```

**Description**: Check if there were any errors.

- **Ligne**: 237
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `duration_seconds`

```python
def duration_seconds(self) -> Optional[float]:
```

**Description**: Import duration in seconds.

- **Ligne**: 242
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[float]`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Optional`

#### 🔹 `to_dict`

```python
def to_dict(self) -> Dict[str, Any]:
```

**Description**: Convert to dictionary for JSON serialization.

- **Ligne**: 248
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

#### 🔹 `for_bnp`

```python
def for_bnp(cls) -> "ColumnPositions":
```

**Description**: BNP bank column positions.

- **Ligne**: 302
- **Réutilisabilité**: Medium
- **Type de retour**: `'ColumnPositions'`
- **Décorateurs**: `classmethod`
- **Paramètres**:
  - `cls`

### `core/bank_import/orchestrator.py`

#### 🔹 `_process_statement` 🎀

```python
def _process_statement( self, statement: ParsedStatement,
```

**Description**: Process a single parsed statement.

- **Ligne**: 206
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `self`
  - `statement`: `ParsedStatement`
  - `account_id`: `int`
  - `source_file`: `str`
  - `bank_type`: `Optional[BankType]` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `categorizer.TransactionCategorizer`
  - `datetime.datetime`
  - `decimal.Decimal`
  - `deduplicator.TransactionDeduplicator`
  - *... et 14 autres*

#### 🔹 `_finalize_result` 🎀

```python
def _finalize_result(self, result: ImportResult) -> ImportResult:
```

**Description**: Finalize import result.

- **Ligne**: 546
- **Réutilisabilité**: High
- **Type de retour**: `ImportResult`
- **Paramètres**:
  - `self`
  - `result`: `ImportResult`
- **Dépendances**:
  - `datetime.datetime`
  - `models.ImportResult`

### `core/bank_import/parser.py`

#### 🔹 `bank_type`

```python
def bank_type(self) -> BankType:
```

**Description**: Retourne le type de banque géré par ce parseur.

- **Ligne**: 46
- **Réutilisabilité**: Medium
- **Type de retour**: `BankType`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `models.BankType`

#### 🔹 `bank_type`

```python
def bank_type(self) -> BankType:
```

**Description**: Return the bank type this parser handles.

- **Ligne**: 101
- **Réutilisabilité**: Medium
- **Type de retour**: `BankType`
- **Décorateurs**: `property`, `abstractmethod`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `abc.abstractmethod`
  - `models.BankType`

#### 🔹 `__init__`

```python
def __init__( self, config: Optional[ParserConfig] = None,
```

- **Ligne**: 244
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `config`: `Optional[ParserConfig]` = `None`
  - `bank_type`: `Optional[BankType]` = `None`
- **Dépendances**:
  - `logging`
  - `models.BankType`
  - `typing.Optional`

#### 🔹 `bank_type`

```python
def bank_type(self) -> BankType:
```

**Description**: Return the bank type this parser is configured for.

- **Ligne**: 254
- **Réutilisabilité**: Medium
- **Type de retour**: `BankType`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `models.BankType`

#### 🔹 `can_parse`

```python
def can_parse(self, text: str) -> bool:
```

**Description**: Check if this parser can handle the given text.

- **Ligne**: 258
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `text`: `str`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `parse` 🎀

```python
def parse( self, lines: List[str],
```

**Description**: Analyse les lignes pour constituer un relevé complet.

- **Ligne**: 268
- **Réutilisabilité**: Medium
- **Type de retour**: `ParsedStatement`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
  - `bank_type`: `BankType` = `BankType.LCL`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 15 autres*

#### 🔹 `_extract_balance`

```python
def _extract_balance( self, lines: List[str],
```

**Description**: Extrait les informations de solde depuis le relevé.

- **Ligne**: 422
- **Réutilisabilité**: Low
- **Type de retour**: `Optional[StatementBalance]`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `bank_type`: `BankType` = `BankType.LCL`
- **Dépendances**:
  - `abc.abstractmethod`
  - `models.BalanceType`
  - `models.BankType`
  - `models.StatementBalance`
  - `typing.List`
  - *... et 1 autres*

#### 🔹 `_is_header_line`

```python
def _is_header_line(self, line: str) -> bool:
```

**Description**: Vérifie si la ligne correspond à un en-tête ou des métadonnées.

- **Ligne**: 940
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `line`: `str`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `_generate_checksum`

```python
def _generate_checksum( self, op_date: date,
```

**Description**: Génère un checksum unique pour le dédoublonnage.

- **Ligne**: 945
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `op_date`: `date`
  - `libelle`: `str`
  - `montant`: `Decimal`
  - `direction`: `TransactionDirection`
- **Dépendances**:
  - `abc.abstractmethod`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 3 autres*

#### 🔹 `register`

```python
def register(self, bank_type: BankType, parser_class: type) -> None:
```

**Description**: Enregistre une classe de parseur pour un type de banque.

- **Ligne**: 1142
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `bank_type`: `BankType`
  - `parser_class`: `type`
- **Dépendances**:
  - `models.BankType`

### `core/bank_import/validator.py`

#### 🔹 `validate`

```python
def validate(self, statement: ParsedStatement) -> ValidationResult:
```

**Description**: Validate statement balance.

- **Ligne**: 47
- **Réutilisabilité**: Medium
- **Type de retour**: `ValidationResult`
- **Paramètres**:
  - `self`
  - `statement`: `ParsedStatement`
- **Dépendances**:
  - `decimal.Decimal`
  - `models.BalanceType`
  - `models.ParsedStatement`
  - `models.TransactionDirection`
  - `typing.List`

#### 🔹 `quick_check`

```python
def quick_check(self, statement: ParsedStatement) -> bool:
```

**Description**: Quick validation check without detailed results.

- **Ligne**: 177
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `statement`: `ParsedStatement`
- **Dépendances**:
  - `models.ParsedStatement`

### `core/catalog_repository.py`

#### 🔹 `list_active_products`

```python
def list_active_products(self, tenant_id: int) -> list[ProductSummary]:
```

- **Ligne**: 17
- **Réutilisabilité**: High
- **Type de retour**: `list[ProductSummary]`
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`

#### 🔹 `find_product`

```python
def find_product(self, identifier: str | int, tenant_id: int) -> ProductSummary | None:
```

- **Ligne**: 20
- **Réutilisabilité**: High
- **Type de retour**: `ProductSummary | None`
- **Paramètres**:
  - `self`
  - `identifier`: `str | int`
  - `tenant_id`: `int`

### `core/catalog_sql_repository.py`

#### 🔹 `list_active_products`

```python
def list_active_products(self, tenant_id: int) -> list[ProductSummary]:
```

- **Ligne**: 11
- **Réutilisabilité**: High
- **Type de retour**: `list[ProductSummary]`
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`
- **Dépendances**:
  - `catalog_repository.ProductSummary`
  - `data_repository.query_df`
  - `sqlalchemy.text`

#### 🔹 `find_product`

```python
def find_product(self, identifier: str | int, tenant_id: int) -> ProductSummary | None:
```

- **Ligne**: 32
- **Réutilisabilité**: High
- **Type de retour**: `ProductSummary | None`
- **Paramètres**:
  - `self`
  - `identifier`: `str | int`
  - `tenant_id`: `int`
- **Dépendances**:
  - `catalog_repository.ProductSummary`
  - `data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

### `core/consolidation_loader.py`

#### 🔸 `sync_invoice_dataframe` 🎀

```python
def sync_invoice_dataframe( invoice_df: pd.DataFrame,
```

**Description**: Synchronise un DataFrame de facture vers les tables dimensionnelles.

- **Ligne**: 183
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, int]`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `json`
  - `sqlalchemy.text`

### `core/data_repository.py`

#### 🔸 `query_df`

```python
def query_df(sql: str | ClauseElement, params=None) -> pd.DataFrame:
```

**Description**: Exécute une requête SELECT et retourne le résultat sous forme de DataFrame Pandas.

- **Ligne**: 44
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `sql`: `str | ClauseElement`
  - `params` = `None`
- **Dépendances**:
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`
  - `sqlalchemy.sql.elements.ClauseElement`
  - `sqlalchemy.sql.elements.TextClause`
  - `sqlalchemy.text`

#### 🔸 `exec_sql`

```python
def exec_sql(sql: str | ClauseElement, params=None) -> None:
```

**Description**: Exécute une requête d'écriture (INSERT, UPDATE, DELETE).

- **Ligne**: 80
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `sql`: `str | ClauseElement`
  - `params` = `None`
- **Dépendances**:
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`
  - `sqlalchemy.sql.elements.ClauseElement`
  - `sqlalchemy.sql.elements.TextClause`
  - `sqlalchemy.text`

#### 🔸 `exec_sql_return_id`

```python
def exec_sql_return_id(sql: str | ClauseElement, params=None):
```

**Description**: Exécute une requête et retourne l'ID (via RETURNING id).

- **Ligne**: 97
- **Réutilisabilité**: High
- **Paramètres**:
  - `sql`: `str | ClauseElement`
  - `params` = `None`
- **Dépendances**:
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`
  - `sqlalchemy.sql.elements.ClauseElement`
  - `sqlalchemy.sql.elements.TextClause`
  - `sqlalchemy.text`

### `core/event_handlers.py`

#### 🔸 `handle_invoice_imported`

```python
def handle_invoice_imported(event: Event):
```

**Description**: Handler: Facture importée

- **Ligne**: 115
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `event`: `Event`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `core.finance.event_sourcing.Event`
  - `core.finance.event_sourcing.EventDispatcher`
  - *... et 6 autres*

#### 🔸 `handle_stock_movement`

```python
def handle_stock_movement(event: Event):
```

**Description**: Handler: Mouvement de stock

- **Ligne**: 157
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `event`: `Event`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `core.finance.event_sourcing.Event`
  - `core.finance.event_sourcing.EventDispatcher`
  - *... et 6 autres*

#### 🔸 `handle_price_updated`

```python
def handle_price_updated(event: Event):
```

**Description**: Handler: Prix mis à jour

- **Ligne**: 236
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `event`: `Event`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `core.finance.event_sourcing.Event`
  - `core.finance.event_sourcing.EventDispatcher`
  - *... et 6 autres*

#### 🔸 `handle_bank_transaction_categorized`

```python
def handle_bank_transaction_categorized(event: Event):
```

**Description**: Handler: Transaction bancaire catégorisée

- **Ligne**: 291
- **Réutilisabilité**: High
- **Paramètres**:
  - `event`: `Event`
- **Dépendances**:
  - `core.finance.event_sourcing.Event`
  - `core.finance.event_sourcing.EventDispatcher`
  - `core.finance.event_sourcing.EventStore`
  - `core.finance.event_sourcing.EventType`

#### 🔸 `handle_reconciliation_matched`

```python
def handle_reconciliation_matched(event: Event):
```

**Description**: Handler: Rapprochement bancaire réussi

- **Ligne**: 310
- **Réutilisabilité**: High
- **Paramètres**:
  - `event`: `Event`
- **Dépendances**:
  - `core.finance.event_sourcing.Event`
  - `core.finance.event_sourcing.EventDispatcher`
  - `core.finance.event_sourcing.EventStore`
  - `core.finance.event_sourcing.EventType`

#### 🔸 `register_all_handlers`

```python
def register_all_handlers():
```

**Description**: Enregistre tous les handlers auprès de l'EventStore.

- **Ligne**: 335
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `core.finance.event_sourcing.EventStore`
  - `core.finance.event_sourcing.EventType`

#### 🔸 `unregister_all_handlers`

```python
def unregister_all_handlers():
```

**Description**: Désenregistre tous les handlers (pour tests).

- **Ligne**: 355
- **Réutilisabilité**: Medium

### `core/import_analyzer.py`

#### 🔹 `coverage_rate`

```python
def coverage_rate(self) -> float:
```

- **Ligne**: 31
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `non_zero_rate`

```python
def non_zero_rate(self) -> float:
```

- **Ligne**: 35
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `to_dict`

```python
def to_dict(self) -> dict:
```

- **Ligne**: 83
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `dataclasses.asdict`

#### 🔹 `to_json`

```python
def to_json(self, indent: int = 2) -> str:
```

- **Ligne**: 86
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `indent`: `int` = `2`
- **Dépendances**:
  - `json`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 98
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`

#### 🔹 `analyze_dataframe` 🎀

```python
def analyze_dataframe( self, df: pd.DataFrame,
```

**Description**: Analyse un DataFrame et génère un rapport de qualité.

- **Ligne**: 101
- **Réutilisabilité**: Medium
- **Type de retour**: `ImportAnalysisReport`
- **Paramètres**:
  - `self`
  - `df`: `pd.DataFrame`
  - `source_file`: `str`
  - `source_type`: `str` = `'invoice'`
  - `quantity_columns`: `Sequence[str] | None` = `None`
  - `amount_columns`: `Sequence[str] | None` = `None`
- **Dépendances**:
  - `typing.Sequence`

#### 🔹 `analyze_bank_transactions` 🎀

```python
def analyze_bank_transactions( self, df: pd.DataFrame,
```

**Description**: Analyse des transactions bancaires avec catégorisation.

- **Ligne**: 204
- **Réutilisabilité**: High
- **Type de retour**: `ImportAnalysisReport`
- **Paramètres**:
  - `self`
  - `df`: `pd.DataFrame`
  - `source_file`: `str`
  - `categorizer_func` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `dataclasses.asdict`

#### 🔹 `_analyze_field_coverage` 🎀

```python
def _analyze_field_coverage(self, df: pd.DataFrame, column: str) -> FieldCoverage:
```

**Description**: Analyse la couverture d'un champ.

- **Ligne**: 243
- **Réutilisabilité**: High
- **Type de retour**: `FieldCoverage`
- **Paramètres**:
  - `self`
  - `df`: `pd.DataFrame`
  - `column`: `str`

#### 🔹 `_analyze_numeric_field` 🎀

```python
def _analyze_numeric_field( self, df: pd.DataFrame, column: str, field_type: str
```

**Description**: Analyse un champ numérique.

- **Ligne**: 263
- **Réutilisabilité**: Medium
- **Type de retour**: `NumericStats`
- **Paramètres**:
  - `self`
  - `df`: `pd.DataFrame`
  - `column`: `str`
  - `field_type`: `str`

#### 🔹 `generate_summary_report`

```python
def generate_summary_report(self) -> dict:
```

**Description**: Génère un rapport de synthèse de tous les imports analysés.

- **Ligne**: 344
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `__future__.annotations`
  - `dataclasses.asdict`

#### 🔸 `analyze_invoice_import`

```python
def analyze_invoice_import( df: pd.DataFrame,
```

**Description**: Fonction helper pour analyser un import de facture.

- **Ligne**: 388
- **Réutilisabilité**: High
- **Type de retour**: `ImportAnalysisReport`
- **Paramètres**:
  - `df`: `pd.DataFrame`
  - `source_file`: `str`

#### 🔸 `analyze_bank_import`

```python
def analyze_bank_import( df: pd.DataFrame,
```

**Description**: Fonction helper pour analyser un import bancaire.

- **Ligne**: 410
- **Réutilisabilité**: High
- **Type de retour**: `ImportAnalysisReport`
- **Paramètres**:
  - `df`: `pd.DataFrame`
  - `source_file`: `str`
  - `categorizer_func` = `None`

### `core/inventory_classification.py`

#### 🔸 `classify_inventory`

```python
def classify_inventory(*, tenant_id: int = 1) -> dict[str, int]:
```

- **Ligne**: 111
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, int]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

### `core/inventory_costing.py`

#### 🔸 `consume_layers`

```python
def consume_layers( conn, *, tenant_id: int,
```

- **Ligne**: 127
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `conn`
- **Dépendances**:
  - `decimal.Decimal`
  - `sqlalchemy.text`

### `core/product_input.py`

#### 🔹 `as_dict`

```python
def as_dict(self) -> Dict[str, Any]:
```

- **Ligne**: 18
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

#### 🔸 `from_row`

```python
def from_row(row: Dict[str, Any]) -> ProductInput:
```

- **Ligne**: 33
- **Réutilisabilité**: High
- **Type de retour**: `ProductInput`
- **Paramètres**:
  - `row`: `Dict[str, Any]`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

### `core/products_loader.py`

#### 🔸 `determine_categorie` 🎀

```python
def determine_categorie(nom_produit: Any, fournisseur: str | None = None, code: str | None = None) -> str:
```

**Description**: Détermine la catégorie METRO à partir du nom, fournisseur ou code du produit.

- **Ligne**: 312
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `nom_produit`: `Any`
  - `fournisseur`: `str | None` = `None`
  - `code`: `str | None` = `None`
- **Dépendances**:
  - `typing.Any`
  - `unicodedata`

#### 🔸 `process_products_file` 🎀

```python
def process_products_file(csv_path: str) -> Dict[str, Any]:
```

**Description**: Lit un fichier CSV puis délègue le traitement à :func:`load_products_from_df`.

- **Ligne**: 957
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `csv_path`: `str`
- **Dépendances**:
  - `sqlalchemy.exc`
  - `typing.Any`
  - `typing.Dict`

### `core/settings.py`

#### 🔹 `load`

```python
def load() -> "AppSettings":
```

- **Ligne**: 26
- **Réutilisabilité**: Medium
- **Type de retour**: `'AppSettings'`
- **Décorateurs**: `staticmethod`
- **Dépendances**:
  - `os`

---

## Business Logic

**96 fonctions**

### `backend/services/admin.py`

#### 🔸 `fetch_table_counts`

```python
def fetch_table_counts(*, tenant_id: int) -> list[dict[str, Any]]:
```

- **Ligne**: 37
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.backup_manager.list_backups`
  - `core.user_service.list_users`
  - `typing.Any`

#### 🔸 `fetch_stock_diagnostics`

```python
def fetch_stock_diagnostics(*, tenant_id: int, limit: int = 50) -> list[dict[str, Any]]:
```

- **Ligne**: 48
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.backup_manager.list_backups`
  - `core.user_service.list_users`
  - `typing.Any`

#### 🔸 `fetch_recent_movements`

```python
def fetch_recent_movements(*, tenant_id: int, limit: int = 20) -> list[dict[str, Any]]:
```

- **Ligne**: 81
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.backup_manager.list_backups`
  - `core.data_repository.query_df`
  - `core.user_service.list_users`
  - `typing.Any`

#### 🔸 `fetch_table_preview`

```python
def fetch_table_preview(table_name: str, limit: int = 50) -> list[dict[str, Any]]:
```

- **Ligne**: 103
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `table_name`: `str`
  - `limit`: `int` = `50`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.backup_manager.list_backups`
  - `core.user_service.list_users`
  - `typing.Any`

#### 🔸 `serialize_backup`

```python
def serialize_backup(metadata) -> dict[str, Any]:
```

- **Ligne**: 110
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `metadata`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `serialize_binary_status`

```python
def serialize_binary_status(status: BinaryStatus) -> dict[str, Any]:
```

- **Ligne**: 119
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `status`: `BinaryStatus`
- **Dépendances**:
  - `core.backup_manager.BinaryStatus`
  - `typing.Any`

#### 🔸 `fetch_backup_overview`

```python
def fetch_backup_overview() -> dict[str, Any]:
```

- **Ligne**: 129
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `core.backup_manager.build_backup_timeline`
  - `core.backup_manager.check_backup_tools`
  - `core.backup_manager.compute_backup_statistics`
  - `core.backup_manager.list_backups`
  - `core.backup_manager.load_backup_settings`
  - *... et 4 autres*

#### 🔸 `fetch_admin_overview`

```python
def fetch_admin_overview(*, tenant_id: int) -> dict[str, Any]:
```

- **Ligne**: 170
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `typing.Any`

#### 🔸 `list_admin_users`

```python
def list_admin_users() -> list[dict[str, Any]]:
```

- **Ligne**: 179
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.backup_manager.list_backups`
  - `core.backup_manager.plan_next_backup`
  - `core.data_repository.query_df`
  - `core.user_service.list_users`
  - `typing.Any`

#### 🔸 `update_role`

```python
def update_role(user_id: int, role: str) -> None:
```

- **Ligne**: 189
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `user_id`: `int`
  - `role`: `str`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.user_service.update_user_role`

#### 🔸 `reset_password`

```python
def reset_password(user_id: int, new_password: str | None = None) -> str:
```

- **Ligne**: 193
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `user_id`: `int`
  - `new_password`: `str | None` = `None`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.user_service.reset_user_password`

#### 🔸 `save_settings` 🎀

```python
def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
```

- **Ligne**: 197
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.backup_manager.save_backup_settings`
  - `typing.Any`

#### 🔸 `create_backup_now`

```python
def create_backup_now(label: str | None = None) -> dict[str, Any]:
```

- **Ligne**: 214
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `label`: `str | None` = `None`
- **Dépendances**:
  - `core.backup_manager.create_backup`
  - `typing.Any`

#### 🔸 `restore_backup_file`

```python
def restore_backup_file(filename: str) -> None:
```

- **Ligne**: 219
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `core.backup_manager.restore_backup`

#### 🔸 `delete_backup_file`

```python
def delete_backup_file(filename: str) -> None:
```

- **Ligne**: 223
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `core.backup_manager.delete_backup`

#### 🔸 `run_integrity_report` 🎀

```python
def run_integrity_report() -> list[dict[str, Any]]:
```

- **Ligne**: 227
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.backup_manager.integrity_report`
  - `core.backup_manager.list_backups`
  - `core.user_service.list_users`
  - `datetime.datetime`
  - `typing.Any`

### `backend/services/audit.py`

#### 🔸 `list_diagnostics`

```python
def list_diagnostics( *, categories: Iterable[str] | None = None,
```

- **Ligne**: 94
- **Réutilisabilité**: Low
- **Type de retour**: `dict[str, object]`
- **Dépendances**:
  - `backend.services.catalog_data.fetch_customer_catalog`
  - `typing.Iterable`
  - `typing.List`

#### 🔸 `list_actions`

```python
def list_actions(*, include_closed: bool = False, tenant_id: int = 1) -> list[dict[str, object]]:
```

- **Ligne**: 203
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, object]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`

#### 🔸 `list_resolution_log`

```python
def list_resolution_log(limit: int = 100, *, tenant_id: int = 1) -> list[dict[str, object]]:
```

- **Ligne**: 242
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, object]]`
- **Paramètres**:
  - `limit`: `int` = `100`
- **Dépendances**:
  - `core.data_repository.query_df`

#### 🔸 `create_assignment`

```python
def create_assignment( *, product_id: int,
```

- **Ligne**: 260
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `sqlalchemy.text`

#### 🔸 `update_action_status`

```python
def update_action_status( *, action_id: int,
```

- **Ligne**: 311
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/capital.py`

#### 🔸 `build_capital_overview`

```python
def build_capital_overview(limit_latest_prices: int = 20) -> dict[str, object]:
```

- **Ligne**: 162
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Paramètres**:
  - `limit_latest_prices`: `int` = `20`
- **Dépendances**:
  - `core.price_history_service.fetch_latest_price_per_code`
  - `datetime.datetime`
  - `decimal.Decimal`

#### 🔸 `persist_daily_snapshot`

```python
def persist_daily_snapshot(snapshot_date: datetime | None = None) -> None:
```

- **Ligne**: 222
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `snapshot_date`: `datetime | None` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.datetime`
  - `sqlalchemy.text`

### `backend/services/catalog.py`

#### 🔸 `list_products_page`

```python
def list_products_page( tenant_id: int,
```

- **Ligne**: 63
- **Réutilisabilité**: Medium
- **Type de retour**: `Tuple[list[dict[str, Any]], int]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Tuple`

#### 🔸 `get_product` 🎀

```python
def get_product(product_id: int, tenant_id: int) -> dict[str, Any]:
```

- **Ligne**: 118
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `product_id`: `int`
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `create_product` 🎀

```python
def create_product( payload: dict[str, Any],
```

- **Ligne**: 131
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.product_service.parse_barcode_input`
  - `core.products_loader.insert_or_update_barcode`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `update_product`

```python
def update_product( product_id: int,
```

- **Ligne**: 159
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `product_id`: `int`
  - `changes`: `dict[str, Any]`
  - `codes`: `Iterable[str] | None` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.product_service.parse_barcode_input`
  - `core.products_loader.insert_or_update_barcode`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `delete_product`

```python
def delete_product(product_id: int, *, tenant_id: int) -> None:
```

- **Ligne**: 204
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `product_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔸 `get_product_by_barcode` 🎀

```python
def get_product_by_barcode(barcode: str, *, tenant_id: int) -> dict[str, Any]:
```

- **Ligne**: 214
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `barcode`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.product_service.parse_barcode_input`
  - `core.products_loader.insert_or_update_barcode`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_categories`

```python
def list_categories(*, tenant_id: int) -> list[dict[str, Any]]:
```

**Description**: Liste toutes les categories distinctes de produits.

- **Ligne**: 242
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_vendors`

```python
def list_vendors(*, tenant_id: int) -> list[dict[str, Any]]:
```

**Description**: Liste tous les fournisseurs depuis processed_invoices ou restaurant_fournisseurs.

- **Ligne**: 260
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

### `backend/services/catalog_data.py`

#### 🔸 `fetch_customer_catalog` 🎀

```python
def fetch_customer_catalog(*, tenant_id: int = 1) -> pd.DataFrame:
```

**Description**: Retourne le catalogue actif enrichi des ventes glissantes et du code-barres principal.

- **Ligne**: 88
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Dépendances**:
  - `core.data_repository.query_df`

#### 🔸 `fetch_recent_suppliers` 🎀

```python
def fetch_recent_suppliers(*, tenant_id: int = 1) -> pd.DataFrame:
```

**Description**: Retourne la dernière source de mouvement entrant par produit.

- **Ligne**: 135
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Dépendances**:
  - `core.data_repository.query_df`

### `backend/services/dashboard.py`

#### 🔸 `fetch_kpis`

```python
def fetch_kpis(tenant_id: int) -> dict[str, float | int]:
```

- **Ligne**: 13
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, float | int]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`

#### 🔸 `fetch_top_stock_value`

```python
def fetch_top_stock_value(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
```

**Description**: Top produits par valeur de stock (prix_achat * stock_actuel).

- **Ligne**: 56
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `fetch_top_sales`

```python
def fetch_top_sales(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
```

- **Ligne**: 72
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `fetch_status_distribution`

```python
def fetch_status_distribution(*, tenant_id: int) -> List[dict[str, Any]]:
```

- **Ligne**: 88
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `fetch_supplier_breakdown`

```python
def fetch_supplier_breakdown(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
```

- **Ligne**: 106
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `fetch_weekly_variation`

```python
def fetch_weekly_variation(*, tenant_id: int, weeks: int = 8) -> List[dict[str, Any]]:
```

- **Ligne**: 126
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `fetch_margin_alerts`

```python
def fetch_margin_alerts(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
```

- **Ligne**: 145
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `fetch_dashboard_metrics`

```python
def fetch_dashboard_metrics(*, tenant_id: int) -> dict[str, Any]:
```

- **Ligne**: 164
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `typing.Any`

### `backend/services/importers/bank_statement_csv.py`

#### 🔸 `parse_csv` 🎀

```python
def parse_csv(content: bytes | str) -> list[dict[str, Any]]:
```

**Description**: Parse un contenu CSV en liste de mouvements normalisés.

- **Ligne**: 58
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `content`: `bytes | str`
- **Dépendances**:
  - `__future__.annotations`
  - `csv`
  - `io`
  - `typing.Any`

#### 🔸 `import_csv`

```python
def import_csv(content: bytes | str, account_id: int, *, source: str = "CSV") -> dict[str, int]:
```

**Description**: Insère un CSV dans finance_bank_statements/lines avec dédoublonnage.

- **Ligne**: 92
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, int]`
- **Paramètres**:
  - `content`: `bytes | str`
  - `account_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `datetime.date`
  - `hashlib`
  - *... et 1 autres*

#### 🔸 `import_pdf_best_effort`

```python
def import_pdf_best_effort( path: str | Path,
```

**Description**: Importe un PDF via le workflow unifié core.bank_import.

- **Ligne**: 221
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, int]`
- **Paramètres**:
  - `path`: `str | Path`
  - `account_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `pathlib.Path`
  - `sqlalchemy.text`

### `backend/services/maintenance.py`

#### 🔸 `list_backups` 🎀

```python
def list_backups(limit: int | None = None) -> list[dict[str, object]]:
```

- **Ligne**: 11
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, object]]`
- **Paramètres**:
  - `limit`: `int | None` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timezone`
  - `pathlib.Path`

### `backend/services/product_matching.py`

#### 🔸 `get_fuzzy_product_matches` 🎀

```python
def get_fuzzy_product_matches( query: str,
```

**Description**: Trouve les produits correspondant à une requête via correspondance floue.

- **Ligne**: 16
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `query`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.query_df`
  - `rapidfuzz.fuzz`
  - `rapidfuzz.process`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `get_best_product_match`

```python
def get_best_product_match( query: str,
```

**Description**: Retourne le meilleur match flou pour une requête produit.

- **Ligne**: 133
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any] | None`
- **Paramètres**:
  - `query`: `str`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `enrich_lines_with_fuzzy_matches` 🎀

```python
def enrich_lines_with_fuzzy_matches( lines: list[dict[str, Any]],
```

**Description**: Enrichit les lignes de facture avec des suggestions de matching flou.

- **Ligne**: 162
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `lines`: `list[dict[str, Any]]`
- **Dépendances**:
  - `typing.Any`

### `backend/services/reports.py`

#### 🔸 `fetch_report_kpis`

```python
def fetch_report_kpis(*, tenant_id: int) -> dict[str, float | int]:
```

**Description**: Récupère les KPI principaux affichés sur le dashboard (totaux, alertes, stock négatif).

- **Ligne**: 21
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, float | int]`
- **Dépendances**:
  - `core.data_repository.query_df`

#### 🔸 `fetch_category_breakdown`

```python
def fetch_category_breakdown(*, tenant_id: int, limit: int = 50) -> list[dict[str, Any]]:
```

**Description**: Agrège le stock par catégorie pour prioriser les familles les plus valorisées.

- **Ligne**: 64
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `fetch_top_value`

```python
def fetch_top_value(*, tenant_id: int, limit: int = 10) -> list[dict[str, Any]]:
```

**Description**: Retourne les articles les plus coûteux en valeur d'achat immobilisée.

- **Ligne**: 83
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `fetch_low_stock`

```python
def fetch_low_stock(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
```

**Description**: Liste les produits passés sous leur seuil d'alerte.

- **Ligne**: 102
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `fetch_negative_stock`

```python
def fetch_negative_stock(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
```

**Description**: Identifie les stocks négatifs, symptôme d'écarts ou de ventes non comptabilisées.

- **Ligne**: 122
- **Réutilisabilité**: High
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `fetch_rotation`

```python
def fetch_rotation(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
```

**Description**: Calcule la rotation sur 30 jours à partir des mouvements d'entrées/sorties.

- **Ligne**: 142
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `fetch_supplier_inflows`

```python
def fetch_supplier_inflows(*, tenant_id: int, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
```

**Description**: Classe les fournisseurs ayant injecté le plus de valeur sur la période choisie.

- **Ligne**: 171
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Any`

#### 🔸 `fetch_latest_capital_snapshot`

```python
def fetch_latest_capital_snapshot(*, tenant_id: int) -> dict[str, object]:
```

**Description**: Récupère la dernière photographie des actifs (stock + banques + caisse).

- **Ligne**: 196
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Dépendances**:
  - `core.data_repository.query_df`

#### 🔸 `build_overview`

```python
def build_overview(*, tenant_id: int) -> dict[str, Any]:
```

**Description**: Assemble toutes les sections du rapport consolidé consommé par la SPA.

- **Ligne**: 219
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `export_dataset`

```python
def export_dataset(report_type: str, limit: int, *, tenant_id: int) -> Tuple[str, bytes]:
```

**Description**: Retourne (filename, csv_bytes) pour le dataset sélectionné.

- **Ligne**: 337
- **Réutilisabilité**: High
- **Type de retour**: `Tuple[str, bytes]`
- **Paramètres**:
  - `report_type`: `str`
  - `limit`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `typing.Tuple`

### `backend/services/stock.py`

#### 🔸 `fetch_movement_timeseries` 🎀

```python
def fetch_movement_timeseries( window_days: int = 30,
```

**Description**: Récupère les mouvements de stock groupés par jour.

- **Ligne**: 13
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `window_days`: `int` = `30`
  - `product_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔸 `fetch_recent_movements` 🎀

```python
def fetch_recent_movements( limit: int = 100,
```

- **Ligne**: 57
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `limit`: `int` = `100`
  - `product_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Optional`

#### 🔸 `adjust_stock_level`

```python
def adjust_stock_level( product_id: int,
```

- **Ligne**: 90
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, object]`
- **Paramètres**:
  - `product_id`: `int`
  - `target_quantity`: `float`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `backend/services/supply.py`

#### 🔸 `compute_supply_plan`

```python
def compute_supply_plan( target_coverage: int = 21,
```

**Description**: Retourne le plan d'approvisionnement dynamique aligné sur l'ancienne vue Streamlit.

- **Ligne**: 36
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Paramètres**:
  - `target_coverage`: `int` = `21`
  - `alert_threshold`: `int` = `7`
  - `min_daily_sales`: `float` = `0.0`
  - `categories`: `Iterable[str] | None` = `None`
  - `search`: `str | None` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.catalog_data.fetch_customer_catalog`
  - `backend.services.catalog_data.fetch_recent_suppliers`
  - `core.inventory_forecast.forecast_daily_consumption`
  - `typing.Iterable`
  - *... et 1 autres*

### `backend/services/zero_click_jobs.py`

#### 🔸 `create_job`

```python
def create_job( job_id: str,
```

**Description**: Crée un nouveau job zero-click en base de données.

- **Ligne**: 16
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `job_id`: `str`
  - `tenant_id`: `int`
  - `filename`: `str | None` = `None`
  - `supplier_hint`: `str | None` = `None`
  - `margin_percent`: `float` = `40.0`
  - `auto_confirm`: `bool` = `True`
  - `session_id`: `str | None` = `None`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_job_status`

```python
def update_job_status( job_id: str,
```

**Description**: Met à jour le statut d'un job.

- **Ligne**: 62
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `job_id`: `str`
  - `status`: `str`
  - `result`: `dict[str, Any] | None` = `None`
  - `error`: `str | None` = `None`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `datetime.datetime`
  - `datetime.timezone`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `get_job`

```python
def get_job(job_id: str, tenant_id: int | None = None) -> dict[str, Any] | None:
```

**Description**: Récupère un job par son ID.

- **Ligne**: 103
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any] | None`
- **Paramètres**:
  - `job_id`: `str`
  - `tenant_id`: `int | None` = `None`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_jobs`

```python
def list_jobs( tenant_id: int,
```

**Description**: Liste les jobs d'un tenant avec filtres optionnels.

- **Ligne**: 146
- **Réutilisabilité**: Medium
- **Type de retour**: `tuple[list[dict[str, Any]], int]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `status`: `str | None` = `None`
  - `session_id`: `str | None` = `None`
  - `limit`: `int` = `50`
  - `offset`: `int` = `0`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `json`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `delete_old_jobs`

```python
def delete_old_jobs(days: int = 30) -> int:
```

**Description**: Supprime les jobs terminés de plus de N jours.

- **Ligne**: 215
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `days`: `int` = `30`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `sqlalchemy.text`

#### 🔸 `list_import_sessions`

```python
def list_import_sessions( tenant_id: int,
```

**Description**: Liste les sessions d'import avec statistiques agrégées.

- **Ligne**: 227
- **Réutilisabilité**: Medium
- **Type de retour**: `tuple[list[dict[str, Any]], int]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `limit`: `int` = `50`
  - `offset`: `int` = `0`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `get_session_details` 🎀

```python
def get_session_details( session_id: str,
```

**Description**: Récupère tous les imports d'une session donnée.

- **Ligne**: 310
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any] | None`
- **Paramètres**:
  - `session_id`: `str`
  - `tenant_id`: `int`
- **Dépendances**:
  - `json`
  - `typing.Any`

#### 🔸 `execute_raw_sql`

```python
def execute_raw_sql(sql, params=None, fetch=False):
```

**Description**: Compat: exécution SQL simple avec option de fetch.

- **Ligne**: 370
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `sql`
  - `params` = `None`
  - `fetch` = `False`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

### `core/inventory_service.py`

#### 🔸 `process_sale_transaction`

```python
def process_sale_transaction( cart: list,
```

**Description**: Enregistre une vente en décrémentant le stock et en traçant les mouvements.

- **Ligne**: 42
- **Réutilisabilité**: Medium
- **Type de retour**: `tuple[bool, str | None, dict[str, bytes] | None]`
- **Paramètres**:
  - `cart`: `list`
  - `username`: `str`
- **Dépendances**:
  - `collections.defaultdict`
  - `data_repository.get_engine`
  - `decimal.Decimal`
  - `pdf_utils.render_receipt_pdf`
  - `pdf_utils.sanitize_receipt_text`
  - *... et 2 autres*

#### 🔸 `match_invoice_products` 🎀

```python
def match_invoice_products(invoice_df: pd.DataFrame, *, tenant_id: int = 1) -> pd.DataFrame:
```

**Description**: Associe les lignes d'une facture aux produits du catalogue via code-barres.

- **Ligne**: 265
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `collections.defaultdict`
  - `data_repository.get_engine`
  - `data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 12 autres*

#### 🔸 `find_similar_products` 🎀

```python
def find_similar_products( product_name: str,
```

**Description**: Trouve des produits similaires par nom en utilisant trigram similarity.

- **Ligne**: 359
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict]`
- **Paramètres**:
  - `product_name`: `str`
- **Dépendances**:
  - `collections.defaultdict`
  - `data_repository.get_engine`
  - `data_repository.query_df`
  - `decimal.ROUND_HALF_UP`
  - `pdf_utils.format_currency_line`
  - *... et 5 autres*

#### 🔸 `suggest_product_matches` 🎀

```python
def suggest_product_matches( invoice_df: pd.DataFrame,
```

**Description**: Enrichit les lignes de facture non-matchées avec des suggestions de produits similaires.

- **Ligne**: 471
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `pdf_utils.format_currency_line`
  - `pdf_utils.format_quantity`
  - `pdf_utils.render_receipt_pdf`
  - `pdf_utils.sanitize_receipt_text`

#### 🔸 `register_invoice_reception` 🎀

```python
def register_invoice_reception( invoice_df: pd.DataFrame,
```

**Description**: Crée des mouvements d'entrée à partir d'une réception de facture.

- **Ligne**: 555
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `collections.defaultdict`
  - `data_repository.get_engine`
  - `data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 9 autres*

### `core/price_correction_service.py`

#### 🔸 `apply_price_corrections`

```python
def apply_price_corrections(items: Iterable[Mapping[str, Any]], *, tenant_id: int) -> Dict[str, Any]:
```

**Description**: Met à jour en masse les prix manquants (prix_achat/prix_vente/tva) sur produits.

- **Ligne**: 29
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `items`: `Iterable[Mapping[str, Any]]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.Iterable`
  - *... et 1 autres*

### `core/price_history_service.py`

#### 🔸 `fill_missing_prices_from_history`

```python
def fill_missing_prices_from_history(tenant_id: int = 1, margin_multiplier: float | None = None) -> dict:
```

**Description**: Remplit les prix_achat/prix_vente manquants depuis l'historique produits_price_history.

- **Ligne**: 168
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `tenant_id`: `int` = `1`
  - `margin_multiplier`: `float | None` = `None`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `sqlalchemy.text`

#### 🔸 `record_price_history`

```python
def record_price_history( df: pd.DataFrame,
```

**Description**: Enregistre un instantané des prix d'achat extraits d'une facture.

- **Ligne**: 216
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `df`: `pd.DataFrame`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.query_df`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - *... et 1 autres*

#### 🔸 `fetch_price_history` 🎀

```python
def fetch_price_history( *, produit_id: int | None = None,
```

**Description**: Récupère l'historique des prix d'achat selon différents filtres.

- **Ligne**: 340
- **Réutilisabilité**: Low
- **Type de retour**: `pd.DataFrame`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.query_df`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - *... et 1 autres*

#### 🔸 `fetch_latest_price_per_code`

```python
def fetch_latest_price_per_code( *, tenant_id: int = 1,
```

**Description**: Récupère la dernière entrée par code pour le tenant demandé.

- **Ligne**: 549
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Iterable`

#### 🔸 `fetch_price_history_for_product`

```python
def fetch_price_history_for_product( *, produit_id: int | None = None,
```

**Description**: Retourne l'historique pour un produit ou un code spécifique.

- **Ligne**: 597
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`

### `core/product_service.py`

#### 🔸 `parse_barcode_input` 🎀

```python
def parse_barcode_input(raw_codes: str | Iterable[str] | None) -> list[str]:
```

**Description**: Normalise une entrée utilisateur en liste de codes-barres uniques.

- **Ligne**: 53
- **Réutilisabilité**: High
- **Type de retour**: `list[str]`
- **Paramètres**:
  - `raw_codes`: `str | Iterable[str] | None`
- **Dépendances**:
  - `__future__.annotations`
  - `data_repository.get_engine`
  - `re`
  - `typing.Iterable`

#### 🔸 `update_catalog_entry`

```python
def update_catalog_entry( product_id: int,
```

**Description**: Applique les modifications du tableau catalogue à un produit donné.

- **Ligne**: 112
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `product_id`: `int`
  - `field_changes`: `Mapping[str, Any] | None`
  - `barcode_field`: `str | Iterable[str] | None` = `None`
- **Dépendances**:
  - `data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Iterable`
  - `typing.Mapping`

#### 🔸 `delete_product_by_barcode`

```python
def delete_product_by_barcode(raw_code: str | None, *, tenant_id: int = 1) -> dict[str, Any]:
```

**Description**: Supprime un code-barres (ou le produit entier s'il est unique) pour un tenant donné.

- **Ligne**: 210
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `raw_code`: `str | None`
- **Dépendances**:
  - `data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

### `core/tenant_service.py`

#### 🔸 `ensure_tenants_table`

```python
def ensure_tenants_table() -> None:
```

**Description**: Crée la table tenants et insère les lignes de base si nécessaire.

- **Ligne**: 25
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.get_engine`
  - `os`
  - `sqlalchemy.text`

### `core/user_service.py`

#### 🔸 `ensure_user_table`

```python
def ensure_user_table() -> None:
```

**Description**: Crée la table des utilisateurs si nécessaire.

- **Ligne**: 33
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `os`
  - `sqlalchemy.text`

#### 🔸 `generate_secure_password` 🎀

```python
def generate_secure_password(length: int = 14) -> str:
```

**Description**: Génère un mot de passe robuste conforme à la politique de l’entreprise.

- **Ligne**: 77
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `length`: `int` = `14`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `hmac`
  - `secrets`
  - *... et 3 autres*

#### 🔸 `get_user_by_login`

```python
def get_user_by_login(identifier: str) -> Optional[dict]:
```

**Description**: Retourne un utilisateur à partir de son email ou nom d'utilisateur.

- **Ligne**: 97
- **Réutilisabilité**: High
- **Type de retour**: `Optional[dict]`
- **Paramètres**:
  - `identifier`: `str`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `sqlalchemy.exc.IntegrityError`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔸 `get_user_by_id`

```python
def get_user_by_id(user_id: int) -> Optional[dict]:
```

- **Ligne**: 115
- **Réutilisabilité**: High
- **Type de retour**: `Optional[dict]`
- **Paramètres**:
  - `user_id`: `int`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `sqlalchemy.exc.IntegrityError`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `list_users`

```python
def list_users():
```

**Description**: Retourne l'ensemble des utilisateurs ordonnés par date de création.

- **Ligne**: 130
- **Réutilisabilité**: Medium
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `sqlalchemy.exc.IntegrityError`
  - `sqlalchemy.text`

#### 🔸 `authenticate_user`

```python
def authenticate_user(identifier: str, password: str) -> Optional[dict]:
```

**Description**: Valide les identifiants et retourne l'utilisateur sans le hash.

- **Ligne**: 143
- **Réutilisabilité**: High
- **Type de retour**: `Optional[dict]`
- **Paramètres**:
  - `identifier`: `str`
  - `password`: `str`
- **Dépendances**:
  - `string`
  - `typing.Optional`

#### 🔸 `create_user`

```python
def create_user(username: str, email: str, password: str, role: str = "standard") -> dict:
```

**Description**: Crée un utilisateur et retourne ses métadonnées (sans hash).

- **Ligne**: 165
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `username`: `str`
  - `email`: `str`
  - `password`: `str`
  - `role`: `str` = `'standard'`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `sqlalchemy.exc.IntegrityError`
  - `sqlalchemy.text`
  - `string`

#### 🔸 `update_user_role`

```python
def update_user_role(user_id: int, role: str) -> None:
```

**Description**: Modifie le rôle d'un utilisateur tout en protégeant le dernier admin.

- **Ligne**: 228
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `user_id`: `int`
  - `role`: `str`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `sqlalchemy.text`
  - `string`

#### 🔸 `reset_user_password` 🎀

```python
def reset_user_password(user_id: int, new_password: Optional[str] = None) -> str:
```

**Description**: Réinitialise le mot de passe et retourne sa valeur en clair.

- **Ligne**: 253
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `user_id`: `int`
  - `new_password`: `Optional[str]` = `None`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `sqlalchemy.text`
  - `string`
  - `typing.Optional`

#### 🔸 `bootstrap_default_admin`

```python
def bootstrap_default_admin() -> None:
```

**Description**: Crée un compte admin par défaut si aucun utilisateur n'existe.

- **Ligne**: 272
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `os`
  - `sqlalchemy.text`

#### 🔸 `bootstrap_users_if_enabled`

```python
def bootstrap_users_if_enabled() -> None:
```

**Description**: Initialise la table utilisateurs et l'admin par défaut si autorisé.

- **Ligne**: 291
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Dépendances**:
  - `data_repository.exec_sql`
  - `data_repository.exec_sql_return_id`
  - `data_repository.query_df`
  - `os`
  - `sqlalchemy.exc.IntegrityError`

---

## Restaurant

**77 fonctions**

### `backend/services/restaurant/bank_statements.py`

#### 🔸 `list_bank_statements`

```python
def list_bank_statements(tenant_id: int, account: str | None = None) -> List[dict[str, Any]]:
```

**Description**: Retourne les lignes de relevé bancaire via les tables finance_* (filtre compte optionnel).

- **Ligne**: 24
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `account`: `str | None` = `None`
- **Dépendances**:
  - `backend.services.restaurant.utils._get_restaurant_entity_id`
  - `collections.defaultdict`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `list_bank_accounts_overview` 🎀

```python
def list_bank_accounts_overview(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Synthèse par compte (volume, flux, dernière activité).

- **Ligne**: 66
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.services.restaurant.utils._get_restaurant_entity_id`
  - `backend.services.restaurant.utils._safe_float`
  - `collections.defaultdict`
  - `core.data_repository.query_df`
  - `datetime.date`
  - *... et 6 autres*

#### 🔸 `create_bank_statement`

```python
def create_bank_statement(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Insère une ligne de relevé bancaire importée/éditée.

- **Ligne**: 130
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_bank_statement`

```python
def update_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Met à jour un relevé existant et renvoie la version enrichie.

- **Ligne**: 152
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `entry_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `collections.defaultdict`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `import_bank_statements_from_pdf`

```python
def import_bank_statements_from_pdf(tenant_id: int, account: str, pdf_bytes: bytes) -> dict[str, int]:
```

**Description**: Analyse un relevé PDF et l'importe via l'orchestrateur unifié.

- **Ligne**: 182
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, int]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `account`: `str`
  - `pdf_bytes`: `bytes`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.constants.CATEGORY_GROUP_PRESETS`
  - `backend.services.restaurant.expenses.get_expense_detail`
  - `backend.services.restaurant.utils._ensure_depense_category`
  - `backend.services.restaurant.utils._get_grouping_preset`
  - *... et 11 autres*

#### 🔸 `create_expense_from_bank_statement`

```python
def create_expense_from_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Crée une dépense depuis un relevé bancaire et les relie.

- **Ligne**: 224
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `entry_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `backend.services.restaurant.expenses.get_expense_detail`
  - `backend.services.restaurant.utils._ensure_depense_category`
  - `backend.services.restaurant.utils._safe_float`
  - `collections.defaultdict`
  - `core.bank_import.orchestrator.BankImportOrchestrator`
  - *... et 3 autres*

#### 🔸 `transfer_from_epicerie`

```python
def transfer_from_epicerie(tenant_id: int, produit_restaurant_id: int, quantite: float = 1.0) -> Dict[str, Any]:
```

**Description**: Appelle la fonction SQL transfer_from_epicerie pour les mouvements épicerie -> restaurant.

- **Ligne**: 302
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `produit_restaurant_id`: `int`
  - `quantite`: `float` = `1.0`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `collections.OrderedDict`
  - `core.bank_import.orchestrator.BankImportOrchestrator`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔸 `get_bank_statement_summary`

```python
def get_bank_statement_summary( tenant_id: int, account: str | None = None, months: int = 6, grouping: str | None = None
```

**Description**: Construit les agrégats quotidiens/hebdomadaires/mensuels et les regroupements par catégorie.

- **Ligne**: 315
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `account`: `str | None` = `None`
  - `months`: `int` = `6`
  - `grouping`: `str | None` = `None`
- **Dépendances**:
  - `backend.services.restaurant.constants.CATEGORY_GROUP_PRESETS`
  - `backend.services.restaurant.utils._get_grouping_preset`
  - `backend.services.restaurant.utils._get_restaurant_entity_id`
  - `backend.services.restaurant.utils._resolve_group_name`
  - `backend.services.restaurant.utils._safe_float`
  - *... et 11 autres*

### `backend/services/restaurant/dashboard.py`

#### 🔸 `build_dashboard_overview`

```python
def build_dashboard_overview(tenant_id: int) -> dict[str, Any]:
```

**Description**: Assemble les indicateurs pour la page Dashboard (dépenses, marges plats, stocks).

- **Ligne**: 22
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.services.restaurant.expenses.expense_summary_by_cost_center`
  - `backend.services.restaurant.expenses.expense_summary_by_month`
  - `backend.services.restaurant.ingredients.list_ingredients`
  - `backend.services.restaurant.ingredients.list_plats`
  - `backend.services.restaurant.utils._safe_float`
  - *... et 4 autres*

#### 🔸 `build_forecast_overview` 🎀

```python
def build_forecast_overview( tenant_id: int,
```

**Description**: Construit la vue de prévision (consommation quotidienne estimée, timeline, top produits).

- **Ligne**: 81
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `horizon_days`: `int` = `30`
  - `granularity`: `str` = `'weekly'`
  - `top_limit`: `int` = `8`
- **Dépendances**:
  - `backend.services.catalog_data.fetch_customer_catalog`
  - `backend.services.restaurant.constants.ALLOWED_FORECAST_GRANULARITY`
  - `backend.services.restaurant.utils._safe_float`
  - `core.inventory_forecast.forecast_daily_consumption`
  - `datetime.date`
  - *... et 3 autres*

### `backend/services/restaurant/expenses.py`

#### 🔸 `list_depense_categories`

```python
def list_depense_categories(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Liste toutes les catégories de dépense pour un tenant.

- **Ligne**: 13
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `create_depense_category`

```python
def create_depense_category(tenant_id: int, nom: str) -> dict[str, Any]:
```

**Description**: Crée une nouvelle catégorie de dépense.

- **Ligne**: 29
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `nom`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_cost_centers`

```python
def list_cost_centers(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Liste tous les centres de coûts pour un tenant.

- **Ligne**: 45
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `create_cost_center`

```python
def create_cost_center(tenant_id: int, nom: str) -> dict[str, Any]:
```

**Description**: Crée un nouveau centre de coûts.

- **Ligne**: 61
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `nom`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_fournisseurs`

```python
def list_fournisseurs(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Liste tous les fournisseurs pour un tenant.

- **Ligne**: 77
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `create_fournisseur`

```python
def create_fournisseur(tenant_id: int, nom: str) -> dict[str, Any]:
```

**Description**: Crée un nouveau fournisseur.

- **Ligne**: 93
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `nom`: `str`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_expenses`

```python
def list_expenses(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Liste toutes les dépenses d'un tenant avec données enrichies.

- **Ligne**: 109
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `get_expense_detail`

```python
def get_expense_detail(tenant_id: int, expense_id: int) -> dict[str, Any] | None:
```

**Description**: Récupère le détail d'une dépense donnée.

- **Ligne**: 131
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any] | None`
- **Paramètres**:
  - `tenant_id`: `int`
  - `expense_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `create_expense` 🎀

```python
def create_expense(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Insère une dépense et renvoie l'enregistrement enrichi.

- **Ligne**: 155
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `expense_summary_by_month`

```python
def expense_summary_by_month(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
```

**Description**: Agrège les dépenses par mois sur la période demandée.

- **Ligne**: 181
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `months`: `int` = `6`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `expense_summary_by_cost_center`

```python
def expense_summary_by_cost_center(tenant_id: int, months: int = 3) -> List[dict[str, Any]]:
```

**Description**: Répartit les dépenses par centre de coûts sur la période récente.

- **Ligne**: 196
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `months`: `int` = `3`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `expense_summary_by_tva`

```python
def expense_summary_by_tva(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
```

**Description**: Résume les montants HT/TVA/TTC pour la déclaration fiscale.

- **Ligne**: 215
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `months`: `int` = `6`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

### `backend/services/restaurant/ingredients.py`

#### 🔸 `list_ingredients` 🎀

```python
def list_ingredients(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Retourne les ingrédients disponibles pour composer les plats avec infos catégorie/fournisseur.

- **Ligne**: 14
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔸 `create_ingredient` 🎀

```python
def create_ingredient(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Crée un ingrédient avec prix unitaire et stock initial.

- **Ligne**: 83
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `link_ingredient_to_epicerie` 🎀

```python
def link_ingredient_to_epicerie(tenant_id: int, ingredient_id: int, produit_epicerie_id: int, ratio: float = 1.0) -> dict[str, Any]:
```

**Description**: Lie un ingrédient à un produit épicerie et synchronise catégorie/fournisseur.

- **Ligne**: 146
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `produit_epicerie_id`: `int`
  - `ratio`: `float` = `1.0`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `unlink_ingredient_from_epicerie` 🎀

```python
def unlink_ingredient_from_epicerie(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
```

**Description**: Retire le lien entre un ingrédient et un produit épicerie.

- **Ligne**: 205
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_ingredient_ratio` 🎀

```python
def update_ingredient_ratio(tenant_id: int, ingredient_id: int, ratio: float) -> dict[str, Any]:
```

**Description**: Met à jour le ratio de conversion ingrédient/épicerie.

- **Ligne**: 229
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `ratio`: `float`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_ingredient_price`

```python
def update_ingredient_price(tenant_id: int, ingredient_id: int, new_price: float) -> dict[str, Any]:
```

**Description**: Met à jour le coût de l'ingrédient et recalcule les marges des plats.

- **Ligne**: 263
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `new_price`: `float`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_plats` 🎀

```python
def list_plats(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Charge les plats avec marge brute calculée depuis les ingrédients.

- **Ligne**: 283
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - *... et 1 autres*

#### 🔸 `refresh_plat_costs`

```python
def refresh_plat_costs(tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
```

**Description**: Délègue le recalcul des coûts/marges aux utilitaires partagés.

- **Ligne**: 416
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `margin_threshold`: `float` = `35.0`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.restaurant_costs`
  - `typing.Any`

#### 🔸 `list_plat_alerts`

```python
def list_plat_alerts(tenant_id: int) -> List[dict[str, Any]]:
```

**Description**: Retourne les alertes de marge générées par le recalcul précédent.

- **Ligne**: 421
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.restaurant_costs`
  - `typing.Any`
  - `typing.List`

#### 🔸 `create_plat` 🎀

```python
def create_plat(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Crée un plat et initialise totaux/marges depuis les ingrédients liés.

- **Ligne**: 426
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `attach_ingredient_to_plat`

```python
def attach_ingredient_to_plat(tenant_id: int, plat_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Associe un ingrédient à un plat avec recalcul des coûts.

- **Ligne**: 462
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `remove_ingredient_from_plat`

```python
def remove_ingredient_from_plat(tenant_id: int, plat_id: int, ingredient_id: int) -> dict[str, Any]:
```

**Description**: Retire un ingrédient d'un plat et rafraîchit les coûts.

- **Ligne**: 491
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
  - `ingredient_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_plat_ingredient`

```python
def update_plat_ingredient( tenant_id: int,
```

**Description**: Met à jour la quantité/unité d'un ingrédient du plat et rafraîchit les coûts.

- **Ligne**: 509
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
  - `ingredient_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.restaurant_costs`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_plat_price`

```python
def update_plat_price(tenant_id: int, plat_id: int, new_price: float) -> dict[str, Any]:
```

**Description**: Met à jour le prix TTC du plat et recalcule les marges liées.

- **Ligne**: 549
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
  - `new_price`: `float`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_ingredient_price_history`

```python
def list_ingredient_price_history(tenant_id: int, ingredient_id: int) -> List[dict[str, Any]]:
```

**Description**: Affiche l'historique des prix pour un ingrédient donné.

- **Ligne**: 571
- **Réutilisabilité**: Medium
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `core.restaurant_costs`
  - *... et 4 autres*

#### 🔸 `list_plat_price_history`

```python
def list_plat_price_history(tenant_id: int, plat_id: int) -> List[dict[str, Any]]:
```

**Description**: Affiche l'historique des prix pour un plat donné.

- **Ligne**: 651
- **Réutilisabilité**: High
- **Type de retour**: `List[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.List`

#### 🔸 `list_recent_price_changes`

```python
def list_recent_price_changes(tenant_id: int, limit: int = 12) -> dict[str, list[dict[str, Any]]]:
```

**Description**: Retourne les dernières modifications de prix pour ingrédients et plats.

- **Ligne**: 668
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, list[dict[str, Any]]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `limit`: `int` = `12`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `update_ingredient` 🎀

```python
def update_ingredient(tenant_id: int, ingredient_id: int, payload: dict[str, Any]) -> dict[str, Any]:
```

**Description**: Met à jour les détails d'un ingrédient (nom, unité, coût, stock, catégorie, fournisseur).

- **Ligne**: 699
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `payload`: `dict[str, Any]`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `delete_ingredient`

```python
def delete_ingredient(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
```

**Description**: Supprime un ingrédient. Échoue si l'ingrédient est utilisé dans un plat.

- **Ligne**: 739
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `delete_plat`

```python
def delete_plat(tenant_id: int, plat_id: int) -> dict[str, Any]:
```

**Description**: Supprime un plat et cascade sur restaurant_plat_ingredients.

- **Ligne**: 777
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`
  - `typing.Any`

### `backend/services/restaurant/mappings.py`

#### 🔸 `list_sales_consumptions` 🎀

```python
def list_sales_consumptions(tenant_id: int, period: str = "all") -> list[Dict[str, Any]]:
```

**Description**: Retourne tous les ingrédients liés aux produits Épicerie avec leurs données de consommation.

- **Ligne**: 12
- **Réutilisabilité**: Medium
- **Type de retour**: `list[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `period`: `str` = `'all'`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `sync_ingredients_from_mappings` 🎀

```python
def sync_ingredients_from_mappings(tenant_id: int = 2) -> int:
```

**Description**: Synchronise les ingrédients à partir des mappings SKU épicerie-restaurant.

- **Ligne**: 98
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Paramètres**:
  - `tenant_id`: `int` = `2`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`

#### 🔸 `guess_unit`

```python
def guess_unit(category: str | None) -> str:
```

- **Ligne**: 117
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `category`: `str | None`

#### 🔸 `list_combined_price_history` 🎀

```python
def list_combined_price_history(tenant_id: int) -> list[Dict[str, Any]]:
```

**Description**: Retourne l'historique des prix restaurant avec les coûts Épicerie associés.

- **Ligne**: 180
- **Réutilisabilité**: Medium
- **Type de retour**: `list[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `list_plat_epicerie_links` 🎀

```python
def list_plat_epicerie_links(tenant_id: int) -> list[Dict[str, Any]]:
```

**Description**: Liste tous les liens plat-produit épicerie.

- **Ligne**: 215
- **Réutilisabilité**: Medium
- **Type de retour**: `list[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `math`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔸 `upsert_plat_epicerie_mapping`

```python
def upsert_plat_epicerie_mapping( tenant_restaurant: int,
```

**Description**: Crée ou met à jour un mapping plat-épicerie et synchronise les coûts des ingrédients.

- **Ligne**: 253
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_restaurant`: `int`
  - `plat_id`: `int`
  - `produit_epicerie_id`: `int`
  - `ratio`: `float` = `1.0`
  - `tenant_epicerie`: `int` = `1`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `delete_plat_epicerie_mapping`

```python
def delete_plat_epicerie_mapping(tenant_restaurant: int, plat_id: int) -> bool:
```

**Description**: Supprime un mapping plat-épicerie.

- **Ligne**: 343
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `tenant_restaurant`: `int`
  - `plat_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`

#### 🔸 `list_epicerie_products`

```python
def list_epicerie_products(tenant_epicerie: int = 1) -> list[Dict[str, Any]]:
```

**Description**: Liste tous les produits épicerie disponibles pour le mapping.

- **Ligne**: 360
- **Réutilisabilité**: Medium
- **Type de retour**: `list[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_epicerie`: `int` = `1`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `search_epicerie_products` 🎀

```python
def search_epicerie_products( tenant_epicerie: int = 1,
```

**Description**: Fast search for epicerie products with optional fuzzy suggestions.

- **Ligne**: 384
- **Réutilisabilité**: Medium
- **Type de retour**: `list[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_epicerie`: `int` = `1`
  - `query`: `str` = `''`
  - `limit`: `int` = `20`
  - `suggest_for`: `str | None` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - *... et 3 autres*

### `backend/services/restaurant/menus.py`

#### 🔸 `get_menu_overview`

```python
def get_menu_overview(tenant_id: int) -> RestaurantMenuOverview:
```

**Description**: Aggregated view of menus & costs for a restaurant tenant.

- **Ligne**: 20
- **Réutilisabilité**: Medium
- **Type de retour**: `RestaurantMenuOverview`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.schemas.restaurant.RestaurantMenuIngredientAlert`
  - `backend.schemas.restaurant.RestaurantMenuMetrics`
  - `backend.schemas.restaurant.RestaurantMenuOverview`
  - `backend.schemas.restaurant.RestaurantMenuPlatCost`
  - *... et 6 autres*

### `backend/services/restaurant/overview.py`

#### 🔸 `get_restaurant_overview`

```python
def get_restaurant_overview(tenant_id: int, period: str = "30d") -> dict[str, Any]:
```

**Description**: Fournit l'overview restaurant avec métriques, top plats et alertes.

- **Ligne**: 20
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `period`: `str` = `'30d'`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - *... et 3 autres*

#### 🔸 `list_plats_paginated`

```python
def list_plats_paginated( tenant_id: int,
```

**Description**: Liste les plats avec pagination, filtres et tri.

- **Ligne**: 136
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `page`: `int` = `1`
  - `page_size`: `int` = `50`
  - `categorie`: `Optional[str]` = `None`
  - `actif`: `Optional[bool]` = `None`
  - `min_margin_pct`: `Optional[float]` = `None`
  - `sort_by`: `str` = `'nom'`
  - `sort_desc`: `bool` = `False`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔸 `get_plat_detail`

```python
def get_plat_detail(tenant_id: int, plat_id: int) -> dict[str, Any]:
```

**Description**: Récupère les détails complets d'un plat avec ingrédients et historique de prix.

- **Ligne**: 238
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `get_plat_cost_breakdown`

```python
def get_plat_cost_breakdown(tenant_id: int, plat_id: int) -> dict[str, Any]:
```

**Description**: Détaille le coût par ingrédient avec tendances de prix.

- **Ligne**: 343
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `list_ingredients_enhanced` 🎀

```python
def list_ingredients_enhanced(tenant_id: int) -> list[dict[str, Any]]:
```

**Description**: Liste les ingrédients avec fournisseur et tendance de prix.

- **Ligne**: 409
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `get_ingredient_price_history_detail`

```python
def get_ingredient_price_history_detail(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
```

**Description**: Récupère l'historique de prix détaillé pour un ingrédient.

- **Ligne**: 442
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `analyze_food_cost`

```python
def analyze_food_cost( tenant_id: int,
```

**Description**: Analyse le food cost avec tendances et recommandations.

- **Ligne**: 486
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `period`: `str` = `'30d'`
  - `target_food_cost`: `float` = `30.0`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - *... et 4 autres*

#### 🔸 `simulate_price_change`

```python
def simulate_price_change( tenant_id: int,
```

**Description**: Simule l'impact d'un changement de prix sur les marges et le food cost.

- **Ligne**: 628
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `plat_id`: `int`
  - `new_price`: `Optional[float]` = `None`
  - `target_margin_pct`: `Optional[float]` = `None`
- **Dépendances**:
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Optional`

#### 🔸 `list_alerts_detailed` 🎀

```python
def list_alerts_detailed( tenant_id: int,
```

**Description**: Liste les alertes restaurant détaillées avec filtres.

- **Ligne**: 710
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `alert_type`: `Optional[str]` = `None`
  - `severity`: `Optional[str]` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.utils._safe_float`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 2 autres*

### `backend/services/restaurant/price_sync.py`

#### 🔸 `audit_epicerie_links`

```python
def audit_epicerie_links(tenant_id: int, *, dry_run: bool = True) -> dict[str, Any]:
```

**Description**: Détecte et éventuellement délier les correspondances incohérentes ingrédient ↔ épicerie.

- **Ligne**: 45
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.ingredients.refresh_plat_costs`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 1 autres*

#### 🔸 `sync_ingredient_prices_from_epicerie` 🎀

```python
def sync_ingredient_prices_from_epicerie(tenant_id: int, force_update: bool = False) -> dict[str, Any]:
```

**Description**: Synchronise les prix des ingrédients à partir des produits épicerie liés.

- **Ligne**: 121
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `force_update`: `bool` = `False`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.ingredients.refresh_plat_costs`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - *... et 2 autres*

#### 🔸 `get_ingredients_with_price_source` 🎀

```python
def get_ingredients_with_price_source(tenant_id: int) -> list[dict[str, Any]]:
```

**Description**: Retourne les ingrédients avec indication explicite de la source de prix (manuel vs épicerie).

- **Ligne**: 271
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.services.restaurant.ingredients.refresh_plat_costs`
  - `core.data_repository.query_df`
  - `logging`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `get_price_sync_summary`

```python
def get_price_sync_summary(tenant_id: int) -> dict[str, Any]:
```

**Description**: Fournit un récapitulatif du statut de synchronisation des prix pour tous les ingrédients.

- **Ligne**: 353
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.restaurant.ingredients.refresh_plat_costs`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `logging`
  - *... et 2 autres*

### `backend/services/restaurant/stock.py`

#### 🔸 `list_stock_movements`

```python
def list_stock_movements( tenant_id: int,
```

**Description**: Liste les mouvements de stock restaurant avec filtres.

- **Ligne**: 33
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `Optional[int]` = `None`
  - `source`: `Optional[str]` = `None`
  - `type_mouvement`: `Optional[str]` = `None`
  - `date_from`: `Optional[date]` = `None`
  - `date_to`: `Optional[date]` = `None`
  - `limit`: `int` = `100`
  - `offset`: `int` = `0`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 3 autres*

#### 🔸 `get_stock_summary`

```python
def get_stock_summary(tenant_id: int) -> List[Dict[str, Any]]:
```

**Description**: Retourne le résumé du stock actuel par ingrédient avec dernier mouvement.

- **Ligne**: 105
- **Réutilisabilité**: High
- **Type de retour**: `List[Dict[str, Any]]`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `get_daily_movements_by_category`

```python
def get_daily_movements_by_category( tenant_id: int,
```

**Description**: Agrège les mouvements par jour et catégorie pour les graphiques.

- **Ligne**: 137
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `date_from`: `Optional[date]` = `None`
  - `date_to`: `Optional[date]` = `None`
  - `type_mouvement`: `str` = `'sortie'`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - `json`
  - `sqlalchemy.text`
  - *... et 3 autres*

#### 🔸 `create_stock_movement`

```python
def create_stock_movement( tenant_id: int,
```

**Description**: Crée un mouvement de stock et met à jour le stock de l'ingrédient.

- **Ligne**: 189
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `type_mouvement`: `str`
  - `quantite`: `float`
  - `source`: `str`
  - `unite`: `Optional[str]` = `None`
  - `cout_unitaire`: `Optional[float]` = `None`
  - `facture_id`: `Optional[int]` = `None`
  - `facture_ref`: `Optional[str]` = `None`
  - `fournisseur`: `Optional[str]` = `None`
  - `produit_epicerie_id`: `Optional[int]` = `None`
  - `commentaire`: `Optional[str]` = `None`
  - `date_mouvement`: `Optional[datetime]` = `None`
  - `created_by`: `Optional[str]` = `None`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `datetime.date`
  - `datetime.datetime`
  - `sqlalchemy.text`
  - `typing.Any`
  - *... et 2 autres*

#### 🔸 `transfer_from_epicerie`

```python
def transfer_from_epicerie( tenant_id: int,
```

**Description**: Transfère du stock depuis un produit épicerie vers un ingrédient restaurant.

- **Ligne**: 283
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `produit_epicerie_id`: `int`
  - `quantite`: `float`
  - `commentaire`: `Optional[str]` = `None`
  - `created_by`: `Optional[str]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

#### 🔸 `record_invoice_entry`

```python
def record_invoice_entry( tenant_id: int,
```

**Description**: Enregistre une entrée de stock depuis une facture.

- **Ligne**: 323
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `quantite`: `float`
  - `cout_unitaire`: `float`
  - `facture_id`: `int`
  - `facture_ref`: `str`
  - `fournisseur`: `str`
  - `unite`: `Optional[str]` = `None`
  - `date_mouvement`: `Optional[datetime]` = `None`
  - `created_by`: `Optional[str]` = `None`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

#### 🔸 `record_consumption`

```python
def record_consumption( tenant_id: int,
```

**Description**: Enregistre une sortie de stock pour consommation.

- **Ligne**: 354
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `quantite`: `float`
  - `commentaire`: `Optional[str]` = `None`
  - `created_by`: `Optional[str]` = `None`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

#### 🔸 `record_adjustment`

```python
def record_adjustment( tenant_id: int,
```

**Description**: Ajuste le stock à une nouvelle quantité (inventaire).

- **Ligne**: 375
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `ingredient_id`: `int`
  - `new_quantity`: `float`
  - `commentaire`: `Optional[str]` = `None`
  - `created_by`: `Optional[str]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`
  - `typing.Optional`

#### 🔸 `get_daily_consumption_by_plat`

```python
def get_daily_consumption_by_plat( tenant_id: int,
```

**Description**: Agrège les ventes par jour et par plat.

- **Ligne**: 412
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `date_from`: `Optional[date]` = `None`
  - `date_to`: `Optional[date]` = `None`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - `json`
  - `sqlalchemy.text`
  - *... et 3 autres*

#### 🔸 `get_stock_analytics`

```python
def get_stock_analytics( tenant_id: int,
```

**Description**: Statistiques de stock sur une période.

- **Ligne**: 480
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `days`: `int` = `30`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

### `core/restaurant_costs.py`

#### 🔸 `refresh_plat_costs`

```python
def refresh_plat_costs(*, tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
```

- **Ligne**: 47
- **Réutilisabilité**: Low
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

#### 🔸 `list_margin_alerts`

```python
def list_margin_alerts(*, tenant_id: int) -> list[dict[str, Any]]:
```

- **Ligne**: 161
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`

---

## Database

**60 fonctions**

### `core/bank_import/models.py`

#### 🔹 `to_dict`

```python
def to_dict(self) -> Dict[str, Any]:
```

**Description**: Convert to dictionary for database insertion.

- **Ligne**: 153
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

### `core/bank_import/orchestrator.py`

#### 🔹 `__init__`

```python
def __init__( self, engine: Optional[Engine] = None,
```

**Description**: Initialize orchestrator.

- **Ligne**: 52
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `engine`: `Optional[Engine]` = `None`
  - `dry_run`: `bool` = `False`
  - `strict_validation`: `bool` = `False`
- **Dépendances**:
  - `categorizer.TransactionCategorizer`
  - `deduplicator.TransactionDeduplicator`
  - `detector.BankDetector`
  - `extractor.PDFExtractor`
  - `parser.UnifiedBankParser`
  - *... et 3 autres*

#### 🔹 `test_pdf` 🎀

```python
def test_pdf(self, pdf_path: Path) -> dict:
```

**Description**: Test PDF parsing without database operations.

- **Ligne**: 558
- **Réutilisabilité**: Medium
- **Type de retour**: `dict`
- **Paramètres**:
  - `self`
  - `pdf_path`: `Path`
- **Dépendances**:
  - `__future__.annotations`
  - `categorizer.TransactionCategorizer`
  - `datetime.datetime`
  - `deduplicator.TransactionDeduplicator`
  - `detector.BankDetector`
  - *... et 12 autres*

#### 🔸 `import_bank_pdf`

```python
def import_bank_pdf( pdf_path: Path,
```

**Description**: Convenience function for importing a bank PDF.

- **Ligne**: 633
- **Réutilisabilité**: High
- **Type de retour**: `ImportResult`
- **Paramètres**:
  - `pdf_path`: `Path`
  - `entity_code`: `str`
  - `account_label`: `str`
  - `dry_run`: `bool` = `False`
  - `strict_validation`: `bool` = `False`
- **Dépendances**:
  - `models.ImportResult`
  - `pathlib.Path`
  - `sqlalchemy.engine.Engine`

### `core/data_repository.py`

#### 🔸 `execute_raw_sql`

```python
def execute_raw_sql(sql: str | ClauseElement, params=None, fetch: bool = False):
```

**Description**: Compat: exécute une requête SQL et peut retourner les lignes si fetch=True.

- **Ligne**: 114
- **Réutilisabilité**: High
- **Paramètres**:
  - `sql`: `str | ClauseElement`
  - `params` = `None`
  - `fetch`: `bool` = `False`
- **Dépendances**:
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`
  - `sqlalchemy.sql.elements.ClauseElement`
  - `sqlalchemy.sql.elements.TextClause`
  - `sqlalchemy.text`

### `core/database_url.py`

#### 🔸 `get_database_url` 🎀

```python
def get_database_url() -> str:
```

**Description**: Build a SQLAlchemy compatible DATABASE_URL.

- **Ligne**: 19
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Dépendances**:
  - `urllib.parse.quote_plus`

### `core/products_loader.py`

#### 🔸 `exec_sql_return_id_with_conn`

```python
def exec_sql_return_id_with_conn(conn: Connection, sql: str, params=None):
```

**Description**: Exécute une requête SQL et retourne l'ID (colonne 0) en utilisant une connexion ouverte.

- **Ligne**: 199
- **Réutilisabilité**: High
- **Paramètres**:
  - `conn`: `Connection`
  - `sql`: `str`
  - `params` = `None`
- **Dépendances**:
  - `sqlalchemy.engine.Connection`
  - `sqlalchemy.exc`
  - `sqlalchemy.text`

### `core/repositories/base.py`

#### 🔹 `get_by_id`

```python
def get_by_id(self, id: ID, *, tenant_id: int) -> T | None:
```

**Description**: Get entity by ID.

- **Ligne**: 26
- **Réutilisabilité**: High
- **Type de retour**: `T | None`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `id`: `ID`
- **Dépendances**:
  - `abc.abstractmethod`
  - `typing.TypeVar`

#### 🔹 `list_all`

```python
def list_all(self, *, tenant_id: int, limit: int = 100, offset: int = 0) -> Sequence[T]:
```

**Description**: List all entities with pagination.

- **Ligne**: 31
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[T]`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `abc.abstractmethod`
  - `typing.Sequence`
  - `typing.TypeVar`

#### 🔹 `count`

```python
def count(self, *, tenant_id: int) -> int:
```

**Description**: Count total entities.

- **Ligne**: 36
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `add`

```python
def add(self, entity: T, *, tenant_id: int) -> T:
```

**Description**: Add new entity and return it with generated ID.

- **Ligne**: 45
- **Réutilisabilité**: High
- **Type de retour**: `T`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `entity`: `T`
- **Dépendances**:
  - `abc.abstractmethod`
  - `typing.TypeVar`

#### 🔹 `update`

```python
def update(self, entity: T, *, tenant_id: int) -> T:
```

**Description**: Update existing entity.

- **Ligne**: 50
- **Réutilisabilité**: High
- **Type de retour**: `T`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `entity`: `T`
- **Dépendances**:
  - `abc.abstractmethod`
  - `typing.TypeVar`

#### 🔹 `delete`

```python
def delete(self, id: ID, *, tenant_id: int) -> bool:
```

**Description**: Delete entity by ID. Returns True if deleted.

- **Ligne**: 55
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `id`: `ID`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `__enter__`

```python
def __enter__(self) -> "UnitOfWork":
```

- **Ligne**: 72
- **Réutilisabilité**: Medium
- **Type de retour**: `'UnitOfWork'`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `__exit__`

```python
def __exit__(self, exc_type, exc_val, exc_tb) -> None:
```

- **Ligne**: 76
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `exc_type`
  - `exc_val`
  - `exc_tb`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `commit`

```python
def commit(self) -> None:
```

**Description**: Commit all changes.

- **Ligne**: 80
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `rollback`

```python
def rollback(self) -> None:
```

**Description**: Rollback all changes.

- **Ligne**: 85
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `total_pages`

```python
def total_pages(self) -> int:
```

- **Ligne**: 100
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `has_next`

```python
def has_next(self) -> bool:
```

- **Ligne**: 106
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `has_prev`

```python
def has_prev(self) -> bool:
```

- **Ligne**: 110
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `__init__`

```python
def __init__(self, engine: Engine):
```

- **Ligne**: 121
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `engine`: `Engine`
- **Dépendances**:
  - `sqlalchemy.engine.Connection`
  - `sqlalchemy.engine.Engine`

#### 🔹 `__enter__` 🎀

```python
def __enter__(self) -> "SqlUnitOfWork":
```

- **Ligne**: 125
- **Réutilisabilité**: Medium
- **Type de retour**: `'SqlUnitOfWork'`
- **Paramètres**:
  - `self`

#### 🔹 `__exit__`

```python
def __exit__(self, exc_type, exc_val, exc_tb) -> None:
```

- **Ligne**: 130
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `exc_type`
  - `exc_val`
  - `exc_tb`

#### 🔹 `connection`

```python
def connection(self) -> Connection:
```

- **Ligne**: 138
- **Réutilisabilité**: Medium
- **Type de retour**: `Connection`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `sqlalchemy.engine.Connection`

#### 🔹 `commit`

```python
def commit(self) -> None:
```

- **Ligne**: 143
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`

#### 🔹 `rollback`

```python
def rollback(self) -> None:
```

- **Ligne**: 147
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`

### `core/repositories/stock_movements.py`

#### 🔹 `get_by_id`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> StockMovement | None:
```

- **Ligne**: 52
- **Réutilisabilité**: High
- **Type de retour**: `StockMovement | None`
- **Paramètres**:
  - `self`
  - `id`: `int`

#### 🔹 `list_by_product`

```python
def list_by_product( self, produit_id: int, *, tenant_id: int, limit: int = 100
```

- **Ligne**: 55
- **Réutilisabilité**: High
- **Type de retour**: `Sequence[StockMovement]`
- **Paramètres**:
  - `self`
  - `produit_id`: `int`
- **Dépendances**:
  - `typing.Sequence`

#### 🔹 `list_recent`

```python
def list_recent( self, *, tenant_id: int, days: int = 30, limit: int = 100
```

- **Ligne**: 60
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[StockMovement]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Sequence`

#### 🔹 `add`

```python
def add(self, movement: StockMovement) -> StockMovement:
```

- **Ligne**: 65
- **Réutilisabilité**: High
- **Type de retour**: `StockMovement`
- **Paramètres**:
  - `self`
  - `movement`: `StockMovement`

#### 🔹 `get_weekly_summary`

```python
def get_weekly_summary( self, *, tenant_id: int, weeks: int = 8
```

- **Ligne**: 68
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[StockMovementSummary]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Sequence`

#### 🔹 `get_daily_totals`

```python
def get_daily_totals( self, *, tenant_id: int, start_date: date, end_date: date
```

- **Ligne**: 73
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[StockMovementSummary]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `datetime.date`
  - `datetime.datetime`
  - `typing.Sequence`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 82
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`

#### 🔹 `get_by_id`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> StockMovement | None:
```

- **Ligne**: 85
- **Réutilisabilité**: High
- **Type de retour**: `StockMovement | None`
- **Paramètres**:
  - `self`
  - `id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`

#### 🔹 `list_by_product`

```python
def list_by_product( self, produit_id: int, *, tenant_id: int, limit: int = 100
```

- **Ligne**: 98
- **Réutilisabilité**: High
- **Type de retour**: `Sequence[StockMovement]`
- **Paramètres**:
  - `self`
  - `produit_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Sequence`

#### 🔹 `list_recent`

```python
def list_recent( self, *, tenant_id: int, days: int = 30, limit: int = 100
```

- **Ligne**: 115
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[StockMovement]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Sequence`

#### 🔹 `add` 🎀

```python
def add(self, movement: StockMovement) -> StockMovement:
```

- **Ligne**: 131
- **Réutilisabilité**: Medium
- **Type de retour**: `StockMovement`
- **Paramètres**:
  - `self`
  - `movement`: `StockMovement`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `get_weekly_summary`

```python
def get_weekly_summary( self, *, tenant_id: int, weeks: int = 8
```

- **Ligne**: 157
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[StockMovementSummary]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `decimal.Decimal`
  - `sqlalchemy.text`
  - `typing.Sequence`

#### 🔹 `get_daily_totals`

```python
def get_daily_totals( self, *, tenant_id: int, start_date: date, end_date: date
```

- **Ligne**: 189
- **Réutilisabilité**: Low
- **Type de retour**: `Sequence[StockMovementSummary]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `datetime.date`
  - `datetime.datetime`
  - `decimal.Decimal`
  - *... et 2 autres*

#### 🔹 `_row_to_movement`

```python
def _row_to_movement(self, row: dict) -> StockMovement:
```

- **Ligne**: 225
- **Réutilisabilité**: High
- **Type de retour**: `StockMovement`
- **Paramètres**:
  - `self`
  - `row`: `dict`
- **Dépendances**:
  - `decimal.Decimal`

### `core/repositories/users.py`

#### 🔹 `get_by_id`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> User | None:
```

- **Ligne**: 33
- **Réutilisabilité**: High
- **Type de retour**: `User | None`
- **Paramètres**:
  - `self`
  - `id`: `int`

#### 🔹 `get_by_username`

```python
def get_by_username(self, username: str, *, tenant_id: int) -> User | None:
```

- **Ligne**: 36
- **Réutilisabilité**: High
- **Type de retour**: `User | None`
- **Paramètres**:
  - `self`
  - `username`: `str`

#### 🔹 `get_by_email`

```python
def get_by_email(self, email: str, *, tenant_id: int) -> User | None:
```

- **Ligne**: 39
- **Réutilisabilité**: High
- **Type de retour**: `User | None`
- **Paramètres**:
  - `self`
  - `email`: `str`

#### 🔹 `list_all`

```python
def list_all(self, *, tenant_id: int, limit: int = 100, offset: int = 0) -> Sequence[User]:
```

- **Ligne**: 42
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[User]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Sequence`

#### 🔹 `list_active`

```python
def list_active(self, *, tenant_id: int) -> Sequence[User]:
```

- **Ligne**: 45
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[User]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Sequence`

#### 🔹 `add`

```python
def add(self, user: User, password_hash: str) -> User:
```

- **Ligne**: 48
- **Réutilisabilité**: High
- **Type de retour**: `User`
- **Paramètres**:
  - `self`
  - `user`: `User`
  - `password_hash`: `str`

#### 🔹 `update`

```python
def update(self, user: User) -> User:
```

- **Ligne**: 51
- **Réutilisabilité**: High
- **Type de retour**: `User`
- **Paramètres**:
  - `self`
  - `user`: `User`

#### 🔹 `update_last_login`

```python
def update_last_login(self, user_id: int, *, tenant_id: int) -> None:
```

- **Ligne**: 54
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `user_id`: `int`

#### 🔹 `deactivate`

```python
def deactivate(self, user_id: int, *, tenant_id: int) -> bool:
```

- **Ligne**: 57
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `user_id`: `int`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 64
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.get_engine`

#### 🔹 `get_by_id`

```python
def get_by_id(self, id: int, *, tenant_id: int) -> User | None:
```

- **Ligne**: 67
- **Réutilisabilité**: High
- **Type de retour**: `User | None`
- **Paramètres**:
  - `self`
  - `id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`

#### 🔹 `get_by_username`

```python
def get_by_username(self, username: str, *, tenant_id: int) -> User | None:
```

- **Ligne**: 80
- **Réutilisabilité**: High
- **Type de retour**: `User | None`
- **Paramètres**:
  - `self`
  - `username`: `str`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`

#### 🔹 `get_by_email`

```python
def get_by_email(self, email: str, *, tenant_id: int) -> User | None:
```

- **Ligne**: 93
- **Réutilisabilité**: High
- **Type de retour**: `User | None`
- **Paramètres**:
  - `self`
  - `email`: `str`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`

#### 🔹 `list_all`

```python
def list_all( self, *, tenant_id: int, limit: int = 100, offset: int = 0
```

- **Ligne**: 106
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[User]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Sequence`

#### 🔹 `list_active`

```python
def list_active(self, *, tenant_id: int) -> Sequence[User]:
```

- **Ligne**: 121
- **Réutilisabilité**: Medium
- **Type de retour**: `Sequence[User]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Sequence`

#### 🔹 `add` 🎀

```python
def add(self, user: User, password_hash: str) -> User:
```

- **Ligne**: 133
- **Réutilisabilité**: Medium
- **Type de retour**: `User`
- **Paramètres**:
  - `self`
  - `user`: `User`
  - `password_hash`: `str`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `update` 🎀

```python
def update(self, user: User) -> User:
```

- **Ligne**: 158
- **Réutilisabilité**: High
- **Type de retour**: `User`
- **Paramètres**:
  - `self`
  - `user`: `User`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`

#### 🔹 `update_last_login`

```python
def update_last_login(self, user_id: int, *, tenant_id: int) -> None:
```

- **Ligne**: 179
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `user_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `sqlalchemy.text`

#### 🔹 `deactivate`

```python
def deactivate(self, user_id: int, *, tenant_id: int) -> bool:
```

- **Ligne**: 189
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `user_id`: `int`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.get_engine`
  - `sqlalchemy.text`

#### 🔹 `_row_to_user`

```python
def _row_to_user(self, row: dict) -> User:
```

- **Ligne**: 203
- **Réutilisabilité**: High
- **Type de retour**: `User`
- **Paramètres**:
  - `self`
  - `row`: `dict`

---

## Middleware

**50 fonctions**

### `backend/middleware/idempotency.py`

#### 🔹 `async dispatch` 🎀

```python
async def dispatch(self, request: Request, call_next: Callable) -> Response:
```

- **Ligne**: 56
- **Réutilisabilité**: Low
- **Type de retour**: `Response`
- **Paramètres**:
  - `self`
  - `request`: `Request`
  - `call_next`: `Callable`
- **Dépendances**:
  - `backend.cache.get_redis_client`
  - `datetime.datetime`
  - `fastapi.Request`
  - `fastapi.Response`
  - `json`
  - *... et 2 autres*

#### 🔹 `_build_cache_key` 🎀

```python
def _build_cache_key( self, idempotency_key: str,
```

**Description**: Construit une clé de cache unique pour la requête idempotente.

- **Ligne**: 174
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `idempotency_key`: `str`
  - `path`: `str`
  - `method`: `str`
  - `tenant_id`: `Optional[int]`
- **Dépendances**:
  - `hashlib`
  - `typing.Optional`

#### 🔹 `generate`

```python
def generate( action: str,
```

**Description**: Génère une clé d'idempotence déterministe.

- **Ligne**: 206
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Décorateurs**: `staticmethod`
- **Paramètres**:
  - `action`: `str`
  - `entity_id`: `Optional[int]` = `None`
  - `user_id`: `Optional[int]` = `None`
  - `extra`: `Optional[str]` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `hashlib`
  - `typing.Optional`

#### 🔹 `random`

```python
def random() -> str:
```

**Description**: Génère une clé d'idempotence aléatoire (pour les opérations non déterministes).

- **Ligne**: 239
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Décorateurs**: `staticmethod`
- **Dépendances**:
  - `uuid`

#### 🔸 `require_idempotency_key` 🎀

```python
def require_idempotency_key(request: Request) -> str:
```

**Description**: Dépendance FastAPI imposant une clé d'idempotence pour les opérations critiques.

- **Ligne**: 246
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `fastapi.Request`

#### 🔸 `has_idempotency_key`

```python
def has_idempotency_key(request: Request) -> bool:
```

**Description**: Vérifie si la requête possède une clé d'idempotence.

- **Ligne**: 272
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `fastapi.Request`

#### 🔸 `async get_idempotency_status`

```python
async def get_idempotency_status(idempotency_key: str, tenant_id: Optional[int] = None) -> dict:
```

**Description**: Récupère le statut d'une clé d'idempotence.

- **Ligne**: 278
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `idempotency_key`: `str`
  - `tenant_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `backend.cache.get_redis_client`
  - `json`
  - `typing.Optional`

### `backend/middleware/performance.py`

#### 🔹 `avg_duration_ms`

```python
def avg_duration_ms(self) -> float:
```

- **Ligne**: 47
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `error_rate`

```python
def error_rate(self) -> float:
```

- **Ligne**: 53
- **Réutilisabilité**: Medium
- **Type de retour**: `float`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `record`

```python
def record(self, duration_ms: float, is_error: bool, slow_threshold: float) -> None:
```

- **Ligne**: 58
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `duration_ms`: `float`
  - `is_error`: `bool`
  - `slow_threshold`: `float`

#### 🔹 `__init__`

```python
def __init__( self, failure_threshold: int = 5,
```

- **Ligne**: 81
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `failure_threshold`: `int` = `5`
  - `recovery_timeout`: `float` = `30.0`
  - `success_threshold`: `int` = `2`
- **Dépendances**:
  - `threading.Lock`

#### 🔹 `state`

```python
def state(self) -> CircuitState:
```

- **Ligne**: 98
- **Réutilisabilité**: Medium
- **Type de retour**: `CircuitState`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `time`

#### 🔹 `can_execute`

```python
def can_execute(self) -> bool:
```

- **Ligne**: 106
- **Réutilisabilité**: Medium
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`

#### 🔹 `record_success`

```python
def record_success(self) -> None:
```

- **Ligne**: 109
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`

#### 🔹 `record_failure`

```python
def record_failure(self) -> None:
```

- **Ligne**: 118
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `time`

#### 🔹 `__init__`

```python
def __init__( self, app, *, slow_threshold_ms: float = 500.0,
```

- **Ligne**: 151
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `app`
- **Dépendances**:
  - `collections.defaultdict`
  - `threading.Lock`
  - `typing.Callable`
  - `typing.Optional`

#### 🔹 `get_stats`

```python
def get_stats(self) -> dict[str, EndpointStats]:
```

**Description**: Retourne les statistiques actuelles.

- **Ligne**: 171
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, EndpointStats]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `collections.defaultdict`

#### 🔹 `async dispatch` 🎀

```python
async def dispatch(self, request: Request, call_next) -> Response:
```

- **Ligne**: 176
- **Réutilisabilité**: Medium
- **Type de retour**: `Response`
- **Paramètres**:
  - `self`
  - `request`: `Request`
  - `call_next`
- **Dépendances**:
  - `starlette.requests.Request`
  - `starlette.responses.Response`
  - `time`

#### 🔹 `_normalize_path`

```python
def _normalize_path(self, path: str) -> str:
```

**Description**: Normalise le path pour le groupement (remplace IDs par :id).

- **Ligne**: 218
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `path`: `str`

#### 🔹 `_apply_cache_control`

```python
def _apply_cache_control(self, response: Response, path: str) -> None:
```

**Description**: Applique le Cache-Control approprié.

- **Ligne**: 233
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `response`: `Response`
  - `path`: `str`
- **Dépendances**:
  - `starlette.responses.Response`

#### 🔸 `get_performance_stats`

```python
def get_performance_stats() -> dict[str, EndpointStats]:
```

**Description**: Récupère les statistiques de performance globales.

- **Ligne**: 248
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, EndpointStats]`
- **Dépendances**:
  - `collections.defaultdict`

#### 🔸 `create_performance_middleware` 🎀

```python
def create_performance_middleware(app, **kwargs) -> PerformanceMiddleware:
```

**Description**: Factory pour créer le middleware avec instance globale.

- **Ligne**: 255
- **Réutilisabilité**: Medium
- **Type de retour**: `PerformanceMiddleware`
- **Paramètres**:
  - `app`
- **Dépendances**:
  - `starlette.middleware.base.BaseHTTPMiddleware`

### `backend/middleware/rate_limiter.py`

#### 🔹 `key`

```python
def key(self) -> str:
```

- **Ligne**: 38
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`

#### 🔹 `__init__`

```python
def __init__(self, config: RateLimitConfig | None = None):
```

- **Ligne**: 58
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `config`: `RateLimitConfig | None` = `None`
- **Dépendances**:
  - `collections.defaultdict`
  - `time`

#### 🔹 `_get_client_key`

```python
def _get_client_key(self, request: Request) -> str:
```

**Description**: Extrait l'identifiant client depuis la requête.

- **Ligne**: 69
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `request`: `Request`
- **Dépendances**:
  - `fastapi.Request`

#### 🔹 `_refill_tokens`

```python
def _refill_tokens(self, entry: RateLimitEntry, now: float) -> None:
```

**Description**: Recharge les jetons selon le temps écoulé.

- **Ligne**: 84
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `entry`: `RateLimitEntry`
  - `now`: `float`

#### 🔹 `_cleanup_expired`

```python
def _cleanup_expired(self, now: float) -> None:
```

**Description**: Supprime les entrées expirées pour éviter la surcharge mémoire.

- **Ligne**: 96
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `now`: `float`

#### 🔹 `async check`

```python
async def check(self, request: Request) -> tuple[bool, dict[str, str]]:
```

**Description**: Check if request is allowed.

- **Ligne**: 114
- **Réutilisabilité**: Medium
- **Type de retour**: `tuple[bool, dict[str, str]]`
- **Paramètres**:
  - `self`
  - `request`: `Request`
- **Dépendances**:
  - `collections.defaultdict`
  - `fastapi.Request`
  - `time`

#### 🔸 `get_rate_limiter` 🎀

```python
def get_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
```

**Description**: Obtient ou crée l'instance globale du rate limiter.

- **Ligne**: 161
- **Réutilisabilité**: High
- **Type de retour**: `RateLimiter`
- **Paramètres**:
  - `config`: `RateLimitConfig | None` = `None`

#### 🔸 `rate_limit` 🎀

```python
def rate_limit( requests: int = 100,
```

**Description**: Decorator for rate limiting endpoints.

- **Ligne**: 169
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `requests`: `int` = `100`
  - `window`: `int` = `60`
  - `burst`: `int` = `10`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`
  - `functools.wraps`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `decorator` 🎀

```python
def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
```

- **Ligne**: 189
- **Réutilisabilité**: Medium
- **Type de retour**: `Callable[..., Any]`
- **Paramètres**:
  - `func`: `Callable[..., Any]`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`
  - `functools.wraps`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `async wrapper` 🎀

```python
async def wrapper(*args, **kwargs):
```

- **Ligne**: 194
- **Réutilisabilité**: Medium
- **Décorateurs**: `wraps(func)`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`
  - `functools.wraps`

#### 🔹 `__init__`

```python
def __init__( self, app, requests: int = 1000,
```

- **Ligne**: 235
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `app`
  - `requests`: `int` = `1000`
  - `window`: `int` = `60`
  - `burst`: `int` = `50`
  - `exclude_paths`: `list[str] | None` = `None`

#### 🔹 `async __call__`

```python
async def __call__(self, scope, receive, send):
```

- **Ligne**: 248
- **Réutilisabilité**: Low
- **Paramètres**:
  - `self`
  - `scope`
  - `receive`
  - `send`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`
  - `functools.wraps`
  - `typing.Any`
  - *... et 1 autres*

### `backend/middleware/request_context.py`

#### 🔸 `get_request_id`

```python
def get_request_id() -> str:
```

**Description**: Récupère l'ID de requête courant (utilisable partout).

- **Ligne**: 50
- **Réutilisabilité**: High
- **Type de retour**: `str`

#### 🔸 `get_request_context`

```python
def get_request_context() -> dict[str, Any]:
```

**Description**: Récupère le contexte complet de la requête courante.

- **Ligne**: 55
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `set_context_value`

```python
def set_context_value(key: str, value: Any) -> None:
```

**Description**: Ajoute une valeur au contexte de la requête courante.

- **Ligne**: 60
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `key`: `str`
  - `value`: `Any`
- **Dépendances**:
  - `typing.Any`

#### 🔸 `get_elapsed_ms`

```python
def get_elapsed_ms() -> float:
```

**Description**: Retourne le temps écoulé depuis le début de la requête.

- **Ligne**: 67
- **Réutilisabilité**: High
- **Type de retour**: `float`
- **Dépendances**:
  - `time`

#### 🔹 `__init__`

```python
def __init__( self, app, *, header_name: str = "X-Request-ID",
```

- **Ligne**: 86
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `app`
- **Dépendances**:
  - `typing.Callable`
  - `typing.Optional`

#### 🔹 `async dispatch` 🎀

```python
async def dispatch(self, request: Request, call_next) -> Response:
```

- **Ligne**: 101
- **Réutilisabilité**: Medium
- **Type de retour**: `Response`
- **Paramètres**:
  - `self`
  - `request`: `Request`
  - `call_next`
- **Dépendances**:
  - `starlette.requests.Request`
  - `starlette.responses.Response`
  - `time`
  - `typing.Optional`
  - `uuid`

#### 🔹 `_get_client_ip`

```python
def _get_client_ip(self, request: Request) -> str:
```

**Description**: Extrait l'IP client en tenant compte des proxies.

- **Ligne**: 158
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `request`: `Request`
- **Dépendances**:
  - `starlette.requests.Request`

#### 🔹 `_log_request`

```python
def _log_request(self, metrics: RequestMetrics) -> None:
```

**Description**: Log structuré de la requête.

- **Ligne**: 165
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `metrics`: `RequestMetrics`
- **Dépendances**:
  - `logging`

### `backend/middleware/response_wrapper.py`

#### 🔹 `from_status`

```python
def from_status(cls, status_code: int) -> tuple[str, str, str]:
```

**Description**: Mappe un code HTTP vers un code d'erreur.

- **Ligne**: 43
- **Réutilisabilité**: High
- **Type de retour**: `tuple[str, str, str]`
- **Décorateurs**: `classmethod`
- **Paramètres**:
  - `cls`
  - `status_code`: `int`

#### 🔸 `build_success_response` 🎀

```python
def build_success_response( data: Any,
```

**Description**: Construit une réponse de succès standardisée.

- **Ligne**: 60
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `data`: `Any`
- **Dépendances**:
  - `request_context.get_elapsed_ms`
  - `request_context.get_request_id`
  - `starlette.responses.JSONResponse`
  - `starlette.responses.Response`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `build_error_response`

```python
def build_error_response( code: str,
```

**Description**: Construit une réponse d'erreur standardisée.

- **Ligne**: 80
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `code`: `str`
  - `message`: `str`
- **Dépendances**:
  - `request_context.get_elapsed_ms`
  - `request_context.get_request_id`
  - `typing.Any`
  - `typing.Optional`

#### 🔹 `__init__`

```python
def __init__( self, app, *, exclude_paths: Optional[list[str]] = None,
```

- **Ligne**: 133
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `app`
- **Dépendances**:
  - `typing.Optional`

#### 🔹 `async dispatch` 🎀

```python
async def dispatch(self, request: Request, call_next) -> Response:
```

- **Ligne**: 149
- **Réutilisabilité**: Medium
- **Type de retour**: `Response`
- **Paramètres**:
  - `self`
  - `request`: `Request`
  - `call_next`
- **Dépendances**:
  - `json`
  - `request_context.get_elapsed_ms`
  - `request_context.get_request_id`
  - `starlette.requests.Request`
  - `starlette.responses.JSONResponse`
  - *... et 3 autres*

#### 🔹 `_is_already_wrapped`

```python
def _is_already_wrapped(self, data: Any) -> bool:
```

**Description**: Vérifie si la réponse est déjà au format standardisé.

- **Ligne**: 203
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `data`: `Any`
- **Dépendances**:
  - `typing.Any`

#### 🔹 `_wrap_success`

```python
def _wrap_success(self, data: Any, status_code: int) -> dict[str, Any]:
```

**Description**: Wrappe une réponse de succès.

- **Ligne**: 209
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `self`
  - `data`: `Any`
  - `status_code`: `int`
- **Dépendances**:
  - `request_context.get_elapsed_ms`
  - `request_context.get_request_id`
  - `typing.Any`

#### 🔹 `_wrap_error`

```python
def _wrap_error(self, data: Any, status_code: int) -> dict[str, Any]:
```

**Description**: Wrappe une réponse d'erreur.

- **Ligne**: 234
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `self`
  - `data`: `Any`
  - `status_code`: `int`
- **Dépendances**:
  - `logging`
  - `request_context.get_elapsed_ms`
  - `request_context.get_request_id`
  - `starlette.middleware.base.BaseHTTPMiddleware`
  - `starlette.requests.Request`
  - *... et 4 autres*

---

## Invoicing

**32 fonctions**

### `backend/services/invoice_utils.py`

#### 🔸 `prepare_invoice_dataframe` 🎀

```python
def prepare_invoice_dataframe(source_df: pd.DataFrame, margin_rate: float) -> pd.DataFrame:
```

**Description**: Normalise les colonnes numériques et calcule marges/totaux pour les lignes de facture.

- **Ligne**: 8
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `source_df`: `pd.DataFrame`
  - `margin_rate`: `float`

### `backend/services/invoices.py`

#### 🔸 `normalize_supplier_name` 🎀

```python
def normalize_supplier_name(supplier: str | None) -> str:
```

**Description**: Normalise le nom d'un fournisseur selon les conventions standard.

- **Ligne**: 39
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `supplier`: `str | None`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.invoice_utils.prepare_invoice_dataframe`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.inventory_service.match_invoice_products`
  - *... et 8 autres*

#### 🔸 `detect_supplier_from_invoice`

```python
def detect_supplier_from_invoice(invoice_df: pd.DataFrame, raw_text: str | None = None) -> str:
```

**Description**: Détecte automatiquement le fournisseur à partir des données de facture.

- **Ligne**: 67
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
  - `raw_text`: `str | None` = `None`
- **Dépendances**:
  - `core.invoice_extractor`
  - `core.pdf_utils.split_pdf_into_invoices`

#### 🔸 `get_last_invoice_sequence`

```python
def get_last_invoice_sequence(tenant_id: int = 1) -> int:
```

**Description**: Récupère le dernier numéro de séquence INV-XXX depuis la base.

- **Ligne**: 110
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `tenant_id`: `int` = `1`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.invoice_utils.prepare_invoice_dataframe`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.inventory_service.match_invoice_products`
  - *... et 9 autres*

#### 🔸 `extract_invoice_lines` 🎀

```python
def extract_invoice_lines( text: str,
```

**Description**: Extrait des lignes structurées depuis le texte brut d'une facture.

- **Ligne**: 132
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `text`: `str`
- **Dépendances**:
  - `core.parsers.parse_invoice`
  - `core.pdf_utils.split_pdf_into_invoices`
  - `sqlalchemy.text`

#### 🔸 `enrich_lines_with_catalog` 🎀

```python
def enrich_lines_with_catalog( lines: pd.DataFrame,
```

**Description**: Associe les métadonnées catalogue (matchs) aux lignes de facture parsées.

- **Ligne**: 309
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `lines`: `pd.DataFrame`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.services.invoice_utils.prepare_invoice_dataframe`
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.inventory_service.match_invoice_products`
  - *... et 15 autres*

#### 🔸 `apply_invoice_import` 🎀

```python
def apply_invoice_import( invoice_df: pd.DataFrame,
```

**Description**: Persiste les mouvements à partir des lignes de facture.

- **Ligne**: 469
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `core.inventory_service.register_invoice_reception`
  - `core.pdf_utils.split_pdf_into_invoices`
  - `datetime.date`
  - `datetime.datetime`
  - `datetime.time`
  - *... et 1 autres*

#### 🔸 `import_catalog_from_invoice` 🎀

```python
def import_catalog_from_invoice( invoice_df: pd.DataFrame,
```

**Description**: Crée/met à jour le catalogue depuis les lignes de facture et journalise l'historique de prix.

- **Ligne**: 503
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `core.pdf_utils.split_pdf_into_invoices`
  - `core.price_history_service.record_price_history`
  - `core.products_loader`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 2 autres*

#### 🔸 `record_processed_invoices`

```python
def record_processed_invoices(invoice_df: pd.DataFrame, *, supplier: str | None, tenant_id: int) -> None:
```

- **Ligne**: 612
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.pdf_utils.split_pdf_into_invoices`
  - `sqlalchemy.text`

#### 🔸 `find_processed_invoice_ids`

```python
def find_processed_invoice_ids(invoice_ids: set[str], *, tenant_id: int) -> set[str]:
```

- **Ligne**: 757
- **Réutilisabilité**: High
- **Type de retour**: `set[str]`
- **Paramètres**:
  - `invoice_ids`: `set[str]`
- **Dépendances**:
  - `core.pdf_utils.split_pdf_into_invoices`

#### 🔸 `list_processed_invoices`

```python
def list_processed_invoices( *, tenant_id: int,
```

- **Ligne**: 764
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, object]]`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.pdf_utils.split_pdf_into_invoices`
  - `sqlalchemy.text`

#### 🔸 `persist_invoice_documents` 🎀

```python
def persist_invoice_documents(pdf_bytes: bytes, *, tenant_id: int, supplier: str | None = None) -> dict[str, dict[str, str]]:
```

**Description**: Découpe et stocke physiquement chaque facture détectée.

- **Ligne**: 806
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, dict[str, str]]`
- **Paramètres**:
  - `pdf_bytes`: `bytes`
- **Dépendances**:
  - `core.pdf_utils.split_pdf_into_invoices`

#### 🔸 `get_processed_invoice_file` 🎀

```python
def get_processed_invoice_file(*, tenant_id: int, invoice_id: str) -> Path | None:
```

- **Ligne**: 834
- **Réutilisabilité**: Medium
- **Type de retour**: `Path | None`
- **Dépendances**:
  - `core.data_repository.exec_sql`
  - `core.data_repository.query_df`
  - `core.pdf_utils.split_pdf_into_invoices`
  - `pathlib.Path`
  - `sqlalchemy.text`

### `backend/tasks/invoices.py`

#### 🔸 `process_invoice`

```python
def process_invoice(self, invoice_id: int, tenant_id: int):
```

**Description**: Traite une facture (OCR, parsing, validation).

- **Ligne**: 6
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(bind=True, max_retries=3, queue='invoices')`
- **Paramètres**:
  - `self`
  - `invoice_id`: `int`
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `sync_pending`

```python
def sync_pending():
```

**Description**: Synchronise les factures en attente.

- **Ligne**: 16
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task(queue='invoices')`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `batch_import_invoices`

```python
def batch_import_invoices(self, file_path: str, tenant_id: int):
```

**Description**: Importe des factures depuis un fichier batch.

- **Ligne**: 22
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(bind=True, queue='invoices')`
- **Paramètres**:
  - `self`
  - `file_path`: `str`
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.worker.app`

### `core/invoice_extractor.py`

#### 🔹 `__init__`

```python
def __init__(self, *_args, **_kwargs): # Constructeur factice
```

- **Ligne**: 25
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`

#### 🔸 `register_invoice_parser`

```python
def register_invoice_parser(name: str, handler: Callable[..., pd.DataFrame]) -> None:
```

**Description**: Expose un parseur supplémentaire (permet d'ajouter d'autres fournisseurs).

- **Ligne**: 101
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `name`: `str`
  - `handler`: `Callable[..., pd.DataFrame]`
- **Dépendances**:
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`
  - `typing.Callable`

#### 🔸 `detect_invoice_format` 🎀

```python
def detect_invoice_format(raw_text: str, supplier_hint: str | None = None) -> str:
```

**Description**: Détermine le parseur à utiliser selon le hint ou des heuristiques.

- **Ligne**: 109
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `raw_text`: `str`
  - `supplier_hint`: `str | None` = `None`

#### 🔸 `extract_products`

```python
def extract_products( raw_product_text: str,
```

**Description**: Route vers le parseur détecté (fallback générique).

- **Ligne**: 134
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`

#### 🔸 `clean_data` 🎀

```python
def clean_data(value):
```

**Description**: Nettoie une valeur numérique (remplace la virgule par le point).

- **Ligne**: 154
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `value`

#### 🔸 `extract_text_from_file` 🎀

```python
def extract_text_from_file(uploaded_file):
```

**Description**: Extrait le texte brut d'un fichier téléversé (PDF, DOCX, TXT, etc.).

- **Ligne**: 162
- **Réutilisabilité**: Low
- **Paramètres**:
  - `uploaded_file`
- **Dépendances**:
  - `PyPDF2.PdfReader`
  - `__future__.annotations`
  - `docx.Document`
  - `io`
  - `pathlib.Path`
  - *... et 2 autres*

#### 🔸 `extract_products_from_metro_invoice` 🎀

```python
def extract_products_from_metro_invoice( raw_product_text: str,
```

**Description**: Analyse une facture METRO : parse lignes, infère prix/quantités/TVA et construit un DataFrame standardisé.

- **Ligne**: 610
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `PyPDF2.PdfReader`
  - `__future__.annotations`
  - `io`
  - `pathlib.Path`
  - `pdfminer.high_level.extract_text`
  - *... et 6 autres*

#### 🔸 `extract_products_from_generic_invoice`

```python
def extract_products_from_generic_invoice( raw_product_text: str,
```

**Description**: Parseur générique - fallback vers le parseur Metro en attendant d'autres formats.

- **Ligne**: 935
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`

#### 🔸 `extract_products_from_pomona_invoice`

```python
def extract_products_from_pomona_invoice(raw_product_text: str, *, margin_rate: float = 0.0, start_invoice_sequence: int = 0) -> pd.DataFrame:
```

**Description**: Prétraitement Pomona (numerotation différente, colonnes séparées par tab).

- **Ligne**: 948
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`

#### 🔸 `extract_products_from_transgourmet_invoice`

```python
def extract_products_from_transgourmet_invoice(raw_product_text: str, *, margin_rate: float = 0.0, start_invoice_sequence: int = 0) -> pd.DataFrame:
```

**Description**: Transgourmet : colonnes alignées, suffixes 'HT'. Enlève mentions spécifiques.

- **Ligne**: 956
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`

#### 🔸 `extract_products_from_eurociel_invoice`

```python
def extract_products_from_eurociel_invoice( raw_product_text: str,
```

**Description**: Parser spécifique pour les factures Eurociel.

- **Ligne**: 1020
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`
  - `re`

#### 🔸 `extract_products_from_taiyat_invoice`

```python
def extract_products_from_taiyat_invoice( raw_product_text: str,
```

**Description**: Parser spécifique pour les factures TAIYAT (TAI YAT).

- **Ligne**: 1232
- **Réutilisabilité**: Medium
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `raw_product_text`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `pdfminer.high_level.extract_text`
  - `pypdf.PdfReader`
  - `re`

### `core/invoice_workflow.py`

#### 🔹 `__init__`

```python
def __init__(self):
```

- **Ligne**: 151
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.List`
  - `typing.Optional`

#### 🔹 `to_dict`

```python
def to_dict(self) -> Dict[str, Any]:
```

- **Ligne**: 164
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `typing.Any`
  - `typing.Dict`

#### 🔸 `import_invoice_complete` 🎀

```python
def import_invoice_complete( invoice_df: pd.DataFrame,
```

**Description**: Import complet d'une facture en UNE SEULE TRANSACTION.

- **Ligne**: 179
- **Réutilisabilité**: Medium
- **Type de retour**: `InvoiceImportResult`
- **Paramètres**:
  - `invoice_df`: `pd.DataFrame`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.get_engine`
  - `core.data_repository.query_df`
  - `core.event_handlers.register_all_handlers`
  - `core.finance.event_sourcing.EventDispatcher`
  - *... et 14 autres*

#### 🔸 `get_invoice_workflow_summary`

```python
def get_invoice_workflow_summary(tenant_id: int, days: int = 30) -> Dict[str, Any]:
```

**Description**: Retourne un résumé des imports de factures récents.

- **Ligne**: 442
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `tenant_id`: `int`
  - `days`: `int` = `30`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Any`
  - `typing.Dict`

---

## Data Retrieval

**31 fonctions**

### `backend/dependencies/security.py`

#### 🔸 `get_current_user_from_request`

```python
def get_current_user_from_request(request: Request) -> AuthenticatedUser:
```

**Description**: Récupère l'utilisateur courant depuis le cookie HTTP-Only.

- **Ligne**: 200
- **Réutilisabilité**: High
- **Type de retour**: `AuthenticatedUser`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `core.user_service.ALLOWED_ROLES`
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - `fastapi.status`

#### 🔸 `get_current_user`

```python
def get_current_user(token: str | None = Depends(oauth2_scheme)) -> AuthenticatedUser:
```

**Description**: Héritage : récupère l'utilisateur depuis un token Bearer OAuth2.

- **Ligne**: 243
- **Réutilisabilité**: High
- **Type de retour**: `AuthenticatedUser`
- **Paramètres**:
  - `token`: `str | None` = `Depends(oauth2_scheme)`
- **Dépendances**:
  - `core.user_service.ALLOWED_ROLES`
  - `fastapi.Depends`
  - `fastapi.HTTPException`
  - `fastapi.status`

### `backend/dependencies/tenant.py`

#### 🔸 `async get_current_tenant` 🎀

```python
async def get_current_tenant(request: Request) -> Tenant:
```

**Description**: Récupère le tenant courant depuis l'utilisateur authentifié (cookies ou bearer).

- **Ligne**: 76
- **Réutilisabilité**: High
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `backend.dependencies.security._extract_token_from_request`
  - `backend.dependencies.security.get_current_user_from_request`
  - `core.tenant_service.ensure_tenants_table`
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - *... et 1 autres*

#### 🔸 `async get_current_tenant_or_default`

```python
async def get_current_tenant_or_default(request: Request) -> Tenant:
```

**Description**: Variante permissive pour le newCMS : accepte l'absence de token en mode démo.

- **Ligne**: 93
- **Réutilisabilité**: Medium
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `backend.dependencies.security._extract_token_from_request`
  - `backend.dependencies.security.get_current_user_from_request`
  - `core.data_repository.get_engine`
  - `core.tenant_service.ensure_tenants_table`
  - `fastapi.HTTPException`
  - *... et 3 autres*

#### 🔸 `async get_restaurant_tenant` 🎀

```python
async def get_restaurant_tenant(request: Request) -> Tenant:
```

**Description**: Dépendance pour le module restaurant.

- **Ligne**: 131
- **Réutilisabilité**: High
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `fastapi.Request`

#### 🔸 `async get_restaurant_tenant_strict` 🎀

```python
async def get_restaurant_tenant_strict(request: Request) -> Tenant:
```

**Description**: Dépendance pour le module restaurant avec authentification obligatoire.

- **Ligne**: 141
- **Réutilisabilité**: High
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `backend.dependencies.security._extract_token_from_request`
  - `backend.dependencies.security.get_current_user_from_request`
  - `fastapi.Request`

#### 🔸 `async get_intelligence_tenant` 🎀

```python
async def get_intelligence_tenant(request: Request) -> Tenant:
```

**Description**: Dépendance pour le module intelligence/scoring.

- **Ligne**: 150
- **Réutilisabilité**: High
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `backend.dependencies.security._extract_token_from_request`
  - `backend.dependencies.security.get_current_user_from_request`
  - `fastapi.Request`

#### 🔸 `async get_epicerie_tenant` 🎀

```python
async def get_epicerie_tenant(request: Request) -> Tenant:
```

**Description**: Dépendance pour le module épicerie (operations, catalogue, etc.).

- **Ligne**: 159
- **Réutilisabilité**: High
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `backend.dependencies.security._extract_token_from_request`
  - `backend.dependencies.security.get_current_user_from_request`
  - `fastapi.Request`

#### 🔸 `async get_tenant_by_route` 🎀

```python
async def get_tenant_by_route(request: Request) -> Tenant:
```

**Description**: Dépendance intelligente qui détermine le tenant selon la route.

- **Ligne**: 168
- **Réutilisabilité**: Medium
- **Type de retour**: `Tenant`
- **Paramètres**:
  - `request`: `Request`
- **Dépendances**:
  - `backend.dependencies.security._extract_token_from_request`
  - `backend.dependencies.security.get_current_user_from_request`
  - `core.tenant_service.ensure_tenants_table`
  - `fastapi.HTTPException`
  - `fastapi.Request`
  - *... et 1 autres*

### `core/backup_manager.py`

#### 🔸 `load_backup_settings` 🎀

```python
def load_backup_settings( directory: str | os.PathLike[str] | None = None,
```

**Description**: Retourne les paramètres d'automatisation de sauvegarde persistés.

- **Ligne**: 85
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, object]`
- **Paramètres**:
  - `directory`: `str | os.PathLike[str] | None` = `None`
- **Dépendances**:
  - `json`
  - `os`
  - `pathlib.Path`
  - `sqlalchemy.engine.url.make_url`
  - `typing.Dict`

#### 🔸 `get_backup_directory` 🎀

```python
def get_backup_directory( directory: str | os.PathLike[str] | None = None,
```

**Description**: Retourne le répertoire utilisé pour stocker les fichiers de sauvegarde.

- **Ligne**: 122
- **Réutilisabilité**: High
- **Type de retour**: `Path`
- **Paramètres**:
  - `directory`: `str | os.PathLike[str] | None` = `None`
- **Dépendances**:
  - `os`
  - `pathlib.Path`
  - `typing.Tuple`

### `core/bank_import/categories.py`

#### 🔸 `get_category`

```python
def get_category(code: str) -> Optional[CategoryDefinition]:
```

**Description**: Get category definition by code.

- **Ligne**: 347
- **Réutilisabilité**: High
- **Type de retour**: `Optional[CategoryDefinition]`
- **Paramètres**:
  - `code`: `str`
- **Dépendances**:
  - `typing.Optional`

#### 🔸 `get_all_categories`

```python
def get_all_categories() -> List[CategoryDefinition]:
```

**Description**: Get all category definitions sorted by priority (highest first).

- **Ligne**: 352
- **Réutilisabilité**: Medium
- **Type de retour**: `List[CategoryDefinition]`
- **Dépendances**:
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `typing.Dict`
  - `typing.List`

#### 🔸 `get_categories_for_direction`

```python
def get_categories_for_direction(direction: str) -> List[CategoryDefinition]:
```

**Description**: Get categories matching a direction (IN, OUT, or BOTH).

- **Ligne**: 361
- **Réutilisabilité**: High
- **Type de retour**: `List[CategoryDefinition]`
- **Paramètres**:
  - `direction`: `str`
- **Dépendances**:
  - `typing.List`

### `core/bank_import/categorizer.py`

#### 🔹 `_load_db_rules`

```python
def _load_db_rules(self) -> None:
```

**Description**: Load categorization rules from finance_rules table.

- **Ligne**: 83
- **Réutilisabilité**: Low
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `__future__.annotations`
  - `categories.CATEGORIES`
  - `categories.CategoryDefinition`
  - `categories.KEYWORD_INDEX`
  - `categories.get_all_categories`
  - *... et 7 autres*

#### 🔹 `_get_keywords_for_category` 🎀

```python
def _get_keywords_for_category(self, cat: CategoryDefinition) -> List[Tuple[str, float]]:
```

**Description**: Get keywords for a category with their confidence bonus.

- **Ligne**: 196
- **Réutilisabilité**: Medium
- **Type de retour**: `List[Tuple[str, float]]`
- **Paramètres**:
  - `self`
  - `cat`: `CategoryDefinition`
- **Dépendances**:
  - `categories.CATEGORIES`
  - `categories.CategoryDefinition`
  - `categories.KEYWORD_INDEX`
  - `categories.get_all_categories`
  - `models.BankType`
  - *... et 2 autres*

#### 🔸 `get_feedback_stats`

```python
def get_feedback_stats() -> Dict:
```

**Description**: Get statistics about categorization feedback.

- **Ligne**: 487
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Dict`

#### 🔸 `get_common_corrections`

```python
def get_common_corrections(limit: int = 20) -> List[Dict]:
```

**Description**: Get the most common categorization corrections.

- **Ligne**: 526
- **Réutilisabilité**: High
- **Type de retour**: `List[Dict]`
- **Paramètres**:
  - `limit`: `int` = `20`
- **Dépendances**:
  - `core.data_repository.exec_sql_return_id`
  - `core.data_repository.query_df`
  - `sqlalchemy.text`
  - `typing.Dict`
  - `typing.List`

### `core/bank_import/deduplicator.py`

#### 🔹 `load_existing_checksums`

```python
def load_existing_checksums( self, account_id: int,
```

**Description**: Load existing checksums from database with occurrence counts.

- **Ligne**: 68
- **Réutilisabilité**: Medium
- **Type de retour**: `Set[str]`
- **Paramètres**:
  - `self`
  - `account_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `datetime.date`
  - `sqlalchemy.text`
  - `typing.Set`

#### 🔹 `load_existing_transactions`

```python
def load_existing_transactions( self, account_id: int,
```

**Description**: Load existing transactions for fuzzy matching.

- **Ligne**: 244
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `account_id`: `int`
  - `period_start`: `date`
  - `period_end`: `date`
- **Dépendances**:
  - `datetime.date`
  - `datetime.timedelta`
  - `decimal.Decimal`
  - `sqlalchemy.text`

### `core/bank_import/detector.py`

#### 🔹 `get_detection_details`

```python
def get_detection_details(self) -> dict[str, int]:
```

**Description**: Get detailed detection scores for debugging.

- **Ligne**: 227
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, int]`
- **Paramètres**:
  - `self`

### `core/bank_import/extractor.py`

#### 🔹 `get_lines_for_period` 🎀

```python
def get_lines_for_period( self, lines: List[str],
```

**Description**: Get lines belonging to a specific period.

- **Ligne**: 373
- **Réutilisabilité**: Medium
- **Type de retour**: `List[str]`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
  - `period_line_ranges`: `Optional[dict]` = `None`
- **Dépendances**:
  - `models.StatementPeriod`
  - `typing.List`
  - `typing.Optional`

### `core/bank_import/parser.py`

#### 🔹 `_get_columns`

```python
def _get_columns(self, bank_type: BankType) -> ColumnPositions:
```

**Description**: Retourne les positions de colonnes selon le type de banque.

- **Ligne**: 353
- **Réutilisabilité**: High
- **Type de retour**: `ColumnPositions`
- **Paramètres**:
  - `self`
  - `bank_type`: `BankType`
- **Dépendances**:
  - `models.BankType`
  - `models.ColumnPositions`

#### 🔹 `get_parser`

```python
def get_parser(self, bank_type: BankType) -> UnifiedBankParser:
```

**Description**: Récupère une instance de parseur pour un type de banque.

- **Ligne**: 1146
- **Réutilisabilité**: High
- **Type de retour**: `UnifiedBankParser`
- **Paramètres**:
  - `self`
  - `bank_type`: `BankType`
- **Dépendances**:
  - `models.BankType`

#### 🔹 `get_available_banks`

```python
def get_available_banks(self) -> List[BankType]:
```

**Description**: Retourne la liste des types de banque pris en charge.

- **Ligne**: 1151
- **Réutilisabilité**: Medium
- **Type de retour**: `List[BankType]`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `models.BankType`
  - `typing.List`

#### 🔸 `get_parser`

```python
def get_parser(bank_type: BankType) -> UnifiedBankParser:
```

**Description**: Fonction fabrique pour obtenir le parseur adapté à un type de banque.

- **Ligne**: 1160
- **Réutilisabilité**: High
- **Type de retour**: `UnifiedBankParser`
- **Paramètres**:
  - `bank_type`: `BankType`
- **Dépendances**:
  - `models.BankType`

### `core/data_repository.py`

#### 🔸 `get_engine`

```python
def get_engine() -> Engine:
```

**Description**: Retourne le moteur SQLAlchemy, mis en cache via functools (sans dépendance Streamlit).

- **Ligne**: 19
- **Réutilisabilité**: Medium
- **Type de retour**: `Engine`
- **Décorateurs**: `lru_cache(maxsize=1)`
- **Dépendances**:
  - `functools.lru_cache`
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`

#### 🔸 `get_product_options`

```python
def get_product_options(*, tenant_id: int = 1) -> list[tuple[str, int]]:
```

**Description**: Retourne la liste des produits actifs (nom, id) triés par nom pour un tenant donné.

- **Ligne**: 128
- **Réutilisabilité**: Medium
- **Type de retour**: `list[tuple[str, int]]`
- **Dépendances**:
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`
  - `sqlalchemy.sql.elements.ClauseElement`
  - `sqlalchemy.sql.elements.TextClause`
  - `sqlalchemy.text`

#### 🔸 `get_product_details`

```python
def get_product_details(identifier: str | int, *, tenant_id: int = 1) -> dict | None:
```

**Description**: Recherche les détails d'un produit par son ID ou un de ses codes-barres.

- **Ligne**: 145
- **Réutilisabilité**: Medium
- **Type de retour**: `dict | None`
- **Paramètres**:
  - `identifier`: `str | int`
- **Dépendances**:
  - `sqlalchemy.create_engine`
  - `sqlalchemy.engine.Engine`
  - `sqlalchemy.text`

### `core/products_loader.py`

#### 🔸 `load_products_from_df` 🎀

```python
def load_products_from_df( df: pd.DataFrame,
```

**Description**: Charge les produits à partir d'un DataFrame et retourne un résumé détaillé.

- **Ligne**: 693
- **Réutilisabilité**: Medium
- **Type de retour**: `Dict[str, Any]`
- **Paramètres**:
  - `df`: `pd.DataFrame`
- **Dépendances**:
  - `__future__.annotations`
  - `data_repository.get_engine`
  - `datetime.datetime`
  - `io`
  - `sqlalchemy.engine.Connection`
  - *... et 5 autres*

### `core/vendor_categories.py`

#### 🔸 `load_vendor_category_rules`

```python
def load_vendor_category_rules() -> tuple[tuple[tuple[str, ...], str, Sequence[str] | None], ...]:
```

**Description**: Charge la table `data/vendor_category_mapping.csv` pour étendre les règles.

- **Ligne**: 25
- **Réutilisabilité**: High
- **Type de retour**: `tuple[tuple[tuple[str, ...], str, Sequence[str] | None], ...]`
- **Dépendances**:
  - `csv`
  - `typing.Sequence`

---

## Document Processing

**24 fonctions**

### `core/bank_import/USAGE_EXAMPLES.py`

#### 🔹 `can_parse`

```python
def can_parse(self, text: str) -> bool:
```

**Description**: Vérifie si ce parser peut traiter le texte donné.

- **Ligne**: 89
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `text`: `str`

#### 🔹 `parse`

```python
def parse( self, lines: List[str],
```

**Description**: Parse les lignes du relevé Crédit Agricole.

- **Ligne**: 105
- **Réutilisabilité**: Medium
- **Type de retour**: `ParsedStatement`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
- **Dépendances**:
  - `core.bank_import.BankType`
  - `core.bank_import.BaseBankParser`
  - `core.bank_import.ParsedStatement`
  - `core.bank_import.StatementPeriod`
  - `core.bank_import.detect_bank_full`
  - *... et 3 autres*

### `core/bank_import/detector.py`

#### 🔹 `detect`

```python
def detect(self, text: str) -> Tuple[BankType, float]:
```

**Description**: Detect bank type from text content.

- **Ligne**: 146
- **Réutilisabilité**: Medium
- **Type de retour**: `Tuple[BankType, float]`
- **Paramètres**:
  - `self`
  - `text`: `str`
- **Dépendances**:
  - `models.BankType`
  - `typing.Tuple`

#### 🔹 `extract_account_number`

```python
def extract_account_number(self, text: str, bank_type: BankType) -> Optional[str]:
```

**Description**: Extract account number based on bank type.

- **Ligne**: 205
- **Réutilisabilité**: High
- **Type de retour**: `Optional[str]`
- **Paramètres**:
  - `self`
  - `text`: `str`
  - `bank_type`: `BankType`
- **Dépendances**:
  - `models.BankType`
  - `typing.Optional`

#### 🔹 `detect_full`

```python
def detect_full(self, text: str) -> DetectionResult:
```

**Description**: Perform full detection with IBAN and BIC extraction.

- **Ligne**: 231
- **Réutilisabilité**: High
- **Type de retour**: `DetectionResult`
- **Paramètres**:
  - `self`
  - `text`: `str`
- **Dépendances**:
  - `models.BankType`

#### 🔹 `extract_iban`

```python
def extract_iban(self, text: str, bank_type: Optional[BankType] = None) -> Optional[str]:
```

**Description**: Extract IBAN from text.

- **Ligne**: 272
- **Réutilisabilité**: High
- **Type de retour**: `Optional[str]`
- **Paramètres**:
  - `self`
  - `text`: `str`
  - `bank_type`: `Optional[BankType]` = `None`
- **Dépendances**:
  - `models.BankType`
  - `typing.Optional`

#### 🔹 `extract_bic`

```python
def extract_bic(self, text: str) -> Optional[str]:
```

**Description**: Extract BIC/SWIFT code from text.

- **Ligne**: 300
- **Réutilisabilité**: High
- **Type de retour**: `Optional[str]`
- **Paramètres**:
  - `self`
  - `text`: `str`
- **Dépendances**:
  - `typing.Optional`

#### 🔸 `detect_bank_type`

```python
def detect_bank_type(text: str) -> Tuple[BankType, float, Optional[str]]:
```

**Description**: Enhanced bank type detection with confidence and IBAN.

- **Ligne**: 315
- **Réutilisabilité**: High
- **Type de retour**: `Tuple[BankType, float, Optional[str]]`
- **Paramètres**:
  - `text`: `str`
- **Dépendances**:
  - `models.BankType`
  - `typing.Optional`
  - `typing.Tuple`

#### 🔸 `detect_bank_type_simple` 🎀

```python
def detect_bank_type_simple(text: str) -> BankType:
```

**Description**: Simple bank type detection (backward compatibility).

- **Ligne**: 342
- **Réutilisabilité**: High
- **Type de retour**: `BankType`
- **Paramètres**:
  - `text`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `models.BankType`

#### 🔸 `detect_bank_full`

```python
def detect_bank_full(text: str) -> DetectionResult:
```

**Description**: Convenience function for full bank detection with IBAN extraction.

- **Ligne**: 360
- **Réutilisabilité**: High
- **Type de retour**: `DetectionResult`
- **Paramètres**:
  - `text`: `str`

### `core/bank_import/extractor.py`

#### 🔹 `extract_text`

```python
def extract_text(self, pdf_path: Path) -> str:
```

**Description**: Extract raw text from PDF using pdftotext.

- **Ligne**: 93
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `pdf_path`: `Path`
- **Dépendances**:
  - `__future__.annotations`
  - `dataclasses.dataclass`
  - `datetime.date`
  - `models.BankType`
  - `models.StatementPeriod`
  - *... et 4 autres*

#### 🔹 `extract`

```python
def extract(self, pdf_path: Path) -> ExtractionResult:
```

**Description**: Extract and preprocess PDF content.

- **Ligne**: 125
- **Réutilisabilité**: High
- **Type de retour**: `ExtractionResult`
- **Paramètres**:
  - `self`
  - `pdf_path`: `Path`
- **Dépendances**:
  - `pathlib.Path`

#### 🔹 `_detect_periods`

```python
def _detect_periods( self, full_text: str, lines: List[str]
```

**Description**: Detect statement periods from text.

- **Ligne**: 158
- **Réutilisabilité**: Medium
- **Type de retour**: `Tuple[List[StatementPeriod], dict]`
- **Paramètres**:
  - `self`
  - `full_text`: `str`
  - `lines`: `List[str]`
- **Dépendances**:
  - `__future__.annotations`
  - `datetime.date`
  - `models.BankType`
  - `models.StatementPeriod`
  - `pathlib.Path`
  - *... et 5 autres*

#### 🔸 `extract_pdf_text`

```python
def extract_pdf_text(pdf_path: Path) -> str:
```

**Description**: Convenience function to extract PDF text.

- **Ligne**: 414
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `pdf_path`: `Path`
- **Dépendances**:
  - `pathlib.Path`

### `core/bank_import/models.py`

#### 🔹 `actual_transaction_credits`

```python
def actual_transaction_credits(self) -> Decimal:
```

**Description**: Actual credit transactions (excluding ANCIEN SOLDE if crediteur).

- **Ligne**: 99
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔹 `actual_transaction_debits`

```python
def actual_transaction_debits(self) -> Decimal:
```

**Description**: Actual debit transactions (excluding ANCIEN SOLDE if debiteur).

- **Ligne**: 111
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔹 `for_lcl`

```python
def for_lcl(cls) -> "ColumnPositions":
```

**Description**: LCL bank column positions.

- **Ligne**: 283
- **Réutilisabilité**: Medium
- **Type de retour**: `'ColumnPositions'`
- **Décorateurs**: `classmethod`
- **Paramètres**:
  - `cls`

### `core/bank_import/orchestrator.py`

#### 🔹 `import_pdf`

```python
def import_pdf( self, pdf_path: Path,
```

**Description**: Import a bank statement PDF.

- **Ligne**: 77
- **Réutilisabilité**: Low
- **Type de retour**: `ImportResult`
- **Paramètres**:
  - `self`
  - `pdf_path`: `Path`
  - `entity_code`: `str`
  - `account_label`: `str`
  - `account_id_override`: `Optional[int]` = `None`
- **Dépendances**:
  - `__future__.annotations`
  - `categorizer.TransactionCategorizer`
  - `datetime.datetime`
  - `decimal.Decimal`
  - `deduplicator.TransactionDeduplicator`
  - *... et 15 autres*

#### 🔹 `_import_sumup`

```python
def _import_sumup( self, full_text: str,
```

**Description**: Import SumUp statement using specialized parser.

- **Ligne**: 471
- **Réutilisabilité**: Medium
- **Type de retour**: `ImportResult`
- **Paramètres**:
  - `self`
  - `full_text`: `str`
  - `account_id`: `int`
  - `source_file`: `str`
  - `result`: `ImportResult`
- **Dépendances**:
  - `__future__.annotations`
  - `categorizer.TransactionCategorizer`
  - `datetime.datetime`
  - `decimal.Decimal`
  - `deduplicator.TransactionDeduplicator`
  - *... et 13 autres*

### `core/bank_import/parser.py`

#### 🔹 `parse`

```python
def parse( self, lines: List[str],
```

**Description**: Analyse les lignes du relevé en données structurées.

- **Ligne**: 50
- **Réutilisabilité**: High
- **Type de retour**: `ParsedStatement`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
- **Dépendances**:
  - `abc.abstractmethod`
  - `models.ParsedStatement`
  - `models.StatementPeriod`
  - `typing.List`

#### 🔹 `can_parse`

```python
def can_parse(self, text: str) -> bool:
```

**Description**: Vérifie si ce parseur peut gérer le texte fourni.

- **Ligne**: 66
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `text`: `str`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `parse`

```python
def parse( self, lines: List[str],
```

**Description**: Analyse les lignes du relevé en données structurées.

- **Ligne**: 110
- **Réutilisabilité**: High
- **Type de retour**: `ParsedStatement`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
- **Dépendances**:
  - `abc.abstractmethod`
  - `models.ParsedStatement`
  - `models.StatementPeriod`
  - `typing.List`

#### 🔹 `can_parse`

```python
def can_parse(self, text: str) -> bool:
```

**Description**: Vérifie si ce parseur peut gérer le texte fourni.

- **Ligne**: 130
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Décorateurs**: `abstractmethod`
- **Paramètres**:
  - `self`
  - `text`: `str`
- **Dépendances**:
  - `abc.abstractmethod`

#### 🔹 `_detect_ancien_solde_from_position`

```python
def _detect_ancien_solde_from_position( self, lines: List[str]
```

**Description**: Détecte le montant et le type d'ANCIEN SOLDE via la position de colonne.

- **Ligne**: 361
- **Réutilisabilité**: Medium
- **Type de retour**: `Tuple[Optional[Decimal], BalanceType]`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `decimal.Decimal`
  - `models.BalanceType`
  - `models.TransactionDirection`
  - *... et 4 autres*

---

## Cache

**22 fonctions**

### `backend/cache.py`

#### 🔸 `get_redis_client` 🎀

```python
def get_redis_client() -> Optional[redis.Redis]:
```

**Description**: Obtient ou crée un client Redis avec pool de connexions.

- **Ligne**: 25
- **Réutilisabilité**: Low
- **Type de retour**: `Optional[redis.Redis]`
- **Dépendances**:
  - `os`
  - `redis`
  - `typing.Optional`

#### 🔸 `cache_key`

```python
def cache_key(*args, tenant_id: Optional[int] = None, prefix: str = "cache") -> str:
```

**Description**: Génère une clé de cache cohérente à partir des arguments.

- **Ligne**: 48
- **Réutilisabilité**: Medium
- **Type de retour**: `str`
- **Dépendances**:
  - `hashlib`
  - `json`
  - `typing.Optional`

#### 🔸 `cached` 🎀

```python
def cached( ttl: int = 300, # 5 minutes default
```

**Description**: Décorateur pour mettre en cache les résultats d'une fonction dans Redis.

- **Ligne**: 58
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `ttl`: `int` = `300`
  - `prefix`: `str` = `'api'`
  - `tenant_aware`: `bool` = `True`
- **Dépendances**:
  - `functools`
  - `json`
  - `redis`
  - `typing.Callable`

#### 🔸 `decorator` 🎀

```python
def decorator(func: Callable) -> Callable:
```

- **Ligne**: 76
- **Réutilisabilité**: Medium
- **Type de retour**: `Callable`
- **Paramètres**:
  - `func`: `Callable`
- **Dépendances**:
  - `functools`
  - `json`
  - `redis`
  - `typing.Callable`

#### 🔸 `async async_wrapper` 🎀

```python
async def async_wrapper(*args, **kwargs):
```

- **Ligne**: 78
- **Réutilisabilité**: Medium
- **Décorateurs**: `functools.wraps(func)`
- **Dépendances**:
  - `functools`
  - `json`
  - `redis`

#### 🔸 `sync_wrapper` 🎀

```python
def sync_wrapper(*args, **kwargs):
```

- **Ligne**: 116
- **Réutilisabilité**: Medium
- **Décorateurs**: `functools.wraps(func)`
- **Dépendances**:
  - `functools`
  - `json`
  - `redis`

#### 🔸 `asyncio_available`

```python
def asyncio_available(func: Callable) -> bool:
```

**Description**: Vérifie si la fonction est asynchrone.

- **Ligne**: 155
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `func`: `Callable`
- **Dépendances**:
  - `functools`
  - `typing.Callable`

#### 🔹 `__init__`

```python
def __init__(self, prefix: str = "app"):
```

- **Ligne**: 173
- **Réutilisabilité**: High
- **Paramètres**:
  - `self`
  - `prefix`: `str` = `'app'`

#### 🔹 `client`

```python
def client(self) -> Optional[redis.Redis]:
```

- **Ligne**: 178
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[redis.Redis]`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `redis`
  - `typing.Optional`

#### 🔹 `_key`

```python
def _key(self, key: str) -> str:
```

- **Ligne**: 183
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `self`
  - `key`: `str`

#### 🔹 `get`

```python
def get(self, key: str) -> Optional[Any]:
```

**Description**: Récupère une valeur depuis le cache.

- **Ligne**: 186
- **Réutilisabilité**: High
- **Type de retour**: `Optional[Any]`
- **Paramètres**:
  - `self`
  - `key`: `str`
- **Dépendances**:
  - `json`
  - `redis`
  - `typing.Any`
  - `typing.Optional`

#### 🔹 `set`

```python
def set(self, key: str, value: Any, ttl: int = 300) -> bool:
```

**Description**: Enregistre une valeur dans le cache avec TTL.

- **Ligne**: 196
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `key`: `str`
  - `value`: `Any`
  - `ttl`: `int` = `300`
- **Dépendances**:
  - `json`
  - `redis`
  - `typing.Any`

#### 🔹 `delete`

```python
def delete(self, key: str) -> bool:
```

**Description**: Supprime une clé du cache.

- **Ligne**: 209
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `key`: `str`
- **Dépendances**:
  - `redis`

#### 🔹 `invalidate_pattern` 🎀

```python
def invalidate_pattern(self, pattern: str) -> int:
```

**Description**: Invalide toutes les clés correspondant au motif.

- **Ligne**: 218
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `pattern`: `str`
- **Dépendances**:
  - `redis`

#### 🔹 `invalidate_tenant`

```python
def invalidate_tenant(self, tenant_id: int) -> int:
```

**Description**: Invalide tout le cache pour un tenant donné.

- **Ligne**: 248
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `tenant_id`: `int`

#### 🔸 `invalidate_on_mutation` 🎀

```python
def invalidate_on_mutation(cache_prefixes: list[str], tenant_id: Optional[int] = None):
```

**Description**: Décorateur pour invalider le cache après une mutation.

- **Ligne**: 271
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `cache_prefixes`: `list[str]`
  - `tenant_id`: `Optional[int]` = `None`
- **Dépendances**:
  - `functools`
  - `typing.Callable`
  - `typing.Optional`

#### 🔸 `decorator` 🎀

```python
def decorator(func: Callable) -> Callable:
```

- **Ligne**: 280
- **Réutilisabilité**: High
- **Type de retour**: `Callable`
- **Paramètres**:
  - `func`: `Callable`
- **Dépendances**:
  - `functools`
  - `typing.Callable`

#### 🔸 `async async_wrapper` 🎀

```python
async def async_wrapper(*args, **kwargs):
```

- **Ligne**: 282
- **Réutilisabilité**: Medium
- **Décorateurs**: `functools.wraps(func)`
- **Dépendances**:
  - `functools`

#### 🔸 `sync_wrapper` 🎀

```python
def sync_wrapper(*args, **kwargs):
```

- **Ligne**: 297
- **Réutilisabilité**: Medium
- **Décorateurs**: `functools.wraps(func)`
- **Dépendances**:
  - `functools`

### `backend/main.py`

#### 🔸 `async startup_event`

```python
async def startup_event():
```

**Description**: Initialise le pool de connexions Redis au démarrage.

- **Ligne**: 300
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.on_event('startup')`
- **Dépendances**:
  - `backend.cache.get_redis_client`
  - `backend.middleware.ResponseWrapperMiddleware`
  - `logging`

#### 🔸 `cache_metrics`

```python
def cache_metrics():
```

**Description**: Retourne les statistiques du cache Redis.

- **Ligne**: 389
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.get('/metrics/cache', dependencies=_security_dependencies())`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.api.admin`
  - `backend.api.analytics`
  - `backend.api.anomaly_detection`
  - `backend.api.audit`
  - *... et 56 autres*

### `core/inventory_forecast.py`

#### 🔸 `forecast_daily_consumption` 🎀

```python
def forecast_daily_consumption(*, tenant_id: int = 1, horizon: int = 30) -> dict[int, float]:
```

**Description**: Calcule les prévisions de consommation quotidienne pour chaque produit.

- **Ligne**: 71
- **Réutilisabilité**: Low
- **Type de retour**: `dict[int, float]`
- **Dépendances**:
  - `core.data_repository.query_df`
  - `datetime.datetime`
  - `datetime.timedelta`

---

## Background Tasks

**18 fonctions**

### `backend/tasks/maintenance.py`

#### 🔸 `cleanup_cache`

```python
def cleanup_cache():
```

**Description**: Clean up expired cache entries.

- **Ligne**: 7
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task(queue='maintenance')`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `refresh_views`

```python
def refresh_views():
```

**Description**: Refresh materialized views.

- **Ligne**: 23
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task(queue='maintenance')`
- **Dépendances**:
  - `backend.cache.get_redis_client`
  - `backend.worker.app`
  - `os`

#### 🔸 `aggregate_stats`

```python
def aggregate_stats():
```

**Description**: Aggregate daily statistics.

- **Ligne**: 55
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task(queue='maintenance')`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `check_stock_alerts`

```python
def check_stock_alerts():
```

**Description**: Check for low stock alerts.

- **Ligne**: 61
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task(queue='maintenance')`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `vacuum_database`

```python
def vacuum_database():
```

**Description**: Run VACUUM ANALYZE on key tables.

- **Ligne**: 67
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task(queue='maintenance')`
- **Dépendances**:
  - `backend.cache.get_redis_client`
  - `backend.worker.app`
  - `contextlib.closing`
  - `os`
  - `psycopg2`

### `backend/tasks/reports.py`

#### 🔸 `generate_report`

```python
def generate_report(self, report_type: str, params: dict, tenant_id: int):
```

**Description**: Génère un rapport de manière asynchrone.

- **Ligne**: 6
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(bind=True, max_retries=2, queue='reports')`
- **Paramètres**:
  - `self`
  - `report_type`: `str`
  - `params`: `dict`
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `generate_daily_summary`

```python
def generate_daily_summary(tenant_id: int):
```

**Description**: Génère un rapport quotidien de synthèse.

- **Ligne**: 20
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(queue='reports')`
- **Paramètres**:
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.worker.app`

#### 🔸 `generate_monthly_report`

```python
def generate_monthly_report(tenant_id: int, month: int, year: int):
```

**Description**: Génère un rapport financier mensuel.

- **Ligne**: 26
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(queue='reports')`
- **Paramètres**:
  - `tenant_id`: `int`
  - `month`: `int`
  - `year`: `int`
- **Dépendances**:
  - `backend.worker.app`

### `backend/worker.py`

#### 🔸 `process_invoice_async`

```python
def process_invoice_async(self, invoice_id: int, tenant_id: int):
```

**Description**: Traite une facture en tâche de fond (OCR, parsing, validation).

- **Ligne**: 108
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(bind=True, max_retries=3)`
- **Paramètres**:
  - `self`
  - `invoice_id`: `int`
  - `tenant_id`: `int`

#### 🔸 `generate_report_async`

```python
def generate_report_async(self, report_type: str, params: dict, tenant_id: int):
```

**Description**: Génère un rapport en tâche de fond.

- **Ligne**: 129
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(bind=True, max_retries=2)`
- **Paramètres**:
  - `self`
  - `report_type`: `str`
  - `params`: `dict`
  - `tenant_id`: `int`
- **Dépendances**:
  - `backend.services.invoices.InvoiceService`

#### 🔸 `cleanup_cache`

```python
def cleanup_cache():
```

**Description**: Nettoie les entrées de cache expirées et les données anciennes.

- **Ligne**: 151
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task`

#### 🔸 `refresh_materialized_views`

```python
def refresh_materialized_views():
```

**Description**: Rafraîchit les vues matérialisées PostgreSQL pour accélérer les requêtes.

- **Ligne**: 168
- **Réutilisabilité**: Low
- **Décorateurs**: `app.task`
- **Dépendances**:
  - `backend.cache.get_redis_client`
  - `backend.services.invoices.InvoiceService`
  - `backend.services.reports.ReportService`
  - `celery.Celery`
  - `celery.schedules.crontab`
  - *... et 2 autres*

#### 🔸 `aggregate_daily_stats`

```python
def aggregate_daily_stats():
```

**Description**: Agrège les statistiques pour les performances du tableau de bord.

- **Ligne**: 202
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task`

#### 🔸 `check_stock_alerts`

```python
def check_stock_alerts():
```

**Description**: Vérifie les stocks bas et génère des alertes.

- **Ligne**: 209
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task`

#### 🔸 `sync_pending_invoices`

```python
def sync_pending_invoices():
```

**Description**: Synchronise les factures en attente qui ont échoué au traitement.

- **Ligne**: 215
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.task`

#### 🔸 `send_notification_async`

```python
def send_notification_async(self, notification_type: str, recipient: str, data: dict):
```

**Description**: Envoie une notification en tâche de fond (email, SMS, push).

- **Ligne**: 221
- **Réutilisabilité**: High
- **Décorateurs**: `app.task(bind=True)`
- **Paramètres**:
  - `self`
  - `notification_type`: `str`
  - `recipient`: `str`
  - `data`: `dict`

#### 🔸 `get_task_status`

```python
def get_task_status(task_id: str) -> dict:
```

**Description**: Récupère le statut d'une tâche en arrière-plan.

- **Ligne**: 238
- **Réutilisabilité**: High
- **Type de retour**: `dict`
- **Paramètres**:
  - `task_id`: `str`

#### 🔸 `cancel_task`

```python
def cancel_task(task_id: str) -> bool:
```

**Description**: Annule une tâche en attente ou en cours.

- **Ligne**: 248
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `task_id`: `str`

---

## Data Creation

**16 fonctions**

### `backend/dependencies/security.py`

#### 🔸 `create_access_token`

```python
def create_access_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
```

**Description**: Sérialise les claims fournis dans un JWT signé avec des claims adaptés à la rotation.

- **Ligne**: 98
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `claims`: `dict[str, Any]`
  - `expires_delta`: `timedelta | None` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - `jwt`
  - `typing.Any`
  - *... et 1 autres*

#### 🔸 `create_refresh_token`

```python
def create_refresh_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
```

**Description**: Crée un refresh token avec une durée d'expiration plus longue.

- **Ligne**: 109
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `claims`: `dict[str, Any]`
  - `expires_delta`: `timedelta | None` = `None`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - `jwt`
  - `typing.Any`
  - *... et 1 autres*

### `backend/main.py`

#### 🔸 `create_app` 🎀

```python
def create_app() -> FastAPI:
```

**Description**: Construit l'application FastAPI ainsi que tous les routeurs de domaine.

- **Ligne**: 216
- **Réutilisabilité**: Low
- **Type de retour**: `FastAPI`
- **Décorateurs**: `lru_cache`
- **Dépendances**:
  - `__future__.annotations`
  - `backend.api.admin`
  - `backend.api.analytics`
  - `backend.api.anomaly_detection`
  - `backend.api.audit`
  - *... et 58 autres*

### `core/backup_manager.py`

#### 🔸 `save_backup_settings`

```python
def save_backup_settings( settings: Dict[str, object],
```

**Description**: Persiste les paramètres d'automatisation des sauvegardes sur disque.

- **Ligne**: 110
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `settings`: `Dict[str, object]`
  - `directory`: `str | os.PathLike[str] | None` = `None`
- **Dépendances**:
  - `json`
  - `os`
  - `pathlib.Path`
  - `sqlalchemy.engine.url.make_url`
  - `typing.Dict`

#### 🔸 `create_backup`

```python
def create_backup( *, label: Optional[str] = None,
```

**Description**: Crée une nouvelle sauvegarde via ``pg_dump`` et retourne ses métadonnées.

- **Ligne**: 437
- **Réutilisabilité**: Low
- **Type de retour**: `BackupMetadata`
- **Dépendances**:
  - `datetime.datetime`
  - `datetime.timedelta`
  - `datetime.timezone`
  - `gzip`
  - `os`
  - *... et 3 autres*

#### 🔸 `restore_backup`

```python
def restore_backup( filename: str,
```

**Description**: Restaure la base de données à partir du fichier de sauvegarde fourni.

- **Ligne**: 505
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `gzip`
  - `os`
  - `pathlib.Path`
  - `subprocess`
  - `typing.Optional`

### `core/bank_import/categorizer.py`

#### 🔹 `_add_pattern`

```python
def _add_pattern(self, keyword: str) -> None:
```

**Description**: Add a regex pattern for a keyword.

- **Ligne**: 188
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `keyword`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `core.data_repository.query_df`
  - `models.TransactionDirection`
  - `re`

#### 🔹 `add_custom_rule`

```python
def add_custom_rule(self, libelle_pattern: str, category_code: str) -> None:
```

**Description**: Add a custom categorization rule.

- **Ligne**: 389
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `libelle_pattern`: `str`
  - `category_code`: `str`
- **Dépendances**:
  - `categories.CATEGORIES`

### `core/bank_import/models.py`

#### 🔹 `add_error`

```python
def add_error(self, msg: str) -> None:
```

**Description**: Add an error message.

- **Ligne**: 228
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `msg`: `str`

#### 🔹 `add_warning`

```python
def add_warning(self, msg: str) -> None:
```

**Description**: Add a warning message.

- **Ligne**: 232
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `msg`: `str`

### `core/bank_import/orchestrator.py`

#### 🔹 `_insert_transactions` 🎀

```python
def _insert_transactions( self, transactions: List[ParsedTransaction],
```

**Description**: Insert transactions into database.

- **Ligne**: 336
- **Réutilisabilité**: Medium
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `transactions`: `List[ParsedTransaction]`
  - `account_id`: `int`
  - `period_start`
  - `period_end`
  - `source_file`: `str`
- **Dépendances**:
  - `models.ParsedTransaction`
  - `models.TransactionDirection`
  - `sqlalchemy.text`
  - `typing.List`

### `core/import_analyzer.py`

#### 🔹 `save_report`

```python
def save_report(self, report: ImportAnalysisReport, output_path: str | Path) -> None:
```

**Description**: Sauvegarde un rapport en JSON.

- **Ligne**: 361
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `report`: `ImportAnalysisReport`
  - `output_path`: `str | Path`
- **Dépendances**:
  - `pathlib.Path`

#### 🔹 `save_summary_csv`

```python
def save_summary_csv(self, output_path: str | Path) -> None:
```

**Description**: Sauvegarde un résumé en CSV.

- **Ligne**: 366
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `self`
  - `output_path`: `str | Path`
- **Dépendances**:
  - `__future__.annotations`
  - `pathlib.Path`

### `core/inventory_costing.py`

#### 🔸 `add_cost_layer`

```python
def add_cost_layer( conn, *, tenant_id: int,
```

- **Ligne**: 70
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Paramètres**:
  - `conn`
- **Dépendances**:
  - `datetime.datetime`
  - `decimal.Decimal`
  - `sqlalchemy.text`

### `core/products_loader.py`

#### 🔸 `insert_or_update_barcode`

```python
def insert_or_update_barcode( conn: Connection,
```

**Description**: Insère un code-barres et renvoie *added*, *skipped* ou *conflict*.

- **Ligne**: 150
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `conn`: `Connection`
  - `produit_id`: `int`
  - `barcode`: `str`
  - `tenant_id`: `float | int | None` = `None`
- **Dépendances**:
  - `sqlalchemy.engine.Connection`
  - `sqlalchemy.text`

#### 🔸 `create_initial_stock`

```python
def create_initial_stock( conn: Connection,
```

**Description**: Insère un mouvement de stock positif et renvoie ``True`` s'il est créé.

- **Ligne**: 400
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `conn`: `Connection`
  - `produit_id`: `int`
  - `quantite`: `float`
- **Dépendances**:
  - `datetime.datetime`
  - `sqlalchemy.engine.Connection`
  - `sqlalchemy.exc`
  - `sqlalchemy.text`

---

## Formatting

**15 fonctions**

### `core/bank_import/USAGE_EXAMPLES.py`

#### 🔹 `_parse_ca_transaction`

```python
def _parse_ca_transaction(self, line, line_num, period):
```

**Description**: Parse une ligne de transaction CA.

- **Ligne**: 154
- **Réutilisabilité**: Medium
- **Paramètres**:
  - `self`
  - `line`
  - `line_num`
  - `period`

### `core/bank_import/extractor.py`

#### 🔹 `_parse_french_period_match`

```python
def _parse_french_period_match(self, match: re.Match) -> Optional[StatementPeriod]:
```

**Description**: Parse French text date match (BNP format).

- **Ligne**: 249
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[StatementPeriod]`
- **Paramètres**:
  - `self`
  - `match`: `re.Match`
- **Dépendances**:
  - `__future__.annotations`
  - `datetime.date`
  - `models.StatementPeriod`
  - `re`
  - `typing.Optional`

#### 🔹 `_parse_period_match`

```python
def _parse_period_match(self, match: re.Match) -> Optional[StatementPeriod]:
```

**Description**: Parse regex match into StatementPeriod.

- **Ligne**: 273
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[StatementPeriod]`
- **Paramètres**:
  - `self`
  - `match`: `re.Match`
- **Dépendances**:
  - `__future__.annotations`
  - `dataclasses.dataclass`
  - `datetime.date`
  - `models.BankType`
  - `models.StatementPeriod`
  - *... et 5 autres*

### `core/bank_import/parser.py`

#### 🔹 `_parse_transactions` 🎀

```python
def _parse_transactions( self, lines: List[str],
```

**Description**: Parse transaction lines.

- **Ligne**: 551
- **Réutilisabilité**: Low
- **Type de retour**: `List[ParsedTransaction]`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
  - `columns`: `ColumnPositions`
  - `bank_type`: `BankType` = `BankType.LCL`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `models.BankType`
  - `models.ColumnPositions`
  - `models.ParsedTransaction`
  - *... et 5 autres*

#### 🔹 `_parse_transaction_line`

```python
def _parse_transaction_line( self, line: str,
```

**Description**: Parse a single transaction line.

- **Ligne**: 658
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[ParsedTransaction]`
- **Paramètres**:
  - `self`
  - `line`: `str`
  - `line_num`: `int`
  - `period`: `StatementPeriod`
  - `columns`: `ColumnPositions`
  - `bank_type`: `BankType` = `BankType.LCL`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 15 autres*

#### 🔹 `_parse_bnp_transaction_line`

```python
def _parse_bnp_transaction_line( self, line: str,
```

**Description**: Parse a BNP transaction line using semantic direction detection.

- **Ligne**: 755
- **Réutilisabilité**: Low
- **Type de retour**: `Optional[ParsedTransaction]`
- **Paramètres**:
  - `self`
  - `line`: `str`
  - `line_num`: `int`
  - `period`: `StatementPeriod`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 16 autres*

#### 🔹 `_parse_date`

```python
def _parse_date(self, date_str: str, period: StatementPeriod) -> Optional[date]:
```

**Description**: Parse a date string.

- **Ligne**: 872
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[date]`
- **Paramètres**:
  - `self`
  - `date_str`: `str`
  - `period`: `StatementPeriod`
- **Dépendances**:
  - `abc.abstractmethod`
  - `datetime.date`
  - `datetime.datetime`
  - `models.StatementPeriod`
  - `typing.Optional`

#### 🔹 `_parse_amount`

```python
def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
```

**Description**: Parse an amount string.

- **Ligne**: 911
- **Réutilisabilité**: Medium
- **Type de retour**: `Optional[Decimal]`
- **Paramètres**:
  - `self`
  - `amount_str`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `decimal.Decimal`
  - `decimal.InvalidOperation`
  - `models.TransactionDirection`
  - *... et 2 autres*

#### 🔸 `parse_lcl_statement`

```python
def parse_lcl_statement( lines: List[str],
```

**Description**: Fonction utilitaire pour parser un relevé LCL.

- **Ligne**: 972
- **Réutilisabilité**: High
- **Type de retour**: `ParsedStatement`
- **Paramètres**:
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
- **Dépendances**:
  - `abc.abstractmethod`
  - `models.BankType`
  - `models.ParsedStatement`
  - `models.StatementPeriod`
  - `typing.List`

#### 🔸 `parse_sumup_statement`

```python
def parse_sumup_statement(text: str) -> ParsedStatement:
```

**Description**: Analyse le texte PDF d'un relevé de compte SumUp (format tabulaire).

- **Ligne**: 989
- **Réutilisabilité**: Medium
- **Type de retour**: `ParsedStatement`
- **Paramètres**:
  - `text`: `str`
- **Dépendances**:
  - `__future__.annotations`
  - `abc.abstractmethod`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - *... et 17 autres*

#### 🔸 `parse_statement`

```python
def parse_statement( lines: List[str],
```

**Description**: Fonction utilitaire pour parser un relevé.

- **Ligne**: 1176
- **Réutilisabilité**: High
- **Type de retour**: `ParsedStatement`
- **Paramètres**:
  - `lines`: `List[str]`
  - `period`: `StatementPeriod`
  - `bank_type`: `BankType`
- **Dépendances**:
  - `abc.abstractmethod`
  - `models.BankType`
  - `models.ParsedStatement`
  - `models.StatementPeriod`
  - `typing.List`

### `core/parsers/__init__.py`

#### 🔸 `parse_metro`

```python
def parse_metro(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

- **Ligne**: 96
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `text`: `str`
  - `margin_rate`: `float`
  - `start_sequence`: `int`
- **Dépendances**:
  - `core.invoice_extractor`

#### 🔸 `parse_eurociel`

```python
def parse_eurociel(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

- **Ligne**: 105
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `text`: `str`
  - `margin_rate`: `float`
  - `start_sequence`: `int`
- **Dépendances**:
  - `core.invoice_extractor`

#### 🔸 `parse_taiyat`

```python
def parse_taiyat(text: str, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

- **Ligne**: 114
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `text`: `str`
  - `margin_rate`: `float`
  - `start_sequence`: `int`
- **Dépendances**:
  - `core.invoice_extractor`

#### 🔸 `parse_invoice`

```python
def parse_invoice(text: str, supplier_hint: str | None, margin_rate: float, start_sequence: int) -> pd.DataFrame:
```

- **Ligne**: 130
- **Réutilisabilité**: High
- **Type de retour**: `pd.DataFrame`
- **Paramètres**:
  - `text`: `str`
  - `supplier_hint`: `str | None`
  - `margin_rate`: `float`
  - `start_sequence`: `int`
- **Dépendances**:
  - `core.invoice_extractor`

---

## Validation

**8 fonctions**

### `backend/main.py`

#### 🔸 `invalidate_cache`

```python
def invalidate_cache(pattern: str, tenant: Tenant = Depends(get_current_tenant)):
```

**Description**: Invalide les entrées de cache correspondant au pattern.

- **Ligne**: 407
- **Réutilisabilité**: Medium
- **Décorateurs**: `app.post('/cache/invalidate/{pattern}', dependencies=_security_dependencies())`
- **Paramètres**:
  - `pattern`: `str`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.cache.CacheManager`
  - `backend.cache.CacheTTL`
  - `backend.cache.get_redis_client`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - *... et 6 autres*

### `core/backup_manager.py`

#### 🔸 `check_backup_integrity`

```python
def check_backup_integrity( metadata: BackupMetadata,
```

**Description**: Effectue des vérifications légères d'intégrité sur un fichier de sauvegarde.

- **Ligne**: 385
- **Réutilisabilité**: High
- **Type de retour**: `Tuple[bool, str]`
- **Paramètres**:
  - `metadata`: `BackupMetadata`
- **Dépendances**:
  - `gzip`
  - `pathlib.Path`
  - `typing.Tuple`

#### 🔸 `check_backup_tools`

```python
def check_backup_tools( *, pg_dump_path: Optional[str] = None,
```

**Description**: Retourne un diagnostic de disponibilité de pg_dump et psql.

- **Ligne**: 556
- **Réutilisabilité**: Medium
- **Type de retour**: `Tuple[BinaryStatus, BinaryStatus]`
- **Dépendances**:
  - `typing.Optional`
  - `typing.Tuple`

### `core/bank_import/deduplicator.py`

#### 🔹 `check_duplicate`

```python
def check_duplicate(self, txn: ParsedTransaction) -> bool:
```

**Description**: Check if a transaction is a duplicate.

- **Ligne**: 115
- **Réutilisabilité**: High
- **Type de retour**: `bool`
- **Paramètres**:
  - `self`
  - `txn`: `ParsedTransaction`
- **Dépendances**:
  - `models.ParsedTransaction`

### `core/bank_import/orchestrator.py`

#### 🔹 `_ensure_account`

```python
def _ensure_account(self, entity_code: str, account_label: str) -> int:
```

**Description**: Ensure account exists and return its ID.

- **Ligne**: 296
- **Réutilisabilité**: High
- **Type de retour**: `int`
- **Paramètres**:
  - `self`
  - `entity_code`: `str`
  - `account_label`: `str`
- **Dépendances**:
  - `sqlalchemy.text`

### `core/bank_import/validator.py`

#### 🔹 `validate_transaction` 🎀

```python
def validate_transaction(self, txn: ParsedTransaction) -> List[str]:
```

**Description**: Validate a single transaction.

- **Ligne**: 151
- **Réutilisabilité**: High
- **Type de retour**: `List[str]`
- **Paramètres**:
  - `self`
  - `txn`: `ParsedTransaction`
- **Dépendances**:
  - `models.ParsedTransaction`
  - `typing.List`

#### 🔸 `validate_statement`

```python
def validate_statement(statement: ParsedStatement) -> ValidationResult:
```

**Description**: Convenience function for validation.

- **Ligne**: 190
- **Réutilisabilité**: High
- **Type de retour**: `ValidationResult`
- **Paramètres**:
  - `statement`: `ParsedStatement`
- **Dépendances**:
  - `models.ParsedStatement`

### `core/products_loader.py`

#### 🔸 `ensure_barcode_constraints`

```python
def ensure_barcode_constraints() -> None:
```

**Description**: Crée un index d'unicité sur (tenant_id, lower(code)) pour sécuriser les codes-barres.

- **Ligne**: 373
- **Réutilisabilité**: Medium
- **Type de retour**: `None`
- **Dépendances**:
  - `data_repository.get_engine`
  - `sqlalchemy.engine.Connection`
  - `sqlalchemy.exc`

---

## Authentication

**7 fonctions**

### `backend/dependencies/auth.py`

#### 🔸 `require_api_key` 🎀

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
```

**Description**: Valide l'en-tête `X-API-KEY` si une clé est configurée.

- **Ligne**: 13
- **Réutilisabilité**: High
- **Type de retour**: `str | None`
- **Paramètres**:
  - `x_api_key`: `str | None` = `Header(default=None)`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.Header`
  - `fastapi.status`

#### 🔸 `optional_api_key`

```python
def optional_api_key(api_key: str | None = Depends(require_api_key)) -> None:
```

**Description**: Déclenche la vérification mais ne retourne rien.

- **Ligne**: 33
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `api_key`: `str | None` = `Depends(require_api_key)`
- **Dépendances**:
  - `fastapi.Depends`

### `backend/dependencies/security.py`

#### 🔸 `set_auth_cookies`

```python
def set_auth_cookies( response: Response,
```

**Description**: Définit les cookies httpOnly pour les tokens d'accès et de rafraîchissement.

- **Ligne**: 125
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `response`: `Response`
  - `access_token`: `str`
  - `refresh_token`: `str`
  - `access_max_age`: `int | None` = `None`
  - `refresh_max_age`: `int | None` = `None`
- **Dépendances**:
  - `fastapi.Response`

#### 🔸 `clear_auth_cookies`

```python
def clear_auth_cookies(response: Response) -> None:
```

**Description**: Supprime les cookies d'authentification (logout).

- **Ligne**: 157
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `response`: `Response`
- **Dépendances**:
  - `fastapi.Response`

#### 🔸 `decode_refresh_token` 🎀

```python
def decode_refresh_token(token: str) -> dict[str, Any]:
```

**Description**: Décode et valide un refresh token.

- **Ligne**: 284
- **Réutilisabilité**: High
- **Type de retour**: `dict[str, Any]`
- **Paramètres**:
  - `token`: `str`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `fastapi.status`
  - `typing.Any`

#### 🔸 `revoke_token`

```python
def revoke_token(token: str) -> None:
```

**Description**: Ajoute le jti d'un token à la liste de révocation jusqu'à expiration.

- **Ligne**: 336
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `token`: `str`
- **Dépendances**:
  - `fastapi.HTTPException`
  - `jwt`

### `backend/tests/conftest.py`

#### 🔸 `authenticated_client`

```python
def authenticated_client(client, mock_tenant, mock_user):
```

**Description**: Client avec authentification simulée.

- **Ligne**: 47
- **Réutilisabilité**: Medium
- **Décorateurs**: `pytest.fixture`
- **Paramètres**:
  - `client`
  - `mock_tenant`
  - `mock_user`
- **Dépendances**:
  - `backend.main.app`
  - `fastapi.testclient.TestClient`
  - `pytest`

---

## Data Schema

**6 fonctions**

### `backend/schemas/catalog.py`

#### 🔹 `nom_not_empty`

```python
def nom_not_empty(cls, v: str) -> str:
```

- **Ligne**: 23
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Décorateurs**: `field_validator('nom')`, `classmethod`
- **Paramètres**:
  - `cls`
  - `v`: `str`
- **Dépendances**:
  - `pydantic.field_validator`

### `backend/schemas/supplier_scoring.py`

#### 🔹 `validate_grade` 🎀

```python
def validate_grade(cls, v: str) -> str:
```

**Description**: Valide que le grade est A, B, C, D ou F.

- **Ligne**: 88
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Décorateurs**: `field_validator('grade')`, `classmethod`
- **Paramètres**:
  - `cls`
  - `v`: `str`
- **Dépendances**:
  - `pydantic.field_validator`

#### 🔹 `validate_total_weight` 🎀

```python
def validate_total_weight(cls, v: float) -> float:
```

**Description**: Valide que le poids total est proche de 1.0.

- **Ligne**: 137
- **Réutilisabilité**: High
- **Type de retour**: `float`
- **Décorateurs**: `field_validator('total_weight')`, `classmethod`
- **Paramètres**:
  - `cls`
  - `v`: `float`
- **Dépendances**:
  - `pydantic.field_validator`

#### 🔹 `validate_weights` 🎀

```python
def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
```

**Description**: Valide que tous les poids sont entre 0 et 1 et que leur somme fait ~1.0.

- **Ligne**: 153
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, float]`
- **Décorateurs**: `field_validator('weights')`, `classmethod`
- **Paramètres**:
  - `cls`
  - `v`: `Dict[str, float]`
- **Dépendances**:
  - `pydantic.field_validator`
  - `typing.Dict`

#### 🔹 `validate_issue_type` 🎀

```python
def validate_issue_type(cls, v: str) -> str:
```

**Description**: Valide le type de problème.

- **Ligne**: 299
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Décorateurs**: `field_validator('issue_type')`, `classmethod`
- **Paramètres**:
  - `cls`
  - `v`: `str`
- **Dépendances**:
  - `pydantic.field_validator`

#### 🔹 `validate_severity` 🎀

```python
def validate_severity(cls, v: str) -> str:
```

**Description**: Valide la sévérité.

- **Ligne**: 308
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Décorateurs**: `field_validator('severity')`, `classmethod`
- **Paramètres**:
  - `cls`
  - `v`: `str`
- **Dépendances**:
  - `pydantic.field_validator`

---

## Calculation

**5 fonctions**

### `core/backup_manager.py`

#### 🔸 `compute_backup_statistics`

```python
def compute_backup_statistics(backups: Iterable[BackupMetadata]) -> Dict[str, float]:
```

**Description**: Calcule des statistiques agrégées (min/max/moyenne/taille totale).

- **Ligne**: 294
- **Réutilisabilité**: High
- **Type de retour**: `Dict[str, float]`
- **Paramètres**:
  - `backups`: `Iterable[BackupMetadata]`
- **Dépendances**:
  - `statistics.mean`
  - `typing.Dict`
  - `typing.Iterable`

### `core/bank_import/models.py`

#### 🔹 `total_in`

```python
def total_in(self) -> Decimal:
```

**Description**: Total incoming amount.

- **Ligne**: 181
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `__future__.annotations`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 5 autres*

#### 🔹 `total_out`

```python
def total_out(self) -> Decimal:
```

**Description**: Total outgoing amount.

- **Ligne**: 189
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `__future__.annotations`
  - `dataclasses.dataclass`
  - `dataclasses.field`
  - `datetime.date`
  - `datetime.datetime`
  - *... et 5 autres*

### `core/bank_import/validator.py`

#### 🔹 `total_difference`

```python
def total_difference(self) -> Decimal:
```

**Description**: Total absolute difference.

- **Ligne**: 30
- **Réutilisabilité**: Medium
- **Type de retour**: `Decimal`
- **Décorateurs**: `property`
- **Paramètres**:
  - `self`
- **Dépendances**:
  - `decimal.Decimal`

### `core/import_analyzer.py`

#### 🔹 `_calculate_quality_score`

```python
def _calculate_quality_score(self, report: ImportAnalysisReport) -> float:
```

**Description**: Calcule un score de qualité global (0-100).

- **Ligne**: 318
- **Réutilisabilité**: High
- **Type de retour**: `float`
- **Paramètres**:
  - `self`
  - `report`: `ImportAnalysisReport`
- **Dépendances**:
  - `dataclasses.field`

---

## Utilities

**5 fonctions**

### `core/pdf_utils.py`

#### 🔸 `split_pdf_into_invoices` 🎀

```python
def split_pdf_into_invoices(pdf_bytes: bytes) -> list[dict[str, object]]:
```

**Description**: Découpe un PDF en sous-documents par facture (détectée via Date facture).

- **Ligne**: 16
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, object]]`
- **Paramètres**:
  - `pdf_bytes`: `bytes`
- **Dépendances**:
  - `PyPDF2.PdfReader`
  - `PyPDF2.PdfWriter`
  - `invoice_extractor.DATE_FACTURE_PATTERN`
  - `invoice_extractor.FINAL_INVOICE_PATTERN`
  - `io.BytesIO`
  - *... et 2 autres*

#### 🔸 `sanitize_receipt_text`

```python
def sanitize_receipt_text(value: object) -> str:
```

**Description**: Convertit un contenu en chaîne ASCII sans caractères spéciaux.

- **Ligne**: 83
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `value`: `object`
- **Dépendances**:
  - `unicodedata`

#### 🔸 `format_currency_line`

```python
def format_currency_line(label: str, amount: Decimal) -> str:
```

- **Ligne**: 100
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `label`: `str`
  - `amount`: `Decimal`
- **Dépendances**:
  - `decimal.Decimal`
  - `decimal.ROUND_HALF_UP`

#### 🔸 `format_quantity`

```python
def format_quantity(qty: Decimal) -> str:
```

- **Ligne**: 105
- **Réutilisabilité**: High
- **Type de retour**: `str`
- **Paramètres**:
  - `qty`: `Decimal`
- **Dépendances**:
  - `decimal.Decimal`

#### 🔸 `render_receipt_pdf` 🎀

```python
def render_receipt_pdf(lines: list[str]) -> bytes:
```

**Description**: Encode les lignes du ticket dans un PDF minimaliste.

- **Ligne**: 113
- **Réutilisabilité**: High
- **Type de retour**: `bytes`
- **Paramètres**:
  - `lines`: `list[str]`

---

## Data Normalization

**3 fonctions**

### `backend/main.py`

#### 🔹 `_clean_barcodes` 🎀

```python
def _clean_barcodes(cls, value: Iterable[str] | None) -> list[str] | None:
```

- **Ligne**: 118
- **Réutilisabilité**: Medium
- **Type de retour**: `list[str] | None`
- **Décorateurs**: `field_validator('barcodes', mode='before')`
- **Paramètres**:
  - `cls`
  - `value`: `Iterable[str] | None`
- **Dépendances**:
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - `backend.middleware.RequestContextMiddleware`
  - `core.products_loader.ensure_barcode_constraints`
  - `core.user_service.bootstrap_users_if_enabled`
  - `pydantic.field_validator`
  - *... et 1 autres*

### `core/bank_import/extractor.py`

#### 🔹 `clean_lines` 🎀

```python
def clean_lines( self, lines: List[str],
```

**Description**: Remove header/footer lines and noise.

- **Ligne**: 340
- **Réutilisabilité**: High
- **Type de retour**: `List[str]`
- **Paramètres**:
  - `self`
  - `lines`: `List[str]`
  - `bank_type`: `BankType` = `BankType.UNKNOWN`
- **Dépendances**:
  - `models.BankType`
  - `typing.List`

### `core/cart_normalizer.py`

#### 🔸 `normalize_cart_rows` 🎀

```python
def normalize_cart_rows(cart: Iterable[Mapping[str, Any] | None]) -> list[dict[str, Any]]:
```

**Description**: Return a normalised list of cart rows ready for persistence.

- **Ligne**: 84
- **Réutilisabilité**: Medium
- **Type de retour**: `list[dict[str, Any]]`
- **Paramètres**:
  - `cart`: `Iterable[Mapping[str, Any] | None]`
- **Dépendances**:
  - `typing.Any`
  - `typing.Iterable`
  - `typing.Mapping`

---

## Data Update

**1 fonctions**

### `backend/main.py`

#### 🔸 `update_product`

```python
def update_product( product_id: int,
```

- **Ligne**: 462
- **Réutilisabilité**: Medium
- **Type de retour**: `dict[str, object]`
- **Décorateurs**: `app.patch('/products/{product_id}', dependencies=_security_dependencies())`
- **Paramètres**:
  - `product_id`: `int`
  - `payload`: `ProductUpdateRequest`
  - `tenant`: `Tenant` = `Depends(get_current_tenant)`
- **Dépendances**:
  - `backend.api.inventory_intelligence`
  - `backend.api.maintenance`
  - `backend.dependencies.auth.optional_api_key`
  - `backend.dependencies.tenant.Tenant`
  - `backend.dependencies.tenant.bootstrap_tenants_if_enabled`
  - *... et 10 autres*

---

## Data Deletion

**1 fonctions**

### `core/backup_manager.py`

#### 🔸 `delete_backup`

```python
def delete_backup( filename: str,
```

**Description**: Supprime un fichier de sauvegarde existant.

- **Ligne**: 494
- **Réutilisabilité**: High
- **Type de retour**: `None`
- **Paramètres**:
  - `filename`: `str`
- **Dépendances**:
  - `os`
  - `pathlib.Path`

---
