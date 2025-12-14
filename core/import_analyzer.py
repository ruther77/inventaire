"""Analyseur de qualité des imports (factures et relevés bancaires).

Ce module fournit des hooks d'analyse pour chaque parseur afin de :
- Calculer le taux de lignes avec montants/quantités non nuls
- Détecter les anomalies (valeurs aberrantes, zéros)
- Mesurer la couverture des champs (libellé, dates, montants)
- Générer des rapports de qualité par fichier
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd


@dataclass
class FieldCoverage:
    """Couverture d'un champ dans les données importées."""
    field_name: str
    total_rows: int = 0
    non_null_count: int = 0
    non_zero_count: int = 0

    @property
    def coverage_rate(self) -> float:
        return self.non_null_count / max(self.total_rows, 1)

    @property
    def non_zero_rate(self) -> float:
        return self.non_zero_count / max(self.total_rows, 1)


@dataclass
class NumericStats:
    """Statistiques pour un champ numérique."""
    field_name: str
    count: int = 0
    min_value: float | None = None
    max_value: float | None = None
    median_value: float | None = None
    mean_value: float | None = None
    zero_count: int = 0
    outlier_count: int = 0
    outliers: list[dict] = field(default_factory=list)


@dataclass
class ImportAnalysisReport:
    """Rapport d'analyse d'un import."""
    source_file: str
    source_type: str  # "invoice" | "bank_statement"
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())

    # Métriques générales
    total_rows: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0

    # Couverture des champs
    field_coverage: dict[str, dict] = field(default_factory=dict)

    # Stats numériques
    numeric_stats: dict[str, dict] = field(default_factory=dict)

    # Anomalies détectées
    anomalies: list[dict] = field(default_factory=list)

    # Catégorisation (pour relevés bancaires)
    categorization_rate: float = 0.0
    uncategorized_labels: list[str] = field(default_factory=list)
    category_distribution: dict[str, int] = field(default_factory=dict)

    # Flags de qualité
    quality_flags: list[str] = field(default_factory=list)
    quality_score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ImportAnalyzer:
    """Analyseur de qualité pour les imports."""

    # Seuils pour détection d'anomalies
    OUTLIER_THRESHOLD = 3.0  # Écarts-types
    MIN_AMOUNT_THRESHOLD = 0.01
    MAX_AMOUNT_THRESHOLD = 100000.0

    def __init__(self):
        self.reports: list[ImportAnalysisReport] = []

    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        source_file: str,
        source_type: str = "invoice",
        quantity_columns: Sequence[str] | None = None,
        amount_columns: Sequence[str] | None = None,
    ) -> ImportAnalysisReport:
        """Analyse un DataFrame et génère un rapport de qualité."""

        report = ImportAnalysisReport(
            source_file=source_file,
            source_type=source_type,
            total_rows=len(df),
        )

        if df.empty:
            report.quality_flags.append("EMPTY_FILE")
            report.quality_score = 0.0
            return report

        # Colonnes par défaut
        if quantity_columns is None:
            quantity_columns = [
                "quantite", "quantite_recue", "qte_init", "qte", "qty",
                "quantity", "nb", "nombre"
            ]
        if amount_columns is None:
            amount_columns = [
                "prix_achat", "prix_vente", "montant_ht", "montant_ttc",
                "prix_ht", "prix_ttc", "amount", "montant", "unit_cost",
                "total_ht", "total_ttc"
            ]

        # Analyse de couverture des champs
        for col in df.columns:
            coverage = self._analyze_field_coverage(df, col)
            report.field_coverage[col] = {
                "total": coverage.total_rows,
                "non_null": coverage.non_null_count,
                "non_zero": coverage.non_zero_count,
                "coverage_rate": round(coverage.coverage_rate, 4),
                "non_zero_rate": round(coverage.non_zero_rate, 4),
            }

        # Stats numériques pour quantités
        for col in quantity_columns:
            if col in df.columns:
                stats = self._analyze_numeric_field(df, col, "quantity")
                if stats.count > 0:
                    report.numeric_stats[f"qty_{col}"] = {
                        "count": stats.count,
                        "min": stats.min_value,
                        "max": stats.max_value,
                        "median": stats.median_value,
                        "mean": round(stats.mean_value, 4) if stats.mean_value else None,
                        "zero_count": stats.zero_count,
                        "outlier_count": stats.outlier_count,
                    }
                    report.anomalies.extend(stats.outliers)

        # Stats numériques pour montants
        for col in amount_columns:
            if col in df.columns:
                stats = self._analyze_numeric_field(df, col, "amount")
                if stats.count > 0:
                    report.numeric_stats[f"amt_{col}"] = {
                        "count": stats.count,
                        "min": stats.min_value,
                        "max": stats.max_value,
                        "median": stats.median_value,
                        "mean": round(stats.mean_value, 4) if stats.mean_value else None,
                        "zero_count": stats.zero_count,
                        "outlier_count": stats.outlier_count,
                    }
                    report.anomalies.extend(stats.outliers)

        # Calculer les lignes valides (avec au moins une quantité ou montant non nul)
        valid_mask = pd.Series([False] * len(df))
        for col in list(quantity_columns) + list(amount_columns):
            if col in df.columns:
                numeric_col = pd.to_numeric(df[col], errors="coerce")
                valid_mask |= (numeric_col.notna() & (numeric_col != 0))

        report.valid_rows = int(valid_mask.sum())
        report.rejected_rows = report.total_rows - report.valid_rows

        # Flags de qualité
        valid_rate = report.valid_rows / max(report.total_rows, 1)
        if valid_rate < 0.5:
            report.quality_flags.append("LOW_VALID_RATE")
        if valid_rate < 0.8:
            report.quality_flags.append("MODERATE_VALID_RATE")

        if len(report.anomalies) > report.total_rows * 0.1:
            report.quality_flags.append("HIGH_ANOMALY_RATE")

        # Score de qualité (0-100)
        report.quality_score = self._calculate_quality_score(report)

        self.reports.append(report)
        return report

    def analyze_bank_transactions(
        self,
        df: pd.DataFrame,
        source_file: str,
        categorizer_func=None,
    ) -> ImportAnalysisReport:
        """Analyse des transactions bancaires avec catégorisation."""

        report = self.analyze_dataframe(
            df, source_file, source_type="bank_statement",
            amount_columns=["montant", "amount", "debit", "credit"],
        )

        # Analyse de catégorisation
        if categorizer_func and "libelle_banque" in df.columns:
            categorized = 0
            uncategorized = []
            category_counts: dict[str, int] = {}

            for _, row in df.iterrows():
                libelle = str(row.get("libelle_banque", ""))
                category = categorizer_func(libelle)

                if category:
                    categorized += 1
                    category_counts[category] = category_counts.get(category, 0) + 1
                else:
                    if libelle and libelle not in uncategorized[:50]:
                        uncategorized.append(libelle[:100])

            report.categorization_rate = categorized / max(len(df), 1)
            report.uncategorized_labels = uncategorized[:20]
            report.category_distribution = category_counts

            if report.categorization_rate < 0.8:
                report.quality_flags.append("LOW_CATEGORIZATION_RATE")

        return report

    def _analyze_field_coverage(self, df: pd.DataFrame, column: str) -> FieldCoverage:
        """Analyse la couverture d'un champ."""
        coverage = FieldCoverage(field_name=column, total_rows=len(df))

        if column not in df.columns:
            return coverage

        series = df[column]
        coverage.non_null_count = int(series.notna().sum())

        # Vérifier les non-zéros (pour les numériques)
        try:
            numeric = pd.to_numeric(series, errors="coerce")
            coverage.non_zero_count = int((numeric.notna() & (numeric != 0)).sum())
        except Exception:
            # Pour les strings, non-vide = non-zéro
            coverage.non_zero_count = int((series.notna() & (series != "")).sum())

        return coverage

    def _analyze_numeric_field(
        self, df: pd.DataFrame, column: str, field_type: str
    ) -> NumericStats:
        """Analyse un champ numérique."""
        stats = NumericStats(field_name=column)

        if column not in df.columns:
            return stats

        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            return stats

        stats.count = len(series)
        stats.min_value = float(series.min())
        stats.max_value = float(series.max())
        stats.median_value = float(series.median())
        stats.mean_value = float(series.mean())
        stats.zero_count = int((series == 0).sum())

        # Détection d'outliers (méthode IQR)
        if len(series) > 10:
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers_mask = (series < lower_bound) | (series > upper_bound)
            stats.outlier_count = int(outliers_mask.sum())

            # Capturer quelques exemples d'outliers
            outlier_indices = series[outliers_mask].head(5).index.tolist()
            for idx in outlier_indices:
                stats.outliers.append({
                    "row": int(idx),
                    "field": column,
                    "value": float(series.loc[idx]),
                    "type": "outlier",
                    "field_type": field_type,
                })

        # Détecter les valeurs aberrantes absolues
        if field_type == "amount":
            extreme_mask = (series.abs() > self.MAX_AMOUNT_THRESHOLD)
            for idx in series[extreme_mask].head(3).index:
                stats.outliers.append({
                    "row": int(idx),
                    "field": column,
                    "value": float(series.loc[idx]),
                    "type": "extreme_value",
                    "field_type": field_type,
                })

        return stats

    def _calculate_quality_score(self, report: ImportAnalysisReport) -> float:
        """Calcule un score de qualité global (0-100)."""
        score = 100.0

        # Pénalité pour taux de lignes valides faible
        valid_rate = report.valid_rows / max(report.total_rows, 1)
        if valid_rate < 1.0:
            score -= (1.0 - valid_rate) * 30

        # Pénalité pour anomalies
        anomaly_rate = len(report.anomalies) / max(report.total_rows, 1)
        score -= min(anomaly_rate * 100, 20)

        # Pénalité pour flags
        score -= len(report.quality_flags) * 5

        # Bonus pour bonne couverture des champs critiques
        critical_fields = ["montant", "quantite", "prix_achat", "libelle"]
        for field in critical_fields:
            if field in report.field_coverage:
                coverage = report.field_coverage[field].get("coverage_rate", 0)
                if coverage > 0.9:
                    score += 2

        return max(0, min(100, round(score, 1)))

    def generate_summary_report(self) -> dict:
        """Génère un rapport de synthèse de tous les imports analysés."""
        if not self.reports:
            return {"total_files": 0, "reports": []}

        return {
            "total_files": len(self.reports),
            "total_rows": sum(r.total_rows for r in self.reports),
            "total_valid": sum(r.valid_rows for r in self.reports),
            "total_rejected": sum(r.rejected_rows for r in self.reports),
            "average_quality_score": round(
                sum(r.quality_score for r in self.reports) / len(self.reports), 1
            ),
            "files_with_issues": sum(1 for r in self.reports if r.quality_flags),
            "reports": [r.to_dict() for r in self.reports],
        }

    def save_report(self, report: ImportAnalysisReport, output_path: str | Path) -> None:
        """Sauvegarde un rapport en JSON."""
        path = Path(output_path)
        path.write_text(report.to_json())

    def save_summary_csv(self, output_path: str | Path) -> None:
        """Sauvegarde un résumé en CSV."""
        if not self.reports:
            return

        rows = []
        for r in self.reports:
            rows.append({
                "source_file": r.source_file,
                "source_type": r.source_type,
                "total_rows": r.total_rows,
                "valid_rows": r.valid_rows,
                "rejected_rows": r.rejected_rows,
                "quality_score": r.quality_score,
                "flags": ";".join(r.quality_flags),
                "anomaly_count": len(r.anomalies),
            })

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)


def analyze_invoice_import(
    df: pd.DataFrame,
    source_file: str,
) -> ImportAnalysisReport:
    """Fonction helper pour analyser un import de facture."""
    analyzer = ImportAnalyzer()
    return analyzer.analyze_dataframe(
        df,
        source_file,
        source_type="invoice",
        quantity_columns=[
            "quantite", "quantite_recue", "qte_init", "qte", "qty",
            "quantity", "nb", "nombre", "pieces"
        ],
        amount_columns=[
            "prix_achat", "prix_vente", "montant_ht", "montant_ttc",
            "prix_ht", "prix_ttc", "amount", "montant", "unit_cost",
            "total_ht", "total_ttc", "pu_ht", "pu"
        ],
    )


def analyze_bank_import(
    df: pd.DataFrame,
    source_file: str,
    categorizer_func=None,
) -> ImportAnalysisReport:
    """Fonction helper pour analyser un import bancaire."""
    analyzer = ImportAnalyzer()
    return analyzer.analyze_bank_transactions(df, source_file, categorizer_func)


__all__ = [
    "ImportAnalyzer",
    "ImportAnalysisReport",
    "analyze_invoice_import",
    "analyze_bank_import",
]
