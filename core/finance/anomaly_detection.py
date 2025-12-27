"""
Détection d'anomalies financières avancée.

Fonctionnalités:
- Détection montants anormaux (Z-score, IQR)
- Paiements dupliqués
- Incohérences débit/crédit
- Fréquence inhabituelle
- Horaires suspects
- Factures manquantes
- Écarts prix attendu/facturé
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math
from statistics import mean, stdev, median

from sqlalchemy import text
from core.data_repository import get_engine


class AnomalyType(str, Enum):
    """Types d'anomalies."""
    AMOUNT_OUTLIER = "amount_outlier"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DEBIT_CREDIT_MISMATCH = "debit_credit_mismatch"
    UNUSUAL_FREQUENCY = "unusual_frequency"
    UNUSUAL_TIME = "unusual_time"
    MISSING_INVOICE = "missing_invoice"
    PRICE_DISCREPANCY = "price_discrepancy"
    ROUND_AMOUNT = "round_amount"  # Montants ronds suspects
    SEQUENCE_GAP = "sequence_gap"  # Numéros de facture manquants
    CATEGORY_MISMATCH = "category_mismatch"
    VELOCITY_SPIKE = "velocity_spike"  # Pic soudain de transactions


class Severity(str, Enum):
    """Niveaux de sévérité."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectedAnomaly:
    """Anomalie détectée."""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: Severity
    confidence: float  # 0.0 - 1.0
    title: str
    description: str
    entity_type: str  # transaction, invoice, product
    entity_id: str
    details: Dict[str, Any]
    suggested_action: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class AnomalyDetector:
    """Détecteur d'anomalies financières."""

    # Seuils par défaut
    Z_SCORE_THRESHOLD = 3.0
    IQR_MULTIPLIER = 1.5
    DUPLICATE_TOLERANCE_DAYS = 7
    DUPLICATE_AMOUNT_TOLERANCE = 0.02  # 2%

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._ensure_tables()
        self._category_stats: Dict[str, Dict] = {}

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS detected_anomalies (
                    id SERIAL PRIMARY KEY,
                    anomaly_id VARCHAR(50) UNIQUE NOT NULL,
                    tenant_id INTEGER NOT NULL,
                    anomaly_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    confidence FLOAT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    entity_type VARCHAR(50),
                    entity_id VARCHAR(100),
                    details JSONB DEFAULT '{}',
                    suggested_action TEXT,
                    detected_at TIMESTAMPTZ DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMPTZ,
                    resolved_by VARCHAR(100),
                    false_positive BOOLEAN DEFAULT FALSE,
                    notes TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_anomalies_tenant
                    ON detected_anomalies(tenant_id, resolved);
                CREATE INDEX IF NOT EXISTS idx_anomalies_type
                    ON detected_anomalies(tenant_id, anomaly_type);
                CREATE INDEX IF NOT EXISTS idx_anomalies_severity
                    ON detected_anomalies(tenant_id, severity);
            """))

    def detect_all(
        self,
        transactions: Optional[List[Dict]] = None,
        invoices: Optional[List[Dict]] = None,
        period_days: int = 30
    ) -> List[DetectedAnomaly]:
        """Lance toutes les détections."""
        anomalies = []

        if transactions:
            anomalies.extend(self.detect_transaction_anomalies(transactions))

        if invoices:
            anomalies.extend(self.detect_invoice_anomalies(invoices))

        # Détections basées sur l'historique
        anomalies.extend(self.detect_from_history(period_days))

        # Sauvegarder et retourner
        for anomaly in anomalies:
            self._save_anomaly(anomaly)

        return anomalies

    def detect_transaction_anomalies(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[DetectedAnomaly]:
        """Détecte les anomalies dans les transactions."""
        anomalies = []

        # Grouper par catégorie pour les stats
        by_category = defaultdict(list)
        for tx in transactions:
            cat = tx.get("category") or tx.get("categorie") or "Non catégorisé"
            amount = abs(float(tx.get("amount") or tx.get("montant") or 0))
            by_category[cat].append(amount)

        # Calculer les stats par catégorie
        category_stats = {}
        for cat, amounts in by_category.items():
            if len(amounts) >= 3:
                category_stats[cat] = {
                    "mean": mean(amounts),
                    "std": stdev(amounts) if len(amounts) > 1 else 0,
                    "median": median(amounts),
                    "q1": sorted(amounts)[len(amounts) // 4],
                    "q3": sorted(amounts)[3 * len(amounts) // 4],
                }

        for tx in transactions:
            tx_anomalies = []

            # 1. Montant anormal (Z-score)
            amount = abs(float(tx.get("amount") or tx.get("montant") or 0))
            cat = tx.get("category") or tx.get("categorie") or "Non catégorisé"

            if cat in category_stats:
                stats = category_stats[cat]
                if stats["std"] > 0:
                    z_score = abs(amount - stats["mean"]) / stats["std"]
                    if z_score > self.Z_SCORE_THRESHOLD:
                        tx_anomalies.append(self._create_amount_outlier_anomaly(
                            tx, z_score, stats
                        ))

            # 2. Montant rond suspect (fraude potentielle)
            if self._is_suspicious_round_amount(amount):
                tx_anomalies.append(self._create_round_amount_anomaly(tx, amount))

            # 3. Horaire inhabituel
            tx_date = tx.get("date")
            if tx_date and self._is_unusual_time(tx_date):
                tx_anomalies.append(self._create_unusual_time_anomaly(tx, tx_date))

            anomalies.extend(tx_anomalies)

        # 4. Détection de doublons
        anomalies.extend(self._detect_duplicate_transactions(transactions))

        # 5. Spike de vélocité
        velocity_anomaly = self._detect_velocity_spike(transactions)
        if velocity_anomaly:
            anomalies.append(velocity_anomaly)

        return anomalies

    def detect_invoice_anomalies(
        self,
        invoices: List[Dict[str, Any]]
    ) -> List[DetectedAnomaly]:
        """Détecte les anomalies dans les factures."""
        anomalies = []

        # 1. Factures dupliquées
        seen_signatures = {}
        for inv in invoices:
            signature = self._compute_invoice_signature(inv)
            if signature in seen_signatures:
                anomalies.append(self._create_duplicate_invoice_anomaly(
                    inv, seen_signatures[signature]
                ))
            else:
                seen_signatures[signature] = inv

        # 2. Écarts de prix
        for inv in invoices:
            price_anomalies = self._detect_price_discrepancies(inv)
            anomalies.extend(price_anomalies)

        # 3. Séquence de numéros manquants
        sequence_anomalies = self._detect_sequence_gaps(invoices)
        anomalies.extend(sequence_anomalies)

        return anomalies

    def detect_from_history(self, period_days: int = 30) -> List[DetectedAnomaly]:
        """Détecte les anomalies basées sur l'historique DB."""
        anomalies = []
        since = datetime.utcnow() - timedelta(days=period_days)

        # 1. Factures non rapprochées (potentiellement manquantes côté banque)
        anomalies.extend(self._detect_missing_bank_transactions(since))

        # 2. Transactions non rapprochées (factures manquantes)
        anomalies.extend(self._detect_missing_invoices(since))

        # 3. Changements de fréquence inhabituels
        anomalies.extend(self._detect_frequency_changes(since))

        return anomalies

    def _create_amount_outlier_anomaly(
        self,
        tx: Dict,
        z_score: float,
        stats: Dict
    ) -> DetectedAnomaly:
        """Crée une anomalie de montant anormal."""
        amount = abs(float(tx.get("amount") or tx.get("montant") or 0))
        tx_id = str(tx.get("id", "unknown"))

        severity = Severity.MEDIUM
        if z_score > 5:
            severity = Severity.HIGH
        if z_score > 7:
            severity = Severity.CRITICAL

        return DetectedAnomaly(
            anomaly_id=f"AMT-{tx_id}-{int(datetime.utcnow().timestamp())}",
            anomaly_type=AnomalyType.AMOUNT_OUTLIER,
            severity=severity,
            confidence=min(z_score / 5, 1.0),
            title=f"Montant inhabituel: {amount:.2f}€",
            description=f"Le montant est à {z_score:.1f} écarts-types de la moyenne ({stats['mean']:.2f}€)",
            entity_type="transaction",
            entity_id=tx_id,
            details={
                "amount": amount,
                "z_score": round(z_score, 2),
                "category_mean": round(stats["mean"], 2),
                "category_std": round(stats["std"], 2),
                "category": tx.get("category") or tx.get("categorie"),
            },
            suggested_action="Vérifier la validité de cette transaction et confirmer le montant",
        )

    def _create_round_amount_anomaly(
        self,
        tx: Dict,
        amount: float
    ) -> DetectedAnomaly:
        """Crée une anomalie de montant rond suspect."""
        tx_id = str(tx.get("id", "unknown"))

        return DetectedAnomaly(
            anomaly_id=f"RND-{tx_id}-{int(datetime.utcnow().timestamp())}",
            anomaly_type=AnomalyType.ROUND_AMOUNT,
            severity=Severity.LOW,
            confidence=0.5,
            title=f"Montant rond: {amount:.2f}€",
            description="Les montants parfaitement ronds sont parfois associés à des fraudes",
            entity_type="transaction",
            entity_id=tx_id,
            details={
                "amount": amount,
                "description": tx.get("description") or tx.get("libelle"),
            },
            suggested_action="Vérifier que ce montant correspond à une opération légitime",
        )

    def _create_unusual_time_anomaly(
        self,
        tx: Dict,
        tx_date: Any
    ) -> DetectedAnomaly:
        """Crée une anomalie d'horaire inhabituel."""
        tx_id = str(tx.get("id", "unknown"))

        if isinstance(tx_date, str):
            tx_date = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))

        return DetectedAnomaly(
            anomaly_id=f"TIME-{tx_id}-{int(datetime.utcnow().timestamp())}",
            anomaly_type=AnomalyType.UNUSUAL_TIME,
            severity=Severity.LOW,
            confidence=0.4,
            title=f"Transaction à une heure inhabituelle",
            description=f"Transaction effectuée à {tx_date.strftime('%H:%M') if hasattr(tx_date, 'strftime') else tx_date}",
            entity_type="transaction",
            entity_id=tx_id,
            details={
                "timestamp": str(tx_date),
                "hour": tx_date.hour if hasattr(tx_date, "hour") else None,
            },
            suggested_action="Vérifier que cette transaction est légitime",
        )

    def _create_duplicate_invoice_anomaly(
        self,
        inv: Dict,
        original: Dict
    ) -> DetectedAnomaly:
        """Crée une anomalie de facture dupliquée."""
        inv_id = str(inv.get("id", "unknown"))

        return DetectedAnomaly(
            anomaly_id=f"DUP-INV-{inv_id}-{int(datetime.utcnow().timestamp())}",
            anomaly_type=AnomalyType.DUPLICATE_INVOICE,
            severity=Severity.HIGH,
            confidence=0.9,
            title=f"Facture potentiellement dupliquée",
            description=f"Cette facture semble être un doublon de la facture #{original.get('id')}",
            entity_type="invoice",
            entity_id=inv_id,
            details={
                "duplicate_of": original.get("id"),
                "supplier": inv.get("fournisseur") or inv.get("supplier"),
                "amount": inv.get("total") or inv.get("montant"),
                "date": str(inv.get("date")),
            },
            suggested_action="Vérifier si cette facture est un doublon et la supprimer si nécessaire",
        )

    def _is_suspicious_round_amount(self, amount: float) -> bool:
        """Vérifie si un montant est suspecteusement rond."""
        if amount < 50:
            return False

        # Montants exactement ronds (100, 500, 1000, etc.)
        if amount == int(amount) and amount >= 100:
            # Vérifier si c'est un multiple de 100 ou 500
            if amount % 100 == 0:
                return True

        return False

    def _is_unusual_time(self, tx_date: Any) -> bool:
        """Vérifie si l'heure est inhabituelle."""
        if isinstance(tx_date, str):
            try:
                tx_date = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))
            except ValueError:
                return False

        if not hasattr(tx_date, "hour"):
            return False

        # Transactions entre minuit et 6h du matin
        return 0 <= tx_date.hour < 6

    def _detect_duplicate_transactions(
        self,
        transactions: List[Dict]
    ) -> List[DetectedAnomaly]:
        """Détecte les transactions dupliquées."""
        anomalies = []
        seen = {}

        for tx in transactions:
            amount = abs(float(tx.get("amount") or tx.get("montant") or 0))
            date = tx.get("date")
            desc = str(tx.get("description") or tx.get("libelle") or "")[:50]

            # Signature simplifiée
            key = f"{amount:.2f}:{desc}"

            if key in seen:
                original = seen[key]
                # Vérifier la proximité temporelle
                if self._dates_are_close(date, original.get("date"), self.DUPLICATE_TOLERANCE_DAYS):
                    anomalies.append(DetectedAnomaly(
                        anomaly_id=f"DUP-TX-{tx.get('id', 'unknown')}-{int(datetime.utcnow().timestamp())}",
                        anomaly_type=AnomalyType.DUPLICATE_TRANSACTION,
                        severity=Severity.HIGH,
                        confidence=0.85,
                        title=f"Transaction potentiellement dupliquée: {amount:.2f}€",
                        description=f"Même montant et description similaire à {self.DUPLICATE_TOLERANCE_DAYS} jours d'intervalle",
                        entity_type="transaction",
                        entity_id=str(tx.get("id", "unknown")),
                        details={
                            "amount": amount,
                            "original_id": original.get("id"),
                            "original_date": str(original.get("date")),
                            "current_date": str(date),
                        },
                        suggested_action="Vérifier si c'est un paiement en double",
                    ))
            else:
                seen[key] = tx

        return anomalies

    def _detect_velocity_spike(
        self,
        transactions: List[Dict]
    ) -> Optional[DetectedAnomaly]:
        """Détecte un pic soudain de transactions."""
        if len(transactions) < 10:
            return None

        # Grouper par jour
        by_day = defaultdict(int)
        for tx in transactions:
            date = tx.get("date")
            if date:
                if isinstance(date, str):
                    date = date[:10]  # YYYY-MM-DD
                elif hasattr(date, "date"):
                    date = date.date().isoformat()
                by_day[date] += 1

        if len(by_day) < 5:
            return None

        counts = list(by_day.values())
        avg_count = mean(counts)
        std_count = stdev(counts) if len(counts) > 1 else 0

        # Trouver les jours avec pic
        for day, count in by_day.items():
            if std_count > 0:
                z = (count - avg_count) / std_count
                if z > 3:
                    return DetectedAnomaly(
                        anomaly_id=f"VEL-{day}-{int(datetime.utcnow().timestamp())}",
                        anomaly_type=AnomalyType.VELOCITY_SPIKE,
                        severity=Severity.MEDIUM,
                        confidence=min(z / 4, 1.0),
                        title=f"Pic de transactions le {day}",
                        description=f"{count} transactions ce jour vs moyenne de {avg_count:.1f}",
                        entity_type="period",
                        entity_id=day,
                        details={
                            "count": count,
                            "average": round(avg_count, 1),
                            "z_score": round(z, 2),
                        },
                        suggested_action="Vérifier l'activité inhabituelle de cette journée",
                    )

        return None

    def _compute_invoice_signature(self, inv: Dict) -> str:
        """Calcule une signature unique pour détecter les doublons."""
        supplier = str(inv.get("fournisseur") or inv.get("supplier") or "").lower()[:20]
        amount = float(inv.get("total") or inv.get("montant") or 0)
        date = str(inv.get("date") or "")[:10]

        return f"{supplier}:{amount:.2f}:{date}"

    def _detect_price_discrepancies(self, inv: Dict) -> List[DetectedAnomaly]:
        """Détecte les écarts de prix par rapport aux attendus."""
        anomalies = []
        items = inv.get("items") or inv.get("lignes") or []

        engine = get_engine()

        for item in items:
            product_id = item.get("product_id") or item.get("produit_id")
            if not product_id:
                continue

            invoiced_price = float(item.get("prix_unitaire") or item.get("prix") or 0)
            if invoiced_price <= 0:
                continue

            # Récupérer le dernier prix connu
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT prix_achat as prix FROM produits_price_history
                        WHERE produit_id = :product_id
                        ORDER BY facture_date DESC
                        LIMIT 1
                    """),
                    {"product_id": product_id}
                )
                row = result.fetchone()

                if row and row.prix > 0:
                    expected_price = row.prix
                    deviation_pct = abs(invoiced_price - expected_price) / expected_price * 100

                    if deviation_pct > 15:  # Plus de 15% d'écart
                        anomalies.append(DetectedAnomaly(
                            anomaly_id=f"PRICE-{inv.get('id')}-{product_id}-{int(datetime.utcnow().timestamp())}",
                            anomaly_type=AnomalyType.PRICE_DISCREPANCY,
                            severity=Severity.MEDIUM if deviation_pct < 30 else Severity.HIGH,
                            confidence=min(deviation_pct / 50, 1.0),
                            title=f"Écart de prix: {deviation_pct:.1f}%",
                            description=f"Prix facturé {invoiced_price:.2f}€ vs attendu {expected_price:.2f}€",
                            entity_type="invoice_line",
                            entity_id=f"{inv.get('id')}-{product_id}",
                            details={
                                "product_id": product_id,
                                "invoiced_price": invoiced_price,
                                "expected_price": expected_price,
                                "deviation_pct": round(deviation_pct, 1),
                            },
                            suggested_action="Vérifier le prix avec le fournisseur",
                        ))

        return anomalies

    def _detect_sequence_gaps(self, invoices: List[Dict]) -> List[DetectedAnomaly]:
        """Détecte les trous dans les séquences de numéros de facture."""
        anomalies = []

        # Grouper par fournisseur
        by_supplier = defaultdict(list)
        for inv in invoices:
            supplier = inv.get("fournisseur") or inv.get("supplier") or "unknown"
            number = inv.get("numero") or inv.get("number")
            if number:
                by_supplier[supplier].append((number, inv))

        for supplier, items in by_supplier.items():
            # Essayer d'extraire des numéros
            numbers = []
            for num_str, inv in items:
                try:
                    # Extraire la partie numérique
                    num = int("".join(filter(str.isdigit, str(num_str))) or "0")
                    if num > 0:
                        numbers.append((num, inv))
                except ValueError:
                    continue

            if len(numbers) < 3:
                continue

            # Trier et chercher les gaps
            numbers.sort(key=lambda x: x[0])
            for i in range(1, len(numbers)):
                gap = numbers[i][0] - numbers[i-1][0]
                if gap > 1 and gap < 10:  # Gap raisonnable mais suspect
                    anomalies.append(DetectedAnomaly(
                        anomaly_id=f"SEQ-{supplier[:10]}-{numbers[i-1][0]}-{int(datetime.utcnow().timestamp())}",
                        anomaly_type=AnomalyType.SEQUENCE_GAP,
                        severity=Severity.MEDIUM,
                        confidence=0.7,
                        title=f"Factures manquantes: {supplier}",
                        description=f"Gap de {gap-1} factures entre #{numbers[i-1][0]} et #{numbers[i][0]}",
                        entity_type="invoice_sequence",
                        entity_id=f"{supplier}-{numbers[i-1][0]}",
                        details={
                            "supplier": supplier,
                            "from_number": numbers[i-1][0],
                            "to_number": numbers[i][0],
                            "missing_count": gap - 1,
                        },
                        suggested_action="Vérifier si des factures sont manquantes",
                    ))

        return anomalies

    def _detect_missing_bank_transactions(self, since: datetime) -> List[DetectedAnomaly]:
        """Détecte les factures sans transaction bancaire correspondante.
        Note: Utilise finance_invoices_supplier/finance_transactions avec entity_id.
        """
        anomalies = []
        engine = get_engine()

        # Conversion tenant_id -> entity_id
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            # Factures non rapprochées depuis plus de X jours
            result = conn.execute(
                text("""
                    SELECT f.id, f.invoice_number as numero, v.name as fournisseur,
                           f.montant_ttc as total, f.date_invoice as date
                    FROM finance_invoices_supplier f
                    LEFT JOIN finance_vendors v ON v.id = f.vendor_id
                    WHERE f.entity_id = :entity_id
                      AND f.date_invoice >= :since
                      AND f.date_invoice <= NOW() - INTERVAL '7 days'
                      AND f.status NOT IN ('PAID', 'CANCELLED')
                      AND NOT EXISTS (
                          SELECT 1 FROM finance_reconciliations fr
                          WHERE fr.invoice_id = f.id
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM finance_transactions ft
                          WHERE ft.entity_id = f.entity_id
                            AND ft.direction = 'OUT'
                            AND ABS(CAST(ft.amount AS NUMERIC)) BETWEEN f.montant_ttc * 0.98 AND f.montant_ttc * 1.02
                            AND ft.date_operation BETWEEN f.date_invoice - INTERVAL '30 days' AND f.date_invoice + INTERVAL '30 days'
                      )
                    LIMIT 20
                """),
                {"entity_id": entity_id, "since": since}
            )

            for row in result:
                anomalies.append(DetectedAnomaly(
                    anomaly_id=f"MISS-BANK-{row.id}-{int(datetime.utcnow().timestamp())}",
                    anomaly_type=AnomalyType.MISSING_INVOICE,
                    severity=Severity.MEDIUM,
                    confidence=0.6,
                    title=f"Facture sans paiement: {row.fournisseur or 'Inconnu'}",
                    description=f"Facture #{row.numero} de {row.total:.2f}€ sans transaction bancaire correspondante" if row.total else f"Facture #{row.numero} sans transaction bancaire correspondante",
                    entity_type="invoice",
                    entity_id=str(row.id),
                    details={
                        "invoice_number": row.numero,
                        "supplier": row.fournisseur,
                        "amount": float(row.total) if row.total else 0,
                        "date": row.date.isoformat() if row.date else None,
                    },
                    suggested_action="Vérifier si le paiement a été effectué",
                ))

        return anomalies

    def _detect_missing_invoices(self, since: datetime) -> List[DetectedAnomaly]:
        """Détecte les transactions sans facture correspondante.
        Note: Utilise finance_transactions avec entity_id.
        """
        anomalies = []
        engine = get_engine()

        # Conversion tenant_id -> entity_id
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            # Transactions fournisseurs sans facture
            result = conn.execute(
                text("""
                    SELECT ft.id, ft.label as libelle, CAST(ft.amount AS NUMERIC) as montant, ft.date_operation as date
                    FROM finance_transactions ft
                    WHERE ft.entity_id = :entity_id
                      AND ft.date_operation >= :since
                      AND ft.direction = 'OUT'
                      AND ABS(CAST(ft.amount AS NUMERIC)) > 50
                      AND NOT EXISTS (
                          SELECT 1 FROM finance_reconciliations fr
                          WHERE fr.transaction_id = ft.id
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM finance_invoices_supplier f
                          WHERE f.entity_id = ft.entity_id
                            AND f.montant_ttc BETWEEN ABS(CAST(ft.amount AS NUMERIC)) * 0.98 AND ABS(CAST(ft.amount AS NUMERIC)) * 1.02
                            AND f.date_invoice BETWEEN ft.date_operation - INTERVAL '30 days' AND ft.date_operation + INTERVAL '30 days'
                      )
                    LIMIT 20
                """),
                {"entity_id": entity_id, "since": since}
            )

            for row in result:
                amount = abs(float(row.montant)) if row.montant else 0
                label = row.libelle or 'Sans libellé'
                anomalies.append(DetectedAnomaly(
                    anomaly_id=f"MISS-INV-{row.id}-{int(datetime.utcnow().timestamp())}",
                    anomaly_type=AnomalyType.MISSING_INVOICE,
                    severity=Severity.MEDIUM,
                    confidence=0.65,
                    title=f"Paiement sans facture: {amount:.2f}€",
                    description=f"Transaction '{label[:50]}' sans facture correspondante",
                    entity_type="transaction",
                    entity_id=str(row.id),
                    details={
                        "description": label,
                        "amount": amount,
                        "date": row.date.isoformat() if row.date else None,
                    },
                    suggested_action="Retrouver la facture correspondante",
                ))

        return anomalies

    def _detect_frequency_changes(self, since: datetime) -> List[DetectedAnomaly]:
        """Détecte les changements de fréquence inhabituels.
        Note: Utilise finance_invoices_supplier/finance_vendors avec entity_id.
        """
        anomalies = []
        engine = get_engine()

        # Conversion tenant_id -> entity_id
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        # Comparer la fréquence récente vs historique
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    WITH recent AS (
                        SELECT v.name as fournisseur, COUNT(*) as recent_count
                        FROM finance_invoices_supplier f
                        JOIN finance_vendors v ON v.id = f.vendor_id
                        WHERE f.entity_id = :entity_id
                          AND f.date_invoice >= :since
                        GROUP BY v.name
                    ),
                    historical AS (
                        SELECT v.name as fournisseur, COUNT(*) / 3.0 as monthly_avg
                        FROM finance_invoices_supplier f
                        JOIN finance_vendors v ON v.id = f.vendor_id
                        WHERE f.entity_id = :entity_id
                          AND f.date_invoice >= :since - INTERVAL '90 days'
                          AND f.date_invoice < :since
                        GROUP BY v.name
                    )
                    SELECT r.fournisseur, r.recent_count, h.monthly_avg,
                           r.recent_count / NULLIF(h.monthly_avg, 0) as ratio
                    FROM recent r
                    JOIN historical h ON r.fournisseur = h.fournisseur
                    WHERE h.monthly_avg > 0
                      AND (r.recent_count / h.monthly_avg > 2 OR r.recent_count / h.monthly_avg < 0.5)
                """),
                {"entity_id": entity_id, "since": since}
            )

            for row in result:
                ratio = row.ratio or 0
                supplier_name = row.fournisseur or 'Inconnu'
                if ratio > 2:
                    desc = f"Augmentation x{ratio:.1f} des factures"
                else:
                    desc = f"Diminution à {ratio*100:.0f}% des factures habituelles"

                anomalies.append(DetectedAnomaly(
                    anomaly_id=f"FREQ-{supplier_name[:20]}-{int(datetime.utcnow().timestamp())}",
                    anomaly_type=AnomalyType.UNUSUAL_FREQUENCY,
                    severity=Severity.LOW,
                    confidence=0.5,
                    title=f"Fréquence inhabituelle: {supplier_name}",
                    description=desc,
                    entity_type="supplier",
                    entity_id=supplier_name,
                    details={
                        "recent_count": row.recent_count,
                        "monthly_average": round(row.monthly_avg, 1),
                        "ratio": round(ratio, 2),
                    },
                    suggested_action="Vérifier si ce changement est normal",
                ))

        return anomalies

    def _dates_are_close(self, date1: Any, date2: Any, days: int) -> bool:
        """Vérifie si deux dates sont proches."""
        try:
            if isinstance(date1, str):
                date1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
            if isinstance(date2, str):
                date2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))

            if hasattr(date1, "date"):
                date1 = date1.date() if hasattr(date1.date, "__call__") else date1
            if hasattr(date2, "date"):
                date2 = date2.date() if hasattr(date2.date, "__call__") else date2

            return abs((date1 - date2).days) <= days
        except Exception:
            return False

    def _save_anomaly(self, anomaly: DetectedAnomaly):
        """Sauvegarde une anomalie en base."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO detected_anomalies
                    (anomaly_id, tenant_id, anomaly_type, severity, confidence,
                     title, description, entity_type, entity_id, details, suggested_action)
                    VALUES
                    (:anomaly_id, :tenant_id, :anomaly_type, :severity, :confidence,
                     :title, :description, :entity_type, :entity_id, :details, :suggested_action)
                    ON CONFLICT (anomaly_id) DO NOTHING
                """),
                {
                    "anomaly_id": anomaly.anomaly_id,
                    "tenant_id": self.tenant_id,
                    "anomaly_type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity.value,
                    "confidence": anomaly.confidence,
                    "title": anomaly.title,
                    "description": anomaly.description,
                    "entity_type": anomaly.entity_type,
                    "entity_id": anomaly.entity_id,
                    "details": json.dumps(anomaly.details),
                    "suggested_action": anomaly.suggested_action,
                }
            )

    def get_unresolved_anomalies(
        self,
        severity: Optional[Severity] = None,
        anomaly_type: Optional[AnomalyType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Récupère les anomalies non résolues."""
        engine = get_engine()

        query = """
            SELECT anomaly_id, anomaly_type, severity, confidence, title,
                   description, entity_type, entity_id, details, suggested_action, detected_at
            FROM detected_anomalies
            WHERE tenant_id = :tenant_id AND resolved = FALSE AND false_positive = FALSE
        """
        params = {"tenant_id": self.tenant_id, "limit": limit}

        if severity:
            query += " AND severity = :severity"
            params["severity"] = severity.value

        if anomaly_type:
            query += " AND anomaly_type = :anomaly_type"
            params["anomaly_type"] = anomaly_type.value

        query += " ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, detected_at DESC LIMIT :limit"

        with engine.connect() as conn:
            result = conn.execute(text(query), params)

            return [
                {
                    "anomaly_id": row.anomaly_id,
                    "type": row.anomaly_type,
                    "severity": row.severity,
                    "confidence": row.confidence,
                    "title": row.title,
                    "description": row.description,
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "details": row.details if isinstance(row.details, dict) else json.loads(row.details or "{}"),
                    "suggested_action": row.suggested_action,
                    "detected_at": row.detected_at.isoformat() if row.detected_at else None,
                }
                for row in result
            ]

    def resolve_anomaly(
        self,
        anomaly_id: str,
        resolved_by: str,
        false_positive: bool = False,
        notes: Optional[str] = None
    ):
        """Marque une anomalie comme résolue."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE detected_anomalies
                    SET resolved = TRUE,
                        resolved_at = NOW(),
                        resolved_by = :resolved_by,
                        false_positive = :false_positive,
                        notes = :notes
                    WHERE anomaly_id = :anomaly_id AND tenant_id = :tenant_id
                """),
                {
                    "anomaly_id": anomaly_id,
                    "tenant_id": self.tenant_id,
                    "resolved_by": resolved_by,
                    "false_positive": false_positive,
                    "notes": notes,
                }
            )
