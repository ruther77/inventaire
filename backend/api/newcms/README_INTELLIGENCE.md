# NewCMS Intelligence Module - Documentation Technique

## Architecture

Le module Intelligence agrège les données des différents modules IA existants pour fournir une vue d'ensemble unifiée et des recommandations actionnables.

### Structure

```
backend/api/newcms/
├── __init__.py
├── intelligence.py          # Module Intelligence (NOUVEAU)
├── finance.py              # Finance Overview & Reconciliation
├── cockpit.py              # Morning Brief
└── operations.py           # Opérations
```

### Modules Core Utilisés

Le module Intelligence s'appuie sur les modules core existants :

```python
core/finance/
├── inventory_intelligence.py    # EOQ, Safety Stock, Reorder Points, ABC-XYZ
├── forecasting.py              # Sales, Stock, Cash Flow, Price Forecasting
├── anomaly_detection.py        # Détection anomalies financières
├── supplier_scoring.py         # Scoring fournisseurs
└── margin_calculator.py        # Calcul marges PAMP
```

### Endpoints Backend Utilisés

Les endpoints suivants sont appelés en interne :

- `/inventory-intelligence/*` - Intelligence inventaire
- `/forecasting/*` - Prévisions
- `/anomaly-detection/*` - Anomalies
- `/supplier-scoring/*` - Scoring fournisseurs
- `/margins/*` - Marges

## Endpoints Intelligence

### 1. GET `/api/newcms/intelligence/overview`

**Vue d'ensemble complète** agrégant :
- Score de santé global (0-10)
- Top 5 anomalies critiques
- Prévisions clés (ruptures 7j, cash 30j)
- Scoring fournisseurs (top 5 + bottom 5)
- Recommandations IA actionnables (max 10)

**Calculs** :
- Score global = 30% stock + 30% cash + 20% anomalies + 20% marges
- Grade : A (9-10), B (7-9), C (5-7), D (3-5), F (<3)

### 2. GET `/api/newcms/intelligence/recommendations`

**Liste des recommandations** avec filtres :
- `priority`: critical, high, medium, low
- `type`: reorder_stock, change_supplier, adjust_price, reduce_stock, optimize_margin, etc.
- `limit`: max 100

### 3. POST `/api/newcms/intelligence/recommendations/{id}/apply`

**Application d'une recommandation** :
- Exécute l'action définie dans le payload
- Paramètre `action_index` pour sélectionner l'action (0 par défaut)
- Retourne le résultat de l'exécution

**Note** : En production, ceci devrait appeler les vrais endpoints backend. Actuellement en mode simulation.

### 4. GET `/api/newcms/intelligence/health-score`

Score de santé uniquement (sans les autres données).

### 5. GET `/api/newcms/intelligence/metrics/summary`

Métriques résumées pour affichage dashboard.

## Score de Santé - Algorithme Détaillé

### Score Stock (30% du total)

```python
# Requête SQL
WITH stock_metrics AS (
    SELECT
        COUNT(*) as total_products,
        SUM(CASE WHEN stock_actuel <= 0 THEN 1 ELSE 0 END) as stockout_count,
        SUM(CASE WHEN stock_actuel > avg_consumption_90d THEN 1 ELSE 0 END) as overstock_count
    FROM produits
)
# Calcul
stock_score = 10.0 * (1 - (stockout_count + overstock_count) / (total_products * 2))
```

**Facteurs** :
- Produits en rupture (-0.5 par produit)
- Produits en surstock (-0.5 par produit)
- Rotation lente (-0.3 par produit)

### Score Cash (30% du total)

```python
# Requête SQL (finance_transactions - entity_id)
WITH cash_metrics AS (
    SELECT
        SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) as inflows,
        SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END) as outflows
    FROM finance_transactions
    WHERE date_operation >= CURRENT_DATE - INTERVAL '30 days'
)
# Calcul
ratio = inflows / outflows
if ratio >= 1.2: cash_score = 10.0
elif ratio >= 1.0: cash_score = 7.0
elif ratio >= 0.8: cash_score = 5.0
else: cash_score = 3.0
```

