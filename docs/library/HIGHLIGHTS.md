# Fonctions Remarquables - Highlights

Cette page présente une sélection de fonctions particulièrement intéressantes du catalogue.

---

## Top Fonctions Hautement Réutilisables

### Traitement de Données

#### `normalize_cart_rows` - Normalisation de Panier
**Fichier**: `core/cart_normalizer.py`
**Réutilisabilité**: High

Fonction pure qui normalise les données de panier shopping provenant de diverses sources.

**Pourquoi c'est remarquable** :
- Gestion robuste de multiples formats d'entrée
- Normalisation de champs avec alias (product_id, productId, pid → id)
- Conversion sécurisée de types (str → float, avec fallback)
- Valeurs par défaut intelligentes
- Aucune dépendance externe lourde

**Cas d'usage** : Idéale pour intégration avec multiples systèmes externes (POS, e-commerce, etc.)

---

#### `prepare_invoice_dataframe` - Préparation DataFrames Factures
**Fichier**: `backend/services/invoice_utils.py`
**Réutilisabilité**: High

Normalise et enrichit un DataFrame de lignes de facture avec calculs automatiques.

**Pourquoi c'est remarquable** :
- Calculs automatiques : marges, TVA, totaux
- Gestion des valeurs manquantes
- Alertes automatiques (marge insuffisante)
- Pipeline de transformation clair
- Bien typé avec Pandas

**Cas d'usage** : Processing batch de factures, rapports financiers

---

### Traitement PDF

#### `split_pdf_into_invoices` - Découpage PDF Multi-Factures
**Fichier**: `core/pdf_utils.py`
**Réutilisabilité**: High

Découpe un PDF contenant plusieurs factures en documents individuels.

**Pourquoi c'est remarquable** :
- Détection automatique des limites de factures (regex sur dates)
- Extraction metadata (ID, date facture)
- Aucune dépendance externe (pure PyPDF)
- Gestion robuste des edge cases
- Output structuré (dict avec bytes)

**Cas d'usage** : Import automatique de relevés multi-factures, archivage

---

#### `render_receipt_pdf` - Génération PDF Minimaliste
**Fichier**: `core/pdf_utils.py`
**Réutilisabilité**: High

Génère un PDF minimaliste à partir de lignes de texte, sans dépendance externe.

**Pourquoi c'est remarquable** :
- Pur Python - génération PDF from scratch
- Aucune librairie externe (pas de reportlab)
- Icône de boîte 3D en pur PostScript
- Lightweight (quelques Ko par PDF)
- Encodage sécurisé

**Cas d'usage** : Tickets de caisse, reçus simples, exports texte → PDF

---

### Cache & Performance

#### `get_redis_client` - Singleton Redis
**Fichier**: `backend/cache.py`
**Réutilisabilité**: High

Gestion singleton du client Redis avec pool de connexions.

**Pourquoi c'est remarquable** :
- Pattern singleton propre
- Pool de connexions réutilisable
- Health check intégré (ping)
- Fallback gracieux si Redis indisponible
- Thread-safe

**Cas d'usage** : Base pour tout système de cache applicatif

---

#### `@cached` - Décorateur de Cache
**Fichier**: `backend/cache.py`
**Réutilisabilité**: High

Décorateur universel pour mise en cache automatique (sync + async).

**Pourquoi c'est remarquable** :
- Support sync ET async
- Tenant-aware (clés par tenant)
- TTL configurable
- Fallback automatique si Redis down
- Sérialisation automatique JSON

**Cas d'usage** : Cacher n'importe quelle fonction lente (DB queries, API calls)

```python
@cached(ttl=300, prefix="dashboard")
async def get_dashboard_data(tenant_id: int):
    # Heavy computation
    return data
```

---

#### `cache_key` - Génération de Clés
**Fichier**: `backend/cache.py`
**Réutilisabilité**: High

Génère des clés de cache cohérentes et courtes à partir d'arguments variés.

