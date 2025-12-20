# Fuzzy Matching pour le Matching de Produits - Documentation

## Vue d'ensemble

Cette fonctionnalité améliore le matching des produits importés depuis les factures avec le catalogue existant en utilisant le fuzzy matching (correspondance floue). Elle permet de suggérer automatiquement des produits similaires du catalogue lorsqu'un produit importé ne correspond pas exactement.

## Architecture

### Backend

#### 1. Service de Matching Fuzzy (`backend/services/product_matching.py`)

Le service utilise la bibliothèque `rapidfuzz` pour effectuer des comparaisons de similarité entre les noms de produits.

**Fonctions principales:**

- `get_fuzzy_product_matches()`: Recherche les produits similaires dans le catalogue
  - Utilise `token_sort_ratio` de rapidfuzz pour gérer les mots dans différents ordres
  - Retourne les top N résultats avec leurs scores de confiance (0-100)
  - Paramètres configurables: `max_results`, `min_score`

- `get_best_product_match()`: Retourne le meilleur match unique
  - Utile pour l'auto-matching automatique
  - Seuil par défaut: 75%

- `enrich_lines_with_fuzzy_matches()`: Enrichit un batch de lignes avec suggestions
  - Traite plusieurs lignes d'un coup
  - Ajoute un champ `fuzzy_suggestions` à chaque ligne

**Exemple d'utilisation:**

```python
from backend.services import product_matching

# Rechercher des suggestions pour "Tomate rouge"
suggestions = product_matching.get_fuzzy_product_matches(
    "Tomate rouge",
    tenant_id=1,
    max_results=5,
    min_score=60.0
)

# Résultat:
# [
#     {
#         "produit_id": 123,
#         "produit_nom": "Tomates rouges en grappe",
#         "categorie": "Fruits & Légumes",
#         "prix_achat": 2.50,
#         "prix_vente": 3.99,
#         "barcode": "3245678901234",
#         "score": 92.5,
#         "match_type": "fuzzy_name"
#     },
#     ...
# ]
```

#### 2. Endpoint API (`backend/api/invoices.py`)

**Nouveau endpoint:** `GET /invoices/match-suggestions`

**Paramètres:**
- `query` (required): Nom du produit à rechercher
- `max_results` (optional, default=5): Nombre maximum de suggestions
- `min_score` (optional, default=60.0): Score minimum de confiance (0-100)

**Exemple de requête:**

```bash
curl -X GET "http://localhost:8000/api/invoices/match-suggestions?query=Tomate%20rouge&max_results=5&min_score=60"
```

**Réponse:**

```json
{
  "suggestions": [
    {
      "produit_id": 123,
      "produit_nom": "Tomates rouges en grappe",
      "categorie": "Fruits & Légumes",
      "prix_achat": 2.50,
      "prix_vente": 3.99,
      "barcode": "3245678901234",
      "score": 92.5,
      "match_type": "fuzzy_name"
    }
  ]
}
```

### Frontend

#### 1. Hook React (`frontend/src/hooks/useInvoiceImport.js`)

**Nouveau hook:** `useProductMatchSuggestions(query, options)`

Utilise React Query pour gérer les requêtes de suggestions:
- Cache automatique (1 minute)
- Pas de requête si `query` est vide
- Gestion d'erreur intégrée

**Exemple d'utilisation:**

```javascript
import { useProductMatchSuggestions } from '../hooks/useInvoiceImport.js';

function MyComponent() {
  const { data: suggestions, isLoading, isError } = useProductMatchSuggestions(
    "Tomate rouge",
    { maxResults: 5, minScore: 60.0 }
  );

  if (isLoading) return <div>Chargement...</div>;
  if (isError) return <div>Erreur</div>;

  return (
    <ul>
      {suggestions.map(s => (
        <li key={s.produit_id}>{s.produit_nom} - {s.score}%</li>
      ))}
    </ul>
  );
}
```

#### 2. Composant ProductMatchSuggestions (`frontend/src/features/invoices/components/ProductMatchSuggestions.jsx`)

Composant UI réutilisable qui affiche une dropdown de suggestions de matching.

**Props:**
- `productName`: Nom du produit à rechercher
- `onSelectMatch`: Callback quand un produit est sélectionné
- `onCreateNew`: Callback pour créer un nouveau produit
- `className`: Classes CSS additionnelles

**Fonctionnalités:**
- Dropdown avec liste de suggestions
- Badges de score avec couleur selon la confiance:
  - Vert foncé (≥90%): Très bonne correspondance
  - Vert clair (≥75%): Bonne correspondance
  - Jaune (≥60%): Correspondance acceptable
  - Gris (<60%): Faible correspondance
- Affichage des détails produit (catégorie, prix, EAN)
- Bouton pour créer un nouveau produit si aucune suggestion ne convient
- Fermeture automatique en cliquant en dehors

