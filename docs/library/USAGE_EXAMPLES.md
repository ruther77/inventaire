# Guide d'Utilisation du Catalogue de Fonctions

Ce guide montre comment exploiter le catalogue de fonctions pour différents cas d'usage.

## Structure du Catalogue JSON

Le fichier `python_functions_catalog.json` est structuré comme suit :

```json
{
  "metadata": {
    "total_functions": 1149,
    "total_files": 179,
    "categories": [...],
    "base_path": "..."
  },
  "statistics": {
    "by_category": {...},
    "async_functions": 83,
    "class_methods": 407,
    "decorators": 207,
    "high_reusability": 504
  },
  "functions_by_category": {
    "API": [...],
    "Finance": [...],
    ...
  }
}
```

## Cas d'Usage

### 1. Rechercher toutes les fonctions dans un fichier spécifique

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

file_path = "backend/services/finance/dashboard.py"

# Parcourir toutes les catégories
for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        if func['file_path'] == file_path:
            print(f"{func['name']} (ligne {func['line_number']})")
```

### 2. Trouver toutes les fonctions asynchrones

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

async_functions = []
for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        if func['is_async']:
            async_functions.append({
                'name': func['name'],
                'file': func['file_path'],
                'category': category
            })

print(f"Trouvé {len(async_functions)} fonctions asynchrones")
```

### 3. Identifier les fonctions avec décorateur spécifique

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Trouver toutes les fonctions avec @router.post
post_endpoints = []
for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        for decorator in func['decorators']:
            if 'router.post' in decorator:
                post_endpoints.append({
                    'name': func['name'],
                    'file': func['file_path'],
                    'decorator': decorator
                })
                break

print(f"Trouvé {len(post_endpoints)} endpoints POST")
```

### 4. Analyser les dépendances d'une fonction

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

function_name = "prepare_invoice_dataframe"

for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        if func['name'] == function_name:
            print(f"Fonction: {func['name']}")
            print(f"Fichier: {func['file_path']}")
            print(f"Dépendances:")
            for dep in func['dependencies']:
                print(f"  - {dep}")
```

### 5. Extraire toutes les fonctions d'une catégorie

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

category = "Cache"

if category in catalog['functions_by_category']:
    functions = catalog['functions_by_category'][category]
    print(f"Catégorie {category}: {len(functions)} fonctions")

    for func in functions:
        print(f"\n{func['name']}")
        print(f"  Fichier: {func['file_path']}:{func['line_number']}")
        print(f"  Réutilisabilité: {func['reusability']}")
```

### 6. Générer un graphe de dépendances

```python
import json
from collections import defaultdict

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Construire un graphe de dépendances
dependency_graph = defaultdict(set)

for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        func_id = f"{func['file_path']}::{func['name']}"
        for dep in func['dependencies']:
            dependency_graph[dep].add(func_id)

# Trouver les dépendances les plus critiques
most_used = sorted(
    dependency_graph.items(),
    key=lambda x: len(x[1]),
    reverse=True
)[:10]

print("Top 10 dépendances les plus utilisées:")
for dep, users in most_used:
    print(f"{dep}: utilisé par {len(users)} fonctions")
```

### 7. Identifier les candidats au refactoring

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Critères de refactoring :
# - Nombreux paramètres (>5)
# - Faible réutilisabilité
# - Pas de types

candidates = []
for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        if (len(func['parameters']) > 5 and
            func['reusability'] == 'Low' and
            func['return_type'] is None):

            candidates.append({
                'name': func['name'],
                'file': func['file_path'],
                'params': len(func['parameters']),
                'category': category
            })

candidates.sort(key=lambda x: x['params'], reverse=True)

print(f"Trouvé {len(candidates)} candidats au refactoring")
for c in candidates[:10]:
    print(f"{c['name']} ({c['params']} params) - {c['file']}")
```

### 8. Extraire toutes les routes API avec leurs méthodes HTTP

```python
import json
import re

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

endpoints = []

if 'API' in catalog['functions_by_category']:
    for func in catalog['functions_by_category']['API']:
        for decorator in func['decorators']:
            # Extraire méthode HTTP
            method = None
            path = None

            if 'router.get' in decorator:
                method = 'GET'
            elif 'router.post' in decorator:
                method = 'POST'
            elif 'router.put' in decorator:
                method = 'PUT'
            elif 'router.delete' in decorator:
                method = 'DELETE'
            elif 'router.patch' in decorator:
                method = 'PATCH'

            if method:
                # Extraire le chemin
                match = re.search(r'\(["\']([^"\']+)["\']', decorator)
                if match:
                    path = match.group(1)

                    endpoints.append({
                        'method': method,
                        'path': path,
                        'function': func['name'],
                        'file': func['file_path']
                    })

# Grouper par module
from collections import defaultdict
by_module = defaultdict(list)

for ep in endpoints:
    module = ep['file'].replace('backend/api/', '').replace('.py', '')
    by_module[module].append(ep)

# Afficher
for module in sorted(by_module.keys()):
    print(f"\n## {module}")
    for ep in by_module[module]:
        print(f"  {ep['method']:6} {ep['path']:40} → {ep['function']}")
```

### 9. Trouver les fonctions sans documentation

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

