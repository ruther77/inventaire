# Documentation du Code - Bibliothèque de Fonctions

Cette documentation a été générée automatiquement à partir de l'analyse du code source :
- **Backend Python** : `/backend` et `/core`
- **Frontend JavaScript/React** : `/frontend/src`

## Fichiers Disponibles

### 📊 Catalogues JSON

#### Backend Python
**[python_functions_catalog.json](./python_functions_catalog.json)** (1.2 MB)
- Catalogue exhaustif de 1,149 fonctions Python
- Inclut toutes les métadonnées : signatures, paramètres, types, dépendances, etc.
- Organisé par catégorie fonctionnelle
- Prêt pour l'analyse programmatique

#### Frontend JavaScript/React
**[javascript_functions_catalog.json](./javascript_functions_catalog.json)** (5.9 MB)
- Catalogue exhaustif de 1,824 fonctions/composants JavaScript/React
- Métadonnées : signatures, paramètres, dépendances, analyse de corps
- Catégorisation avancée (Components, Hooks, API, Utils, etc.)
- Score de réutilisabilité et complexité cyclomatique
- Prêt pour l'analyse et recherche programmatique

### 📖 Documentation Markdown

#### Backend Python

**[FUNCTIONS_CATALOG.md](./FUNCTIONS_CATALOG.md)** (561 KB, 22,666 lignes)
- Catalogue complet de 1,149 fonctions Python
- Organisé par catégorie et fichier source
- Signatures complètes avec types
- Descriptions et dépendances

**[API_ENDPOINTS.md](./API_ENDPOINTS.md)** (109 KB, 4,968 lignes)
- Documentation de 293 endpoints FastAPI
- Routes HTTP (GET, POST, PUT, DELETE, PATCH)
- Paramètres et types de retour

**[HIGH_REUSABILITY_FUNCTIONS.md](./HIGH_REUSABILITY_FUNCTIONS.md)** (139 KB, 8,587 lignes)
- 504 fonctions hautement réutilisables
- Fonctions pures, bien typées
- Candidates pour extraction en bibliothèque

#### Frontend JavaScript/React

**[JAVASCRIPT_CATALOG_SUMMARY.md](./JAVASCRIPT_CATALOG_SUMMARY.md)** (10 KB)
- Vue d'ensemble et statistiques JavaScript/React
- Répartition par catégories (Components, Hooks, API, Utils)
- Top 30 fonctions hautement réutilisables
- Recommandations de refactoring
- Méthodologie d'analyse détaillée

### 🔍 Outils de Recherche JavaScript

**[search_catalog.py](./search_catalog.py)** - Utilitaire CLI de recherche
- Recherche par nom, catégorie, type, fichier
- Filtres par réutilisabilité et complexité
- Affichage des statistiques
- Usage: `python3 search_catalog.py [command] [options]`

## Statistiques Globales

### Backend Python
```
Fonctions totales:         1,149
Fichiers analysés:           179
Catégories:                   22
Fonctions async:              83
Méthodes de classe:          407
Décorateurs:                 207
Haute réutilisabilité:       504
```

### Frontend JavaScript/React
```
Fonctions totales:         1,824
Fichiers analysés:           399
Catégories:                   34
React Components:            639
Custom Hooks:                299
Arrow Functions:             781
Haute réutilisabilité:       345 (19%)
Complexité High:             486 (27%)
```

## Distribution par Catégorie

### Backend Python (Top 15)

