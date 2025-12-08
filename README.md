# Plateforme de Gestion Épicerie & Restaurant

Plateforme web complète pour la gestion intégrée de deux métiers : **Épicerie**
(inventaire, catalogue, factures fournisseurs, suivi des prix) et **Restaurant**
(menus & recettes, coûts matières, charges opérationnelles, marges). Un module
**Trésorerie** unifié permet le suivi des flux bancaires, la catégorisation
automatique des dépenses et le rapprochement comptable.

L'architecture repose sur une **SPA React** moderne (Vite + TailwindCSS), une
**API REST FastAPI** et une base **PostgreSQL** avec support multi-tenant natif.

## État du projet

* **Tests automatisés :** `pytest` couvre les services d'accès aux données, le
  chargeur de produits, les extracteurs de factures ainsi que les conversions
  utilitaires utilisées par l'application principale.
* **Interface :** la feuille de style `legacy/streamlit/styles/style.css`
  applique une palette plus douce et chaleureuse à l'ensemble des composants
  Streamlit, et le fichier
  `.streamlit/config.toml` force l'utilisation du thème clair sur tous les
  environnements d'exécution.
* **SPA React :** le dossier `frontend/` contient une application Vite + React
  avec un router, un PoS minimal et désormais deux expériences : un shell
  complet pour **Epicerie HQ** et une interface dédiée, plus légère, pour
  **Restaurant HQ**.
* **Legacy archivé :** les anciennes applis Streamlit / PHP ont été déplacées
  sous `legacy/` et documentées dans `docs/legacy.md`. Elles servent uniquement
  de référence (structures SQL, assets) et ne participent plus aux builds.
* **API REST :** `backend/main.py` expose un service FastAPI (`/health`,
  `/products`, `/inventory/summary`, `/pos/checkout`, `/products/{id}`) qui
  encapsule la logique métier existante.
* **Workflows avancés :** les onglets _Plan d'approvisionnement dynamique_,
  _Audit & résolution d'écarts_, _Factures → Commandes_, _Qualité catalogue &
  codes-barres_ et _Sauvegardes & reprise d'activité_ embarquent des vues
  orientées actions : calculs de couverture et propositions de commandes,
  assignation des écarts avec export CSV, rapprochement factures / réceptions,
  gouvernance des codes-barres et supervision des sauvegardes.

Pour vérifier localement que tout fonctionne, installez d'abord les
dépendances de développement puis lancez la suite de tests :

```bash
pip install -r requirements-dev.txt
pytest
```

### Tests automatisés (API + SPA)

Un script permet d'orchestrer la base PostgreSQL de test, `pytest` et le build Vite :

```bash
./scripts/run-tests.sh
```

Il démarre un conteneur `db-test`, exécute les migrations (`db/init.sql`), lance `pytest`
et vérifie le build front. Pensez à arrêter les services résiduels avec
`docker compose --env-file .env.test down -v` en cas d'interruption.

## Démarrer l'application

### Vérifier votre version locale

Toutes les commandes `git` ci-dessous sont à exécuter dans un terminal ouvert
à la racine du dépôt cloné (le dossier `inventaire-epicerie`) **sans** les
préfixer par `docker`. Elles fonctionnent aussi bien sur l'hôte que dans un
shell ouvert via `make shell`.

1. Afficher la branche active et l'état des fichiers :

   ```bash
   git status -sb
   ```

2. Mettre à jour les références distantes puis comparer avec la branche
   distante suivie (ici `origin/work`) :

   ```bash
   git fetch origin
   git log --oneline HEAD..origin/work
   ```

3. Si vous souhaitez aligner votre copie locale sur la branche distante :

   ```bash
   git pull --ff-only
   ```

### Avec Docker (recommandé)

1. Créez un fichier `.env` à partir de `env.prod.example` en adaptant les
   valeurs si nécessaire.
2. Lancez la stack :

   ```bash
   docker compose up -d db api app frontend
   ```

3. Dès que les conteneurs sont démarrés, ouvrez un navigateur sur
   <http://localhost:8501> pour accéder à l'application Streamlit. La base
   PostgreSQL est exposée sur le port 5432 (définis dans `docker-compose.yml`).
   L'API FastAPI est désormais servie par le conteneur `inventaire-api` sur
   `http://localhost:8000`, ce qui permet de consommer l'API sans lancer
   `uvicorn` manuellement. Le front-end React est servi par le conteneur
   `inventaire-frontend` (build Vite) sur `http://localhost:5175`.
