#!/usr/bin/env python3
"""
Import complet des données restaurant depuis les fichiers CSV.

Ce script:
1. Ajoute les plats manquants avec catégories et prix
2. Importe les ventes depuis le rapport de commandes
3. Crée et remplit la table TVA journal
4. Génère les mouvements de stock depuis les ventes (optionnel)

Usage:
    python scripts/import_restaurant_data.py --all
    python scripts/import_restaurant_data.py --plats
    python scripts/import_restaurant_data.py --ventes
    python scripts/import_restaurant_data.py --tva
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import execute_values

# Configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'db'),  # 'db' est le nom du service Docker
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'epicerie'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
}

DATA_DIR = Path(__file__).parent.parent / "Ventes & Mouvement Stock & Comptabilite Restaurant"
COMMANDES_DIRS = [
    DATA_DIR / "rapport-de-commandes-2023-01-01_2024-01-01",
    DATA_DIR / "rapport-de-commandes-2024-01-01_2024-12-31",
    DATA_DIR / "rapport-de-commandes-2025-01-01_2025-12-31",
]
COMPTABLE_DIR = DATA_DIR / "rapport-comptable-detaille-2023-01-01_2025-11-07"

TENANT_ID = 2  # Restaurant tenant

# =============================================================================
# PLATS MANQUANTS - Liste des plats à ajouter avec catégories
# =============================================================================

PLATS_A_AJOUTER = [
    # =========================================================================
    # VIANDES & VOLAILLES
    # =========================================================================
    ("CUISSES DE POULET", 10.00, "Viandes", "plat"),
    ("AILES DE POULET", 10.00, "Viandes", "plat"),
    ("AILES DE POULET RIZ", 15.00, "Viandes", "plat"),
    ("DEMI PLAT AILES", 5.00, "Viandes", "plat"),
    ("1/2 PLAT AILES", 5.00, "Viandes", "plat"),
    ("COTELETTE DE PORC BRAISE", 10.00, "Viandes", "plat"),
    ("PORC RIZ", 15.00, "Viandes", "plat"),
    ("ROTI PORC", 15.00, "Viandes", "plat"),
    ("TRIPPES SAUTEES", 12.00, "Viandes", "plat"),
    ("ROGNON SAUTEE 15€", 15.00, "Viandes", "plat"),
    ("ROGNON SAUTEE 20€", 20.00, "Viandes", "plat"),

    # =========================================================================
    # POISSONS
    # =========================================================================
    ("CAPITAINE PM", 20.00, "Poissons", "plat"),
    ("GROS CAPTAINE", 25.00, "Poissons", "plat"),
    ("SOLE PM", 25.00, "Poissons", "plat"),
    ("SOLE GROS", 45.00, "Poissons", "plat"),
    ("MAQUEREAU PM", 15.00, "Poissons", "plat"),
    ("MAQUEREAU GROS", 20.00, "Poissons", "plat"),
    ("TILAPIA", 15.00, "Poissons", "plat"),

    # =========================================================================
    # BOUILLONS
    # =========================================================================
    ("BOUILLON DE POISSON", 20.00, "Bouillons", "plat"),
    ("BOUILLON QUEUE DE B", 15.00, "Bouillons", "plat"),

    # =========================================================================
    # GRILLADES & BROCHETTES
    # =========================================================================
    ("BROCHETTES DE CREVETTES", 10.00, "Grillades", "plat"),
    ("BROCHETTES DE VIANDES", 10.00, "Grillades", "plat"),
    ("5 BROCHETTES DE CREVETTES", 10.00, "Grillades", "plat"),
    ("5 BROCHETTES DE VIANDES", 10.00, "Grillades", "plat"),

    # =========================================================================
    # PLATS EN SAUCE - GOMBO
    # =========================================================================
    ("GOMBO POISSON FRIT", 18.00, "Plats en sauce", "plat"),
    ("GOMBO POISSON FUME", 15.00, "Plats en sauce", "plat"),
    ("GOMBO ROYAL", 20.00, "Plats en sauce", "plat"),
    ("GOMBO VIANDE", 15.00, "Plats en sauce", "plat"),

    # =========================================================================
    # PLATS EN SAUCE - NDOLE
    # =========================================================================
    ("NDOLE CREVETTES", 15.00, "Plats en sauce", "plat"),
    ("NDOLE POISSON FRIT", 20.00, "Plats en sauce", "plat"),
    ("NDOLE POISSON FUME", 16.00, "Plats en sauce", "plat"),
    ("NDOLE ROYAL", 20.00, "Plats en sauce", "plat"),
    ("NDOLE VIANDE", 15.00, "Plats en sauce", "plat"),

    # =========================================================================
    # PLATS EN SAUCE - PISTACHE
    # =========================================================================
    ("PISTACHE POISSON FRIT", 20.00, "Plats en sauce", "plat"),
    ("PISTACHE POISSON FUME", 15.00, "Plats en sauce", "plat"),
    ("PISTACHE VIANDE", 15.00, "Plats en sauce", "plat"),

    # =========================================================================
    # PLATS EN SAUCE - MAFE
    # =========================================================================
    ("MAFE POISSON FRIT", 15.00, "Plats en sauce", "plat"),
    ("MAFE POISSON FUME", 15.00, "Plats en sauce", "plat"),
    ("MAFE VIANDE", 12.00, "Plats en sauce", "plat"),

    # =========================================================================
    # PLATS EN SAUCE - SAUCE TOMATE
    # =========================================================================
    ("SAUCE TOMATE POISSON FRIT", 20.00, "Plats en sauce", "plat"),
    ("SAUCE TOMATE VIANDE", 15.00, "Plats en sauce", "plat"),

    # =========================================================================
    # LEGUMES SAUTES
    # =========================================================================
    ("LEGUMES ROYAL", 20.00, "Légumes", "plat"),
    ("LEGUMES SAUTES CREVETTES", 15.00, "Légumes", "plat"),
    ("LEGUMES SAUTES POISSON FRIT", 20.00, "Légumes", "plat"),
    ("LEGUMES SAUTES POISSON FUME", 20.00, "Légumes", "plat"),
    ("LEGUMES SAUTES VIANDE", 15.00, "Légumes", "plat"),

    # =========================================================================
    # PLATS TRADITIONNELS
    # =========================================================================
    ("KOKI", 12.00, "Plats traditionnels", "plat"),
    ("KONDRE", 20.00, "Plats traditionnels", "plat"),
    ("TARO", 18.00, "Plats traditionnels", "plat"),
    ("SOYA", 10.00, "Plats traditionnels", "plat"),
    ("HERU", 18.00, "Plats traditionnels", "plat"),  # Eru

    # =========================================================================
    # ENTREES
    # =========================================================================
    ("SALADE MAISON", 15.00, "Entrées", "plat"),

    # =========================================================================
    # SUPPLEMENTS & EXTRAS
    # =========================================================================
    ("SUPPLEMENTS 3€", 3.00, "Suppléments", "supplement"),
    ("SUPPLEMENTS 5€", 5.00, "Suppléments", "supplement"),
    ("SUPPLEMENTS 10€", 10.00, "Suppléments", "supplement"),
    ("OEUF", 0.50, "Suppléments", "supplement"),
    ("PRUNES 5€", 5.00, "Desserts", "plat"),
    ("PRUNES 10€", 10.00, "Desserts", "plat"),

    # =========================================================================
    # BOISSONS - BIERES (variantes manquantes)
    # =========================================================================
    ("GUINESS", 12.00, "Bières", "plat"),
    ("GRANDE GUINESS", 10.00, "Bières", "plat"),
    ("PETITE GUINESS", 5.00, "Bières", "plat"),
    ("DESPERADOS", 10.00, "Bières", "plat"),
    ("GRANDE DESPERADOS", 8.00, "Bières", "plat"),
    ("PETITE DESPERADOS", 4.00, "Bières", "plat"),
    ("LEFFE", 10.00, "Bières", "plat"),
    ("GRANDE LEFFE", 7.00, "Bières", "plat"),
    ("PETITE LEFFE", 4.00, "Bières", "plat"),
    ("PELFORT", 7.00, "Bières", "plat"),
    ("HEINEKEIN", 5.00, "Bières", "plat"),

    # =========================================================================
    # BOISSONS - VINS
    # =========================================================================
    ("1/2 DG", 15.00, "Vins", "plat"),
    ("DG", 30.00, "Vins", "plat"),
    ("PETIT VIN", 7.00, "Vins", "plat"),
    ("ROSE", 15.00, "Vins", "plat"),

    # =========================================================================
    # BOISSONS - SPIRITUEUX & COCKTAILS
    # =========================================================================
    ("BALLEYS", 50.00, "Spiritueux", "plat"),
    ("BALLEYS CONSO", 5.00, "Apéritifs", "plat"),
    ("BLACK LABEL", 60.00, "Whisky", "plat"),
    ("CHIVAS", 60.00, "Whisky", "plat"),
    ("GLENFIDDICH", 70.00, "Whisky", "plat"),
    ("JACK DANIEL", 60.00, "Whisky", "plat"),
    ("JB", 50.00, "Whisky", "plat"),
    ("MARTINI", 45.00, "Apéritifs", "plat"),
    ("MARTINI CONSO", 5.00, "Apéritifs", "plat"),
    ("COGNAC CONSO", 5.00, "Apéritifs", "plat"),
    ("COMPARI CONSO", 5.00, "Apéritifs", "plat"),
    ("RHUM CONSO", 5.00, "Apéritifs", "plat"),
    ("MOET", 60.00, "Champagne", "plat"),
    ("VEUVE CLICOT", 70.00, "Champagne", "plat"),
    ("COUPE MOET", 10.00, "Champagne", "plat"),
    ("COUPE VEUVE CLICOT", 10.00, "Champagne", "plat"),

    # =========================================================================
    # PRODUITS ADDITIONNELS (2024-2025)
    # =========================================================================
    ("BROCHETTES DE GESIER", 10.00, "Grillades", "plat"),
    ("BEIGNET HARICOT", 5.00, "Entrées", "plat"),
    ("BEIGNET HARICOT VIANDE", 8.00, "Entrées", "plat"),
    ("CONSO WHISKY", 5.00, "Apéritifs", "plat"),
    ("GRANDE PELFORT", 8.00, "Bières", "plat"),
    ("GESIER 15€", 15.00, "Viandes", "plat"),
    ("MECHOUI CHEVRE", 25.00, "Viandes", "plat"),
    ("PISTACHE ROYAL", 20.00, "Plats en sauce", "plat"),
    ("RAGOUT VIANDE", 15.00, "Plats en sauce", "plat"),
    ("REDBULL", 5.00, "Softs", "plat"),
    ("SALADE AVOCATS", 10.00, "Entrées", "plat"),
    ("SAUCE JAUNE P FUME", 15.00, "Plats en sauce", "plat"),
    ("SAUCE JAUNE ROYAL", 20.00, "Plats en sauce", "plat"),
    ("SAUCE JAUNE VIANDE", 15.00, "Plats en sauce", "plat"),
    ("SALADE", 8.00, "Entrées", "plat"),
    ("VODKA CONSO", 5.00, "Apéritifs", "plat"),
    ("VODKA", 50.00, "Spiritueux", "plat"),
]

# =============================================================================
# MAPPING DES SYNONYMES - Pour lier les noms CSV aux noms DB
# Format: "NOM_CSV": "NOM_DB"
# =============================================================================

SYNONYMES = {
    # Variations d'orthographe et de casse
    "1/2 BLACK LABEL": "1/2 Black Label",
    "1/2 BLACL LABEL": "1/2 Black Label",
    "LEGUMES SAUTES POISSON FUME ": "LEGUMES SAUTES POISSON FUME",  # trailing space

    # Boissons avec variantes de noms
    "HEINEKEIN": "Heineken (petite)",
    "GUINNESS": "GUINESS",

    # Suppléments
    "Supplements 3€": "SUPPLEMENTS 3€",
    "Supplements 5€": "SUPPLEMENTS 5€",
    "Suppléments 10€": "SUPPLEMENTS 10€",
    "Prunes 5€": "PRUNES 5€",
    "Prunes 10€": "PRUNES 10€",
    "Oeuf": "OEUF",
    "Rognon sautée 15€": "ROGNON SAUTEE 15€",
    "Rognon sautée 20€": "ROGNON SAUTEE 20€",
    "Rôti porc": "ROTI PORC",

    # Plats avec accents et casse variable
    "Ginger": "GINGER",
    "Booster": "BOOSTER",
    "Coca": "COCA",
    "Glenfiddich": "GLENFIDDICH",
    "1/2 Glenfiddich": "1/2 GLENFIDDICH",
    "1/2 BlACK LABEL": "1/2 BLACK LABEL",
    "Vin 20€": "VIN 20€",
    "Vin 25€": "VIN 25€",
    "Vin 30€": "VIN 30€",
    "Vin 50€": "VIN 50€",

    # Produits 2024-2025 avec variantes
    "Beignet haricot": "BEIGNET HARICOT",
    "Beignet haricot viande": "BEIGNET HARICOT VIANDE",
    "Conso whisky": "CONSO WHISKY",
    "Gésier 15€": "GESIER 15€",
    "Ragoût viande": "RAGOUT VIANDE",
    "Redbull": "REDBULL",
    "Salade": "SALADE",
    "Vodka conso": "VODKA CONSO",

    # Bières renommées
    "DESPERADOS": "GRANDE DESPERADOS",
    "GRANDE GUINESS": "GUINNESS (GRANDE)",
}


def get_connection():
    """Établit la connexion à la base de données."""
    return psycopg2.connect(**DB_CONFIG)


def parse_french_decimal(value: str) -> Decimal:
    """Parse un nombre au format français (virgule comme séparateur décimal)."""
    if not value or value.strip() == '':
        return Decimal('0')
    # Remplacer la virgule par un point
    clean = value.strip().replace(',', '.').replace(' ', '').replace('\xa0', '')
    try:
        return Decimal(clean)
    except:
        return Decimal('0')


def parse_french_datetime(value: str) -> datetime:
    """Parse une date au format français."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d %H:%M:%S')
    except:
        try:
            return datetime.strptime(value.strip(), '%Y-%m-%d')
        except:
            return None


