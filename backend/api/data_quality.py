from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df
from sqlalchemy import text

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


@router.get("/categorization/coverage")
def categorization_coverage(
    days_back: int = Query(default=90, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    """Analyse la couverture de catégorisation des transactions bancaires.

    Utilise le KeywordAnalyzer pour mesurer :
    - Taux de transactions catégorisées
    - Distribution par catégorie
    - Libellés non mappés (pour améliorer les règles)
    """
    from backend.services.parsers.keyword_analyzer import KeywordAnalyzer, CATEGORIES

    entity_id = 2 if tenant.id == 4 else tenant.id

    # Récupérer les transactions
    sql = """
        SELECT id, libelle_banque, montant, date_operation
        FROM finance_bank_statement_lines
        WHERE statement_id IN (
            SELECT id FROM finance_bank_statements WHERE account_id IN (
                SELECT id FROM finance_accounts WHERE entity_id = :entity_id
            )
        )
        AND date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
    """
    df = query_df(text(sql), {"entity_id": entity_id, "days": days_back})

    if df.empty:
        return {
            "total_transactions": 0,
            "categorized": 0,
            "uncategorized": 0,
            "coverage_rate": 0,
            "by_category": {},
            "uncategorized_labels": [],
            "suggestions": []
        }

    analyzer = KeywordAnalyzer()

    categorized = 0
    category_counts: dict[str, int] = {}
    category_amounts: dict[str, float] = {}
    uncategorized_labels: list[dict] = []

    for _, row in df.iterrows():
        libelle = str(row.get("libelle_banque", ""))
        montant = float(row.get("montant", 0) or 0)

        # Créer une transaction mock pour l'analyzer
        from backend.services.parsers.bank_statement_parsers import Transaction
        tx = Transaction(
            date=row.get("date_operation"),
            libelle=libelle,
            debit=abs(montant) if montant < 0 else None,
            credit=montant if montant > 0 else None
        )

        cat_code, keywords = analyzer.analyze_transaction(tx)

        if cat_code:
            categorized += 1
            cat_name = CATEGORIES.get(cat_code, {}).get("name", cat_code)
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
            category_amounts[cat_name] = category_amounts.get(cat_name, 0) + abs(montant)
        else:
            if libelle and len(uncategorized_labels) < 50:
                # Éviter les doublons
                if not any(u["label"] == libelle[:80] for u in uncategorized_labels):
                    uncategorized_labels.append({
                        "label": libelle[:80],
                        "amount": abs(montant),
                        "date": str(row.get("date_operation", ""))
                    })

    total = len(df)
    coverage_rate = categorized / total if total > 0 else 0

    # Générer des suggestions pour les labels non catégorisés fréquents
    suggestions = []
    label_counts: dict[str, int] = {}
    for item in uncategorized_labels:
        label = item["label"].upper()[:30]
        label_counts[label] = label_counts.get(label, 0) + 1

    for label, count in sorted(label_counts.items(), key=lambda x: -x[1])[:10]:
        if count >= 2:
            suggestions.append({
                "label": label,
                "count": count,
                "suggestion": f"Ajouter '{label}' aux mots-clés d'une catégorie"
            })

    return {
        "total_transactions": total,
        "categorized": categorized,
        "uncategorized": total - categorized,
        "coverage_rate": round(coverage_rate * 100, 1),
        "by_category": {
            cat: {
                "count": category_counts.get(cat, 0),
                "amount": round(category_amounts.get(cat, 0), 2)
            }
            for cat in sorted(category_counts.keys(), key=lambda c: -category_counts.get(c, 0))
        },
        "uncategorized_labels": uncategorized_labels[:20],
        "suggestions": suggestions
    }


@router.get("/flags")
def list_flags(
    table: str | None = Query(default=None, description="Table ciblée (ex: produits, finance_transactions)"),
    limit: int = Query(default=200, ge=1, le=2000),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    sql = """
        SELECT table_name, row_id, issue, details, created_at
        FROM data_quality_flags
        WHERE (:table IS NULL OR table_name = :table)
        ORDER BY created_at DESC
        LIMIT :limit
    """
    df = query_df(text(sql), {"table": table, "limit": limit})
    return {"items": df.where(df.notna(), None).to_dict("records") if not df.empty else []}
