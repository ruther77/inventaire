# Flux de données - Fuzzy Matching

## Diagramme de flux

```
┌─────────────────────────────────────────────────────────────────────┐
│                         IMPORT DE FACTURE                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  InvoiceLinesEditor.jsx                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  Ligne de facture                                         │       │
│  │  ┌────────────────────────────────────────────────────┐  │       │
│  │  │ Nom: "Tomate rouge"                                 │  │       │
│  │  │ EAN: (vide)                                         │  │       │
│  │  │ produit_id: null  ← PAS DE MATCH AUTOMATIQUE       │  │       │
│  │  └────────────────────────────────────────────────────┘  │       │
│  │                                                           │       │
│  │  Actions disponibles:                                    │       │
│  │  ┌──────────────────┐  ┌──────┐  ┌────────┐            │       │
│  │  │  Suggestions  ▼  │  │ Lier │  │ Créer  │            │       │
│  │  └──────────────────┘  └──────┘  └────────┘            │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    L'utilisateur clique sur "Suggestions"
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ProductMatchSuggestions.jsx                                         │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  Component State                                          │       │
│  │  • isOpen = true                                          │       │
│  │  • productName = "Tomate rouge"                           │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                        Déclenche useProductMatchSuggestions hook
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  useProductMatchSuggestions (React Query)                            │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  Query Key: ['product-match-suggestions',                │       │
│  │              'Tomate rouge', 5, 60.0]                     │       │
│  │  Enabled: true (car query non vide)                      │       │
│  │  Cache: 60s                                               │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                            Appelle fetchProductMatchSuggestions
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  frontend/src/api/client.js                                          │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  GET /api/invoices/match-suggestions                     │       │
│  │  Params:                                                  │       │
│  │    • query = "Tomate rouge"                               │       │
│  │    • max_results = 5                                      │       │
│  │    • min_score = 60.0                                     │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND - backend/api/invoices.py                                   │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  @router.get("/match-suggestions")                       │       │
│  │  def get_product_match_suggestions()                     │       │
│  │                                                           │       │
│  │  1. Valide la query                                      │       │
│  │  2. Récupère tenant_id                                   │       │
│  │  3. Appelle product_matching.get_fuzzy_product_matches() │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND - backend/services/product_matching.py                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  get_fuzzy_product_matches()                             │       │
│  │                                                           │       │
│  │  1. Normalise query: "tomate rouge"                      │       │
│  │  2. Récupère tous les produits du catalogue              │       │
│  │     SELECT id, nom, categorie, prix...                   │       │
│  │     FROM produits WHERE tenant_id = 1                    │       │
│  │                                                           │       │
│  │  3. Prépare les données pour rapidfuzz:                  │       │
│  │     product_names = [                                    │       │
│  │       "tomates rouges en grappe",                        │       │
│  │       "tomates cerises",                                 │       │
│  │       "tomate coeur de boeuf",                           │       │
│  │       ...                                                 │       │
│  │     ]                                                     │       │
│  │                                                           │       │
│  │  4. Utilise rapidfuzz pour le matching:                  │       │
│  │     matches = process.extract(                           │       │
│  │       "tomate rouge",                                    │       │
│  │       product_names,                                     │       │
│  │       scorer=fuzz.token_sort_ratio,                      │       │
│  │       limit=5                                            │       │
│  │     )                                                     │       │
│  │                                                           │       │
│  │  5. Résultats triés par score:                           │       │
│  │     [                                                     │       │
│  │       ("tomates rouges en grappe", 92.5),                │       │
│  │       ("tomate coeur de boeuf", 78.3),                   │       │
│  │       ("tomates cerises", 65.2),                         │       │
│  │     ]                                                     │       │
│  │                                                           │       │
│  │  6. Filtre par min_score (60.0) et enrichit:             │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RÉPONSE JSON                                                        │
│  {                                                                   │
│    "suggestions": [                                                  │
│      {                                                               │
│        "produit_id": 123,                                            │
│        "produit_nom": "Tomates rouges en grappe",                    │
│        "categorie": "Fruits & Légumes",                              │
│        "prix_achat": 2.50,                                           │
│        "prix_vente": 3.99,                                           │
│        "barcode": "3245678901234",                                   │
│        "score": 92.5,                           ┌──────────┐         │
│        "match_type": "fuzzy_name"               │🟢 92.5%  │         │
│      },                                         └──────────┘         │
│      {                                                               │
│        "produit_id": 456,                                            │
│        "produit_nom": "Tomate coeur de boeuf",                       │
│        "categorie": "Fruits & Légumes",                              │
│        "prix_achat": 3.20,                                           │
│        "prix_vente": 4.99,                                           │
│        "barcode": "3245678901235",                                   │
│        "score": 78.3,                           ┌──────────┐         │
│        "match_type": "fuzzy_name"               │🟡 78.3%  │         │
│      },                                         └──────────┘         │
│      {                                                               │
│        "produit_id": 789,                                            │
│        "produit_nom": "Tomates cerises",                             │
│        "categorie": "Fruits & Légumes",                              │
│        "prix_achat": 3.50,                                           │
│        "prix_vente": 5.49,                                           │
│        "barcode": "3245678901236",                                   │
│        "score": 65.2,                           ┌──────────┐         │
│        "match_type": "fuzzy_name"               │🟠 65.2%  │         │
│      }                                          └──────────┘         │
│    ]                                                                 │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    Retour au frontend via React Query
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ProductMatchSuggestions.jsx - AFFICHAGE                             │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  ┌────────────────────────────────────────────────────┐  │       │
│  │  │ Suggestions de matching                            │  │       │
│  │  │ Produits similaires dans le catalogue              │  │       │
│  │  ├────────────────────────────────────────────────────┤  │       │
│  │  │                                                     │  │       │
│  │  │ 🟢 Tomates rouges en grappe         [92.5%] →     │  │       │
│  │  │    Fruits & Légumes                                │  │       │
│  │  │    EAN: 3245678901234                              │  │       │
│  │  │    Prix achat: 2.50 € | Prix vente: 3.99 €        │  │       │
│  │  │                                                     │  │       │
│  │  │ 🟡 Tomate coeur de boeuf            [78.3%] →     │  │       │
│  │  │    Fruits & Légumes                                │  │       │
│  │  │    EAN: 3245678901235                              │  │       │
│  │  │    Prix achat: 3.20 € | Prix vente: 4.99 €        │  │       │
│  │  │                                                     │  │       │
│  │  │ 🟠 Tomates cerises                  [65.2%] →     │  │       │
│  │  │    Fruits & Légumes                                │  │       │
│  │  │    EAN: 3245678901236                              │  │       │
│  │  │    Prix achat: 3.50 € | Prix vente: 5.49 €        │  │       │
│  │  │                                                     │  │       │
│  │  ├────────────────────────────────────────────────────┤  │       │
│  │  │        + Créer un nouveau produit                  │  │       │
│  │  └────────────────────────────────────────────────────┘  │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    L'utilisateur sélectionne une suggestion
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  onSelectMatch(suggestion)                                           │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  1. Ferme la dropdown                                    │       │
│  │  2. Appelle linkMutation.mutate()                        │       │
│  │  3. Envoie POST /invoices/lines/link                     │       │
│  │     {                                                     │       │
│  │       line: { nom: "Tomate rouge", ... },                │       │
│  │       product_id: 123                                    │       │
│  │     }                                                     │       │
│  │  4. Backend enrichit la ligne avec infos catalogue       │       │
│  │  5. Met à jour la ligne dans l'éditeur                   │       │
│  │     ligne.produit_id = 123                               │       │
│  │     ligne.catalogue_nom = "Tomates rouges en grappe"     │       │
│  │     ligne.catalogue_categorie = "Fruits & Légumes"       │       │
│  │     ligne.prix_achat = 2.50                              │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  InvoiceLinesEditor.jsx - LIGNE MISE À JOUR                          │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  Ligne de facture                                         │       │
│  │  ┌────────────────────────────────────────────────────┐  │       │
│  │  │ Nom: "Tomate rouge" → "Tomates rouges en grappe" │  │       │
│  │  │ EAN: (vide) → "3245678901234"                     │  │       │
│  │  │ produit_id: null → 123  ✅ MATCHÉE               │  │       │
│  │  │ Prix achat: → 2.50 €                              │  │       │
│  │  └────────────────────────────────────────────────────┘  │       │
│  │                                                           │       │
│  │  Actions:                                                 │       │
│  │  (Bouton "Suggestions" n'apparaît plus car produit_id    │       │
│  │   est maintenant défini)                                 │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

## Flux alternatif - Aucune suggestion

```
Ligne sans match → Clic "Suggestions" → Aucune suggestion trouvée
                                              │
                                              ▼
                        ┌────────────────────────────────────┐
                        │ Aucune suggestion trouvée          │
                        │ Essayez de créer un nouveau produit│
                        │                                    │
                        │  + Créer un nouveau produit        │
                        └────────────────────────────────────┘
                                              │
                                Clic sur "Créer un nouveau produit"
                                              │
                                              ▼
                        ┌────────────────────────────────────┐
                        │ POST /invoices/lines/create-product│
                        │ Crée le produit dans le catalogue  │
                        │ Lie automatiquement la ligne       │
                        └────────────────────────────────────┘