#### 3. Intégration dans InvoiceLinesEditor

Le composant `ProductMatchSuggestions` est intégré dans l'éditeur de lignes de facture:

- Apparaît automatiquement pour les lignes sans `produit_id`
- Se place dans la colonne "Actions" à gauche des boutons existants
- Sélectionner une suggestion lie automatiquement la ligne au produit
- Le bouton "Créer un nouveau produit" fonctionne comme le bouton "Créer" existant

## Installation

### Backend

1. Installer la dépendance rapidfuzz:

```bash
pip install -r requirements.txt
```

La ligne suivante a été ajoutée à `requirements.txt`:
```
rapidfuzz>=3.6.0
```

2. Redémarrer le serveur FastAPI:

```bash
uvicorn backend.main:app --reload
```

### Frontend

Aucune installation supplémentaire nécessaire. Les composants utilisent les dépendances React existantes.

## Utilisation

### Pour les utilisateurs finaux

1. **Importer une facture** via la page d'import
2. **Visualiser les lignes détectées** dans l'éditeur
3. Pour chaque ligne sans match automatique (pas de `produit_id`):
   - Cliquer sur le bouton **"Suggestions"**
   - Une dropdown s'ouvre avec les produits similaires du catalogue
   - Chaque suggestion affiche:
     - Le nom du produit
     - Le score de confiance en %
     - La catégorie
     - Le code EAN
     - Les prix d'achat et vente
4. **Sélectionner une suggestion** pour lier automatiquement la ligne
5. Si aucune suggestion ne convient, cliquer sur **"Créer un nouveau produit"**

### Scénarios d'utilisation

#### Scénario 1: Variations orthographiques

**Produit importé:** "Pommes Golden 1kg"
**Catalogue contient:** "Pomme Golden (1 kg)"
**Score:** 95%
→ Suggéré automatiquement

#### Scénario 2: Ordre des mots différent

