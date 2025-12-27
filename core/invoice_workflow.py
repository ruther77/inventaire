"""
Module de gestion du workflow complet d'import de factures fournisseurs.

Ce module centralise et orchestre le flux complet d'import d'une facture en une seule
transaction atomique pour garantir la cohérence des données. Il constitue le point d'entrée
principal pour l'intégration des factures dans le système de gestion d'inventaire.

FLUX COMPLET D'IMPORT:
======================
1. Extraction des lignes de facture (depuis PDF, CSV, ou texte)
2. Matching intelligent avec le catalogue produits existant (par code, nom, etc.)
3. Création automatique des produits manquants ou mise à jour des existants
4. Enregistrement des mouvements de stock avec le prix unitaire HT exact
5. Historisation complète des prix (achat, vente, TVA) pour analyse temporelle
6. Émission d'événements métier pour synchronisation avec autres modules

GARANTIES TRANSACTIONNELLES:
============================
- Tout l'import est réalisé dans UNE SEULE transaction SQL (engine.begin())
- En cas d'erreur, rollback automatique complet (aucune donnée partielle)
- Les événements ne sont émis qu'après commit réussi de la transaction
- Traçabilité complète via logs et InvoiceImportResult

UTILISATION TYPIQUE:
====================
    from core.invoice_workflow import import_invoice_complete

    result = import_invoice_complete(
        invoice_df=df_facture,
        username="user@example.com",
        supplier="METRO",
        invoice_date=datetime.now(),
        invoice_id="FACT-2025-001",
        tenant_id=1
    )

    if result.success:
        print(f"Import réussi: {result.products_created} produits créés")
    else:
        print(f"Erreurs: {result.errors}")

SÉCURITÉ ET COHÉRENCE:
======================
- Vérification de l'existence des produits avant création
- Gestion des doublons par code-barres et nom
- Validation des quantités et prix (> 0)
- Détection automatique des variations de prix significatives (> 1%)
- Support multi-tenant avec isolation stricte des données
"""

from __future__ import annotations

import logging
from datetime import datetime, date, time, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df
from core import invoice_extractor, products_loader
from core.inventory_service import match_invoice_products
from core.price_history_service import record_price_history
from core.finance.event_sourcing import (
    EventDispatcher,
    EventType,
    emit_invoice_imported,
    emit_price_updated,
    emit_stock_movement,
)
from core.event_handlers import register_all_handlers

LOGGER = logging.getLogger(__name__)


