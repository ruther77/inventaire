"""
Moteur de règles financières avec apprentissage semi-supervisé.

Fonctionnalités:
- Matching automatique dépenses → catégories
- Regex, scoring de similarité, poids par fournisseur
- Apprentissage progressif
- Détection d'anomalies
- Propositions automatiques avec confiance
"""

from __future__ import annotations

import re
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from collections import defaultdict

from sqlalchemy import text
from core.data_repository import get_engine


class RuleType(str, Enum):
    """Types de règles."""
    REGEX = "regex"
    KEYWORD = "keyword"
    AMOUNT_RANGE = "amount_range"
    SUPPLIER = "supplier"
    COMBINED = "combined"
    ML_LEARNED = "ml_learned"


class AnomalyType(str, Enum):
    """Types d'anomalies détectées."""
    AMOUNT_ABNORMAL = "amount_abnormal"
    DUPLICATE_PAYMENT = "duplicate_payment"
    DEBIT_CREDIT_MISMATCH = "debit_credit_mismatch"
    UNUSUAL_FREQUENCY = "unusual_frequency"
    UNUSUAL_TIME = "unusual_time"
    MISSING_INVOICE = "missing_invoice"


@dataclass
class Rule:
    """Représentation d'une règle de catégorisation."""
    id: int
    tenant_id: int
    name: str
    rule_type: RuleType
    category: str
    conditions: Dict[str, Any]
    priority: int = 0
    weight: float = 1.0
    hits: int = 0
    accuracy: float = 1.0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ClassificationResult:
    """Résultat de classification."""
    category: str
    confidence: float
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    method: str = "rule"
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Anomaly:
    """Représentation d'une anomalie détectée."""
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    description: str
    details: Dict[str, Any]
    confidence: float