undocumented = []
for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        if func['description'] == "No description available":
            undocumented.append({
                'name': func['name'],
                'file': func['file_path'],
                'category': category
            })

print(f"Fonctions sans documentation: {len(undocumented)}")

# Grouper par fichier
from collections import defaultdict
by_file = defaultdict(list)

for func in undocumented:
    by_file[func['file']].append(func['name'])

# Fichiers avec le plus de fonctions non documentées
sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)

print("\nTop 10 fichiers à documenter:")
for file, funcs in sorted_files[:10]:
    print(f"{file}: {len(funcs)} fonctions")
```

### 10. Créer un rapport de couverture de types

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Par catégorie
from collections import defaultdict
type_coverage = defaultdict(lambda: {'total': 0, 'typed': 0})

for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        type_coverage[category]['total'] += 1

        # Considérer "typé" si au moins le retour est typé
        if func['return_type'] is not None:
            type_coverage[category]['typed'] += 1

# Calculer les pourcentages
print("Couverture de types par catégorie:\n")
print(f"{'Catégorie':<30} {'Typées':<10} {'Total':<10} {'%':<10}")
print("-" * 60)

for category in sorted(type_coverage.keys()):
    stats = type_coverage[category]
    pct = (stats['typed'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{category:<30} {stats['typed']:<10} {stats['total']:<10} {pct:>5.1f}%")
```

## Scripts d'Analyse Avancée

### Trouver les fonctions similaires (par signature)

```python
import json
from collections import defaultdict

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Grouper par signature similaire (nombre et types de paramètres)
signatures = defaultdict(list)

for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        # Créer une clé basée sur les types de paramètres
        param_types = tuple(p['type'] or 'Any' for p in func['parameters'])
        return_type = func['return_type'] or 'Any'

        sig_key = (len(func['parameters']), param_types, return_type)

        signatures[sig_key].append({
            'name': func['name'],
            'file': func['file_path'],
            'category': category
        })

# Trouver les signatures communes (possibles duplications)
print("Signatures communes (potentiel de factorisation):\n")

for sig, funcs in signatures.items():
    if len(funcs) >= 3:  # Au moins 3 fonctions avec la même signature
        print(f"\nSignature: {len(funcs[0])} params")
        print(f"Trouvé {len(funcs)} fonctions:")
        for f in funcs[:5]:  # Afficher les 5 premières
            print(f"  - {f['name']} ({f['file']})")
        if len(funcs) > 5:
            print(f"  ... et {len(funcs) - 5} autres")
```

## Intégration avec d'Autres Outils

### Générer des tests automatiques

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Générer des squelettes de tests pour les fonctions hautement réutilisables
for category, functions in catalog['functions_by_category'].items():
    for func in functions:
        if func['reusability'] == 'High' and not func['is_method']:
            # Générer un test basique
            test_code = f"""
def test_{func['name']}():
    \"\"\"Test for {func['name']}\"\"\"
    # TODO: Implement test
    # File: {func['file_path']}:{func['line_number']}
    pass
"""
            print(test_code)
```

### Générer de la documentation Sphinx

```python
import json

with open('python_functions_catalog.json', 'r') as f:
    catalog = json.load(f)

# Générer un fichier RST pour Sphinx
print(".. API Reference")
print("=" * 80)
print()

for category in sorted(catalog['functions_by_category'].keys()):
    functions = catalog['functions_by_category'][category]

    print(f"{category}")
    print("-" * len(category))
    print()

    for func in functions[:5]:  # Limiter pour l'exemple
        print(f".. function:: {func['name']}")
        print()
        print(f"   {func['description']}")
        print()
        print(f"   :file: {func['file_path']}")
        print(f"   :line: {func['line_number']}")
        print()
```

## Conseils d'Utilisation

1. **Recherche rapide** : Utilisez `jq` en ligne de commande pour des requêtes rapides
   ```bash
   # Trouver toutes les fonctions async
   jq '.functions_by_category | to_entries[] | .value[] | select(.is_async == true) | .name' python_functions_catalog.json

   # Compter les fonctions par catégorie
   jq '.statistics.by_category' python_functions_catalog.json
   ```

2. **Analyse de code** : Intégrez le catalogue dans vos outils de CI/CD pour détecter les régressions

3. **Documentation** : Utilisez les rapports Markdown comme base de documentation

4. **Refactoring** : Identifiez les patterns communs pour créer des abstractions

5. **Tests** : Trouvez les fonctions non testées en croisant avec votre coverage

## Mise à Jour du Catalogue

Pour régénérer le catalogue après des modifications du code :

```bash
# Analyser le code
python3 /home/ruuuzer/Documents/monprojet/analyze_functions.py

# Générer les rapports
python3 /home/ruuuzer/Documents/monprojet/generate_report.py

# Générer les statistiques
python3 /home/ruuuzer/Documents/monprojet/generate_stats.py
```

## Automatisation

Vous pouvez automatiser la génération avec un hook Git pre-commit ou dans votre CI/CD :

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Régénérer la documentation si des fichiers Python ont changé
if git diff --cached --name-only | grep -q '\.py$'; then
    echo "Régénération du catalogue de fonctions..."
    python3 analyze_functions.py
    python3 generate_report.py
    git add docs/library/
fi
```

---

Pour toute question ou suggestion d'amélioration, consultez le README principal du projet.