**Facteurs** :
- Ratio entrées/sorties
- Solde de trésorerie actuel
- Prévisions de trésorerie négative

### Score Anomalies (20% du total)

```python
# Requête SQL
SELECT
    COUNT(*) as total,
    SUM(CASE
        WHEN severity = 'critical' THEN 3
        WHEN severity = 'high' THEN 2
        WHEN severity = 'medium' THEN 1
        ELSE 0
    END) as severity_weight
FROM detected_anomalies
WHERE resolved = false AND detected_at >= CURRENT_DATE - 30

# Calcul
anomaly_score = 10.0 - min(10.0, severity_weight / 5)
```

**Facteurs** :
- Nombre d'anomalies non résolues
- Sévérité (critical=3, high=2, medium=1, low=0)
- Ancienneté (poids croissant avec le temps)

### Score Marges (20% du total)

```python
# Requête SQL
WITH margin_metrics AS (
    SELECT
        AVG((prix_vente - prix_achat) / NULLIF(prix_vente, 0) * 100) as avg_margin_pct,
        SUM(CASE WHEN prix_vente < prix_achat THEN 1 ELSE 0 END) as negative_margin_count
    FROM produits
    WHERE actif = true AND prix_vente > 0
)
# Calcul
if avg_margin_pct >= 30: base_score = 10.0
elif avg_margin_pct >= 20: base_score = 8.0
elif avg_margin_pct >= 15: base_score = 6.0
elif avg_margin_pct >= 10: base_score = 4.0
else: base_score = 2.0

margin_score = base_score - (negative_margin_count * 0.5)
```

**Facteurs** :
- Marge brute moyenne
- Nombre de produits avec marge négative (-0.5 par produit)
- Tendance des marges (amélioration/détérioration)

## Recommandations - Types et Actions

### 1. REORDER_STOCK (critical/high)

**Condition** : `stock_actuel / avg_daily <= 10 jours`

**Calculs** :
```python
# EOQ (Economic Order Quantity)
annual_demand = avg_daily * 365
eoq = sqrt((2 * annual_demand * ordering_cost) / (unit_cost * holding_cost_rate))

# Ajustements
adjusted_eoq = min(max(eoq, supplier_moq), max_order_qty)
```

**Actions** :
- Commander maintenant : `POST /api/orders/create` avec payload prêt

**Payload** :
```json
{
  "product_id": 123,
  "product_name": "Produit XYZ",
  "quantity": 50,
  "estimated_cost": 250.0
}
```

### 2. REDUCE_STOCK (medium)

**Condition** : `consumption_90d == 0 AND stock_actuel > 5`

**Actions** :
- Créer promotion : `POST /api/promotions/create` (discount 20%, 14j)
- Retourner au fournisseur : `POST /api/returns/create`

### 3. OPTIMIZE_MARGIN (medium/high)

**Condition** : `margin_pct < 15%` (seuil configurable)

**Calculs** :
```python
target_margin = 20.0  # %
new_price = prix_achat / (1 - target_margin / 100)
price_increase = new_price - prix_vente
```

**Actions** :
- Ajuster le prix : `POST /api/products/update-price`

### 4. CHANGE_SUPPLIER (high/medium)

**Condition** : `supplier_score < 5.0`

**Actions** :
- Voir alternatives : `GET /api/suppliers/alternatives`
- Négocier conditions : `POST /api/suppliers/negotiate`

### 5. IMPROVE_CASHFLOW (high)

**Condition** : Prévisions cash flow négatives dans les 30j

**Actions** :
- Retarder paiements : `POST /api/payments/reschedule`
- Accélérer recouvrements : `POST /api/invoices/send-reminders`

### 6. RESOLVE_ANOMALY (critical/high)

**Condition** : Anomalies non résolues de type critical/high

**Actions** :
- Investiguer : `GET /api/anomaly-detection/details/{id}`
- Marquer résolu : `POST /api/anomaly-detection/resolve/{id}`

## Conventions de Développement

### Tenant Mapping

Le tenant intelligence (4) accède aux données d'autres tenants :

