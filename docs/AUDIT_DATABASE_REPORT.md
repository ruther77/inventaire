================================================================================
RAPPORT D'AUDIT DE LA BASE DE DONNEES
Date de generation: 2025-12-10T22:48:20.286898
================================================================================

## RESUME
- Erreurs critiques: 1
- Avertissements: 5
- Informations: 21

================================================================================
## ERREURS CRITIQUES
================================================================================

### Erreur #1
- Table: processed_invoices
- Categorie: NULL_FILE_PATH
- Message: 250 factures sans file_path
- Details: [2652, 2656, 2657, 2725, 2726, 2727, 2728, 2729, 2730, 2639]

================================================================================
## AVERTISSEMENTS
================================================================================

### Avertissement #1
- Table: produits
- Categorie: NULL_PRIX_VENTE
- Message: 499 produits sans prix de vente
- Details: [{'id': 4990, 'nom': 'CORDON BLEU 5X1KG'}, {'id': 4991, 'nom': 'FEUILLE SPRING ROLL 20X40PCS'}, {'id': 4992, 'nom': 'FILET DE POULET 10KG'}, {'id': 4993, 'nom': 'FRITE 10X1KG'}, {'id': 4994, 'nom': 'FRITE 4X2.5KG'}, {'id': 4995, 'nom': 'NUGGETS POULET 5X1KG'}, {'id': 4996, 'nom': 'POULET TANDOORI 11X1KG'}, {'id': 4997, 'nom': 'STEAK HACHE BOEUF 4KG VRAC'}, {'id': 4998, 'nom': 'PAROTTA NON CUIT 24X5PCS'}, {'id': 4956, 'nom': 'AIL 8X250G'}]

### Avertissement #2
- Table: produits
- Categorie: NULL_PRIX_ACHAT
- Message: 499 produits sans prix d'achat
- Details: [{'id': 4990, 'nom': 'CORDON BLEU 5X1KG'}, {'id': 4991, 'nom': 'FEUILLE SPRING ROLL 20X40PCS'}, {'id': 4992, 'nom': 'FILET DE POULET 10KG'}, {'id': 4993, 'nom': 'FRITE 10X1KG'}, {'id': 4994, 'nom': 'FRITE 4X2.5KG'}, {'id': 4995, 'nom': 'NUGGETS POULET 5X1KG'}, {'id': 4996, 'nom': 'POULET TANDOORI 11X1KG'}, {'id': 4997, 'nom': 'STEAK HACHE BOEUF 4KG VRAC'}, {'id': 4998, 'nom': 'PAROTTA NON CUIT 24X5PCS'}, {'id': 4956, 'nom': 'AIL 8X250G'}]

### Avertissement #3
- Table: finance_transactions
- Categorie: NULL_LABEL
- Message: 8973 transactions sans libelle
- Details: [144660, 144661, 144662, 144663, 144664, 144665, 144666, 144667, 144668, 144669]

### Avertissement #4
- Table: finance_transactions
- Categorie: POTENTIAL_DUPLICATES
- Message: 342 groupes de transactions potentiellement en double
- Details: [{'date': '2025-08-11', 'amount': 179.6, 'count': 2}, {'date': '2025-08-07', 'amount': 550.0, 'count': 2}, {'date': '2025-08-27', 'amount': 5.0, 'count': 2}, {'date': '2025-08-19', 'amount': 0.04, 'count': 2}, {'date': '2025-08-22', 'amount': 237.08, 'count': 2}, {'date': '2024-10-25', 'amount': 370.42, 'count': 3}, {'date': '2025-08-25', 'amount': 109.63, 'count': 2}, {'date': '2024-04-25', 'amount': 89.68, 'count': 3}, {'date': '2025-08-04', 'amount': 200.0, 'count': 2}, {'date': '2025-08-22', 'amount': 0.05, 'count': 2}]

### Avertissement #5
- Table: DATA_QUALITY
- Categorie: HIGH_STOCK
- Message: 4 produits avec stock > 10000
- Details: [{'id': 76, 'nom': 'GILBERT MAYONAISE', 'stock': 16200.0}, {'id': 8, 'nom': 'LEFFE BLONDE 6.6 BLE 33CL', 'stock': 14940.0}, {'id': 15, 'nom': 'ROCHES DES ECRINS PET', 'stock': 18720.0}, {'id': 3, 'nom': 'HEINEKEN 5D 65CL VP', 'stock': 49662.0}]

================================================================================
## STATISTIQUES DES TABLES
================================================================================
- [produits] Total: 1596 enregistrements
- [finance_transactions] Total: 8973 enregistrements
- [mouvements_stock] Total: 16033 enregistrements
- [restaurant_depenses] Total: 956 enregistrements
- [restaurant_plats] Total: 73 enregistrements
- [restaurant_ingredients] Total: 57 enregistrements
- [processed_invoices] Total: 529 enregistrements
- [finance_accounts] Total: 4 enregistrements
- [finance_categories] Total: 16 enregistrements
- [produits_barcodes] Total: 1702 enregistrements
- [produits_price_history] Total: 16396 enregistrements
- [vendor_aliases] Total: 0 enregistrements
- [tenants] Total: 4 enregistrements
- [app_users] Total: 1 enregistrements
- [finance_entities] Total: 3 enregistrements
- [supplier_scores] Total: 0 enregistrements
- [detected_anomalies] Total: 0 enregistrements
- [forecast_cache] Total: 0 enregistrements
- [audit_trail] Total: 0 enregistrements
- [bank_reconciliations] Total: 0 enregistrements
- [financial_rules] Total: 0 enregistrements

================================================================================
## RECOMMANDATIONS
================================================================================

### Priorite HAUTE (Erreurs critiques a corriger)

### Priorite MOYENNE (Avertissements a examiner)
- Completer les prix manquants dans produits
- Verifier les transactions en double dans finance_transactions

================================================================================
FIN DU RAPPORT
================================================================================