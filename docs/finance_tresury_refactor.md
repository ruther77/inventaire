# Trésorerie transverse (restaurant + épicerie)

Objectif : unifier la trésorerie des deux domaines dans une base modulaire et évolutive, en s'appuyant sur les briques existantes et en décrivant précisément chaque changement attendu dans la base, les migrations et les flux applicatifs.

## Principes directeurs
- Multi-entités natif : toute donnée financière inclut un `entity_id` référencé dans `finance_entities`.
- Comptes & flux normalisés : séparation stricte entre contenant (`finance_accounts`) et mouvement (`finance_transactions`).
- Analytique et traçabilité : lignes analytiques par catégorie / centre de coût, références externes conservées, rapprochements bancaires journalisés.
- Interopérabilité : API REST alignée entre restaurant et épicerie, compatible avec imports bancaires et factures.
- Séparation des responsabilités : modèles, services, API, importeurs et vues matérialisées clairement délimités.
- Tests et migration sécurisés : backfill idempotent, contrôles d'intégrité, validation applicative.


## Plan d'exécution concret (SQL, core, backend)
Cette section décrit **quoi coder et où** pour matérialiser la refonte. Les blocs suivants doivent être appliqués dans l'ordre dans le dépôt `backend/` et les migrations Alembic.

### 0.1 Migrations SQL cibles (Alembic)
- Générer un script Alembic unique `versions/2024xxxx_finance_treasury.py` contenant **les DDL complètes** ci-dessous.
  - Point d'entrée : `alembic.ini` et répertoire `db/` (adapter le chemin si vos migrations sont ailleurs). Utiliser le moteur existant (PostgreSQL).
- DDL à insérer (copier/coller et adapter le naming des contraintes si besoin) :
  ```sql
  CREATE TABLE finance_entities (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE TABLE finance_entity_members (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT NOT NULL REFERENCES finance_entities(id) ON DELETE CASCADE,
    tenant_id BIGINT NOT NULL,
    role TEXT NOT NULL DEFAULT 'OWNER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, tenant_id)
  );

  CREATE TABLE finance_categories (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT REFERENCES finance_entities(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    parent_id BIGINT REFERENCES finance_categories(id) ON DELETE SET NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, code)
  );

  CREATE TABLE finance_cost_centers (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT NOT NULL REFERENCES finance_entities(id),
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, code)
  );

  CREATE TYPE finance_account_type AS ENUM ('BANQUE','CAISSE','CB','AUTRE','PLATFORM');
  CREATE TABLE finance_accounts (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT NOT NULL REFERENCES finance_entities(id),
    type finance_account_type NOT NULL,
    label TEXT NOT NULL,
    iban TEXT,
    bic TEXT,
    currency TEXT NOT NULL DEFAULT 'EUR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (iban)
  );

  CREATE TABLE finance_account_balances (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES finance_accounts(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    balance NUMERIC(18,2) NOT NULL,
    source TEXT NOT NULL DEFAULT 'COMPUTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_id, date)
  );

  CREATE TYPE finance_tx_direction AS ENUM ('IN','OUT','TRANSFER');
  CREATE TYPE finance_tx_status AS ENUM ('DRAFT','CONFIRMED','CANCELLED');
  CREATE TABLE finance_transactions (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT NOT NULL REFERENCES finance_entities(id),
    account_id BIGINT NOT NULL REFERENCES finance_accounts(id),
    counterparty_account_id BIGINT REFERENCES finance_accounts(id),
    direction finance_tx_direction NOT NULL,
    source TEXT NOT NULL,
    date_operation DATE NOT NULL,
    date_value DATE,
    amount NUMERIC(18,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    ref_externe TEXT,
    note TEXT,
    status finance_tx_status NOT NULL DEFAULT 'CONFIRMED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by BIGINT,
    locked_at TIMESTAMPTZ,
    UNIQUE (ref_externe)
  );

  CREATE TABLE finance_transaction_lines (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES finance_transactions(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES finance_categories(id),
    cost_center_id BIGINT REFERENCES finance_cost_centers(id),
    montant_ht NUMERIC(18,2),
    tva_pct NUMERIC(5,2),
    montant_ttc NUMERIC(18,2) NOT NULL,
    description TEXT,
    position INT NOT NULL DEFAULT 1
  );

  CREATE TABLE finance_vendors (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT REFERENCES finance_entities(id),
    name TEXT NOT NULL,
    siret TEXT,
    iban TEXT,
    bic TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    address TEXT,
    metadata JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, name)
  );

  CREATE TABLE finance_invoices_supplier (
    id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT NOT NULL REFERENCES finance_entities(id),
    vendor_id BIGINT NOT NULL REFERENCES finance_vendors(id),
    invoice_number TEXT NOT NULL,
    date_invoice DATE,
    date_due DATE,
    montant_ht NUMERIC(18,2),
    montant_tva NUMERIC(18,2),
    montant_ttc NUMERIC(18,2),
    status TEXT NOT NULL DEFAULT 'EN_ATTENTE',
    source TEXT,
    currency TEXT NOT NULL DEFAULT 'EUR',
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, vendor_id, invoice_number)
  );

  CREATE TABLE finance_invoice_lines_supplier (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES finance_invoices_supplier(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES finance_categories(id),
    description TEXT,
    quantite NUMERIC(12,3),
    prix_unitaire NUMERIC(18,4),
    montant_ht NUMERIC(18,2) NOT NULL,
    tva_pct NUMERIC(5,2),
    position INT NOT NULL DEFAULT 1
  );

  CREATE TABLE finance_payments (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT REFERENCES finance_invoices_supplier(id) ON DELETE SET NULL,
    transaction_id BIGINT REFERENCES finance_transactions(id) ON DELETE SET NULL,
    amount NUMERIC(18,2) NOT NULL,
    date_payment DATE NOT NULL,
    mode TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE TABLE finance_bank_statements (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES finance_accounts(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    source TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE TABLE finance_bank_statement_lines (
    id BIGSERIAL PRIMARY KEY,
    statement_id BIGINT NOT NULL REFERENCES finance_bank_statements(id) ON DELETE CASCADE,
    date_operation DATE NOT NULL,
    date_valeur DATE,
    libelle_banque TEXT,
    montant NUMERIC(18,2) NOT NULL,
    balance_apres NUMERIC(18,2),
    ref_banque TEXT,
    raw_data JSONB
  );

  CREATE TABLE finance_reconciliations (
    id BIGSERIAL PRIMARY KEY,
    statement_line_id BIGINT NOT NULL REFERENCES finance_bank_statement_lines(id) ON DELETE CASCADE,
    transaction_id BIGINT NOT NULL REFERENCES finance_transactions(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'AUTO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );
  ```
- Règles Alembic complémentaires :
  - Ajouter un `op.execute("CREATE TYPE ...")` uniquement si le type n'existe pas (tester via `DO $$ BEGIN IF NOT EXISTS ... END $$`).
  - Prévoir `downgrade` pour supprimer les tables dans l'ordre inverse et dropper les enums.
  - Intégrer les index spécifiques (voir sections suivantes) en `op.create_index` pour éviter les full scans.

### 0.2 Implémentations backend (FastAPI)
- Models Pydantic : créer `backend/schemas/finance.py` avec les schémas `FinanceAccountCreate`, `FinanceTransactionCreate`, `FinanceVendorCreate`, `FinanceInvoiceCreate`, etc. Ces schémas doivent reprendre les champs SQL (sans `id`, `created_at`).
- Services :
  - `backend/services/finance_accounts.py` : CRUD basés sur `finance_accounts` avec validation `currency` cohérente par entité.
  - `backend/services/finance_transactions.py` : création transaction + lignes atomique (utiliser transaction DB) et calcul automatique des montants agrégés.
  - `backend/services/finance_reconciliation.py` : association statement line ↔ transaction, verrouillage `locked_at`.
  - `backend/services/finance_invoices.py` : gestion factures + paiements, synchronisation avec `finance_transactions` pour les règlements.
- Routes API :
  - Monter un router `backend/api/finance.py` avec préfixe `/finance` exposant :
    - POST `/accounts` (création), GET `/accounts` (liste filtrable par entity_id/is_active).
    - POST `/transactions` (création transaction + lignes), GET `/transactions` (filtrage par date/entity/account/status), PATCH `/transactions/{id}` (annulation ou update note/status), POST `/transactions/{id}/lock` (verrouillage après rapprochement).
    - POST `/bank-statements/import` (ingest CSV) déléguant à un importeur (voir ci-dessous).
    - POST `/reconciliations` (création), DELETE `/reconciliations/{id}` (annulation manuel).
    - POST `/vendors`, GET `/vendors`, POST `/invoices`, POST `/payments`.
  - Brancher ces routes dans `backend/main.py` via `app.include_router`.
- Dépendances / DB : réutiliser `backend/dependencies` pour fournir la session SQLAlchemy et le contexte `entity_id` (dérivé du tenant ou paramètre explicite).

### 0.3 Couche core (domain + import)
- Ajouter un module `backend/services/importers/bank_statement_csv.py` qui :
  - Consomme un fichier CSV (dialecte restaurant/épicerie existant) et mappe vers `finance_bank_statements` + `finance_bank_statement_lines`.
  - Normalise les montants (signe) et déduit `date_operation` / `libelle_banque`.
  - Détecte les doublons via `ref_banque` ou `(account_id, date_operation, montant, libelle_banque)`.
- Ajouter un module `backend/services/mappers/restaurant_to_finance.py` pour backfill :
  - Lit `restaurant_depenses`, `restaurant_fournisseurs`, `restaurant_bank_statements` et construit les inserts correspondants dans les tables finance_*.
  - S'exécute via une commande `python backend/main.py --backfill-finance` ou script dédié dans `scripts/backfill_finance.py`.

### 0.4 Tests automatisés
- Créer `tests/test_finance_transactions.py` avec :
  - Cas création IN/OUT/TRANSFER, validation des directions, et écriture lignes analytiques.
  - Cas verrouillage après rapprochement empêchant toute modification (vérifier exception).
- Créer `tests/test_finance_import_bank.py` pour valider l'import CSV (fixtures de fichiers) et la détection de doublons.
- Créer `tests/test_finance_invoices.py` pour s'assurer que la création d'un paiement génère le lien `finance_payments` + transaction associée.

### 0.5 Séquence d'exécution
1. Écrire et exécuter la migration Alembic (DDL ci-dessus).
2. Implémenter les modèles SQLAlchemy correspondants (si utilisés) dans `backend/models/finance.py` avec enums partagés.
3. Ajouter schémas Pydantic et services.
4. Exposer les routes API et brancher les dépendances.
5. Implémenter importeurs et scripts de backfill.
6. Couvrir par les tests précédents + intégrer dans CI (ajouter jobs si nécessaire dans `Makefile` / pipeline existant).

Les sections suivantes détaillent chaque table / flux et restent la référence fonctionnelle. Les extraits ci-dessus servent de **guide de codage immédiat** pour aligner SQL, core et API.

