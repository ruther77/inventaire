# Guide d'intégration - NewCMS Restaurant & Mobile API

## Situation actuelle

Le projet a déjà un module `backend/api/newcms.py` avec:
- Finance router
- Cockpit router
- Operations router
- Intelligence router

**Notre mission:** Ajouter le router Restaurant & Mobile sans conflit.

## Option 1: Ajouter au newcms existant (RECOMMANDÉ)

### Étape 1: Créer le sous-module

Créer `/home/ruuuzer/Documents/monprojet/backend/api/newcms/restaurant.py`:

```python
"""NewCMS Restaurant & Mobile endpoints."""

from fastapi import APIRouter

# Importer notre router depuis newCMS
import sys
sys.path.insert(0, '/home/ruuuzer/Documents/monprojet')
from newCMS.backend.api.restaurant import router as restaurant_api_router

# Créer un wrapper avec prefix newcms
router = APIRouter(prefix="/restaurant", tags=["newcms-restaurant"])

# Inclure notre router
router.include_router(restaurant_api_router)
```

### Étape 2: Modifier backend/api/newcms.py

Dans `/home/ruuuzer/Documents/monprojet/backend/api/newcms.py`, ajouter:

```python
from backend.api.newcms.restaurant import router as restaurant_router

# ...

# Ligne 26, après intelligence_router
router.include_router(restaurant_router)
```

**Résultat:**
- Routes montées sous `/api/restaurant/*`
- Exemple: `GET /api/restaurant/overview`
- Exemple: `POST /api/restaurant/mobile/scan`

---

## Option 2: Router séparé (ALTERNATIVE)

Si vous préférez garder le router restaurant complètement séparé:

### Modifier backend/main.py

Ligne 58, remplacer:
```python
from backend.api import newcms as newcms_router
```

Par:
```python
from backend.api import newcms as newcms_router
from newCMS.backend.api import restaurant_router as newcms_restaurant_router
```

Ligne 356, après le router newcms existant:
```python
app.include_router(newcms_router.router, tags=['newcms'])
app.include_router(newcms_restaurant_router, tags=['newcms-restaurant'])  # NOUVEAU
```

**Résultat:**
- Routes montées sous `/newcms/*`
- Exemple: `GET /newcms/restaurant/overview`
- Exemple: `POST /newcms/mobile/scan`

---

## Option 3: Symlink (RAPIDE)

Créer un symlink du code newCMS dans backend/api/newcms:

```bash
# Copier les fichiers
cp -r newCMS/backend/api/restaurant.py backend/api/newcms/restaurant.py
cp -r newCMS/backend/schemas/restaurant.py backend/schemas/restaurant_mobile.py

# Modifier les imports dans restaurant.py
# Remplacer:
#   from newCMS.backend.schemas.restaurant import ...
# Par:
#   from backend.schemas.restaurant_mobile import ...
```

Puis dans `backend/api/newcms.py`:

```python
from backend.api.newcms.restaurant import router as restaurant_router

# ...

router.include_router(restaurant_router)
```

---

## Comparaison des options

| Critère | Option 1 | Option 2 | Option 3 |
|---------|----------|----------|----------|
| Intégration | ✅ Seamless | ⚠️ Séparé | ✅ Natif |
| URL | `/api/restaurant/*` | `/newcms/*` | `/api/restaurant/*` |
| Maintenance | ⚠️ Dual source | ✅ Simple | ❌ Duplication |
| Cohérence | ✅ Unifié | ⚠️ Split | ✅ Unifié |
| Rapidité | ⚠️ Moyen | ✅ Rapide | ❌ Lent |

**Recommandation:** Option 1 pour cohérence avec l'existant.

---

## Instructions détaillées - Option 1

### 1. Créer le fichier backend/api/newcms/restaurant.py

```bash
# Vérifier que le dossier existe
ls -la /home/ruuuzer/Documents/monprojet/backend/api/newcms/

# Copier notre router
cp /home/ruuuzer/Documents/monprojet/newCMS/backend/api/restaurant.py \
   /home/ruuuzer/Documents/monprojet/backend/api/newcms/restaurant_mobile.py
```

### 2. Adapter les imports

Éditer `/home/ruuuzer/Documents/monprojet/backend/api/newcms/restaurant_mobile.py`:

**Remplacer:**
```python
from newCMS.backend.schemas.restaurant import (
    RestaurantOverviewResponse,
    # ...
)
```

**Par:**
```python
# Copier d'abord les schemas
# cp newCMS/backend/schemas/restaurant.py backend/schemas/restaurant_mobile.py

from backend.schemas.restaurant_mobile import (
    RestaurantOverviewResponse,
    # ...
)
```

### 3. Modifier backend/api/newcms.py

**Ajouter l'import:**
```python
from backend.api.newcms.restaurant_mobile import router as restaurant_router
```

**Inclure le router:**
```python
router.include_router(restaurant_router)
```

### 4. Copier les schemas

