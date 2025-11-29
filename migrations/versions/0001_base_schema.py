"""Initial schema extracted from db/init.sql"""

from alembic import op
import sqlalchemy as sa

revision = '0001_base_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE type_mouvement AS ENUM ('ENTREE', 'SORTIE', 'TRANSFERT', 'INVENTAIRE');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;

    DO $$ BEGIN
        CREATE TYPE type_cat AS ENUM ('Epicerie sucree', 'Epicerie salee', 'Alcool', 'Autre', 'Afrique', 'Boissons', 'Hygiene');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.create_table(
        'produits',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nom', sa.Text, nullable=False),
        sa.Column('categorie', sa.Text, server_default='Autre'),
        sa.Column('prix_achat', sa.Numeric(10, 2)),
        sa.Column('prix_vente', sa.Numeric(10, 2)),
        sa.Column('tva', sa.Numeric(5, 2), server_default='0'),
        sa.Column('seuil_alerte', sa.Numeric(12, 3), server_default='0'),
        sa.Column('actif', sa.Boolean, server_default=sa.sql.expression.true()),
        sa.Column('stock_actuel', sa.Numeric(12, 3), server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )

    op.create_table(
        'produits_barcodes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('produit_id', sa.Integer, sa.ForeignKey('produits.id', ondelete='CASCADE')),
        sa.Column('code', sa.Text, nullable=False),
        sa.Column('symbologie', sa.Text),
        sa.Column('pays_iso2', sa.String(2)),
        sa.Column('is_principal', sa.Boolean, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )

    op.create_table(
        'mouvements_stock',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('produit_id', sa.Integer, sa.ForeignKey('produits.id', ondelete='CASCADE')),
        sa.Column('type', sa.Text, nullable=False),
        sa.Column('quantite', sa.Numeric(12, 3), nullable=False),
        sa.Column('source', sa.Text),
        sa.Column('date_mvt', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )

    op.create_table(
        'app_users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.Text, unique=True, nullable=False),
        sa.Column('email', sa.Text, unique=True, nullable=False),
        sa.Column('password_hash', sa.Text, nullable=False),
        sa.Column('role', sa.Text, server_default='standard'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION update_stock_actuel()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE produits
        SET stock_actuel = stock_actuel + CASE
            WHEN NEW.type = 'ENTREE' THEN NEW.quantite
            WHEN NEW.type = 'SORTIE' THEN -NEW.quantite
            ELSE 0
        END
        WHERE id = NEW.produit_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE OR REPLACE TRIGGER trg_update_stock_actuel
    AFTER INSERT ON mouvements_stock
    FOR EACH ROW EXECUTE FUNCTION update_stock_actuel();
    """)

    op.create_index('uix_produits_nom_ci', 'produits', [sa.text('LOWER(nom)')], unique=True)
    op.create_index('uix_barcodes_code_ci', 'produits_barcodes', [sa.text('LOWER(code)')], unique=True)
    op.create_index('idx_barcode_produit', 'produits_barcodes', ['produit_id'])
    op.create_index('idx_mouvements_produit', 'mouvements_stock', ['produit_id'])
    op.create_index('idx_mouvements_date', 'mouvements_stock', ['date_mvt'])

    # Views (simplified version)
    op.execute("""
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
    GROUP BY p.id;
    """)


def downgrade():
    op.execute("DROP VIEW IF EXISTS v_stock_courant;")
    op.drop_index('idx_mouvements_date', table_name='mouvements_stock')
    op.drop_index('idx_mouvements_produit', table_name='mouvements_stock')
    op.drop_index('idx_barcode_produit', table_name='produits_barcodes')
    op.drop_index('uix_barcodes_code_ci', table_name='produits_barcodes')
    op.drop_index('uix_produits_nom_ci', table_name='produits')
    op.drop_table('app_users')
    op.drop_table('mouvements_stock')
    op.drop_table('produits_barcodes')
    op.drop_table('produits')
    op.execute("DROP TYPE IF EXISTS type_cat; DROP TYPE IF EXISTS type_mouvement;")