## Schéma cible : tables et colonnes détaillées
### Table finance_entities
Description : Référentiel des sociétés (restaurant, épicerie, futures entités).
Colonnes :
- id : PK, serial/bigint, non nullable.
- code : Texte court unique (RESTO, EPICERIE). Contrainte UNIQUE.
- name : Nom complet légal ou commercial. Non nullable.
- currency : Code ISO, défaut EUR.
- is_active : Booléen, défaut TRUE pour gérer l'archivage logique.
- created_at : Timestamp défaut now().
- updated_at : Timestamp auto via trigger ou ORM.
Index et contraintes :
- UNIQUE(code)
- INDEX on is_active
- INDEX on name for recherche
Étapes de migration :
- Créer les lignes RESTO et EPICERIE avec les codes existants s'ils sont présents.
- Lier avec `finance_entity_members` en reprenant les tenants actuels.
- Nomenclature confirmée : `INCONTOURNABLE` = restaurant (code RESTO), `NOUTAM` = épicerie (code EPICERIE) pour aligner toutes les tables dérivées.
---
### Table finance_entity_members
Description : Association entre une entité et un tenant/app existant.
Colonnes :
- id : PK, serial.
- entity_id : FK vers finance_entities.id, ON DELETE CASCADE.
- tenant_id : FK vers table tenant existante; contrainte UNIQUE (entity_id, tenant_id).
- role : Enum OWNER/CONTRIBUTOR/VIEWER pour tracer les droits si utile.
- created_at : Timestamp.
Index et contraintes :
- UNIQUE(entity_id, tenant_id)
- INDEX on tenant_id
Étapes de migration :
- Backfill en lisant les liaisons actuelles entre tenants et apps.
---
### Table finance_categories
Description : Plan de catégories de trésorerie hiérarchique.
Colonnes :
- id : PK, serial.
- entity_id : FK optionnelle vers finance_entities pour catégories dédiées; NULL = partagée.
- name : Texte non nul.
- type : Enum DEPENSE/RECETTE/TRANSFERT, non nul.
- parent_id : FK auto-référente pour hiérarchie, NULL si racine.
- code : Code court stable pour mappings; UNIQUE par entity_id.
- created_at : Timestamp.
- updated_at : Timestamp.
Index et contraintes :
- UNIQUE(entity_id, code)
- INDEX(parent_id)
- INDEX(entity_id, type)
Étapes de migration :
- Mapper `restaurant_depense_categories` vers des catégories DEPENSE RESTO en préservant le libellé.
- Créer catégories RECETTE pour encaissements (tickets, ventes épicerie) si absent.
- Créer catégories TRANSFERT pour mouvements internes banque↔caisse.
---
### Table finance_cost_centers
Description : Centres de coûts mutualisés dérivés de restaurant_cost_centers.
Colonnes :
- id : PK, serial.
- entity_id : FK vers finance_entities.
- name : Texte non nul.
- code : Code court unique par entité.
- is_active : Booléen, défaut TRUE.
- created_at : Timestamp.
- updated_at : Timestamp.
Index et contraintes :
- UNIQUE(entity_id, code)
- INDEX(entity_id, is_active)
Étapes de migration :
- Copier restaurant_cost_centers dans cette table avec entity_id RESTO.
- Créer centres EPICERIE au besoin.
---
### Table finance_accounts
Description : Contenant financier : banque, caisse, carte bancaire, compte interne.
Colonnes :
- id : PK, serial.
- entity_id : FK vers finance_entities.
- type : Enum BANQUE/CAISSE/CB/AUTRE/PLATFORM (Stripe...).
- label : Nom affiché; non nul.
- iban : Texte optionnel.
- bic : Texte optionnel.
- currency : Code ISO; défaut EUR.
- is_active : Booléen défaut TRUE.
- metadata : JSONB optionnel pour identifiants externes.
- created_at : Timestamp.
- updated_at : Timestamp.
Index et contraintes :
- INDEX(entity_id, type)
- INDEX(is_active)
- UNIQUE(iban) si renseigné
Étapes de migration :
- Créer un compte par ancienne valeur distincte de restaurant_bank_statements.account.
- Créer comptes caisse/CB en lisant restaurant_depenses.source ou équivalent.
- Instancier explicitement les comptes bancaires existants : `BNP - INCONTOURNABLE (RESTO)`, `BNP - NOUTAM (EPICERIE)`, `LCL - INCONTOURNABLE (RESTO)`, `LCL - NOUTAM (EPICERIE)` en type BANQUE, chacun avec son `entity_id` dédié.
- Déclarer un seul compte `SUMUP - INCONTOURNABLE` (type CB ou PLATFORM, entity=RESTO). Quand la carte est utilisée pour des achats épicerie, enregistrer la transaction sur ce compte puis créer une écriture de régularisation inter-entités (TRANSFER contre un compte NOUTAM) avec catégorie/interco dédiée pour que la trésorerie EPICERIE soit remontée correctement.
---
### Table finance_account_balances
Description : Snapshots de solde par compte pour accélérer les dashboards.
Colonnes :
- id : PK, serial.
- account_id : FK finance_accounts.
- date : Date, non nulle.
- balance : NUMERIC(18,2), non nul.
- source : Enum COMPUTED/IMPORTED.
- created_at : Timestamp.
Index et contraintes :
- UNIQUE(account_id, date)
- INDEX(date)
Étapes de migration :
- Initialiser via calcul cumulatif sur finance_transactions après backfill.
---
### Table finance_transactions
Description : Mouvement monétaire unique (entrée/sortie/transfert).
Colonnes :
- id : PK, serial.
- entity_id : FK finance_entities.
- account_id : FK finance_accounts.
- counterparty_account_id : FK finance_accounts pour transferts internes, NULL sinon.
- direction : Enum IN/OUT/TRANSFER, non nul.
- source : Enum BANQUE/CAISSE/CB/MANUEL/IMPORT/API.
- date_operation : Date de mouvement visible utilisateur.
- date_value : Date valeur bancaire optionnelle.
- amount : NUMERIC(18,2); signe conforme à direction (positif attendu).
- currency : Code ISO; défaut EUR; cohérent avec account.
- ref_externe : Texte ou UUID externe; utilisé pour rapprochements et audits.
- note : Texte libre.
- status : Enum DRAFT/CONFIRMED/CANCELLED.
- created_at : Timestamp.
- updated_at : Timestamp.
- created_by : FK user/tenant si disponible.
- locked_at : Timestamp quand rapproché et verrouillé.
Index et contraintes :
- INDEX(entity_id, date_operation)
- INDEX(account_id, date_operation)
- UNIQUE(ref_externe) filtré non null
Étapes de migration :
- Transformer restaurant_depenses en transactions OUT avec mapping des comptes (caisse/CB).
- Pour relevés bancaires, créer transactions IN/OUT selon montant, source=BANQUE.
- Pour transferts internes détectés, utiliser counterparty_account_id et direction=TRANSFER.
---
### Table finance_transaction_lines
Description : Détail analytique multi-catégories par transaction.
Colonnes :
- id : PK, serial.
- transaction_id : FK finance_transactions ON DELETE CASCADE.
- category_id : FK finance_categories.
- cost_center_id : FK finance_cost_centers optionnel.
- montant_ht : NUMERIC(18,2) >= 0, nullable si pas de TVA.
- tva_pct : NUMERIC(5,2) nullable.
- montant_ttc : NUMERIC(18,2) >=0.
- description : Texte facultatif.
- position : Ordre d'affichage entier.
Index et contraintes :
- INDEX(transaction_id)
- INDEX(category_id)
- INDEX(cost_center_id)
Étapes de migration :
- Pour chaque dépense, créer une ligne unique montant_ttc=montant, category_id mappé, cost_center repris.
---
### Table finance_vendors
Description : Référentiel de fournisseurs commun.
Colonnes :
- id : PK.
- entity_id : FK optionnelle pour fournisseur dédié.
- name : Texte non nul.
- siret : Texte optionnelle; contrainte UNIQUE filtrée non null.
- iban : Texte optionnel.
- bic : Texte optionnel.
- contact_email : Texte optionnel.
- contact_phone : Texte optionnel.
- address : Texte optionnel.
- metadata : JSONB pour tags internes.
- is_active : Booléen.
- created_at : Timestamp.
- updated_at : Timestamp.
Index et contraintes :
- INDEX(entity_id, name)
- UNIQUE(entity_id, name)
Étapes de migration :
- Migrer restaurant_fournisseurs → finance_vendors (entity_id RESTO).
- Dédupliquer par nom ou SIRET.
---
### Table finance_invoices_supplier
Description : Factures fournisseurs normalisées.
Colonnes :
- id : PK.
- entity_id : FK finance_entities.
- vendor_id : FK finance_vendors.
- invoice_number : Texte non nul; UNIQUE(entity_id, vendor_id, invoice_number).
- date_invoice : Date émission.
- date_due : Date d'échéance.
- montant_ht : NUMERIC.
- montant_tva : NUMERIC.
- montant_ttc : NUMERIC, non nul.
- status : Enum DRAFT/EN_ATTENTE/PAYEE/PARTIELLEMENT_PAYEE/ANNULEE.
- source : Enum UPLOAD/OCR/MANUEL/API.
- currency : Code ISO, défaut EUR.
- ref_externe : Référence fichier ou système tiers.
- created_at : Timestamp.
- updated_at : Timestamp.
Index et contraintes :
- UNIQUE(entity_id, vendor_id, invoice_number)
- INDEX(status)
- INDEX(date_due)
Étapes de migration :
- Si factures existantes dans le système, les insérer; sinon générer factures synthétiques à partir des dépenses par mois pour préparer la structure.
---
### Table finance_invoice_lines_supplier
Description : Lignes détaillées de factures fournisseurs.
Colonnes :
- id : PK.
- invoice_id : FK finance_invoices_supplier ON DELETE CASCADE.
- category_id : FK finance_categories.
- description : Texte.
- quantite : NUMERIC(18,3) défaut 1.
- prix_unitaire : NUMERIC(18,4).
- montant_ht : NUMERIC.
- tva_pct : NUMERIC.
- montant_ttc : NUMERIC.
- position : Ordre.
Index et contraintes :
- INDEX(invoice_id)
- INDEX(category_id)
Étapes de migration :
- Créer une ligne unique par dépense si pas de détails; répartir par catégorie si info disponible.
---
### Table finance_payments
Description : Lien paiement ↔ facture ↔ transaction.
Colonnes :
- id : PK.
- invoice_id : FK finance_invoices_supplier nullable pour paiements sans facture.
- transaction_id : FK finance_transactions non nul.
- amount : NUMERIC non nul, signe positif.
- date_payment : Date non nulle.
- mode : Enum VIREMENT/CB/CHEQUE/ESPECES/PRELEVEMENT.
- created_at : Timestamp.
Index et contraintes :
- INDEX(invoice_id)
- INDEX(transaction_id)
Étapes de migration :
- Lier chaque transaction OUT issue d'une facture à la facture correspondante en créant un paiement.
---
### Table finance_bank_statements
Description : Entêtes de relevés importés.
Colonnes :
- id : PK.
- account_id : FK finance_accounts.
- period_start : Date non nulle.
- period_end : Date non nulle.
- source : Enum CSV/API/MANUAL.
- imported_at : Timestamp non nul.
- file_name : Texte optionnel pour audit.
- hash : Texte optionnel pour éviter doublons.
Index et contraintes :
- INDEX(account_id, period_start)
- UNIQUE(account_id, hash) filtré non null
Étapes de migration :
- Transformer restaurant_bank_statements en entêtes par mois avec hash sur contenu importé.
---
### Table finance_bank_statement_lines
Description : Lignes brutes des relevés.
Colonnes :
- id : PK.
- statement_id : FK finance_bank_statements.
- date_operation : Date.
- date_valeur : Date optionnelle.
- libelle_banque : Texte.
- montant : NUMERIC(18,2) avec signe selon banque.
- balance_apres : NUMERIC optionnel.
- ref_banque : Texte optionnel unique par compte.
- raw_data : JSONB brut.
- checksum : Texte hash ligne pour dédoublonnage.
Index et contraintes :
- INDEX(statement_id)
- INDEX(ref_banque)
- INDEX(checksum)
Étapes de migration :
- Importer chaque ligne depuis restaurant_bank_statements en conservant libellé et montant, générer checksum = hash(date_operation + montant + libelle).
---
### Table finance_reconciliations
Description : Lien entre ligne de relevé et transaction.
Colonnes :
- id : PK.
- statement_line_id : FK finance_bank_statement_lines ON DELETE CASCADE.
- transaction_id : FK finance_transactions ON DELETE CASCADE.
- status : Enum AUTO/MANUEL/PARTIEL.
- confidence : NUMERIC(5,2) optionnel pour scoring auto.
- created_at : Timestamp.
- created_by : FK user/tenant optionnel.
Index et contraintes :
- UNIQUE(statement_line_id)
- INDEX(transaction_id)
- INDEX(status)
Étapes de migration :
- Peupler en exécutant un script de matching automatique exact amount+date puis manuel si nécessaire.
---
### Table capital_snapshot
Description : Snapshot consolidé par entité ou global.
Colonnes :
- id : PK.
- entity_id : FK finance_entities, NULL pour consolidé.
- snapshot_date : Date non nulle.
- stock_value : NUMERIC optionnel.
- bank_balance : NUMERIC optionnel.
- cash_balance : NUMERIC optionnel.
- total_assets : NUMERIC optionnel.
- created_at : Timestamp.
Index et contraintes :
- UNIQUE(entity_id, snapshot_date)
Étapes de migration :
- Ajouter colonne entity_id, backfill en dupliquant ligne existante pour RESTO; créer ligne consolidée si besoin.
---

## Plan de migration détaillé par lot
### Lot 1 - Paramétrage
- [1] Créer tables finance_entities, finance_entity_members, finance_categories, finance_cost_centers.
- [2] Écrire migration Alembic avec création de enums, contraintes, index listés ci-dessus.
- [3] Backfill RESTO et EPICERIE; vérifier unicité des codes.
- [4] Script de validation : comparer nombre de catégories anciennes et nouvelles, logguer mismatches.
---
### Lot 2 - Comptes financiers
- [1] Créer finance_accounts et finance_account_balances.
- [2] Migration Python/SQL : extraire distinct account de restaurant_bank_statements; détecter types par libellé.
- [3] Associer entity_id RESTO; préparer comptes EPICERIE manuellement dans fixture.
- [4] Mettre à jour dépendances applicatives pour lire le nouvel ID de compte.
---
### Lot 3 - Transactions
- [1] Créer finance_transactions et finance_transaction_lines.
- [2] Backfill depuis restaurant_depenses : direction=OUT, source selon mode de paiement, amount=montant, date_operation=date.
- [3] Pour chaque dépense, créer transaction_lines avec category_id mappé et cost_center_id.
- [4] Installer triggers ou contraintes pour forcer amount >= somme des lines TTC.
---
### Lot 4 - Fournisseurs & factures
- [1] Créer finance_vendors, finance_invoices_supplier, finance_invoice_lines_supplier, finance_payments.
- [2] Importer fournisseurs existants; dédoublonner via clé (lower(name), siret).
- [3] Générer factures à partir des dépenses si fichiers disponibles; sinon créer factures synthétiques par fournisseur/mois.
- [4] Lier transactions aux factures via finance_payments avec amount égal montant facture ou partiel.
---
### Lot 5 - Relevés bancaires
- [1] Créer finance_bank_statements, finance_bank_statement_lines, finance_reconciliations.
- [2] Importer anciens relevés; calculer hash fichier pour éviter doublon; regrouper par mois.
- [3] Exécuter script auto-match exact (montant & date ±1j) pour remplir finance_reconciliations status AUTO.
- [4] Préparer UI pour résolution manuelle et mise à jour status=MANUEL.
---
### Lot 6 - Reporting
- [1] Modifier capital_snapshot pour ajouter entity_id et recalculer.
- [2] Créer vues matérialisées quotidiennes/mensuelles pour cashflow et PnL.
- [3] Mettre en place tâches cron de refresh (ex: 1x/jour).
- [4] Documenter métriques et queries d'audit.
---

