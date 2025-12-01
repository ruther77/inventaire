.PHONY: up down rebuild logs psql shell fmt lint test precommit-install

up: ## démarrer tous les services
	docker compose --env-file .env up -d

down: ## arrêter et supprimer (conteneurs/volumes)
	docker compose --env-file .env down -v

rebuild: ## rebuild clean
	docker compose --env-file .env build --no-cache
	docker compose --env-file .env up -d

logs: ## suivre les logs de l'app
	docker compose logs -f app

psql: ## console postgres
	docker compose exec db psql -U postgres -d epicerie

update-epicerie-costs: ## met à jour les prix d’achat Epicerie liés à la carte restaurant
	@bash scripts/run_epicerie_cost_updates.sh

shell: ## shell dans le conteneur app
	docker compose exec app bash || docker compose exec app sh

sync-restaurant-ingredients: ## synchronise les ingrédients plats ↔ Epicerie (sans ventes)
	docker compose exec api env PYTHONPATH=/app python scripts/generate_restaurant_ingredients.py

fmt: ## format (black + ruff --fix)
	docker compose run --rm app bash -lc "python -m pip install -q black ruff && black . && ruff check . --fix || true"

lint: ## lint (ruff)
	docker compose run --rm app bash -lc "python -m pip install -q ruff && ruff check ."

test: ## placeholder tests
	@echo 'Aucun test défini pour le moment.'

precommit-install:
	python -m pip install -q pre-commit
	pre-commit install

start-dev: ## Bootstrap + lance backend (uvicorn) et frontend (npm run dev)
	bash scripts/start_dev_env.sh

# dossier contenant les PDF à réimporter (ajuste au besoin)
PDF_DIR ?= ./pdfs
TENANT_ID ?= 1

refresh-reports: ## Réinitialise les relevés + relance import, charges et reclassification
	test -d $(PDF_DIR) || (echo "Répertoire $(PDF_DIR) introuvable. Crée-le ou redéfinis PDF_DIR." && exit 1)
	docker compose exec db psql -U postgres -d epicerie -c "TRUNCATE restaurant_bank_statements, restaurant_depenses RESTART IDENTITY CASCADE;"
	docker compose exec api bash -lc "python -m scripts.refresh_from_pdf --tenant restaurant --account \"incontournable\" --pdf /app/$(notdir $(PDF_DIR))"
	docker compose exec api bash -lc "python -m scripts.reclassify_bank_statements --tenant $(TENANT_ID)"

# ----- Production helpers -----
prod-up: ## lancer le stack de prod (derrière Caddy)
	docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

prod-down: ## arrêter et supprimer la prod
	docker compose --env-file .env.prod -f docker-compose.prod.yml down -v

prod-rebuild: ## rebuild + up (prod)
	docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache
	docker compose --env-file .env.prod -f docker-compose.prod.yml up -d


# ... (Contenu existant) ...

IMPORT_FILE ?= docs/invoices/Produit.csv
RESTAURANT_SEED ?= docs/restaurant/menu_seed.yaml

import-data: ## Importer les produits (utilise docs/invoices/Produit.csv par défaut)
	@echo "Lancement de l'importation de $(IMPORT_FILE) avec prix d'achat par défaut de 0.5..."
	docker compose exec app python3 -m core.products_loader $(IMPORT_FILE)
	@echo "Importation terminée. Redémarrez le conteneur 'app' ou videz le cache Streamlit si l'affichage n'est pas à jour."

seed-restaurant: ## Alimente les tables Restaurant HQ depuis docs/restaurant/menu_seed.yaml
	python3 scripts/seed_restaurant.py --file $(RESTAURANT_SEED)

seed-restaurant-sql: ## Applique les scripts SQL issus des fichiers docs/restaurant/*.txt
	python3 scripts/apply_restaurant_sql.py

seed-partie3: ## Applique uniquement les inserts contenus dans PARTIE_3_MENU.txt
	docker compose --env-file .env run --rm app bash -lc "cd /app && source .venv/bin/activate && python scripts/apply_restaurant_sql.py --files docs/restaurant/PARTIE_3_MENU.txt"

reset-restaurant: ## Recrée les ingrédients/bouteilles puis réimporte les relevés
	make seed-partie3
	make refresh-reports PDF_DIR=./pdfs

check-partie3: ## Affiche les plats liés à PARTIE_3_MENU dans le container
	docker compose --env-file .env run --rm app bash -lc "cd /app && source .venv/bin/activate && python scripts/check_partie3.py"

bootstrap-local: ## Applique le schéma + les SQL Restaurant + le seed YAML
	python3 scripts/bootstrap_local.py
