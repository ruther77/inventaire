"""ajout nouvelle vue

Revision ID: 5ff57783ea01
Revises: 0001_base_schema
Create Date: 2025-11-08 17:25:18.958596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ff57783ea01'
down_revision: Union[str, Sequence[str], None] = '0001_base_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VIEWS_SQL = """
-- Stock produit basé sur la colonne matérialisée stock_actuel
CREATE OR REPLACE VIEW v_stock_produits AS
SELECT
    p.id,
    p.nom,
    p.categorie,
    COALESCE(p.prix_vente, 0)      AS prix_vente,
    COALESCE(p.tva, 0)             AS tva,
    COALESCE(p.seuil_alerte, 0)    AS seuil_alerte,
    COALESCE(p.stock_actuel, 0)    AS quantite_stock
FROM produits p
WHERE p.actif = TRUE;

CREATE OR REPLACE VIEW v_alertes_rupture AS
SELECT
    p.id,
    p.nom,
    COALESCE(p.categorie::text, 'Non renseignée') AS categorie,
    COALESCE(p.stock_actuel, 0)                   AS stock,
    COALESCE(p.seuil_alerte, 0)                   AS seuil_alerte
FROM produits p
WHERE p.actif = TRUE
  AND COALESCE(p.stock_actuel, 0) <= COALESCE(p.seuil_alerte, 0)
ORDER BY p.stock_actuel ASC;

CREATE OR REPLACE VIEW v_stock_courant AS
SELECT
    p.id,
    p.nom,
    p.categorie,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.seuil_alerte,
    p.actif,
    COALESCE(SUM(
        CASE
            WHEN m.type IN ('ENTREE', 'INVENTAIRE', 'TRANSFERT') THEN m.quantite
            WHEN m.type = 'SORTIE' THEN -m.quantite
            ELSE 0
        END
    ), 0) AS stock
FROM produits p
LEFT JOIN mouvements_stock m ON m.produit_id = p.id
GROUP BY
    p.id,
    p.nom,
    p.categorie,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.seuil_alerte,
    p.actif
ORDER BY p.nom;

CREATE OR REPLACE VIEW v_valorisation_stock AS
SELECT
    s.id,
    s.nom,
    s.stock,
    p.prix_achat,
    ROUND(s.stock * COALESCE(p.prix_achat, 0), 2) AS valeur_achat
FROM v_stock_courant s
JOIN produits p ON p.id = s.id
ORDER BY valeur_achat DESC;

CREATE OR REPLACE VIEW v_top_ventes_30j AS
SELECT
    p.id,
    p.nom,
    SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS qte_sorties_30j
FROM produits p
LEFT JOIN mouvements_stock m
    ON m.produit_id = p.id
   AND m.date_mvt >= now() - INTERVAL '30 days'
GROUP BY p.id, p.nom
ORDER BY qte_sorties_30j DESC NULLS LAST;

CREATE OR REPLACE VIEW v_rotation_30j AS
SELECT
    p.id,
    p.nom,
    SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite ELSE 0 END) AS entrees_30j,
    SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS sorties_30j
FROM produits p
LEFT JOIN mouvements_stock m
    ON m.produit_id = p.id
   AND m.date_mvt >= now() - INTERVAL '30 days'
GROUP BY p.id, p.nom
ORDER BY sorties_30j DESC NULLS LAST;

CREATE OR REPLACE VIEW v_inventaire_negatif AS
SELECT *
FROM v_stock_courant
WHERE stock < 0
ORDER BY stock ASC;

CREATE OR REPLACE VIEW v_produits_codes AS
SELECT
    p.id,
    p.nom,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.actif,
    COALESCE(string_agg(pb.code, ', ' ORDER BY pb.is_principal DESC, pb.code), '') AS codes
FROM produits p
LEFT JOIN produits_barcodes pb ON pb.produit_id = p.id
GROUP BY p.id, p.nom, p.prix_achat, p.prix_vente, p.tva, p.actif
ORDER BY p.nom;

CREATE OR REPLACE VIEW v_produits_sans_barcode AS
SELECT p.*
FROM produits p
LEFT JOIN produits_barcodes pb ON pb.produit_id = p.id
WHERE pb.id IS NULL
ORDER BY p.nom;

CREATE OR REPLACE VIEW v_mouvements_recents AS
SELECT
    m.id,
    m.date_mvt,
    m.type,
    m.quantite,
    m.source,
    p.id  AS produit_id,
    p.nom AS nom
FROM mouvements_stock m
JOIN produits p ON p.id = m.produit_id
ORDER BY m.date_mvt DESC
LIMIT 500;

-- Alias pour compatibilité avec les anciens scripts
CREATE OR REPLACE VIEW stock_courant  AS SELECT * FROM v_stock_courant;
CREATE OR REPLACE VIEW v_prod_barcodes AS SELECT * FROM v_produits_codes;
"""

DROP_VIEWS_SQL = """
DROP VIEW IF EXISTS v_prod_barcodes;
DROP VIEW IF EXISTS stock_courant;
DROP VIEW IF EXISTS v_mouvements_recents;
DROP VIEW IF EXISTS v_inventaire_negatif;
DROP VIEW IF EXISTS v_valorisation_stock;
DROP VIEW IF EXISTS v_produits_sans_barcode;
DROP VIEW IF EXISTS v_produits_codes;
DROP VIEW IF EXISTS v_rotation_30j;
DROP VIEW IF EXISTS v_top_ventes_30j;
DROP VIEW IF EXISTS v_alertes_rupture;
DROP VIEW IF EXISTS v_stock_produits;
DROP VIEW IF EXISTS v_stock_courant;
"""


def upgrade() -> None:
    """Create the derived inventory views required by the API."""

    op.execute(DROP_VIEWS_SQL)
    op.execute(VIEWS_SQL)


def downgrade() -> None:
    """Drop the derived inventory views."""

    op.execute(DROP_VIEWS_SQL)