# =============================================================================
# 1. IMPORT DES PLATS MANQUANTS
# =============================================================================

def import_plats(conn):
    """Ajoute les plats manquants à la base de données."""
    print("\n" + "="*60)
    print("1. IMPORT DES PLATS MANQUANTS")
    print("="*60)

    cur = conn.cursor()
    added = 0
    skipped = 0

    for nom, prix, categorie, type_plat in PLATS_A_AJOUTER:
        # Vérifier si le plat existe déjà
        cur.execute(
            "SELECT id FROM restaurant_plats WHERE tenant_id = %s AND UPPER(TRIM(nom)) = UPPER(TRIM(%s))",
            (TENANT_ID, nom)
        )
        if cur.fetchone():
            skipped += 1
            continue

        # Ajouter le plat
        cur.execute("""
            INSERT INTO restaurant_plats (tenant_id, nom, prix_vente_ttc, categorie, type, actif)
            VALUES (%s, %s, %s, %s, %s, true)
            RETURNING id
        """, (TENANT_ID, nom, prix, categorie, type_plat))

        plat_id = cur.fetchone()[0]
        print(f"  ✓ Ajouté: {nom} ({categorie}) - {prix}€")
        added += 1

    conn.commit()
    print(f"\n  Résultat: {added} plats ajoutés, {skipped} déjà existants")
    return added