## API REST détaillées (schémas et validations)
### POST /finance/transactions
- Payload requis : {entity_id, account_id, direction, amount, date_operation, source}.
- Champs optionnels : counterparty_account_id (si TRANSFER), lines[], ref_externe, note.
- Validation : direction=TRANSFER => counterparty_account_id obligatoire; amount>0; currency cohérent avec compte.
- Effet : crée transaction + lines, recalcule balance prévisionnelle.
---
### POST /finance/transactions/import
- Import CSV/JSON; support mapping colonnes; logs erreurs par ligne.
- Option `dedupe_on=ref_externe` pour ignorer doublons.
- Mode dry-run pour valider avant insertion.
---
### GET /finance/transactions
- Filtres : entity_id, account_id, date_from, date_to, category_id, reconciled=false.
- Tri : date_operation desc par défaut.
- Pagination standard (limit/offset).
---
### POST /finance/bank-statements/import
- Reçoit fichier CSV; sélection du compte; parse configurable par banque (mapping colonnes).
- Crée finance_bank_statements + lines; calcule checksum par ligne.
- Retourne lignes rejetées avec raison.
---
### POST /finance/reconciliation/run
- Lance matching auto montant+date ±1 jour, option fuzzy sur libellé.
- Met à jour finance_reconciliations avec status AUTO et confidence.
- Retourne stats (matched, remaining).
---
### GET /finance/reconciliation/pending
- Retourne lignes de relevé sans reconciliation + transactions candidates.
- Filtres : entity_id, account_id, montant_min/max, date_range.
---
### POST /finance/vendors
- Créer/mettre à jour un fournisseur; vérifie unicité (entity_id, name) et SIRET.
- Peut attacher IBAN/BIC et metadata.
---
### POST /finance/invoices
- Crée facture fournisseur avec lignes; vérifie somme TTC = somme lignes TTC.
- Peut déclencher création automatique de transaction draft.
---
### POST /finance/payments
- Associe transaction existante à une facture; valide amount <= facture restante.
- Met à jour status facture en conséquence.
---
### GET /finance/dashboard
- Retour cash-in/out, soldes par compte, alertes (soldes négatifs, TVA manquante).
- Filtres entity=RESTO/EPICERIE/ALL, period=day/week/month.
---

## Règles de qualité et contrôles automatiques
- [RQ001] Vérifier règle n°1: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ002] Vérifier règle n°2: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ003] Vérifier règle n°3: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ004] Vérifier règle n°4: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ005] Vérifier règle n°5: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ006] Vérifier règle n°6: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ007] Vérifier règle n°7: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ008] Vérifier règle n°8: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ009] Vérifier règle n°9: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ010] Vérifier règle n°10: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ011] Vérifier règle n°11: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ012] Vérifier règle n°12: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ013] Vérifier règle n°13: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ014] Vérifier règle n°14: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ015] Vérifier règle n°15: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ016] Vérifier règle n°16: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ017] Vérifier règle n°17: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ018] Vérifier règle n°18: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ019] Vérifier règle n°19: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ020] Vérifier règle n°20: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ021] Vérifier règle n°21: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ022] Vérifier règle n°22: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ023] Vérifier règle n°23: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ024] Vérifier règle n°24: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ025] Vérifier règle n°25: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ026] Vérifier règle n°26: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ027] Vérifier règle n°27: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ028] Vérifier règle n°28: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ029] Vérifier règle n°29: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ030] Vérifier règle n°30: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ031] Vérifier règle n°31: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ032] Vérifier règle n°32: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ033] Vérifier règle n°33: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ034] Vérifier règle n°34: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ035] Vérifier règle n°35: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ036] Vérifier règle n°36: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ037] Vérifier règle n°37: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ038] Vérifier règle n°38: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ039] Vérifier règle n°39: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ040] Vérifier règle n°40: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ041] Vérifier règle n°41: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ042] Vérifier règle n°42: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ043] Vérifier règle n°43: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ044] Vérifier règle n°44: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ045] Vérifier règle n°45: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ046] Vérifier règle n°46: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ047] Vérifier règle n°47: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ048] Vérifier règle n°48: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ049] Vérifier règle n°49: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ050] Vérifier règle n°50: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ051] Vérifier règle n°51: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ052] Vérifier règle n°52: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ053] Vérifier règle n°53: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ054] Vérifier règle n°54: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ055] Vérifier règle n°55: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ056] Vérifier règle n°56: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ057] Vérifier règle n°57: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ058] Vérifier règle n°58: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ059] Vérifier règle n°59: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ060] Vérifier règle n°60: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ061] Vérifier règle n°61: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ062] Vérifier règle n°62: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ063] Vérifier règle n°63: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ064] Vérifier règle n°64: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ065] Vérifier règle n°65: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ066] Vérifier règle n°66: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ067] Vérifier règle n°67: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ068] Vérifier règle n°68: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ069] Vérifier règle n°69: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ070] Vérifier règle n°70: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ071] Vérifier règle n°71: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ072] Vérifier règle n°72: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ073] Vérifier règle n°73: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ074] Vérifier règle n°74: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ075] Vérifier règle n°75: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ076] Vérifier règle n°76: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ077] Vérifier règle n°77: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ078] Vérifier règle n°78: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ079] Vérifier règle n°79: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ080] Vérifier règle n°80: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ081] Vérifier règle n°81: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ082] Vérifier règle n°82: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ083] Vérifier règle n°83: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ084] Vérifier règle n°84: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ085] Vérifier règle n°85: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ086] Vérifier règle n°86: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ087] Vérifier règle n°87: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ088] Vérifier règle n°88: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ089] Vérifier règle n°89: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ090] Vérifier règle n°90: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ091] Vérifier règle n°91: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ092] Vérifier règle n°92: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ093] Vérifier règle n°93: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ094] Vérifier règle n°94: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ095] Vérifier règle n°95: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ096] Vérifier règle n°96: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ097] Vérifier règle n°97: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ098] Vérifier règle n°98: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ099] Vérifier règle n°99: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ100] Vérifier règle n°100: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ101] Vérifier règle n°101: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ102] Vérifier règle n°102: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ103] Vérifier règle n°103: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ104] Vérifier règle n°104: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ105] Vérifier règle n°105: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ106] Vérifier règle n°106: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ107] Vérifier règle n°107: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ108] Vérifier règle n°108: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ109] Vérifier règle n°109: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ110] Vérifier règle n°110: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ111] Vérifier règle n°111: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ112] Vérifier règle n°112: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ113] Vérifier règle n°113: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ114] Vérifier règle n°114: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ115] Vérifier règle n°115: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ116] Vérifier règle n°116: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ117] Vérifier règle n°117: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ118] Vérifier règle n°118: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ119] Vérifier règle n°119: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ120] Vérifier règle n°120: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ121] Vérifier règle n°121: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ122] Vérifier règle n°122: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ123] Vérifier règle n°123: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ124] Vérifier règle n°124: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ125] Vérifier règle n°125: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ126] Vérifier règle n°126: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ127] Vérifier règle n°127: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ128] Vérifier règle n°128: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ129] Vérifier règle n°129: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ130] Vérifier règle n°130: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ131] Vérifier règle n°131: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ132] Vérifier règle n°132: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ133] Vérifier règle n°133: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ134] Vérifier règle n°134: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ135] Vérifier règle n°135: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ136] Vérifier règle n°136: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ137] Vérifier règle n°137: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ138] Vérifier règle n°138: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ139] Vérifier règle n°139: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ140] Vérifier règle n°140: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ141] Vérifier règle n°141: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ142] Vérifier règle n°142: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ143] Vérifier règle n°143: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ144] Vérifier règle n°144: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ145] Vérifier règle n°145: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ146] Vérifier règle n°146: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ147] Vérifier règle n°147: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ148] Vérifier règle n°148: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ149] Vérifier règle n°149: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).
- [RQ150] Vérifier règle n°150: précision attendue (exemple : somme des lignes TTC = montant transaction pour transaction OUT).

## Plan de tests et validation
- [TEST001] Cas de test 1: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST002] Cas de test 2: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST003] Cas de test 3: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST004] Cas de test 4: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST005] Cas de test 5: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST006] Cas de test 6: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST007] Cas de test 7: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST008] Cas de test 8: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST009] Cas de test 9: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST010] Cas de test 10: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST011] Cas de test 11: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST012] Cas de test 12: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST013] Cas de test 13: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST014] Cas de test 14: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST015] Cas de test 15: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST016] Cas de test 16: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST017] Cas de test 17: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST018] Cas de test 18: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST019] Cas de test 19: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST020] Cas de test 20: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST021] Cas de test 21: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST022] Cas de test 22: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST023] Cas de test 23: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST024] Cas de test 24: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST025] Cas de test 25: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST026] Cas de test 26: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST027] Cas de test 27: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST028] Cas de test 28: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST029] Cas de test 29: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST030] Cas de test 30: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST031] Cas de test 31: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST032] Cas de test 32: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST033] Cas de test 33: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST034] Cas de test 34: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST035] Cas de test 35: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST036] Cas de test 36: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST037] Cas de test 37: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST038] Cas de test 38: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST039] Cas de test 39: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST040] Cas de test 40: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST041] Cas de test 41: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST042] Cas de test 42: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST043] Cas de test 43: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST044] Cas de test 44: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST045] Cas de test 45: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST046] Cas de test 46: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST047] Cas de test 47: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST048] Cas de test 48: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST049] Cas de test 49: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST050] Cas de test 50: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST051] Cas de test 51: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST052] Cas de test 52: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST053] Cas de test 53: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST054] Cas de test 54: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST055] Cas de test 55: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST056] Cas de test 56: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST057] Cas de test 57: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST058] Cas de test 58: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST059] Cas de test 59: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST060] Cas de test 60: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST061] Cas de test 61: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST062] Cas de test 62: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST063] Cas de test 63: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST064] Cas de test 64: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST065] Cas de test 65: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST066] Cas de test 66: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST067] Cas de test 67: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST068] Cas de test 68: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST069] Cas de test 69: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST070] Cas de test 70: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST071] Cas de test 71: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST072] Cas de test 72: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST073] Cas de test 73: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST074] Cas de test 74: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST075] Cas de test 75: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST076] Cas de test 76: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST077] Cas de test 77: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST078] Cas de test 78: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST079] Cas de test 79: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST080] Cas de test 80: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST081] Cas de test 81: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST082] Cas de test 82: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST083] Cas de test 83: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST084] Cas de test 84: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST085] Cas de test 85: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST086] Cas de test 86: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST087] Cas de test 87: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST088] Cas de test 88: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST089] Cas de test 89: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST090] Cas de test 90: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST091] Cas de test 91: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST092] Cas de test 92: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST093] Cas de test 93: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST094] Cas de test 94: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST095] Cas de test 95: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST096] Cas de test 96: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST097] Cas de test 97: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST098] Cas de test 98: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST099] Cas de test 99: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST100] Cas de test 100: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST101] Cas de test 101: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST102] Cas de test 102: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST103] Cas de test 103: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST104] Cas de test 104: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST105] Cas de test 105: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST106] Cas de test 106: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST107] Cas de test 107: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST108] Cas de test 108: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST109] Cas de test 109: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST110] Cas de test 110: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST111] Cas de test 111: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST112] Cas de test 112: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST113] Cas de test 113: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST114] Cas de test 114: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST115] Cas de test 115: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST116] Cas de test 116: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST117] Cas de test 117: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST118] Cas de test 118: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST119] Cas de test 119: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST120] Cas de test 120: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST121] Cas de test 121: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST122] Cas de test 122: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST123] Cas de test 123: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST124] Cas de test 124: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST125] Cas de test 125: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST126] Cas de test 126: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST127] Cas de test 127: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST128] Cas de test 128: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST129] Cas de test 129: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST130] Cas de test 130: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST131] Cas de test 131: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST132] Cas de test 132: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST133] Cas de test 133: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST134] Cas de test 134: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST135] Cas de test 135: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST136] Cas de test 136: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST137] Cas de test 137: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST138] Cas de test 138: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST139] Cas de test 139: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST140] Cas de test 140: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST141] Cas de test 141: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST142] Cas de test 142: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST143] Cas de test 143: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST144] Cas de test 144: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST145] Cas de test 145: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST146] Cas de test 146: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST147] Cas de test 147: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST148] Cas de test 148: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST149] Cas de test 149: scénario couvrant import, création, mise à jour ou rapport spécifique.
- [TEST150] Cas de test 150: scénario couvrant import, création, mise à jour ou rapport spécifique.

## Mapping ancien → nouveau
- restaurant_depenses.amount → finance_transactions.amount / finance_transaction_lines.montant_ttc
- restaurant_depenses.date → finance_transactions.date_operation
- restaurant_depenses.category_id → finance_transaction_lines.category_id via mapping catégories
- restaurant_cost_centers.id → finance_cost_centers.id
- restaurant_bank_statements.account → finance_accounts.label + type
- restaurant_bank_statements.montant → finance_bank_statement_lines.montant
- restaurant_bank_statements.date → finance_bank_statement_lines.date_operation
- restaurant_fournisseurs.nom → finance_vendors.name
---