4. Pour arrêter et nettoyer les conteneurs :

   ```bash
   make down
   ```

#### Réaligner la base existante

Les migrations Alembic supposaient l'existence de `capital_snapshot` et de la vue `latest_price_history`.
Si vous avez initialisé la base avant ce correctif, créez-les manuellement puis resynchronisez la version Alembic :

```bash
docker compose exec db psql -U postgres -d epicerie <<'SQL'
CREATE TABLE IF NOT EXISTS capital_snapshot (
  id SERIAL PRIMARY KEY,
  tenant_id INT NOT NULL,
  snapshot_date TIMESTAMPTZ NOT NULL,
  stock_value NUMERIC(14,2) NOT NULL DEFAULT 0,
  bank_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
  cash_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
  total_assets NUMERIC(14,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_capital_snapshot_tenant_date ON capital_snapshot (tenant_id, snapshot_date);
CREATE OR REPLACE VIEW latest_price_history AS
SELECT code, tenant_id, fournisseur, prix_achat, quantite, facture_date, source_context, created_at
FROM (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY tenant_id, code
           ORDER BY facture_date DESC NULLS LAST, created_at DESC
         ) AS row_num
  FROM produits_price_history
) ranked
WHERE row_num = 1;
SQL
docker compose exec api alembic stamp e32e12bd5139
docker compose restart api
```

Cela aligne la base de données avec le schéma attendu par le portefeuille et évite les erreurs `UndefinedTable`.

#### Mettre à jour le conteneur `app`

Lorsque vous modifiez le code Python ou les assets Streamlit, enregistrez vos
fichiers puis rechargez simplement la page : grâce au montage du dossier du
projet, la vue <http://localhost:8501> reflète immédiatement vos changements.

En revanche, les environnements sans montage (production, CI, export d'une
image) doivent être reconstruits pour embarquer les nouveaux fichiers :

```bash
make rebuild          # reconstruit l'image puis relance les services
docker compose up --build app  # alternative équivalente
```

Cela garantit que le conteneur dispose bien des utilitaires comme
`invoice_extractor.py` ou `cart_normalizer.py`, et évite tout décalage entre
l'affichage local et l'image exécutée en production.

### En local (hors Docker)

1. Créez et activez un environnement virtuel Python 3.11. Sur Debian/Ubuntu
   récents (PEP 668), évitez l'option `--break-system-packages` et préférez un
   environnement isolé :

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```

2. Installez les dépendances applicatives et de test :

   ```bash
   pip install -r requirements-dev.txt
   ```

   (Ce fichier inclut `requirements.txt` et ajoute les outils de test comme
   `pytest`.)

3. Exportez les variables d'environnement nécessaires (voir `env.prod.example`
   pour la liste complète) ou créez un fichier `.streamlit/secrets.toml`.

   En local, assurez-vous qu'au moins `DATABASE_URL` ou les variables
   `POSTGRES_*` individuelles (notamment `POSTGRES_PASSWORD`) sont définies
   avant de lancer `uvicorn`, sinon PostgreSQL refuse la connexion avec
   `psycopg2.errors.OperationalError: fe_sendauth: no password supplied`.
4. Démarrez l'application puis ouvrez votre navigateur sur
   <http://localhost:8501> :

   ```bash
   streamlit run legacy/streamlit/app.py
   ```

5. Dans un autre terminal, démarrez l'API puis la SPA :

   ```bash
   uvicorn backend.main:app --reload --port 8000
   cd frontend && npm install && npm run dev
   ```

   La SPA est disponible sur <http://localhost:5173> et communique avec
   l'ancienne application via l'iframe « Outils Streamlit » tant que certaines
   fonctionnalités n'ont pas été portées. Si vous servez un build Vite derrière
   Streamlit, PHP ou Caddy sans proxy `/api`, définissez `VITE_API_BASE_URL`
   (par exemple `http://localhost:8000`) avant `npm run build` pour que les
   exports CSV et appels REST ciblent directement FastAPI.

