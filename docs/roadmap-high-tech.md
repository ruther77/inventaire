## Roadmap High-tech

1. **Dashboard & Catalogue**
   * Modes “focus” : card metrics interactives (sélection, anchor actions) et affichage des erreurs via toasts/descriptions.
   * Pagination & filtering côté API (fin de saisir l’ensemble du catalogue en mémoire).
   * Indicateurs de fragilité : boutons “actifs” désactivés lors d’erreur API.

2. **Approvisionnement & Import**
   * Advisor multi-step : upload → scan → validate → import avec contrôle des lignes (prix >=0, TVA 5/10/20, quantités).
   * État “Batch pending” et export des drafts validés.
   * Relance “scanner + import” via `ScannerPage`.

3. **Restaurant HQ**
   * Board unifié “Relevés → Charges → Catégories” (board de tickets avec états).
   * Distinction “matières premières vs bouteilles” en vue Menu.
   * Automatic sync complet via `make refresh-reports` et `make reset-restaurant`.

Chaque étape inclut tests visuels (design tokens, CTA) et doc utilisateur.
