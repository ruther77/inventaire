# Migration FastAPI + SPA — Cartographie & Plan d’implémentation

## 1. Cartographie détaillée de l’application Streamlit

| Onglet / Feature             | Inputs principaux                                                                                | Outputs / actions clés                                                                                         | Dépendances SQL / Services                                                                               | Règles métier notables                                                                                              | Catégorie |
|-----------------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|-----------|
| **Vitrine**                 | Aucun input direct (lecture seule).                                                             | KPIs clients, badges marketing, graphes Plotly Top ventes.                                                     | `load_customer_catalog`, `fetch_price_history`, caches produits.                                         | Calcul marge %, alertes bas stock, badges dynamiques.                                                                | Support   |
| **Approvisionnement**       | Sélecteurs filtres, import CSV, formulaires d’ajout/fusion fournisseur.                         | Table plan appro, exports CSV, suggestions de commandes.                                                       | `plan_supply`, `load_products_list`, `register_supply_order`.                                            | Calcul couverture jours, application marges, alertes rupture.                                                         | Critique  |
| **Vente (PoS)**             | Sélecteur produit, quantité, scanner (WebRTC), bouton “Finaliser vente”.                        | Ticket, `process_sale_transaction`, mise à jour panier/stock.                                                  | `inventory_service.process_sale_transaction`, `register_cache products`.                                | Concurrence panier, validation stock, calcul TVA.                                                                    | Critique  |
| **Catalogue**               | Formulaires CRUD produit, modale fiche, import CSV, assignation catégorie.                      | Création/édition produit, gestion codes-barres, export CSV.                                                    | `products_loader`, `product_service.update_catalog_entry`, `data_repository` requêtes directes.          | Règles inflation prix, marge minimale, validation codes.                                                             | Critique  |
| **Stock & Mvt**             | Filtres produit/période, formulaires ajustement stock, import inventaire.                       | Graphiques mouvement, DataFrame mouvements, bouton “Créer mouvement”.                                          | `load_movement_timeseries`, `register_invoice_reception`, `create_manual_movement`.                     | Alignement stock calculé vs matérialisé, permissions admin.                                                           | Critique  |
| **Audit & écarts**          | Assignation responsable, statut tâches, exports CSV.                                            | Tableau écarts, toasts assignation, export investigations.                                                     | `load_stock_diagnostics`, `assign_audit_task`, `record_resolution`.                                      | Workflow assignation, log résolution, suivi SLA.                                                                     | Support   |
| **Dashboard**               | Filtres segmentations, date range.                                                              | Cartes KPI, graphiques synthèse, export PDF/PNG (Plotly).                                                       | `build_dashboard_metrics`, `fetch_price_history`, `load_recent_movements`.                               | Consolidation multi-sources, arrondis financiers.                                                                    | Support   |
| **Scanner**                 | Flux webcam (WebRTC), bouton start/stop.                                                        | Dernier code scanné injecté dans PoS ou import.                                                                | `BarcodeDetector` (OpenCV + pyzbar), `st.session_state` synchronisation.                                 | Déclenche `st.rerun` sur détection.                                                                                  | Legacy    |
| **Extraction Facture**      | Upload PDF/DOCX/TXT, textarea texte brut, slider marge, table édition colonnes détectées.        | Résumé import (`products_loader.load_products_from_df`), enregistrement prix historique.                       | `invoice_extractor`, `products_loader`, `record_price_history`.                                          | Règles inflation, marge minimum, normalisation libellés, plus **pas** de mouvements après refactor.                   | Legacy    |
| **Importation**             | Upload facture, textarea, configuration réception (fournisseur, date, mode), bouton mouvements. | `register_invoice_reception` → mouvements `ENTREE`, export CSV commande.                                      | `_prepare_invoice_dataframe`, `register_invoice_reception`, `record_price_history` (via extraction).     | Vérifie produits identifiés, ne touche plus au catalogue (notice).                                                  | Critique  |
| **Suivi Prix**              | Filtres produit/fournisseur, date range, limite lignes.                                         | Graphiques Recharts/Plotly variations, table historique, export CSV.                                           | `fetch_price_history`, `record_price_history`.                                                            | Calcul amplitude, variations %, alertes promo.                                                                       | Support   |
| **Maintenance (Admin)**     | Boutons backup/restore, forms planification, tableau sauvegardes, gestion utilisateurs (nouveau). | Lancement `pg_dump`/`psql`, affichage diagnostic, création/restauration backup, gestion comptes.               | `backup_manager`, `user_service`, `load_table_counts`, `load_stock_diagnostics`.                         | Vérif binaires, statut backup, restrictions rôle admin.                                                              | Support   |
| **Outils hérités (Scanner/Extraction PDF avancée)** | Caméra, parsing PDF complexe (OCR). | Flux WebRTC, modale extraction. | `streamlit_webrtc`, `invoice_extractor`. | Forte dépendance libs desktop → maintenance future. | Legacy |