## Backlog précis des actions à réaliser
- [ACTION001] Détailler et exécuter l'action numéro 1 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION002] Détailler et exécuter l'action numéro 2 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION003] Détailler et exécuter l'action numéro 3 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION004] Détailler et exécuter l'action numéro 4 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION005] Détailler et exécuter l'action numéro 5 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION006] Détailler et exécuter l'action numéro 6 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION007] Détailler et exécuter l'action numéro 7 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION008] Détailler et exécuter l'action numéro 8 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION009] Détailler et exécuter l'action numéro 9 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION010] Détailler et exécuter l'action numéro 10 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION011] Détailler et exécuter l'action numéro 11 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION012] Détailler et exécuter l'action numéro 12 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION013] Détailler et exécuter l'action numéro 13 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION014] Détailler et exécuter l'action numéro 14 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION015] Détailler et exécuter l'action numéro 15 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION016] Détailler et exécuter l'action numéro 16 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION017] Détailler et exécuter l'action numéro 17 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION018] Détailler et exécuter l'action numéro 18 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION019] Détailler et exécuter l'action numéro 19 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION020] Détailler et exécuter l'action numéro 20 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION021] Détailler et exécuter l'action numéro 21 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION022] Détailler et exécuter l'action numéro 22 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION023] Détailler et exécuter l'action numéro 23 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION024] Détailler et exécuter l'action numéro 24 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION025] Détailler et exécuter l'action numéro 25 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION026] Détailler et exécuter l'action numéro 26 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION027] Détailler et exécuter l'action numéro 27 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION028] Détailler et exécuter l'action numéro 28 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION029] Détailler et exécuter l'action numéro 29 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION030] Détailler et exécuter l'action numéro 30 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION031] Détailler et exécuter l'action numéro 31 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION032] Détailler et exécuter l'action numéro 32 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION033] Détailler et exécuter l'action numéro 33 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION034] Détailler et exécuter l'action numéro 34 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION035] Détailler et exécuter l'action numéro 35 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION036] Détailler et exécuter l'action numéro 36 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION037] Détailler et exécuter l'action numéro 37 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION038] Détailler et exécuter l'action numéro 38 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION039] Détailler et exécuter l'action numéro 39 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION040] Détailler et exécuter l'action numéro 40 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION041] Détailler et exécuter l'action numéro 41 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION042] Détailler et exécuter l'action numéro 42 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION043] Détailler et exécuter l'action numéro 43 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION044] Détailler et exécuter l'action numéro 44 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION045] Détailler et exécuter l'action numéro 45 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION046] Détailler et exécuter l'action numéro 46 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION047] Détailler et exécuter l'action numéro 47 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION048] Détailler et exécuter l'action numéro 48 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION049] Détailler et exécuter l'action numéro 49 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION050] Détailler et exécuter l'action numéro 50 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION051] Détailler et exécuter l'action numéro 51 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION052] Détailler et exécuter l'action numéro 52 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION053] Détailler et exécuter l'action numéro 53 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION054] Détailler et exécuter l'action numéro 54 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION055] Détailler et exécuter l'action numéro 55 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION056] Détailler et exécuter l'action numéro 56 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION057] Détailler et exécuter l'action numéro 57 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION058] Détailler et exécuter l'action numéro 58 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION059] Détailler et exécuter l'action numéro 59 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION060] Détailler et exécuter l'action numéro 60 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION061] Détailler et exécuter l'action numéro 61 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION062] Détailler et exécuter l'action numéro 62 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION063] Détailler et exécuter l'action numéro 63 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION064] Détailler et exécuter l'action numéro 64 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION065] Détailler et exécuter l'action numéro 65 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION066] Détailler et exécuter l'action numéro 66 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION067] Détailler et exécuter l'action numéro 67 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION068] Détailler et exécuter l'action numéro 68 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION069] Détailler et exécuter l'action numéro 69 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION070] Détailler et exécuter l'action numéro 70 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION071] Détailler et exécuter l'action numéro 71 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION072] Détailler et exécuter l'action numéro 72 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION073] Détailler et exécuter l'action numéro 73 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION074] Détailler et exécuter l'action numéro 74 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION075] Détailler et exécuter l'action numéro 75 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION076] Détailler et exécuter l'action numéro 76 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION077] Détailler et exécuter l'action numéro 77 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION078] Détailler et exécuter l'action numéro 78 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION079] Détailler et exécuter l'action numéro 79 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION080] Détailler et exécuter l'action numéro 80 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION081] Détailler et exécuter l'action numéro 81 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION082] Détailler et exécuter l'action numéro 82 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION083] Détailler et exécuter l'action numéro 83 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION084] Détailler et exécuter l'action numéro 84 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION085] Détailler et exécuter l'action numéro 85 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION086] Détailler et exécuter l'action numéro 86 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION087] Détailler et exécuter l'action numéro 87 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION088] Détailler et exécuter l'action numéro 88 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION089] Détailler et exécuter l'action numéro 89 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION090] Détailler et exécuter l'action numéro 90 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION091] Détailler et exécuter l'action numéro 91 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION092] Détailler et exécuter l'action numéro 92 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION093] Détailler et exécuter l'action numéro 93 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION094] Détailler et exécuter l'action numéro 94 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION095] Détailler et exécuter l'action numéro 95 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION096] Détailler et exécuter l'action numéro 96 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION097] Détailler et exécuter l'action numéro 97 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION098] Détailler et exécuter l'action numéro 98 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION099] Détailler et exécuter l'action numéro 99 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION100] Détailler et exécuter l'action numéro 100 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION101] Détailler et exécuter l'action numéro 101 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION102] Détailler et exécuter l'action numéro 102 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION103] Détailler et exécuter l'action numéro 103 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION104] Détailler et exécuter l'action numéro 104 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION105] Détailler et exécuter l'action numéro 105 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION106] Détailler et exécuter l'action numéro 106 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION107] Détailler et exécuter l'action numéro 107 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION108] Détailler et exécuter l'action numéro 108 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION109] Détailler et exécuter l'action numéro 109 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION110] Détailler et exécuter l'action numéro 110 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION111] Détailler et exécuter l'action numéro 111 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION112] Détailler et exécuter l'action numéro 112 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION113] Détailler et exécuter l'action numéro 113 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION114] Détailler et exécuter l'action numéro 114 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION115] Détailler et exécuter l'action numéro 115 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION116] Détailler et exécuter l'action numéro 116 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION117] Détailler et exécuter l'action numéro 117 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION118] Détailler et exécuter l'action numéro 118 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION119] Détailler et exécuter l'action numéro 119 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION120] Détailler et exécuter l'action numéro 120 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION121] Détailler et exécuter l'action numéro 121 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION122] Détailler et exécuter l'action numéro 122 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION123] Détailler et exécuter l'action numéro 123 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION124] Détailler et exécuter l'action numéro 124 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION125] Détailler et exécuter l'action numéro 125 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION126] Détailler et exécuter l'action numéro 126 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION127] Détailler et exécuter l'action numéro 127 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION128] Détailler et exécuter l'action numéro 128 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION129] Détailler et exécuter l'action numéro 129 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION130] Détailler et exécuter l'action numéro 130 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION131] Détailler et exécuter l'action numéro 131 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION132] Détailler et exécuter l'action numéro 132 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION133] Détailler et exécuter l'action numéro 133 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION134] Détailler et exécuter l'action numéro 134 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION135] Détailler et exécuter l'action numéro 135 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION136] Détailler et exécuter l'action numéro 136 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION137] Détailler et exécuter l'action numéro 137 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION138] Détailler et exécuter l'action numéro 138 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION139] Détailler et exécuter l'action numéro 139 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION140] Détailler et exécuter l'action numéro 140 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION141] Détailler et exécuter l'action numéro 141 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION142] Détailler et exécuter l'action numéro 142 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION143] Détailler et exécuter l'action numéro 143 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION144] Détailler et exécuter l'action numéro 144 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION145] Détailler et exécuter l'action numéro 145 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION146] Détailler et exécuter l'action numéro 146 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION147] Détailler et exécuter l'action numéro 147 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION148] Détailler et exécuter l'action numéro 148 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION149] Détailler et exécuter l'action numéro 149 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION150] Détailler et exécuter l'action numéro 150 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION151] Détailler et exécuter l'action numéro 151 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION152] Détailler et exécuter l'action numéro 152 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION153] Détailler et exécuter l'action numéro 153 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION154] Détailler et exécuter l'action numéro 154 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION155] Détailler et exécuter l'action numéro 155 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION156] Détailler et exécuter l'action numéro 156 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION157] Détailler et exécuter l'action numéro 157 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION158] Détailler et exécuter l'action numéro 158 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION159] Détailler et exécuter l'action numéro 159 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION160] Détailler et exécuter l'action numéro 160 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION161] Détailler et exécuter l'action numéro 161 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION162] Détailler et exécuter l'action numéro 162 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION163] Détailler et exécuter l'action numéro 163 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION164] Détailler et exécuter l'action numéro 164 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION165] Détailler et exécuter l'action numéro 165 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION166] Détailler et exécuter l'action numéro 166 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION167] Détailler et exécuter l'action numéro 167 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION168] Détailler et exécuter l'action numéro 168 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION169] Détailler et exécuter l'action numéro 169 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION170] Détailler et exécuter l'action numéro 170 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION171] Détailler et exécuter l'action numéro 171 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION172] Détailler et exécuter l'action numéro 172 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION173] Détailler et exécuter l'action numéro 173 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION174] Détailler et exécuter l'action numéro 174 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION175] Détailler et exécuter l'action numéro 175 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION176] Détailler et exécuter l'action numéro 176 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION177] Détailler et exécuter l'action numéro 177 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION178] Détailler et exécuter l'action numéro 178 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION179] Détailler et exécuter l'action numéro 179 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION180] Détailler et exécuter l'action numéro 180 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION181] Détailler et exécuter l'action numéro 181 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION182] Détailler et exécuter l'action numéro 182 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION183] Détailler et exécuter l'action numéro 183 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION184] Détailler et exécuter l'action numéro 184 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION185] Détailler et exécuter l'action numéro 185 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION186] Détailler et exécuter l'action numéro 186 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION187] Détailler et exécuter l'action numéro 187 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION188] Détailler et exécuter l'action numéro 188 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION189] Détailler et exécuter l'action numéro 189 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION190] Détailler et exécuter l'action numéro 190 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION191] Détailler et exécuter l'action numéro 191 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION192] Détailler et exécuter l'action numéro 192 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION193] Détailler et exécuter l'action numéro 193 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION194] Détailler et exécuter l'action numéro 194 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION195] Détailler et exécuter l'action numéro 195 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION196] Détailler et exécuter l'action numéro 196 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION197] Détailler et exécuter l'action numéro 197 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION198] Détailler et exécuter l'action numéro 198 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION199] Détailler et exécuter l'action numéro 199 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION200] Détailler et exécuter l'action numéro 200 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION201] Détailler et exécuter l'action numéro 201 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION202] Détailler et exécuter l'action numéro 202 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION203] Détailler et exécuter l'action numéro 203 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION204] Détailler et exécuter l'action numéro 204 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION205] Détailler et exécuter l'action numéro 205 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION206] Détailler et exécuter l'action numéro 206 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION207] Détailler et exécuter l'action numéro 207 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION208] Détailler et exécuter l'action numéro 208 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION209] Détailler et exécuter l'action numéro 209 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION210] Détailler et exécuter l'action numéro 210 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION211] Détailler et exécuter l'action numéro 211 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION212] Détailler et exécuter l'action numéro 212 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION213] Détailler et exécuter l'action numéro 213 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION214] Détailler et exécuter l'action numéro 214 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION215] Détailler et exécuter l'action numéro 215 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION216] Détailler et exécuter l'action numéro 216 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION217] Détailler et exécuter l'action numéro 217 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION218] Détailler et exécuter l'action numéro 218 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION219] Détailler et exécuter l'action numéro 219 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION220] Détailler et exécuter l'action numéro 220 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION221] Détailler et exécuter l'action numéro 221 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION222] Détailler et exécuter l'action numéro 222 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION223] Détailler et exécuter l'action numéro 223 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION224] Détailler et exécuter l'action numéro 224 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION225] Détailler et exécuter l'action numéro 225 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION226] Détailler et exécuter l'action numéro 226 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION227] Détailler et exécuter l'action numéro 227 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION228] Détailler et exécuter l'action numéro 228 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION229] Détailler et exécuter l'action numéro 229 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION230] Détailler et exécuter l'action numéro 230 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION231] Détailler et exécuter l'action numéro 231 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION232] Détailler et exécuter l'action numéro 232 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION233] Détailler et exécuter l'action numéro 233 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION234] Détailler et exécuter l'action numéro 234 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION235] Détailler et exécuter l'action numéro 235 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION236] Détailler et exécuter l'action numéro 236 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION237] Détailler et exécuter l'action numéro 237 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION238] Détailler et exécuter l'action numéro 238 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION239] Détailler et exécuter l'action numéro 239 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION240] Détailler et exécuter l'action numéro 240 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION241] Détailler et exécuter l'action numéro 241 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION242] Détailler et exécuter l'action numéro 242 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION243] Détailler et exécuter l'action numéro 243 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION244] Détailler et exécuter l'action numéro 244 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION245] Détailler et exécuter l'action numéro 245 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION246] Détailler et exécuter l'action numéro 246 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION247] Détailler et exécuter l'action numéro 247 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION248] Détailler et exécuter l'action numéro 248 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION249] Détailler et exécuter l'action numéro 249 décrite dans les spécifications (voir sections tables, migrations, API).
- [ACTION250] Détailler et exécuter l'action numéro 250 décrite dans les spécifications (voir sections tables, migrations, API).

