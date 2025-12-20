# Fuzzy Matching - Résumé de l'implémentation

## Vue d'ensemble rapide

Cette fonctionnalité améliore le matching des produits importés depuis les factures en utilisant la bibliothèque **rapidfuzz** pour suggérer automatiquement des produits similaires du catalogue.

## Fichiers créés

### Backend
1. **`backend/services/product_matching.py`** - Service de fuzzy matching
   - `get_fuzzy_product_matches()` - Recherche de produits similaires
   - `get_best_product_match()` - Meilleur match unique
   - `enrich_lines_with_fuzzy_matches()` - Enrichissement batch

2. **`backend/api/invoices.py`** - Endpoint ajouté
   - `GET /invoices/match-suggestions` - API de suggestions

### Frontend
1. **`frontend/src/features/invoices/components/ProductMatchSuggestions.jsx`**
   - Composant dropdown de suggestions avec scores

2. **`frontend/src/hooks/useInvoiceImport.js`** - Hook ajouté
   - `useProductMatchSuggestions()` - Hook React Query

3. **`frontend/src/api/client.js`** - Fonction ajoutée
   - `fetchProductMatchSuggestions()` - Client API

### Documentation
- **`docs/FUZZY_MATCHING_IMPLEMENTATION.md`** - Documentation complète
- **`scripts/test_fuzzy_matching.py`** - Script de test

### Configuration
- **`requirements.txt`** - Ajout de `rapidfuzz>=3.6.0`

## Fichiers modifiés

1. **`frontend/src/features/invoices/components/InvoiceLinesEditor.jsx`**
   - Intégration du composant `ProductMatchSuggestions`
   - Affichage automatique pour lignes sans produit_id

2. **`frontend/src/features/invoices/components/index.js`**
   - Export du nouveau composant

## Installation rapide

### Backend
```bash
# 1. Installer rapidfuzz
pip install -r requirements.txt

# 2. (Optionnel) Installer l'extension PostgreSQL pour meilleures performances
psql -d votre_base -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
psql -d votre_base -c "CREATE INDEX idx_produits_nom_trgm ON produits USING gin(nom gin_trgm_ops);"

# 3. Redémarrer le serveur
uvicorn backend.main:app --reload
```

### Frontend
Aucune installation nécessaire - les composants utilisent les dépendances React existantes.

## Test rapide

### 1. Test Backend (Python)
```bash
python scripts/test_fuzzy_matching.py
```

### 2. Test API (curl)
```bash
curl -X GET "http://localhost:8000/api/invoices/match-suggestions?query=Tomate&max_results=5"
```

### 3. Test Frontend (UI)
1. Aller sur la page Import de factures
2. Uploader une facture
3. Cliquer sur "Suggestions" pour une ligne sans produit_id
4. Visualiser les suggestions avec scores

## Comment ça marche

### Backend
```python
# Exemple d'utilisation
from backend.services import product_matching

suggestions = product_matching.get_fuzzy_product_matches(
    "Tomate rouge",  # Recherche
    tenant_id=1,
    max_results=5,    # Top 5 résultats
    min_score=60.0    # Score minimum 60%
)
# Retourne: liste de produits avec scores 0-100
```

### Frontend
```jsx
// Composant automatiquement intégré dans InvoiceLinesEditor
<ProductMatchSuggestions
  productName={line.nom}
  onSelectMatch={(suggestion) => {
    // Lie automatiquement au produit
    linkToProduct(suggestion.produit_id);
  }}
  onCreateNew={() => {
    // Crée un nouveau produit
    createNewProduct();
  }}
/>
```

## Fonctionnalités clés

### Scores de confiance avec badges colorés
- 🟢 **≥90%** - Très bonne correspondance (vert foncé)
- 🟡 **≥75%** - Bonne correspondance (vert clair)
- 🟠 **≥60%** - Correspondance acceptable (jaune)
- 🔴 **<60%** - Faible correspondance (gris)

### Algorithme intelligent
- **token_sort_ratio** de rapidfuzz
- Ignore l'ordre des mots ("Lait UHT" = "UHT Lait")
- Tolère les fautes d'orthographe ("écréme" vs "écrémé")
- Gère les variations ("bio" vs "biologique")