### Importer des produits

Un Makefile facilite l'import CSV :

```bash
make import-data
```

Par défaut, le fichier `docs/invoices/Produit.csv` sera chargé et les codes barres seront
enregistrés. Redémarrez ensuite l'application ou videz le cache Streamlit pour
voir les nouveaux produits.

### Importer automatiquement des factures METRO

Le script `scripts/import_invoice_files.py` orchestre l'intégralité du flux : extraction du PDF/DOCX, enrichissement catalogue, création des mouvements de stock et alimentation des tables de consolidation (`dim_*`, `fact_*`).

```bash
source .venv/bin/activate
python scripts/import_invoice_files.py \
  --tenant epicerie \
  --supplier METRO \
  --username admin \
  docs/invoices/ilovepdf_merged-2.pdf docs/invoices/ilovepdf_merged-3.pdf
```

Options utiles : `--invoice-date YYYY-MM-DD` pour forcer la date de facture et `--initialize-stock` si vous souhaitez initialiser le stock lors de la création d'un produit. Chaque import met automatiquement à jour les tables `fact_invoices` ainsi que le catalogue (`produits`, `prix`, historiques).

### Sauvegardes PostgreSQL & onglet Maintenance

L'onglet **Maintenance (Admin)** de l'application affiche maintenant un
diagnostic des utilitaires PostgreSQL attendus (`pg_dump` et `psql`). Pour que
les boutons de sauvegarde/restauration fonctionnent :