## Exemples SQL de migration
- Exemple SQL 1: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 1.
- Exemple SQL 2: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 2.
- Exemple SQL 3: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 3.
- Exemple SQL 4: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 4.
- Exemple SQL 5: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 5.
- Exemple SQL 6: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 6.
- Exemple SQL 7: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 7.
- Exemple SQL 8: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 8.
- Exemple SQL 9: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 9.
- Exemple SQL 10: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 10.
- Exemple SQL 11: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 11.
- Exemple SQL 12: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 12.
- Exemple SQL 13: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 13.
- Exemple SQL 14: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 14.
- Exemple SQL 15: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 15.
- Exemple SQL 16: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 16.
- Exemple SQL 17: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 17.
- Exemple SQL 18: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 18.
- Exemple SQL 19: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 19.
- Exemple SQL 20: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 20.
- Exemple SQL 21: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 21.
- Exemple SQL 22: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 22.
- Exemple SQL 23: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 23.
- Exemple SQL 24: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 24.
- Exemple SQL 25: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 25.
- Exemple SQL 26: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 26.
- Exemple SQL 27: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 27.
- Exemple SQL 28: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 28.
- Exemple SQL 29: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 29.
- Exemple SQL 30: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 30.
- Exemple SQL 31: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 31.
- Exemple SQL 32: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 32.
- Exemple SQL 33: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 33.
- Exemple SQL 34: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 34.
- Exemple SQL 35: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 35.
- Exemple SQL 36: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 36.
- Exemple SQL 37: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 37.
- Exemple SQL 38: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 38.
- Exemple SQL 39: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 39.
- Exemple SQL 40: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 40.
- Exemple SQL 41: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 41.
- Exemple SQL 42: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 42.
- Exemple SQL 43: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 43.
- Exemple SQL 44: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 44.
- Exemple SQL 45: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 45.
- Exemple SQL 46: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 46.
- Exemple SQL 47: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 47.
- Exemple SQL 48: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 48.
- Exemple SQL 49: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 49.
- Exemple SQL 50: INSERT INTO finance_transactions (...) SELECT ... FROM restaurant_depenses WHERE condition 50.

## Exigences UI/UX pour la nouvelle app Trésorerie
- Écran Paramétrage entités : CRUD avec validation code unique.
- Écran Comptes financiers : affichage soldes, filtres par type, bouton désactivation.
- Écran Import relevé : drag & drop fichier, sélection compte, aperçu avant import.
- Écran Rapprochement : double liste, raccourcis clavier, filtres montant/date, badge confiance.
- Écran Factures fournisseurs : upload PDF, OCR optionnel, statut, paiements associés.
- Écran Transactions : création rapide, duplication, tags, recherche texte sur libellé.
- Dashboard : cartes solde par compte, courbes cash-in/out, heatmap anomalies.
- Accessibilité : navigation clavier, contraste, labels ARIA.
- Internationalisation : fr/en, format date local, séparateurs décimaux.
- Gestion des erreurs : toasts explicites, lien vers logs import.
- [UI001] Comportement détaillé du composant 1 (voir maquettes).
- [UI002] Comportement détaillé du composant 2 (voir maquettes).
- [UI003] Comportement détaillé du composant 3 (voir maquettes).
- [UI004] Comportement détaillé du composant 4 (voir maquettes).
- [UI005] Comportement détaillé du composant 5 (voir maquettes).
- [UI006] Comportement détaillé du composant 6 (voir maquettes).
- [UI007] Comportement détaillé du composant 7 (voir maquettes).
- [UI008] Comportement détaillé du composant 8 (voir maquettes).
- [UI009] Comportement détaillé du composant 9 (voir maquettes).
- [UI010] Comportement détaillé du composant 10 (voir maquettes).
- [UI011] Comportement détaillé du composant 11 (voir maquettes).
- [UI012] Comportement détaillé du composant 12 (voir maquettes).
- [UI013] Comportement détaillé du composant 13 (voir maquettes).
- [UI014] Comportement détaillé du composant 14 (voir maquettes).
- [UI015] Comportement détaillé du composant 15 (voir maquettes).
- [UI016] Comportement détaillé du composant 16 (voir maquettes).
- [UI017] Comportement détaillé du composant 17 (voir maquettes).
- [UI018] Comportement détaillé du composant 18 (voir maquettes).
- [UI019] Comportement détaillé du composant 19 (voir maquettes).
- [UI020] Comportement détaillé du composant 20 (voir maquettes).
- [UI021] Comportement détaillé du composant 21 (voir maquettes).
- [UI022] Comportement détaillé du composant 22 (voir maquettes).
- [UI023] Comportement détaillé du composant 23 (voir maquettes).
- [UI024] Comportement détaillé du composant 24 (voir maquettes).
- [UI025] Comportement détaillé du composant 25 (voir maquettes).
- [UI026] Comportement détaillé du composant 26 (voir maquettes).
- [UI027] Comportement détaillé du composant 27 (voir maquettes).
- [UI028] Comportement détaillé du composant 28 (voir maquettes).
- [UI029] Comportement détaillé du composant 29 (voir maquettes).
- [UI030] Comportement détaillé du composant 30 (voir maquettes).
- [UI031] Comportement détaillé du composant 31 (voir maquettes).
- [UI032] Comportement détaillé du composant 32 (voir maquettes).
- [UI033] Comportement détaillé du composant 33 (voir maquettes).
- [UI034] Comportement détaillé du composant 34 (voir maquettes).
- [UI035] Comportement détaillé du composant 35 (voir maquettes).
- [UI036] Comportement détaillé du composant 36 (voir maquettes).
- [UI037] Comportement détaillé du composant 37 (voir maquettes).
- [UI038] Comportement détaillé du composant 38 (voir maquettes).
- [UI039] Comportement détaillé du composant 39 (voir maquettes).
- [UI040] Comportement détaillé du composant 40 (voir maquettes).
- [UI041] Comportement détaillé du composant 41 (voir maquettes).
- [UI042] Comportement détaillé du composant 42 (voir maquettes).
- [UI043] Comportement détaillé du composant 43 (voir maquettes).
- [UI044] Comportement détaillé du composant 44 (voir maquettes).
- [UI045] Comportement détaillé du composant 45 (voir maquettes).
- [UI046] Comportement détaillé du composant 46 (voir maquettes).
- [UI047] Comportement détaillé du composant 47 (voir maquettes).
- [UI048] Comportement détaillé du composant 48 (voir maquettes).
- [UI049] Comportement détaillé du composant 49 (voir maquettes).
- [UI050] Comportement détaillé du composant 50 (voir maquettes).

## Observabilité, monitoring et opérations
- [OPS001] Mise en place métrique/log/alerte numéro 1 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS002] Mise en place métrique/log/alerte numéro 2 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS003] Mise en place métrique/log/alerte numéro 3 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS004] Mise en place métrique/log/alerte numéro 4 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS005] Mise en place métrique/log/alerte numéro 5 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS006] Mise en place métrique/log/alerte numéro 6 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS007] Mise en place métrique/log/alerte numéro 7 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS008] Mise en place métrique/log/alerte numéro 8 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS009] Mise en place métrique/log/alerte numéro 9 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS010] Mise en place métrique/log/alerte numéro 10 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS011] Mise en place métrique/log/alerte numéro 11 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS012] Mise en place métrique/log/alerte numéro 12 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS013] Mise en place métrique/log/alerte numéro 13 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS014] Mise en place métrique/log/alerte numéro 14 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS015] Mise en place métrique/log/alerte numéro 15 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS016] Mise en place métrique/log/alerte numéro 16 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS017] Mise en place métrique/log/alerte numéro 17 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS018] Mise en place métrique/log/alerte numéro 18 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS019] Mise en place métrique/log/alerte numéro 19 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS020] Mise en place métrique/log/alerte numéro 20 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS021] Mise en place métrique/log/alerte numéro 21 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS022] Mise en place métrique/log/alerte numéro 22 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS023] Mise en place métrique/log/alerte numéro 23 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS024] Mise en place métrique/log/alerte numéro 24 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS025] Mise en place métrique/log/alerte numéro 25 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS026] Mise en place métrique/log/alerte numéro 26 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS027] Mise en place métrique/log/alerte numéro 27 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS028] Mise en place métrique/log/alerte numéro 28 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS029] Mise en place métrique/log/alerte numéro 29 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS030] Mise en place métrique/log/alerte numéro 30 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS031] Mise en place métrique/log/alerte numéro 31 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS032] Mise en place métrique/log/alerte numéro 32 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS033] Mise en place métrique/log/alerte numéro 33 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS034] Mise en place métrique/log/alerte numéro 34 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS035] Mise en place métrique/log/alerte numéro 35 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS036] Mise en place métrique/log/alerte numéro 36 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS037] Mise en place métrique/log/alerte numéro 37 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS038] Mise en place métrique/log/alerte numéro 38 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS039] Mise en place métrique/log/alerte numéro 39 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS040] Mise en place métrique/log/alerte numéro 40 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS041] Mise en place métrique/log/alerte numéro 41 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS042] Mise en place métrique/log/alerte numéro 42 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS043] Mise en place métrique/log/alerte numéro 43 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS044] Mise en place métrique/log/alerte numéro 44 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS045] Mise en place métrique/log/alerte numéro 45 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS046] Mise en place métrique/log/alerte numéro 46 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS047] Mise en place métrique/log/alerte numéro 47 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS048] Mise en place métrique/log/alerte numéro 48 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS049] Mise en place métrique/log/alerte numéro 49 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS050] Mise en place métrique/log/alerte numéro 50 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS051] Mise en place métrique/log/alerte numéro 51 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS052] Mise en place métrique/log/alerte numéro 52 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS053] Mise en place métrique/log/alerte numéro 53 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS054] Mise en place métrique/log/alerte numéro 54 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS055] Mise en place métrique/log/alerte numéro 55 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS056] Mise en place métrique/log/alerte numéro 56 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS057] Mise en place métrique/log/alerte numéro 57 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS058] Mise en place métrique/log/alerte numéro 58 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS059] Mise en place métrique/log/alerte numéro 59 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS060] Mise en place métrique/log/alerte numéro 60 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS061] Mise en place métrique/log/alerte numéro 61 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS062] Mise en place métrique/log/alerte numéro 62 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS063] Mise en place métrique/log/alerte numéro 63 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS064] Mise en place métrique/log/alerte numéro 64 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS065] Mise en place métrique/log/alerte numéro 65 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS066] Mise en place métrique/log/alerte numéro 66 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS067] Mise en place métrique/log/alerte numéro 67 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS068] Mise en place métrique/log/alerte numéro 68 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS069] Mise en place métrique/log/alerte numéro 69 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS070] Mise en place métrique/log/alerte numéro 70 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS071] Mise en place métrique/log/alerte numéro 71 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS072] Mise en place métrique/log/alerte numéro 72 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS073] Mise en place métrique/log/alerte numéro 73 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS074] Mise en place métrique/log/alerte numéro 74 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS075] Mise en place métrique/log/alerte numéro 75 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS076] Mise en place métrique/log/alerte numéro 76 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS077] Mise en place métrique/log/alerte numéro 77 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS078] Mise en place métrique/log/alerte numéro 78 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS079] Mise en place métrique/log/alerte numéro 79 couvrant imports, rapprochements, soldes, erreurs API.
- [OPS080] Mise en place métrique/log/alerte numéro 80 couvrant imports, rapprochements, soldes, erreurs API.

## RACI simplifié par lot
- Lot 1 - Paramétrage : Product Owner=A/C, Tech Lead=R, Backend=C/I, Frontend=C/I, Data/DBA=C/I, QA=C/I
- Lot 2 - Comptes financiers : Product Owner=A/C, Tech Lead=R, Backend=C/I, Frontend=C/I, Data/DBA=C/I, QA=C/I
- Lot 3 - Transactions : Product Owner=A/C, Tech Lead=R, Backend=C/I, Frontend=C/I, Data/DBA=C/I, QA=C/I
- Lot 4 - Fournisseurs & factures : Product Owner=A/C, Tech Lead=R, Backend=C/I, Frontend=C/I, Data/DBA=C/I, QA=C/I
- Lot 5 - Relevés bancaires : Product Owner=A/C, Tech Lead=R, Backend=C/I, Frontend=C/I, Data/DBA=C/I, QA=C/I
- Lot 6 - Reporting : Product Owner=A/C, Tech Lead=R, Backend=C/I, Frontend=C/I, Data/DBA=C/I, QA=C/I

