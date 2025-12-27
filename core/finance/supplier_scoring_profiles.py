"""
Gestion des profils de scoring fournisseur.

Permet de créer, gérer et assigner des profils de scoring
personnalisés pour différents types de fournisseurs (PME, Grands Comptes, etc.).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from core.data_repository import get_engine


@dataclass
class ScoringProfile:
    """Profil de scoring fournisseur."""
    id: Optional[int]
    tenant_id: int
    name: str
    description: Optional[str]
    price_stability_weight: float
    delivery_reliability_weight: float
    invoice_accuracy_weight: float
    stock_accuracy_weight: float
    payment_terms_weight: float
    responsiveness_weight: float
    product_quality_weight: float
    is_default: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def weights_dict(self) -> Dict[str, float]:
        """Retourne les poids sous forme de dictionnaire."""
        return {
            "price_stability": self.price_stability_weight,
            "delivery_reliability": self.delivery_reliability_weight,
            "invoice_accuracy": self.invoice_accuracy_weight,
            "stock_accuracy": self.stock_accuracy_weight,
            "payment_terms": self.payment_terms_weight,
            "responsiveness": self.responsiveness_weight,
            "product_quality": self.product_quality_weight,
        }

    def validate_weights(self) -> bool:
        """Vérifie que les poids somment à 100."""
        total = sum(self.weights_dict.values())
        return abs(total - 100.0) < 0.01  # Allow small floating point errors


class ScoringProfileManager:
    """Gestionnaire de profils de scoring."""

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id

    def create_profile(
        self,
        name: str,
        description: str,
        weights: Dict[str, float],
        is_default: bool = False
    ) -> ScoringProfile:
        """Crée un nouveau profil de scoring.

        Args:
            name: Nom du profil
            description: Description du profil
            weights: Dictionnaire des poids (doit sommer à 100)
            is_default: Si ce profil est le défaut pour le tenant

        Returns:
            Le profil créé

        Raises:
            ValueError: Si les poids ne somment pas à 100
        """
        # Validate weights sum to 100
        total = sum(weights.values())
        if abs(total - 100.0) >= 0.01:
            raise ValueError(f"Les poids doivent sommer à 100, actuellement: {total}")

        engine = get_engine()
        with engine.begin() as conn:
            # If this is default, unset other defaults
            if is_default:
                conn.execute(
                    text("""
                        UPDATE supplier_scoring_profiles
                        SET is_default = false
                        WHERE tenant_id = :tenant_id AND is_default = true
                    """),
                    {"tenant_id": self.tenant_id}
                )

            # Insert profile
            result = conn.execute(
                text("""
                    INSERT INTO supplier_scoring_profiles (
                        tenant_id, name, description,
                        price_stability_weight, delivery_reliability_weight,
                        invoice_accuracy_weight, stock_accuracy_weight,
                        payment_terms_weight, responsiveness_weight,
                        product_quality_weight, is_default
                    ) VALUES (
                        :tenant_id, :name, :description,
                        :price_stability, :delivery_reliability,
                        :invoice_accuracy, :stock_accuracy,
                        :payment_terms, :responsiveness,
                        :product_quality, :is_default
                    )
                    RETURNING id, created_at, updated_at
                """),
                {
                    "tenant_id": self.tenant_id,
                    "name": name,
                    "description": description,
                    "price_stability": weights.get("price_stability", 25.0),
                    "delivery_reliability": weights.get("delivery_reliability", 20.0),
                    "invoice_accuracy": weights.get("invoice_accuracy", 15.0),
                    "stock_accuracy": weights.get("stock_accuracy", 15.0),
                    "payment_terms": weights.get("payment_terms", 10.0),
                    "responsiveness": weights.get("responsiveness", 10.0),
                    "product_quality": weights.get("product_quality", 5.0),
                    "is_default": is_default,
                }
            )

            row = result.fetchone()
            return ScoringProfile(
                id=row[0],
                tenant_id=self.tenant_id,
                name=name,
                description=description,
                price_stability_weight=weights.get("price_stability", 25.0),
                delivery_reliability_weight=weights.get("delivery_reliability", 20.0),
                invoice_accuracy_weight=weights.get("invoice_accuracy", 15.0),
                stock_accuracy_weight=weights.get("stock_accuracy", 15.0),
                payment_terms_weight=weights.get("payment_terms", 10.0),
                responsiveness_weight=weights.get("responsiveness", 10.0),
                product_quality_weight=weights.get("product_quality", 5.0),
                is_default=is_default,
                created_at=row[1],
                updated_at=row[2],
            )

    def get_profile(self, profile_id: int) -> Optional[ScoringProfile]:
        """Récupère un profil par ID."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        id, tenant_id, name, description,
                        price_stability_weight, delivery_reliability_weight,
                        invoice_accuracy_weight, stock_accuracy_weight,
                        payment_terms_weight, responsiveness_weight,
                        product_quality_weight, is_default,
                        created_at, updated_at
                    FROM supplier_scoring_profiles
                    WHERE id = :profile_id AND tenant_id = :tenant_id
                """),
                {"profile_id": profile_id, "tenant_id": self.tenant_id}
            )

            row = result.fetchone()
            if not row:
                return None

            return ScoringProfile(
                id=row[0],
                tenant_id=row[1],
                name=row[2],
                description=row[3],
                price_stability_weight=float(row[4]),
                delivery_reliability_weight=float(row[5]),
                invoice_accuracy_weight=float(row[6]),
                stock_accuracy_weight=float(row[7]),
                payment_terms_weight=float(row[8]),
                responsiveness_weight=float(row[9]),
                product_quality_weight=float(row[10]),
                is_default=row[11],
                created_at=row[12],
                updated_at=row[13],
            )

    def list_profiles(self) -> List[ScoringProfile]:
        """Liste tous les profils du tenant."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        id, tenant_id, name, description,
                        price_stability_weight, delivery_reliability_weight,
                        invoice_accuracy_weight, stock_accuracy_weight,
                        payment_terms_weight, responsiveness_weight,
                        product_quality_weight, is_default,
                        created_at, updated_at
                    FROM supplier_scoring_profiles
                    WHERE tenant_id = :tenant_id
                    ORDER BY is_default DESC, name
                """),
                {"tenant_id": self.tenant_id}
            )

            profiles = []
            for row in result:
                profiles.append(ScoringProfile(
                    id=row[0],
                    tenant_id=row[1],
                    name=row[2],
                    description=row[3],
                    price_stability_weight=float(row[4]),
                    delivery_reliability_weight=float(row[5]),
                    invoice_accuracy_weight=float(row[6]),
                    stock_accuracy_weight=float(row[7]),
                    payment_terms_weight=float(row[8]),
                    responsiveness_weight=float(row[9]),
                    product_quality_weight=float(row[10]),
                    is_default=row[11],
                    created_at=row[12],
                    updated_at=row[13],
                ))

            return profiles

    def assign_profile_to_supplier(
        self,
        supplier_id: int,
        profile_id: int
    ) -> bool:
        """Assigne un profil à un fournisseur.

        Args:
            supplier_id: ID du fournisseur dans dim_supplier
            profile_id: ID du profil à assigner

        Returns:
            True si l'assignation a réussi
        """
        engine = get_engine()
        with engine.begin() as conn:
            # Verify profile exists and belongs to tenant
            profile_check = conn.execute(
                text("""
                    SELECT id FROM supplier_scoring_profiles
                    WHERE id = :profile_id AND tenant_id = :tenant_id
                """),
                {"profile_id": profile_id, "tenant_id": self.tenant_id}
            )

            if not profile_check.fetchone():
                return False

            # Update supplier
            conn.execute(
                text("""
                    UPDATE dim_supplier
                    SET scoring_profile_id = :profile_id,
                        updated_at = NOW()
                    WHERE id = :supplier_id
                """),
                {"supplier_id": supplier_id, "profile_id": profile_id}
            )

            return True

    def get_default_profile(self) -> Optional[ScoringProfile]:
        """Récupère le profil par défaut du tenant."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        id, tenant_id, name, description,
                        price_stability_weight, delivery_reliability_weight,
                        invoice_accuracy_weight, stock_accuracy_weight,
                        payment_terms_weight, responsiveness_weight,
                        product_quality_weight, is_default,
                        created_at, updated_at
                    FROM supplier_scoring_profiles
                    WHERE tenant_id = :tenant_id AND is_default = true
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"tenant_id": self.tenant_id}
            )

            row = result.fetchone()
            if not row:
                return None

            return ScoringProfile(
                id=row[0],
                tenant_id=row[1],
                name=row[2],
                description=row[3],
                price_stability_weight=float(row[4]),
                delivery_reliability_weight=float(row[5]),
                invoice_accuracy_weight=float(row[6]),
                stock_accuracy_weight=float(row[7]),
                payment_terms_weight=float(row[8]),
                responsiveness_weight=float(row[9]),
                product_quality_weight=float(row[10]),
                is_default=row[11],
                created_at=row[12],
                updated_at=row[13],
            )


