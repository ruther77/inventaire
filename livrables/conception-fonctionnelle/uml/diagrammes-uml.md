# Diagrammes UML

## 1. Cas d’usage (vue d’ensemble)
```mermaid
flowchart LR
  Gerant((Gerant)) --> UC1[Consulter cockpit & KPIs]
  Gerant --> UC2[Configurer tenants & roles]
  Achats((Resp. achats)) --> UC3[Importer facture fournisseur]
  Achats --> UC4[Maintenir catalogue produits]
  Stock((Resp. stock)) --> UC5[Realiser inventaire]
  Stock --> UC6[Traiter alertes de rupture]
  Resto((Resp. restaurant)) --> UC7[Maintenir ingredients]
  Resto --> UC8[Creer plats & menus]
  Finance((Comptable)) --> UC9[Importer releves]
  Finance --> UC10[Rapprocher transactions]
  Analyste((Analyste)) --> UC11[Consulter previsions & marges]
```

## 1.1 Diagramme de composants (haut niveau)
```mermaid
flowchart LR
  SPA[SPA React] --> API[FastAPI]
  API --> OPS[Opérations]
  API --> RESTO[Restaurant]
  API --> FIN[Finance]
  API --> INTEL[Intelligence]
  API --> TABLEAU[Tableau de bord]
  OPS --> DB[(PostgreSQL)]
  RESTO --> DB
  FIN --> DB
  INTEL --> DB
```

## 2. Sequence : Import facture fournisseur
```mermaid
sequenceDiagram
  actor Acheteur as Resp. achats
  participant UI as SPA
  participant API as FastAPI
  participant OCR as Extraction
  participant DB as PostgreSQL

  Acheteur->>UI: Deposer facture (PDF/CSV)
  UI->>API: Televersement + metadonnees
  API->>OCR: Extraire lignes
  OCR-->>API: Lignes facture
  API->>DB: Stocker facture + lignes (brouillon)
  API-->>UI: Renvoyer lignes a valider
  Acheteur->>UI: Corriger/associer produits
  UI->>API: Valider facture
  API->>DB: Maj prix + stock + historique
  API-->>UI: Confirmation
```

## 3. Sequence : Rapprochement bancaire
```mermaid
sequenceDiagram
  actor Comptable as Comptable
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Comptable->>UI: Importer releve
  UI->>API: Televersement releve
  API->>DB: Stocker transactions
  API->>API: Rapprochement automatique
  API-->>UI: Propositions de rapprochement
  Comptable->>UI: Valider / corriger
  UI->>API: Appliquer rapprochement
  API->>DB: Ecrire reconciliation + audit
  API-->>UI: Statut OK
```

## 4. Sequence : Optimisation stock (EOQ / reapprovisionnement)
```mermaid
sequenceDiagram
  actor Stock as Resp. stock
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Stock->>UI: Ouvrir optimisation stock
  UI->>API: /inventory-intelligence/reorder-suggestions
  API->>DB: Charger ventes, stock, delais
  API->>API: Calcul EOQ + stock de securite
  API-->>UI: Liste suggestions
  Stock->>UI: Creer plan d’appro
```

## 5. Sequence : Synchronisation prix restaurant
```mermaid
sequenceDiagram
  actor Resto as Resp. restaurant
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Resto->>UI: Lancer synchronisation prix
  UI->>API: /restaurant/ingredients/sync-prices
  API->>DB: Charger liens epicerie
  API->>DB: Mettre a jour prix ingredients
  API-->>UI: Statut et rapport
```

## 6. Activite : Inventaire
```mermaid
flowchart TD
  A[Demarrer session inventaire] --> B[Scanner / saisir quantites]
  B --> C[Calcul ecarts]
  C --> D{Ecarts significatifs?}
  D -- Oui --> E[Valider ajustements]
  D -- Non --> F[Cloturer]
  E --> F[Cloturer]
```

## 7. Activite : Categorisation bancaire
```mermaid
flowchart TD
  A[Importer releve] --> B[Normaliser libelles]
  B --> C[Appliquer regles]
  C --> D{Categorie trouvee?}
  D -- Oui --> E[Marquer categorisee]
  D -- Non --> F[Mettre en attente]
  F --> G[Correction manuelle]
  G --> E
```

## 8. Etat : Facture fournisseur
```mermaid
stateDiagram-v2
  [*] --> Brouillon
  Brouillon --> En_validation
  En_validation --> Validee
  En_validation --> Rejetee
  Validee --> Comptabilisee
  Rejetee --> Brouillon
  Comptabilisee --> [*]
```

## 9. Sequence : Ajustement stock (inventaire)
```mermaid
sequenceDiagram
  actor Stock as Resp. stock
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Stock->>UI: Ouvrir session inventaire
  UI->>API: Creer session
  API->>DB: Insert session
  Stock->>UI: Saisir quantites
  UI->>API: Enregistrer lignes
  API->>DB: Insert lignes inventaire
  Stock->>UI: Valider
  UI->>API: Valider session
  API->>DB: Generer mouvements + maj stock
  API-->>UI: Statut OK
```

## 10. Sequence : Application regles finance
```mermaid
sequenceDiagram
  actor Finance as Comptable
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Finance->>UI: Lancer application regles
  UI->>API: /rules-engine/apply
  API->>DB: Charger transactions
  API->>API: Evaluer regles
  API->>DB: Ecrire classifications
  API-->>UI: Rapport d’application
```

## 11. Diagramme de classes (domaines cles)
```mermaid
classDiagram
  class Produit {
    id
    nom
    categorie
    prix_achat
    prix_vente
    stock_actuel
  }
  class MouvementStock {
    id
    type
    quantite
    date_mvt
  }
  class Facture {
    id
    total
    status
  }
  class Ingredient {
    id
    nom
    cout
  }
  class Plat {
    id
    nom
    prix_vente
  }
  class Transaction {
    id
    montant
    status
  }

  Produit "1" --> "0..*" MouvementStock
  Facture "1" --> "0..*" Produit : lines
  Ingredient "0..*" --> "0..*" Plat : compose
  Transaction "0..*" --> "0..1" Facture : rapproche
```

## 12. Sequence : Calcul marges (snapshots)
```mermaid
sequenceDiagram
  actor Analyste as Analyste
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Analyste->>UI: Demander analyse marges
  UI->>API: /margins/summary
  API->>DB: Charger ventes + prix + stock
  API->>API: Calculer marge brute
  API->>DB: Stocker snapshot
  API-->>UI: Resultats + tendances
```

## 13. Sequence : Detection anomalies
```mermaid
sequenceDiagram
  actor Analyste as Analyste
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Analyste->>UI: Lancer detection anomalies
  UI->>API: /anomaly-detection/run
  API->>DB: Charger historiques prix/stock
  API->>API: Detecter anomalies
  API->>DB: Ecrire anomalies detectees
  API-->>UI: Liste + severite
```

## 14. Sequence : Notation fournisseurs
```mermaid
sequenceDiagram
  actor Acheteur as Resp. achats
  participant UI as SPA
  participant API as FastAPI
  participant DB as PostgreSQL

  Acheteur->>UI: Recalculer notation
  UI->>API: /supplier-scoring/recalculate
  API->>DB: Charger livraisons + incidents
  API->>API: Calcul scores par dimension
  API->>DB: Stocker historique scores
  API-->>UI: Scores + classement
```