# =============================================================================
# HELPER: Normalisation des noms
# =============================================================================

def normalize_product_name(name: str) -> str:
    """Normalise un nom de produit pour le matching."""
    name = name.strip()
    # Appliquer les synonymes si définis
    if name in SYNONYMES:
        name = SYNONYMES[name]
    return name.upper().strip()


# =============================================================================
# 2. HISTORIQUE DES PRIX
# =============================================================================

def create_price_history_table(conn):
    """Crée la table d'historique des prix si elle n'existe pas."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS restaurant_plat_prix_history (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 2,
            plat_id INTEGER NOT NULL REFERENCES restaurant_plats(id) ON DELETE CASCADE,
            prix_ttc NUMERIC(10,2) NOT NULL,
            date_debut DATE NOT NULL,
            date_fin DATE,
            source TEXT DEFAULT 'import_csv',
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(tenant_id, plat_id, date_debut)
        );

        CREATE INDEX IF NOT EXISTS idx_plat_prix_history_plat
        ON restaurant_plat_prix_history(plat_id, date_debut DESC);

        COMMENT ON TABLE restaurant_plat_prix_history IS 'Historique des prix des plats';
    """)
    conn.commit()


def import_price_history(conn):
    """Importe l'historique des prix depuis les CSV et met à jour les prix actuels."""
    print("\n" + "="*60)
    print("2. HISTORIQUE DES PRIX")
    print("="*60)

    create_price_history_table(conn)

    cur = conn.cursor()

    # Charger le mapping nom -> plat_id
    cur.execute("SELECT id, UPPER(TRIM(nom)) FROM restaurant_plats WHERE tenant_id = %s", (TENANT_ID,))
    plat_mapping = {nom: pid for pid, nom in cur.fetchall()}

    # Collecter les prix par produit et par mois
    from collections import defaultdict
    price_by_month = defaultdict(lambda: defaultdict(list))  # produit -> YYYY-MM -> [prix]

    for commandes_dir in COMMANDES_DIRS:
        if not commandes_dir.exists():
            continue

        csv_files = list(commandes_dir.glob("rapport-de-commandes-produits-*.csv"))
        if not csv_files:
            continue

        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';', quotechar='"')

            for row in reader:
                produit = row.get('Produit', '').strip()
                # Le nom de colonne a des caractères invisibles
                prix_str = row.get('Prix \u200b\u200bunitaire TTC', '') or row.get('Prix unitaire TTC', '')
                date_str = row.get('Date fermeture', '')[:7]  # YYYY-MM

                if not produit or not prix_str or not date_str:
                    continue

                try:
                    prix = float(prix_str.replace(',', '.').replace(' ', ''))
                    if prix > 0:
                        normalized = normalize_product_name(produit)
                        price_by_month[normalized][date_str].append(prix)
                except:
                    pass

    # Calculer le prix médian par mois pour chaque produit
    price_changes = []
    latest_prices = {}

    for produit, months in price_by_month.items():
        plat_id = plat_mapping.get(produit)
        if not plat_id:
            continue

        # Trier les mois
        sorted_months = sorted(months.keys())
        prev_price = None

        for month in sorted_months:
            prices = months[month]
            # Utiliser le prix le plus fréquent (mode)
            from statistics import mode
            try:
                median_price = mode(prices)
            except:
                median_price = sum(prices) / len(prices)

            if prev_price is None or abs(median_price - prev_price) > 0.01:
                date_debut = f"{month}-01"
                price_changes.append((TENANT_ID, plat_id, median_price, date_debut, 'import_csv'))
                prev_price = median_price

        # Garder le dernier prix
        if sorted_months:
            last_prices = months[sorted_months[-1]]
            try:
                latest_prices[plat_id] = mode(last_prices)
            except:
                latest_prices[plat_id] = sum(last_prices) / len(last_prices)

    # Insérer l'historique des prix
    if price_changes:
        cur.execute("DELETE FROM restaurant_plat_prix_history WHERE tenant_id = %s AND source = 'import_csv'", (TENANT_ID,))

        execute_values(
            cur,
            """
            INSERT INTO restaurant_plat_prix_history (tenant_id, plat_id, prix_ttc, date_debut, source)
            VALUES %s
            ON CONFLICT (tenant_id, plat_id, date_debut) DO UPDATE SET prix_ttc = EXCLUDED.prix_ttc
            """,
            price_changes,
            page_size=1000
        )

    # Mettre à jour les prix actuels dans restaurant_plats
    updated = 0
    for plat_id, prix in latest_prices.items():
        cur.execute("""
            UPDATE restaurant_plats
            SET prix_vente_ttc = %s
            WHERE id = %s AND tenant_id = %s AND (prix_vente_ttc IS NULL OR prix_vente_ttc != %s)
        """, (prix, plat_id, TENANT_ID, prix))
        if cur.rowcount > 0:
            updated += 1

    conn.commit()

    print(f"  ✓ {len(price_changes)} entrées d'historique créées")
    print(f"  ✓ {updated} prix actuels mis à jour")

    # Afficher les produits avec plusieurs prix
    cur.execute("""
        SELECT p.nom, COUNT(*) as nb_prix
        FROM restaurant_plat_prix_history h
        JOIN restaurant_plats p ON p.id = h.plat_id
        WHERE h.tenant_id = %s
        GROUP BY p.nom
        HAVING COUNT(*) > 1
        ORDER BY nb_prix DESC
        LIMIT 10
    """, (TENANT_ID,))

    results = cur.fetchall()
    if results:
        print(f"\n  Produits avec évolution de prix:")
        for nom, nb in results:
            print(f"    - {nom}: {nb} changements")

    return len(price_changes)


