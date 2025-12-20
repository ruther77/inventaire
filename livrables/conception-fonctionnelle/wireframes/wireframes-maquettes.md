# Wireframes / maquettes fonctionnelles

## 1. Tableau de bord (vue consolidee)
```
+-------------------------------------------------------------+
| Logo | Recherche...                          | Profil       |
+----------------------+----------------------+---------------+
| KPIs                 | Alertes              | Actions       |
| - CA jour            | - Ruptures (8)       | + Produit     |
| - Marge brute        | - Anomalies (3)      | + Inventaire  |
| - Stock valorise     | - Factures a valider | + Import      |
+----------------------+----------------------+---------------+
| Graphiques (Marge, Stock, Tresorerie, Previsions)           |
+-------------------------------------------------------------+
```

## 2. Catalogue produits
```
+-------------------------------------------------------------+
| Filtres | Cat | Fournisseur | Statut | Recherche            |
+-------------------------------------------------------------+
| Table: Nom | Code-barres | Unite | Prix | Stock | Actions   |
| ...                                                          |
+-------------------------------------------------------------+
| Panneau details: historique prix / mouvements               |
+-------------------------------------------------------------+
```

## 3. Facture fournisseur (validation)
```
+-------------------------------------------------------------+
| Facture #2024-038 | Fournisseur | Date | Statut: Brouillon  |
+-------------------------------------------------------------+
| Lignes facture: Libelle | Qte | PU | Total | Produit | OK ? |
|  - Edition inline / recherche produit                        |
+-------------------------------------------------------------+
| Resume: Total | Ecarts | Bouton Valider                      |
+-------------------------------------------------------------+
```

## 4. Inventaire
```
+-------------------------------------------------------------+
| Session inventaire: Zone A | Date | Responsable             |
+-------------------------------------------------------------+
| Scanner / saisie: Produit | Qte constatee | Qte theorique    |
| Table ecarts: Produit | Ecart | Motif | Action              |
+-------------------------------------------------------------+
| Boutons: Valider ajustements | Export CSV                   |
+-------------------------------------------------------------+
```

## 5. Recettes et menus
```
+-------------------------------------------------------------+
| Plat: Pizza Maison | Cout matiere | Marge                    |
+-------------------------------------------------------------+
| Ingredients: Produit | Qte | Unite | Cout                   |
+-------------------------------------------------------------+
| Menus: Menu Midi -> Plats associes                           |
+-------------------------------------------------------------+
```

## 6. Tresorerie / rapprochement
```
+-------------------------------------------------------------+
| Import releve | Filtres | Statut                            |
+-------------------------------------------------------------+
| Transactions: Date | Libelle | Montant | Categorie | Etat   |
|  - Edition inline, regles automatiques                       |
+-------------------------------------------------------------+
| Rapprochement: Facture | Transaction | Ecart                |
+-------------------------------------------------------------+
```

## 7. Intelligence stock
```
+-------------------------------------------------------------+
| Suggestions de reappro | ABC/XYZ | Stock de securite         |
+-------------------------------------------------------------+
| Produit | Stock | Jours couv. | Suggestion | Action         |
| ...                                                          |
+-------------------------------------------------------------+
| Bouton: Export plan / Creer commande                          |
+-------------------------------------------------------------+
```

## 8. Regles finance
```
+-------------------------------------------------------------+
| Regles de categorisation                                   |
+-------------------------------------------------------------+
| Regle | Mot-cle | IBAN | Montant | Categorie | Active       |
| ...                                                          |
+-------------------------------------------------------------+
| Bouton: Ajouter regle | Appliquer sur periode               |
+-------------------------------------------------------------+
```