def seed_default_profiles(tenant_id: int) -> Dict[str, ScoringProfile]:
    """Crée les profils par défaut pour un tenant.

    Args:
        tenant_id: ID du tenant

    Returns:
        Dictionnaire des profils créés {nom: profil}
    """
    manager = ScoringProfileManager(tenant_id)

    profiles = {}

    # PME Profile: Focus on price stability and delivery
    pme_profile = manager.create_profile(
        name="PME",
        description="Profil pour PME - Focus sur stabilité prix et livraison",
        weights={
            "price_stability": 30.0,
            "delivery_reliability": 25.0,
            "invoice_accuracy": 15.0,
            "stock_accuracy": 10.0,
            "payment_terms": 10.0,
            "responsiveness": 5.0,
            "product_quality": 5.0,
        },
        is_default=True
    )
    profiles["PME"] = pme_profile

    # Grand Compte Profile: Focus on delivery, quality, and responsiveness
    grand_compte_profile = manager.create_profile(
        name="Grand Compte",
        description="Profil pour grands comptes - Focus sur livraison, qualité et réactivité",
        weights={
            "price_stability": 15.0,
            "delivery_reliability": 30.0,
            "invoice_accuracy": 15.0,
            "stock_accuracy": 10.0,
            "payment_terms": 10.0,
            "responsiveness": 15.0,
            "product_quality": 5.0,
        },
        is_default=False
    )
    profiles["Grand Compte"] = grand_compte_profile

    # Quality Focused Profile: For critical products
    quality_profile = manager.create_profile(
        name="Qualité Premium",
        description="Focus sur qualité et fiabilité",
        weights={
            "price_stability": 10.0,
            "delivery_reliability": 25.0,
            "invoice_accuracy": 15.0,
            "stock_accuracy": 15.0,
            "payment_terms": 5.0,
            "responsiveness": 10.0,
            "product_quality": 20.0,
        },
        is_default=False
    )
    profiles["Qualité Premium"] = quality_profile

    # Price Focused Profile: For commodity items
    price_profile = manager.create_profile(
        name="Prix Compétitif",
        description="Focus sur stabilité des prix",
        weights={
            "price_stability": 40.0,
            "delivery_reliability": 20.0,
            "invoice_accuracy": 10.0,
            "stock_accuracy": 10.0,
            "payment_terms": 10.0,
            "responsiveness": 5.0,
            "product_quality": 5.0,
        },
        is_default=False
    )
    profiles["Prix Compétitif"] = price_profile

    return profiles