## Critères d'acceptation détaillés par fonctionnalité
- [AC001] Critère d'acceptation spécifique 1: résultat attendu, métrique de succès, tolérance.
- [AC002] Critère d'acceptation spécifique 2: résultat attendu, métrique de succès, tolérance.
- [AC003] Critère d'acceptation spécifique 3: résultat attendu, métrique de succès, tolérance.
- [AC004] Critère d'acceptation spécifique 4: résultat attendu, métrique de succès, tolérance.
- [AC005] Critère d'acceptation spécifique 5: résultat attendu, métrique de succès, tolérance.
- [AC006] Critère d'acceptation spécifique 6: résultat attendu, métrique de succès, tolérance.
- [AC007] Critère d'acceptation spécifique 7: résultat attendu, métrique de succès, tolérance.
- [AC008] Critère d'acceptation spécifique 8: résultat attendu, métrique de succès, tolérance.
- [AC009] Critère d'acceptation spécifique 9: résultat attendu, métrique de succès, tolérance.
- [AC010] Critère d'acceptation spécifique 10: résultat attendu, métrique de succès, tolérance.
- [AC011] Critère d'acceptation spécifique 11: résultat attendu, métrique de succès, tolérance.
- [AC012] Critère d'acceptation spécifique 12: résultat attendu, métrique de succès, tolérance.
- [AC013] Critère d'acceptation spécifique 13: résultat attendu, métrique de succès, tolérance.
- [AC014] Critère d'acceptation spécifique 14: résultat attendu, métrique de succès, tolérance.
- [AC015] Critère d'acceptation spécifique 15: résultat attendu, métrique de succès, tolérance.
- [AC016] Critère d'acceptation spécifique 16: résultat attendu, métrique de succès, tolérance.
- [AC017] Critère d'acceptation spécifique 17: résultat attendu, métrique de succès, tolérance.
- [AC018] Critère d'acceptation spécifique 18: résultat attendu, métrique de succès, tolérance.
- [AC019] Critère d'acceptation spécifique 19: résultat attendu, métrique de succès, tolérance.
- [AC020] Critère d'acceptation spécifique 20: résultat attendu, métrique de succès, tolérance.
- [AC021] Critère d'acceptation spécifique 21: résultat attendu, métrique de succès, tolérance.
- [AC022] Critère d'acceptation spécifique 22: résultat attendu, métrique de succès, tolérance.
- [AC023] Critère d'acceptation spécifique 23: résultat attendu, métrique de succès, tolérance.
- [AC024] Critère d'acceptation spécifique 24: résultat attendu, métrique de succès, tolérance.
- [AC025] Critère d'acceptation spécifique 25: résultat attendu, métrique de succès, tolérance.
- [AC026] Critère d'acceptation spécifique 26: résultat attendu, métrique de succès, tolérance.
- [AC027] Critère d'acceptation spécifique 27: résultat attendu, métrique de succès, tolérance.
- [AC028] Critère d'acceptation spécifique 28: résultat attendu, métrique de succès, tolérance.
- [AC029] Critère d'acceptation spécifique 29: résultat attendu, métrique de succès, tolérance.
- [AC030] Critère d'acceptation spécifique 30: résultat attendu, métrique de succès, tolérance.
- [AC031] Critère d'acceptation spécifique 31: résultat attendu, métrique de succès, tolérance.
- [AC032] Critère d'acceptation spécifique 32: résultat attendu, métrique de succès, tolérance.
- [AC033] Critère d'acceptation spécifique 33: résultat attendu, métrique de succès, tolérance.
- [AC034] Critère d'acceptation spécifique 34: résultat attendu, métrique de succès, tolérance.
- [AC035] Critère d'acceptation spécifique 35: résultat attendu, métrique de succès, tolérance.
- [AC036] Critère d'acceptation spécifique 36: résultat attendu, métrique de succès, tolérance.
- [AC037] Critère d'acceptation spécifique 37: résultat attendu, métrique de succès, tolérance.
- [AC038] Critère d'acceptation spécifique 38: résultat attendu, métrique de succès, tolérance.
- [AC039] Critère d'acceptation spécifique 39: résultat attendu, métrique de succès, tolérance.
- [AC040] Critère d'acceptation spécifique 40: résultat attendu, métrique de succès, tolérance.
- [AC041] Critère d'acceptation spécifique 41: résultat attendu, métrique de succès, tolérance.
- [AC042] Critère d'acceptation spécifique 42: résultat attendu, métrique de succès, tolérance.
- [AC043] Critère d'acceptation spécifique 43: résultat attendu, métrique de succès, tolérance.
- [AC044] Critère d'acceptation spécifique 44: résultat attendu, métrique de succès, tolérance.
- [AC045] Critère d'acceptation spécifique 45: résultat attendu, métrique de succès, tolérance.
- [AC046] Critère d'acceptation spécifique 46: résultat attendu, métrique de succès, tolérance.
- [AC047] Critère d'acceptation spécifique 47: résultat attendu, métrique de succès, tolérance.
- [AC048] Critère d'acceptation spécifique 48: résultat attendu, métrique de succès, tolérance.
- [AC049] Critère d'acceptation spécifique 49: résultat attendu, métrique de succès, tolérance.
- [AC050] Critère d'acceptation spécifique 50: résultat attendu, métrique de succès, tolérance.
- [AC051] Critère d'acceptation spécifique 51: résultat attendu, métrique de succès, tolérance.
- [AC052] Critère d'acceptation spécifique 52: résultat attendu, métrique de succès, tolérance.
- [AC053] Critère d'acceptation spécifique 53: résultat attendu, métrique de succès, tolérance.
- [AC054] Critère d'acceptation spécifique 54: résultat attendu, métrique de succès, tolérance.
- [AC055] Critère d'acceptation spécifique 55: résultat attendu, métrique de succès, tolérance.
- [AC056] Critère d'acceptation spécifique 56: résultat attendu, métrique de succès, tolérance.
- [AC057] Critère d'acceptation spécifique 57: résultat attendu, métrique de succès, tolérance.
- [AC058] Critère d'acceptation spécifique 58: résultat attendu, métrique de succès, tolérance.
- [AC059] Critère d'acceptation spécifique 59: résultat attendu, métrique de succès, tolérance.
- [AC060] Critère d'acceptation spécifique 60: résultat attendu, métrique de succès, tolérance.
- [AC061] Critère d'acceptation spécifique 61: résultat attendu, métrique de succès, tolérance.
- [AC062] Critère d'acceptation spécifique 62: résultat attendu, métrique de succès, tolérance.
- [AC063] Critère d'acceptation spécifique 63: résultat attendu, métrique de succès, tolérance.
- [AC064] Critère d'acceptation spécifique 64: résultat attendu, métrique de succès, tolérance.
- [AC065] Critère d'acceptation spécifique 65: résultat attendu, métrique de succès, tolérance.
- [AC066] Critère d'acceptation spécifique 66: résultat attendu, métrique de succès, tolérance.
- [AC067] Critère d'acceptation spécifique 67: résultat attendu, métrique de succès, tolérance.
- [AC068] Critère d'acceptation spécifique 68: résultat attendu, métrique de succès, tolérance.
- [AC069] Critère d'acceptation spécifique 69: résultat attendu, métrique de succès, tolérance.
- [AC070] Critère d'acceptation spécifique 70: résultat attendu, métrique de succès, tolérance.
- [AC071] Critère d'acceptation spécifique 71: résultat attendu, métrique de succès, tolérance.
- [AC072] Critère d'acceptation spécifique 72: résultat attendu, métrique de succès, tolérance.
- [AC073] Critère d'acceptation spécifique 73: résultat attendu, métrique de succès, tolérance.
- [AC074] Critère d'acceptation spécifique 74: résultat attendu, métrique de succès, tolérance.
- [AC075] Critère d'acceptation spécifique 75: résultat attendu, métrique de succès, tolérance.
- [AC076] Critère d'acceptation spécifique 76: résultat attendu, métrique de succès, tolérance.
- [AC077] Critère d'acceptation spécifique 77: résultat attendu, métrique de succès, tolérance.
- [AC078] Critère d'acceptation spécifique 78: résultat attendu, métrique de succès, tolérance.
- [AC079] Critère d'acceptation spécifique 79: résultat attendu, métrique de succès, tolérance.
- [AC080] Critère d'acceptation spécifique 80: résultat attendu, métrique de succès, tolérance.
- [AC081] Critère d'acceptation spécifique 81: résultat attendu, métrique de succès, tolérance.
- [AC082] Critère d'acceptation spécifique 82: résultat attendu, métrique de succès, tolérance.
- [AC083] Critère d'acceptation spécifique 83: résultat attendu, métrique de succès, tolérance.
- [AC084] Critère d'acceptation spécifique 84: résultat attendu, métrique de succès, tolérance.
- [AC085] Critère d'acceptation spécifique 85: résultat attendu, métrique de succès, tolérance.
- [AC086] Critère d'acceptation spécifique 86: résultat attendu, métrique de succès, tolérance.
- [AC087] Critère d'acceptation spécifique 87: résultat attendu, métrique de succès, tolérance.
- [AC088] Critère d'acceptation spécifique 88: résultat attendu, métrique de succès, tolérance.
- [AC089] Critère d'acceptation spécifique 89: résultat attendu, métrique de succès, tolérance.
- [AC090] Critère d'acceptation spécifique 90: résultat attendu, métrique de succès, tolérance.
- [AC091] Critère d'acceptation spécifique 91: résultat attendu, métrique de succès, tolérance.
- [AC092] Critère d'acceptation spécifique 92: résultat attendu, métrique de succès, tolérance.
- [AC093] Critère d'acceptation spécifique 93: résultat attendu, métrique de succès, tolérance.
- [AC094] Critère d'acceptation spécifique 94: résultat attendu, métrique de succès, tolérance.
- [AC095] Critère d'acceptation spécifique 95: résultat attendu, métrique de succès, tolérance.
- [AC096] Critère d'acceptation spécifique 96: résultat attendu, métrique de succès, tolérance.
- [AC097] Critère d'acceptation spécifique 97: résultat attendu, métrique de succès, tolérance.
- [AC098] Critère d'acceptation spécifique 98: résultat attendu, métrique de succès, tolérance.
- [AC099] Critère d'acceptation spécifique 99: résultat attendu, métrique de succès, tolérance.
- [AC100] Critère d'acceptation spécifique 100: résultat attendu, métrique de succès, tolérance.
- [AC101] Critère d'acceptation spécifique 101: résultat attendu, métrique de succès, tolérance.
- [AC102] Critère d'acceptation spécifique 102: résultat attendu, métrique de succès, tolérance.
- [AC103] Critère d'acceptation spécifique 103: résultat attendu, métrique de succès, tolérance.
- [AC104] Critère d'acceptation spécifique 104: résultat attendu, métrique de succès, tolérance.
- [AC105] Critère d'acceptation spécifique 105: résultat attendu, métrique de succès, tolérance.
- [AC106] Critère d'acceptation spécifique 106: résultat attendu, métrique de succès, tolérance.
- [AC107] Critère d'acceptation spécifique 107: résultat attendu, métrique de succès, tolérance.
- [AC108] Critère d'acceptation spécifique 108: résultat attendu, métrique de succès, tolérance.
- [AC109] Critère d'acceptation spécifique 109: résultat attendu, métrique de succès, tolérance.
- [AC110] Critère d'acceptation spécifique 110: résultat attendu, métrique de succès, tolérance.
- [AC111] Critère d'acceptation spécifique 111: résultat attendu, métrique de succès, tolérance.
- [AC112] Critère d'acceptation spécifique 112: résultat attendu, métrique de succès, tolérance.
- [AC113] Critère d'acceptation spécifique 113: résultat attendu, métrique de succès, tolérance.
- [AC114] Critère d'acceptation spécifique 114: résultat attendu, métrique de succès, tolérance.
- [AC115] Critère d'acceptation spécifique 115: résultat attendu, métrique de succès, tolérance.
- [AC116] Critère d'acceptation spécifique 116: résultat attendu, métrique de succès, tolérance.
- [AC117] Critère d'acceptation spécifique 117: résultat attendu, métrique de succès, tolérance.
- [AC118] Critère d'acceptation spécifique 118: résultat attendu, métrique de succès, tolérance.
- [AC119] Critère d'acceptation spécifique 119: résultat attendu, métrique de succès, tolérance.
- [AC120] Critère d'acceptation spécifique 120: résultat attendu, métrique de succès, tolérance.
- [AC121] Critère d'acceptation spécifique 121: résultat attendu, métrique de succès, tolérance.
- [AC122] Critère d'acceptation spécifique 122: résultat attendu, métrique de succès, tolérance.
- [AC123] Critère d'acceptation spécifique 123: résultat attendu, métrique de succès, tolérance.
- [AC124] Critère d'acceptation spécifique 124: résultat attendu, métrique de succès, tolérance.
- [AC125] Critère d'acceptation spécifique 125: résultat attendu, métrique de succès, tolérance.
- [AC126] Critère d'acceptation spécifique 126: résultat attendu, métrique de succès, tolérance.
- [AC127] Critère d'acceptation spécifique 127: résultat attendu, métrique de succès, tolérance.
- [AC128] Critère d'acceptation spécifique 128: résultat attendu, métrique de succès, tolérance.
- [AC129] Critère d'acceptation spécifique 129: résultat attendu, métrique de succès, tolérance.
- [AC130] Critère d'acceptation spécifique 130: résultat attendu, métrique de succès, tolérance.
- [AC131] Critère d'acceptation spécifique 131: résultat attendu, métrique de succès, tolérance.
- [AC132] Critère d'acceptation spécifique 132: résultat attendu, métrique de succès, tolérance.
- [AC133] Critère d'acceptation spécifique 133: résultat attendu, métrique de succès, tolérance.
- [AC134] Critère d'acceptation spécifique 134: résultat attendu, métrique de succès, tolérance.
- [AC135] Critère d'acceptation spécifique 135: résultat attendu, métrique de succès, tolérance.
- [AC136] Critère d'acceptation spécifique 136: résultat attendu, métrique de succès, tolérance.
- [AC137] Critère d'acceptation spécifique 137: résultat attendu, métrique de succès, tolérance.
- [AC138] Critère d'acceptation spécifique 138: résultat attendu, métrique de succès, tolérance.
- [AC139] Critère d'acceptation spécifique 139: résultat attendu, métrique de succès, tolérance.
- [AC140] Critère d'acceptation spécifique 140: résultat attendu, métrique de succès, tolérance.
- [AC141] Critère d'acceptation spécifique 141: résultat attendu, métrique de succès, tolérance.
- [AC142] Critère d'acceptation spécifique 142: résultat attendu, métrique de succès, tolérance.
- [AC143] Critère d'acceptation spécifique 143: résultat attendu, métrique de succès, tolérance.
- [AC144] Critère d'acceptation spécifique 144: résultat attendu, métrique de succès, tolérance.
- [AC145] Critère d'acceptation spécifique 145: résultat attendu, métrique de succès, tolérance.
- [AC146] Critère d'acceptation spécifique 146: résultat attendu, métrique de succès, tolérance.
- [AC147] Critère d'acceptation spécifique 147: résultat attendu, métrique de succès, tolérance.
- [AC148] Critère d'acceptation spécifique 148: résultat attendu, métrique de succès, tolérance.
- [AC149] Critère d'acceptation spécifique 149: résultat attendu, métrique de succès, tolérance.
- [AC150] Critère d'acceptation spécifique 150: résultat attendu, métrique de succès, tolérance.
- [AC151] Critère d'acceptation spécifique 151: résultat attendu, métrique de succès, tolérance.
- [AC152] Critère d'acceptation spécifique 152: résultat attendu, métrique de succès, tolérance.
- [AC153] Critère d'acceptation spécifique 153: résultat attendu, métrique de succès, tolérance.
- [AC154] Critère d'acceptation spécifique 154: résultat attendu, métrique de succès, tolérance.
- [AC155] Critère d'acceptation spécifique 155: résultat attendu, métrique de succès, tolérance.
- [AC156] Critère d'acceptation spécifique 156: résultat attendu, métrique de succès, tolérance.
- [AC157] Critère d'acceptation spécifique 157: résultat attendu, métrique de succès, tolérance.
- [AC158] Critère d'acceptation spécifique 158: résultat attendu, métrique de succès, tolérance.
- [AC159] Critère d'acceptation spécifique 159: résultat attendu, métrique de succès, tolérance.
- [AC160] Critère d'acceptation spécifique 160: résultat attendu, métrique de succès, tolérance.
- [AC161] Critère d'acceptation spécifique 161: résultat attendu, métrique de succès, tolérance.
- [AC162] Critère d'acceptation spécifique 162: résultat attendu, métrique de succès, tolérance.
- [AC163] Critère d'acceptation spécifique 163: résultat attendu, métrique de succès, tolérance.
- [AC164] Critère d'acceptation spécifique 164: résultat attendu, métrique de succès, tolérance.
- [AC165] Critère d'acceptation spécifique 165: résultat attendu, métrique de succès, tolérance.
- [AC166] Critère d'acceptation spécifique 166: résultat attendu, métrique de succès, tolérance.
- [AC167] Critère d'acceptation spécifique 167: résultat attendu, métrique de succès, tolérance.
- [AC168] Critère d'acceptation spécifique 168: résultat attendu, métrique de succès, tolérance.
- [AC169] Critère d'acceptation spécifique 169: résultat attendu, métrique de succès, tolérance.
- [AC170] Critère d'acceptation spécifique 170: résultat attendu, métrique de succès, tolérance.
- [AC171] Critère d'acceptation spécifique 171: résultat attendu, métrique de succès, tolérance.
- [AC172] Critère d'acceptation spécifique 172: résultat attendu, métrique de succès, tolérance.
- [AC173] Critère d'acceptation spécifique 173: résultat attendu, métrique de succès, tolérance.
- [AC174] Critère d'acceptation spécifique 174: résultat attendu, métrique de succès, tolérance.
- [AC175] Critère d'acceptation spécifique 175: résultat attendu, métrique de succès, tolérance.
- [AC176] Critère d'acceptation spécifique 176: résultat attendu, métrique de succès, tolérance.
- [AC177] Critère d'acceptation spécifique 177: résultat attendu, métrique de succès, tolérance.
- [AC178] Critère d'acceptation spécifique 178: résultat attendu, métrique de succès, tolérance.
- [AC179] Critère d'acceptation spécifique 179: résultat attendu, métrique de succès, tolérance.
- [AC180] Critère d'acceptation spécifique 180: résultat attendu, métrique de succès, tolérance.
- [AC181] Critère d'acceptation spécifique 181: résultat attendu, métrique de succès, tolérance.
- [AC182] Critère d'acceptation spécifique 182: résultat attendu, métrique de succès, tolérance.
- [AC183] Critère d'acceptation spécifique 183: résultat attendu, métrique de succès, tolérance.
- [AC184] Critère d'acceptation spécifique 184: résultat attendu, métrique de succès, tolérance.
- [AC185] Critère d'acceptation spécifique 185: résultat attendu, métrique de succès, tolérance.
- [AC186] Critère d'acceptation spécifique 186: résultat attendu, métrique de succès, tolérance.
- [AC187] Critère d'acceptation spécifique 187: résultat attendu, métrique de succès, tolérance.
- [AC188] Critère d'acceptation spécifique 188: résultat attendu, métrique de succès, tolérance.
- [AC189] Critère d'acceptation spécifique 189: résultat attendu, métrique de succès, tolérance.
- [AC190] Critère d'acceptation spécifique 190: résultat attendu, métrique de succès, tolérance.
- [AC191] Critère d'acceptation spécifique 191: résultat attendu, métrique de succès, tolérance.
- [AC192] Critère d'acceptation spécifique 192: résultat attendu, métrique de succès, tolérance.
- [AC193] Critère d'acceptation spécifique 193: résultat attendu, métrique de succès, tolérance.
- [AC194] Critère d'acceptation spécifique 194: résultat attendu, métrique de succès, tolérance.
- [AC195] Critère d'acceptation spécifique 195: résultat attendu, métrique de succès, tolérance.
- [AC196] Critère d'acceptation spécifique 196: résultat attendu, métrique de succès, tolérance.
- [AC197] Critère d'acceptation spécifique 197: résultat attendu, métrique de succès, tolérance.
- [AC198] Critère d'acceptation spécifique 198: résultat attendu, métrique de succès, tolérance.
- [AC199] Critère d'acceptation spécifique 199: résultat attendu, métrique de succès, tolérance.
- [AC200] Critère d'acceptation spécifique 200: résultat attendu, métrique de succès, tolérance.

