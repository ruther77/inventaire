#!/usr/bin/env python3
"""
Génère un rapport Markdown lisible à partir du catalogue de fonctions.
"""

import json
from pathlib import Path
from collections import defaultdict


def load_catalog():
    """Charge le catalogue JSON."""
    catalog_path = Path('/home/ruuuzer/Documents/monprojet/docs/library/python_functions_catalog.json')
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_markdown_report(catalog):
    """Génère un rapport Markdown complet."""

    lines = []

    # En-tête
    lines.append("# Catalogue des Fonctions Python")
    lines.append("")
    lines.append("Documentation générée automatiquement des fonctions dans `/backend` et `/core`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Statistiques globales
    meta = catalog['metadata']
    stats = catalog['statistics']

    lines.append("## Statistiques Globales")
    lines.append("")
    lines.append(f"- **Fonctions totales**: {meta['total_functions']}")
    lines.append(f"- **Fichiers analysés**: {meta['total_files']}")
    lines.append(f"- **Catégories**: {len(meta['categories'])}")
    lines.append(f"- **Fonctions asynchrones**: {stats['async_functions']}")
    lines.append(f"- **Méthodes de classe**: {stats['class_methods']}")
    lines.append(f"- **Décorateurs**: {stats['decorators']}")
    lines.append(f"- **Haute réutilisabilité**: {stats['high_reusability']}")
    lines.append("")

    # Distribution par catégorie
    lines.append("## Distribution par Catégorie")
    lines.append("")
    lines.append("| Catégorie | Nombre de Fonctions |")
    lines.append("|-----------|---------------------|")

    sorted_cats = sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True)
    for cat, count in sorted_cats:
        lines.append(f"| {cat} | {count} |")

    lines.append("")

    # Index des catégories
    lines.append("## Index des Catégories")
    lines.append("")

    for cat, _ in sorted_cats:
        anchor = cat.lower().replace(' ', '-')
        lines.append(f"- [{cat}](#{anchor})")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Détails par catégorie
    funcs_by_cat = catalog['functions_by_category']

    for cat, _ in sorted_cats:
        if cat not in funcs_by_cat:
            continue

        functions = funcs_by_cat[cat]

        lines.append(f"## {cat}")
        lines.append("")
        lines.append(f"**{len(functions)} fonctions**")
        lines.append("")

        # Grouper par fichier
        by_file = defaultdict(list)
        for func in functions:
            by_file[func['file_path']].append(func)

        for file_path in sorted(by_file.keys()):
            file_funcs = by_file[file_path]

            lines.append(f"### `{file_path}`")
            lines.append("")

            for func in sorted(file_funcs, key=lambda x: x['line_number']):
                # Nom et signature
                async_marker = "async " if func['is_async'] else ""
                method_marker = "🔹 " if func['is_method'] else "🔸 "
                decorator_marker = " 🎀" if func['is_decorator'] else ""

                lines.append(f"#### {method_marker}`{async_marker}{func['name']}`{decorator_marker}")
                lines.append("")

                # Signature
                lines.append("```python")
                lines.append(func['signature'])
                lines.append("```")
                lines.append("")

                # Description
                if func['description'] != "No description available":
                    lines.append(f"**Description**: {func['description']}")
                    lines.append("")

                # Métadonnées
                lines.append(f"- **Ligne**: {func['line_number']}")
                lines.append(f"- **Réutilisabilité**: {func['reusability']}")

                if func['return_type']:
                    lines.append(f"- **Type de retour**: `{func['return_type']}`")

                if func['decorators']:
                    lines.append(f"- **Décorateurs**: `{'`, `'.join(func['decorators'])}`")

                # Paramètres
                if func['parameters']:
                    lines.append("- **Paramètres**:")
                    for param in func['parameters']:
                        param_str = f"  - `{param['name']}`"
                        if param['type']:
                            param_str += f": `{param['type']}`"
                        if param['default']:
                            param_str += f" = `{param['default']}`"
                        lines.append(param_str)

                # Dépendances
                if func['dependencies']:
                    lines.append("- **Dépendances**:")
                    for dep in func['dependencies'][:5]:  # Limiter à 5
                        lines.append(f"  - `{dep}`")
                    if len(func['dependencies']) > 5:
                        lines.append(f"  - *... et {len(func['dependencies']) - 5} autres*")

                lines.append("")

        lines.append("---")
        lines.append("")

    return '\n'.join(lines)


