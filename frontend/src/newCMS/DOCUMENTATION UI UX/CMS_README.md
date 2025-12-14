# newCMS - Système de gestion de contenu

## Vue d'ensemble

Système CMS flexible pour gérer les pages et la navigation de l'application avec:
- Contenu JSONB structuré
- Navigation hiérarchique
- Multi-tenant natif
- API REST complète

## Installation rapide

```bash
# 1. Migration BDD
alembic upgrade head

# 2. Données par défaut
python scripts/seed_cms_navigation.py

# 3. Vérification
python scripts/verify_cms_setup.py

# 4. Tests
pytest tests/test_newcms_api.py -v
```

## Fichiers

```
migrations/versions/20251211_cms_tables.py    # Migration tables
scripts/seed_cms_navigation.py               # Seed navigation
scripts/verify_cms_setup.py                  # Vérification setup
tests/test_newcms_api.py                     # Tests (30+)
backend/api/newcms.py                        # API endpoints
docs/CMS_INFRASTRUCTURE_GUIDE.md             # Guide complet
CMS_QUICKSTART.md                            # Quick start
DELIVERABLES_CMS.md                          # Livrables détaillés
```

## API Endpoints

```bash
# Pages
GET    /newcms/pages           # Liste pages
POST   /newcms/pages           # Crée page
PUT    /newcms/pages/{id}      # Met à jour
DELETE /newcms/pages/{id}      # Supprime

# Navigation
GET    /newcms/nav             # Liste navigation
POST   /newcms/nav             # Crée item
```

## Exemple d'utilisation

### Créer une page

```bash
curl -X POST http://localhost:8000/newcms/pages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "slug": "dashboard",
    "title": "Tableau de bord",
    "description": "Vue d'\''ensemble des KPIs",
    "content": {
      "sections": [
        {
          "type": "kpi_grid",
          "widgets": [
            {"metric": "revenue", "label": "CA", "icon": "TrendingUp"}
          ]
        }
      ]
    },
    "status": "published"
  }'
```

### Lister la navigation

```bash
curl http://localhost:8000/newcms/nav \
  -H "Authorization: Bearer $TOKEN"
```

## Structure JSONB

Le champ `content` supporte plusieurs types de sections:

```json
{
  "sections": [
    {"type": "kpi_grid", "widgets": [...]},
    {"type": "chart", "chartType": "line", "dataSource": "..."},
    {"type": "data_table", "dataSource": "..."},
    {"type": "quick_actions", "actions": [...]},
    {"type": "ai_insights", "features": [...]},
    {"type": "settings_grid", "categories": [...]},
    {"type": "recent_transactions", "limit": 10},
    {"type": "margin_analysis", "dataSource": "..."}
  ]
}
```

## Pages par défaut (seed)

1. **Cockpit** - Vue consolidée KPIs et alertes
2. **Opérations** - Catalogue, stock, factures
3. **Finance** - Trésorerie, rapprochement
4. **Restaurant** - Plats, ingrédients, marges
5. **Intelligence** - Prévisions, anomalies, scoring
6. **Config** - Administration système

## Navigation par défaut

- Cockpit (Gauge)
- Opérations (Package)
  - Catalogue (BookOpen)
  - Stock (Archive)
  - Factures (FileText)
- Finance (Wallet)
  - Trésorerie (Coins)
  - Rapprochement (GitCompare)
- Restaurant (Utensils)
  - Plats (ChefHat)
  - Ingrédients (Carrot)
- Intelligence (Brain) + badge AI
  - Prévisions (TrendingUp)
  - Anomalies (AlertTriangle)
- Config (Settings)

## Tests

Suite complète de 30+ tests:

```bash
# Tous les tests
pytest tests/test_newcms_api.py -v

# Test spécifique
pytest tests/test_newcms_api.py::test_list_pages_success -v

# Avec couverture
pytest tests/test_newcms_api.py --cov=backend.api.newcms --cov-report=html
```

**Couverture:**
- CRUD pages et navigation
- Isolation multi-tenant
- Erreurs HTTP (400, 401, 404, 422)
- ResponseWrapper format
- Edge cases (JSONB large, caractères spéciaux)

## Conventions

**Slugs:**
- Format: `kebab-case`
- Unique par tenant
- Exemples: `cockpit`, `operations-overview`, `finance-treasury`

**Status:**
- `draft` - Brouillon
- `published` - Publié

**Sections navigation:**
- `main` - Menu principal
- `operations` - Sous-menu Opérations
- `finance` - Sous-menu Finance
- `restaurant` - Sous-menu Restaurant
- `intelligence` - Sous-menu Intelligence

**Icons (Lucide):**
- Gauge, Package, Wallet, Utensils, Brain, Settings
- BookOpen, Archive, FileText, Coins, GitCompare
- ChefHat, Carrot, TrendingUp, AlertTriangle

## Troubleshooting

**Migration échoue:**
```bash
alembic current                    # État actuel
alembic history                    # Historique
alembic downgrade -1               # Revenir en arrière
```

**Seed échoue:**
```bash
psql -d inventaire -c "SELECT * FROM tenants;"
psql -d inventaire -c "\d cms_pages"
```

**Tests échouent:**
```bash
export RUN_BACKEND_API_TESTS=1
export SKIP_TENANT_INIT=1
export SKIP_USER_BOOTSTRAP=1
pytest tests/test_newcms_api.py -vv --tb=short
```

## Documentation complète

- **Guide complet:** `docs/CMS_INFRASTRUCTURE_GUIDE.md`
- **Quick start:** `CMS_QUICKSTART.md`
- **Livrables:** `DELIVERABLES_CMS.md`
- **API docs:** http://localhost:8000/docs#tag/newcms

## Développement

```bash
# Lancer le serveur
uvicorn backend.main:app --reload

# Watcher tests
pytest-watch tests/test_newcms_api.py

# Format code
black backend/api/newcms.py tests/test_newcms_api.py

# Linter
ruff check backend/api/newcms.py
```

## Roadmap

- [ ] Endpoints vues spécifiques (`/newcms/cockpit`, etc.)
- [ ] Pagination
- [ ] Recherche full-text
- [ ] Versioning pages
- [ ] Permissions granulaires
- [ ] Cache navigation
- [ ] Éditeur frontend drag-and-drop
- [ ] Preview temps réel
- [ ] Export/import pages

## Support

**Contact:** Expert Infrastructure/Tests
**Date:** 2025-12-11
**Status:** ✅ Production Ready