| Catégorie | Fonctions | Description |
|-----------|-----------|-------------|
| **API** | 293 | Endpoints FastAPI et routes HTTP |
| **Finance** | 265 | Logique financière et comptable |
| **General** | 114 | Fonctions générales et utilitaires |
| **Business Logic** | 96 | Logique métier des services |
| **Restaurant** | 77 | Gestion restaurant et menus |
| **Database** | 60 | Requêtes et accès aux données |
| **Middleware** | 50 | Middleware FastAPI |
| **Invoicing** | 32 | Traitement des factures |
| **Data Retrieval** | 31 | Récupération de données |
| **Document Processing** | 24 | Traitement de documents (PDF, etc.) |
| **Cache** | 22 | Gestion du cache Redis |
| **Background Tasks** | 18 | Tâches Celery asynchrones |
| **Data Creation** | 16 | Création de données |
| **Formatting** | 15 | Formatage et sérialisation |
| **Validation** | 8 | Validation de données |

### Frontend JavaScript/React (Top 15)

| Catégorie | Fonctions | Description |
|-----------|-----------|-------------|
| **Uncategorized** | 343 | Nécessite catégorisation manuelle |
| **Handlers/Events** | 275 | Event handlers React (onClick, onChange, etc.) |
| **Components/Generic** | 238 | Composants génériques non spécialisés |
| **Hooks/Data Fetching** | 231 | useQuery, useMutation, API hooks |
| **API/Read** | 131 | Fonctions fetch*, get*, search* |
| **Components/Layout** | 92 | Layouts, wrappers, shells |
| **Components/Containers** | 75 | Cards, panels, sections |
| **API/Client** | 61 | Configuration clients HTTP |
| **Hooks/State Management** | 46 | useState, useContext, reducers |
| **Components/UI Elements** | 39 | Buttons, badges, icons basiques |
| **Components/Data Display** | 38 | Tables, lists, grids |
| **Components/Feedback** | 36 | Toasts, alerts, notifications |
| **Components/Loading** | 36 | Skeletons, spinners, loaders |
| **Components/Overlays** | 27 | Modals, dialogs, drawers |
| **Components/Animation** | 19 | Transitions, animations |

## Méthodologie d'Analyse

### Backend Python

L'analyse a été effectuée avec les critères suivants :

#### Catégorisation
Les fonctions sont catégorisées selon :
1. Le chemin du fichier (api/, finance/, restaurant/, etc.)
2. Le nom de la fonction (get_, create_, validate_, etc.)
3. La docstring et le contenu

#### Niveau de Réutilisabilité

**High** (504 fonctions)
- Fonctions pures ou quasi-pures
- Paramètres bien typés avec annotations
- Peu de dépendances (≤ 5)
- Pas d'accès aux variables globales
- Moins de 50 lignes de code
- Facilement extractibles en bibliothèque

**Medium**
- Quelques dépendances externes
- Peut dépendre d'un état ou contexte
- Réutilisable avec adaptation

**Low**
- Nombreuses dépendances
- Fortement couplée au contexte
- Accès aux variables globales
- Difficile à extraire

### Frontend JavaScript/React

L'analyse utilise parsing RegEx et analyse de corps de fonction :

#### Catégorisation multi-critères
1. **Nom de la fonction**: Patterns (use*, handle*, fetch*, format*)
2. **Chemin du fichier**: components/, hooks/, utils/, api/
3. **Imports/dépendances**: react-query, axios, framer-motion
4. **Patterns dans le corps**: useState, useEffect, JSX, API calls
5. **Documentation JSDoc**: Description et paramètres

#### Score de réutilisabilité (0-11)
Facteurs évalués :
- Custom hook (+3 points)
- Dans utils/hooks/components/ui (+2-3 points)
- Exporté (+1 point)
- Peu de dépendances (+1 point)
- Faible complexité (+1 point)
- Nom générique (+1 point)
- Non spécifique à une feature (+1 point)

**High** (≥7): Très réutilisable - 345 fonctions (19%)
**Medium** (4-6): Réutilisable - 494 fonctions (27%)
**Low** (<4): Peu réutilisable - 985 fonctions (54%)

#### Complexité cyclomatique
Estimation basée sur :
- Structures conditionnelles (if, else, switch)
- Boucles (for, while)
- Opérateurs logiques (&&, ||)
- Ternaires (? :)
- Gestion d'erreurs (catch)

