#!/usr/bin/env python3
"""
Module d'analyse de performance du système de catégorisation automatique des transactions.

Ce script permet de:
- Analyser la précision de la catégorisation automatique des transactions financières
- Mesurer l'évolution de la confiance des prédictions au fil du temps
- Identifier les catégories les plus problématiques (faux positifs)
- Détecter les patterns de correction fréquents
- Générer des rapports détaillés (texte, JSON, CSV)
- Créer des visualisations graphiques (timeline, distributions)
- Calculer des métriques de précision et taux d'erreur

Le système de catégorisation utilise du machine learning pour prédire automatiquement
la catégorie financière d'une transaction bancaire. Ce script mesure l'efficacité
en analysant les corrections manuelles apportées par les utilisateurs.

Usage:
    # Rapport textuel dans la console
    python scripts/analyze_categorization_performance.py

    # Rapport JSON pour intégration
    python scripts/analyze_categorization_performance.py --format json

    # Rapports CSV pour analyse Excel
    python scripts/analyze_categorization_performance.py --format csv

    # Tous les formats dans un répertoire
    python scripts/analyze_categorization_performance.py --format all --output-dir reports/

    # Avec graphiques (nécessite matplotlib)
    python scripts/analyze_categorization_performance.py --plot --days 60

Arguments CLI:
    --format FORM    : Format de sortie (text, json, csv, all) - défaut: text
    --output-dir DIR : Répertoire de sortie pour les rapports - défaut: reports/categorization
    --plot           : Générer des graphiques (nécessite matplotlib)
    --days N         : Nombre de jours pour l'analyse temporelle (défaut: 30)

Prérequis:
    - Base de données avec table finance_categorization_feedback
    - Corrections de catégorisation enregistrées
    - Module core.bank_import.categorizer configuré
    - matplotlib (optionnel, pour graphiques)

Métriques calculées:
    1. STATISTIQUES GLOBALES:
       - Total de corrections effectuées
       - Nombre de transactions uniques corrigées
       - Nombre de catégories source (prédictions incorrectes)
       - Nombre de catégories cible (corrections)
       - Confiance moyenne des erreurs
       - Répartition par source (manuel, règle, bulk)

    2. PRÉCISION:
       - Taux de précision global (transactions correctes / total)
       - Taux d'erreur (corrections / total)

    3. CORRECTIONS FRÉQUENTES:
       - Top 10 des paires (catégorie_prédite → catégorie_correcte)
       - Confiance moyenne pour chaque paire
       - Nombre d'occurrences

    4. CATÉGORIES PROBLÉMATIQUES:
       - Catégories source de faux positifs
       - Confiance moyenne des mauvaises prédictions
       - Nombre de transactions affectées

    5. TIMELINE:
       - Évolution quotidienne des corrections
       - Tendance de la confiance au fil du temps

Fichiers de sortie:
    Format text:
    - Rapport console avec sections structurées

    Format JSON:
    - reports/categorization/report_YYYYMMDD_HHMMSS.json
      Structure complète avec toutes les métriques

    Format CSV:
    - reports/categorization/common_corrections.csv
    - reports/categorization/error_prone_categories.csv
    - reports/categorization/correction_targets.csv

    Format plot:
    - reports/categorization/timeline_YYYYMMDD.png
      Graphiques d'évolution temporelle

Exemple de sortie (format text):
    RAPPORT DE PERFORMANCE - SYSTÈME DE CATÉGORISATION
    Date: 2025-01-15 10:30:00

    1. STATISTIQUES GLOBALES
    Total corrections:              1,245
    Transactions uniques corrigées: 1,180
    Confiance moyenne (erreurs):    67.8%
    Corrections manuelles:          1,120
    Corrections via règles:         95
    Corrections en masse:           30

    2. MÉTRIQUES DE PRÉCISION
    Total transactions catégorisées: 15,420
    Total corrections:               1,245
    Précision estimée:               91.9%
    Taux d'erreur estimé:            8.1%

    3. CORRECTIONS LES PLUS FRÉQUENTES
    Prédite                  →  Correcte                 Count    Conf.
    TRANSFERT_INTERNE        →  LOYER                    45       72.5%
    ACHAT_ALIMENTAIRE        →  RESTAURANT               38       65.2%

Notes:
    - La précision est calculée de manière conservative
    - Chaque correction = 1 erreur (peut sous-estimer si transaction corrigée plusieurs fois)
    - Les graphiques nécessitent matplotlib (`pip install matplotlib`)
    - Le mode --days permet d'analyser des périodes variables
    - Utile pour monitoring continu et amélioration du modèle ML
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from core.bank_import.categorizer import get_feedback_stats, get_common_corrections
from core.data_repository import query_df
from sqlalchemy import text


def get_feedback_timeline(days: int = 30):
    """Get feedback statistics over time."""
    sql = text("""
        WITH daily_stats AS (
            SELECT
                DATE(created_at) as date,
                COUNT(*) as total_corrections,
                COUNT(DISTINCT transaction_id) as unique_transactions,
                AVG(confidence_score) as avg_confidence,
                COUNT(CASE WHEN correction_source = 'manual' THEN 1 END) as manual,
                COUNT(CASE WHEN correction_source = 'rule' THEN 1 END) as rule,
                COUNT(CASE WHEN correction_source = 'bulk_action' THEN 1 END) as bulk
            FROM finance_categorization_feedback
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        )
        SELECT * FROM daily_stats
    """)

    return query_df(sql, {"days": days})


def get_category_error_rates():
    """Get error rates by category."""
    sql = text("""
        SELECT
            fc.code,
            fc.name,
            COUNT(*) as times_corrected_from,
            AVG(cf.confidence_score) as avg_wrong_confidence,
            COUNT(DISTINCT cf.transaction_id) as unique_transactions
        FROM finance_categorization_feedback cf
        JOIN finance_categories fc ON fc.id = cf.predicted_category_id
        GROUP BY fc.code, fc.name
        ORDER BY COUNT(*) DESC
        LIMIT 20
    """)

    return query_df(sql, {})


def get_category_correction_targets():
    """Get categories that are most commonly corrected to."""
    sql = text("""
        SELECT
            fc.code,
            fc.name,
            COUNT(*) as times_corrected_to,
            COUNT(DISTINCT cf.transaction_id) as unique_transactions
        FROM finance_categorization_feedback cf
        JOIN finance_categories fc ON fc.id = cf.actual_category_id
        GROUP BY fc.code, fc.name
        ORDER BY COUNT(*) DESC
        LIMIT 20
    """)

    return query_df(sql, {})


def calculate_accuracy_metrics():
    """Calculate accuracy metrics."""
    # Get total transactions categorized
    sql_total = text("""
        SELECT COUNT(*) as total
        FROM finance_transactions
        WHERE category_id IS NOT NULL
    """)
    total_df = query_df(sql_total, {})
    total_categorized = int(total_df.iloc[0]["total"]) if not total_df.empty else 0

    # Get total corrections
    stats = get_feedback_stats()
    total_corrections = stats.get("total_corrections", 0)

    # Calculate accuracy (assuming each correction = 1 error)
    if total_categorized > 0:
        accuracy = (total_categorized - total_corrections) / total_categorized
    else:
        accuracy = 0.0

    return {
        "total_categorized": total_categorized,
        "total_corrections": total_corrections,
        "accuracy": accuracy,
        "error_rate": 1.0 - accuracy,
    }


def generate_text_report():
    """Generate a text report."""
    print("=" * 80)
    print("RAPPORT DE PERFORMANCE - SYSTÈME DE CATÉGORISATION")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Global stats
    print("1. STATISTIQUES GLOBALES")
    print("-" * 80)
    stats = get_feedback_stats()
    print(f"  Total corrections:              {stats['total_corrections']:,}")
    print(f"  Transactions uniques corrigées: {stats['unique_transactions']:,}")
    print(f"  Catégories corrigées (from):    {stats['categories_corrected_from']}")
    print(f"  Catégories corrigées (to):      {stats['categories_corrected_to']}")
    if stats['avg_wrong_confidence']:
        print(f"  Confiance moyenne (erreurs):    {stats['avg_wrong_confidence']:.2%}")
    print()
    print(f"  Corrections manuelles:          {stats['manual_corrections']:,}")
    print(f"  Corrections via règles:         {stats['rule_corrections']:,}")
    print(f"  Corrections en masse:           {stats['bulk_corrections']:,}")
    print()

    # Accuracy metrics
    print("2. MÉTRIQUES DE PRÉCISION")
    print("-" * 80)
    accuracy = calculate_accuracy_metrics()
    print(f"  Total transactions catégorisées: {accuracy['total_categorized']:,}")
    print(f"  Total corrections:               {accuracy['total_corrections']:,}")
    print(f"  Précision estimée:               {accuracy['accuracy']:.2%}")
    print(f"  Taux d'erreur estimé:            {accuracy['error_rate']:.2%}")
    print()

    # Common corrections
    print("3. CORRECTIONS LES PLUS FRÉQUENTES")
    print("-" * 80)
    corrections = get_common_corrections(limit=10)
    if corrections:
        print(f"  {'Prédite':<25} {'→':<3} {'Correcte':<25} {'Count':<8} {'Conf.':<8}")
        print("  " + "-" * 70)
        for c in corrections:
            pred = c['predicted_name'] or 'N/A'
            actual = c['actual_name']
            count = c['correction_count']
            conf = f"{c['avg_confidence']:.1%}" if c['avg_confidence'] else 'N/A'
            print(f"  {pred:<25} → {actual:<25} {count:<8} {conf:<8}")
    else:
        print("  Aucune correction enregistrée.")
    print()

    # Error-prone categories
    print("4. CATÉGORIES LES PLUS PROBLÉMATIQUES")
    print("-" * 80)
    error_rates = get_category_error_rates()
    if not error_rates.empty:
        print(f"  {'Catégorie':<30} {'Corrections':<12} {'Confiance':<12}")
        print("  " + "-" * 54)
        for _, row in error_rates.head(10).iterrows():
            name = row['name']
            count = int(row['times_corrected_from'])
            conf = f"{row['avg_wrong_confidence']:.1%}" if row['avg_wrong_confidence'] else 'N/A'
            print(f"  {name:<30} {count:<12} {conf:<12}")
    else:
        print("  Aucune donnée disponible.")
    print()

    # Correction targets
    print("5. CATÉGORIES CIBLES DE CORRECTION")
    print("-" * 80)
    targets = get_category_correction_targets()
    if not targets.empty:
        print(f"  {'Catégorie':<35} {'Fois corrigé vers':<20}")
        print("  " + "-" * 55)
        for _, row in targets.head(10).iterrows():
            name = row['name']
            count = int(row['times_corrected_to'])
            print(f"  {name:<35} {count:<20}")
    else:
        print("  Aucune donnée disponible.")
    print()

    print("=" * 80)
    print("FIN DU RAPPORT")
    print("=" * 80)


def generate_json_report(output_file: Path):
    """Generate a JSON report."""
    import json

    report = {
        "generated_at": datetime.now().isoformat(),
        "global_stats": get_feedback_stats(),
        "accuracy_metrics": calculate_accuracy_metrics(),
        "common_corrections": get_common_corrections(limit=20),
        "error_prone_categories": get_category_error_rates().to_dict(orient="records"),
        "correction_targets": get_category_correction_targets().to_dict(orient="records"),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"✓ Rapport JSON généré: {output_file}")


def generate_csv_reports(output_dir: Path):
    """Generate CSV reports."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Common corrections
    corrections = get_common_corrections(limit=100)
    if corrections:
        import pandas as pd
        df = pd.DataFrame(corrections)
        csv_file = output_dir / "common_corrections.csv"
        df.to_csv(csv_file, index=False)
        print(f"✓ Rapport CSV généré: {csv_file}")

    # Error-prone categories
    error_rates = get_category_error_rates()
    if not error_rates.empty:
        csv_file = output_dir / "error_prone_categories.csv"
        error_rates.to_csv(csv_file, index=False)
        print(f"✓ Rapport CSV généré: {csv_file}")

    # Correction targets
    targets = get_category_correction_targets()
    if not targets.empty:
        csv_file = output_dir / "correction_targets.csv"
        targets.to_csv(csv_file, index=False)
        print(f"✓ Rapport CSV généré: {csv_file}")


