#!/usr/bin/env python3
"""
Script de génération de requêtes SQL INSERT pour l'import de produits.

Ce script lit un fichier CSV "prêt pour la base" contenant les produits avec
leurs prix de vente TTC, catégories et TVA, puis génère un fichier SQL avec
des instructions INSERT pour les insérer dans la table `produits`.

Le SQL généré utilise ON CONFLICT DO UPDATE pour mettre à jour les produits
existants (match sur nom en minuscules) ou créer les nouveaux.

Usage:
    python scripts/catalog/generate_insert_sql_from_ready.py

Fichier d'entrée:
    - docs/articles_prix_ttc_ready_for_db.csv : Produits validés prêts pour insertion
      Colonnes attendues: nom_clean, categorie, prix_vente, tva

Fichier de sortie:
    - docs/articles_insert.sql : Requêtes SQL d'insertion/mise à jour
      Format: INSERT INTO produits ... ON CONFLICT DO UPDATE

Variables d'environnement:
    Aucune

Prérequis:
    - pandas
    - Fichier CSV préparé avec tous les champs requis remplis

Notes:
    - Le SQL généré est transactionnel (BEGIN/COMMIT)
    - Les apostrophes dans les noms sont échappées ('' pour SQL)
    - tenant_id est fixé à 1 (peut être adapté selon besoins)
    - Le champ 'actif' est mis à TRUE pour tous les produits
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# Configuration des chemins de fichiers
READY_PATH = Path("docs/articles_prix_ttc_ready_for_db.csv")  # Entrée : CSV prêt
OUTPUT_SQL = Path("docs/articles_insert.sql")  # Sortie : SQL d'insertion


def escape(val: str) -> str:
    """
    Échappe les apostrophes pour SQL (simple quote devient double quote).

    Args:
        val (str): Valeur texte à échapper

    Returns:
        str: Valeur avec apostrophes échappées (ex: "l'huile" -> "l''huile")
    """
    return val.replace("'", "''")


def main():
    """
    Fonction principale : lit le CSV et génère le fichier SQL d'insertion.

    Processus:
    1. Charge le CSV avec les produits prêts
    2. Pour chaque ligne, crée une instruction VALUES (nom, tenant_id, categorie, prix, tva, actif)
    3. Génère un INSERT unique avec tous les produits
    4. Ajoute une clause ON CONFLICT pour mettre à jour les produits existants
    5. Écrit le tout dans un fichier .sql transactionnel
    """
    # Charge les données
    df = pd.read_csv(READY_PATH)

    # Construit les valeurs SQL pour chaque produit
    values_sql = []
    for _, row in df.iterrows():
        nom = escape(row["nom_clean"])
        categorie = escape(row["categorie"])
        prix_vente = float(row["prix_vente"])
        tva = float(row["tva"])

        # Format : (nom, tenant_id, categorie, prix_vente, tva, actif)
        values_sql.append(
            f"('{nom}', 1, '{categorie}', {prix_vente:.2f}, {tva:.2f}, TRUE)"
        )

    # Assemble toutes les lignes VALUES
    bulk_values = ",\n".join(values_sql)

    # Génère le SQL complet avec transaction et gestion des conflits
    sql = f"""-- Généré automatiquement depuis {READY_PATH.name}
BEGIN;
INSERT INTO produits (nom, tenant_id, categorie, prix_vente, tva, actif)
VALUES
{bulk_values}
ON CONFLICT (lower(nom)) DO UPDATE
  SET categorie = EXCLUDED.categorie,
      prix_vente = EXCLUDED.prix_vente,
      tva = EXCLUDED.tva,
      actif = TRUE,
      updated_at = now();
COMMIT;
"""

    # Écrit le fichier SQL
    OUTPUT_SQL.write_text(sql)
    print("SQL généré ->", OUTPUT_SQL, f"({len(df)} lignes)")


if __name__ == "__main__":
    main()
