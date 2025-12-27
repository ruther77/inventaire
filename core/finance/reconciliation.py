"""
Module de rapprochement bancaire automatique (Bank Reconciliation).

Ce module implémente un algorithme heuristique de rapprochement automatique entre:
- Les écritures bancaires (débits/crédits sur les comptes LCL, BNP, SumUp, etc.)
- Les documents factures fournisseurs enregistrés dans le système

OBJECTIF:
=========
Automatiser la comptabilité en associant automatiquement chaque paiement bancaire
à sa facture correspondante, réduisant ainsi le travail manuel et les erreurs.

ALGORITHME DE MATCHING:
=======================
L'algorithme utilise trois critères principaux avec pondération:

1. MONTANT (70% du score):
   - Compare le montant bancaire avec le montant TTC/HT de la facture
   - Tolère un écart paramétrable (défaut: ±2.00€)
   - Plus l'écart est faible, plus le score est élevé

2. DATE (20% du score):
   - Compare la date de l'opération bancaire avec la date de facture
   - Tolère un écart paramétrable (défaut: ±10 jours)
   - Plus les dates sont proches, plus le score est élevé

3. TEXTE (10% du score):
   - Calcule la similarité textuelle entre:
     * Le libellé bancaire et le nom du fournisseur
     * Le libellé bancaire et la référence/numéro de facture
   - Utilise l'algorithme SequenceMatcher (Ratcliff-Obershelp)

BONUS SUPPLÉMENTAIRES:
=====================
- +10% si le libellé contient explicitement le nom du fournisseur
- +10% si l'écart de montant < 10% de la tolérance (quasi-identique)
- +5% si l'écart de date ≤ 5 jours (très récent)
- +10% si le compte bancaire correspond au fournisseur

TYPES DE MATCHING:
==================
1. HEURISTIC (1→1): Un paiement = Une facture
   - Cas le plus courant
   - Association directe

2. GROUPED (N→1): Plusieurs paiements = Une facture
   - Paiements fractionnés (échelonnement)
   - Regroupe max 3 écritures sur une fenêtre temporelle
   - Somme les montants et compare au total facture

SEUILS DE DÉCISION:
===================
- Score ≥ 0.90 (auto_threshold): Match AUTO-VALIDÉ
- Score < 0.90: Match EN ATTENTE de validation manuelle

TABLES IMPLIQUÉES:
==================
- finance_bank_statement_lines: Écritures bancaires importées
- finance_invoice_documents: Documents factures fournisseurs
- finance_bank_invoice_matches: Associations créées (résultats)
- finance_reconciliation_runs: Historique des exécutions

UTILISATION TYPIQUE:
====================
    from core.finance.reconciliation import run_reconciliation_job

    result = run_reconciliation_job(
        tenant_id=1,
        amount_tolerance=2.0,      # ±2€ d'écart acceptable
        max_days_difference=10,    # ±10 jours d'écart acceptable
        auto_threshold=0.90        # Seuil d'auto-validation
    )

    print(f"Créé {result['matches_created']} associations")
    print(f"Dont {result['auto_matches']} auto-validées")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any, Iterable

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.cache import cached, CacheTTL


@dataclass
class BankStatementEntry:
    id: int  # Identifiant de l'écriture bancaire
    date: date  # Date de l'écriture
    label: str  # Libellé
    amount: Decimal  # Montant (absolu)
    account: str | None  # Compte bancaire
    category: str | None  # Catégorie bancaire


@dataclass
class InvoiceDocument:
    id: int  # Identifiant du document facture
    supplier_name: str  # Nom du fournisseur
    invoice_reference: str  # Référence de facture (unique)
    invoice_number: str | None  # Numéro de facture éventuel
    invoice_date: date  # Date de facture
    total_incl_tax: Decimal  # Total TTC
    total_excl_tax: Decimal  # Total HT


def _decimal(value: Any) -> Decimal:
    if value is None:  # Valeur absente
        return Decimal("0")  # Retourne zéro
    if isinstance(value, Decimal):  # Déjà un Decimal
        return value  # Renvoie tel quel
    return Decimal(str(value))  # Conversion via chaîne


def _load_bank_statements(conn, tenant_id: int) -> list[BankStatementEntry]:
    # Utilise les écritures normalisées finance_bank_statement_lines (import LCL/BNP/SumUp)
    rows = conn.execute(
        text(
            """
            SELECT l.id,
                   l.date_operation AS date,
                   COALESCE(l.libelle_banque, '') AS label,
                   l.montant,
                   acc.label AS account,
                   acc.entity_id::text AS categorie
            FROM finance_bank_statement_lines l
            JOIN finance_bank_statements s ON s.id = l.statement_id
            JOIN finance_accounts acc ON acc.id = l.account_id
            WHERE l.montant IS NOT NULL
              AND l.montant < 0  -- on cible les sorties (paiements fournisseurs)
              AND NOT EXISTS (
                  SELECT 1
                  FROM finance_bank_invoice_matches m
                  WHERE m.bank_statement_id = l.id
                    AND m.status IN ('pending', 'auto', 'confirmed')
              )
            ORDER BY l.date_operation ASC
            """
        )
    ).fetchall()  # Charge toutes les sorties/entrées non rapprochées (montant signé)
    return [
        BankStatementEntry(
            id=row.id,
            date=row.date,
            label=row.label or "",
            amount=_decimal(row.montant).copy_abs(),
            account=row.account,
            category=row.categorie,
        )
        for row in rows
    ]  # Transforme en objets BankStatementEntry


def _load_invoice_documents(conn, tenant_id: int) -> list[InvoiceDocument]:
    rows = conn.execute(
        text(
            """
            SELECT doc.id,
                   doc.supplier_name,
                   doc.invoice_reference,
                   doc.invoice_number,
                   doc.invoice_date,
                   doc.total_incl_tax,
                   doc.total_excl_tax
            FROM finance_invoice_documents doc
            WHERE doc.tenant_id = :tenant_id
              AND COALESCE(doc.total_incl_tax, doc.total_excl_tax) IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM finance_bank_invoice_matches m
                  WHERE m.document_id = doc.id
                    AND m.status IN ('pending', 'auto', 'confirmed')
              )
            ORDER BY doc.invoice_date ASC
            """
        ),
        {"tenant_id": tenant_id},
    ).fetchall()  # Charge les factures non rapprochées
    documents: list[InvoiceDocument] = []  # Liste résultante
    for row in rows:  # Convertit chaque ligne en InvoiceDocument
        incl = _decimal(row.total_incl_tax) if row.total_incl_tax is not None else None  # TTC éventuel
        excl = _decimal(row.total_excl_tax) if row.total_excl_tax is not None else None  # HT éventuel
        documents.append(
            InvoiceDocument(
                id=row.id,
                supplier_name=row.supplier_name or "",
                invoice_reference=row.invoice_reference,
                invoice_number=row.invoice_number,
                invoice_date=row.invoice_date,
                total_incl_tax=incl if incl is not None else excl or Decimal("0"),
                total_excl_tax=excl if excl is not None else incl or Decimal("0"),
            )
        )
    return documents  # Retourne la liste


def _similarity(a: str, b: str) -> float:
    a_clean = (a or "").lower()  # Nettoie le texte A
    b_clean = (b or "").lower()  # Nettoie le texte B
    if not a_clean or not b_clean:  # Si l'un est vide
        return 0.0  # Similarité nulle
    return SequenceMatcher(None, a_clean, b_clean).ratio()  # Ratio de similarité


def _chunk_sum(
    statements: Iterable[BankStatementEntry],
    *,
    window_days: int,
) -> list[list[BankStatementEntry]]:
    """Regroupe les écritures par fenêtres temporelles (paiements fractionnés).

    - si window_days <= 0 : on met tout dans un seul lot (couverture maximale).
    - sinon on segmente par date de départ + taille max (30 par lot).
    """
    batches: list[list[BankStatementEntry]] = []
    current: list[BankStatementEntry] = []
    max_group_size = 5000 if window_days <= 0 else 30  # lot unique si fenêtre désactivée
    for st in sorted(statements, key=lambda x: x.date):
        if not current:
            current.append(st)
            continue
        delta_days = abs((st.date - current[0].date).days)
        if window_days <= 0 or (delta_days <= window_days and len(current) < max_group_size):
            current.append(st)
        else:
            batches.append(current)
            current = [st]
    if current:
        batches.append(current)
    return batches


def _score_candidate(
    statement: BankStatementEntry,
    document: InvoiceDocument,
    *,
    amount_tolerance: Decimal,
    max_days_difference: int,
) -> dict[str, Any] | None:
    """Score un candidat facture vs écriture bancaire en combinant montant/date/texte."""
    invoice_amount = document.total_incl_tax or document.total_excl_tax  # Montant facture
    if invoice_amount is None:  # Montant absent
        return None  # Pas de score
    invoice_amount = invoice_amount.copy_abs()  # Valeur absolue
    if invoice_amount == 0:  # Montant nul
        return None  # Pas de score

    bank_amount = statement.amount.copy_abs()  # Montant bancaire absolu
    if bank_amount == 0:  # Montant nul
        return None  # Pas de score

    amount_diff = (bank_amount - invoice_amount).copy_abs()  # Écart absolu
    if amount_diff > amount_tolerance:  # Écart trop important
        return None  # Candidat rejeté

    days_diff = abs((statement.date - document.invoice_date).days)  # Écart en jours
    if days_diff > max_days_difference:  # Trop éloigné dans le temps
        return None  # Candidat rejeté

    denom = max(bank_amount, invoice_amount, amount_tolerance)  # Dénominateur pour la normalisation
    amount_score = max(Decimal("0"), Decimal("1") - (amount_diff / denom))  # Score basé sur l'écart montant
    day_score = Decimal("1") - (
        Decimal(days_diff) / Decimal(max_days_difference or 1)
    )  # Score basé sur l'écart jours
    label_score_supplier = Decimal(str(_similarity(statement.label, document.supplier_name)))  # Similarité libellé ↔ fournisseur
    label_score_ref = Decimal(str(_similarity(statement.label, document.invoice_reference)))  # Similarité libellé ↔ réf facture
    label_score_number = Decimal(str(_similarity(statement.label, document.invoice_number))) if document.invoice_number else Decimal("0")

    # Bonus : si le libellé contient explicitement le fournisseur ou la référence/numéro
    label_lower = (statement.label or "").lower()
    explicit_hit = any(
        token for token in [
            (document.supplier_name or "").lower(),
            (document.invoice_reference or "").lower(),
            (document.invoice_number or "").lower() if document.invoice_number else "",
        ]
        if token and token in label_lower
    )
    bonus = Decimal("0.1") if explicit_hit else Decimal("0")

    # Bonus compte/catégorie si aligné (ex: compte LCL/BNP/SUMUP correspond au fournisseur)
    account_lower = (statement.account or "").lower()
    supplier_lower = (document.supplier_name or "").lower()
    account_match = Decimal("0.1") if account_lower and supplier_lower and supplier_lower[:5] in account_lower else Decimal("0")

    # Pondération plus riche : montant 55%, date 15%, texte 30% réparti sur trois signaux + bonus
    text_score = (label_score_supplier + label_score_ref + label_score_number) / Decimal("3") if label_score_number else (label_score_supplier + label_score_ref) / Decimal("2")
    # Bonus fort si écart montant très faible et date proche
    if amount_diff <= amount_tolerance * Decimal("0.1"):
        bonus += Decimal("0.10")
    if days_diff <= 5:
        bonus += Decimal("0.05")

    final_score = (
        amount_score * Decimal("0.70")
        + day_score * Decimal("0.20")
        + text_score * Decimal("0.10")
        + bonus
        + account_match
    )

    return {
        "score": float(round(final_score, 4)),
        "amount_diff": float(amount_diff),
        "days_diff": days_diff,
        "bank_amount": float(bank_amount),
        "invoice_amount": float(invoice_amount),
    }  # Détails du candidat


def run_reconciliation_job(
    tenant_id: int,
    *,
    amount_tolerance: float = 2.0,
    max_days_difference: int = 10,
    auto_threshold: float = 0.9,
) -> dict[str, Any]:
    """Execute the heuristic reconciliation job and persist suggestions."""  # Docstring job principal

    amount_delta = Decimal(str(amount_tolerance))  # Tolérance sur les montants
    auto_threshold_value = max(0.0, min(auto_threshold, 1.0))  # Seuil d'acceptation auto borné à [0,1]

    engine = get_engine()  # Moteur SQL
    with engine.begin() as conn:  # Transaction
        run_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO finance_reconciliation_runs (tenant_id, status, params)
                    VALUES (:tenant_id, 'running', CAST(:params AS JSONB))
                    RETURNING id
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "params": json.dumps(
                        {
                            "amount_tolerance": amount_tolerance,
                            "max_days_difference": max_days_difference,
                            "auto_threshold": auto_threshold_value,
                        }
                    ),
                },
            ).scalar_one()
        )  # Crée un enregistrement de run et récupère l'ID

        statements = _load_bank_statements(conn, tenant_id)  # Écritures bancaires candidates
        documents = _load_invoice_documents(conn, tenant_id)  # Factures candidates

        inserted = 0  # Compteur de correspondances créées
        auto_matches = 0  # Compteur de correspondances auto
        used_documents: set[int] = set()  # Suivi des factures déjà utilisées

        # 1) Matching 1→1 classique
        for statement in statements:  # Parcourt chaque écriture bancaire
            best_candidate: dict[str, Any] | None = None  # Score du meilleur match
            best_document: InvoiceDocument | None = None  # Document correspondant

            for document in documents:  # Parcourt chaque facture
                if document.id in used_documents:  # Ignore les factures déjà utilisées
                    continue
                candidate = _score_candidate(
                    statement,
                    document,
                    amount_tolerance=amount_delta,
                    max_days_difference=max_days_difference,
                )  # Calcule un score
                if not candidate:  # Si pas de score
                    continue  # Passe au document suivant
                if best_candidate is None or candidate["score"] > best_candidate["score"]:  # Si meilleur score
                    best_candidate = candidate  # Met à jour le meilleur
                    best_document = document  # Sauvegarde le document

            if not best_candidate or not best_document:  # Aucun match trouvé
                continue  # Passe à l'écriture suivante

            status = "auto" if best_candidate["score"] >= auto_threshold_value else "pending"  # Statut selon seuil
            if status == "auto":  # Si auto-accepté
                auto_matches += 1  # Incrémente le compteur auto

            explanation = (
                f"Δ montant {best_candidate['amount_diff']:.2f} € · Δ jours {best_candidate['days_diff']} · "
                f"similarité {best_candidate['score']:.2f}"
            )  # Message d'explication
            result = conn.execute(
                text(
                    """
                    INSERT INTO finance_bank_invoice_matches (
                        tenant_id,
                        run_id,
                        bank_statement_id,
                        document_id,
                        match_type,
                        status,
                        score,
                        bank_amount,
                        invoice_amount,
                        amount_diff,
                        days_diff,
                        explanation
                    )
                    VALUES (
                        :tenant_id,
                        :run_id,
                        :bank_statement_id,
                        :document_id,
                        'heuristic',
                        :status,
                        :score,
                        :bank_amount,
                        :invoice_amount,
                        :amount_diff,
                        :days_diff,
                        :explanation
                    )
                    ON CONFLICT (bank_statement_id, document_id) DO NOTHING
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "run_id": run_id,
                    "bank_statement_id": statement.id,
                    "document_id": best_document.id,
                    "status": status,
                    "score": best_candidate["score"],
                    "bank_amount": best_candidate["bank_amount"],
                    "invoice_amount": best_candidate["invoice_amount"],
                    "amount_diff": best_candidate["amount_diff"],
                    "days_diff": best_candidate["days_diff"],
                    "explanation": explanation,
                },
            )  # Insère la correspondance
            if result.rowcount:  # Si insertion effective
                inserted += 1  # Incrémente le compteur
                used_documents.add(best_document.id)  # Marque la facture comme utilisée

        # 2) Matching groupé (paiements fractionnés) : somme d'un petit groupe d'écritures sur une fenêtre
        grouped_batches = _chunk_sum(statements, window_days=max_days_difference)
        for batch in grouped_batches:
            if len(batch) <= 1:
                continue
            if len(batch) > 3:  # peu de paiements fractionnés : on limite la taille pour précision
                continue
            total_amount = sum((st.amount.copy_abs() for st in batch), Decimal("0"))
            batch_ids = [st.id for st in batch]
            best_candidate = None
            best_document = None

            for document in documents:
                if document.id in used_documents:
                    continue
                invoice_amount = document.total_incl_tax or document.total_excl_tax
                if invoice_amount is None:
                    continue
                diff = (total_amount - invoice_amount.copy_abs()).copy_abs()
                if diff > amount_delta:
                    continue
                # Score simple pour lot : plus proche du montant et de la date de la 1ère écriture
                days_diff = abs((batch[0].date - document.invoice_date).days)
                if days_diff > max_days_difference:
                    continue
                label_score = _similarity(" ".join([st.label for st in batch]), document.supplier_name)
                denom = max(invoice_amount, total_amount, amount_delta)
                amount_score = max(Decimal("0"), Decimal("1") - (diff / denom))
                day_score = Decimal("1") - (Decimal(days_diff) / Decimal(max_days_difference or 1))
                text_score = Decimal(str(label_score))
                bonus = Decimal("0")
                if diff <= amount_delta * Decimal("0.1"):
                    bonus += Decimal("0.10")
                if days_diff <= 5:
                    bonus += Decimal("0.05")
                score = float(
                    amount_score * Decimal("0.70")
                    + day_score * Decimal("0.20")
                    + text_score * Decimal("0.10")
                    + bonus
                )
                if best_candidate is None or score > best_candidate["score"]:
                    best_candidate = {
                        "score": score,
                        "amount_diff": float(diff),
                        "days_diff": days_diff,
                        "bank_amount": float(total_amount),
                        "invoice_amount": float(invoice_amount),
                        "batch_ids": batch_ids,
                    }
                    best_document = document

            if not best_candidate or not best_document:
                continue

            status = "auto" if best_candidate["score"] >= auto_threshold_value else "pending"
            if status == "auto":
                auto_matches += 1
            explanation = (
                f"Lot {len(batch_ids)} écritures Δ montant {best_candidate['amount_diff']:.2f} € · "
                f"Δ jours {best_candidate['days_diff']} · score {best_candidate['score']:.2f}"
            )
            # on rattache le lot à la première écriture pour garder le schéma existant
            result = conn.execute(
                text(
                    """
                    INSERT INTO finance_bank_invoice_matches (
                        tenant_id,
                        run_id,
                        bank_statement_id,
                        document_id,
                        match_type,
                        status,
                        score,
                        bank_amount,
                        invoice_amount,
                        amount_diff,
                        days_diff,
                        explanation
                    )
                    VALUES (
                        :tenant_id,
                        :run_id,
                        :bank_statement_id,
                        :document_id,
                        'grouped',
                        :status,
                        :score,
                        :bank_amount,
                        :invoice_amount,
                        :amount_diff,
                        :days_diff,
                        :explanation
                    )
                    ON CONFLICT (bank_statement_id, document_id) DO NOTHING
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "run_id": run_id,
                    "bank_statement_id": batch_ids[0],
                    "document_id": best_document.id,
                    "status": status,
                    "score": best_candidate["score"],
                    "bank_amount": best_candidate["bank_amount"],
                    "invoice_amount": best_candidate["invoice_amount"],
                    "amount_diff": best_candidate["amount_diff"],
                    "days_diff": best_candidate["days_diff"],
                    "explanation": explanation,
                },
            )
            if result.rowcount:
                inserted += 1
                used_documents.add(best_document.id)

        conn.execute(
            text(
                """
                UPDATE finance_reconciliation_runs
                SET status = 'completed',
                    completed_at = NOW(),
                    stats = CAST(:stats AS JSONB)
                WHERE id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "stats": json.dumps(
                    {
                        "statements_scanned": len(statements),
                        "documents_available": len(documents),
                        "matches_created": inserted,
                        "auto_matches": auto_matches,
                    }
                ),
            },
        )  # Met à jour le run avec les statistiques

    return {
        "run_id": run_id,
        "statements_scanned": len(statements),
        "documents_available": len(documents),
        "matches_created": inserted,
        "auto_matches": auto_matches,
    }  # Résumé du run


