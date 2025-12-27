#!/usr/bin/env python3
"""
Génère un rapport markdown lisible à partir de l'analyse JSON.
"""

import json
import os


def generate_markdown_report(json_path: str, output_path: str):
    """Génère un rapport markdown à partir du JSON."""

    # Charger le JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Créer le markdown
    md = []

    # En-tête
    md.append("# Analyse Approfondie des 30 Fonctions les Plus Réutilisables")
    md.append("")
    md.append(f"**Date:** {data['metadata']['generated_at']}")
    md.append(f"**Projet:** {data['metadata']['project_root']}")
    md.append(f"**Fonctions analysées:** {data['metadata']['total_functions_analyzed']}")
    md.append("")

    # Résumé exécutif
    md.append("## Résumé Exécutif")
    md.append("")
    md.append(f"- **Bugs potentiels identifiés:** {data['summary']['total_bugs_identified']}")
    md.append(f"- **Problèmes de performance:** {data['summary']['total_performance_issues']}")
    md.append(f"- **Risques de sécurité:** {data['summary']['total_security_risks']}")
    md.append("")

    # Répartition par domaines
    md.append("### Répartition par Domaines Métier")
    md.append("")
    md.append("| Domaine | Nombre de fonctions |")
    md.append("|---------|---------------------|")
    for domain, count in sorted(data['summary']['business_domains'].items(), key=lambda x: x[1], reverse=True):
        md.append(f"| {domain} | {count} |")
    md.append("")

    md.append("### Répartition par Domaines Techniques")
    md.append("")
    md.append("| Domaine | Nombre de fonctions |")
    md.append("|---------|---------------------|")
    for domain, count in sorted(data['summary']['technical_domains'].items(), key=lambda x: x[1], reverse=True):
        md.append(f"| {domain} | {count} |")
    md.append("")

    md.append("### Patterns de Conception Utilisés")
    md.append("")
    md.append("| Pattern | Nombre de fonctions |")
    md.append("|---------|---------------------|")
    for pattern, count in sorted(data['summary']['design_patterns'].items(), key=lambda x: x[1], reverse=True):
        md.append(f"| {pattern} | {count} |")
    md.append("")

    # Table des matières
    md.append("## Table des Matières")
    md.append("")
    for i, func in enumerate(data['functions'], 1):
        md.append(f"{i}. [{func['name']}](#{func['name'].lower().replace('_', '-')}) - `{func['file_path']}`")
    md.append("")

    # Analyses détaillées
    md.append("---")
    md.append("")
    md.append("## Analyses Détaillées")
    md.append("")

    for i, func in enumerate(data['functions'], 1):
        md.append(f"### {i}. {func['name']}")
        md.append("")

        # Informations de base
        md.append("#### Informations de Base")
        md.append("")
        md.append(f"- **Fichier:** `{func['file_path']}`")
        md.append(f"- **Ligne:** {func['line_number']}")
        md.append(f"- **Signature:** `{func['signature']}`")
        md.append("")

        # Rôle et contexte
        md.append("#### 1. RÔLE")
        md.append("")
        md.append(f"**Description:** {func['role_description']}")
        md.append("")
        md.append(f"**Contexte métier:** {func['business_context']}")
        md.append("")

        # Classification
        md.append("#### 2. CLASSIFICATION")
        md.append("")
        md.append(f"- **Domaine métier:** {func['business_domain']}")
        md.append(f"- **Domaine technique:** {func['technical_domain']}")
        md.append(f"- **Pattern utilisé:** {func['design_pattern']}")
        md.append("")

        # Préconditions/Postconditions
        md.append("#### 3. PRÉCONDITIONS / POSTCONDITIONS")
        md.append("")

        md.append("**Préconditions:**")
        for pre in func['preconditions']:
            md.append(f"- {pre}")
        md.append("")

        md.append("**Postconditions:**")
        for post in func['postconditions']:
            md.append(f"- {post}")
        md.append("")

        md.append("**Invariants:**")
        for inv in func['invariants']:
            md.append(f"- {inv}")
        md.append("")

        # Dépendances
        md.append("#### 4. DÉPENDANCES")
        md.append("")

        if func['internal_dependencies']:
            md.append("**Dépendances internes:**")
            for dep in func['internal_dependencies']:
                md.append(f"- `{dep}`")
            md.append("")

        if func['external_dependencies']:
            md.append("**Dépendances externes:**")
            for dep in func['external_dependencies']:
                md.append(f"- `{dep}`")
            md.append("")

        if func['required_config']:
            md.append("**Configuration requise:**")
            for cfg in func['required_config']:
                md.append(f"- {cfg}")
            md.append("")

        # Risques
        md.append("#### 5. RISQUES")
        md.append("")

        md.append("**Bugs potentiels:**")
        for bug in func['potential_bugs']:
            severity = "🔴" if "CRITICAL" in bug else "🟠" if "RISK" in bug else "🟡"
            md.append(f"{severity} {bug}")
        md.append("")

        md.append("**Performance:**")
        md.append(f"- Complexité cyclomatique: {func['complexity_metrics']['cyclomatic_complexity']}")
        md.append(f"- Lignes de code: {func['complexity_metrics']['lines_of_code']}")
        md.append(f"- Niveau d'imbrication: {func['complexity_metrics']['max_nesting_level']}")
        for issue in func['performance_issues']:
            md.append(f"- ⚠️ {issue}")
        md.append("")

        md.append("**Sécurité:**")
        for risk in func['security_risks']:
            severity = "🔴" if "CRITICAL" in risk else "🟠"
            md.append(f"{severity} {risk}")
        md.append("")

        # Version refactorisée
        md.append("#### 6. VERSION REFACTORISÉE")
        md.append("")

        md.append("**Améliorations proposées:**")
        for improvement in func['refactoring_improvements']:
            md.append(f"- ✅ {improvement}")
        md.append("")

        md.append("<details>")
        md.append("<summary>Code refactorisé (cliquer pour voir)</summary>")
        md.append("")
        md.append("```python")
        md.append(func['refactored_code'])
        md.append("```")
        md.append("")
        md.append("</details>")
        md.append("")

        # Tests unitaires
        md.append("#### 7. TESTS UNITAIRES")
        md.append("")

        md.append("**Cas de test:**")
        for test in func['test_cases']:
            md.append(f"- **{test['name']}** ({test['type']}): {test['description']}")
        md.append("")

        md.append("<details>")
        md.append("<summary>Code des tests (cliquer pour voir)</summary>")
        md.append("")
        md.append("```python")
        md.append(func['test_code'])
        md.append("```")
        md.append("")
        md.append("</details>")
        md.append("")

        # Code source original
        md.append("<details>")
        md.append("<summary>Code source original (cliquer pour voir)</summary>")
        md.append("")
        md.append("```python")
        md.append(func['source_code'])
        md.append("```")
        md.append("")
        md.append("</details>")
        md.append("")

        md.append("---")
        md.append("")

    # Annexes
    md.append("## Annexes")
    md.append("")

    md.append("### Méthodologie")
    md.append("")
    md.append("Cette analyse a été réalisée en utilisant:")
    md.append("- Analyse statique du code Python via AST (Abstract Syntax Tree)")
    md.append("- Détection de patterns de conception")
    md.append("- Analyse de complexité cyclomatique")
    md.append("- Identification de risques de sécurité et de performance")
    md.append("- Génération automatique de tests unitaires")
    md.append("")

    md.append("### Légende des Risques")
    md.append("")
    md.append("- 🔴 **CRITICAL**: Nécessite une action immédiate")
    md.append("- 🟠 **RISK/WARNING**: Doit être revu et corrigé")
    md.append("- 🟡 **INFO**: Bonne pratique à considérer")
    md.append("- ✅ **Amélioration**: Proposition d'amélioration")
    md.append("")

    # Écrire le fichier
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f"Rapport markdown généré: {output_path}")
    print(f"Taille: {len('\n'.join(md))} caractères")


def main():
    """Point d'entrée principal."""
    json_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.json'
    output_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.md'

    generate_markdown_report(json_path, output_path)


if __name__ == '__main__':
    main()
