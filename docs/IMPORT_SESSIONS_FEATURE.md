# Fonctionnalité "Historique Import par Session"

## Vue d'ensemble

Cette fonctionnalité permet de grouper les imports de factures par **session utilisateur**, facilitant ainsi le suivi et l'analyse des imports effectués durant une même session de travail.

## Architecture

### Backend (FastAPI)

#### 1. Base de données

**Migration SQL**: `/db/migrations/add_import_sessions.sql`

- **Table `zero_click_jobs`**: Ajout du champ `session_id` (TEXT, nullable)
  - Index sur `session_id` pour optimiser les requêtes

- **Table `processed_invoices`**: Ajout du champ `session_id` (TEXT, nullable)
  - Index sur `session_id`

#### 2. Services

**Fichier**: `/backend/services/zero_click_jobs.py`

Nouvelles fonctions:
- `create_job()`: Accepte maintenant `session_id` en paramètre
- `list_jobs()`: Filtre par `session_id` optionnel
- `list_import_sessions()`: Liste les sessions avec statistiques agrégées
- `get_session_details()`: Récupère tous les imports d'une session

#### 3. Schémas Pydantic

**Fichier**: `/backend/schemas/invoices.py`

Nouveaux modèles:
```python
class ImportSession(BaseModel):
    session_id: str
    date_debut: datetime
    date_fin: Optional[datetime]
    nb_imports: int
    nb_completed: int
    nb_failed: int
    total_lignes: int
    total_mouvements: int
    total_produits_crees: int
    fournisseurs: Optional[str]

class ImportSessionDetails(BaseModel):
    # Étend ImportSession avec la liste des imports
    imports: List[ZeroClickJobStatus]
```

#### 4. Endpoints API

**Fichier**: `/backend/api/invoices.py`

Nouveaux endpoints:
- `GET /invoices/sessions`: Liste les sessions d'import
  - Query params: `limit`, `offset`
  - Retourne: `ImportSessionListResponse`

- `GET /invoices/sessions/{session_id}`: Détails d'une session
  - Retourne: `ImportSessionDetails` avec tous les imports

Endpoints modifiés:
- `POST /invoices/zero-click/jobs`: Accepte `session_id` (Form)
- `GET /invoices/zero-click/jobs`: Filtre par `session_id` (Query)

### Frontend (React)

#### 1. Gestion du session_id

**Fichier**: `/frontend/src/utils/sessionManager.js`

Fonctions:
- `getSessionId()`: Récupère ou génère un session_id (UUID v4)
- `clearSessionId()`: Efface la session courante
- `getCurrentSessionId()`: Lit la session sans en créer
- `startNewSession()`: Démarre explicitement une nouvelle session
- `hasActiveSession()`: Vérifie si une session existe