```python
def _get_effective_tenant(tenant_id: int, data_type: str) -> int:
    if tenant_id != 4:
        return tenant_id

    if data_type in ["product", "inventory"]:
        return 1  # Épicerie
    elif data_type == "restaurant":
        return 2  # Restaurant
    elif data_type == "finance":
        return 2  # Entity ID pour finance_transactions
    else:
        return tenant_id
```

### Priorités

Ordre décroissant :
1. **CRITICAL** : Action immédiate requise (< 3j)
2. **HIGH** : Action importante (< 7j)
3. **MEDIUM** : Action recommandée (< 30j)
4. **LOW** : Optimisation possible

### Recommandations Actionnables

Chaque recommandation doit avoir :
- `id` : Unique, format `{type}_{entity_id}_{uuid_short}`
- `actions` : Liste d'actions avec payload complet
- `confirmation_required` : true pour actions critiques
- `impact_estimate` : Estimation chiffrée de l'impact

Exemple :
```python
RecommendationResponse(
    id=f"reorder_{product_id}_{uuid.uuid4().hex[:8]}",
    type=RecommendationType.REORDER_STOCK,
    priority=PriorityLevel.CRITICAL,
    title="Réapprovisionner Produit XYZ",
    description="Stock critique: 10 unités (3.2j)",
    impact_estimate="Éviter rupture, coût: 250€",
    confidence=0.9,
    actions=[
        ActionPayload(
            label="Commander maintenant",
            endpoint="/api/orders/create",
            method="POST",
            payload={
                "product_id": 123,
                "quantity": 50,
                "estimated_cost": 250.0
            },
            confirmation_required=True,
            confirmation_message="Commander 50 unités ?"
        )
    ],
    metadata={
        "product_id": 123,
        "current_stock": 10,
        "days_remaining": 3.2
    }
)
```

## Évolutions Futures

### Phase 1 - Actuellement Implémenté
- ✅ Score de santé global
- ✅ Top 5 anomalies critiques
- ✅ Prévisions clés (ruptures, cash)
- ✅ Scoring fournisseurs
- ✅ Recommandations avec payloads
- ⚠️  Application recommandations (simulé)

### Phase 2 - À Implémenter
- [ ] Historique des scores de santé (tendances)
- [ ] Application réelle des recommandations
- [ ] Feedback loop (efficacité des recommandations)
- [ ] Machine Learning pour prévisions
- [ ] Alertes temps réel (WebSocket)
- [ ] Recommandations personnalisées par utilisateur

### Phase 3 - Advanced
- [ ] Multi-tenant scoring comparé
- [ ] Benchmarking sectoriel
- [ ] Recommandations conditionnelles
- [ ] Optimisation automatique (auto-pilot)
- [ ] Intégration ERP externe
- [ ] Export rapports PDF/Excel

## Dépendances

### Modules Core
```python
from core.finance.inventory_intelligence import InventoryIntelligence
from core.finance.forecasting import ForecastingEngine
from core.finance.anomaly_detection import AnomalyDetector
from core.finance.supplier_scoring import SupplierScoreCalculator
from core.finance.margin_calculator import MarginCalculator
```

### Tables Database
- `produits`, `mouvements_stock` - Stock
- `finance_transactions` - Trésorerie
- `finance_invoices_supplier`, `finance_vendors` - Factures
- `detected_anomalies` - Anomalies persistées
- `restaurant_sales`, `restaurant_plats` - Ventes restaurant

### Configuration
Aucune configuration externe requise. Tous les seuils sont configurables via les paramètres des endpoints.

## Tests

Voir `TEST_ENDPOINTS.md` pour les exemples de tests manuels.

Pour les tests automatisés :
```bash
pytest backend/api/newcms/test_intelligence.py -v
```

## Monitoring

Métriques à surveiller :
- Temps de réponse `/overview` (cible: < 2s)
- Nombre de recommandations générées par jour
- Taux d'application des recommandations
- Précision des prévisions (MAPE)
- Faux positifs sur anomalies

## Support

Pour toute question :
- Documentation technique : Ce fichier
- Exemples d'utilisation : `TEST_ENDPOINTS.md`
- Schemas Pydantic : Voir code source `intelligence.py`