def generate_high_reusability_report(catalog):
    """Génère un rapport des fonctions hautement réutilisables."""

    lines = []

    lines.append("# Fonctions Hautement Réutilisables")
    lines.append("")
    lines.append("Liste des fonctions avec une haute réutilisabilité (pures, bien typées, peu de dépendances)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Collecter toutes les fonctions haute réutilisabilité
    high_reuse = []
    for cat, functions in catalog['functions_by_category'].items():
        for func in functions:
            if func['reusability'] == 'High':
                func_copy = func.copy()
                func_copy['category'] = cat
                high_reuse.append(func_copy)

    # Grouper par catégorie
    by_cat = defaultdict(list)
    for func in high_reuse:
        by_cat[func['category']].append(func)

    lines.append(f"**Total: {len(high_reuse)} fonctions**")
    lines.append("")

    for cat in sorted(by_cat.keys()):
        functions = by_cat[cat]

        lines.append(f"## {cat} ({len(functions)})")
        lines.append("")

        for func in sorted(functions, key=lambda x: x['name']):
            lines.append(f"### `{func['name']}`")
            lines.append("")
            lines.append(f"**Fichier**: `{func['file_path']}:{func['line_number']}`")
            lines.append("")
            lines.append("```python")
            lines.append(func['signature'])
            lines.append("```")
            lines.append("")

            if func['description'] != "No description available":
                lines.append(f"{func['description']}")
                lines.append("")

            if func['parameters']:
                lines.append("**Paramètres**:")
                for param in func['parameters']:
                    param_str = f"- `{param['name']}`"
                    if param['type']:
                        param_str += f": `{param['type']}`"
                    lines.append(param_str)
                lines.append("")

            if func['return_type']:
                lines.append(f"**Retour**: `{func['return_type']}`")
                lines.append("")

            lines.append("---")
            lines.append("")

    return '\n'.join(lines)


def generate_api_endpoints_report(catalog):
    """Génère un rapport spécifique pour les endpoints API."""

    lines = []

    lines.append("# Endpoints API")
    lines.append("")
    lines.append("Documentation des endpoints FastAPI extraits du code")
    lines.append("")
    lines.append("---")
    lines.append("")

    api_funcs = catalog['functions_by_category'].get('API', [])

    # Grouper par fichier
    by_file = defaultdict(list)
    for func in api_funcs:
        by_file[func['file_path']].append(func)

    for file_path in sorted(by_file.keys()):
        module_name = file_path.replace('backend/api/', '').replace('.py', '')
        module_name = module_name.replace('/', '.')

        lines.append(f"## Module: `{module_name}`")
        lines.append("")
        lines.append(f"**Fichier**: `{file_path}`")
        lines.append("")

        functions = by_file[file_path]

        for func in sorted(functions, key=lambda x: x['line_number']):
            # Extraire la route du décorateur
            route_info = "N/A"
            http_method = "GET"

            for dec in func['decorators']:
                if 'router.' in dec or 'app.' in dec:
                    # Extraire méthode HTTP et route
                    if '.get(' in dec:
                        http_method = 'GET'
                    elif '.post(' in dec:
                        http_method = 'POST'
                    elif '.put(' in dec:
                        http_method = 'PUT'
                    elif '.delete(' in dec:
                        http_method = 'DELETE'
                    elif '.patch(' in dec:
                        http_method = 'PATCH'

                    # Extraire le path
                    import re
                    match = re.search(r'\(["\']([^"\']+)["\']', dec)
                    if match:
                        route_info = match.group(1)

            lines.append(f"### `{http_method}` {route_info}")
            lines.append("")
            lines.append(f"**Fonction**: `{func['name']}`")
            lines.append("")

            if func['description'] != "No description available":
                lines.append(f"{func['description']}")
                lines.append("")

            if func['parameters']:
                lines.append("**Paramètres**:")
                for param in func['parameters']:
                    param_str = f"- `{param['name']}`"
                    if param['type']:
                        param_str += f": `{param['type']}`"
                    if param['default']:
                        param_str += f" (défaut: `{param['default']}`)"
                    lines.append(param_str)
                lines.append("")

            if func['return_type']:
                lines.append(f"**Retour**: `{func['return_type']}`")
                lines.append("")

            lines.append("```python")
            lines.append(func['signature'])
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("")

    return '\n'.join(lines)


def main():
    """Génère tous les rapports."""

    print("Chargement du catalogue...")
    catalog = load_catalog()

    output_dir = Path('/home/ruuuzer/Documents/monprojet/docs/library')

    # Rapport principal
    print("Génération du rapport principal...")
    main_report = generate_markdown_report(catalog)
    with open(output_dir / 'FUNCTIONS_CATALOG.md', 'w', encoding='utf-8') as f:
        f.write(main_report)
    print(f"  ✓ {output_dir / 'FUNCTIONS_CATALOG.md'}")

    # Rapport haute réutilisabilité
    print("Génération du rapport de réutilisabilité...")
    reuse_report = generate_high_reusability_report(catalog)
    with open(output_dir / 'HIGH_REUSABILITY_FUNCTIONS.md', 'w', encoding='utf-8') as f:
        f.write(reuse_report)
    print(f"  ✓ {output_dir / 'HIGH_REUSABILITY_FUNCTIONS.md'}")

    # Rapport API
    print("Génération du rapport API...")
    api_report = generate_api_endpoints_report(catalog)
    with open(output_dir / 'API_ENDPOINTS.md', 'w', encoding='utf-8') as f:
        f.write(api_report)
    print(f"  ✓ {output_dir / 'API_ENDPOINTS.md'}")

    print("")
    print("Tous les rapports ont été générés avec succès!")


if __name__ == '__main__':
    main()