**Pourquoi c'est remarquable** :
- Hash MD5 pour clés courtes
- Sérialisation JSON avec sort_keys
- Support tenant_id
- Préfixes personnalisables
- Déterministe (mêmes args → même clé)

---

### Formatage & Validation

#### `sanitize_receipt_text` - Nettoyage Texte
**Fichier**: `core/pdf_utils.py`
**Réutilisabilité**: High

Convertit du texte en ASCII pur pour PDF/impression.

**Pourquoi c'est remarquable** :
- Normalisation Unicode (NFKD)
- Conversion ASCII sûre
- Nettoyage espaces multiples
- Gestion symboles monétaires
- Robuste (gère None, objets)

**Cas d'usage** : Préparation texte pour PDF, ESC/POS, exports ASCII

---

#### `format_currency_line` - Formatage Monétaire
**Fichier**: `core/pdf_utils.py`
**Réutilisabilité**: High

Formate une ligne avec montant monétaire, arrondi correct.

**Pourquoi c'est remarquable** :
- Utilise Decimal pour précision
- Arrondi HALF_UP (standard bancaire)
- Formatage cohérent (2 décimales)
- Sanitization intégrée

**Cas d'usage** : Tickets de caisse, rapports financiers, exports

---

#### `format_quantity` - Formatage Quantités
**Fichier**: `core/pdf_utils.py`
**Réutilisabilité**: High

Formate des quantités en supprimant zéros inutiles.

**Pourquoi c'est remarquable** :
- Normalisation Decimal intelligente
- Suppression .0 pour entiers
- Suppression zéros trailing
- Fallback "0" sûr

**Exemples** :
- 5.000 → "5"
- 2.5 → "2.5"
- 0.0 → "0"

---

## Patterns Architecturaux Intéressants

### Pattern: Tenant-Aware Cache

**Fichier**: `backend/cache.py`

Le système de cache implémente un pattern tenant-aware élégant :

```python
# Clés de cache préfixées par tenant
key = f"{prefix}:tenant:{tenant_id}:{hash}"

# Invalidation par tenant
cache.invalidate_tenant(tenant_id)  # Invalide TOUT pour ce tenant
```

**Avantages** :
- Isolation complète entre tenants
- Invalidation sélective facile
- Sécurité multi-tenant

---

### Pattern: Decorator Factory

**Fichier**: `backend/cache.py`

Le décorateur `@cached` est une factory qui détecte automatiquement sync vs async :

```python
@cached(ttl=60)
async def async_func():
    pass

@cached(ttl=60)
def sync_func():
    pass
```

**Avantages** :
- API unique pour sync et async
- Détection automatique avec `asyncio.iscoroutinefunction`
- Zero boilerplate

---

### Pattern: Graceful Degradation

**Fichier**: `backend/cache.py`

Le cache dégrade gracieusement si Redis est indisponible :

```python
client = get_redis_client()
if client is None:
    # Redis down → exécute directement sans cache
    return await func(*args, **kwargs)
```

**Avantages** :
- Application continue de fonctionner
- Pas de crash si Redis down
- Logging pour alertes

---

### Pattern: Pipeline Transformation

**Fichier**: `backend/services/invoice_utils.py`

Transformation DataFrame en pipeline clair :

```python
# 1. Normaliser colonnes
# 2. Remplir valeurs manquantes
# 3. Calculer champs dérivés
# 4. Ajouter alertes
```

**Avantages** :
- Lisibilité
- Facile à debugger
- Extensible

---

## API Endpoints Remarquables

### `POST /finance/import/bank-statement`
**Fichier**: `backend/api/finance.py`

Import intelligent de relevés bancaires avec déduplication automatique.

**Remarquable car** :
- Upload fichier CSV/Excel
- Détection automatique format
- Parsing intelligent
- Déduplication sur hash
- Categorisation automatique

---

### `GET /cockpit/consolidated-kpis`
**Fichier**: `backend/api/newcms/cockpit.py`

KPIs consolidés en temps réel pour dashboard.