@cached(ttl=CacheTTL.SHORT, prefix="reconciliation_matches", tenant_aware=True)
def fetch_matches(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
    """Return reconciliation matches for manual review.

    Note: Cette fonction utilise des JOINs pour éviter les requêtes N+1.
    Tous les détails (bank_statement, invoice_document) sont récupérés en une seule requête.
    """

    filters: list[str] = ["m.tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}
    if status:
        filters.append("m.status = :status")
        params["status"] = status

    where_clause = " AND ".join(filters)
    # Utilisation de JOINs pour récupérer toutes les données en une seule requête (évite N+1)
    sql = f"""
        SELECT
            m.id,
            m.status,
            m.score,
            m.match_type,
            m.bank_amount,
            m.invoice_amount,
            m.amount_diff,
            m.days_diff,
            m.explanation,
            s.id AS bank_id,
            s.date AS bank_date,
            s.libelle AS bank_label,
            s.montant AS bank_raw_amount,
            s.account AS bank_account,
            s.categorie AS bank_category,
            doc.id AS document_id,
            doc.invoice_reference,
            doc.invoice_number,
            doc.invoice_date,
            doc.total_incl_tax,
            doc.total_excl_tax,
            doc.supplier_name
        FROM finance_bank_invoice_matches m
        JOIN restaurant_bank_statements s ON s.id = m.bank_statement_id
        JOIN finance_invoice_documents doc ON doc.id = m.document_id
        WHERE {where_clause}
        ORDER BY m.created_at DESC
    """
    engine = get_engine()
    df = query_df(sql, params=params)
    if df.empty:
        return []
    return df.to_dict("records")


def update_match_status(tenant_id: int, match_id: int, *, status: str, note: str | None = None) -> dict[str, Any]:
    allowed = {"pending", "auto", "confirmed", "rejected"}  # Statuts autorisés
    if status not in allowed:  # Validation du statut
        raise ValueError(f"Statut {status} invalide.")  # Erreur explicite

    engine = get_engine()  # Moteur SQL
    with engine.begin() as conn:  # Transaction
        row = conn.execute(
            text(
                """
                UPDATE finance_bank_invoice_matches
                SET status = :status,
                    explanation = COALESCE(:note, explanation),
                    updated_at = NOW()
                WHERE id = :match_id AND tenant_id = :tenant_id
                RETURNING id
                """
            ),
            {"status": status, "note": note, "match_id": match_id, "tenant_id": tenant_id},
        ).fetchone()  # Met à jour la correspondance
        if not row:  # Si aucune ligne mise à jour
            raise ValueError("Association introuvable.")  # Erreur
    matches = fetch_matches(tenant_id, status=None)  # Recharge les correspondances
    for item in matches:  # Parcourt pour trouver la ligne ciblée
        if item["id"] == match_id:  # Si correspond
            return item  # Retourne l'élément mis à jour
    raise ValueError("Association introuvable.")  # Si non trouvée