## Checklist de livraison
- [CHK001] Point de contrôle 1 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK002] Point de contrôle 2 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK003] Point de contrôle 3 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK004] Point de contrôle 4 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK005] Point de contrôle 5 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK006] Point de contrôle 6 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK007] Point de contrôle 7 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK008] Point de contrôle 8 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK009] Point de contrôle 9 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK010] Point de contrôle 10 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK011] Point de contrôle 11 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK012] Point de contrôle 12 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK013] Point de contrôle 13 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK014] Point de contrôle 14 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK015] Point de contrôle 15 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK016] Point de contrôle 16 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK017] Point de contrôle 17 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK018] Point de contrôle 18 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK019] Point de contrôle 19 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK020] Point de contrôle 20 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK021] Point de contrôle 21 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK022] Point de contrôle 22 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK023] Point de contrôle 23 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK024] Point de contrôle 24 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK025] Point de contrôle 25 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK026] Point de contrôle 26 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK027] Point de contrôle 27 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK028] Point de contrôle 28 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK029] Point de contrôle 29 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK030] Point de contrôle 30 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK031] Point de contrôle 31 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK032] Point de contrôle 32 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK033] Point de contrôle 33 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK034] Point de contrôle 34 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK035] Point de contrôle 35 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK036] Point de contrôle 36 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK037] Point de contrôle 37 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK038] Point de contrôle 38 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK039] Point de contrôle 39 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK040] Point de contrôle 40 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK041] Point de contrôle 41 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK042] Point de contrôle 42 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK043] Point de contrôle 43 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK044] Point de contrôle 44 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK045] Point de contrôle 45 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK046] Point de contrôle 46 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK047] Point de contrôle 47 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK048] Point de contrôle 48 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK049] Point de contrôle 49 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK050] Point de contrôle 50 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK051] Point de contrôle 51 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK052] Point de contrôle 52 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK053] Point de contrôle 53 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK054] Point de contrôle 54 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK055] Point de contrôle 55 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK056] Point de contrôle 56 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK057] Point de contrôle 57 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK058] Point de contrôle 58 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK059] Point de contrôle 59 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK060] Point de contrôle 60 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK061] Point de contrôle 61 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK062] Point de contrôle 62 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK063] Point de contrôle 63 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK064] Point de contrôle 64 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK065] Point de contrôle 65 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK066] Point de contrôle 66 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK067] Point de contrôle 67 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK068] Point de contrôle 68 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK069] Point de contrôle 69 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK070] Point de contrôle 70 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK071] Point de contrôle 71 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK072] Point de contrôle 72 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK073] Point de contrôle 73 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK074] Point de contrôle 74 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK075] Point de contrôle 75 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK076] Point de contrôle 76 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK077] Point de contrôle 77 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK078] Point de contrôle 78 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK079] Point de contrôle 79 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK080] Point de contrôle 80 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK081] Point de contrôle 81 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK082] Point de contrôle 82 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK083] Point de contrôle 83 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK084] Point de contrôle 84 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK085] Point de contrôle 85 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK086] Point de contrôle 86 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK087] Point de contrôle 87 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK088] Point de contrôle 88 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK089] Point de contrôle 89 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK090] Point de contrôle 90 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK091] Point de contrôle 91 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK092] Point de contrôle 92 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK093] Point de contrôle 93 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK094] Point de contrôle 94 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK095] Point de contrôle 95 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK096] Point de contrôle 96 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK097] Point de contrôle 97 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK098] Point de contrôle 98 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK099] Point de contrôle 99 à valider avant mise en prod (migrations, backups, feature flags, comms).
- [CHK100] Point de contrôle 100 à valider avant mise en prod (migrations, backups, feature flags, comms).
## Annexes supplémentaires orientées code

