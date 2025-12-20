# Specifications fonctionnelles generales (SFG)

## 1. Contexte
Plateforme web pour la gestion integree Epicerie/Restaurant/Tresorerie avec un module
Intelligence (previsions, optimisation, alertes) et un tableau de bord consolide.

## 2. Objectifs business
- Reduire les ecarts stock/inventaire.
- Fiabiliser les prix d’achat et les marges.
- Accelerer les rapprochements comptables.
- Centraliser indicateurs et alertes.

## 3. Acteurs et droits
- Gerant : tous droits, parametres.
- Responsable achats : produits, fournisseurs, factures.
- Responsable stock : inventaires, mouvements, alertes.
- Responsable restaurant : ingredients, plats, couts.
- Comptable/Finance : tresorerie, regles, rapprochement.
- Analyste : lecture des tableaux de bord, intelligence.

## 4. Perimetre fonctionnel
### 4.1 Opérations
- Catalogue produits, codes-barres, prix.
- Mouvements stock, alertes, inventaires.
- Factures fournisseurs et import.
- Approvisionnement et recommandations.

### 4.2 Restaurant
- Ingredients, plats, menus.
- Calculs couts/marges.
- Transferts et mouvements stock restaurant.

### 4.3 Finance
- Import releves bancaires.
- Regles de categorisation.
- Rapprochement transactions/factures.
- Exports comptables.

### 4.4 Intelligence
- Previsions ventes/cashflow.
- Optimisation stock (EOQ, stock de securite, points de reapprovisionnement).
- Detection anomalies.
- Notation fournisseurs.
- Analyses marges.

### 4.5 Gouvernance
- Multi-tenant et roles.
- Journal d’audit.
- Sauvegardes et reprise.

### 4.6 Carte fonctionnelle (ASCII)
```
Utilisateurs
|-- Gerant
|-- Achats
|-- Stock
|-- Restaurant
|-- Finance
`-- Analyste

Fonctions
|-- Opérations
|-- Restaurant
|-- Finance
|-- Intelligence
|-- Tableau de bord
`-- Admin
```

### 4.7 Matrice acteurs x modules (ASCII)
```
Acteurs \\ Modules | Opérations | Restaurant | Finance | Intelligence | Tableau de bord | Admin
------------------+------------+------------+---------+--------------+-----------------+------
Gerant            |    X       |     X      |   X     |      X       |   X     |  X
Resp. achats      |    X       |            |         |              |         |
Resp. stock       |    X       |     X      |         |      X       |   X     |
Resp. restaurant  |            |     X      |         |              |   X     |
Comptable         |            |            |   X     |              |   X     |
Analyste          |            |            |   X     |      X       |   X     |
```

### 4.8 Arbres detailles par sous-domaine (ASCII)
```
Opérations
|-- Catalogue
|   |-- Produits
|   |-- Codes-barres
|   `-- Historique prix
|-- Stock
|   |-- Mouvements
|   |-- Inventaires
|   `-- Alertes
`-- Factures
    |-- Import
    |-- Rapprochement
    `-- Validation
```

```
Finance
|-- Releves
|   |-- Import
|   `-- Normalisation
|-- Regles
|   |-- Creation
|   |-- Priorites
|   `-- Exceptions
|-- Categorisation
|   |-- Auto
|   `-- Manuelle
`-- Rapprochement
    |-- Rapprochement auto
    `-- Validation
```

```
Restaurant
|-- Ingredients
|-- Plats
|   |-- Composition
|   `-- Cout/marge
|-- Menus
`-- Stock restaurant
```

## 5. Exigences non fonctionnelles
- Disponibilite : 99.5% cible.
- Performance : P90 < 300ms endpoints critiques.
- Securite : RBAC, isolation tenant, TLS.
- Observabilite : journaux structures + metriques.

## 6. Hypotheses
- Les imports fournisseurs sont heterogenes mais exploitables.
- Les codes-barres sont uniques par tenant.
- L’authentification est interne (pas SSO).

## 7. Criteres d’acceptation globaux
- Un produit peut etre cree, utilise en stock et en recette.
- Une facture importee met a jour prix et stock apres validation.
- Les previsions sont consultables par periode.
- Un releve bancaire est categorise et exportable.
- Les alertes stock et anomalies sont visibles dans le tableau de bord.