```

## Légende des badges de score

| Badge | Score  | Couleur      | Signification              |
|-------|--------|--------------|----------------------------|
| 🟢    | ≥90%   | Vert foncé   | Très bonne correspondance  |
| 🟡    | ≥75%   | Vert clair   | Bonne correspondance       |
| 🟠    | ≥60%   | Jaune/Ambre  | Correspondance acceptable  |
| 🔴    | <60%   | Gris         | Faible correspondance      |

## Optimisations de performance

### Cache React Query
```
Premier appel:  API → Backend → PostgreSQL → Résultats
                ↓
              Cache (60s)
                ↓
Appels suivants: Cache → Résultats (instantané)
```

### Index PostgreSQL
```
Sans index:     Scan complet de la table produits (lent)
Avec index:     Utilisation de l'index gin_trgm (rapide)
```

### Extension pg_trgm
```
Algorithme standard:  O(n) - Parcours linéaire
Avec pg_trgm:        O(log n) - Recherche optimisée
```

## Cas d'usage détaillés

### Cas 1: Match parfait
```
Input:  "Tomate rouge"
Catalogue: "Tomate rouge"
Score: 100%
Action: Auto-match recommandé (score ≥90%)
```

### Cas 2: Variation orthographique
```
Input:  "Lait demi écréme"  (sans accent)
Catalogue: "Lait demi-écrémé"
Score: 95%
Action: Suggéré avec confiance élevée
```

### Cas 3: Ordre des mots différent
```
Input:  "Lait UHT demi-écrémé"
Catalogue: "Demi-écrémé Lait UHT"
Score: 88%
Action: token_sort_ratio détecte la similarité
```

### Cas 4: Synonymes/Abréviations
```
Input:  "Tomates cerises bio"
Catalogue: "Tomates cerises biologiques"
Score: 78%
Action: Suggéré, validation utilisateur recommandée
```

### Cas 5: Produit incomplet
```
Input:  "Tomate"
Catalogue: "Tomate rouge", "Tomate cerise", "Tomate coeur de boeuf"
Scores: 85%, 82%, 78%
Action: Afficher les 3 suggestions pour choix utilisateur
```

### Cas 6: Aucune correspondance
```
Input:  "Nouveau produit XYZ"
Catalogue: Rien de similaire
Score: <60% pour tous
Action: Aucune suggestion → Créer nouveau produit
```

---

**Ce diagramme montre le flux complet de données depuis l'interaction utilisateur jusqu'à la mise à jour de la ligne de facture.**
