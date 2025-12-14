# Guide Infrastructure CMS

## Vue d'ensemble

Ce guide décrit l'infrastructure complète du nouveau système CMS (newCMS) avec:
- Tables de base de données (migration Alembic)
- Données de seed (navigation par défaut)
- Tests complets (pytest)

## Fichiers créés

### 1. Migration Alembic

**Fichier:** `migrations/versions/20251211_cms_tables.py`

Crée deux tables:

#### Table `cms_pages`
```sql
- id (SERIAL PRIMARY KEY)
- tenant_id (INT NOT NULL)
- slug (TEXT NOT NULL) -- Identifiant unique de la page
- title (TEXT NOT NULL)
- description (TEXT)
- content (JSONB) -- Contenu structuré de la page
- status (TEXT) -- 'draft' ou 'published'
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
- UNIQUE(tenant_id, slug)
```

#### Table `cms_nav_items`
```sql
- id (SERIAL PRIMARY KEY)
- tenant_id (INT NOT NULL)
- label (TEXT NOT NULL)
- path (TEXT NOT NULL)
- section (TEXT) -- Groupement des items (main, operations, etc.)
- order_index (INT) -- Ordre d'affichage
- icon (TEXT) -- Nom de l'icône (Lucide icons)
- badge (TEXT NULLABLE) -- Badge optionnel (ex: "AI", "NEW")
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

**Commandes:**
```bash
# Appliquer la migration
cd /home/ruuuzer/Documents/monprojet
alembic upgrade head

# Annuler la migration (si nécessaire)
alembic downgrade -1
```

### 2. Script de seed

**Fichier:** `scripts/seed_cms_navigation.py`

Initialise les pages et la navigation par défaut pour tous les tenants.

**Pages créées:**
1. **Cockpit** (`/newcms/cockpit`)
   - Vue consolidée avec KPIs et alertes
   - Widgets: CA du jour, valorisation stock, alertes actives

2. **Opérations** (`/newcms/operations`)
   - Gestion quotidienne: catalogue, stock, factures
   - Actions rapides: ajouter produit, scanner facture

3. **Finance** (`/newcms/finance`)
   - Trésorerie et comptabilité
   - KPIs: solde, rapprochement, CA mensuel

4. **Restaurant** (`/newcms/restaurant`)
   - Plats, ingrédients, marges
   - Analyse des coûts et marges

5. **Intelligence** (`/newcms/intelligence`)
   - Prévisions, anomalies, scoring fournisseurs
   - Insights IA et graphiques

6. **Config** (`/newcms/config`)
   - Administration système
   - Gestion utilisateurs, tenants, paramètres

**Navigation créée:** 15 items de navigation organisés par sections

**Commandes:**
```bash
# Exécuter le seed
cd /home/ruuuzer/Documents/monprojet
python scripts/seed_cms_navigation.py

# Le script est idempotent (ON CONFLICT DO UPDATE)
# Vous pouvez le relancer sans risque de doublons
```

### 3. Tests pytest

**Fichier:** `tests/test_newcms_api.py`

Suite complète de tests couvrant:

#### Tests Pages CMS
- `test_list_pages_success` - Liste des pages
- `test_list_pages_different_tenant` - Isolation par tenant
- `test_create_page_success` - Création de page
- `test_update_page_success` - Mise à jour
- `test_update_page_no_changes` - Validation erreurs 400
- `test_update_page_not_found` - Erreur 404
- `test_delete_page_success` - Suppression

#### Tests Navigation
- `test_list_nav_success` - Liste navigation
- `test_list_nav_ordered_correctly` - Ordre correct (order_index)
- `test_create_nav_item_success` - Création item

#### Tests Erreurs & Edge Cases
- `test_unauthenticated_request` - Sans auth (401)
- `test_page_not_found_404` - Ressource inexistante
- `test_invalid_page_slug` - Validation Pydantic (422)
- `test_response_wrapper_format` - Format ResponseWrapper
- `test_response_wrapper_error_format` - Format erreurs

#### Tests Isolation par Tenant
- `test_pages_isolation_by_tenant` - Pages isolées
- `test_nav_isolation_by_tenant` - Navigation isolée

#### Tests Intégration Vues
- `test_cockpit_overview_placeholder`
- `test_operations_overview_placeholder`
- `test_finance_overview_placeholder`
- `test_restaurant_overview_placeholder`
- `test_intelligence_overview_placeholder`

#### Tests Performance
- `test_large_content_jsonb` - Contenu volumineux
- `test_special_characters_in_slug` - Caractères spéciaux
- `test_pagination_validation` - Validation pagination

**Commandes:**
```bash
# Exécuter tous les tests CMS
cd /home/ruuuzer/Documents/monprojet
pytest tests/test_newcms_api.py -v

# Exécuter un test spécifique
pytest tests/test_newcms_api.py::test_list_pages_success -v

# Avec couverture
pytest tests/test_newcms_api.py --cov=backend.api.newcms --cov-report=html