**Remarquable car** :
- Agrégation multi-sources
- Cache intelligent (TTL court)
- Calculs optimisés
- Format prêt pour visualisation

---

### `POST /restaurant/ingredients/bulk-update`
**Fichier**: `backend/api/restaurant.py`

Mise à jour en masse des ingrédients.

**Remarquable car** :
- Validation batch
- Transaction atomique
- Rollback automatique sur erreur
- Audit trail intégré

---

## Fonctions Complexes Bien Gérées

### Gestion de Transactions Bancaires
**Fichier**: `backend/services/finance/transactions.py`

Fonctions de réconciliation bancaire avec :
- Machine à états
- Gestion conflits
- Audit complet
- Idempotence

---

### Forecasting Financier
**Fichier**: `core/finance/forecasting.py`

Prévisions basées sur historique avec :
- Détection saisonnalité
- Moyennes mobiles
- Prédictions linéaires
- Intervalles de confiance

---

### Détection d'Anomalies
**Fichier**: `core/finance/anomaly_detection.py`

ML-based anomaly detection :
- Z-score statistics
- Isolation Forest
- Threshold dynamiques
- Alerting automatique

---

## Middleware Innovant

### Performance Tracking
**Fichier**: `backend/middleware/performance.py`

Middleware qui track automatiquement :
- Temps de réponse
- Slow queries detection
- Memory usage
- N+1 queries detection

**Innovant car** : Détection automatique des anti-patterns en production

---

### Idempotency Middleware
**Fichier**: `backend/middleware/idempotency.py`

Implémente idempotence pour requêtes POST/PUT :
- Idempotency-Key header
- Cache des résultats
- Replay protection
- TTL configurable

**Innovant car** : Idempotence automatique sans modifier les handlers

---

### Request Context
**Fichier**: `backend/middleware/request_context.py`

Context vars pour traçabilité :
- Request ID propagation
- User context
- Tenant context
- Logging enrichi

**Innovant car** : Context propagation async-safe (contextvars)

---

## Algorithmes Intéressants

### ABC Analysis (Inventaire)
**Fichier**: `core/inventory_classification.py`

Classification ABC automatique des produits :
- Calcul Pareto (80/20)
- Catégorisation A/B/C
- Scoring multi-critères

---

### Fuzzy Matching Produits
**Fichier**: `backend/services/product_matching.py`

Matching intelligent produits fournisseurs :
- Levenshtein distance
- Soundex français
- Synonymes métier
- Learning progressif

---

### Bank Statement Parsing
**Fichier**: `core/bank_import/parser.py`

Parsing multi-format avec :
- Détection automatique format
- Extraction regex patterns
- Validation IBAN
- Categorisation ML

---

## Utilitaires Génériques Extractibles

Ces fonctions sont candidates idéales pour extraction en bibliothèque :

### 📦 Package "pdf-utils"
- `split_pdf_into_invoices`
- `render_receipt_pdf`
- `sanitize_receipt_text`

### 📦 Package "cache-helpers"
- `get_redis_client`
- `@cached` decorator
- `cache_key`
- `CacheManager` class

### 📦 Package "data-normalizers"
- `normalize_cart_rows`
- `prepare_invoice_dataframe`
- Coercion functions

### 📦 Package "format-utils"
- `format_currency_line`
- `format_quantity`
- Currency formatters

---

## Conclusion

Le code contient de nombreuses **perles cachées** :
- Fonctions pures hautement réutilisables
- Patterns architecturaux élégants
- Algorithmes métier sophistiqués
- Middleware innovant

**Opportunité** : Extraire ces fonctions en bibliothèques open-source ou internes.

---

**Sources** :
- Catalogue complet : [FUNCTIONS_CATALOG.md](./FUNCTIONS_CATALOG.md)
- Haute réutilisabilité : [HIGH_REUSABILITY_FUNCTIONS.md](./HIGH_REUSABILITY_FUNCTIONS.md)
- Statistiques : [ADVANCED_STATISTICS.md](./ADVANCED_STATISTICS.md)