class FinancialRulesEngine:
    """Moteur de règles pour classification automatique."""

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._rules_cache: Optional[List[Rule]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._stats_cache: Dict[str, Dict] = {}
        self._ensure_tables()

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS financial_rules (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    rule_type VARCHAR(50) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    conditions JSONB NOT NULL DEFAULT '{}',
                    priority INTEGER DEFAULT 0,
                    weight FLOAT DEFAULT 1.0,
                    hits INTEGER DEFAULT 0,
                    accuracy FLOAT DEFAULT 1.0,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(tenant_id, name)
                );

                CREATE INDEX IF NOT EXISTS idx_financial_rules_tenant
                    ON financial_rules(tenant_id, active);
                CREATE INDEX IF NOT EXISTS idx_financial_rules_category
                    ON financial_rules(tenant_id, category);

                CREATE TABLE IF NOT EXISTS classification_history (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    transaction_id VARCHAR(100) NOT NULL,
                    predicted_category VARCHAR(100),
                    actual_category VARCHAR(100),
                    confidence FLOAT,
                    rule_id INTEGER,
                    method VARCHAR(50),
                    feedback VARCHAR(20), -- correct, incorrect, adjusted
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_classification_history_tenant
                    ON classification_history(tenant_id, created_at);

                CREATE TABLE IF NOT EXISTS category_stats (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    supplier VARCHAR(200),
                    avg_amount FLOAT DEFAULT 0,
                    stddev_amount FLOAT DEFAULT 0,
                    min_amount FLOAT DEFAULT 0,
                    max_amount FLOAT DEFAULT 0,
                    count INTEGER DEFAULT 0,
                    last_updated TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(tenant_id, category, supplier)
                );
            """))

    def _load_rules(self) -> List[Rule]:
        """Charge les règles depuis la DB avec cache."""
        now = datetime.utcnow()
        if (self._rules_cache is not None and
            self._cache_timestamp is not None and
            (now - self._cache_timestamp).seconds < 60):
            return self._rules_cache

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, tenant_id, name, rule_type, category, conditions,
                           priority, weight, hits, accuracy, active, created_at, updated_at
                    FROM financial_rules
                    WHERE tenant_id = :tenant_id AND active = TRUE
                    ORDER BY priority DESC, weight DESC
                """),
                {"tenant_id": self.tenant_id}
            )

            rules = []
            for row in result:
                rules.append(Rule(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    name=row.name,
                    rule_type=RuleType(row.rule_type),
                    category=row.category,
                    conditions=row.conditions if isinstance(row.conditions, dict) else json.loads(row.conditions),
                    priority=row.priority,
                    weight=row.weight,
                    hits=row.hits,
                    accuracy=row.accuracy,
                    active=row.active,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                ))

            self._rules_cache = rules
            self._cache_timestamp = now
            return rules

    def _load_category_stats(self, category: str, supplier: Optional[str] = None) -> Dict[str, float]:
        """Charge les statistiques d'une catégorie."""
        cache_key = f"{category}:{supplier or 'ALL'}"
        if cache_key in self._stats_cache:
            return self._stats_cache[cache_key]

        engine = get_engine()
        with engine.connect() as conn:
            query = """
                SELECT avg_amount, stddev_amount, min_amount, max_amount, count
                FROM category_stats
                WHERE tenant_id = :tenant_id AND category = :category
            """
            params = {"tenant_id": self.tenant_id, "category": category}

            if supplier:
                query += " AND supplier = :supplier"
                params["supplier"] = supplier
            else:
                query += " AND supplier IS NULL"

            result = conn.execute(text(query), params)
            row = result.fetchone()

            if row:
                stats = {
                    "avg_amount": row.avg_amount or 0,
                    "stddev_amount": row.stddev_amount or 0,
                    "min_amount": row.min_amount or 0,
                    "max_amount": row.max_amount or 0,
                    "count": row.count or 0,
                }
            else:
                stats = {"avg_amount": 0, "stddev_amount": 0, "min_amount": 0, "max_amount": 0, "count": 0}

            self._stats_cache[cache_key] = stats
            return stats

    def classify(
        self,
        transaction: Dict[str, Any],
        detect_anomalies: bool = True
    ) -> ClassificationResult:
        """Classifie une transaction."""
        rules = self._load_rules()
        matches: List[Tuple[Rule, float]] = []

        description = str(transaction.get("description", "") or transaction.get("libelle", "")).lower()
        amount = abs(float(transaction.get("amount", 0) or transaction.get("montant", 0)))
        supplier = str(transaction.get("supplier", "") or transaction.get("fournisseur", "")).lower()
        date = transaction.get("date")

        # Évaluer chaque règle
        for rule in rules:
            score = self._evaluate_rule(rule, description, amount, supplier, date)
            if score > 0:
                matches.append((rule, score * rule.weight * rule.accuracy))

        # Trier par score
        matches.sort(key=lambda x: x[1], reverse=True)

        # Détecter les anomalies
        anomalies = []
        if detect_anomalies:
            anomalies = self._detect_anomalies(transaction, matches)

        if not matches:
            # Essayer l'apprentissage automatique
            ml_result = self._ml_classify(description, amount, supplier)
            if ml_result:
                return ClassificationResult(
                    category=ml_result[0],
                    confidence=ml_result[1],
                    method="ml_learned",
                    anomalies=[a.__dict__ for a in anomalies],
                )

            return ClassificationResult(
                category="Non catégorisé",
                confidence=0.0,
                method="none",
                anomalies=[a.__dict__ for a in anomalies],
            )

        best_match = matches[0]
        alternatives = [(m[0].category, m[1]) for m in matches[1:4]]

        return ClassificationResult(
            category=best_match[0].category,
            confidence=min(best_match[1], 1.0),
            rule_id=best_match[0].id,
            rule_name=best_match[0].name,
            method="rule",
            alternatives=alternatives,
            anomalies=[a.__dict__ for a in anomalies],
        )

    def _evaluate_rule(
        self,
        rule: Rule,
        description: str,
        amount: float,
        supplier: str,
        date: Any
    ) -> float:
        """Évalue une règle et retourne un score."""
        conditions = rule.conditions
        total_score = 0.0
        total_weight = 0.0

        # Règle regex sur description
        if rule.rule_type == RuleType.REGEX or "pattern" in conditions:
            pattern = conditions.get("pattern", "")
            if pattern:
                try:
                    if re.search(pattern, description, re.IGNORECASE):
                        total_score += 1.0
                    total_weight += 1.0
                except re.error:
                    pass

        # Règle mots-clés
        if rule.rule_type == RuleType.KEYWORD or "keywords" in conditions:
            keywords = conditions.get("keywords", [])
            if keywords:
                matched = sum(1 for kw in keywords if kw.lower() in description)
                if matched > 0:
                    total_score += matched / len(keywords)
                total_weight += 1.0

        # Règle plage de montant
        if rule.rule_type == RuleType.AMOUNT_RANGE or "amount_min" in conditions or "amount_max" in conditions:
            amount_min = conditions.get("amount_min", 0)
            amount_max = conditions.get("amount_max", float("inf"))
            if amount_min <= amount <= amount_max:
                total_score += 1.0
            total_weight += 1.0

        # Règle fournisseur
        if rule.rule_type == RuleType.SUPPLIER or "suppliers" in conditions:
            suppliers = conditions.get("suppliers", [])
            if suppliers:
                for s in suppliers:
                    if s.lower() in supplier or supplier in s.lower():
                        total_score += 1.0
                        break
                total_weight += 1.0

        # Score de similarité fuzzy
        if "fuzzy_terms" in conditions:
            fuzzy_terms = conditions["fuzzy_terms"]
            similarity = self._calculate_similarity(description, fuzzy_terms)
            if similarity > 0.3:
                total_score += similarity
                total_weight += 1.0

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def _calculate_similarity(self, text: str, terms: List[str]) -> float:
        """Calcule un score de similarité fuzzy."""
        if not terms:
            return 0.0

        text_words = set(text.lower().split())
        max_similarity = 0.0

        for term in terms:
            term_words = set(term.lower().split())
            if not term_words:
                continue

            # Jaccard similarity
            intersection = len(text_words & term_words)
            union = len(text_words | term_words)
            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)

            # Substring matching
            if term.lower() in text:
                max_similarity = max(max_similarity, 0.8)

        return max_similarity

    def _ml_classify(
        self,
        description: str,
        amount: float,
        supplier: str
    ) -> Optional[Tuple[str, float]]:
        """Classification par apprentissage (basée sur l'historique)."""
        engine = get_engine()
        with engine.connect() as conn:
            # Chercher des transactions similaires avec feedback positif
            result = conn.execute(
                text("""
                    SELECT actual_category, COUNT(*) as cnt
                    FROM classification_history
                    WHERE tenant_id = :tenant_id
                      AND feedback = 'correct'
                      AND actual_category IS NOT NULL
                    GROUP BY actual_category
                    ORDER BY cnt DESC
                    LIMIT 10
                """),
                {"tenant_id": self.tenant_id}
            )

            categories = [(row.actual_category, row.cnt) for row in result]
            if not categories:
                return None

            # Score basé sur fréquence + similarité historique
            # Pour une vraie implémentation ML, utiliser TF-IDF ou embeddings
            total = sum(c[1] for c in categories)
            best_category = categories[0][0]
            confidence = categories[0][1] / total if total > 0 else 0.3

            return (best_category, confidence)

    def _detect_anomalies(
        self,
        transaction: Dict[str, Any],
        matches: List[Tuple[Rule, float]]
    ) -> List[Anomaly]:
        """Détecte les anomalies dans une transaction."""
        anomalies = []

        amount = abs(float(transaction.get("amount", 0) or transaction.get("montant", 0)))
        description = str(transaction.get("description", "") or transaction.get("libelle", ""))
        date = transaction.get("date")
        tx_type = transaction.get("type", "").lower()

        # Détection montant anormal
        if matches:
            category = matches[0][0].category
            stats = self._load_category_stats(category)

            if stats["count"] >= 5 and stats["stddev_amount"] > 0:
                z_score = abs(amount - stats["avg_amount"]) / stats["stddev_amount"]
                if z_score > 3:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.AMOUNT_ABNORMAL,
                        severity="high" if z_score > 5 else "medium",
                        description=f"Montant inhabituel pour la catégorie {category}",
                        details={
                            "amount": amount,
                            "avg": stats["avg_amount"],
                            "stddev": stats["stddev_amount"],
                            "z_score": round(z_score, 2),
                        },
                        confidence=min(z_score / 5, 1.0),
                    ))

        # Détection incohérence débit/crédit
        if tx_type:
            debit_keywords = ["achat", "paiement", "prelevement", "virement sortant", "retrait"]
            credit_keywords = ["remboursement", "avoir", "virement entrant", "depot"]

            is_debit_desc = any(kw in description.lower() for kw in debit_keywords)
            is_credit_desc = any(kw in description.lower() for kw in credit_keywords)

            if (tx_type == "debit" and is_credit_desc) or (tx_type == "credit" and is_debit_desc):
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.DEBIT_CREDIT_MISMATCH,
                    severity="medium",
                    description="Incohérence entre le type de transaction et sa description",
                    details={"type": tx_type, "description": description[:100]},
                    confidence=0.7,
                ))

        return anomalies

    def classify_batch(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[ClassificationResult]:
        """Classifie un lot de transactions."""
        return [self.classify(tx) for tx in transactions]

    def add_rule(
        self,
        name: str,
        rule_type: RuleType,
        category: str,
        conditions: Dict[str, Any],
        priority: int = 0,
        weight: float = 1.0
    ) -> int:
        """Ajoute une nouvelle règle."""
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO financial_rules
                    (tenant_id, name, rule_type, category, conditions, priority, weight)
                    VALUES (:tenant_id, :name, :rule_type, :category, :conditions, :priority, :weight)
                    ON CONFLICT (tenant_id, name) DO UPDATE SET
                        rule_type = EXCLUDED.rule_type,
                        category = EXCLUDED.category,
                        conditions = EXCLUDED.conditions,
                        priority = EXCLUDED.priority,
                        weight = EXCLUDED.weight,
                        updated_at = NOW()
                    RETURNING id
                """),
                {
                    "tenant_id": self.tenant_id,
                    "name": name,
                    "rule_type": rule_type.value,
                    "category": category,
                    "conditions": json.dumps(conditions),
                    "priority": priority,
                    "weight": weight,
                }
            )
            row = result.fetchone()
            self._rules_cache = None  # Invalider le cache
            return row.id

    def record_feedback(
        self,
        transaction_id: str,
        predicted_category: str,
        actual_category: str,
        feedback: str,
        rule_id: Optional[int] = None,
        confidence: float = 0.0,
        method: str = "rule"
    ):
        """Enregistre le feedback pour améliorer l'apprentissage."""
        engine = get_engine()
        with engine.begin() as conn:
            # Enregistrer l'historique
            conn.execute(
                text("""
                    INSERT INTO classification_history
                    (tenant_id, transaction_id, predicted_category, actual_category,
                     confidence, rule_id, method, feedback)
                    VALUES
                    (:tenant_id, :transaction_id, :predicted_category, :actual_category,
                     :confidence, :rule_id, :method, :feedback)
                """),
                {
                    "tenant_id": self.tenant_id,
                    "transaction_id": transaction_id,
                    "predicted_category": predicted_category,
                    "actual_category": actual_category,
                    "confidence": confidence,
                    "rule_id": rule_id,
                    "method": method,
                    "feedback": feedback,
                }
            )

            # Mettre à jour l'accuracy de la règle si applicable
            if rule_id:
                if feedback == "correct":
                    conn.execute(
                        text("""
                            UPDATE financial_rules
                            SET hits = hits + 1,
                                accuracy = (accuracy * hits + 1.0) / (hits + 1),
                                updated_at = NOW()
                            WHERE id = :rule_id
                        """),
                        {"rule_id": rule_id}
                    )
                elif feedback == "incorrect":
                    conn.execute(
                        text("""
                            UPDATE financial_rules
                            SET hits = hits + 1,
                                accuracy = (accuracy * hits) / (hits + 1),
                                updated_at = NOW()
                            WHERE id = :rule_id
                        """),
                        {"rule_id": rule_id}
                    )

        self._rules_cache = None

    def update_category_stats(self, category: str, supplier: Optional[str], amount: float):
        """Met à jour les statistiques d'une catégorie."""
        engine = get_engine()
        with engine.begin() as conn:
            # Upsert avec calcul incrémental
            conn.execute(
                text("""
                    INSERT INTO category_stats
                    (tenant_id, category, supplier, avg_amount, min_amount, max_amount, count, stddev_amount)
                    VALUES (:tenant_id, :category, :supplier, :amount, :amount, :amount, 1, 0)
                    ON CONFLICT (tenant_id, category, supplier) DO UPDATE SET
                        avg_amount = (category_stats.avg_amount * category_stats.count + :amount) / (category_stats.count + 1),
                        min_amount = LEAST(category_stats.min_amount, :amount),
                        max_amount = GREATEST(category_stats.max_amount, :amount),
                        count = category_stats.count + 1,
                        last_updated = NOW()
                """),
                {
                    "tenant_id": self.tenant_id,
                    "category": category,
                    "supplier": supplier,
                    "amount": amount,
                }
            )

        # Invalider le cache stats
        cache_key = f"{category}:{supplier or 'ALL'}"
        self._stats_cache.pop(cache_key, None)

    def get_rules(self) -> List[Dict[str, Any]]:
        """Retourne toutes les règles."""
        rules = self._load_rules()
        return [
            {
                "id": r.id,
                "name": r.name,
                "rule_type": r.rule_type.value,
                "category": r.category,
                "conditions": r.conditions,
                "priority": r.priority,
                "weight": r.weight,
                "hits": r.hits,
                "accuracy": r.accuracy,
                "active": r.active,
            }
            for r in rules
        ]

    def detect_duplicate_payments(
        self,
        transaction: Dict[str, Any],
        tolerance_days: int = 7,
        tolerance_amount: float = 0.02
    ) -> Optional[Anomaly]:
        """Détecte les paiements en double potentiels."""
        amount = abs(float(transaction.get("amount", 0) or transaction.get("montant", 0)))
        date = transaction.get("date")
        description = str(transaction.get("description", "") or transaction.get("libelle", ""))

        if not date:
            return None

        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))

        # Utilise finance_transactions avec entity_id
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, date_operation as date, CAST(amount AS NUMERIC) as montant, label as libelle
                    FROM finance_transactions
                    WHERE entity_id = :entity_id
                      AND ABS(CAST(amount AS NUMERIC)) BETWEEN :amount_min AND :amount_max
                      AND date_operation BETWEEN :date_min AND :date_max
                      AND label ILIKE :description
                    LIMIT 5
                """),
                {
                    "entity_id": entity_id,
                    "amount_min": amount * (1 - tolerance_amount),
                    "amount_max": amount * (1 + tolerance_amount),
                    "date_min": date - timedelta(days=tolerance_days),
                    "date_max": date + timedelta(days=tolerance_days),
                    "description": f"%{description[:30]}%",
                }
            )

            duplicates = list(result)
            if len(duplicates) > 1:
                return Anomaly(
                    anomaly_type=AnomalyType.DUPLICATE_PAYMENT,
                    severity="high",
                    description=f"Paiement potentiellement dupliqué ({len(duplicates)} occurrences similaires)",
                    details={
                        "count": len(duplicates),
                        "ids": [d.id for d in duplicates],
                        "dates": [d.date.isoformat() if d.date else None for d in duplicates],
                    },
                    confidence=0.8 if len(duplicates) == 2 else 0.9,
                )

        return None


# Règles prédéfinies pour bootstrap
DEFAULT_RULES = [
    {
        "name": "Approvisionnement Metro",
        "rule_type": RuleType.SUPPLIER,
        "category": "Approvisionnement",
        "conditions": {"suppliers": ["metro", "metro cash"], "keywords": ["metro"]},
        "priority": 10,
    },
    {
        "name": "Approvisionnement Promocash",
        "rule_type": RuleType.SUPPLIER,
        "category": "Approvisionnement",
        "conditions": {"suppliers": ["promocash", "pro cash"], "keywords": ["promocash"]},
        "priority": 10,
    },
    {
        "name": "Charges locatives",
        "rule_type": RuleType.KEYWORD,
        "category": "Loyer & Charges",
        "conditions": {"keywords": ["loyer", "bail", "charges locatives", "foncier"]},
        "priority": 5,
    },
    {
        "name": "Électricité",
        "rule_type": RuleType.KEYWORD,
        "category": "Énergie",
        "conditions": {"keywords": ["edf", "engie", "electricite", "électricité", "energie"]},
        "priority": 5,
    },
    {
        "name": "Télécom",
        "rule_type": RuleType.KEYWORD,
        "category": "Télécom",
        "conditions": {"keywords": ["orange", "sfr", "bouygues", "free", "telephone", "internet"]},
        "priority": 5,
    },
    {
        "name": "Salaires",
        "rule_type": RuleType.KEYWORD,
        "category": "Salaires",
        "conditions": {"keywords": ["salaire", "paie", "virement personnel"], "amount_min": 500},
        "priority": 8,
    },
    {
        "name": "URSSAF",
        "rule_type": RuleType.KEYWORD,
        "category": "Charges sociales",
        "conditions": {"keywords": ["urssaf", "cotisation", "prevoyance", "mutuelle"]},
        "priority": 7,
    },
    {
        "name": "Impôts et taxes",
        "rule_type": RuleType.KEYWORD,
        "category": "Impôts",
        "conditions": {"keywords": ["impot", "taxe", "tva", "cfe", "cvae", "tresor public"]},
        "priority": 7,
    },
    {
        "name": "Banque",
        "rule_type": RuleType.KEYWORD,
        "category": "Frais bancaires",
        "conditions": {"keywords": ["commission", "agios", "frais bancaire", "tenue compte"]},
        "priority": 3,
    },
    {
        "name": "Assurance",
        "rule_type": RuleType.KEYWORD,
        "category": "Assurance",
        "conditions": {"keywords": ["assurance", "axa", "maaf", "allianz", "groupama"]},
        "priority": 5,
    },
]


def bootstrap_default_rules(tenant_id: int):
    """Initialise les règles par défaut pour un tenant."""
    engine_instance = FinancialRulesEngine(tenant_id)
    for rule_def in DEFAULT_RULES:
        try:
            engine_instance.add_rule(
                name=rule_def["name"],
                rule_type=rule_def["rule_type"],
                category=rule_def["category"],
                conditions=rule_def["conditions"],
                priority=rule_def.get("priority", 0),
            )
        except Exception:
            pass  # Ignore si la règle existe déjà