## Catégorisation synthétique

- **Critiques temps réel** : Catalogue, PoS, Stock & Mvt, Importation (réception), Approvisionnement.
- **Support métier** : Vitrine, Audit & écarts, Dashboard, Suivi Prix, Maintenance.
- **Legacy / Expert** : Scanner (WebRTC), Extraction facture avancée (OCR multi-format) – à encapsuler ou réécrire plus tard.

---

## 2. Plan de stabilisation API FastAPI

1. **Structure des services**
   ```
   backend/
   ├── api/                 # routeurs FastAPI (catalog.py, pos.py, invoices.py, admin.py, etc.)
   ├── services/            # logique métier (catalog_service, invoice_service, stock_service…)
   ├── schemas/             # Pydantic v2 models (requests/responses)
   ├── db/                  # session, models SQLAlchemy (optionnel, aujourd’hui requêtes text)
   └── main.py              # instancie FastAPI, inclut routeurs, middlewares CORS/JWT
   ```

2. **Endoints clés à (ré)implémenter**
   - `/catalogue` : CRUD produits, gestion codes-barres, recherche, import CSV (upload → background task).
   - `/pos` : validation panier, émission ticket (PDF/base64), suivi caisse.
   - `/inventory/receptions` : pipeline facture → mouvements (upload, mapping, création `ENTREE`).
   - `/stock` : mouvements, ajustements, diagnostics.
   - `/audit`, `/reports`, `/price-watch` : exposer les jeux de données aujourd’hui calculés côté Streamlit.
   - `/admin` : backups, diagnostics, gestion utilisateurs (promotion/déclassement, reset password).

3. **Techniques**
   - Pydantic v2 pour toutes les payloads (idéalement `BaseModel` avec `ConfigDict` strict).
   - Gestion erreurs harmonisée (`HTTPException` + format JSON). Ajouter un middleware pour convertir les erreurs métiers.
   - Authentification : JWT stateless ou session signée (selon besoin). `user_service.py` servira d’entrée pour l’auth API.
   - Tests : pytest + httpx TestClient. Couvrir chaque route critique + scénarios d’échec.

4. **Transitions**
   - Au fur et à mesure qu’une fonctionnalité est exposée via FastAPI, détourner Streamlit pour consommer l’API (ou désactiver l’onglet) afin de valider la parité fonctionnelle avant suppression.

---

## 3. SPA React (Vite) — Architecture cible

1. **Structure du code**
   ```
   frontend/src/
   ├── app/                  # Provider, routes, layout
   ├── features/
   │   ├── catalog/
   │   ├── pos/
   │   ├── inventory/
   │   ├── invoices/
   │   ├── audit/
   │   ├── admin/
   │   └── legacy/ (scanner, extraction)
   ├── components/           # UI primitives (Button, Card, Table…)
   ├── hooks/                # useProducts(), useInvoices(), etc.
   ├── api/                  # client axios + typage endpoints
   └── styles/               # design system (Tailwind + tokens)
   ```

2. **Data layer**
   - React Query déjà en place → créer des hooks par feature (`useProducts`, `useReceptionWizard`, `usePriceHistory`).
   - Typage via `zod` ou Typescript interfaces générées à partir des schémas Pydantic (long terme : `openapi-typescript`).

3. **Design system**
   - Continuer à enrichir les composants (cards, tables virtuelles, modales, steps). Gérer les states `empty`, `loading`, `error` de façon cohérente.
   - Prévoir un theming clair/sombre.

4. **Modules à migrer**
   - **Catalogue** : listing + fiche modale + création/modif + import CSV + gestion codes-barres.
   - **PoS** : caisse tactile, scanner (WebRTC), panier, ticket.
   - **Import facture/Inventaire** : wizard upload → matching → réception (avec preview mouvements et export). Possibilité de laisser la partie OCR en iframe tant qu’elle n’est pas réécrite.
   - **Maintenance/Admin** : dashboards backup, gestion comptes, diagnostics (charts + tables). Les actions critiques déclenchent des modales de confirmation.
   - **Support (Audit, Price watch, Dashboard)** : transposer en graphiques/rapports React (Recharts/Plotly) avec filtres modernes.

5. **Performance**
   - Code-splitting par route (`React.lazy`) + configuration Rollup `manualChunks` pour éviter le warning >500 kB.
   - Mise en cache des données (React Query + staleTime) et skeletons pour chargements.

---

## Étapes suivantes

1. Valider cette cartographie + structure API/SPA.
2. Prioriser les modules Critiques (Catalogue, PoS, Stock/Mvt, Importation) → implémenter les services FastAPI correspondants + vues React.
3. Migrer progressivement les modules Support, puis traiter les Legacy (scanner/OCR) en dernier (iframe ou réécriture complète).