### A.1 Modèle de migration Alembic prêt à l'emploi
Utiliser ce squelette pour générer la migration complète (adapter les noms de tables s'ils existent déjà) :
```python
"""Finance treasury refactor"""
from alembic import op
import sqlalchemy as sa

revision = "202412120001"
down_revision = None  # renseigner la dernière révision réelle
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "finance_entities",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "finance_entity_members",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="OWNER"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entity_id", "tenant_id", name="uq_finance_entity_members_member"),
    )

    account_type = sa.Enum("BANQUE", "CAISSE", "CB", "AUTRE", "PLATFORM", name="finance_account_type")
    account_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "finance_accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=False),
        sa.Column("type", account_type, nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("iban", sa.Text()),
        sa.Column("bic", sa.Text()),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("iban", name="uq_finance_accounts_iban"),
    )

    op.create_index("ix_finance_accounts_entity", "finance_accounts", ["entity_id"])
    op.create_index("ix_finance_accounts_label", "finance_accounts", ["label"])

    tx_direction = sa.Enum("IN", "OUT", "TRANSFER", name="finance_tx_direction")
    tx_status = sa.Enum("DRAFT", "CONFIRMED", "CANCELLED", name="finance_tx_status")
    tx_direction.create(op.get_bind(), checkfirst=True)
    tx_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "finance_transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=False),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("finance_accounts.id"), nullable=False),
        sa.Column("counterparty_account_id", sa.BigInteger(), sa.ForeignKey("finance_accounts.id")),
        sa.Column("direction", tx_direction, nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("date_operation", sa.Date(), nullable=False),
        sa.Column("date_value", sa.Date()),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("ref_externe", sa.Text()),
        sa.Column("note", sa.Text()),
        sa.Column("status", tx_status, nullable=False, server_default="CONFIRMED"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger()),
        sa.Column("locked_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("ref_externe", name="uq_finance_transactions_ref_externe"),
    )

    op.create_index("ix_finance_transactions_entity_date", "finance_transactions", ["entity_id", "date_operation"], postgresql_using="btree")
    op.create_index("ix_finance_transactions_account", "finance_transactions", ["account_id"])

    op.create_table(
        "finance_transaction_lines",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("transaction_id", sa.BigInteger(), sa.ForeignKey("finance_transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("finance_categories.id"), nullable=False),
        sa.Column("cost_center_id", sa.BigInteger(), sa.ForeignKey("finance_cost_centers.id")),
        sa.Column("montant_ht", sa.Numeric(18, 2)),
        sa.Column("tva_pct", sa.Numeric(5, 2)),
        sa.Column("montant_ttc", sa.Numeric(18, 2), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_finance_transaction_lines_tx", "finance_transaction_lines", ["transaction_id"])


def downgrade():
    op.drop_index("ix_finance_transaction_lines_tx", table_name="finance_transaction_lines")
    op.drop_table("finance_transaction_lines")
    op.drop_index("ix_finance_transactions_account", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_entity_date", table_name="finance_transactions")
    op.drop_table("finance_transactions")
    tx_status = sa.Enum(name="finance_tx_status")
    tx_direction = sa.Enum(name="finance_tx_direction")
    tx_status.drop(op.get_bind(), checkfirst=True)
    tx_direction.drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_finance_accounts_label", table_name="finance_accounts")
    op.drop_index("ix_finance_accounts_entity", table_name="finance_accounts")
    op.drop_table("finance_accounts")
    account_type = sa.Enum(name="finance_account_type")
    account_type.drop(op.get_bind(), checkfirst=True)
    op.drop_table("finance_entity_members")
    op.drop_table("finance_entities")
```

### A.2 Modèles Pydantic / FastAPI prêts à coller dans `backend/app/finance/schemas.py`
```python
from datetime import date
from pydantic import BaseModel, Field, constr, condecimal
from typing import Optional, List


class FinanceAccountCreate(BaseModel):
    entity_id: int
    type: constr(regex=r"^(BANQUE|CAISSE|CB|AUTRE|PLATFORM)$")
    label: str
    iban: Optional[str] = None
    bic: Optional[str] = None
    currency: str = "EUR"
    metadata: Optional[dict] = None


class FinanceTransactionLineIn(BaseModel):
    category_id: int
    cost_center_id: Optional[int] = None
    montant_ht: Optional[condecimal(max_digits=18, decimal_places=2)] = None
    tva_pct: Optional[condecimal(max_digits=5, decimal_places=2)] = None
    montant_ttc: condecimal(max_digits=18, decimal_places=2)
    notes: Optional[str] = None


class FinanceTransactionCreate(BaseModel):
    entity_id: int
    account_id: int
    counterparty_account_id: Optional[int] = None
    direction: constr(regex=r"^(IN|OUT|TRANSFER)$")
    source: str
    date_operation: date
    date_value: Optional[date] = None
    amount: condecimal(max_digits=18, decimal_places=2)
    currency: str = "EUR"
    ref_externe: Optional[str] = None
    note: Optional[str] = None
    lines: List[FinanceTransactionLineIn] = Field(default_factory=list)


class FinanceTransactionOut(BaseModel):
    id: int
    entity_id: int
    account_id: int
    direction: str
    date_operation: date
    amount: condecimal(max_digits=18, decimal_places=2)
    currency: str
    lines: List[FinanceTransactionLineIn]

    class Config:
        orm_mode = True
```

### A.2bis Modèles SQLAlchemy prêts à coller dans `backend/app/finance/models.py`
```python
from sqlalchemy import (
    Column, BigInteger, Text, Numeric, Date, Boolean, ForeignKey, Enum, JSON, TIMESTAMP, func
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class FinanceEntity(Base):
    __tablename__ = "finance_entities"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    currency = Column(Text, nullable=False, default="EUR")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    members = relationship("FinanceEntityMember", back_populates="entity")


class FinanceEntityMember(Base):
    __tablename__ = "finance_entity_members"

    id = Column(BigInteger, primary_key=True)
    entity_id = Column(BigInteger, ForeignKey("finance_entities.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(BigInteger, nullable=False)
    role = Column(Text, nullable=False, default="OWNER")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    entity = relationship("FinanceEntity", back_populates="members")


class FinanceAccount(Base):
    __tablename__ = "finance_accounts"

    id = Column(BigInteger, primary_key=True)
    entity_id = Column(BigInteger, ForeignKey("finance_entities.id"), nullable=False)
    type = Column(Enum("BANQUE", "CAISSE", "CB", "AUTRE", "PLATFORM", name="finance_account_type"), nullable=False)
    label = Column(Text, nullable=False)
    iban = Column(Text)
    bic = Column(Text)
    currency = Column(Text, nullable=False, default="EUR")
    is_active = Column(Boolean, nullable=False, default=True)
    metadata = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    entity = relationship("FinanceEntity")
    transactions = relationship("FinanceTransaction", back_populates="account")


class FinanceTransaction(Base):
    __tablename__ = "finance_transactions"

    id = Column(BigInteger, primary_key=True)
    entity_id = Column(BigInteger, ForeignKey("finance_entities.id"), nullable=False)
    account_id = Column(BigInteger, ForeignKey("finance_accounts.id"), nullable=False)
    counterparty_account_id = Column(BigInteger, ForeignKey("finance_accounts.id"))
    direction = Column(Enum("IN", "OUT", "TRANSFER", name="finance_tx_direction"), nullable=False)
    source = Column(Text, nullable=False)
    date_operation = Column(Date, nullable=False)
    date_value = Column(Date)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(Text, nullable=False, default="EUR")
    ref_externe = Column(Text, unique=True)
    note = Column(Text)
    status = Column(Enum("DRAFT", "CONFIRMED", "CANCELLED", name="finance_tx_status"), nullable=False, default="CONFIRMED")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(BigInteger)
    locked_at = Column(TIMESTAMP(timezone=True))

    account = relationship("FinanceAccount", foreign_keys=[account_id], back_populates="transactions")
    lines = relationship("FinanceTransactionLine", back_populates="transaction", cascade="all, delete-orphan")


class FinanceTransactionLine(Base):
    __tablename__ = "finance_transaction_lines"

    id = Column(BigInteger, primary_key=True)
    transaction_id = Column(BigInteger, ForeignKey("finance_transactions.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(BigInteger, ForeignKey("finance_categories.id"), nullable=False)
    cost_center_id = Column(BigInteger, ForeignKey("finance_cost_centers.id"))
    montant_ht = Column(Numeric(18, 2))
    tva_pct = Column(Numeric(5, 2))
    montant_ttc = Column(Numeric(18, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    transaction = relationship("FinanceTransaction", back_populates="lines")
```

**Brancher les modèles** :
- Ajouter `from backend.app.finance import models as finance_models` dans le module central d'enregistrement des modèles SQLAlchemy (souvent `backend/app/db/base.py`).
- Exposer `finance_models.Base.metadata` dans `alembic/env.py` pour l'autogénération (si utilisée) afin que les futures migrations incluent les tables finance.

### A.3 Interfaces de repository (ex: `backend/app/finance/repositories.py`)
```python
from typing import Protocol, Sequence
from . import models, schemas


class TransactionRepo(Protocol):
    def create(self, tx: schemas.FinanceTransactionCreate, user_id: int) -> models.FinanceTransaction:
        ...

    def list_unreconciled(self, entity_id: int, limit: int = 100) -> Sequence[models.FinanceTransaction]:
        ...

    def attach_lines(self, tx_id: int, lines: list[schemas.FinanceTransactionLineIn]) -> None:
        ...

    def lock(self, tx_id: int, user_id: int) -> None:
        ...


class BankStatementRepo(Protocol):
    def create_statement(self, payload: dict) -> models.FinanceBankStatement:
        ...

    def add_line(self, statement_id: int, line_payload: dict) -> models.FinanceBankStatementLine:
        ...

    def link_reconciliation(self, line_id: int, tx_id: int, status: str = "AUTO") -> None:
        ...
```

### A.3bis Implémentation SQLAlchemy de `TransactionRepo` (ex: `backend/app/finance/repositories_sqlalchemy.py`)
```python
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import models, schemas


class SqlAlchemyTransactionRepo:
    def __init__(self, db: Session):
        self.db = db

    def create_account(self, payload: schemas.FinanceAccountCreate) -> models.FinanceAccount:
        account = models.FinanceAccount(**payload.dict())
        self.db.add(account)
        self.db.flush()  # pour récupérer l'ID sans commit
        return account

    def create(self, tx: schemas.FinanceTransactionCreate, user_id: int) -> models.FinanceTransaction:
        tx_model = models.FinanceTransaction(**tx.dict(exclude={"lines"}), created_by=user_id)
        self.db.add(tx_model)
        self.db.flush()
        return tx_model

    def attach_lines(self, tx_id: int, lines: list[schemas.FinanceTransactionLineIn]):
        for line in lines:
            self.db.add(models.FinanceTransactionLine(transaction_id=tx_id, **line.dict()))

    def lock(self, tx_id: int, user_id: int):
        self.db.query(models.FinanceTransaction).filter_by(id=tx_id).update({"locked_at": func.now(), "updated_at": func.now()})

    def list_unreconciled(self, entity_id: int, limit: int = 100):
        return (
            self.db.query(models.FinanceTransaction)
            .filter(models.FinanceTransaction.entity_id == entity_id, models.FinanceTransaction.locked_at.is_(None))
            .order_by(models.FinanceTransaction.date_operation.desc())
            .limit(limit)
            .all()
        )
```

### A.4 Services (ex: `backend/app/finance/services.py`)
```python
from .schemas import FinanceTransactionCreate
from .repositories import TransactionRepo, BankStatementRepo


class TransactionService:
    def __init__(self, tx_repo: TransactionRepo):
        self.tx_repo = tx_repo

    def create_transaction(self, payload: FinanceTransactionCreate, user_id: int):
        tx = self.tx_repo.create(payload, user_id)
        if payload.lines:
            self.tx_repo.attach_lines(tx.id, payload.lines)
        return tx

    def lock_transaction(self, tx_id: int, user_id: int):
        self.tx_repo.lock(tx_id, user_id)


class ReconciliationService:
    def __init__(self, tx_repo: TransactionRepo, bs_repo: BankStatementRepo):
        self.tx_repo = tx_repo
        self.bs_repo = bs_repo

    def auto_match(self, entity_id: int, threshold: float = 0.01):
        candidates = self.tx_repo.list_unreconciled(entity_id, limit=500)
        # Implémentation d'un matching naïf montant+date ; à remplacer par une heuristique améliorée.
        for tx in candidates:
            matching_lines = self.bs_repo.find_by_amount_date(entity_id, tx.amount, tx.date_operation)
            for line in matching_lines:
                self.bs_repo.link_reconciliation(line.id, tx.id, status="AUTO")
```

### A.5 Routes FastAPI (ex: `backend/app/finance/routes.py`)
```python
from fastapi import APIRouter, Depends, status
from .schemas import FinanceTransactionCreate, FinanceTransactionOut, FinanceAccountCreate
from .services import TransactionService


router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_account(payload: FinanceAccountCreate, svc: TransactionService = Depends()):
    return svc.tx_repo.create_account(payload)


@router.post("/transactions", response_model=FinanceTransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: FinanceTransactionCreate, svc: TransactionService = Depends(), user_id: int = Depends(get_current_user_id)):
    return svc.create_transaction(payload, user_id)


@router.post("/reconciliation/auto")
def reconciliation_auto(entity_id: int, svc: ReconciliationService = Depends()):
    return svc.auto_match(entity_id)
```

### A.5bis Injection de dépendances FastAPI (ex: `backend/app/finance/deps.py`)
```python
from fastapi import Depends
from backend.app.db.session import get_db
from .repositories_sqlalchemy import SqlAlchemyTransactionRepo
from .services import TransactionService


def get_transaction_service(db=Depends(get_db)) -> TransactionService:
    repo = SqlAlchemyTransactionRepo(db)
    return TransactionService(tx_repo=repo)
```

Puis référencer `get_transaction_service` dans les routes :
```python
@router.post("/transactions", response_model=FinanceTransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: FinanceTransactionCreate,
    svc: TransactionService = Depends(get_transaction_service),
    user_id: int = Depends(get_current_user_id),
):
    return svc.create_transaction(payload, user_id)
```

### A.6 Indexation et contraintes additionnelles à appliquer après migration
- Index GIN sur `finance_transactions.ref_externe` pour accélérer les recherches par référence externe : `CREATE INDEX CONCURRENTLY IF NOT EXISTS gin_finance_transactions_ref ON finance_transactions USING gin (ref_externe gin_trgm_ops);`
- Vérification de cohérence `amount` vs somme des `finance_transaction_lines.montant_ttc` via une contrainte check :
  ```sql
  ALTER TABLE finance_transactions
  ADD CONSTRAINT chk_finance_transactions_lines_total
  CHECK (
    NOT EXISTS (
      SELECT 1 FROM finance_transaction_lines l
      WHERE l.transaction_id = id
      GROUP BY l.transaction_id
      HAVING SUM(l.montant_ttc) <> amount
    )
  );
  ```
- Trigger de mise à jour `updated_at` : utiliser un trigger générique `set_timestamp()` partagé par toutes les tables finance.

### A.7 Mapping ETL précis depuis l'existant
- `restaurant_depenses` → `finance_transactions` (`direction=OUT`, `source='RESTO_DEPENSE'`, `entity_id=RESTO`).
- `restaurant_depense_categories` → `finance_categories` (copier `code` et libellés, typer en DEPENSE).
- `restaurant_bank_statements` → `finance_bank_statement_lines` (par compte `finance_accounts` mappé via IBAN ou libellé).
- `capital_snapshot` → enrichir avec `entity_id` et rematérialiser les vues journalières `mv_finance_daily_cashflow`.

### A.8 Jeux de données de test minimaux (à insérer dans `tests/fixtures/finance.py`)
```python
ENTITY_RESTO = {"id": 1, "code": "RESTO", "name": "Restaurant", "currency": "EUR"}
ENTITY_EPI = {"id": 2, "code": "EPI", "name": "Epicerie", "currency": "EUR"}

ACCOUNT_CAISSE = {"id": 10, "entity_id": 1, "type": "CAISSE", "label": "Caisse resto", "currency": "EUR"}
ACCOUNT_BANQUE = {"id": 11, "entity_id": 1, "type": "BANQUE", "label": "BNP Resto", "currency": "EUR"}

TX_DEPENSE = {
    "entity_id": 1,
    "account_id": 11,
    "direction": "OUT",
    "source": "FACTURE",
    "date_operation": date(2024, 12, 2),
    "amount": Decimal("120.00"),
    "lines": [
        {"category_id": 100, "montant_ttc": Decimal("120.00"), "montant_ht": Decimal("100.00"), "tva_pct": Decimal("20.00")}
    ],
}
```

### A.9 Scénario de test bout-en-bout (backend)
1. POST `/finance/accounts` avec `ACCOUNT_BANQUE` puis `ACCOUNT_CAISSE`.
2. POST `/finance/transactions` avec `TX_DEPENSE` → vérifier création des lignes.
3. POST `/finance/bank-statements/import` avec un CSV contenant la même opération → créer `finance_bank_statement` + `..._lines`.
4. POST `/finance/reconciliation/auto` → vérifier que la ligne de relevé est reliée à la transaction.
5. GET `/finance/transactions?entity=RESTO` → la transaction apparaît avec `status=CONFIRMED` et `locked_at` null.
