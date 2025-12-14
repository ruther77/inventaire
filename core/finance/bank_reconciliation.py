"""
Rapprochement bancaire automatisé v2.

Fonctionnalités:
- Matching automatique multi-critères
- Matching multi-lignes (1 facture = N prélèvements)
- Matching flou (montant approximatif)
- Reconnaissance par fournisseur, date glissante, alias
- Alertes factures non trouvées
- Scoring de confiance
- Auto-learning
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math

from sqlalchemy import text
from core.data_repository import get_engine


class MatchStatus(str, Enum):
    """Statuts de rapprochement."""
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    MANUAL = "manual"
    DISPUTED = "disputed"


class MatchType(str, Enum):
    """Types de correspondance."""
    EXACT = "exact"
    FUZZY_AMOUNT = "fuzzy_amount"
    MULTI_LINE = "multi_line"
    ALIAS = "alias"
    PATTERN = "pattern"
    LEARNED = "learned"


@dataclass
class MatchCandidate:
    """Candidat pour un rapprochement."""
    invoice_id: int
    transaction_id: int
    match_type: MatchType
    confidence: float  # 0.0 - 1.0
    amount_match: float  # Écart en %
    date_diff_days: int
    supplier_match: float  # Score de correspondance fournisseur
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconciliationResult:
    """Résultat d'un rapprochement."""
    transaction_id: int
    status: MatchStatus
    matched_invoices: List[int]
    confidence: float
    match_type: Optional[MatchType]
    amount_covered: float
    amount_remaining: float
    details: Dict[str, Any]


