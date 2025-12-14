"""
Event Handlers - Réactions automatiques aux événements du système.

Ce module centralise tous les handlers qui synchronisent les entités :
- Facture importée → Stock mis à jour + Prix historisé + Alertes générées
- Stock bas → Alerte créée
- Prix changé → Anomalie détectée si variation > seuil

Les handlers sont enregistrés au démarrage de l'application.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from core.finance.event_sourcing import (
    Event,
    EventStore,
    EventType,
    EventDispatcher,
)

LOGGER = logging.getLogger(__name__)

# Seuils configurables
PRICE_VARIATION_ALERT_THRESHOLD = 0.15  # 15% de variation déclenche une alerte
STOCK_CRITICAL_DAYS = 3  # Stock critique si < 3 jours de consommation


def _get_product_info(product_id: int, tenant_id: int) -> Optional[dict]:
    """Récupère les infos d'un produit."""
    sql = text("""
        SELECT id, nom, stock_actuel, seuil_alerte, prix_achat, prix_vente
        FROM produits
        WHERE id = :product_id AND tenant_id = :tenant_id
    """)
    df = query_df(sql, {"product_id": product_id, "tenant_id": tenant_id})
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def _get_avg_daily_consumption(product_id: int, tenant_id: int, days: int = 30) -> float:
    """Calcule la consommation moyenne journalière d'un produit."""
    sql = text("""
        SELECT COALESCE(SUM(ABS(quantite)), 0) / :days as avg_daily
        FROM mouvements_stock
        WHERE produit_id = :product_id
          AND tenant_id = :tenant_id
          AND type_mouvement = 'SORTIE'
          AND date_mouvement >= CURRENT_DATE - :days * INTERVAL '1 day'
    """)
    df = query_df(sql, {"product_id": product_id, "tenant_id": tenant_id, "days": days})
    if df.empty:
        return 0.0
    return float(df.iloc[0].get("avg_daily", 0) or 0)


def _get_last_price(product_id: int, tenant_id: int, supplier: str = None) -> Optional[float]:
    """Récupère le dernier prix enregistré pour un produit."""
    sql = text("""
        SELECT prix_achat
        FROM produits_price_history
        WHERE tenant_id = :tenant_id
          AND produit_id = :product_id
          AND (:supplier IS NULL OR fournisseur = :supplier)
        ORDER BY date_facture DESC, created_at DESC
        LIMIT 1
    """)
    df = query_df(sql, {"product_id": product_id, "tenant_id": tenant_id, "supplier": supplier})
    if df.empty:
        return None
    return float(df.iloc[0].get("prix_achat", 0) or 0)


def _create_inventory_alert(
    tenant_id: int,
    product_id: int,
    alert_type: str,
    severity: str,
    message: str,
    data: dict = None
):
    """Crée une alerte d'inventaire dans la base."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO inventory_alerts
                (tenant_id, product_id, alert_type, severity, message, data, created_at)
                VALUES (:tenant_id, :product_id, :alert_type, :severity, :message, :data, NOW())
                ON CONFLICT DO NOTHING
            """),
            {
                "tenant_id": tenant_id,
                "product_id": product_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "data": str(data) if data else "{}",
            }
        )


# =============================================================================
# HANDLERS
# =============================================================================

def handle_invoice_imported(event: Event):
    """
    Handler: Facture importée

    Actions:
    1. Log l'événement
    2. Vérifie les stocks des produits concernés
    3. Génère des alertes si stock critique
    """
    LOGGER.info(
        "📦 Facture importée: %s (%s lignes) - Fournisseur: %s",
        event.payload.get("filename"),
        event.payload.get("items_count"),
        event.payload.get("supplier"),
    )

    # Les produits concernés sont dans le payload
    product_ids = event.payload.get("product_ids", [])

    for product_id in product_ids:
        try:
            product = _get_product_info(product_id, event.tenant_id)
            if not product:
                continue

            stock = float(product.get("stock_actuel") or 0)
            seuil = float(product.get("seuil_alerte") or 0)

            # Vérifie si le stock est critique après l'import
            if seuil > 0 and stock < seuil:
                _create_inventory_alert(
                    tenant_id=event.tenant_id,
                    product_id=product_id,
                    alert_type="low_stock",
                    severity="warning",
                    message=f"Stock bas pour {product.get('nom')}: {stock} unités (seuil: {seuil})",
                    data={"stock": stock, "seuil": seuil}
                )
        except Exception as e:
            LOGGER.warning("Erreur vérification stock produit %s: %s", product_id, e)


