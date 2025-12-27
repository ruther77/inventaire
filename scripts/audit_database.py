#!/usr/bin/env python3
"""
Module d'audit complet de la cohérence et qualité des données de la base.

Ce script permet de:
- Analyser toutes les tables principales de la base de données
- Détecter les erreurs de cohérence (NULL invalides, FK orphelines, etc.)
- Identifier les problèmes de qualité (stocks négatifs, marges négatives, etc.)
- Vérifier les contraintes métier (prix, quantités, dates)
- Détecter les doublons potentiels
- Générer un rapport détaillé avec recommandations
- Sauvegarder le rapport dans docs/AUDIT_DATABASE_REPORT.md

Tables auditées:
    - produits: Catalogue de produits de l'épicerie
    - finance_transactions: Transactions financières
    - finance_accounts, finance_categories, finance_entities
    - mouvements_stock: Historique des mouvements de stock
    - restaurant_plats, restaurant_ingredients, restaurant_depenses
    - processed_invoices: Factures traitées
    - produits_barcodes: Codes-barres associés aux produits
    - produits_price_history: Historique des prix
    - vendor_aliases: Alias de fournisseurs
    - tenants, app_users
    - Tables additionnelles (supplier_scores, anomalies, etc.)

Types d'erreurs détectées:
    ERREURS CRITIQUES (bloquantes):
    - Valeurs NULL sur champs requis (nom, prix, montant, etc.)
    - Clés étrangères orphelines (références invalides)
    - Stocks négatifs
    - Tenants ou entités manquants
    - Utilisateurs sans mot de passe

    AVERTISSEMENTS (à examiner):
    - Doublons potentiels (même nom, même date+montant)
    - Marges négatives (prix_vente < prix_achat)
    - Prix ou montants manquants
    - Données de qualité suspecte (prix > 10000€, stock > 10000)

Usage:
    # Audit complet avec rapport
    python scripts/audit_database.py

    # Le rapport est sauvegardé dans docs/AUDIT_DATABASE_REPORT.md

Variables d'environnement:
    DB_HOST: Hôte PostgreSQL (défaut: localhost)
    DB_PORT: Port PostgreSQL (défaut: 5432)
    DB_NAME: Nom de la base (défaut: epicerie)
    DB_USER: Utilisateur (défaut: postgres)
    DB_PASSWORD: Mot de passe (défaut: postgres)

Prérequis:
    - PostgreSQL avec base de données configurée
    - psycopg2 pour la connexion
    - Accès en lecture sur toutes les tables

Fichiers de sortie:
    - Rapport console (stdout) avec résumé et détails
    - docs/AUDIT_DATABASE_REPORT.md : Rapport complet en markdown

Structure du rapport:
    1. RÉSUMÉ: Nombre d'erreurs, avertissements, statistiques
    2. ERREURS CRITIQUES: Liste détaillée des problèmes bloquants
    3. AVERTISSEMENTS: Problèmes à examiner
    4. STATISTIQUES DES TABLES: Nombre d'enregistrements par table
    5. RECOMMANDATIONS: Actions prioritaires à effectuer

Code de sortie:
    0: Aucune erreur critique
    1: Erreurs critiques détectées
    2: Erreur d'exécution du script

Exemple de sortie:
    AUDIT COMPLET DE LA BASE DE DONNEES
    Date: 2025-01-15T10:30:00

    RÉSUMÉ
    - Erreurs critiques: 5
    - Avertissements: 23
    - Informations: 45

    ERREURS CRITIQUES
    ### Erreur #1
    - Table: produits
    - Catégorie: NULL_NAME
    - Message: 3 produits sans nom
    - Details: [42, 89, 123]

    RECOMMANDATIONS
    ### Priorité HAUTE (Erreurs critiques à corriger)
    - Ajouter les noms manquants dans produits
    - Corriger les stocks négatifs dans produits
    - Corriger les references produit invalides dans mouvements_stock

Notes:
    - L'audit est non-destructif (lecture seule)
    - Temps d'exécution: 10-30 secondes selon la taille de la base
    - Peut être exécuté quotidiennement via cron pour monitoring
    - Les requêtes SQL sont protégées contre les erreurs
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """Etablit une connexion a la base de donnees."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "epicerie"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )


