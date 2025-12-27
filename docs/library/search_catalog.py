#!/usr/bin/env python3
"""
Utilitaire de recherche dans le catalogue de fonctions JavaScript
Usage: python search_catalog.py [OPTIONS]
"""

import json
import sys
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "javascript_functions_catalog.json"

def load_catalog():
    """Charge le catalogue"""
    with open(CATALOG_PATH) as f:
        return json.load(f)

def search_by_name(catalog, query):
    """Recherche par nom de fonction"""
    results = []
    query_lower = query.lower()

    for func_id, func in catalog['functions_flat'].items():
        if query_lower in func['name'].lower():
            results.append(func)

    return results

def search_by_category(catalog, category):
    """Recherche par catégorie"""
    if category in catalog['functions_by_category']:
        return catalog['functions_by_category'][category]
    return []

def search_by_type(catalog, func_type):
    """Recherche par type"""
    results = []
    for func in catalog['functions_flat'].values():
        if func['type'] == func_type:
            results.append(func)
    return results

def search_by_file(catalog, filepath):
    """Recherche par fichier"""
    results = []
    for func in catalog['functions_flat'].values():
        if filepath.lower() in func['file'].lower():
            results.append(func)
    return results

def search_high_reusability(catalog):
    """Fonctions hautement réutilisables"""
    results = []
    for func in catalog['functions_flat'].values():
        if func['reusability'] == 'High':
            results.append(func)
    return sorted(results, key=lambda x: x['reusability_score'], reverse=True)

def search_high_complexity(catalog, threshold=10):
    """Fonctions complexes"""
    results = []
    for func in catalog['functions_flat'].values():
        if func['complexity_score'] >= threshold:
            results.append(func)
    return sorted(results, key=lambda x: x['complexity_score'], reverse=True)

def display_function(func, detailed=False):
    """Affiche une fonction"""
    print(f"\n📌 {func['name']}")
    print(f"   📁 {func['file']}")
    print(f"   🏷️  Type: {func['type']}")
    print(f"   📂 Catégorie: {func['category']}")
    print(f"   ♻️  Réutilisabilité: {func['reusability']} (score: {func['reusability_score']})")
    print(f"   📊 Complexité: {func['complexity_score']}")

    if func.get('description'):
        print(f"   📝 {func['description'][:100]}...")

    if detailed:
        print(f"\n   Signature: {func['signature']}")
        print(f"   Async: {func['is_async']}")
        print(f"   Exported: {func['is_exported']}")

        if func['parameters']:
            print(f"   Paramètres:")
            for param in func['parameters']:
                required = "requis" if param['required'] else "optionnel"
                default = f" = {param.get('default')}" if param.get('default') else ""
                print(f"     • {param['name']}: {param['type']} ({required}){default}")

        if func['dependencies']['packages']:
            print(f"   Dépendances: {', '.join(func['dependencies']['packages'][:5])}")

        body = func.get('body_analysis', {})
        features = []
        if body.get('uses_state'): features.append('useState')
        if body.get('uses_effect'): features.append('useEffect')
        if body.get('uses_query'): features.append('useQuery')
        if body.get('has_jsx'): features.append('JSX')
        if body.get('calls_api'): features.append('API')
        if features:
            print(f"   Utilise: {', '.join(features)}")