### Interface utilisateur
- Dropdown élégante avec détails produits
- Affichage du score en %
- Catégorie, prix, code EAN visibles
- Option "Créer nouveau produit" si rien ne convient
- Fermeture auto en cliquant dehors

## Paramètres configurables

### Seuils recommandés
- **Auto-matching backend:** `min_score=75.0` (évite faux positifs)
- **Suggestions UI frontend:** `min_score=60.0` (plus permissif, validation manuelle)

### Personnalisation
```python
# Backend: backend/services/product_matching.py
get_fuzzy_product_matches(
    query,
    tenant_id=1,
    max_results=5,     # Nombre de suggestions
    min_score=60.0     # Score minimum
)
```

```javascript
// Frontend: useProductMatchSuggestions hook
useProductMatchSuggestions(query, {
  maxResults: 5,    // Nombre de suggestions
  minScore: 60.0    // Score minimum
})
```

## Cas d'usage

### ✅ Variations orthographiques
- Importé: "Pommes Golden 1kg"
- Catalogue: "Pomme Golden (1 kg)"
- Score: ~95% → Suggéré

### ✅ Ordre des mots différent
- Importé: "Lait demi-écrémé UHT"
- Catalogue: "UHT Lait Demi-Écrémé"
- Score: ~88% → Suggéré

### ✅ Fautes d'orthographe
- Importé: "Tomates cerises bio"
- Catalogue: "Tomates cerises biologiques"
- Score: ~78% → Suggéré

### ❌ Aucune correspondance
- Importé: "Nouveau produit XYZ"
- Catalogue: Rien de similaire
- Résultat: Aucune suggestion → Créer nouveau

## Performance

### Optimisations
- ✅ Cache React Query (1 minute)
- ✅ Recherche à la demande (enabled=false par défaut)
- ✅ Index PostgreSQL sur `produits.nom`
- ✅ Extension pg_trgm (optionnel, recommandé >10k produits)

### Scalabilité
- **<10k produits:** Excellentes performances sans optimisation
- **10k-50k produits:** Recommandé pg_trgm
- **>50k produits:** Considérer Elasticsearch/MeiliSearch

## Dépannage rapide

### Problème: "rapidfuzz not found"
```bash
pip install rapidfuzz>=3.6.0
```

### Problème: Aucune suggestion
1. Vérifier que le catalogue contient des produits
2. Réduire `min_score` à 40-50
3. Essayer un nom plus générique

### Problème: Suggestions non pertinentes
Augmenter `min_score` à 70-80

### Problème: Performances lentes
```sql
-- Ajouter l'extension et l'index
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_produits_nom_trgm ON produits USING gin(nom gin_trgm_ops);
```

## Documentation complète

Voir **`docs/FUZZY_MATCHING_IMPLEMENTATION.md`** pour:
- Architecture détaillée
- Exemples d'API complets
- Guide de configuration avancée
- Roadmap des améliorations futures
- Tests unitaires

## Prochaines étapes suggérées

1. **Tester l'installation:**
   ```bash
   pip install -r requirements.txt
   python scripts/test_fuzzy_matching.py
   ```

2. **Tester l'API:**
   ```bash
   curl -X GET "http://localhost:8000/api/invoices/match-suggestions?query=Test"
   ```

3. **Tester l'interface:**
   - Importer une facture
   - Cliquer sur "Suggestions" pour une ligne
   - Valider qu'une suggestion fonctionne

4. **Optimiser (si >10k produits):**
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE INDEX idx_produits_nom_trgm ON produits USING gin(nom gin_trgm_ops);
   ```

5. **Ajuster les seuils** selon vos besoins dans:
   - `backend/services/product_matching.py`
   - `frontend/src/hooks/useInvoiceImport.js`

## Support

Questions? Consultez:
1. Cette documentation
2. `docs/FUZZY_MATCHING_IMPLEMENTATION.md`
3. Les logs backend/frontend
4. Le script de test `scripts/test_fuzzy_matching.py`

---

**Statut:** ✅ Implémentation complète et fonctionnelle
**Dernière mise à jour:** 2025-12-15
