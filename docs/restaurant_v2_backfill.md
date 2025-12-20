# Migration Restaurant V2 (tables `restaurant_*`) et backfill

## 1. Réinitialisation du schéma
- Le script `db/init.sql` **supprime** les tables restaurant V1 (`ingredients`, `plats`, `plat_ingredients`, etc.) et recrée uniquement le modèle V2 (`restaurant_ingredients`, `restaurant_plats`, `restaurant_plat_ingredients`, `restaurant_stock_movements`, …).  
- Pour repartir propre : `psql $DATABASE_URL -f db/init.sql` puis `alembic upgrade head` (pour appliquer les migrations finance/consolidation).

## 2. Import depuis `/releve`
- Réinjecter le catalogue/stock/achats avec vos fichiers `/releve` via les loaders existants (ex: `scripts/import_invoice_files.py`, pipelines n8n ou outils internes).  
- Ordre conseillé : `produits` + `produits_barcodes` → `produits_price_history` → `mouvements_stock` → `processed_invoices`/`fact_invoices`.
- Pour le restaurant, remplir ensuite : `restaurant_ingredients` (coûts, catégories, lien `produit_epicerie_id`), `restaurant_plats`, `restaurant_plat_ingredients`, puis les mouvements `restaurant_stock_movements`.

## 3. Pipeline de synchro restaurant → finance (simplifiée)
Objectif : refléter les dépenses et relevés restaurant dans les tables finance (`finance_transactions`, `finance_categories`, `finance_accounts`).

1. **Catégories**  
   ```sql
   INSERT INTO finance_categories (id, entity_id, name, type, code)
   SELECT id, :restaurant_entity_id, nom, 'EXPENSE', 'RESTO_' || id
   FROM restaurant_depense_categories
   ON CONFLICT (entity_id, code) DO NOTHING;
   ```
2. **Comptes**  
   - Créer un compte finance par compte bancaire restaurant si besoin (`restaurant_bank_statements.account`).  
3. **Transactions**  
   ```sql
   INSERT INTO finance_transactions (
     entity_id, account_id, direction, source, date_operation,
     amount, currency, ref_externe, note, status
   )
   SELECT
     :restaurant_entity_id,
     :restaurant_account_id,
     CASE WHEN montant < 0 THEN 'OUT' ELSE 'IN' END,
     'restaurant',
     date,
     montant,
     'EUR',
     libelle,
     categorie,
     'CONFIRMED'
   FROM restaurant_bank_statements
   WHERE tenant_id = :tenant_restaurant;
   ```
4. **Dépenses**  
   - Option rapide : vue matérialisée ou job ETL qui mappe `restaurant_depenses` → `finance_transactions` avec la catégorie finance correspondante.

## 4. Points de contrôle après backfill
- `restaurant_ingredients` : stock et coût unitaire cohérents avec `restaurant_stock_movements` et la vue `v_restaurant_stock_actuel`.
- `restaurant_plats` : marges recalculées via `/restaurant/plats/recompute-costs`.
- Finance : comptes, catégories et transactions présents pour l’entité Restaurant; rapprochement possible.

## 5. Tables supprimées / ignorées
- Tables V1 retirées : `ingredients`, `plats`, `plat_ingredients`, `plat_equivalences`, `bundle_items`, `categories`, `plat_categories`, `ingredient_conditionnements`, `stock_emplacements`, `stock_mouvements`, `productions`, `production_lots`.
- Tables “dormantes” non critiques : `event_log`, `audit_trail`, `financial_rules`, `analytic_axes`, `forecast_cache`, `supplier_scores`, `bank_reconciliations`, `vendor_aliases`, `margin_snapshots`, `inventory_intelligence`, `inventory_alerts`, `detected_anomalies` (peuvent rester vides tant que les features ne sont pas activées).