```bash
cp /home/ruuuzer/Documents/monprojet/newCMS/backend/schemas/restaurant.py \
   /home/ruuuzer/Documents/monprojet/backend/schemas/restaurant_mobile.py
```

### 5. Vérifier

```bash
# Redémarrer le serveur
uvicorn backend.main:app --reload

# Tester
curl http://localhost:8000/docs
# → Chercher tag "newcms-restaurant"
# → Endpoints sous /api/restaurant/*
```

---

## URLs finales (Option 1)

Après intégration, les endpoints seront:

```
GET  /api/restaurant/overview          # Restaurant dashboard
GET  /api/restaurant/mobile/inventory  # Mobile inventory list
POST /api/restaurant/mobile/scan       # Barcode scan
POST /api/restaurant/mobile/adjust     # Stock adjustment
```

**Note:** Le prefix `/api` vient de `backend/api/newcms.py` ligne 20.

---

## URLs finales (Option 2)

Si vous choisissez Option 2:

```
GET  /newcms/restaurant/overview          # Restaurant dashboard
GET  /newcms/mobile/inventory             # Mobile inventory list
POST /newcms/mobile/scan                  # Barcode scan
POST /newcms/mobile/adjust                # Stock adjustment
```

---

## Migration BDD (toutes options)

Quelle que soit l'option choisie:

```bash
psql -U postgres -d inventaire -f /home/ruuuzer/Documents/monprojet/newCMS/migration_mobile_support.sql
```

---

## Tests (toutes options)

### Tests unitaires
```bash
cd /home/ruuuzer/Documents/monprojet
python newCMS/test_endpoints.py
```

### Tests API (Option 1 - URLs /api/restaurant/*)

Modifier `postman_collection.json`:

**Remplacer:**
```json
"path": ["newcms", "restaurant", "overview"]
```

**Par:**
```json
"path": ["api", "restaurant", "overview"]
```

### Tests API (Option 2 - URLs /newcms/*)

Pas de changement, utiliser `postman_collection.json` tel quel.

---

## Checklist d'intégration

### Option 1
- [ ] Copier `newCMS/backend/api/restaurant.py` → `backend/api/newcms/restaurant_mobile.py`
- [ ] Copier `newCMS/backend/schemas/restaurant.py` → `backend/schemas/restaurant_mobile.py`
- [ ] Adapter les imports dans `restaurant_mobile.py`
- [ ] Ajouter import dans `backend/api/newcms.py`
- [ ] Inclure router dans `backend/api/newcms.py`
- [ ] Exécuter migration SQL
- [ ] Redémarrer serveur
- [ ] Tester dans Swagger (`/docs`)
- [ ] Mettre à jour Postman collection (URLs)

### Option 2
- [ ] Ajouter import dans `backend/main.py`
- [ ] Inclure router dans `backend/main.py`
- [ ] Exécuter migration SQL
- [ ] Redémarrer serveur
- [ ] Tester dans Swagger (`/docs`)
- [ ] Utiliser Postman collection tel quel

---

## Troubleshooting

### Erreur "ModuleNotFoundError: No module named 'newCMS'"

**Solution Option 1:**
- Copier les fichiers au lieu d'importer depuis newCMS
- Utiliser paths backend/* au lieu de newCMS/*

**Solution Option 2:**
- Ajouter newCMS au PYTHONPATH:
  ```bash
  export PYTHONPATH=/home/ruuuzer/Documents/monprojet:$PYTHONPATH
  ```

### Endpoints ne s'affichent pas dans /docs

**Vérifier:**
1. Router bien importé
2. Router bien inclus (`app.include_router`)
3. Redémarrage serveur effectué
4. Aucune erreur dans logs

### URL prefix incorrect

**Option 1:**
- Vérifier `backend/api/newcms.py` ligne 20: `prefix="/api"`
- URLs finales: `/api/restaurant/*`

**Option 2:**
- Vérifier `newCMS/backend/api/restaurant.py` ligne 27: `prefix="/newcms"`
- URLs finales: `/newcms/restaurant/*`

---

## Recommandation finale

**Pour une intégration propre et cohérente:**

1. Utiliser **Option 1** (intégration dans newcms existant)
2. URLs sous `/api/restaurant/*`
3. Cohérent avec Finance, Cockpit, Operations, Intelligence
4. Facile à maintenir et documenter

**Commandes rapides:**

```bash
# Copier les fichiers
cp newCMS/backend/api/restaurant.py backend/api/newcms/restaurant_mobile.py
cp newCMS/backend/schemas/restaurant.py backend/schemas/restaurant_mobile.py

# Éditer restaurant_mobile.py (adapter imports)
# Éditer backend/api/newcms.py (ajouter import + include)

# Migration
psql -U postgres -d inventaire -f newCMS/migration_mobile_support.sql

# Redémarrer
uvicorn backend.main:app --reload

# Tester
curl http://localhost:8000/api/restaurant/overview
```

---

**Version:** 1.0.0
**Date:** 2025-12-11
**Status:** Ready to integrate
