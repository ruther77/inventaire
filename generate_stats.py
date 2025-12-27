#!/usr/bin/env python3
"""
Génère des statistiques avancées et analyses du catalogue de fonctions.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter


def load_catalog():
    """Charge le catalogue JSON."""
    catalog_path = Path('/home/ruuuzer/Documents/monprojet/docs/library/python_functions_catalog.json')
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_catalog(catalog):
    """Effectue des analyses approfondies."""

    all_functions = []
    for cat, funcs in catalog['functions_by_category'].items():
        for func in funcs:
            func_copy = func.copy()
            func_copy['category'] = cat
            all_functions.append(func_copy)

    stats = {
        'total_functions': len(all_functions),
        'by_category': {},
        'by_file': {},
        'by_reusability': defaultdict(int),
        'decorators_usage': Counter(),
        'most_common_params': Counter(),
        'dependency_analysis': {},
        'function_length': {'short': 0, 'medium': 0, 'long': 0, 'very_long': 0},
        'type_annotations': {'with_params': 0, 'with_return': 0, 'fully_typed': 0, 'untyped': 0},
        'async_by_category': defaultdict(int),
        'top_files': {},
        'orphan_functions': [],
        'complex_signatures': [],
    }

    # Analyse par fichier
    by_file = defaultdict(list)
    for func in all_functions:
        by_file[func['file_path']].append(func)
        stats['by_reusability'][func['reusability']] += 1

        # Décorateurs
        for dec in func['decorators']:
            # Extraire le nom de base du décorateur
            dec_name = dec.split('(')[0].strip()
            stats['decorators_usage'][dec_name] += 1

        # Paramètres communs
        for param in func['parameters']:
            stats['most_common_params'][param['name']] += 1

        # Longueur de fonction (estimation)
        # On ne peut pas avoir la vraie longueur, mais on peut estimer par le nombre de paramètres
        param_count = len(func['parameters'])
        if param_count <= 2:
            stats['function_length']['short'] += 1
        elif param_count <= 4:
            stats['function_length']['medium'] += 1
        elif param_count <= 6:
            stats['function_length']['long'] += 1
        else:
            stats['function_length']['very_long'] += 1

        # Annotations de type
        has_param_types = any(p['type'] for p in func['parameters'])
        has_return_type = func['return_type'] is not None

        if has_param_types and has_return_type:
            stats['type_annotations']['fully_typed'] += 1
        elif has_param_types:
            stats['type_annotations']['with_params'] += 1
        elif has_return_type:
            stats['type_annotations']['with_return'] += 1
        else:
            stats['type_annotations']['untyped'] += 1

        # Async par catégorie
        if func['is_async']:
            stats['async_by_category'][func['category']] += 1

        # Signatures complexes (nombreux paramètres)
        if len(func['parameters']) >= 6:
            stats['complex_signatures'].append({
                'name': func['name'],
                'file': func['file_path'],
                'param_count': len(func['parameters'])
            })

    # Top fichiers
    stats['top_files'] = {
        file: len(funcs)
        for file, funcs in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    }

    # Analyse des dépendances
    all_deps = []
    for func in all_functions:
        all_deps.extend(func['dependencies'])

    dep_counter = Counter(all_deps)
    stats['dependency_analysis'] = {
        'total_unique_dependencies': len(set(all_deps)),
        'most_common': dict(dep_counter.most_common(20)),
        'functions_with_no_deps': sum(1 for f in all_functions if not f['dependencies']),
        'functions_with_many_deps': sum(1 for f in all_functions if len(f['dependencies']) > 5),
    }

    # Fonctions "orphelines" (pas de description, pas de types, low reusability)
    for func in all_functions:
        if (func['description'] == "No description available" and
            func['reusability'] == 'Low' and
            not func['return_type']):
            stats['orphan_functions'].append({
                'name': func['name'],
                'file': func['file_path'],
                'category': func['category']
            })

    return stats


def generate_stats_report(catalog, stats):
    """Génère un rapport de statistiques détaillées."""

    lines = []

    lines.append("# Analyse Statistique Approfondie")
    lines.append("")
    lines.append("Statistiques avancées sur le catalogue de fonctions Python")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Vue d'ensemble
    lines.append("## Vue d'Ensemble")
    lines.append("")
    lines.append(f"- **Fonctions totales**: {stats['total_functions']}")
    lines.append(f"- **Fichiers analysés**: {len(stats['top_files'])}")
    lines.append(f"- **Dépendances uniques**: {stats['dependency_analysis']['total_unique_dependencies']}")
    lines.append("")

    # Réutilisabilité
    lines.append("## Distribution de la Réutilisabilité")
    lines.append("")
    lines.append("| Niveau | Nombre | Pourcentage |")
    lines.append("|--------|--------|-------------|")
    for level in ['High', 'Medium', 'Low']:
        count = stats['by_reusability'][level]
        pct = (count / stats['total_functions']) * 100
        lines.append(f"| {level} | {count} | {pct:.1f}% |")
    lines.append("")

    # Annotations de type
    lines.append("## Annotations de Type")
    lines.append("")
    lines.append("| Type | Nombre | Pourcentage |")
    lines.append("|------|--------|-------------|")
    type_total = sum(stats['type_annotations'].values())
    for type_name, count in stats['type_annotations'].items():
        pct = (count / type_total) * 100
        lines.append(f"| {type_name.replace('_', ' ').title()} | {count} | {pct:.1f}% |")
    lines.append("")

    # Complexité des signatures
    lines.append("## Complexité des Signatures")
    lines.append("")
    lines.append("Distribution basée sur le nombre de paramètres :")
    lines.append("")
    lines.append("| Complexité | Nombre | Description |")
    lines.append("|------------|--------|-------------|")
    lines.append(f"| Simple (≤2 params) | {stats['function_length']['short']} | Facile à utiliser |")
    lines.append(f"| Moyenne (3-4 params) | {stats['function_length']['medium']} | Standard |")
    lines.append(f"| Élevée (5-6 params) | {stats['function_length']['long']} | À simplifier |")
    lines.append(f"| Très élevée (≥7 params) | {stats['function_length']['very_long']} | Refactoring recommandé |")
    lines.append("")

    # Top décorateurs
    lines.append("## Décorateurs les Plus Utilisés")
    lines.append("")
    lines.append("| Décorateur | Utilisation |")
    lines.append("|------------|-------------|")
    for dec, count in stats['decorators_usage'].most_common(15):
        lines.append(f"| `{dec}` | {count} |")
    lines.append("")

    # Paramètres communs
    lines.append("## Noms de Paramètres les Plus Fréquents")
    lines.append("")
    lines.append("| Paramètre | Occurrences |")
    lines.append("|-----------|-------------|")
    for param, count in stats['most_common_params'].most_common(20):
        lines.append(f"| `{param}` | {count} |")
    lines.append("")

    # Dépendances
    lines.append("## Analyse des Dépendances")
    lines.append("")
    lines.append(f"- **Dépendances uniques**: {stats['dependency_analysis']['total_unique_dependencies']}")
    lines.append(f"- **Fonctions sans dépendances**: {stats['dependency_analysis']['functions_with_no_deps']}")
    lines.append(f"- **Fonctions avec nombreuses dépendances (>5)**: {stats['dependency_analysis']['functions_with_many_deps']}")
    lines.append("")
    lines.append("### Dépendances les Plus Communes")
    lines.append("")
    lines.append("| Dépendance | Utilisations |")
    lines.append("|------------|--------------|")
    for dep, count in sorted(stats['dependency_analysis']['most_common'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| `{dep}` | {count} |")
    lines.append("")

    # Fonctions asynchrones
    lines.append("## Fonctions Asynchrones par Catégorie")
    lines.append("")
    lines.append("| Catégorie | Fonctions Async |")
    lines.append("|-----------|-----------------|")
    for cat, count in sorted(stats['async_by_category'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {cat} | {count} |")
    lines.append("")

    # Top fichiers
    lines.append("## Fichiers avec le Plus de Fonctions")
    lines.append("")
    lines.append("| Fichier | Fonctions |")
    lines.append("|---------|-----------|")
    for file, count in list(stats['top_files'].items())[:20]:
        lines.append(f"| `{file}` | {count} |")
    lines.append("")

    # Signatures complexes
    if stats['complex_signatures']:
        lines.append("## Fonctions avec Signatures Complexes")
        lines.append("")
        lines.append("Fonctions avec 6+ paramètres (candidates au refactoring) :")
        lines.append("")
        lines.append("| Fonction | Fichier | Nb Params |")
        lines.append("|----------|---------|-----------|")
        sorted_complex = sorted(stats['complex_signatures'], key=lambda x: x['param_count'], reverse=True)
        for func in sorted_complex[:30]:
            lines.append(f"| `{func['name']}` | `{func['file']}` | {func['param_count']} |")
        lines.append("")

    # Fonctions orphelines
    if stats['orphan_functions']:
        lines.append("## Fonctions Nécessitant Attention")
        lines.append("")
        lines.append("Fonctions sans description, sans types, et faible réutilisabilité :")
        lines.append("")
        lines.append(f"**Total : {len(stats['orphan_functions'])} fonctions**")
        lines.append("")
        lines.append("| Fonction | Fichier | Catégorie |")
        lines.append("|----------|---------|-----------|")
        for func in stats['orphan_functions'][:50]:
            lines.append(f"| `{func['name']}` | `{func['file']}` | {func['category']} |")
        lines.append("")

    # Recommandations
    lines.append("## Recommandations")
    lines.append("")

    high_reuse_pct = (stats['by_reusability']['High'] / stats['total_functions']) * 100
    if high_reuse_pct < 40:
        lines.append(f"- ⚠️ Seulement {high_reuse_pct:.1f}% de fonctions hautement réutilisables. Objectif : >50%")
    else:
        lines.append(f"- ✅ {high_reuse_pct:.1f}% de fonctions hautement réutilisables")

    untyped_pct = (stats['type_annotations']['untyped'] / stats['total_functions']) * 100
    if untyped_pct > 30:
        lines.append(f"- ⚠️ {untyped_pct:.1f}% de fonctions sans annotations de type. Ajouter des types progressivement")
    else:
        lines.append(f"- ✅ {untyped_pct:.1f}% de fonctions sans types (bon niveau)")

    if stats['orphan_functions']:
        lines.append(f"- ⚠️ {len(stats['orphan_functions'])} fonctions nécessitent documentation et amélioration")

    if stats['function_length']['very_long'] > 0:
        lines.append(f"- ⚠️ {stats['function_length']['very_long']} fonctions avec nombreux paramètres (≥7). Envisager le refactoring")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Note** : Ces statistiques sont basées sur l'analyse statique du code et peuvent nécessiter une validation manuelle.")

    return '\n'.join(lines)


def main():
    """Génère le rapport de statistiques."""

    print("Chargement du catalogue...")
    catalog = load_catalog()

    print("Analyse en cours...")
    stats = analyze_catalog(catalog)

    print("Génération du rapport...")
    report = generate_stats_report(catalog, stats)

    output_dir = Path('/home/ruuuzer/Documents/monprojet/docs/library')
    output_file = output_dir / 'ADVANCED_STATISTICS.md'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Rapport généré : {output_file}")
    print("")
    print("Résumé rapide :")
    print(f"  - Fonctions hautement réutilisables : {stats['by_reusability']['High']} ({stats['by_reusability']['High']/stats['total_functions']*100:.1f}%)")
    print(f"  - Fonctions avec types complets : {stats['type_annotations']['fully_typed']}")
    print(f"  - Fonctions à documenter : {len(stats['orphan_functions'])}")
    print(f"  - Signatures complexes : {len(stats['complex_signatures'])}")


if __name__ == '__main__':
    main()