# =============================================================================
# 3. IMPORT DES VENTES
# =============================================================================

def import_ventes(conn):
    """Importe les ventes depuis tous les fichiers CSV des commandes produits."""
    print("\n" + "="*60)
    print("3. IMPORT DES VENTES")
    print("="*60)

    cur = conn.cursor()

    # Charger le mapping nom -> plat_id
    cur.execute("SELECT id, UPPER(TRIM(nom)) FROM restaurant_plats WHERE tenant_id = %s", (TENANT_ID,))
    plat_mapping = {nom: pid for pid, nom in cur.fetchall()}

    ventes_to_insert = []
    not_found = set()
    files_processed = 0

    # Parcourir tous les dossiers de commandes
    for commandes_dir in COMMANDES_DIRS:
        if not commandes_dir.exists():
            print(f"  ⚠ Dossier non trouvé: {commandes_dir.name}")
            continue

        # Trouver le fichier produits dans ce dossier
        csv_files = list(commandes_dir.glob("rapport-de-commandes-produits-*.csv"))
        if not csv_files:
            print(f"  ⚠ Pas de fichier produits dans: {commandes_dir.name}")
            continue

        csv_path = csv_files[0]
        print(f"  📂 {commandes_dir.name}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';', quotechar='"')

            for row in reader:
                produit = row.get('Produit', '').strip()
                quantite = parse_french_decimal(row.get('Quantité', '0'))
                date_str = row.get('Date fermeture', '') or row.get('Date ouverture', '')
                date_vente = parse_french_datetime(date_str)

                if not produit or not date_vente:
                    continue

                # Trouver le plat_id avec normalisation (synonymes)
                normalized = normalize_product_name(produit)
                plat_id = plat_mapping.get(normalized)

                if not plat_id:
                    not_found.add(produit)
                    continue

                ventes_to_insert.append((
                    TENANT_ID,
                    plat_id,
                    float(quantite),
                    date_vente,
                    'import_csv'
                ))

        files_processed += 1

    # Insérer les ventes
    if ventes_to_insert:
        # Vider les anciennes ventes importées
        cur.execute("DELETE FROM restaurant_sales WHERE tenant_id = %s AND source = 'import_csv'", (TENANT_ID,))

        execute_values(
            cur,
            """
            INSERT INTO restaurant_sales (tenant_id, plat_id, quantity, sold_at, source)
            VALUES %s
            """,
            ventes_to_insert,
            page_size=1000
        )
        conn.commit()

    print(f"\n  ✓ {len(ventes_to_insert)} ventes importées depuis {files_processed} fichiers")

    if not_found:
        print(f"\n  ⚠ {len(not_found)} produits non trouvés en DB:")
        for p in sorted(not_found)[:15]:
            print(f"    - {p}")
        if len(not_found) > 15:
            print(f"    ... et {len(not_found) - 15} autres")

    return len(ventes_to_insert)


# =============================================================================
# 3. IMPORT TVA
# =============================================================================

def create_tva_table(conn):
    """Crée la table de journal TVA si elle n'existe pas."""
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS restaurant_tva_journal (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 2,
            date DATE NOT NULL,
            taux_tva NUMERIC(5,3) NOT NULL,
            ca_ht NUMERIC(12,2) NOT NULL DEFAULT 0,
            ca_ttc NUMERIC(12,2) NOT NULL DEFAULT 0,
            montant_tva NUMERIC(12,2) NOT NULL DEFAULT 0,
            rembourse_ht NUMERIC(12,2) DEFAULT 0,
            rembourse_ttc NUMERIC(12,2) DEFAULT 0,
            source TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(tenant_id, date, taux_tva)
        );

        CREATE INDEX IF NOT EXISTS ix_restaurant_tva_journal_date
        ON restaurant_tva_journal(tenant_id, date);

        COMMENT ON TABLE restaurant_tva_journal IS 'Journal TVA quotidien par taux';
    """)
    conn.commit()
    print("  ✓ Table restaurant_tva_journal créée/vérifiée")


def import_tva(conn):
    """Importe les données TVA depuis le fichier comptable."""
    print("\n" + "="*60)
    print("4. IMPORT JOURNAL TVA")
    print("="*60)

    create_tva_table(conn)

    csv_path = COMPTABLE_DIR / "rapport-comptable-detailles-tva-2023-01-01_2025-11-07.csv"

    if not csv_path.exists():
        print(f"  ✗ Fichier non trouvé: {csv_path}")
        return 0

    cur = conn.cursor()
    tva_records = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';', quotechar='"')

        for row in reader:
            date_str = row.get('Date', '')
            taux = parse_french_decimal(row.get('Taux de TVA', '0'))
            ca_ht = parse_french_decimal(row.get('CA HT', '0'))
            ca_ttc = parse_french_decimal(row.get('CA TTC', '0'))
            montant_tva = parse_french_decimal(row.get('Montant TVA', '0'))
            rembourse_ht = parse_french_decimal(row.get('Remboursé HT', '0'))
            rembourse_ttc = parse_french_decimal(row.get('Remboursé TTC', '0'))

            if not date_str:
                continue

            try:
                date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            except:
                continue

            tva_records.append((
                TENANT_ID,
                date,
                float(taux),
                float(ca_ht),
                float(ca_ttc),
                float(montant_tva),
                float(rembourse_ht),
                float(rembourse_ttc),
                'import_csv'
            ))

    if tva_records:
        # Vider les anciennes données
        cur.execute("DELETE FROM restaurant_tva_journal WHERE tenant_id = %s AND source = 'import_csv'", (TENANT_ID,))

        execute_values(
            cur,
            """
            INSERT INTO restaurant_tva_journal
            (tenant_id, date, taux_tva, ca_ht, ca_ttc, montant_tva, rembourse_ht, rembourse_ttc, source)
            VALUES %s
            ON CONFLICT (tenant_id, date, taux_tva) DO UPDATE SET
                ca_ht = EXCLUDED.ca_ht,
                ca_ttc = EXCLUDED.ca_ttc,
                montant_tva = EXCLUDED.montant_tva,
                rembourse_ht = EXCLUDED.rembourse_ht,
                rembourse_ttc = EXCLUDED.rembourse_ttc
            """,
            tva_records,
            page_size=1000
        )
        conn.commit()

    print(f"  ✓ {len(tva_records)} enregistrements TVA importés")

    # Afficher un résumé par taux
    cur.execute("""
        SELECT
            taux_tva,
            COUNT(*) as nb_jours,
            SUM(ca_ttc) as total_ttc,
            SUM(montant_tva) as total_tva
        FROM restaurant_tva_journal
        WHERE tenant_id = %s
        GROUP BY taux_tva
        ORDER BY taux_tva
    """, (TENANT_ID,))

    print("\n  Résumé par taux de TVA:")
    for row in cur.fetchall():
        taux, nb, total_ttc, total_tva = row
        print(f"    {taux*100:.1f}%: {nb} jours, CA TTC={total_ttc:,.2f}€, TVA={total_tva:,.2f}€")

    return len(tva_records)


# =============================================================================
# 4. GÉNÉRATION DES MOUVEMENTS STOCK (optionnel)
# =============================================================================

def generate_stock_movements(conn):
    """Génère les mouvements de stock SORTIE à partir des ventes."""
    print("\n" + "="*60)
    print("5. GÉNÉRATION MOUVEMENTS STOCK (depuis ventes)")
    print("="*60)

    cur = conn.cursor()

    # Vérifier les liens plat-ingrédients
    cur.execute("""
        SELECT COUNT(*) FROM restaurant_plat_ingredients
        WHERE plat_id IN (SELECT id FROM restaurant_plats WHERE tenant_id = %s)
    """, (TENANT_ID,))
    nb_liens = cur.fetchone()[0]

    if nb_liens == 0:
        print("  ⚠ Aucun lien plat→ingrédient trouvé. Impossible de générer les mouvements.")
        print("    Vous devez d'abord configurer les recettes (ingrédients par plat).")
        return 0

    print(f"  {nb_liens} liens plat→ingrédient trouvés")

    # Générer les mouvements: pour chaque vente, créer une sortie pour chaque ingrédient
    # Note: type_mouvement doit être en minuscules ('sortie', 'entree', 'ajustement', 'transfert_epicerie')
    cur.execute("""
        INSERT INTO restaurant_stock_movements
        (tenant_id, ingredient_id, type_mouvement, quantite, unite, source, commentaire, date_mouvement, created_at)
        SELECT
            %s as tenant_id,
            pi.ingredient_id,
            'sortie' as type_mouvement,
            SUM(s.quantity * pi.quantite) as quantite,
            i.unite_base as unite,
            'ventes_import' as source,
            'Généré depuis ventes importées' as commentaire,
            DATE_TRUNC('day', s.sold_at) as date_mouvement,
            NOW() as created_at
        FROM restaurant_sales s
        JOIN restaurant_plat_ingredients pi ON pi.plat_id = s.plat_id
        JOIN restaurant_ingredients i ON i.id = pi.ingredient_id
        WHERE s.tenant_id = %s
        GROUP BY pi.ingredient_id, i.unite_base, DATE_TRUNC('day', s.sold_at)
        ON CONFLICT DO NOTHING
    """, (TENANT_ID, TENANT_ID))

    nb_mouvements = cur.rowcount
    conn.commit()

    print(f"  ✓ {nb_mouvements} mouvements de stock générés")
    return nb_mouvements


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Import des données restaurant')
    parser.add_argument('--all', action='store_true', help='Exécuter toutes les étapes')
    parser.add_argument('--plats', action='store_true', help='Importer les plats manquants')
    parser.add_argument('--prix', action='store_true', help='Importer historique des prix')
    parser.add_argument('--ventes', action='store_true', help='Importer les ventes')
    parser.add_argument('--tva', action='store_true', help='Importer le journal TVA')
    parser.add_argument('--stock', action='store_true', help='Générer les mouvements stock')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation (pas de commit)')

    args = parser.parse_args()

    # Si aucune option, afficher l'aide
    if not any([args.all, args.plats, args.prix, args.ventes, args.tva, args.stock]):
        parser.print_help()
        return

    print("\n" + "="*60)
    print("  IMPORT DONNÉES RESTAURANT")
    print("="*60)
    print(f"  Répertoire données: {DATA_DIR}")
    print(f"  Base de données: {DB_CONFIG['database']}@{DB_CONFIG['host']}")

    try:
        conn = get_connection()
        print("  ✓ Connexion établie")
    except Exception as e:
        print(f"  ✗ Erreur connexion: {e}")
        return

    try:
        if args.all or args.plats:
            import_plats(conn)

        if args.all or args.prix:
            import_price_history(conn)

        if args.all or args.ventes:
            import_ventes(conn)

        if args.all or args.tva:
            import_tva(conn)

        if args.all or args.stock:
            generate_stock_movements(conn)

        if args.dry_run:
            print("\n  [DRY-RUN] Rollback des changements")
            conn.rollback()
        else:
            conn.commit()

        print("\n" + "="*60)
        print("  IMPORT TERMINÉ")
        print("="*60)

    except Exception as e:
        conn.rollback()
        print(f"\n  ✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