1. Assurez-vous que le client PostgreSQL est installé sur la machine qui
   exécute Streamlit. Sous Debian/Ubuntu la commande suivante suffit en général
   (exécutez-la depuis l'hôte ou le conteneur concerné) :

   ```bash
   sudo apt-get update
   sudo apt-get install postgresql-client
   ```

   Dans certains environnements, des variables `http_proxy`/`https_proxy`
   héritées peuvent forcer l'utilisation d'un proxy inaccessible et provoquer
   des erreurs `403 Forbidden`. Relancez alors la commande en désactivant ces
   variables :

   ```bash
   sudo env -u http_proxy -u https_proxy apt-get update
   sudo env -u http_proxy -u https_proxy apt-get install postgresql-client
   ```

2. Vérifiez que l'utilisateur système qui exécute Streamlit dispose des
   binaires dans son `PATH`. Si ce n'est pas le cas, configurez explicitement
   les chemins via les variables d'environnement `PG_DUMP_PATH` et `PSQL_PATH`
   (par exemple `/usr/lib/postgresql/16/bin/pg_dump`).

3. Une fois les utilitaires détectés, l'onglet Maintenance expose :
   - le statut courant de chaque binaire (✅ disponible ou ❌ introuvable),
   - la liste des sauvegardes existantes avec téléchargement, restauration ou
     suppression,
   - des messages d'aide si un prérequis manque.

Le dossier de sauvegarde par défaut est `backups/` (ou `/app/backups` en
production). Adaptez la variable `BACKUP_DIR` si besoin pour pointer vers un
volume persistant.

### Automatiser la création de charges à partir des relevés

Si vous importez des relevés bancaires en masse (PDF, texte, CSV), exécutez ce
script pour rattacher automatiquement les lignes non encore traitées à une
charge :

```bash
python -m scripts.auto_create_charges \
  --tenant 42 \
  --account "Compte restaurant" \
  [--limit 20] \
  [--dry-run]
```

- `--tenant` est l’ID du client (tenant) ciblé ; il correspond à la même valeur
  que celle utilisée dans l’interface.
- `--account` restreint le traitement à un compte bancaire précis (facultatif).
- `--limit` tranche la quantité de relevés transformés en une seule passe.
- `--dry-run` affiche la liste des mouvements sélectionnés sans appeler
  l’API de création de charge.

La commande réutilise `restaurant_service.create_expense_from_bank_statement`
pour générer automatiquement une dépense par relevé importé et mettre à jour
`depense_id`. En production, planifiez-la en cron (par exemple toutes les
nuitées) pour continuer à synchroniser les relevés sans intervention manuelle.

### Explorer les alias de libellés bancaires

Pour mieux classifier les dépenses, vous pouvez analyser les 2 dernières années
de relevés et repérer les alias courts les plus fréquents :

```bash
python -m scripts.analyze_statement_names \
  --tenant 42 \
  --years 2 \
  --limit 20
```

Le script tronque chaque libellé aux trois premiers mots (en majuscule) et affiche
les alias reçus le plus souvent. Cela permet de repérer par exemple des enseignes
à longue signature et de créer des règles `CATEGORY_RULES` plus fiables par regroupement.

### Étendre automatique le dictionnaire de fournisseurs

Les règles de reconnaissance s’appuient sur `data/vendor_category_mapping.csv` qui
liste les familles, les alias et les types correspondants. Ajoute une ligne par
tranche métier (ex. `Banque / Finances`, `Approvisionnement`, `Plateformes`) avec :

1. `aliases` : la liste des mots-clés séparés par `|` utilisés dans les libellés.
2. `category` : l’étiquette que tu veux voir apparaître dans la vue restaurant.
3. `types` : `Sortie`, `Entrée` ou rien si tu veux laisser la catégorie sauvage.

À chaque redémarrage de l’API, `backend/services/restaurant.py` charge automatiquement
les nouvelles familles via `core/vendor_categories.load_vendor_category_rules()`.

### Générer le CSV depuis un tableau brut

Lorsque tu as un tableau complet (comme celui de “Banque / Finances”), colle-le tel quel dans un fichier texte (`banque.txt`, par exemple) avec une ligne par fournisseur et deux colonnes séparées par un tab ou deux espaces. Ensuite :

```bash
python -m scripts.import_vendor_list banque.txt
```

Le script détecte les rubriques (`🧾 Banque / Finances`…), transforme chaque liste de fournisseurs en alias séparés par `|`, et ajoute les entrées dans `data/vendor_category_mapping.csv` (ajoute `--overwrite` pour repartir de zéro). C’est la manière la plus rapide d’avoir tout ton lexique dans le CSV.

### Récatégoriser les relevés existants

Les lignes déjà importées restent avec leur ancienne catégorie jusqu’à ce que tu les
reclasses avec la nouvelle logique. Pour cela, lance la commande suivante côté API :

```bash
python -m scripts/reclassify_bank_statements --tenant 42 [--account "Mon compte"] [--dry-run]
```

Utilise `--dry-run` pour vérifier le diff, puis relance sans l’option pour appliquer les changements.

Les charges créées automatiquement (`scripts.refresh_from_pdf` / bouton “Créer charge”) utilisent maintenant la même catégorie que les relevés grâce à la correspondance `restaurant_depense_categories` (la catégorie est créée à la volée si elle n’existe pas). Tu conserves ainsi une seule source de vérité entre Relevés et Charges.

Pour automatiser tout le flux (purge + import + charges + catégories), tu peux aussi utiliser :

```bash
make refresh-reports PDF_DIR=/chemin/vers/tes/pdfs
```

Ce `make` target :
1. vide `restaurant_bank_statements` et `restaurant_depenses` via `psql` dans le service `db`,
2. réimporte les PDF + crée toutes les charges pour les relevés du compte,
3. recalcule les catégories avec tes règles les plus récentes.

Définis `PDF_DIR` pour pointer vers le dossier monté dans le conteneur `api` (par défaut `./pdfs` dans ton dépôt) et `TENANT_ID` pour l’ID numérique du tenant Restaurant (par défaut `1`).  
Crée ce répertoire et dépose-y les fichiers `.pdf` de relevés (ils deviennent accessibles à `/app/$(notdir $(PDF_DIR))` dans le conteneur). Si le dossier est vide ou absent, la commande `make refresh-reports` échoue et te le signale. Si ton tenant n’est pas `1`, redéfinis `TENANT_ID` pour la commande (ex. `make refresh-reports PDF_DIR=./pdfs TENANT_ID=42`).

### Orchestrer l’import PDF complet

Pour automatiser complètement la remise en route après une purge (PDF → charge → catégories), utilise :

```bash
python -m scripts.refresh_from_pdf \
  --tenant restaurant \
  --account "incontournable" \
  --pdf path/to/releves \
  [--skip-charges] \
  [--skip-reclassify]
```

Le script :
1. balance tous les PDF fournis dans `restaurant_bank_statements` pour le compte choisi,
2. crée les `restaurant_depenses` manquantes pour associer chaque ligne (comme `scripts.auto_create_charges.py`),
3. recalcule les catégories avec les règles à jour (`core/vendor_categories`).

Les flags `--skip-charges` ou `--skip-reclassify` permettent d’ignorer certaines étapes pour les tests rapides. Tu peux appeler cette commande après chaque lancement de batch PDF ou l’intégrer dans un cron/docker-compose pour garder tout synchronisé.

### Réinitialiser Restaurant HQ

Pour automatiser toute la séquence (chargement du `PARTIE_3_MENU.txt` + purge/import/reclassification), utilise le target suivant :

```bash
make reset-restaurant
```

Il enchaîne `seed-partie3` (pour recharger ingrédients, boissons et catégories) puis `refresh-reports` (pour vider les relevés et relancer le pipeline PDF → charges → catégories). Tu peux le lancer après une purge complète ou avant une nouvelle campagne d’import de factures.

### Reconstituer l'historique des prix

Le module **Suivi prix** lit la table `produits_price_history`. Si elle est
vide, réimportez vos factures via l'onglet _Factures → Commandes_ ou appelez
directement `record_price_history` :

```python
import pandas as pd
from price_history_service import record_price_history

df = pd.read_csv("factures_2023_2024.csv")
record_price_history(
    df,
    supplier="Grossiste X",
    context="Reconstruction",
)
```

Chaque import ajoute les lignes avec prix d'achat, quantités et date de facture,
ce qui permet d'alimenter les statistiques (min/max/moyenne) et les exports du
module **Suivi prix**.

### Nouvelles pages SPA (Rapports & Admin)

La SPA React (<http://localhost:5173>) intègre désormais deux modules clés qui
remplacent progressivement les vues Streamlit :

1. **Rapports consolidés (`/reports`)**
   - Consomme l'endpoint `GET /reports/overview` exposé par FastAPI pour
     alimenter les KPI, la couverture par catégorie, la rotation 30 jours, la
     liste des produits sous seuil et les stocks négatifs.
   - Chaque bloc peut être exporté en CSV via `GET /reports/export/{stock|alerts|rotation|negative_stock}`
     directement depuis l'interface (boutons « Exports CSV »).
   - Cette page suffit pour préparer les revues catalogue sans lancer Streamlit :
     gardez simplement la stack `docker compose up -d db api app` en tâche de
     fond et servez la SPA (`npm run dev` ou `npm run build && npm run preview`).

2. **Outils administratifs (`/admin`)**
   - Reprend les diagnostics Streamlit (statut `pg_dump`/`psql`, planification,
     rétention, intégrité des sauvegardes, comptes utilisateurs et écarts de
     stock) via les nouveaux endpoints `/admin/*`.
   - Actions disponibles : création/restauration/suppression de sauvegarde,
     mise à jour de la planification (`PUT /admin/settings`), export du rapport
     d'intégrité (`GET /admin/backups/integrity`), changement de rôle ou
     réinitialisation de mot de passe utilisateur.
   - Les composants React déclenchent un rafraîchissement automatique du
     dashboard backend après chaque opération, ce qui évite toute manipulation
     manuelle dans Streamlit.

Les outils historiques (scanner, extraction avancée, etc.) restent accessibles
via l'onglet « Outils Streamlit » le temps de finaliser leur portage. Une fois
les pages _Rapports_ et _Admin_ validées en production, il suffira de retirer
le conteneur `app` de la stack Docker pour exploiter uniquement FastAPI + SPA.
## Organisation du dépôt

- `backend/`, `frontend/`, `tests/`, `db/`, `migrations/`, `scripts/` :
  piles API/SPA, données et automatisations actuelles.
- `legacy/streamlit/` : application Streamlit originelle (script principal,
  pages, styles dédiés, Dockerfile historique). Lancez-la avec
  `streamlit run legacy/streamlit/app.py`.
- `legacy/php/` : restes de l'ancienne vitrine PHP (pages marketing, assets,
  navigation « Customer »).
- `docs/restaurant/`, `docs/invoices/`, `docs/screenshots/` : référentiels
  fonctionnels (menus, BOM, cahiers des charges), exports fournisseurs et
  captures d'écran utilisés pendant la migration.

### Données de démo Restaurant HQ

Pour visualiser immédiatement le cockpit Restaurant, un jeu de données YAML se
trouve dans `docs/restaurant/menu_seed.yaml`. Lancez simplement :

```
make seed-restaurant
```

ou directement :

```
python3 scripts/seed_restaurant.py --file docs/restaurant/menu_seed.yaml
```

Cela crée/actualise les ingrédients, plats (avec fiches techniques) et quelques
charges fixes pour le tenant `restaurant`.

Les scripts SQL complets fournis par le métier (RESTAURANT\_DEBUT\_MODELISATION,
BOM, charges, etc.) peuvent aussi être appliqués tels quels :

```
make seed-restaurant-sql
```

Si tu ne veux insérer que les menus de `PARTIE_3_MENU.txt` (Bowl Manioc, Colombo
Gambas, etc.), utilise la cible spécifique :

```
make seed-partie3
```

Et pour vérifier rapidement quels plats/ingrédients ont été injectés par
PARTIE_3_MENU (depuis l’environnement `.venv`), lance :

```
make check-partie3
```

Le fichier `docs/restaurant/menu_seed.yaml` inclut maintenant également les plats
en sauce du relevé (Heru, Ndole, Gombo, Jaune, Pistache, Arachide, Taro) avec leurs
ingrédients clés, ce qui permet de recharger ces fiches techniques via
`make seed-restaurant` après avoir appliqué `seed-partie3`.

La page bancaire `BankStatementAnalyzer` contient deux comptes distincts :
« Incontournable » (restaurant) et « Noutam » (épicerie). Chaque ensemble reprend
les relevés issus des fichiers fournis (relevés Incontournable / Noutam) et
permet d’ajouter manuellement de nouveaux relevés (coller du CSV ou glisser un
fichier). Il est maintenant possible d’envoyer directement un PDF LCL
(`Importer un relevé PDF`) ou d’utiliser la commande :

```
python3 scripts/import_bank_pdf.py --account incontournable ~/releves/
```

Le sélecteur de compte dans la page sert à commuter entre les deux
instances.

La SPA Restaurant expose désormais une page **Relevés bancaires** (route
`/bank-statement`) qui reprend ces transactions, fournit des filtres par mois et
catégorie, et permet d’exporter le tableau filtré via
`frontend/src/features/restaurant/BankStatementAnalyzer.jsx`. Cette page
accepte aussi l’import de relevés PDF LCL (upload direct) : les fichiers sont
parsés côté backend (`/restaurant/bank-statements/import-pdf`) et injectés
dans la table `restaurant_bank_statements`, prêts à être corrigés ou enrichis
depuis l’interface.

Pour vérifier les plats injectés, `python3 scripts/check_partie3.py` affiche la
liste des plats et ingrédients liés au tenant `restaurant`. Utile après
`seed-partie3` pour confirmer qu’on a bien appliqué la Partie 3.

Pour automatiser toutes les étapes (schéma, SQL Restaurant, seed YAML) en une
seule commande :

```
make bootstrap-local
```

La cible appelle `python3 scripts/bootstrap_local.py` et prend les options
`--skip-schema`, `--skip-restaurant-sql`, `--skip-seed`, `--schema-file`,
`--restaurant-sql` et `--tenant` pour maîtriser les phases exécutées.

### Démarrage complet local

`make start-dev` enchaîne :
1. `python3 scripts/bootstrap_local.py --skip-restaurant-sql` pour appliquer le schéma + le
   seed YAML.
2. `uvicorn backend.main:app --reload --port 8000`.
3. `cd frontend && npm run dev`.

Le script `scripts/start_dev_env.sh` gère la capture des signaux et arrête le
backend (uvicorn) quand `npm run dev` se termine.
### Pagination/filter catalogue

Le nouvel endpoint `GET /catalog/products` accepte désormais les filtres `search`, `category`, `status` (`critical|warning|ok`) ainsi que `page` + `per_page`. Il retourne un objet `{ items: ProductOut[], meta: { page, per_page, total } }`.  
Tu peux l’utiliser pour construire les filtres dynamiques du Dashboard/Catalogue sans télécharger tout le catalogue en mémoire (le `fetchProducts` côté SPA accepte un objet `params`).