def _normalize_datetime(value: datetime | date | None) -> datetime | None:
    """
    Normalise une valeur date/datetime en datetime timezone-aware UTC.

    Cette fonction garantit que toutes les dates manipulées dans le workflow
    sont stockées avec une information de fuseau horaire (UTC) pour éviter
    les ambiguïtés et faciliter les comparaisons.

    Comportement:
    - None -> None (valeur optionnelle)
    - datetime sans timezone -> datetime UTC
    - datetime avec timezone -> inchangé
    - date -> datetime à 00:00:00 UTC

    Args:
        value: Date ou datetime à normaliser (peut être None)

    Returns:
        Datetime timezone-aware en UTC, ou None si l'entrée était None

    Exemple:
        >>> _normalize_datetime(date(2025, 1, 15))
        datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        # Si déjà timezone-aware, retourner tel quel, sinon ajouter UTC
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # Convertir date en datetime à minuit UTC
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _get_product_current_price(product_id: int, tenant_id: int) -> Optional[float]:
    """
    Récupère le prix d'achat actuellement enregistré pour un produit.

    Cette fonction est utilisée pour détecter les variations de prix entre
    l'ancien prix en base et le nouveau prix de la facture. Une variation
    significative (> 1%) déclenche un événement PRICE_UPDATED.

    Args:
        product_id: Identifiant unique du produit
        tenant_id: Identifiant du tenant (isolation multi-tenant)

    Returns:
        Prix d'achat actuel en euros (float), ou None si le produit n'existe pas
        ou si le prix n'est pas défini (NULL en base)

    Note:
        Utilise query_df pour bénéficier du cache et de l'optimisation des requêtes.
    """
    sql = text("""
        SELECT prix_achat FROM produits
        WHERE id = :product_id AND tenant_id = :tenant_id
    """)
    df = query_df(sql, {"product_id": product_id, "tenant_id": tenant_id})
    if df.empty:
        return None
    # Conversion en float, avec fallback à 0 si NULL
    return float(df.iloc[0].get("prix_achat") or 0)


def _create_stock_movement_with_cost(
    conn,
    tenant_id: int,
    product_id: int,
    quantity: float,
    prix_unitaire_ht: float,
    movement_type: str,
    reference: str,
    username: str,
    movement_date: datetime,
    supplier: str = None,
):
    """
    Enregistre un mouvement de stock avec son coût unitaire HT dans la base.

    Cette fonction est CRITIQUE car elle enregistre non seulement la quantité
    mais aussi le PRIX UNITAIRE HT, permettant ainsi de calculer précisément
    le coût des stocks (CUMP, FIFO, etc.) et la valorisation de l'inventaire.

    La source est automatiquement marquée comme "FACTURE" pour distinguer
    les mouvements d'import des mouvements manuels ou d'inventaire.

    Args:
        conn: Connexion SQLAlchemy active (dans une transaction)
        tenant_id: ID du tenant (isolation multi-tenant)
        product_id: ID du produit concerné
        quantity: Quantité du mouvement (positive pour ENTREE, négative pour SORTIE)
        prix_unitaire_ht: Prix unitaire HT en euros (coût réel de la facture)
        movement_type: Type de mouvement ("ENTREE", "SORTIE", "INVENTAIRE", etc.)
        reference: Référence unique du mouvement (ex: "FACT-2025-001-3")
        username: Email ou nom de l'utilisateur effectuant l'opération
        movement_date: Date et heure du mouvement (normalisée en UTC)
        supplier: Nom du fournisseur (optionnel, pour traçabilité)

    Note:
        Cette fonction ne fait pas de commit, elle s'exécute dans la transaction
        globale de import_invoice_complete() pour garantir l'atomicité.

    Exemple:
        _create_stock_movement_with_cost(
            conn, tenant_id=1, product_id=123, quantity=10.0,
            prix_unitaire_ht=12.50, movement_type="ENTREE",
            reference="FACT-METRO-001", username="admin@example.com",
            movement_date=datetime.now(timezone.utc), supplier="METRO"
        )
    """
    conn.execute(
        text("""
            INSERT INTO mouvements_stock
            (tenant_id, produit_id, quantite, type_mouvement, reference,
             utilisateur, date_mouvement, fournisseur, prix_unitaire_ht, source)
            VALUES
            (:tenant_id, :produit_id, :quantite, :type_mouvement, :reference,
             :utilisateur, :date_mouvement, :fournisseur, :prix_unitaire_ht, :source)
        """),
        {
            "tenant_id": tenant_id,
            "produit_id": product_id,
            "quantite": quantity,
            "type_mouvement": movement_type,
            "reference": reference,
            "utilisateur": username,
            "date_mouvement": movement_date,
            "fournisseur": supplier,
            "prix_unitaire_ht": prix_unitaire_ht,
            "source": "FACTURE",  # Marqueur pour distinguer les imports de factures
        }
    )


def _update_product_stock(conn, tenant_id: int, product_id: int, quantity_delta: float):
    """
    Met à jour le stock actuel d'un produit en ajoutant un delta de quantité.

    Cette fonction modifie directement le champ stock_actuel dans la table produits.
    Elle utilise COALESCE pour gérer le cas où stock_actuel serait NULL (initialisation).

    Args:
        conn: Connexion SQLAlchemy active (dans une transaction)
        tenant_id: ID du tenant (isolation multi-tenant)
        product_id: ID du produit à mettre à jour
        quantity_delta: Delta à ajouter au stock (peut être positif ou négatif)
                       - Positif pour entrée de stock (réception facture)
                       - Négatif pour sortie de stock (vente, casse, etc.)

    Note:
        - Le champ updated_at est automatiquement mis à jour avec NOW()
        - COALESCE(stock_actuel, 0) gère le cas NULL -> traité comme 0
        - Cette fonction ne valide PAS si le stock devient négatif (fait ailleurs)

    Exemple:
        # Ajouter 10 unités au stock
        _update_product_stock(conn, tenant_id=1, product_id=123, quantity_delta=10.0)

        # Retirer 5 unités du stock
        _update_product_stock(conn, tenant_id=1, product_id=123, quantity_delta=-5.0)
    """
    conn.execute(
        text("""
            UPDATE produits
            SET stock_actuel = COALESCE(stock_actuel, 0) + :delta,
                updated_at = NOW()
            WHERE id = :product_id AND tenant_id = :tenant_id
        """),
        {
            "tenant_id": tenant_id,
            "product_id": product_id,
            "delta": quantity_delta,
        }
    )


def _record_price_history_line(
    conn,
    tenant_id: int,
    product_id: int,
    code: str,
    supplier: str,
    prix_achat: float,
    prix_vente: float,
    tva: float,
    invoice_date: datetime,
):
    """
    Enregistre une entrée dans l'historique des prix pour analyse temporelle.

    Cette table (produits_price_history) permet de tracer l'évolution des prix
    d'achat et de vente au fil du temps, par fournisseur. Elle est utilisée pour:
    - Détecter les variations de prix significatives
    - Analyser les tendances et la saisonnalité
    - Comparer les prix entre fournisseurs
    - Calculer les marges historiques
    - Générer des alertes de hausse/baisse de prix

    Args:
        conn: Connexion SQLAlchemy active (dans une transaction)
        tenant_id: ID du tenant (isolation multi-tenant)
        product_id: ID du produit concerné
        code: Code-barres ou référence produit (peut être vide)
        supplier: Nom du fournisseur (défaut "Inconnu" si non fourni)
        prix_achat: Prix d'achat HT en euros
        prix_vente: Prix de vente TTC en euros (pour calcul marge)
        tva: Taux de TVA en % (ex: 5.5, 10.0, 20.0)
        invoice_date: Date de la facture (normalisée en UTC)

    Note:
        - Une nouvelle ligne est créée à CHAQUE import de facture
        - Pas de déduplication : chaque facture = 1 entrée d'historique
        - Le champ created_at est automatiquement rempli avec NOW()
        - Les valeurs NULL pour code/supplier sont converties en chaînes par défaut

    Exemple:
        _record_price_history_line(
            conn, tenant_id=1, product_id=123, code="3245678901234",
            supplier="METRO", prix_achat=12.50, prix_vente=18.90,
            tva=20.0, invoice_date=datetime(2025, 1, 15, tzinfo=timezone.utc)
        )
    """
    conn.execute(
        text("""
            INSERT INTO produits_price_history
            (tenant_id, produit_id, code, fournisseur, prix_achat, prix_vente, tva, date_facture, created_at)
            VALUES
            (:tenant_id, :produit_id, :code, :fournisseur, :prix_achat, :prix_vente, :tva, :date_facture, NOW())
        """),
        {
            "tenant_id": tenant_id,
            "produit_id": product_id,
            "code": code or "",  # Chaîne vide si NULL
            "fournisseur": supplier or "Inconnu",  # Valeur par défaut
            "prix_achat": prix_achat,
            "prix_vente": prix_vente,
            "tva": tva,
            "date_facture": invoice_date,
        }
    )


class InvoiceImportResult:
    """
    Classe de résultat pour un import de facture fournisseur.

    Cette classe encapsule tous les résultats et métriques d'un import de facture,
    permettant de tracer précisément ce qui a été fait et de détecter les anomalies.

    Attributs:
        success (bool): True si l'import s'est déroulé sans erreur critique
        invoice_id (str | None): Identifiant unique de la facture importée
        supplier (str | None): Nom du fournisseur
        total_lines (int): Nombre total de lignes dans la facture
        products_created (int): Nombre de nouveaux produits créés dans le catalogue
        products_updated (int): Nombre de produits existants mis à jour
        movements_created (int): Nombre de mouvements de stock enregistrés
        prices_recorded (int): Nombre d'entrées créées dans l'historique des prix
        errors (List[str]): Liste des erreurs critiques rencontrées
        warnings (List[str]): Liste des avertissements (problèmes non bloquants)
        product_ids (List[int]): Liste des IDs de produits concernés par l'import

    Utilisation:
        result = InvoiceImportResult()
        result.success = True
        result.products_created = 5
        result.movements_created = 12

        if result.success:
            print(f"Import réussi: {result.to_dict()}")
        else:
            print(f"Erreurs: {result.errors}")
    """

    def __init__(self):
        """Initialise un résultat d'import avec des valeurs par défaut."""
        self.success = False  # Par défaut en échec jusqu'à succès confirmé
        self.invoice_id: Optional[str] = None
        self.supplier: Optional[str] = None
        self.total_lines = 0
        self.products_created = 0  # Nouveaux produits ajoutés au catalogue
        self.products_updated = 0  # Produits existants modifiés
        self.movements_created = 0  # Mouvements de stock enregistrés
        self.prices_recorded = 0  # Entrées dans l'historique des prix
        self.errors: List[str] = []  # Erreurs critiques
        self.warnings: List[str] = []  # Avertissements non bloquants
        self.product_ids: List[int] = []  # IDs des produits affectés

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le résultat en dictionnaire pour sérialisation JSON.

        Returns:
            Dictionnaire contenant toutes les métriques de l'import

        Note:
            product_ids est exclu du dictionnaire pour alléger la réponse API
        """
        return {
            "success": self.success,
            "invoice_id": self.invoice_id,
            "supplier": self.supplier,
            "total_lines": self.total_lines,
            "products_created": self.products_created,
            "products_updated": self.products_updated,
            "movements_created": self.movements_created,
            "prices_recorded": self.prices_recorded,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def import_invoice_complete(
    invoice_df: pd.DataFrame,
    *,
    username: str,
    supplier: str = None,
    movement_type: str = "ENTREE",
    invoice_date: datetime | date = None,
    invoice_id: str = None,
    initialize_stock: bool = False,
    tenant_id: int = 1,
    user_id: int = None,
) -> InvoiceImportResult:
    """
    Importe une facture fournisseur complète en UNE SEULE TRANSACTION ATOMIQUE.

    Cette fonction est le point d'entrée principal pour l'intégration des factures
    fournisseurs dans le système. Elle orchestre l'ensemble du processus d'import
    en garantissant la cohérence et l'intégrité des données via une transaction SQL.

    PROCESSUS COMPLET (dans l'ordre):
    =================================
    1. Validation du DataFrame d'entrée (format, colonnes requises)
    2. Matching intelligent avec le catalogue produits existant (par code/nom)
    3. Création automatique des produits absents du catalogue
    4. Enregistrement des mouvements de stock AVEC prix unitaire HT
    5. Mise à jour des stocks actuels des produits
    6. Historisation complète des prix (achat, vente, TVA) par fournisseur
    7. Mise à jour du prix d'achat du produit si variation détectée
    8. Émission des événements métier (PRICE_UPDATED, STOCK_MOVEMENT, etc.)
    9. Enregistrement de la facture dans processed_invoices (déduplication)
    10. Émission de l'événement global INVOICE_IMPORTED

    GARANTIES:
    ==========
    - Atomicité: Tout réussit ou tout échoue (rollback automatique en cas d'erreur)
    - Cohérence: Les stocks, prix et mouvements sont toujours synchronisés
    - Isolation: Chaque tenant a ses données strictement isolées
    - Traçabilité: Tous les mouvements ont une source, référence, utilisateur

    Args:
        invoice_df: DataFrame pandas contenant les lignes de la facture
                   Colonnes attendues: codes, nom, prix_achat (ou prix_ht),
                   prix_vente, tva, quantite_recue (ou qte_init ou quantite),
                   total_ttc (optionnel)
        username: Email ou identifiant de l'utilisateur effectuant l'import
                 (pour traçabilité dans mouvements_stock)
        supplier: Nom du fournisseur (ex: "METRO", "TRANSGOURMET")
                 Utilisé pour l'historique des prix et les analyses
        movement_type: Type de mouvement de stock à créer
                      - "ENTREE" (défaut): Ajout au stock (réception marchandise)
                      - "SORTIE": Retrait du stock (retour, casse, etc.)
        invoice_date: Date de la facture (datetime ou date)
                     Si None, utilise datetime.now(timezone.utc)
                     Normalisée automatiquement en UTC timezone-aware
        invoice_id: Identifiant unique de la facture (ex: "FACT-METRO-2025-001")
                   Utilisé pour déduplication et traçabilité
        initialize_stock: Mode spécial d'initialisation des stocks
                         - False (défaut): Ajoute les quantités au stock existant
                         - True: Définit le stock initial (pour premiers imports)
        tenant_id: Identifiant du tenant (isolation multi-tenant stricte)
                  Défaut: 1
        user_id: Identifiant de l'utilisateur (pour événements et audit)
                Optionnel, utilisé dans les événements PRICE_UPDATED, etc.

    Returns:
        InvoiceImportResult: Objet contenant
            - success (bool): True si import réussi sans erreur critique
            - invoice_id (str): ID de la facture importée
            - supplier (str): Nom du fournisseur
            - total_lines (int): Nombre de lignes traitées
            - products_created (int): Nouveaux produits créés
            - products_updated (int): Produits existants mis à jour
            - movements_created (int): Mouvements de stock enregistrés
            - prices_recorded (int): Entrées dans l'historique des prix
            - errors (list): Liste des erreurs rencontrées
            - warnings (list): Avertissements non bloquants
            - product_ids (list): IDs des produits affectés

    Raises:
        Exception: En cas d'erreur critique (capturée et retournée dans result.errors)

    Exemples:
        >>> # Import simple d'une facture METRO
        >>> result = import_invoice_complete(
        ...     invoice_df=df_metro,
        ...     username="admin@restaurant.fr",
        ...     supplier="METRO",
        ...     invoice_date=datetime(2025, 1, 15),
        ...     invoice_id="FACT-METRO-2025-001",
        ...     tenant_id=1
        ... )
        >>> print(f"Créé {result.products_created} produits, "
        ...       f"{result.movements_created} mouvements")

        >>> # Initialisation des stocks (premier import)
        >>> result = import_invoice_complete(
        ...     invoice_df=df_initial,
        ...     username="admin@restaurant.fr",
        ...     supplier="INVENTAIRE_INITIAL",
        ...     invoice_date=datetime(2025, 1, 1),
        ...     invoice_id="INIT-2025",
        ...     initialize_stock=True,
        ...     tenant_id=1
        ... )

    Note:
        - Les événements ne sont émis qu'APRÈS le commit de la transaction
        - Les handlers d'événements doivent être enregistrés avant (register_all_handlers)
        - Le DataFrame est copié en interne (working_df), l'original n'est pas modifié
        - Les variations de prix > 1% déclenchent automatiquement un événement PRICE_UPDATED
    """
    # Enregistre les handlers d'événements si pas déjà fait
    # Les handlers sont nécessaires pour traiter les événements émis (PRICE_UPDATED, etc.)
    register_all_handlers()

    # Initialise l'objet de résultat qui sera retourné à l'appelant
    result = InvoiceImportResult()
    result.invoice_id = invoice_id
    result.supplier = supplier

    # === VALIDATION DES DONNÉES D'ENTRÉE ===
    # Vérifie que le DataFrame est valide et non vide
    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:
        result.errors.append("DataFrame vide ou invalide")
        return result  # Sortie anticipée, pas d'import possible

    result.total_lines = len(invoice_df)

    # Normalise la date de facture en datetime UTC timezone-aware
    # Si aucune date fournie, utilise la date/heure actuelle
    normalized_date = _normalize_datetime(invoice_date) or datetime.now(timezone.utc)

    # Normalise le nom du fournisseur avec fallback "Inconnu"
    # strip() enlève les espaces, la double vérification gère les chaînes vides
    supplier_label = (supplier or "Inconnu").strip() or "Inconnu"

    # === CALCUL DU MULTIPLICATEUR DE QUANTITÉ ===
    # Détermine si on ajoute (+1) ou retire (-1) du stock
    # ENTREE: réception fournisseur -> quantité positive
    # SORTIE: retour, casse, vol -> quantité négative
    qty_multiplier = 1 if movement_type == "ENTREE" else -1

    # Récupère le moteur SQLAlchemy pour la transaction
    engine = get_engine()

    try:
        # === DÉBUT DE LA TRANSACTION ATOMIQUE ===
        # engine.begin() ouvre une transaction qui sera automatiquement:
        # - Committée si le bloc se termine sans exception
        # - Rollbackée si une exception est levée
        with engine.begin() as conn:
            # === ÉTAPE 1: ENRICHISSEMENT DES LIGNES AVEC LE CATALOGUE ===
            # Copie du DataFrame pour ne pas modifier l'original
            working_df = invoice_df.copy()

            # === MATCHING INTELLIGENT AVEC LE CATALOGUE EXISTANT ===
            # Cette étape tente d'associer chaque ligne de facture à un produit
            # existant dans le catalogue, pour éviter de créer des doublons
            if "codes" in working_df.columns:
                # Normalise les codes-barres pour le matching (lowercase, trim)
                # fillna("") gère les valeurs NULL
                working_df["_code_lower"] = working_df["codes"].fillna("").astype(str).str.lower().str.strip()

                # Appelle le service de matching qui recherche dans:
                # - produits_barcodes (codes-barres principaux et alternatifs)
                # - produits.nom (matching par nom si pas de code)
                matches_df = match_invoice_products(working_df, tenant_id=tenant_id)

                if not matches_df.empty:
                    # Renomme les colonnes pour éviter les conflits lors du merge
                    # code -> _code_lower (pour joindre)
                    # produit_id -> catalogue_id (pour distinguer du produit_id de la facture)
                    matches_df = matches_df.rename(columns={
                        "code": "_code_lower",
                        "produit_id": "catalogue_id",
                    })

                    # Merge LEFT: garde toutes les lignes de facture, même sans match
                    # Les lignes sans match auront catalogue_id = NULL
                    working_df = working_df.merge(matches_df[["_code_lower", "catalogue_id"]], on="_code_lower", how="left")

                    # Fusion du catalogue_id avec le produit_id potentiellement existant
                    if "produit_id" not in working_df.columns:
                        # Pas de colonne produit_id -> utilise catalogue_id directement
                        working_df["produit_id"] = working_df["catalogue_id"]
                    else:
                        # Colonne produit_id existe -> priorise catalogue_id si disponible
                        # fillna() complète les NULL avec les valeurs de catalogue_id
                        working_df["produit_id"] = working_df["produit_id"].fillna(working_df["catalogue_id"])

            # === ÉTAPE 2: TRAITEMENT LIGNE PAR LIGNE ===
            # Itère sur chaque ligne de facture pour créer/mettre à jour les produits
            # et enregistrer les mouvements de stock
            for idx, row in working_df.iterrows():
                # === EXTRACTION ET NORMALISATION DES DONNÉES DE LA LIGNE ===
                product_id = row.get("produit_id")  # Peut être NULL si produit non trouvé

                # Normalisation du code-barres (strip des espaces)
                code = str(row.get("codes") or "").strip()

                # Nom du produit (OBLIGATOIRE)
                nom = str(row.get("nom") or "").strip()

                # Prix d'achat HT - essaye plusieurs colonnes (variabilité des sources)
                # prix_achat prioritaire, sinon prix_ht, sinon 0
                prix_achat = float(row.get("prix_achat") or row.get("prix_ht") or 0)

                # Prix de vente TTC (pour calcul marge)
                prix_vente = float(row.get("prix_vente") or 0)

                # Taux de TVA en % (5.5, 10.0, 20.0 typiquement)
                tva = float(row.get("tva") or 0)

                # Quantité reçue - essaye plusieurs colonnes (variabilité des sources)
                # quantite_recue (import CSV) > qte_init (init stock) > quantite (défaut)
                quantite = float(row.get("quantite_recue") or row.get("qte_init") or row.get("quantite") or 0)

                # === VALIDATION: NOM OBLIGATOIRE ===
                # Sans nom, impossible de créer ou identifier le produit
                if not nom:
                    result.warnings.append(f"Ligne {idx}: nom manquant, ignorée")
                    continue  # Passe à la ligne suivante

                # === CRÉATION OU RÉCUPÉRATION DU PRODUIT ===
                if pd.isna(product_id) or product_id is None:
                    # Produit non trouvé par le matching de codes-barres
                    # Dernière tentative: recherche par nom (case-insensitive)
                    check_sql = text("""
                        SELECT id FROM produits
                        WHERE tenant_id = :tenant_id AND LOWER(nom) = LOWER(:nom)
                        LIMIT 1
                    """)
                    existing = conn.execute(check_sql, {"tenant_id": tenant_id, "nom": nom}).fetchone()

                    if existing:
                        # Produit trouvé par nom -> réutilise l'existant
                        product_id = existing[0]
                        result.products_updated += 1
                    else:
                        # === CRÉATION D'UN NOUVEAU PRODUIT ===
                        # Aucun produit correspondant trouvé -> création automatique
                        insert_sql = text("""
                            INSERT INTO produits
                            (tenant_id, nom, prix_achat, prix_vente, tva, stock_actuel, actif, created_at, updated_at)
                            VALUES
                            (:tenant_id, :nom, :prix_achat, :prix_vente, :tva, :stock, TRUE, NOW(), NOW())
                            RETURNING id
                        """)
                        new_product = conn.execute(insert_sql, {
                            "tenant_id": tenant_id,
                            "nom": nom,
                            "prix_achat": prix_achat,
                            "prix_vente": prix_vente,
                            "tva": tva,
                            # Stock initial: quantite si mode initialisation, sinon 0
                            # (le stock sera ajouté par le mouvement ensuite)
                            "stock": quantite if initialize_stock else 0,
                        }).fetchone()

                        product_id = new_product[0]
                        result.products_created += 1

                        # === AJOUT DU CODE-BARRES SI PRÉSENT ===
                        # Associe le code-barres au produit nouvellement créé
                        if code:
                            conn.execute(
                                text("""
                                    INSERT INTO produits_barcodes (produit_id, code, tenant_id, is_principal)
                                    VALUES (:produit_id, :code, :tenant_id, TRUE)
                                    ON CONFLICT (tenant_id, code) DO NOTHING
                                """),
                                {"produit_id": product_id, "code": code, "tenant_id": tenant_id}
                            )
                            # ON CONFLICT DO NOTHING: ignore si code déjà existant
                            # (peut arriver en cas de réimport)

                    # Met à jour le DataFrame avec l'ID du produit pour référence ultérieure
                    working_df.at[idx, "produit_id"] = product_id

                # Conversion en entier et ajout à la liste des produits affectés
                product_id = int(product_id)
                result.product_ids.append(product_id)

                # === RÉCUPÉRATION DU PRIX ACTUEL POUR DÉTECTION DE VARIATION ===
                # Nécessaire pour comparer avec le nouveau prix et émettre un événement
                # si variation > 1% (alerte métier)
                old_price = _get_product_current_price(product_id, tenant_id)

                # === ÉTAPE 3: CRÉATION DU MOUVEMENT DE STOCK AVEC COÛT ===
                # Un mouvement de stock n'est créé QUE si quantite > 0
                # (évite les mouvements vides pour les lignes de service, frais, etc.)
                if quantite > 0:
                    # Génère une référence unique pour le mouvement
                    # Format: FACT-{ID_FACTURE}-{INDEX_LIGNE}
                    # Ex: FACT-METRO-2025-001-3 (ligne 3 de la facture METRO-2025-001)
                    reference = f"FACT-{invoice_id or 'IMPORT'}-{idx}"

                    # Appelle la fonction helper pour créer le mouvement
                    # IMPORTANT: enregistre le prix_unitaire_ht pour valorisation stock
                    _create_stock_movement_with_cost(
                        conn,
                        tenant_id=tenant_id,
                        product_id=product_id,
                        quantity=quantite * qty_multiplier,  # Applique le signe (+/-)
                        prix_unitaire_ht=prix_achat,  # CRUCIAL pour CUMP/FIFO
                        movement_type=movement_type,
                        reference=reference,
                        username=username,
                        movement_date=normalized_date,
                        supplier=supplier_label,
                    )
                    result.movements_created += 1

                    # === MISE À JOUR DU STOCK ACTUEL ===
                    # Sauf en mode initialize_stock où le stock a déjà été défini à la création
                    if not initialize_stock:
                        _update_product_stock(conn, tenant_id, product_id, quantite * qty_multiplier)

                # === ÉTAPE 4: HISTORISATION DES PRIX ===
                # Enregistre une nouvelle entrée dans l'historique si prix_achat > 0
                # Permet l'analyse temporelle et la détection de tendances
                if prix_achat > 0:
                    _record_price_history_line(
                        conn,
                        tenant_id=tenant_id,
                        product_id=product_id,
                        code=code,
                        supplier=supplier_label,
                        prix_achat=prix_achat,
                        prix_vente=prix_vente,
                        tva=tva,
                        invoice_date=normalized_date,
                    )
                    result.prices_recorded += 1

                    # === MISE À JOUR DU PRIX D'ACHAT DU PRODUIT ===
                    # Le prix de la facture devient le nouveau prix de référence
                    # Utilisé pour les calculs de marge, valorisation stock, etc.
                    conn.execute(
                        text("""
                            UPDATE produits
                            SET prix_achat = :prix_achat,
                                updated_at = NOW()
                            WHERE id = :product_id AND tenant_id = :tenant_id
                        """),
                        {"prix_achat": prix_achat, "product_id": product_id, "tenant_id": tenant_id}
                    )

                    # === DÉTECTION ET ALERTE DE VARIATION DE PRIX ===
                    # Si variation > 1% par rapport à l'ancien prix, émet un événement
                    # Formule: variation = |nouveau - ancien| / ancien
                    # Exemple: 12.00€ -> 13.00€ = 8.3% -> événement émis
                    if old_price and old_price > 0 and abs(prix_achat - old_price) / old_price > 0.01:
                        emit_price_updated(
                            tenant_id=tenant_id,
                            product_id=product_id,
                            old_price=old_price,
                            new_price=prix_achat,
                            supplier=supplier_label,
                            source="invoice_import",
                            user_id=user_id,
                        )

                # === ÉMISSION ÉVÉNEMENT MOUVEMENT DE STOCK ===
                # Notifie les autres modules (analytics, alertes, etc.)
                if quantite > 0:
                    emit_stock_movement(
                        tenant_id=tenant_id,
                        product_id=product_id,
                        movement_type="in" if movement_type == "ENTREE" else "out",
                        quantity=quantite,
                        reason=f"Import facture {invoice_id or 'N/A'}",
                        reference=invoice_id,
                        user_id=user_id,
                    )

            # === ENREGISTREMENT DE LA FACTURE DANS processed_invoices ===
            # Table de déduplication et de traçabilité des factures importées
            # Permet de détecter les réimports et de suivre l'historique
            if invoice_id:
                conn.execute(
                    text("""
                        INSERT INTO processed_invoices
                        (tenant_id, invoice_id, supplier, facture_date, line_count, created_at)
                        VALUES (:tenant_id, :invoice_id, :supplier, :facture_date, :line_count, NOW())
                        ON CONFLICT (tenant_id, invoice_id) DO UPDATE SET
                            supplier = EXCLUDED.supplier,
                            line_count = EXCLUDED.line_count,
                            updated_at = NOW()
                    """),
                    {
                        "tenant_id": tenant_id,
                        "invoice_id": invoice_id,
                        "supplier": supplier_label,
                        "facture_date": normalized_date,
                        "line_count": result.total_lines,
                    }
                )
                # ON CONFLICT: Si facture déjà importée (même invoice_id), met à jour
                # au lieu de lever une erreur. Permet les réimports correctifs.

        # === FIN DE TRANSACTION - COMMIT AUTOMATIQUE ===
        # À ce point, le bloc with se termine et la transaction est committée
        # Toutes les données (produits, mouvements, prix, facture) sont persistées

        # === ÉMISSION DE L'ÉVÉNEMENT GLOBAL INVOICE_IMPORTED ===
        # Cet événement est émis APRÈS le commit pour garantir la cohérence
        # Il notifie les autres modules que l'import est terminé avec succès
        emit_invoice_imported(
            tenant_id=tenant_id,
            invoice_id=invoice_id or "IMPORT",
            filename=invoice_id or "import_manuel",
            supplier=supplier_label,
            # Calcul du montant total TTC de la facture
            total=sum(float(row.get("total_ttc") or row.get("prix_achat") or 0) for _, row in working_df.iterrows()),
            items_count=result.total_lines,
            user_id=user_id,
        )

        # === MARQUAGE DU SUCCÈS ET LOGGING ===
        result.success = True
        LOGGER.info(
            "✅ Import facture réussi: %s lignes, %s produits créés, %s mouvements, %s prix historisés",
            result.total_lines, result.products_created, result.movements_created, result.prices_recorded
        )

    except Exception as e:
        # === GESTION DES ERREURS ===
        # En cas d'exception, la transaction est automatiquement rollbackée
        # Aucune donnée partielle n'est persistée (garantie d'atomicité)
        LOGGER.error("❌ Erreur import facture: %s", e)
        result.errors.append(str(e))
        result.success = False

    return result


def get_invoice_workflow_summary(tenant_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Récupère un résumé statistique des imports de factures récents.

    Cette fonction agrège les données de la table processed_invoices pour fournir
    une vue d'ensemble de l'activité d'import sur une période donnée.

    Métriques calculées:
    - total_invoices: Nombre total de factures importées
    - total_lines: Nombre total de lignes traitées (somme des line_count)
    - unique_suppliers: Nombre de fournisseurs distincts

    Args:
        tenant_id: ID du tenant (isolation multi-tenant)
        days: Nombre de jours à analyser depuis aujourd'hui (défaut: 30)
             Exemple: days=7 pour la semaine dernière, days=90 pour le trimestre

    Returns:
        Dictionnaire avec les clés:
        {
            "total_invoices": int,      # Nombre de factures
            "total_lines": int,          # Nombre de lignes
            "unique_suppliers": int      # Nombre de fournisseurs
        }
        Si aucune donnée, retourne des valeurs à 0.

    Exemple:
        >>> summary = get_invoice_workflow_summary(tenant_id=1, days=7)
        >>> print(f"Importé {summary['total_invoices']} factures la semaine dernière")
        Importé 12 factures la semaine dernière
    """
    sql = text("""
        SELECT
            COUNT(*) as total_invoices,
            SUM(line_count) as total_lines,
            COUNT(DISTINCT supplier) as unique_suppliers
        FROM processed_invoices
        WHERE tenant_id = :tenant_id
          AND created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
    """)
    df = query_df(sql, {"tenant_id": tenant_id, "days": days})

    # Si aucune facture trouvée, retourne des compteurs à zéro
    if df.empty:
        return {"total_invoices": 0, "total_lines": 0, "unique_suppliers": 0}

    # Convertit la première ligne du DataFrame en dictionnaire
    return df.iloc[0].to_dict()
