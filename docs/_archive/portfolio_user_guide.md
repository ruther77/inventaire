# Guide utilisateur – Interfaces épicerie / restaurant / portefeuille

## 1. Vues principales
- **Épicerie** (`/inventory`, `/supply`, `/audit`, etc.) : gère les `produits`, `codes-barres`, `mouvements_stock`, réappros, marges. Les hooks `useProducts`, `useSupplyPlan`, etc. consomment uniquement `/products`, `/supply/plan`, `/catalog`.
- **Restaurant** (`/charges`, `/menu`, `/bank-statement`) : gère `RestaurantIngredient`, `RestaurantPlat`, charges, relevés bancaires. Les hooks `useRestaurant*` appellent exclusivement `/restaurant/*`.
- **Portefeuille** (`/portfolio`) : vue globale qui affiche les snapshots par tenant, la trésorerie consolidée et les derniers prix (via `/capital/overview` + `/reports/export/capital_snapshot`).

## 2. Factures & price history
- Les imports `/invoices/import` / `/invoices/catalog/import` traitent des lignes brutes (`InvoiceLine`) sans prix de vente. C’est `PriceHistory` (table + vue `latest_price_history`) qui calcule les prix de vente ultérieurs.
- Tu peux alimenter la table manuellement via `scripts/generate_capital_snapshot.py` pour récolter les snapshots valorisés.

## 3. Job snapshot & monitoring
- Le job `capital-snapshot.service` (nota systemd) utilise `scripts/generate_capital_snapshot.py` et écrit dans `/var/log/capital_snapshot.log`.  
- Pour vérifier qu’il tourne :
  ```bash
  ./scripts/check_capital_snapshot.sh
  ```
  Il affiche les 20 dernières lignes du log et les 5 derniers snapshots.
- Pour garder le job actif, la timer `capital-snapshot.timer` déclenche tous les jours à 02h (édition en `/etc/systemd/system/capital-snapshot.timer`).

## 4. Auth & gardes
- Paramètre `ADMIN_API_KEY` dans `.env` pour protéger les routers épicerie/restaurant (`optional_api_key`).
- Les exports/reporting ont leur propre endpoint `GET /reports/export/{report_type}` (ajout `capital_snapshot` dans la liste).

## 5. Export portefeuille
- Depuis la page `Portefeuille`, clique sur « Télécharger le rapport capital » pour récupérer `rapport_capital.csv` ( fichier `reports/export`).
- Ce CSV regroupe `tenant_id`, `snapshot_date`, `stock_value`, `bank_balance`, `cash_balance`, `total_assets`.

Tu veux que je génère aussi une version imprimable (PDF) ou un mini-guide Markdown à donner à ton équipe financière ? 