**Produit importé:** "Lait demi-écrémé UHT"
**Catalogue contient:** "UHT Lait Demi-Écrémé"
**Score:** 88%
→ Suggéré automatiquement (token_sort_ratio ignore l'ordre)

#### Scénario 3: Abréviations

**Produit importé:** "Tomates cerises bio"
**Catalogue contient:** "Tomates cerises biologiques"
**Score:** 78%
→ Suggéré automatiquement

#### Scénario 4: Aucune correspondance

**Produit importé:** "Nouveau produit XYZ"
**Catalogue:** Rien de similaire
**Résultat:** Aucune suggestion
→ L'utilisateur peut créer un nouveau produit

## Configuration

### Seuils de score recommandés

- **Auto-matching (backend automatique):** ≥75%
  - Utilisé pour le matching automatique lors de l'import
  - Évite les faux positifs

- **Suggestions UI (frontend):** ≥60%
  - Affiché à l'utilisateur pour validation manuelle
  - Plus permissif car l'utilisateur valide

### Personnalisation

Pour ajuster les seuils, modifier les paramètres dans:

**Backend:**
```python
# backend/services/product_matching.py
suggestions = get_fuzzy_product_matches(
    query,
    tenant_id=tenant_id,
    max_results=5,      # Nombre de suggestions
    min_score=60.0,     # Score minimum
)
```

**Frontend:**
```javascript
// frontend/src/hooks/useInvoiceImport.js
const { data: suggestions } = useProductMatchSuggestions(
  productName,
  {
    maxResults: 5,   // Nombre de suggestions
    minScore: 60.0   // Score minimum
  }
);
```

## Performance

### Optimisations implémentées

1. **Cache React Query (frontend):**
   - Les suggestions sont cachées pendant 1 minute
   - Évite les requêtes répétées pour le même produit

2. **Recherche à la demande:**
   - Les suggestions ne sont chargées que lorsque l'utilisateur clique sur "Suggestions"
   - Paramètre `enabled` dans le hook

3. **Index PostgreSQL:**
   - Utiliser un index sur la colonne `nom` de la table `produits`:
   ```sql
   CREATE INDEX idx_produits_nom ON produits(nom);
   ```

4. **Extension pg_trgm (optionnel mais recommandé):**
   - Pour des performances optimales avec PostgreSQL:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE INDEX idx_produits_nom_trgm ON produits USING gin(nom gin_trgm_ops);
   ```

### Considérations de scalabilité

- **Catalogue < 10 000 produits:** Performances excellentes sans optimisation
- **Catalogue 10 000 - 50 000 produits:** Recommandé d'ajouter l'extension pg_trgm
- **Catalogue > 50 000 produits:** Considérer un service de recherche dédié (Elasticsearch, MeiliSearch)

## Tests

### Test manuel - Backend

```python
# Depuis un shell Python
from backend.services import product_matching

# Test 1: Recherche simple
suggestions = product_matching.get_fuzzy_product_matches(
    "Tomate",
    tenant_id=1,
    max_results=3,
    min_score=50.0
)
print(suggestions)

# Test 2: Nom complet avec variations
suggestions = product_matching.get_fuzzy_product_matches(
    "Lait demi ecreme",  # Sans accent
    tenant_id=1
)
print(suggestions)

# Test 3: Meilleur match unique
best = product_matching.get_best_product_match(
    "Pomme Golden",
    tenant_id=1,
    min_score=75.0
)
print(best)
```

### Test manuel - API

```bash
# Test avec curl
curl -X GET "http://localhost:8000/api/invoices/match-suggestions?query=Tomate&max_results=3&min_score=60"

# Test avec httpie
http GET "http://localhost:8000/api/invoices/match-suggestions" \
  query=="Tomate rouge" \
  max_results==5 \
  min_score==60
```

### Test manuel - Frontend

1. Ouvrir la page d'import de factures
2. Uploader une facture avec des produits non-matchés
3. Dans l'éditeur de lignes, cliquer sur "Suggestions" pour une ligne
4. Vérifier que la dropdown s'ouvre avec les suggestions
5. Vérifier les badges de score avec les bonnes couleurs
6. Sélectionner une suggestion et vérifier que la ligne est liée

## Dépannage

### Problème: Aucune suggestion affichée

**Causes possibles:**
1. Le catalogue est vide
2. Le score minimum est trop élevé
3. Le nom du produit est trop différent des produits du catalogue

**Solutions:**
1. Vérifier que la table `produits` contient des données
2. Réduire le `min_score` à 40-50
3. Essayer avec un nom de produit plus générique

### Problème: Suggestions non pertinentes

**Cause:** Le score minimum est trop bas

**Solution:** Augmenter le `min_score` à 70-80

### Problème: Performances lentes

**Causes possibles:**
1. Catalogue très large (>50k produits)
2. Pas d'index sur la colonne `nom`

**Solutions:**
1. Ajouter l'extension pg_trgm PostgreSQL
2. Créer des index appropriés
3. Implémenter une recherche en cache côté serveur

### Problème: Erreur "rapidfuzz not found"

**Solution:**
```bash
pip install rapidfuzz>=3.6.0
```

## Améliorations futures

### Court terme

1. **Auto-matching au niveau de l'import:**
   - Lier automatiquement les produits avec score >85%
   - Marquer les lignes auto-matchées pour revue

2. **Apprentissage des choix utilisateur:**
   - Stocker les mappings validés par l'utilisateur
   - Prioriser ces mappings dans les futures suggestions

### Moyen terme

3. **Matching multi-critères:**
   - Combiner nom, catégorie, prix, fournisseur
   - Score composite plus précis

4. **Synonymes et variations:**
   - Base de données de synonymes (bio/biologique, kg/kilo)
   - Normalisation automatique des abréviations

5. **Interface d'apprentissage:**
   - Page pour valider/rejeter les suggestions en batch
   - Feedback pour améliorer l'algorithme

### Long terme

6. **Machine Learning:**
   - Modèle entraîné sur l'historique des imports
   - Suggestions contextuelles (fournisseur, saison)

7. **Service de recherche dédié:**
   - Migration vers Elasticsearch ou MeiliSearch
   - Recherche typo-tolérante avancée
   - Filtres facettés

## Fichiers modifiés/créés

### Backend
- ✅ `requirements.txt` - Ajout de rapidfuzz>=3.6.0
- ✅ `backend/services/product_matching.py` - Nouveau service de fuzzy matching
- ✅ `backend/api/invoices.py` - Nouveau endpoint GET /invoices/match-suggestions

### Frontend
- ✅ `frontend/src/api/client.js` - Nouvelle fonction fetchProductMatchSuggestions
- ✅ `frontend/src/hooks/useInvoiceImport.js` - Nouveau hook useProductMatchSuggestions
- ✅ `frontend/src/features/invoices/components/ProductMatchSuggestions.jsx` - Nouveau composant
- ✅ `frontend/src/features/invoices/components/InvoiceLinesEditor.jsx` - Intégration du composant
- ✅ `frontend/src/features/invoices/components/index.js` - Export du nouveau composant

### Documentation
- ✅ `docs/FUZZY_MATCHING_IMPLEMENTATION.md` - Ce fichier

## Support

Pour toute question ou problème:
1. Vérifier cette documentation
2. Consulter les logs backend pour les erreurs API
3. Inspecter la console du navigateur pour les erreurs frontend
4. Vérifier que rapidfuzz est installé: `pip list | grep rapidfuzz`

## Licence

Même licence que le projet principal.