**Low** (<5): Simple - 683 fonctions (37%)
**Medium** (5-10): Modéré - 655 fonctions (36%)
**High** (>10): Complexe - 486 fonctions (27%)

### Métadonnées Extraites

Pour chaque fonction :
1. **Nom** : Identifiant de la fonction
2. **Fichier source** : Chemin relatif depuis la racine
3. **Numéro de ligne** : Position dans le fichier
4. **Signature complète** : Avec paramètres et types
5. **Catégorie fonctionnelle** : Classification automatique
6. **Description** : Extraite de la docstring
7. **Paramètres** : Liste avec noms, types et valeurs par défaut
8. **Type de retour** : Type annoté si présent
9. **Dépendances** : Imports utilisés
10. **Décorateurs** : Liste des décorateurs appliqués
11. **Marqueurs** :
    - `is_async` : Fonction asynchrone
    - `is_method` : Méthode de classe
    - `is_decorator` : Fonction décorateur
12. **Réutilisabilité** : High/Medium/Low

## Cas d'Usage

### 1. Rechercher une fonction spécifique
Utilisez le catalogue JSON ou recherchez dans FUNCTIONS_CATALOG.md

### 2. Trouver les fonctions réutilisables
Consultez HIGH_REUSABILITY_FUNCTIONS.md pour identifier les candidats à l'extraction

### 3. Documenter l'API
Utilisez API_ENDPOINTS.md pour la documentation des endpoints

### 4. Analyse programmatique
Parsez python_functions_catalog.json pour des analyses automatisées

### 5. Refactoring
Identifiez les fonctions avec low reusability pour amélioration

### 6. Migration
Trouvez les dépendances entre modules avant restructuration

## Exemples de Fonctions Hautement Réutilisables

### Utilitaires de Cache
- `get_redis_client()` - Gestion du pool Redis
- `cache_key()` - Génération de clés de cache
- `cached()` - Décorateur de mise en cache

### Traitement de Données
- `normalize_cart_rows()` - Normalisation de données panier
- `prepare_invoice_dataframe()` - Préparation DataFrames factures
- `sanitize_receipt_text()` - Nettoyage de texte

### Formatage
- `format_currency_line()` - Formatage monétaire
- `format_quantity()` - Formatage quantités
- `render_receipt_pdf()` - Génération PDF

### PDF et Documents
- `split_pdf_into_invoices()` - Découpage PDF multi-factures
- Fonctions d'extraction et parsing

## Scripts d'Analyse

### analyze_functions.py
Script d'analyse AST qui :
- Parse tous les fichiers Python
- Extrait les métadonnées complètes
- Catégorise automatiquement
- Évalue la réutilisabilité
- Génère le JSON complet

### generate_report.py
Générateur de rapports qui :
- Charge le catalogue JSON
- Génère les rapports Markdown
- Organise par catégorie et fichier
- Produit des vues spécialisées

## Maintenance

Cette documentation peut être régénérée à tout moment :

```bash
# Analyser le code et générer le JSON
python3 /home/ruuuzer/Documents/monprojet/analyze_functions.py

# Générer les rapports Markdown
python3 /home/ruuuzer/Documents/monprojet/generate_report.py
```

## Notes

- Les fonctions de test sont exclues de l'analyse
- Les répertoires `__pycache__` sont ignorés
- Les fonctions privées (préfixe `_`) sont incluses uniquement si ce sont des méthodes spéciales
- L'analyse est basée sur l'AST Python, donc robuste et précise
- Les dépendances sont détectées via l'analyse des imports et de l'AST

---

**Dernière génération** : 2025-12-21

**Base path** : `/home/ruuuzer/Documents/monprojet`

**Répertoires analysés** :
- `/home/ruuuzer/Documents/monprojet/backend` (118 fichiers)
- `/home/ruuuzer/Documents/monprojet/core` (61 fichiers)