class DatabaseAuditor:
    """Audit complet de la base de donnees."""

    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []

    def log_error(self, table: str, category: str, message: str, details: Any = None):
        self.errors.append({"table": table, "category": category, "message": message, "details": details, "severity": "ERROR"})

    def log_warning(self, table: str, category: str, message: str, details: Any = None):
        self.warnings.append({"table": table, "category": category, "message": message, "details": details, "severity": "WARNING"})

    def log_info(self, table: str, category: str, message: str, details: Any = None):
        self.info.append({"table": table, "category": category, "message": message, "details": details, "severity": "INFO"})

    def safe_execute(self, query: str, table: str = "UNKNOWN") -> List[dict]:
        """Execute une requete de maniere securisee."""
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            self.log_warning(table, "QUERY_ERROR", f"Erreur SQL: {str(e)[:100]}")
            self.conn.rollback()
            return []

    def get_table_count(self, table: str) -> int:
        try:
            self.cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            return self.cursor.fetchone()["cnt"]
        except Exception:
            self.conn.rollback()
            return 0

    def audit_produits(self):
        """Audit de la table produits."""
        table = "produits"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Noms NULL ou vides
        rows = self.safe_execute("SELECT id, nom FROM produits WHERE nom IS NULL OR TRIM(nom) = ''", table)
        if rows:
            self.log_error(table, "NULL_NAME", f"{len(rows)} produits sans nom", [r["id"] for r in rows[:10]])

        # Prix de vente NULL
        rows = self.safe_execute("SELECT id, nom FROM produits WHERE prix_vente IS NULL", table)
        if rows:
            self.log_warning(table, "NULL_PRIX_VENTE", f"{len(rows)} produits sans prix de vente", [{"id": r["id"], "nom": r["nom"]} for r in rows[:10]])

        # Prix d'achat NULL
        rows = self.safe_execute("SELECT id, nom FROM produits WHERE prix_achat IS NULL", table)
        if rows:
            self.log_warning(table, "NULL_PRIX_ACHAT", f"{len(rows)} produits sans prix d'achat", [{"id": r["id"], "nom": r["nom"]} for r in rows[:10]])

        # Stock negatif
        rows = self.safe_execute("SELECT id, nom, stock_actuel FROM produits WHERE stock_actuel < 0", table)
        if rows:
            self.log_error(table, "NEGATIVE_STOCK", f"{len(rows)} produits avec stock negatif", [{"id": r["id"], "nom": r["nom"], "stock": float(r["stock_actuel"])} for r in rows[:10]])

        # Prix de vente < Prix d'achat (marge negative)
        rows = self.safe_execute("""
            SELECT id, nom, prix_vente, prix_achat FROM produits
            WHERE prix_vente IS NOT NULL AND prix_achat IS NOT NULL AND prix_vente < prix_achat
        """, table)
        if rows:
            self.log_warning(table, "NEGATIVE_MARGIN", f"{len(rows)} produits avec marge negative", [{"id": r["id"], "nom": r["nom"], "vente": float(r["prix_vente"]), "achat": float(r["prix_achat"])} for r in rows[:10]])

        # Tenant_id NULL
        rows = self.safe_execute("SELECT id, nom FROM produits WHERE tenant_id IS NULL", table)
        if rows:
            self.log_error(table, "NULL_TENANT", f"{len(rows)} produits sans tenant_id", [r["id"] for r in rows[:10]])

        # Doublons par nom
        rows = self.safe_execute("SELECT nom, COUNT(*) as cnt FROM produits GROUP BY nom, tenant_id HAVING COUNT(*) > 1", table)
        if rows:
            self.log_warning(table, "DUPLICATE_NAMES", f"{len(rows)} noms de produits en double", [{"nom": r["nom"], "count": r["cnt"]} for r in rows[:10]])

    def audit_finance_transactions(self):
        """Audit de la table finance_transactions."""
        table = "finance_transactions"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Label NULL ou vide
        rows = self.safe_execute("SELECT id, label FROM finance_transactions WHERE label IS NULL OR TRIM(label) = ''", table)
        if rows:
            self.log_warning(table, "NULL_LABEL", f"{len(rows)} transactions sans libelle", [r["id"] for r in rows[:10]])

        # Amount NULL
        rows = self.safe_execute("SELECT id FROM finance_transactions WHERE amount IS NULL", table)
        if rows:
            self.log_error(table, "NULL_AMOUNT", f"{len(rows)} transactions sans montant", [r["id"] for r in rows[:10]])

        # Entity_id NULL
        rows = self.safe_execute("SELECT id FROM finance_transactions WHERE entity_id IS NULL", table)
        if rows:
            self.log_error(table, "NULL_ENTITY", f"{len(rows)} transactions sans entity_id", [r["id"] for r in rows[:10]])

        # Account_id invalide (FK orpheline)
        rows = self.safe_execute("""
            SELECT ft.id, ft.account_id FROM finance_transactions ft
            LEFT JOIN finance_accounts fa ON ft.account_id = fa.id
            WHERE ft.account_id IS NOT NULL AND fa.id IS NULL
        """, table)
        if rows:
            self.log_error(table, "ORPHAN_ACCOUNT", f"{len(rows)} transactions avec account_id invalide", [{"id": r["id"], "account_id": r["account_id"]} for r in rows[:10]])

        # Doublons potentiels (meme date, montant, label)
        rows = self.safe_execute("""
            SELECT date_operation, amount, label, COUNT(*) as cnt FROM finance_transactions
            GROUP BY date_operation, amount, label, entity_id HAVING COUNT(*) > 1
        """, table)
        if rows:
            self.log_warning(table, "POTENTIAL_DUPLICATES", f"{len(rows)} groupes de transactions potentiellement en double", [{"date": str(r["date_operation"]), "amount": float(r["amount"]) if r["amount"] else None, "count": r["cnt"]} for r in rows[:10]])

    def audit_mouvements_stock(self):
        """Audit de la table mouvements_stock."""
        table = "mouvements_stock"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Type mouvement NULL (colonne 'type')
        rows = self.safe_execute("SELECT id FROM mouvements_stock WHERE type IS NULL", table)
        if rows:
            self.log_error(table, "NULL_TYPE", f"{len(rows)} mouvements sans type", [r["id"] for r in rows[:10]])

        # Quantite NULL ou 0
        rows = self.safe_execute("SELECT id, quantite FROM mouvements_stock WHERE quantite IS NULL OR quantite = 0", table)
        if rows:
            self.log_warning(table, "ZERO_QUANTITY", f"{len(rows)} mouvements avec quantite nulle", [r["id"] for r in rows[:10]])

        # Produit_id invalide
        rows = self.safe_execute("""
            SELECT ms.id, ms.produit_id FROM mouvements_stock ms
            LEFT JOIN produits p ON ms.produit_id = p.id
            WHERE ms.produit_id IS NOT NULL AND p.id IS NULL
        """, table)
        if rows:
            self.log_error(table, "ORPHAN_PRODUCT", f"{len(rows)} mouvements avec produit_id invalide", [{"id": r["id"], "produit_id": r["produit_id"]} for r in rows[:10]])

    def audit_restaurant_depenses(self):
        """Audit de la table restaurant_depenses."""
        table = "restaurant_depenses"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Libelle NULL ou vide
        rows = self.safe_execute("SELECT id FROM restaurant_depenses WHERE libelle IS NULL OR TRIM(libelle) = ''", table)
        if rows:
            self.log_error(table, "NULL_LIBELLE", f"{len(rows)} depenses sans libelle", [r["id"] for r in rows[:10]])

        # Montant_ht NULL
        rows = self.safe_execute("SELECT id FROM restaurant_depenses WHERE montant_ht IS NULL", table)
        if rows:
            self.log_warning(table, "NULL_MONTANT", f"{len(rows)} depenses sans montant_ht", [r["id"] for r in rows[:10]])

        # Categorie_id invalide
        rows = self.safe_execute("""
            SELECT rd.id, rd.categorie_id FROM restaurant_depenses rd
            LEFT JOIN restaurant_depense_categories rdc ON rd.categorie_id = rdc.id
            WHERE rd.categorie_id IS NOT NULL AND rdc.id IS NULL
        """, table)
        if rows:
            self.log_error(table, "ORPHAN_CATEGORY", f"{len(rows)} depenses avec categorie_id invalide", [{"id": r["id"], "categorie_id": r["categorie_id"]} for r in rows[:10]])

    def audit_restaurant_plats(self):
        """Audit de la table restaurant_plats."""
        table = "restaurant_plats"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Nom NULL
        rows = self.safe_execute("SELECT id FROM restaurant_plats WHERE nom IS NULL OR TRIM(nom) = ''", table)
        if rows:
            self.log_error(table, "NULL_NOM", f"{len(rows)} plats sans nom", [r["id"] for r in rows[:10]])

        # Prix NULL (colonne prix_vente_ttc)
        rows = self.safe_execute("SELECT id, nom FROM restaurant_plats WHERE prix_vente_ttc IS NULL", table)
        if rows:
            self.log_warning(table, "NULL_PRIX", f"{len(rows)} plats sans prix", [r["id"] for r in rows[:10]])

    def audit_restaurant_ingredients(self):
        """Audit de la table restaurant_ingredients."""
        table = "restaurant_ingredients"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Nom NULL
        rows = self.safe_execute("SELECT id FROM restaurant_ingredients WHERE nom IS NULL OR TRIM(nom) = ''", table)
        if rows:
            self.log_error(table, "NULL_NOM", f"{len(rows)} ingredients sans nom", [r["id"] for r in rows[:10]])

    def audit_processed_invoices(self):
        """Audit de la table processed_invoices."""
        table = "processed_invoices"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # File_path NULL (colonne file_path, pas filename)
        rows = self.safe_execute("SELECT id FROM processed_invoices WHERE file_path IS NULL OR TRIM(file_path) = ''", table)
        if rows:
            self.log_error(table, "NULL_FILE_PATH", f"{len(rows)} factures sans file_path", [r["id"] for r in rows[:10]])

        # Tenant_id NULL
        rows = self.safe_execute("SELECT id FROM processed_invoices WHERE tenant_id IS NULL", table)
        if rows:
            self.log_error(table, "NULL_TENANT", f"{len(rows)} factures sans tenant_id", [r["id"] for r in rows[:10]])

    def audit_finance_accounts(self):
        """Audit de la table finance_accounts."""
        table = "finance_accounts"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Label NULL
        rows = self.safe_execute("SELECT id FROM finance_accounts WHERE label IS NULL OR TRIM(label) = ''", table)
        if rows:
            self.log_error(table, "NULL_LABEL", f"{len(rows)} comptes sans label", [r["id"] for r in rows[:10]])

    def audit_finance_categories(self):
        """Audit de la table finance_categories."""
        table = "finance_categories"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Name NULL
        rows = self.safe_execute("SELECT id FROM finance_categories WHERE name IS NULL OR TRIM(name) = ''", table)
        if rows:
            self.log_error(table, "NULL_NAME", f"{len(rows)} categories sans nom", [r["id"] for r in rows[:10]])

        # Doublons par nom
        rows = self.safe_execute("SELECT name, COUNT(*) as cnt FROM finance_categories GROUP BY name HAVING COUNT(*) > 1", table)
        if rows:
            self.log_warning(table, "DUPLICATE_NAMES", f"{len(rows)} noms de categories en double", [{"name": r["name"], "count": r["cnt"]} for r in rows[:10]])

    def audit_produits_barcodes(self):
        """Audit de la table produits_barcodes."""
        table = "produits_barcodes"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Code NULL (colonne 'code', pas 'barcode')
        rows = self.safe_execute("SELECT id FROM produits_barcodes WHERE code IS NULL OR TRIM(code) = ''", table)
        if rows:
            self.log_error(table, "NULL_CODE", f"{len(rows)} codes-barres vides", [r["id"] for r in rows[:10]])

        # Produit_id invalide
        rows = self.safe_execute("""
            SELECT pb.id, pb.produit_id FROM produits_barcodes pb
            LEFT JOIN produits p ON pb.produit_id = p.id
            WHERE pb.produit_id IS NOT NULL AND p.id IS NULL
        """, table)
        if rows:
            self.log_error(table, "ORPHAN_PRODUCT", f"{len(rows)} codes-barres avec produit_id invalide", [{"id": r["id"], "produit_id": r["produit_id"]} for r in rows[:10]])

        # Doublons code
        rows = self.safe_execute("SELECT code, COUNT(*) as cnt FROM produits_barcodes GROUP BY code HAVING COUNT(*) > 1", table)
        if rows:
            self.log_warning(table, "DUPLICATE_BARCODES", f"{len(rows)} codes-barres en double", [{"code": r["code"], "count": r["cnt"]} for r in rows[:10]])

    def audit_produits_price_history(self):
        """Audit de la table produits_price_history.
        Structure: id, tenant_id, code, fournisseur, prix_achat, quantite, facture_date, source_context, created_at
        """
        table = "produits_price_history"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Code NULL (identifiant produit)
        rows = self.safe_execute("SELECT id FROM produits_price_history WHERE code IS NULL OR TRIM(code) = ''", table)
        if rows:
            self.log_error(table, "NULL_CODE", f"{len(rows)} historiques sans code produit", [r["id"] for r in rows[:10]])

        # Prix_achat NULL
        rows = self.safe_execute("SELECT id FROM produits_price_history WHERE prix_achat IS NULL", table)
        if rows:
            self.log_warning(table, "NULL_PRIX", f"{len(rows)} historiques sans prix_achat", [r["id"] for r in rows[:10]])

        # Fournisseur NULL
        rows = self.safe_execute("SELECT id FROM produits_price_history WHERE fournisseur IS NULL OR TRIM(fournisseur) = ''", table)
        if rows:
            self.log_warning(table, "NULL_FOURNISSEUR", f"{len(rows)} historiques sans fournisseur", [r["id"] for r in rows[:10]])

    def audit_vendor_aliases(self):
        """Audit de la table vendor_aliases.
        Structure: id, tenant_id, vendor_id, vendor_name, alias_pattern, alias_type, source, confidence, times_used, last_used_at, created_at
        """
        table = "vendor_aliases"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # alias_pattern NULL (colonne 'alias_pattern', pas 'alias')
        rows = self.safe_execute("SELECT id FROM vendor_aliases WHERE alias_pattern IS NULL OR TRIM(alias_pattern) = ''", table)
        if rows:
            self.log_warning(table, "NULL_ALIAS_PATTERN", f"{len(rows)} alias vides", [r["id"] for r in rows[:10]])

        # vendor_name NULL
        rows = self.safe_execute("SELECT id FROM vendor_aliases WHERE vendor_name IS NULL OR TRIM(vendor_name) = ''", table)
        if rows:
            self.log_warning(table, "NULL_VENDOR_NAME", f"{len(rows)} vendor_name vides", [r["id"] for r in rows[:10]])

    def audit_tenants(self):
        """Audit de la table tenants."""
        table = "tenants"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Code NULL
        rows = self.safe_execute("SELECT id FROM tenants WHERE code IS NULL OR TRIM(code) = ''", table)
        if rows:
            self.log_error(table, "NULL_CODE", f"{len(rows)} tenants sans code", [r["id"] for r in rows[:10]])

    def audit_app_users(self):
        """Audit de la table app_users."""
        table = "app_users"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # Username NULL
        rows = self.safe_execute("SELECT id FROM app_users WHERE username IS NULL OR TRIM(username) = ''", table)
        if rows:
            self.log_error(table, "NULL_USERNAME", f"{len(rows)} utilisateurs sans username", [r["id"] for r in rows[:10]])

        # Password_hash NULL
        rows = self.safe_execute("SELECT id, username FROM app_users WHERE password_hash IS NULL OR TRIM(password_hash) = ''", table)
        if rows:
            self.log_error(table, "NULL_PASSWORD", f"{len(rows)} utilisateurs sans mot de passe", [r["username"] for r in rows[:10]])

    def audit_data_quality(self):
        """Audit de la qualite des donnees."""

        # Produits avec prix absurdes (> 10000 EUR)
        rows = self.safe_execute("SELECT id, nom, prix_vente FROM produits WHERE prix_vente > 10000", "DATA_QUALITY")
        if rows:
            self.log_warning("DATA_QUALITY", "UNUSUAL_PRICE", f"{len(rows)} produits avec prix > 10000 EUR", [{"id": r["id"], "nom": r["nom"], "prix": float(r["prix_vente"])} for r in rows[:5]])

        # Transactions avec montants tres eleves (> 100000 EUR)
        rows = self.safe_execute("SELECT id, label, amount FROM finance_transactions WHERE ABS(amount) > 100000", "DATA_QUALITY")
        if rows:
            self.log_warning("DATA_QUALITY", "LARGE_TRANSACTION", f"{len(rows)} transactions > 100000 EUR", [{"id": r["id"], "amount": float(r["amount"])} for r in rows[:5]])

        # Produits avec stock > 10000
        rows = self.safe_execute("SELECT id, nom, stock_actuel FROM produits WHERE stock_actuel > 10000", "DATA_QUALITY")
        if rows:
            self.log_warning("DATA_QUALITY", "HIGH_STOCK", f"{len(rows)} produits avec stock > 10000", [{"id": r["id"], "nom": r["nom"], "stock": float(r["stock_actuel"])} for r in rows[:5]])

    def audit_additional_tables(self):
        """Audit des tables additionnelles."""

        # finance_entities
        table = "finance_entities"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")
        rows = self.safe_execute("SELECT id FROM finance_entities WHERE name IS NULL OR TRIM(name) = ''", table)
        if rows:
            self.log_error(table, "NULL_NAME", f"{len(rows)} entites sans nom", [r["id"] for r in rows[:10]])

        # supplier_scores
        table = "supplier_scores"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # detected_anomalies
        table = "detected_anomalies"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # forecast_cache
        table = "forecast_cache"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # audit_trail
        table = "audit_trail"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # bank_reconciliations
        table = "bank_reconciliations"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

        # financial_rules
        table = "financial_rules"
        count = self.get_table_count(table)
        self.log_info(table, "COUNT", f"Total: {count} enregistrements")

    def run_full_audit(self):
        """Execute l'audit complet."""
        print("=" * 80)
        print("AUDIT COMPLET DE LA BASE DE DONNEES")
        print(f"Date: {datetime.now().isoformat()}")
        print("=" * 80)
        print()

        # Audit par table
        self.audit_produits()
        self.audit_finance_transactions()
        self.audit_mouvements_stock()
        self.audit_restaurant_depenses()
        self.audit_restaurant_plats()
        self.audit_restaurant_ingredients()
        self.audit_processed_invoices()
        self.audit_finance_accounts()
        self.audit_finance_categories()
        self.audit_produits_barcodes()
        self.audit_produits_price_history()
        self.audit_vendor_aliases()
        self.audit_tenants()
        self.audit_app_users()
        self.audit_additional_tables()

        # Audit qualite des donnees
        self.audit_data_quality()

    def generate_report(self) -> str:
        """Genere le rapport d'audit."""
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT D'AUDIT DE LA BASE DE DONNEES")
        lines.append(f"Date de generation: {datetime.now().isoformat()}")
        lines.append("=" * 80)
        lines.append("")

        # Resume
        lines.append("## RESUME")
        lines.append(f"- Erreurs critiques: {len(self.errors)}")
        lines.append(f"- Avertissements: {len(self.warnings)}")
        lines.append(f"- Informations: {len(self.info)}")
        lines.append("")

        # Erreurs critiques
        if self.errors:
            lines.append("=" * 80)
            lines.append("## ERREURS CRITIQUES")
            lines.append("=" * 80)
            for i, err in enumerate(self.errors, 1):
                lines.append(f"\n### Erreur #{i}")
                lines.append(f"- Table: {err['table']}")
                lines.append(f"- Categorie: {err['category']}")
                lines.append(f"- Message: {err['message']}")
                if err.get('details'):
                    lines.append(f"- Details: {err['details']}")
            lines.append("")

        # Avertissements
        if self.warnings:
            lines.append("=" * 80)
            lines.append("## AVERTISSEMENTS")
            lines.append("=" * 80)
            for i, warn in enumerate(self.warnings, 1):
                lines.append(f"\n### Avertissement #{i}")
                lines.append(f"- Table: {warn['table']}")
                lines.append(f"- Categorie: {warn['category']}")
                lines.append(f"- Message: {warn['message']}")
                if warn.get('details'):
                    lines.append(f"- Details: {warn['details']}")
            lines.append("")

        # Informations
        if self.info:
            lines.append("=" * 80)
            lines.append("## STATISTIQUES DES TABLES")
            lines.append("=" * 80)
            for inf in self.info:
                lines.append(f"- [{inf['table']}] {inf['message']}")
            lines.append("")

        # Recommandations
        lines.append("=" * 80)
        lines.append("## RECOMMANDATIONS")
        lines.append("=" * 80)
        if self.errors:
            lines.append("\n### Priorite HAUTE (Erreurs critiques a corriger)")
            seen_recs = set()
            for err in self.errors:
                rec = None
                if err['category'] == 'NULL_TENANT':
                    rec = f"- Ajouter tenant_id manquant dans {err['table']}"
                elif err['category'] == 'ORPHAN_PRODUCT':
                    rec = f"- Corriger les references produit invalides dans {err['table']}"
                elif err['category'] == 'ORPHAN_CATEGORY':
                    rec = f"- Corriger les references categorie invalides dans {err['table']}"
                elif err['category'] == 'NEGATIVE_STOCK':
                    rec = f"- Corriger les stocks negatifs dans {err['table']}"
                elif err['category'] == 'NULL_NAME' or err['category'] == 'NULL_NOM':
                    rec = f"- Ajouter les noms manquants dans {err['table']}"
                elif err['category'] == 'NULL_AMOUNT':
                    rec = f"- Verifier les montants NULL dans {err['table']}"
                if rec and rec not in seen_recs:
                    lines.append(rec)
                    seen_recs.add(rec)

        if self.warnings:
            lines.append("\n### Priorite MOYENNE (Avertissements a examiner)")
            seen_recs = set()
            for warn in self.warnings:
                rec = None
                if warn['category'] == 'DUPLICATE_NAMES':
                    rec = f"- Verifier les doublons dans {warn['table']}"
                elif warn['category'] == 'POTENTIAL_DUPLICATES':
                    rec = f"- Verifier les transactions en double dans {warn['table']}"
                elif warn['category'] == 'NEGATIVE_MARGIN':
                    rec = f"- Verifier les marges negatives dans {warn['table']}"
                elif warn['category'] == 'NULL_PRIX_VENTE' or warn['category'] == 'NULL_PRIX_ACHAT':
                    rec = f"- Completer les prix manquants dans {warn['table']}"
                if rec and rec not in seen_recs:
                    lines.append(rec)
                    seen_recs.add(rec)

        lines.append("")
        lines.append("=" * 80)
        lines.append("FIN DU RAPPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def close(self):
        """Ferme la connexion."""
        self.cursor.close()
        self.conn.close()


def main():
    """Point d'entree principal."""
    try:
        auditor = DatabaseAuditor()
        auditor.run_full_audit()
        report = auditor.generate_report()

        # Afficher le rapport
        print(report)

        # Sauvegarder le rapport
        report_path = "docs/AUDIT_DATABASE_REPORT.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nRapport sauvegarde: {report_path}")

        auditor.close()

        # Code de sortie basé sur les erreurs
        if auditor.errors:
            print(f"\n!!! {len(auditor.errors)} erreurs critiques trouvees !!!")
            return 1
        return 0

    except Exception as e:
        print(f"Erreur lors de l'audit: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
