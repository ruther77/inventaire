"""Recurring expense detection and anomaly flags."""  # Docstring décrivant le module finance insights

from __future__ import annotations  # Active les annotations différées

import json  # Sérialisation pour la colonne metadata
from dataclasses import dataclass  # Déclaration de structures simples
from decimal import Decimal  # Type Decimal pour précision
from typing import Any  # Typage générique

from sqlalchemy import text  # Construction de requêtes SQL textuelles

from core.data_repository import get_engine, query_df  # Accès base de données


@dataclass
class RefreshSummary:
    rows: int  # Nombre de lignes traitées


def _slug(text_value: str) -> str:
    return "".join(ch if ch.isalnum() else " " for ch in (text_value or "").lower()).strip()  # Normalise un libellé


def refresh_recurring_expenses(tenant_id: int, *, min_occurrences: int = 3) -> dict[str, Any]:
    """Analyse les écritures bancaires pour détecter les charges récurrentes."""  # Docstring récurrences

    min_occ = max(1, min_occurrences)  # Garde une borne basse de 1
    base_sql = """
        WITH base AS (
            SELECT
                id,
                tenant_id,
                account,
                categorie,
                date,
                montant,
                libelle,
                lower(regexp_replace(libelle, '[^a-z0-9]+', ' ', 'g')) AS normalized_label,
                date_trunc('month', date) AS month_bucket
            FROM restaurant_bank_statements
            WHERE tenant_id = :tenant_id
              AND montant IS NOT NULL
              AND montant <> 0
              AND type ILIKE 'sortie'
        )
        SELECT
            normalized_label,
            MIN(libelle) FILTER (WHERE libelle IS NOT NULL AND libelle <> '') AS sample_label,
            account,
            categorie,
            COUNT(*) AS occurrences,
            COUNT(DISTINCT month_bucket) AS distinct_months,
            AVG(montant) AS avg_amount,
            STDDEV_POP(montant) AS std_amount,
            MIN(date) AS first_date,
            MAX(date) AS last_date
        FROM base
        GROUP BY normalized_label, account, categorie
        HAVING COUNT(*) >= :min_occ
    """  # Requête pour calculer les occurrences par libellé normalisé

    engine = get_engine()  # Récupère le moteur SQL
    rows = []  # Stocke les lignes retournées
    with engine.begin() as conn:  # Transaction lecture/écriture
        rows = conn.execute(
            text(base_sql),
            {"tenant_id": tenant_id, "min_occ": min_occ},
        ).fetchall()  # Exécute la requête de détection

        conn.execute(
            text("DELETE FROM finance_recurring_expenses WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )  # Réinitialise la table pour le tenant

        for row in rows:  # Parcourt chaque libellé trouvé
            occurrences = int(row.occurrences or 0)  # Nombre d'occurrences
            months = int(row.distinct_months or 0) or 1  # Nombre de mois distincts
            ratio = occurrences / months if months else occurrences  # Ratio occurrences/mois
            if occurrences >= 10 and ratio >= 0.9:  # Détection haute fréquence
                periodicity = "monthly"  # Mensuel
            elif ratio >= 0.6:  # Assez fréquent
                periodicity = "frequent"  # Fréquent
            else:  # Faible régularité
                periodicity = "irregular"  # Irrégulier

            metadata = {
                "distinct_months": months,
                "first_date": str(row.first_date) if row.first_date else None,
                "last_date": str(row.last_date) if row.last_date else None,
            }  # Métadonnées pour audit

            conn.execute(
                text(
                    """
                    INSERT INTO finance_recurring_expenses (
                        tenant_id,
                        normalized_label,
                        sample_label,
                        account,
                        category,
                        periodicity,
                        occurrences,
                        avg_amount,
                        std_amount,
                        first_date,
                        last_date,
                        metadata
                    )
                    VALUES (
                        :tenant_id,
                        :normalized_label,
                        :sample_label,
                        :account,
                        :category,
                        :periodicity,
                        :occurrences,
                        :avg_amount,
                        :std_amount,
                        :first_date,
                        :last_date,
                        CAST(:metadata AS JSONB)
                    )
                    ON CONFLICT (tenant_id, normalized_label, account) DO UPDATE
                    SET periodicity = EXCLUDED.periodicity,
                        occurrences = EXCLUDED.occurrences,
                        avg_amount = EXCLUDED.avg_amount,
                        std_amount = EXCLUDED.std_amount,
                        first_date = EXCLUDED.first_date,
                        last_date = EXCLUDED.last_date,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "normalized_label": row.normalized_label or _slug(row.sample_label or ""),
                    "sample_label": row.sample_label or row.normalized_label or "Inconnu",
                    "account": row.account,
                    "category": row.categorie,
                    "periodicity": periodicity,
                    "occurrences": occurrences,
                    "avg_amount": row.avg_amount,
                    "std_amount": row.std_amount,
                    "first_date": row.first_date,
                    "last_date": row.last_date,
                    "metadata": json.dumps(metadata),
                },
            )  # Upsert des charges récurrentes

    return {"recurring_expenses": len(rows)}  # Résumé des lignes traitées


def refresh_anomaly_flags(
    tenant_id: int,
    *,
    zscore_threshold: float = 2.5,
    min_occurrences: int = 3,
) -> dict[str, Any]:
    """Détecte les écritures suspectes (montant hors bande)."""  # Docstring anomalies

    threshold = max(1.0, zscore_threshold)  # Garde un seuil minimal
    engine = get_engine()  # Moteur SQL
    with engine.begin() as conn:  # Transaction
        stats = conn.execute(
            text(
                """
                WITH base AS (
                    SELECT
                        id,
                        tenant_id,
                        account,
                        categorie,
                        date,
                        montant,
                        libelle,
                        lower(regexp_replace(libelle, '[^a-z0-9]+', ' ', 'g')) AS normalized_label
                    FROM restaurant_bank_statements
                    WHERE tenant_id = :tenant_id
                      AND montant IS NOT NULL
                      AND montant <> 0
                )
                SELECT
                    b.id AS statement_id,
                    b.date,
                    b.libelle,
                    b.montant,
                    s.avg_amount,
                    s.std_amount,
                    b.account,
                    b.categorie,
                    b.normalized_label
                FROM base b
                JOIN (
                    SELECT
                        normalized_label,
                        account,
                        COUNT(*) AS occurrences,
                        AVG(montant) AS avg_amount,
                        STDDEV_POP(montant) AS std_amount
                    FROM base
                    GROUP BY normalized_label, account
                    HAVING COUNT(*) >= :min_occ AND STDDEV_POP(montant) IS NOT NULL AND STDDEV_POP(montant) > 0
                ) s ON s.normalized_label = b.normalized_label AND COALESCE(s.account, '') = COALESCE(b.account, '')
                WHERE ABS(b.montant - s.avg_amount) >= s.std_amount * :threshold
                """
            ),
            {"tenant_id": tenant_id, "min_occ": max(2, min_occurrences), "threshold": threshold},
        ).fetchall()  # Récupère les écritures hors bande

        conn.execute(
            text("DELETE FROM finance_anomaly_flags WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )  # Vide la table avant réinsertion

        inserted = 0  # Compteur d'insertions
        for row in stats:  # Parcourt les anomalies détectées
            deviation = abs((row.montant or 0) - (row.avg_amount or 0))  # Écart absolu
            std_amount = row.std_amount or 0  # Écart type
            severity = "critical" if std_amount and (deviation / std_amount) >= threshold * 1.5 else "warning"  # Sévérité
            score = deviation / std_amount if std_amount else 0  # Score normalisé
            message = (
                f"{row.libelle or row.normalized_label}: montant {float(row.montant or 0):.2f} € "
                f"vs moyenne {float(row.avg_amount or 0):.2f} €"
            )  # Message explicatif
            conn.execute(
                text(
                    """
                    INSERT INTO finance_anomaly_flags (
                        tenant_id,
                        bank_statement_id,
                        rule,
                        severity,
                        message,
                        score,
                        amount,
                        expected_amount
                    )
                    VALUES (
                        :tenant_id,
                        :statement_id,
                        'amount_deviation',
                        :severity,
                        :message,
                        :score,
                        :amount,
                        :expected_amount
                    )
                    ON CONFLICT (tenant_id, bank_statement_id, rule) DO UPDATE
                    SET severity = EXCLUDED.severity,
                        message = EXCLUDED.message,
                        score = EXCLUDED.score,
                        amount = EXCLUDED.amount,
                        expected_amount = EXCLUDED.expected_amount,
                        created_at = NOW()
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "statement_id": row.statement_id,
                    "severity": severity,
                    "message": message,
                    "score": float(round(score, 4)),
                    "amount": row.montant,
                    "expected_amount": row.avg_amount,
                },
            )  # Upsert de l'anomalie
            inserted += 1  # Incrémente le compteur

    return {"anomalies": inserted}  # Résumé des anomalies créées


def list_recurring_expenses(tenant_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT
            id,
            normalized_label,
            sample_label,
            account,
            category,
            periodicity,
            occurrences,
            avg_amount,
            std_amount,
            first_date,
            last_date,
            metadata
        FROM finance_recurring_expenses
        WHERE tenant_id = :tenant_id
        ORDER BY occurrences DESC, avg_amount DESC NULLS LAST
    """  # Requête listant les charges récurrentes
    df = query_df(sql, params={"tenant_id": tenant_id})  # Exécute la requête
    if df.empty:  # Aucun résultat
        return []  # Retourne une liste vide
    return df.to_dict("records")  # Convertit en liste de dicts


def list_anomaly_flags(tenant_id: int, severity: str | None = None) -> list[dict[str, Any]]:
    filters = ["f.tenant_id = :tenant_id"]  # Filtre obligatoire tenant
    params: dict[str, Any] = {"tenant_id": tenant_id}  # Paramètres de base
    if severity:  # Filtre optionnel sur la sévérité
        filters.append("f.severity = :severity")  # Ajoute le prédicat
        params["severity"] = severity  # Ajoute le paramètre
    where_clause = " AND ".join(filters)  # Construit la clause WHERE
    sql = f"""
        SELECT
            f.id,
            f.rule,
            f.severity,
            f.message,
            f.score,
            f.amount,
            f.expected_amount,
            s.id AS statement_id,
            s.date AS statement_date,
            s.libelle AS statement_label,
            s.account AS statement_account,
            s.categorie AS statement_category
        FROM finance_anomaly_flags f
        JOIN restaurant_bank_statements s ON s.id = f.bank_statement_id
        WHERE {where_clause}
        ORDER BY f.created_at DESC
    """  # Requête listant les anomalies
    df = query_df(sql, params=params)  # Exécute la requête
    if df.empty:  # Aucun résultat
        return []  # Retourne une liste vide
    return df.to_dict("records")  # Convertit en dicts
