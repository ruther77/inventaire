"""Gestion des coûts (FIFO + coût moyen) pour les mouvements de stock."""  # Docstring du module de coûts

from __future__ import annotations  # Active les annotations différées

from dataclasses import dataclass  # Non utilisé ici mais importé (peut servir à structurer)
from datetime import datetime  # Gestion des horodatages
from decimal import Decimal, InvalidOperation  # Décimaux précis et exceptions associées
from typing import Any  # Typage générique

from sqlalchemy import text  # Construction de requêtes SQL textuelles


def _as_decimal(value: Any, default: str = "0") -> Decimal:
    try:  # Tente la conversion vers Decimal
        return Decimal(str(value))  # Convertit via la représentation chaîne
    except (InvalidOperation, TypeError, ValueError):  # Capture les cas de conversion invalide
        return Decimal(default)  # Retourne la valeur par défaut


def _refresh_average_cost(conn, *, tenant_id: int, product_id: int) -> None:
    row = conn.execute(
        text(
            """
            SELECT
                COALESCE(SUM(quantity_remaining * unit_cost), 0) AS stock_value,
                COALESCE(SUM(quantity_remaining), 0) AS stock_qty
            FROM inventory_cost_layers
            WHERE tenant_id = :tenant_id
              AND product_id = :product_id
            """
        ),
        {"tenant_id": tenant_id, "product_id": product_id},
    ).fetchone()  # Calcule la valeur et la quantité totale de stock
    stock_value = Decimal(str(row.stock_value or 0))  # Valeur totale du stock en Decimal
    stock_qty = Decimal(str(row.stock_qty or 0))  # Quantité totale de stock en Decimal
    average = Decimal("0")  # Valeur moyenne par défaut
    if stock_qty > 0:  # Si du stock existe
        average = (stock_value / stock_qty).quantize(Decimal("0.0001"))  # Calcule le coût moyen pondéré

    conn.execute(
        text(
            """
            UPDATE produits
            SET average_cost = :average_cost,
                updated_at = now()
            WHERE id = :product_id
              AND tenant_id = :tenant_id
            """
        ),
        {"average_cost": float(average), "product_id": product_id, "tenant_id": tenant_id},
    )  # Met à jour le coût moyen du produit


def _effective_unit_cost(conn, *, tenant_id: int, product_id: int, unit_cost: Decimal | None) -> Decimal:
    if unit_cost is not None and unit_cost > 0:  # Si un coût unitaire valide est fourni
        return unit_cost  # Utilise le coût fourni
    row = conn.execute(
        text(
            "SELECT average_cost FROM produits WHERE id = :product_id AND tenant_id = :tenant_id"
        ),
        {"product_id": product_id, "tenant_id": tenant_id},
    ).fetchone()  # Récupère le coût moyen existant
    if row and row.average_cost is not None:  # Si une valeur est trouvée
        candidate = _as_decimal(row.average_cost)  # Convertit en Decimal
        if candidate > 0:  # Si positif
            return candidate  # Renvoie le coût moyen
    return Decimal("0")  # Sinon revient à zéro


def add_cost_layer(
    conn,
    *,
    tenant_id: int,
    product_id: int,
    quantity: Decimal,
    unit_cost: Decimal | None,
    movement_id: int | None = None,
    source: str | None = None,
    received_at: datetime | None = None,
) -> None:
    qty = _as_decimal(quantity)  # Convertit la quantité en Decimal
    if qty <= 0:  # Vérifie que la quantité est positive
        return  # Sort si quantité nulle ou négative

    cost = _effective_unit_cost(conn, tenant_id=tenant_id, product_id=product_id, unit_cost=_as_decimal(unit_cost))  # Détermine le coût unitaire
    received = received_at or datetime.utcnow()  # Date de réception effective

    conn.execute(
        text(
            """
            INSERT INTO inventory_cost_layers (
                tenant_id,
                product_id,
                movement_id,
                quantity,
                quantity_remaining,
                unit_cost,
                received_at,
                source
            )
            VALUES (
                :tenant_id,
                :product_id,
                :movement_id,
                :quantity,
                :quantity_remaining,
                :unit_cost,
                :received_at,
                :source
            )
            """
        ),
        {
            "tenant_id": tenant_id,
            "product_id": product_id,
            "movement_id": movement_id,
            "quantity": float(qty),
            "quantity_remaining": float(qty),
            "unit_cost": float(cost),
            "received_at": received,
            "source": source,
        },
    )  # Insère une nouvelle couche de coût dans la table
    _refresh_average_cost(conn, tenant_id=tenant_id, product_id=product_id)  # Recalcule le coût moyen du produit


def consume_layers(
    conn,
    *,
    tenant_id: int,
    product_id: int,
    quantity: Decimal,
) -> None:
    qty = _as_decimal(quantity)  # Convertit la quantité demandée en Decimal
    if qty <= 0:  # Si la quantité est nulle ou négative
        return  # Sort immédiatement

    rows = conn.execute(
        text(
            """
            SELECT id, quantity_remaining, unit_cost
            FROM inventory_cost_layers
            WHERE tenant_id = :tenant_id
              AND product_id = :product_id
              AND quantity_remaining > 0
            ORDER BY received_at ASC, id ASC
            FOR UPDATE
            """
        ),
        {"tenant_id": tenant_id, "product_id": product_id},
    ).fetchall()  # Sélectionne les couches FIFO disponibles et verrouille pour mise à jour

    remaining = qty  # Quantité restant à consommer
    for row in rows:  # Parcourt chaque couche
        if remaining <= 0:  # Si plus rien à consommer
            break  # Quitte la boucle
        available = _as_decimal(row.quantity_remaining)  # Quantité disponible sur la couche
        if available <= 0:  # Si couche vide
            continue  # Passe à la suivante
        consumed = available if available <= remaining else remaining  # Quantité consommée depuis la couche
        new_remaining = available - consumed  # Stock restant sur la couche
        conn.execute(
            text(
                """
                UPDATE inventory_cost_layers
                SET quantity_remaining = :quantity_remaining,
                    is_depleted = CASE WHEN :quantity_remaining <= 0 THEN TRUE ELSE is_depleted END,
                    updated_at = now()
                WHERE id = :layer_id
                """
            ),
            {
                "quantity_remaining": float(new_remaining),
                "layer_id": row.id,
            },
        )  # Met à jour la couche avec la nouvelle quantité
        remaining -= consumed  # Diminue la quantité restante à consommer

    if remaining > 0:  # Si la demande dépasse le stock disponible
        raise ValueError(
            f"Stocks sans couches de coût suffisantes pour produit {product_id} (manque {remaining})."
        )  # Signale l'absence de couches suffisantes

    _refresh_average_cost(conn, tenant_id=tenant_id, product_id=product_id)  # Recalcule le coût moyen après consommation


__all__ = ["add_cost_layer", "consume_layers"]  # Exporte les fonctions publiques du module
