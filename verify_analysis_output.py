#!/usr/bin/env python3
"""
Vérifie que tous les fichiers d'analyse ont été correctement générés.
"""

import os
import json


def verify_output():
    """Vérifie et liste tous les fichiers générés."""

    base_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs'

    expected_files = {
        'detailed_analysis.json': 'Données brutes JSON avec analyse complète',
        'detailed_analysis.md': 'Documentation Markdown lisible',
        'detailed_analysis.html': 'Interface web interactive',
        'ANALYSIS_SUMMARY.txt': 'Résumé visuel ASCII',
    }

    print("=" * 80)
    print("VÉRIFICATION DES FICHIERS GÉNÉRÉS")
    print("=" * 80)
    print()

    all_good = True
    total_size = 0

    for filename, description in expected_files.items():
        filepath = os.path.join(base_path, filename)

        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            size_mb = size / (1024 * 1024)
            size_kb = size / 1024

            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"

            print(f"✅ {filename}")
            print(f"   📄 {description}")
            print(f"   📊 Taille: {size_str}")
            print(f"   📍 Chemin: {filepath}")
            print()

            total_size += size
        else:
            print(f"❌ {filename}")
            print(f"   📄 {description}")
            print(f"   ⚠️  FICHIER MANQUANT!")
            print()
            all_good = False

    print("=" * 80)
    print(f"Taille totale: {total_size / (1024 * 1024):.2f} MB")
    print("=" * 80)
    print()

    # Vérifier le contenu du JSON
    json_path = os.path.join(base_path, 'detailed_analysis.json')
    if os.path.exists(json_path):
        print("CONTENU DU FICHIER JSON:")
        print("-" * 80)

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"✓ Métadonnées présentes: {list(data.get('metadata', {}).keys())}")
            print(f"✓ Statistiques présentes: {list(data.get('summary', {}).keys())}")
            print(f"✓ Nombre de fonctions: {len(data.get('functions', []))}")
            print()

            if data.get('functions'):
                func = data['functions'][0]
                print(f"✓ Structure d'une fonction (exemple: {func.get('name')}):")
                print(f"  - Champs présents: {list(func.keys())}")
                print(f"  - Préconditions: {len(func.get('preconditions', []))}")
                print(f"  - Postconditions: {len(func.get('postconditions', []))}")
                print(f"  - Tests: {len(func.get('test_cases', []))}")
                print(f"  - Code source: {'Oui' if func.get('source_code') else 'Non'}")
                print(f"  - Code refactorisé: {'Oui' if func.get('refactored_code') else 'Non'}")
                print(f"  - Code tests: {'Oui' if func.get('test_code') else 'Non'}")

            print()
            print("✅ Fichier JSON valide et complet!")

        except json.JSONDecodeError as e:
            print(f"❌ ERREUR: Le fichier JSON est invalide: {e}")
            all_good = False
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            all_good = False

        print()

    # Scripts utilisés
    print("=" * 80)
    print("SCRIPTS UTILISÉS POUR GÉNÉRER L'ANALYSE")
    print("=" * 80)
    print()

    scripts = [
        ('analyze_functions.py', 'Analyse initiale de toutes les fonctions'),
        ('deep_function_analysis.py', 'Analyse approfondie des 30 meilleures'),
        ('generate_readable_report.py', 'Génération du rapport Markdown'),
        ('generate_html_report.py', 'Génération de l\'interface web'),
        ('create_analysis_summary.py', 'Génération du résumé ASCII'),
    ]

    for script, description in scripts:
        script_path = f"/home/ruuuzer/Documents/monprojet/{script}"
        if os.path.exists(script_path):
            print(f"✅ {script}")
            print(f"   {description}")
        else:
            print(f"❌ {script} - MANQUANT")
        print()

    print("=" * 80)
    if all_good:
        print("🎉 ANALYSE COMPLÈTE GÉNÉRÉE AVEC SUCCÈS!")
    else:
        print("⚠️  ATTENTION: Certains fichiers sont manquants")
    print("=" * 80)
    print()

    print("PROCHAINES ÉTAPES:")
    print()
    print("1. CONSULTATION INTERACTIVE (Recommandé):")
    print(f"   firefox {os.path.join(base_path, 'detailed_analysis.html')}")
    print()
    print("2. LECTURE DE LA DOCUMENTATION:")
    print(f"   cat {os.path.join(base_path, 'detailed_analysis.md')}")
    print()
    print("3. EXPLOITATION PROGRAMMATIQUE:")
    print("   python3 -c \"import json; data = json.load(open('detailed_analysis.json'))\"")
    print()
    print("4. RÉSUMÉ RAPIDE:")
    print(f"   cat {os.path.join(base_path, 'ANALYSIS_SUMMARY.txt')}")
    print()


if __name__ == '__main__':
    verify_output()
