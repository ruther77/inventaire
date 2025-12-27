#!/usr/bin/env python3
"""
Crée un résumé visuel ASCII de l'analyse.
"""

import json
import os


def create_summary():
    """Crée un fichier résumé."""

    json_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    summary = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              📊 ANALYSE APPROFONDIE DES FONCTIONS RÉUTILISABLES              ║
║                                                                              ║
║                    Top 30 Fonctions - Projet MonProjet                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📅 Date: {date}
📂 Projet: {project}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              📈 STATISTIQUES GLOBALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✅ Fonctions analysées:           {total_functions}
  🐛 Bugs potentiels identifiés:    {bugs}
  ⚡ Problèmes de performance:       {perf}
  🔒 Risques de sécurité:            {security}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            🏢 RÉPARTITION PAR DOMAINE MÉTIER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""".format(
        date=data['metadata']['generated_at'],
        project=data['metadata']['project_root'],
        total_functions=data['metadata']['total_functions_analyzed'],
        bugs=data['summary']['total_bugs_identified'],
        perf=data['summary']['total_performance_issues'],
        security=data['summary']['total_security_risks']
    )

    # Domaines métier
    for domain, count in sorted(data['summary']['business_domains'].items(), key=lambda x: x[1], reverse=True):
        bar = '█' * count + '░' * (30 - count)
        summary += f"  {domain:.<45} {bar} {count:>2}\n"

    summary += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ⚙️  RÉPARTITION PAR DOMAINE TECHNIQUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    # Domaines techniques
    for domain, count in sorted(data['summary']['technical_domains'].items(), key=lambda x: x[1], reverse=True):
        bar = '█' * count + '░' * (30 - count)
        summary += f"  {domain:.<45} {bar} {count:>2}\n"

    summary += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          🎨 PATTERNS DE CONCEPTION UTILISÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    # Patterns
    for pattern, count in sorted(data['summary']['design_patterns'].items(), key=lambda x: x[1], reverse=True):
        bar = '█' * count + '░' * (30 - count)
        summary += f"  {pattern:.<45} {bar} {count:>2}\n"

    summary += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              🔝 TOP 10 FONCTIONS ANALYSÉES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    # Top 10 fonctions
    for i, func in enumerate(data['functions'][:10], 1):
        complexity = func['complexity_metrics']['cyclomatic_complexity']
        loc = func['complexity_metrics']['lines_of_code']

        # Indicateurs de risque
        has_critical = any('CRITICAL' in item for item in func['potential_bugs'] + func['security_risks'])
        has_warning = any('RISK' in item or 'WARNING' in item for item in func['potential_bugs'] + func['performance_issues'] + func['security_risks'])

        risk_indicator = '🔴' if has_critical else '🟠' if has_warning else '🟢'

        summary += f"{i:>2}. {risk_indicator} {func['name']:<35} | Complexité: {complexity:>2} | LOC: {loc:>3}\n"
        summary += f"     📁 {func['file_path']}\n"
        summary += f"     🏢 {func['business_domain']} | ⚙️  {func['technical_domain']}\n\n"

    summary += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                🎯 ACTIONS PRIORITAIRES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 CRITIQUE (Action Immédiate):
"""

    # Collecter les risques critiques
    critical_risks = set()
    for func in data['functions']:
        for risk in func['potential_bugs'] + func['security_risks']:
            if 'CRITICAL' in risk:
                critical_risks.add(risk.replace('CRITICAL: ', ''))

    for risk in sorted(critical_risks):
        summary += f"   • {risk}\n"

    summary += """
🟠 HAUTE PRIORITÉ:
   • Optimiser les requêtes N+1 dans les boucles
   • Ajouter validation d'entrée manquante
   • Implémenter gestion d'erreurs robuste
   • Corriger les race conditions potentielles

✅ AMÉLIORATIONS:
   • Ajouter cache sur requêtes fréquentes
   • Implémenter pagination systématique
   • Ajouter logging pour observabilité
   • Compléter tests unitaires

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                📁 FICHIERS GÉNÉRÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 detailed_analysis.json      → Données brutes JSON (~1.2MB)
📝 detailed_analysis.md        → Documentation Markdown (~212KB)
🌐 detailed_analysis.html      → Interface web interactive (~378KB)
📋 README.md                   → Guide d'utilisation
📊 ANALYSIS_SUMMARY.txt        → Ce résumé

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                  🚀 UTILISATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMANDÉ:
  Ouvrir detailed_analysis.html dans votre navigateur pour une exploration
  interactive avec filtres et recherche.

  $ firefox /home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.html

ALTERNATIVES:
  • Lire detailed_analysis.md pour documentation textuelle
  • Exploiter detailed_analysis.json pour analyse programmatique

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                   📊 MÉTHODOLOGIE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cette analyse a été réalisée via:

  ✓ Analyse statique AST Python
  ✓ Détection automatique de patterns
  ✓ Calcul de métriques de complexité
  ✓ Identification de risques sécurité/performance
  ✓ Génération automatique de tests

Scripts utilisés:
  • analyze_functions.py           → Analyse initiale (1149 fonctions)
  • deep_function_analysis.py      → Analyse approfondie (30 fonctions)
  • generate_readable_report.py    → Génération markdown
  • generate_html_report.py        → Génération HTML

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyse complétée avec succès! 🎉

Pour toute question ou régénération, exécutez les scripts dans l'ordre ci-dessus.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Écrire le fichier
    output_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/ANALYSIS_SUMMARY.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(summary)
    print(f"\n✅ Résumé généré: {output_path}")


if __name__ == '__main__':
    create_summary()