def main():
    if len(sys.argv) < 2:
        print("""
Utilitaire de recherche dans le catalogue de fonctions JavaScript

Usage:
  python search_catalog.py name <query>        Rechercher par nom
  python search_catalog.py category <name>     Rechercher par catégorie
  python search_catalog.py type <type>         Rechercher par type
  python search_catalog.py file <path>         Rechercher par fichier
  python search_catalog.py reusable            Fonctions hautement réutilisables
  python search_catalog.py complex [threshold] Fonctions complexes (défaut: 10)
  python search_catalog.py stats               Afficher les statistiques

Exemples:
  python search_catalog.py name format
  python search_catalog.py category "Hooks/Data Fetching"
  python search_catalog.py type "custom hook"
  python search_catalog.py file useAuth
  python search_catalog.py reusable
  python search_catalog.py complex 15
  python search_catalog.py stats
""")
        sys.exit(1)

    catalog = load_catalog()
    command = sys.argv[1].lower()

    if command == 'name':
        if len(sys.argv) < 3:
            print("Usage: python search_catalog.py name <query>")
            sys.exit(1)
        query = sys.argv[2]
        results = search_by_name(catalog, query)
        print(f"\n🔍 Recherche par nom: '{query}'")
        print(f"📊 {len(results)} résultat(s)")
        for func in results[:20]:
            display_function(func)

    elif command == 'category':
        if len(sys.argv) < 3:
            print("Catégories disponibles:")
            for cat in sorted(catalog['metadata']['categories'].keys()):
                count = catalog['metadata']['categories'][cat]
                print(f"  • {cat} ({count})")
            sys.exit(0)
        category = sys.argv[2]
        results = search_by_category(catalog, category)
        print(f"\n📂 Catégorie: {category}")
        print(f"📊 {len(results)} résultat(s)")
        for func in results[:20]:
            display_function(func)

    elif command == 'type':
        if len(sys.argv) < 3:
            print("Types disponibles:")
            for t, count in catalog['metadata']['types'].items():
                print(f"  • {t} ({count})")
            sys.exit(0)
        func_type = sys.argv[2]
        results = search_by_type(catalog, func_type)
        print(f"\n🏷️  Type: {func_type}")
        print(f"📊 {len(results)} résultat(s)")
        for func in results[:20]:
            display_function(func)

    elif command == 'file':
        if len(sys.argv) < 3:
            print("Usage: python search_catalog.py file <path>")
            sys.exit(1)
        filepath = sys.argv[2]
        results = search_by_file(catalog, filepath)
        print(f"\n📁 Fichier contenant: '{filepath}'")
        print(f"📊 {len(results)} résultat(s)")
        for func in results:
            display_function(func)

    elif command == 'reusable':
        results = search_high_reusability(catalog)
        print(f"\n♻️  Fonctions hautement réutilisables")
        print(f"📊 {len(results)} résultat(s)")
        for func in results[:30]:
            display_function(func, detailed=True)

    elif command == 'complex':
        threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        results = search_high_complexity(catalog, threshold)
        print(f"\n📈 Fonctions complexes (complexité >= {threshold})")
        print(f"📊 {len(results)} résultat(s)")
        for func in results[:20]:
            display_function(func, detailed=True)

    elif command == 'stats':
        meta = catalog['metadata']
        print(f"\n📊 Statistiques du catalogue")
        print(f"\n📁 Fichiers analysés: {meta['total_files']}")
        print(f"🔧 Fonctions trouvées: {meta['total_functions']}")

        print(f"\n🏷️  Par type:")
        for t, count in sorted(meta['types'].items(), key=lambda x: -x[1]):
            pct = (count / meta['total_functions']) * 100
            print(f"  • {t}: {count} ({pct:.1f}%)")

        print(f"\n♻️  Par réutilisabilité:")
        for level, count in sorted(meta['reusability'].items(), key=lambda x: -x[1]):
            pct = (count / meta['total_functions']) * 100
            print(f"  • {level}: {count} ({pct:.1f}%)")

        print(f"\n📈 Par complexité:")
        for level, count in sorted(meta['complexity_distribution'].items(), key=lambda x: -x[1]):
            pct = (count / meta['total_functions']) * 100
            print(f"  • {level}: {count} ({pct:.1f}%)")

        print(f"\n📂 Top 10 catégories:")
        for cat, count in sorted(meta['categories'].items(), key=lambda x: -x[1])[:10]:
            pct = (count / meta['total_functions']) * 100
            print(f"  • {cat}: {count} ({pct:.1f}%)")

    else:
        print(f"Commande inconnue: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
