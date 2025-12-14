# CMS Infrastructure - Quick Start

## Installation en 3 étapes

### 1. Migration BDD
```bash
cd /home/ruuuzer/Documents/monprojet
alembic upgrade head
```

Crée les tables `cms_pages` et `cms_nav_items`.

### 2. Seed données
```bash
python scripts/seed_cms_navigation.py
```

Initialise 6 pages et 15 items de navigation par défaut.

### 3. Tests
```bash
pytest tests/test_newcms_api.py -v
```

Lance la suite complète de 30+ tests.

## Fichiers créés

```
migrations/versions/
  └── 20251211_cms_tables.py          # Migration Alembic

scripts/
  └── seed_cms_navigation.py          # Script de seed

tests/
  └── test_newcms_api.py              # Tests complets

backend/main.py                       # Router déjà enregistré (ligne 357)
```

## Tests inclus

- ✅ Pages CRUD (list, create, update, delete)
- ✅ Navigation CRUD
- ✅ Isolation par tenant (epicerie, restaurant, intelligence)
- ✅ Erreurs 400/401/404/422
- ✅ ResponseWrapper format
- ✅ Pagination validation
- ✅ Edge cases (JSONB large, caractères spéciaux)

## Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/newcms/pages` | Liste pages |
| POST | `/newcms/pages` | Crée page |
| PUT | `/newcms/pages/{id}` | Met à jour page |
| DELETE | `/newcms/pages/{id}` | Supprime page |
| GET | `/newcms/nav` | Liste navigation |
| POST | `/newcms/nav` | Crée item nav |

## Vérification rapide

```bash
# Lancer le serveur
uvicorn backend.main:app --reload

# Tester
curl http://localhost:8000/newcms/pages
curl http://localhost:8000/newcms/nav
```

## Documentation complète

Voir `/home/ruuuzer/Documents/monprojet/docs/CMS_INFRASTRUCTURE_GUIDE.md`

## Conventions

- **Slugs:** kebab-case (ex: `cockpit`, `operations-overview`)
- **Status:** `draft` | `published`
- **Sections:** `main`, `operations`, `finance`, `restaurant`, `intelligence`
- **Icons:** Lucide icons (ex: `Gauge`, `Package`, `Brain`)
- **Tenant isolation:** Toutes les requêtes filtrées par `tenant_id`

## Todo Next

- [ ] Créer endpoints vues (`/newcms/cockpit`, `/newcms/operations/overview`, etc.)
- [ ] Implémenter pagination
- [ ] Ajouter recherche full-text
- [ ] Versioning pages
- [ ] Permissions granulaires