class BankReconciliationEngine:
    """Moteur de rapprochement bancaire avancé."""

    # Paramètres de matching
    EXACT_AMOUNT_TOLERANCE = 0.005  # 0.5%
    FUZZY_AMOUNT_TOLERANCE = 0.03  # 3%
    MAX_DATE_DIFF_DAYS = 45
    MIN_CONFIDENCE_THRESHOLD = 0.5

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._supplier_aliases: Dict[str, List[str]] = {}
        self._learned_patterns: Dict[str, str] = {}
        self._ensure_tables()
        self._load_aliases()

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS bank_reconciliation (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    transaction_id INTEGER NOT NULL,
                    invoice_id INTEGER,
                    status VARCHAR(20) NOT NULL,
                    match_type VARCHAR(30),
                    confidence FLOAT,
                    amount_covered FLOAT,
                    details JSONB DEFAULT '{}',
                    reconciled_at TIMESTAMPTZ DEFAULT NOW(),
                    reconciled_by VARCHAR(100),
                    UNIQUE(tenant_id, transaction_id, invoice_id)
                );

                CREATE INDEX IF NOT EXISTS idx_reconciliation_tenant
                    ON bank_reconciliation(tenant_id, status);
                CREATE INDEX IF NOT EXISTS idx_reconciliation_transaction
                    ON bank_reconciliation(transaction_id);
                CREATE INDEX IF NOT EXISTS idx_reconciliation_invoice
                    ON bank_reconciliation(invoice_id);

                CREATE TABLE IF NOT EXISTS supplier_aliases (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    supplier_name VARCHAR(200) NOT NULL,
                    alias VARCHAR(200) NOT NULL,
                    source VARCHAR(50), -- manual, learned
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(tenant_id, supplier_name, alias)
                );

                CREATE TABLE IF NOT EXISTS reconciliation_patterns (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    pattern VARCHAR(500) NOT NULL,
                    supplier_name VARCHAR(200),
                    category VARCHAR(100),
                    hits INTEGER DEFAULT 0,
                    accuracy FLOAT DEFAULT 1.0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(tenant_id, pattern)
                );

                CREATE TABLE IF NOT EXISTS reconciliation_alerts (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    entity_type VARCHAR(20), -- invoice, transaction
                    entity_id INTEGER,
                    message TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

    def _load_aliases(self):
        """Charge les alias fournisseurs."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT supplier_name, alias
                    FROM supplier_aliases
                    WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": self.tenant_id}
            )

            for row in result:
                supplier = row.supplier_name.lower()
                if supplier not in self._supplier_aliases:
                    self._supplier_aliases[supplier] = []
                self._supplier_aliases[supplier].append(row.alias.lower())

    def reconcile_batch(
        self,
        transaction_ids: Optional[List[int]] = None,
        auto_apply: bool = False,
        min_confidence: float = 0.7
    ) -> List[ReconciliationResult]:
        """Rapproche un lot de transactions.
        Note: Utilise finance_transactions avec entity_id.
        """
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        # Récupérer les transactions à rapprocher
        with engine.connect() as conn:
            query = """
                SELECT id, date_operation as date, CAST(amount AS NUMERIC) as montant,
                       label as libelle, direction as type, NULL as categorie
                FROM finance_transactions
                WHERE entity_id = :entity_id
                  AND direction = 'OUT'  -- Débits uniquement
            """
            params = {"entity_id": entity_id}

            if transaction_ids:
                query += " AND id = ANY(:ids)"
                params["ids"] = transaction_ids
            else:
                # Par défaut: transactions non rapprochées des 60 derniers jours
                query += """
                    AND date_operation >= NOW() - INTERVAL '60 days'
                    AND id NOT IN (
                        SELECT transaction_id FROM finance_reconciliations
                    )
                """

            query += " ORDER BY date_operation DESC LIMIT 500"

            result = conn.execute(text(query), params)
            transactions = [dict(row._mapping) for row in result]

        results = []
        for tx in transactions:
            result = self.reconcile_single(tx, auto_apply, min_confidence)
            results.append(result)

        return results

    def reconcile_single(
        self,
        transaction: Dict[str, Any],
        auto_apply: bool = False,
        min_confidence: float = 0.7
    ) -> ReconciliationResult:
        """Rapproche une seule transaction."""
        tx_id = transaction["id"]
        tx_amount = abs(float(transaction["montant"]))
        tx_date = transaction["date"]
        tx_libelle = str(transaction.get("libelle") or "").lower()

        # 1. Chercher des correspondances exactes
        candidates = self._find_candidates(tx_amount, tx_date, tx_libelle)

        if not candidates:
            # 2. Essayer le matching multi-lignes
            multi_candidates = self._find_multi_line_candidates(tx_amount, tx_date, tx_libelle)
            candidates.extend(multi_candidates)

        if not candidates:
            # Créer une alerte si montant significatif
            if tx_amount > 100:
                self._create_alert(
                    "missing_invoice",
                    "transaction",
                    tx_id,
                    f"Transaction de {tx_amount:.2f}€ sans facture correspondante"
                )

            return ReconciliationResult(
                transaction_id=tx_id,
                status=MatchStatus.UNMATCHED,
                matched_invoices=[],
                confidence=0.0,
                match_type=None,
                amount_covered=0.0,
                amount_remaining=tx_amount,
                details={"reason": "no_candidates_found"},
            )

        # Trier par confiance
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        best = candidates[0]

        # Vérifier le seuil de confiance
        if best.confidence < min_confidence:
            return ReconciliationResult(
                transaction_id=tx_id,
                status=MatchStatus.PARTIAL,
                matched_invoices=[best.invoice_id],
                confidence=best.confidence,
                match_type=best.match_type,
                amount_covered=tx_amount * (1 - best.amount_match),
                amount_remaining=tx_amount * best.amount_match,
                details={
                    "best_candidate": best.details,
                    "alternatives": [c.details for c in candidates[1:3]],
                },
            )

        # Appliquer automatiquement si demandé
        if auto_apply and best.confidence >= min_confidence:
            self._apply_reconciliation(tx_id, best)

        return ReconciliationResult(
            transaction_id=tx_id,
            status=MatchStatus.MATCHED,
            matched_invoices=[best.invoice_id],
            confidence=best.confidence,
            match_type=best.match_type,
            amount_covered=tx_amount,
            amount_remaining=0.0,
            details=best.details,
        )

    def _find_candidates(
        self,
        amount: float,
        date: datetime,
        libelle: str
    ) -> List[MatchCandidate]:
        """Trouve les factures candidates."""
        candidates = []
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        # Extraire le fournisseur potentiel du libellé
        potential_suppliers = self._extract_suppliers(libelle)

        with engine.connect() as conn:
            # Recherche par montant approximatif + date (finance_invoices_supplier)
            result = conn.execute(
                text("""
                    SELECT f.id, f.invoice_number as numero, v.name as fournisseur,
                           f.montant_ttc as total, f.date_invoice as date
                    FROM finance_invoices_supplier f
                    LEFT JOIN finance_vendors v ON v.id = f.vendor_id
                    WHERE f.entity_id = :entity_id
                      AND f.montant_ttc BETWEEN :amount_min AND :amount_max
                      AND f.date_invoice BETWEEN :date_min AND :date_max
                      AND NOT EXISTS (
                          SELECT 1 FROM finance_reconciliations fr
                          WHERE fr.invoice_id = f.id
                      )
                """),
                {
                    "entity_id": entity_id,
                    "amount_min": amount * (1 - self.FUZZY_AMOUNT_TOLERANCE),
                    "amount_max": amount * (1 + self.FUZZY_AMOUNT_TOLERANCE),
                    "date_min": date - timedelta(days=self.MAX_DATE_DIFF_DAYS),
                    "date_max": date + timedelta(days=7),  # Peut payer avant réception
                }
            )

            for row in result:
                invoice_total = float(row.total)
                amount_diff = abs(invoice_total - amount) / amount if amount > 0 else 1

                # Calculer le score de correspondance fournisseur
                supplier_score = self._calculate_supplier_match(
                    row.fournisseur,
                    potential_suppliers,
                    libelle
                )

                # Calcul de la date
                invoice_date = row.date
                if isinstance(invoice_date, str):
                    invoice_date = datetime.fromisoformat(invoice_date)
                date_diff = abs((date - invoice_date).days) if hasattr(date, '__sub__') else 0

                # Score de confiance global
                amount_score = 1 - (amount_diff / self.FUZZY_AMOUNT_TOLERANCE) if amount_diff <= self.FUZZY_AMOUNT_TOLERANCE else 0
                date_score = max(0, 1 - (date_diff / self.MAX_DATE_DIFF_DAYS))

                confidence = (
                    amount_score * 0.4 +
                    supplier_score * 0.4 +
                    date_score * 0.2
                )

                # Déterminer le type de match
                if amount_diff < self.EXACT_AMOUNT_TOLERANCE:
                    match_type = MatchType.EXACT
                    confidence = min(1.0, confidence + 0.1)  # Bonus pour match exact
                else:
                    match_type = MatchType.FUZZY_AMOUNT

                if confidence > 0.3:
                    candidates.append(MatchCandidate(
                        invoice_id=row.id,
                        transaction_id=0,  # Sera rempli plus tard
                        match_type=match_type,
                        confidence=confidence,
                        amount_match=amount_diff,
                        date_diff_days=date_diff,
                        supplier_match=supplier_score,
                        details={
                            "invoice_number": row.numero,
                            "invoice_supplier": row.fournisseur,
                            "invoice_total": invoice_total,
                            "invoice_date": invoice_date.isoformat() if hasattr(invoice_date, "isoformat") else str(invoice_date),
                            "amount_diff_pct": round(amount_diff * 100, 2),
                            "date_diff_days": date_diff,
                        },
                    ))

        return candidates

    def _find_multi_line_candidates(
        self,
        amount: float,
        date: datetime,
        libelle: str
    ) -> List[MatchCandidate]:
        """Trouve des combinaisons de factures pour le matching multi-lignes.
        Note: Utilise finance_invoices_supplier avec entity_id.
        """
        candidates = []
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        # Chercher des factures qui pourraient être combinées
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT f.id, f.invoice_number as numero, v.name as fournisseur,
                           f.montant_ttc as total, f.date_invoice as date
                    FROM finance_invoices_supplier f
                    LEFT JOIN finance_vendors v ON v.id = f.vendor_id
                    WHERE f.entity_id = :entity_id
                      AND f.montant_ttc < :amount
                      AND f.montant_ttc > :amount * 0.1
                      AND f.date_invoice BETWEEN :date_min AND :date_max
                      AND NOT EXISTS (
                          SELECT 1 FROM finance_reconciliations fr
                          WHERE fr.invoice_id = f.id
                      )
                    ORDER BY f.montant_ttc DESC
                    LIMIT 20
                """),
                {
                    "entity_id": entity_id,
                    "amount": amount,
                    "date_min": date - timedelta(days=self.MAX_DATE_DIFF_DAYS),
                    "date_max": date + timedelta(days=7),
                }
            )

            invoices = [dict(row._mapping) for row in result]

        # Essayer de trouver des combinaisons qui font le montant
        best_combination = self._find_best_combination(invoices, amount)

        if best_combination:
            total_covered = sum(float(inv["total"]) for inv in best_combination)
            amount_diff = abs(total_covered - amount) / amount if amount > 0 else 1

            if amount_diff <= self.FUZZY_AMOUNT_TOLERANCE:
                candidates.append(MatchCandidate(
                    invoice_id=best_combination[0]["id"],  # Premier de la combinaison
                    transaction_id=0,
                    match_type=MatchType.MULTI_LINE,
                    confidence=0.7 * (1 - amount_diff / self.FUZZY_AMOUNT_TOLERANCE),
                    amount_match=amount_diff,
                    date_diff_days=0,
                    supplier_match=0.5,
                    details={
                        "invoices": [
                            {"id": inv["id"], "numero": inv["numero"], "total": float(inv["total"])}
                            for inv in best_combination
                        ],
                        "total_covered": total_covered,
                        "amount_diff_pct": round(amount_diff * 100, 2),
                    },
                ))

        return candidates

    def _find_best_combination(
        self,
        invoices: List[Dict],
        target: float,
        max_items: int = 4
    ) -> Optional[List[Dict]]:
        """Trouve la meilleure combinaison de factures pour atteindre le montant cible."""
        # Algorithme glouton + recherche limitée
        invoices = sorted(invoices, key=lambda x: float(x["total"]), reverse=True)

        def search(remaining: float, start: int, current: List[Dict], depth: int) -> Optional[List[Dict]]:
            if depth > max_items:
                return None

            # Vérifier si on est assez proche
            if abs(remaining) / target <= self.FUZZY_AMOUNT_TOLERANCE:
                return current

            for i in range(start, len(invoices)):
                inv = invoices[i]
                inv_total = float(inv["total"])

                if inv_total > remaining * 1.1:  # Trop grand
                    continue

                result = search(
                    remaining - inv_total,
                    i + 1,
                    current + [inv],
                    depth + 1
                )
                if result:
                    return result

            return None

        return search(target, 0, [], 0)

    def _extract_suppliers(self, libelle: str) -> List[str]:
        """Extrait les noms de fournisseurs potentiels du libellé."""
        suppliers = []
        libelle_lower = libelle.lower()

        # Chercher dans les alias connus
        for supplier, aliases in self._supplier_aliases.items():
            if supplier in libelle_lower:
                suppliers.append(supplier)
            for alias in aliases:
                if alias in libelle_lower:
                    suppliers.append(supplier)

        # Patterns courants
        patterns = [
            r"(?:paiement|virement|prelevement)\s+(?:a|vers?)\s+(.+?)(?:\s+\d|$)",
            r"(?:cb|carte)\s+(.+?)(?:\s+\d|$)",
            r"^(.+?)\s+(?:fact|facture)",
        ]

        for pattern in patterns:
            match = re.search(pattern, libelle_lower)
            if match:
                potential = match.group(1).strip()
                if len(potential) > 2:
                    suppliers.append(potential)

        return list(set(suppliers))

    def _calculate_supplier_match(
        self,
        invoice_supplier: str,
        potential_suppliers: List[str],
        libelle: str
    ) -> float:
        """Calcule le score de correspondance fournisseur."""
        if not invoice_supplier:
            return 0.0

        invoice_supplier_lower = invoice_supplier.lower()

        # Match exact
        if invoice_supplier_lower in libelle.lower():
            return 1.0

        # Match via alias
        aliases = self._supplier_aliases.get(invoice_supplier_lower, [])
        for alias in aliases:
            if alias in libelle.lower():
                return 0.9

        # Match partiel avec les suppliers extraits
        for potential in potential_suppliers:
            if potential in invoice_supplier_lower or invoice_supplier_lower in potential:
                return 0.7

            # Jaccard similarity
            words1 = set(invoice_supplier_lower.split())
            words2 = set(potential.split())
            if words1 and words2:
                jaccard = len(words1 & words2) / len(words1 | words2)
                if jaccard > 0.5:
                    return 0.5 + jaccard * 0.3

        return 0.0

    def _apply_reconciliation(self, transaction_id: int, candidate: MatchCandidate):
        """Applique un rapprochement."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO bank_reconciliation
                    (tenant_id, transaction_id, invoice_id, status, match_type, confidence, amount_covered, details)
                    VALUES
                    (:tenant_id, :transaction_id, :invoice_id, :status, :match_type, :confidence, :amount_covered, :details)
                    ON CONFLICT (tenant_id, transaction_id, invoice_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        confidence = EXCLUDED.confidence,
                        reconciled_at = NOW()
                """),
                {
                    "tenant_id": self.tenant_id,
                    "transaction_id": transaction_id,
                    "invoice_id": candidate.invoice_id,
                    "status": MatchStatus.MATCHED.value,
                    "match_type": candidate.match_type.value,
                    "confidence": candidate.confidence,
                    "amount_covered": candidate.details.get("invoice_total", 0),
                    "details": json.dumps(candidate.details),
                }
            )

            # Apprendre de ce rapprochement
            self._learn_from_match(transaction_id, candidate)

    def _learn_from_match(self, transaction_id: int, candidate: MatchCandidate):
        """Apprend de ce rapprochement pour améliorer les futurs.
        Note: Utilise finance_transactions avec entity_id.
        """
        engine = get_engine()

        # Récupérer le libellé de la transaction
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT label as libelle FROM finance_transactions WHERE id = :id"),
                {"id": transaction_id}
            )
            row = result.fetchone()
            if not row:
                return

            libelle = row.libelle.lower()

            # Ajouter un alias si correspondance forte
            if candidate.supplier_match > 0.8:
                supplier = candidate.details.get("invoice_supplier", "").lower()
                if supplier and supplier not in libelle:
                    # Extraire un alias potentiel
                    words = libelle.split()[:3]
                    potential_alias = " ".join(words)
                    if len(potential_alias) > 3:
                        conn.execute(
                            text("""
                                INSERT INTO supplier_aliases
                                (tenant_id, supplier_name, alias, source)
                                VALUES (:tenant_id, :supplier, :alias, 'learned')
                                ON CONFLICT DO NOTHING
                            """),
                            {
                                "tenant_id": self.tenant_id,
                                "supplier": supplier,
                                "alias": potential_alias,
                            }
                        )

    def _create_alert(
        self,
        alert_type: str,
        entity_type: str,
        entity_id: int,
        message: str
    ):
        """Crée une alerte de rapprochement."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO reconciliation_alerts
                    (tenant_id, alert_type, entity_type, entity_id, message)
                    VALUES (:tenant_id, :alert_type, :entity_type, :entity_id, :message)
                """),
                {
                    "tenant_id": self.tenant_id,
                    "alert_type": alert_type,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "message": message,
                }
            )

    def add_supplier_alias(self, supplier_name: str, alias: str):
        """Ajoute un alias fournisseur manuellement."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO supplier_aliases
                    (tenant_id, supplier_name, alias, source)
                    VALUES (:tenant_id, :supplier, :alias, 'manual')
                    ON CONFLICT DO NOTHING
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier": supplier_name.lower(),
                    "alias": alias.lower(),
                }
            )

        # Rafraîchir le cache
        supplier = supplier_name.lower()
        if supplier not in self._supplier_aliases:
            self._supplier_aliases[supplier] = []
        self._supplier_aliases[supplier].append(alias.lower())

    def manual_reconcile(
        self,
        transaction_id: int,
        invoice_ids: List[int],
        user: str
    ):
        """Rapprochement manuel."""
        engine = get_engine()
        with engine.begin() as conn:
            for invoice_id in invoice_ids:
                conn.execute(
                    text("""
                        INSERT INTO bank_reconciliation
                        (tenant_id, transaction_id, invoice_id, status, match_type, confidence, reconciled_by)
                        VALUES
                        (:tenant_id, :transaction_id, :invoice_id, 'matched', 'manual', 1.0, :user)
                        ON CONFLICT (tenant_id, transaction_id, invoice_id) DO UPDATE SET
                            status = 'matched',
                            match_type = 'manual',
                            confidence = 1.0,
                            reconciled_by = :user,
                            reconciled_at = NOW()
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "transaction_id": transaction_id,
                        "invoice_id": invoice_id,
                        "user": user,
                    }
                )

    def get_reconciliation_status(self) -> Dict[str, Any]:
        """Retourne le statut global du rapprochement.
        Note: Utilise finance_transactions/finance_reconciliations avec entity_id.
        """
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    WITH stats AS (
                        SELECT
                            COUNT(*) as total_transactions,
                            SUM(CASE WHEN fr.id IS NOT NULL THEN 1 ELSE 0 END) as matched,
                            SUM(ABS(CAST(ft.amount AS NUMERIC))) as total_amount
                        FROM finance_transactions ft
                        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
                        WHERE ft.entity_id = :entity_id
                          AND ft.date_operation >= NOW() - INTERVAL '60 days'
                          AND ft.direction = 'OUT'
                    ),
                    matched_amount AS (
                        SELECT COALESCE(SUM(ABS(CAST(ft.amount AS NUMERIC))), 0) as amount
                        FROM finance_transactions ft
                        JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
                        WHERE ft.entity_id = :entity_id
                    )
                    SELECT
                        s.total_transactions,
                        s.matched,
                        s.total_amount,
                        m.amount as matched_amount
                    FROM stats s, matched_amount m
                """),
                {"entity_id": entity_id}
            )

            row = result.fetchone()

            if not row:
                return {
                    "total_transactions": 0,
                    "matched_transactions": 0,
                    "match_rate": 0,
                    "total_amount": 0,
                    "matched_amount": 0,
                }

            total = row.total_transactions or 0
            matched = row.matched or 0

            return {
                "total_transactions": total,
                "matched_transactions": matched,
                "unmatched_transactions": total - matched,
                "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
                "total_amount": float(row.total_amount or 0),
                "matched_amount": float(row.matched_amount or 0),
            }

    def get_unmatched_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les transactions non rapprochées.
        Note: Utilise finance_transactions avec entity_id.
        """
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT ft.id, ft.date_operation as date,
                           CAST(ft.amount AS NUMERIC) as montant,
                           ft.label as libelle, NULL as categorie
                    FROM finance_transactions ft
                    LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
                    WHERE ft.entity_id = :entity_id
                      AND ft.direction = 'OUT'
                      AND ft.date_operation >= NOW() - INTERVAL '60 days'
                      AND fr.id IS NULL
                    ORDER BY ABS(CAST(ft.amount AS NUMERIC)) DESC
                    LIMIT :limit
                """),
                {"entity_id": entity_id, "limit": limit}
            )

            return [
                {
                    "id": row.id,
                    "date": row.date.isoformat() if row.date else None,
                    "amount": abs(float(row.montant)),
                    "description": row.libelle,
                    "category": row.categorie,
                }
                for row in result
            ]

    def get_alerts(self, resolved: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les alertes de rapprochement."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, alert_type, entity_type, entity_id, message, created_at
                    FROM reconciliation_alerts
                    WHERE tenant_id = :tenant_id AND resolved = :resolved
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {
                    "tenant_id": self.tenant_id,
                    "resolved": resolved,
                    "limit": limit,
                }
            )

            return [
                {
                    "id": row.id,
                    "type": row.alert_type,
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "message": row.message,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in result
            ]