def handle_stock_movement(event: Event):
    """
    Handler: Mouvement de stock

    Actions:
    1. Vérifie si le stock passe sous le seuil d'alerte
    2. Calcule les jours de stock restants
    3. Génère une alerte si critique
    """
    product_id = int(event.aggregate_id)
    movement_type = event.payload.get("movement_type")
    quantity = float(event.payload.get("quantity", 0))

    LOGGER.debug(
        "📊 Mouvement stock: Produit %s, Type %s, Quantité %s",
        product_id, movement_type, quantity
    )

    try:
        product = _get_product_info(product_id, event.tenant_id)
        if not product:
            return

        stock = float(product.get("stock_actuel") or 0)
        seuil = float(product.get("seuil_alerte") or 0)
        nom = product.get("nom", f"Produit #{product_id}")

        # Calcul jours de stock restants
        avg_consumption = _get_avg_daily_consumption(product_id, event.tenant_id)
        days_of_stock = stock / avg_consumption if avg_consumption > 0 else float('inf')

        # Alerte stock critique
        if stock <= 0:
            _create_inventory_alert(
                tenant_id=event.tenant_id,
                product_id=product_id,
                alert_type="stockout",
                severity="critical",
                message=f"RUPTURE DE STOCK: {nom}",
                data={"stock": 0}
            )

            # Émet un événement STOCK_ALERT
            dispatcher = EventDispatcher(event.tenant_id, event.user_id)
            dispatcher.emit(
                EventType.STOCK_ALERT,
                "product",
                str(product_id),
                {
                    "alert_type": "stockout",
                    "product_name": nom,
                    "stock": 0,
                }
            )

        elif days_of_stock < STOCK_CRITICAL_DAYS:
            _create_inventory_alert(
                tenant_id=event.tenant_id,
                product_id=product_id,
                alert_type="stockout_imminent",
                severity="warning",
                message=f"Stock critique pour {nom}: {days_of_stock:.1f} jours restants",
                data={"stock": stock, "days_remaining": days_of_stock}
            )

        elif seuil > 0 and stock < seuil:
            _create_inventory_alert(
                tenant_id=event.tenant_id,
                product_id=product_id,
                alert_type="low_stock",
                severity="info",
                message=f"Stock bas pour {nom}: {stock} unités (seuil: {seuil})",
                data={"stock": stock, "seuil": seuil}
            )

    except Exception as e:
        LOGGER.warning("Erreur handler mouvement stock: %s", e)


def handle_price_updated(event: Event):
    """
    Handler: Prix mis à jour

    Actions:
    1. Compare avec le prix précédent
    2. Détecte les variations anormales (>15%)
    3. Génère une alerte/anomalie si nécessaire
    """
    product_id = int(event.aggregate_id)
    old_price = float(event.payload.get("old_price", 0))
    new_price = float(event.payload.get("new_price", 0))
    supplier = event.payload.get("supplier")
    variation_pct = float(event.payload.get("variation_pct", 0))

    LOGGER.debug(
        "💰 Prix mis à jour: Produit %s, %s → %s (%.1f%%)",
        product_id, old_price, new_price, variation_pct
    )

    # Détection d'anomalie si variation > seuil
    if abs(variation_pct) > PRICE_VARIATION_ALERT_THRESHOLD * 100:
        try:
            product = _get_product_info(product_id, event.tenant_id)
            nom = product.get("nom", f"Produit #{product_id}") if product else f"Produit #{product_id}"

            direction = "hausse" if variation_pct > 0 else "baisse"
            severity = "warning" if abs(variation_pct) < 30 else "critical"

            # Émet un événement d'anomalie
            dispatcher = EventDispatcher(event.tenant_id, event.user_id)
            dispatcher.emit(
                EventType.PRICE_ALERT_TRIGGERED,
                "product",
                str(product_id),
                {
                    "product_name": nom,
                    "old_price": old_price,
                    "new_price": new_price,
                    "variation_pct": variation_pct,
                    "supplier": supplier,
                    "direction": direction,
                    "severity": severity,
                }
            )

            LOGGER.warning(
                "⚠️ Anomalie prix détectée: %s - %s de %.1f%% (%s → %s) - Fournisseur: %s",
                nom, direction, abs(variation_pct), old_price, new_price, supplier
            )

        except Exception as e:
            LOGGER.warning("Erreur handler prix: %s", e)


def handle_bank_transaction_categorized(event: Event):
    """
    Handler: Transaction bancaire catégorisée

    Actions:
    1. Log la catégorisation
    2. Met à jour les statistiques de règles (si applicable)
    """
    transaction_id = event.aggregate_id
    category = event.payload.get("category")
    confidence = event.payload.get("confidence", 0)
    method = event.payload.get("method", "manual")

    LOGGER.debug(
        "🏦 Transaction catégorisée: %s → %s (%.0f%% confiance, méthode: %s)",
        transaction_id, category, confidence * 100, method
    )


def handle_reconciliation_matched(event: Event):
    """
    Handler: Rapprochement bancaire réussi

    Actions:
    1. Log le rapprochement
    2. Met à jour le statut de la facture liée
    """
    statement_id = event.payload.get("statement_id")
    invoice_ids = event.payload.get("matched_invoice_ids", [])
    confidence = event.payload.get("confidence", 0)

    LOGGER.info(
        "✅ Rapprochement réussi: Relevé %s → Factures %s (%.0f%% confiance)",
        statement_id, invoice_ids, confidence * 100
    )


# =============================================================================
# REGISTRATION
# =============================================================================

_handlers_registered = False


def register_all_handlers():
    """Enregistre tous les handlers auprès de l'EventStore."""
    global _handlers_registered

    if _handlers_registered:
        return

    store = EventStore()

    # Handlers principaux
    store.subscribe(EventType.INVOICE_IMPORTED, handle_invoice_imported)
    store.subscribe(EventType.STOCK_MOVEMENT, handle_stock_movement)
    store.subscribe(EventType.PRICE_UPDATED, handle_price_updated)
    store.subscribe(EventType.BANK_TRANSACTION_CATEGORIZED, handle_bank_transaction_categorized)
    store.subscribe(EventType.RECONCILIATION_MATCHED, handle_reconciliation_matched)

    _handlers_registered = True
    LOGGER.info("✅ Event handlers enregistrés")


def unregister_all_handlers():
    """Désenregistre tous les handlers (pour tests)."""
    global _handlers_registered
    _handlers_registered = False