# Tests en continu (watch mode)
pytest-watch tests/test_newcms_api.py
```

## Fixtures de test

Les tests utilisent 3 fixtures tenant:
- `epicerie_tenant` (tenant_id=1)
- `restaurant_tenant` (tenant_id=2)
- `intelligence_tenant` (tenant_id=3)

**Mocks fournis:**
- `mock_tenant_resolution` - Résolution automatique du tenant
- `mock_cms_data` - Données CMS sans accès DB
- `auth_headers` - Headers JWT pour authentification

## Workflow complet

```bash
# 1. Appliquer la migration
alembic upgrade head

# 2. Seed les données par défaut
python scripts/seed_cms_navigation.py

# 3. Lancer les tests
pytest tests/test_newcms_api.py -v

# 4. Vérifier l'API (optionnel)
# Démarrer le serveur
uvicorn backend.main:app --reload

# Tester manuellement
curl http://localhost:8000/newcms/pages
curl http://localhost:8000/newcms/nav
```

## Endpoints API disponibles

### Pages
- `GET /newcms/pages` - Liste toutes les pages
- `POST /newcms/pages` - Crée une nouvelle page
- `PUT /newcms/pages/{page_id}` - Met à jour une page
- `DELETE /newcms/pages/{page_id}` - Supprime une page

### Navigation
- `GET /newcms/nav` - Liste tous les items de navigation
- `POST /newcms/nav` - Crée un nouvel item

## Structure du contenu JSONB

Les pages utilisent un format JSONB flexible:

```json
{
  "sections": [
    {
      "type": "kpi_grid",
      "title": "Métriques Clés",
      "widgets": [
        {
          "metric": "revenue",
          "label": "CA du jour",
          "icon": "TrendingUp"
        }
      ]
    },
    {
      "type": "chart",
      "title": "Tendances",
      "chartType": "line",
      "dataSource": "daily_revenue"
    }
  ]
}
```

**Types de sections supportés:**
- `kpi_grid` - Grille de métriques clés
- `chart` - Graphique (line, bar, combo)
- `data_table` - Tableau de données
- `quick_actions` - Actions rapides
- `ai_insights` - Insights IA
- `settings_grid` - Grille de paramètres
- `recent_transactions` - Transactions récentes
- `margin_analysis` - Analyse des marges

## Conventions

### Slugs
- Format: `kebab-case`
- Unique par tenant
- Exemples: `cockpit`, `operations`, `finance-overview`

### Status
- `draft` - Brouillon, non publié
- `published` - Publié, visible

### Sections
- `main` - Navigation principale
- `operations` - Sous-menu Opérations
- `finance` - Sous-menu Finance
- `restaurant` - Sous-menu Restaurant
- `intelligence` - Sous-menu Intelligence

### Icons (Lucide)
Icônes recommandées:
- `Gauge` - Cockpit
- `Package` - Opérations
- `Wallet` - Finance
- `Utensils` - Restaurant
- `Brain` - Intelligence
- `Settings` - Configuration

## Troubleshooting

### Migration échoue
```bash
# Vérifier l'état des migrations
alembic current

# Voir l'historique
alembic history

# Revenir à une version spécifique
alembic downgrade <revision>
```

### Seed échoue
```bash
# Vérifier les tenants
psql -d inventaire -c "SELECT * FROM tenants;"

# Vérifier les tables CMS
psql -d inventaire -c "\d cms_pages"
psql -d inventaire -c "\d cms_nav_items"
```

### Tests échouent
```bash
# Vérifier l'environnement
export RUN_BACKEND_API_TESTS=1
export SKIP_TENANT_INIT=1
export SKIP_USER_BOOTSTRAP=1

# Installer les dépendances de test
pip install pytest pytest-cov fastapi testclient

# Lancer avec verbose
pytest tests/test_newcms_api.py -vv --tb=short
```

## Next Steps

1. **Créer les endpoints de vues** (`/newcms/cockpit`, `/newcms/operations/overview`, etc.)
2. **Implémenter la pagination** sur `/newcms/pages`
3. **Ajouter la recherche** (par titre, description, contenu)
4. **Versioning** des pages (historique des modifications)
5. **Permissions** granulaires par page/section

## Référence rapide

| Fichier | Description | Commande |
|---------|-------------|----------|
| `migrations/versions/20251211_cms_tables.py` | Migration BDD | `alembic upgrade head` |
| `scripts/seed_cms_navigation.py` | Seed données | `python scripts/seed_cms_navigation.py` |
| `tests/test_newcms_api.py` | Tests | `pytest tests/test_newcms_api.py -v` |
| `backend/api/newcms.py` | Router API | Déjà enregistré dans `main.py` |

## Support

Pour toute question:
1. Consulter les tests pour exemples d'utilisation
2. Vérifier les logs: `tail -f logs/app.log`
3. Documentation API: http://localhost:8000/docs#tag/newcms
