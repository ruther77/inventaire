# Expérimentations isolées

Le dossier `experiments/new_model/` contient une implémentation prototype de la refonte (modèle séparé épicerie vs restaurant, calculs de capital consolidé). Cette approche permet de travailler sans polluer l’existant.

## Workflow
1. **Lancer en parallèle** : les scripts `python -m experiments.new_model.simulation` ou d’autres modules de `experiments/new_model` ne touchent aucune table réelle (ils utilisent uniquement des `dataclass`). Tu peux donc expérimenter librement.
2. **Comparer** : lorsque l’algorithme donne une vue satisfaisante (snapshot, agrégations), tu peux transposer la logique dans `backend/services/*` en adaptant `CapitalSnapshot` et `PriceHistory`.
3. **Basculer** : pour revenir à l’existant, il suffit de continuer à lancer les services/commands habituels (`python -m backend.main`, `npm run dev`), puisqu’aucun fichier système n’a été modifié.

## Prochaines étapes
- Traduire les dataclasses en tables (voir `experiments/new_model/schema.sql`), notamment `PriceHistory` et `CapitalSnapshot` avec contraintes multi-tenant et indexes de date.
- Ajouter des scripts de simulation qui ingestent des données réelles (factures, mouvements).
- Intégrer la nouvelle vue dans une route API (`/capital/overview`) et dans la SPA.
- Planifier `scripts/generate_capital_snapshot.py` (cron ou scheduler) pour qu’il s’exécute quotidiennement, en le lançant après les imports/rapports journaliers pour garder les snapshots à jour.