**Stockage**: sessionStorage (disparaît à la fermeture de l'onglet)

#### 2. Client API

**Fichier**: `/frontend/src/api/client.js`

Nouvelles fonctions:
```javascript
// Ajout session_id aux imports
zeroClickInvoiceJob({ ..., sessionId })

// Nouvelles routes
fetchImportSessions({ limit, offset })
fetchImportSessionDetails(sessionId)
```

#### 3. Hooks React

**Fichier**: `/frontend/src/hooks/useInvoiceImport.js`

Nouveaux hooks:
- `useImportSessions(filters)`: Query pour lister les sessions
- `useImportSessionDetails(sessionId)`: Query pour détails d'une session

Hooks modifiés:
- `useZeroClickJob()`: Ajoute automatiquement le session_id via `getSessionId()`

#### 4. Composant UI

**Fichier**: `/frontend/src/features/invoices/components/ImportSessionsView.jsx`

Fonctionnalités:
- Liste des sessions groupées par jour
- Expansion pour voir les détails de chaque session
- Statistiques agrégées:
  - Nombre d'imports
  - Total lignes / mouvements / produits créés
  - Durée de la session
  - Fournisseurs concernés
- Filtres: "Cette session" / "Aujourd'hui" / "Cette semaine" / "Tout"
- Rafraîchissement automatique (60s)

#### 5. Intégration

**Fichier**: `/frontend/src/features/invoices/ImportPage.jsx`

Nouvelle section dans l'historique:
- Onglet "Historique par session" (`history.sessions`)
- Rendu via `renderSessionsPanel()`

## Utilisation

### Côté utilisateur

1. **Import automatique**: Chaque import de facture est automatiquement associé à la session browser courante
2. **Session persistante**: Le session_id persiste dans sessionStorage jusqu'à la fermeture de l'onglet
3. **Visualisation**: Dans "Historique > Historique par session", voir tous les imports groupés

### Workflow

```
1. Utilisateur ouvre l'application
   └─> sessionManager.getSessionId() génère un UUID unique

2. Utilisateur importe plusieurs factures
   └─> Chaque import utilise le même session_id

3. Utilisateur consulte "Historique par session"
   └─> Voit toutes les factures importées dans cette session

4. Utilisateur ferme l'onglet
   └─> session_id est effacé (sessionStorage)

5. Utilisateur rouvre l'application
   └─> Nouvelle session_id générée
```

## Exemples de requêtes

### Lister les sessions
```bash
GET /invoices/sessions?limit=50&offset=0
```

Response:
```json
{
  "items": [
    {
      "session_id": "a1b2c3d4-...",
      "date_debut": "2025-12-15T10:30:00Z",
      "date_fin": "2025-12-15T11:15:00Z",
      "nb_imports": 5,
      "nb_completed": 4,
      "nb_failed": 1,
      "total_lignes": 150,
      "total_mouvements": 145,
      "total_produits_crees": 3,
      "fournisseurs": "METRO, EUROCIEL"
    }
  ],
  "total": 1
}
```

### Détails d'une session
```bash
GET /invoices/sessions/a1b2c3d4-...
```

Response:
```json
{
  "session_id": "a1b2c3d4-...",
  "date_debut": "2025-12-15T10:30:00Z",
  "date_fin": "2025-12-15T11:15:00Z",
  "nb_imports": 5,
  "nb_completed": 4,
  "nb_failed": 1,
  "nb_pending": 0,
  "total_lignes": 150,
  "total_mouvements": 145,
  "total_produits_crees": 3,
  "fournisseurs": ["METRO", "EUROCIEL"],
  "imports": [
    {
      "job_id": "...",
      "status": "completed",
      "filename": "facture_metro_001.pdf",
      "supplier_hint": "METRO",
      "summary": {
        "rows_received": 35,
        "movements_created": 35,
        "products_created": 1
      },
      "created_at": "2025-12-15T10:30:15Z"
    }
  ]
}
```

## Migration

### Appliquer la migration

```bash
# Se connecter à la base de données
psql -U postgres -d inventaire

# Exécuter la migration
\i /home/ruuuzer/Documents/monprojet/db/migrations/add_import_sessions.sql
```

### Vérification

```sql
-- Vérifier que les colonnes existent
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('zero_click_jobs', 'processed_invoices')
  AND column_name = 'session_id';

-- Vérifier les index
SELECT indexname, tablename
FROM pg_indexes
WHERE indexname LIKE '%session%';
```

## Tests

### Test backend

```python
# Test création job avec session_id
job = create_job(
    job_id="test-123",
    tenant_id=1,
    session_id="session-abc",
)

# Test liste sessions
sessions, total = list_import_sessions(tenant_id=1, limit=10)
assert len(sessions) > 0
assert sessions[0]["session_id"] == "session-abc"

# Test détails session
details = get_session_details("session-abc", tenant_id=1)
assert details["nb_imports"] > 0
```

### Test frontend

```javascript
// Test génération session_id
const sessionId = getSessionId();
console.log('Session ID:', sessionId);

// Test persistance
const sameId = getSessionId();
assert(sessionId === sameId);

// Test nouveau démarrage
clearSessionId();
const newId = getSessionId();
assert(newId !== sessionId);
```

## Performance

- **Index sur session_id**: Requêtes optimisées sur les sessions
- **Agrégation SQL**: Calcul des stats côté base de données
- **Cache React Query**: 30s-60s pour éviter les requêtes répétées
- **Limite de résultats**: Pagination par défaut (50 items)

## Améliorations futures

1. **Filtres avancés**:
   - Par date (aujourd'hui, cette semaine, ce mois)
   - Par fournisseur
   - Par statut (succès, échecs)

2. **Statistiques enrichies**:
   - Temps moyen par import
   - Taux de succès par session
   - Comparaison avec sessions précédentes

3. **Actions groupées**:
   - Re-traiter une session entière
   - Exporter tous les imports d'une session

4. **Notifications**:
   - Alerte si session dure trop longtemps
   - Résumé à la fin de session

## Support

Pour toute question sur cette fonctionnalité:
- Backend: `/backend/services/zero_click_jobs.py`
- Frontend: `/frontend/src/features/invoices/components/ImportSessionsView.jsx`
- API: Documentation Swagger à `/docs`