def plot_feedback_timeline(output_file: Path, days: int = 30):
    """Generate timeline chart."""
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError:
        print("⚠ matplotlib non installé. Installer avec: pip install matplotlib")
        return

    df = get_feedback_timeline(days=days)

    if df.empty:
        print("⚠ Aucune donnée disponible pour le graphique.")
        return

    # Create figure with subplots
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # Plot 1: Corrections over time
    ax1 = axes[0]
    ax1.plot(df['date'], df['total_corrections'], marker='o', label='Total Corrections')
    ax1.set_title('Corrections de Catégories au Fil du Temps', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Nombre de Corrections')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Confidence over time
    ax2 = axes[1]
    ax2.plot(df['date'], df['avg_confidence'] * 100, marker='s', color='orange', label='Confiance Moyenne')
    ax2.set_title('Confiance Moyenne des Prédictions Incorrectes', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Confiance (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"✓ Graphique généré: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyser la performance du système de catégorisation"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv", "all"],
        default="text",
        help="Format de sortie (défaut: text)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/categorization"),
        help="Dossier de sortie pour les rapports",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Générer des graphiques (nécessite matplotlib)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Nombre de jours pour l'analyse temporelle (défaut: 30)",
    )

    args = parser.parse_args()

    # Generate reports based on format
    if args.format in ["text", "all"]:
        generate_text_report()

    if args.format in ["json", "all"]:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_file = args.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generate_json_report(json_file)

    if args.format in ["csv", "all"]:
        generate_csv_reports(args.output_dir)

    if args.plot:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        plot_file = args.output_dir / f"timeline_{datetime.now().strftime('%Y%m%d')}.png"
        plot_feedback_timeline(plot_file, days=args.days)


if __name__ == "__main__":
    main()
