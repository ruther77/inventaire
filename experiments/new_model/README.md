# Nouvelle implémentation expérimentale

Ce dossier concentre une **version isolée** de la refonte « capital consolidé / séparation épicerie vs restaurant » afin de pouvoir prototyper sans toucher à l’existant.

## Objectifs
1. Représenter les entités distinctes (`Produit`, `Plat`, `Ingredient`, `InvoiceLine`, `CapitalSnapshot`) sous une forme modulaire.
2. Fournir des scripts expérimentaux qui peuvent calculer les vues consolidées (`CapitalSnapshot`, `PortfolioView`).
3. Permettre de tester rapidement les nouveaux workflows (factures → price history, dashboards globaux) sans impacter la base de production actuelle.

## Contenu
- `model.py` : dataclasses pour les entités principales (tenant, produit, plat, invoice line, price history, capital snapshot).
- `simulation.py` : fonctions utilitaires pour synthétiser les métriques globales à partir d’exemples.
- `README.md` : cette note.

## Usage
```bash
python -m experiments.new_model.simulation
```

## Remarque
Ce dossier est volontairement découplé. Une fois validé, les modules pourront être backportés dans `backend/` et `frontend/`.
