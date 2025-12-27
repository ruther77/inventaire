# Quick Reference - Aide-Mémoire

Guide de référence rapide pour les fonctions Python les plus utiles.

---

## Fonctions Utilitaires Essentielles

### Cache & Performance

```python
# Obtenir client Redis (singleton)
from backend.cache import get_redis_client
redis = get_redis_client()  # Retourne None si Redis down

# Décorateur de cache
from backend.cache import cached

@cached(ttl=300, prefix="dashboard", tenant_aware=True)
async def get_stats(tenant_id: int):
    return expensive_computation()

# Gestionnaire de cache manuel
from backend.cache import CacheManager
cache = CacheManager(prefix="api")
cache.set("key", {"data": "value"}, ttl=60)
data = cache.get("key")
cache.invalidate_pattern("user:*")
cache.invalidate_tenant(tenant_id)

# Générer clé de cache
from backend.cache import cache_key
key = cache_key("users", "list", tenant_id=1, prefix="api")
# → "api:tenant:1:abc123..."
```

---

### PDF & Documents

```python
# Découper PDF multi-factures
from core.pdf_utils import split_pdf_into_invoices

pdf_bytes = open("factures.pdf", "rb").read()
invoices = split_pdf_into_invoices(pdf_bytes)
# → [{"invoice_id": "INV-001", "facture_date": "2024-01-15", "pdf_bytes": b"..."}, ...]

# Générer PDF minimaliste
from core.pdf_utils import render_receipt_pdf

lines = [
    "FACTURE",
    "Date: 2024-01-15",
    "Total: 150.00 EUR"
]
pdf_bytes = render_receipt_pdf(lines)

# Nettoyer texte pour PDF/ASCII
from core.pdf_utils import sanitize_receipt_text

text = sanitize_receipt_text("Café € 3,50")
# → "Cafe EUR 3.50"

# Formater ligne monétaire
from core.pdf_utils import format_currency_line
from decimal import Decimal

line = format_currency_line("Total HT", Decimal("150.00"))
# → "Total HT: 150.00 EUR"

# Formater quantité
from core.pdf_utils import format_quantity

qty = format_quantity(Decimal("5.000"))  # → "5"
qty = format_quantity(Decimal("2.5"))    # → "2.5"
```

---

### Normalisation de Données

```python
# Normaliser lignes de panier
from core.cart_normalizer import normalize_cart_rows

raw_cart = [
    {"productId": "123", "quantity": "5", "price": "10.50€"},
    {"code": "456", "qte": 2, "prix_unitaire": 8.0}
]

normalized = normalize_cart_rows(raw_cart)
# → [
#     {"id": 123, "nom": "Produit 123", "qty": 5.0, "prix_vente": 10.5, ...},
#     {"id": 456, "nom": "Produit 456", "qty": 2.0, "prix_vente": 8.0, ...}
# ]

# Préparer DataFrame factures
from backend.services.invoice_utils import prepare_invoice_dataframe
import pandas as pd

df = pd.DataFrame([
    {"product_id": 1, "qte_init": 10, "prix_achat": 5.0},
    {"product_id": 2, "qte_init": 5, "prix_achat": 12.0}
])

prepared_df = prepare_invoice_dataframe(df, margin_rate=0.3)
# → Ajoute colonnes: quantite_recue, prix_vente_minimum, montant_ht,
#                    montant_tva, montant_ttc, alerte_marge, etc.
```

---

## Patterns Courants

### Multi-Tenant

```python
# Récupérer tenant courant (dans endpoint FastAPI)
from backend.dependencies.tenant import get_current_tenant
from fastapi import Depends

@router.get("/data")
def get_data(tenant: Tenant = Depends(get_current_tenant)):
    # tenant.id, tenant.nom, etc.
    return query_tenant_data(tenant.id)
```

---

### Gestion d'Erreurs

```python
# Invalidation cache sur mutation
from backend.cache import invalidate_on_mutation

@invalidate_on_mutation(["catalog", "dashboard"])
async def create_product(tenant_id: int, ...):
    # Crée le produit
    # Cache automatiquement invalidé après
    pass
```

---

### Background Tasks

```python
# Tâche Celery
from backend.worker import app

@app.task(bind=True)
def process_invoice(self, invoice_id: int):
    # Traitement asynchrone
    pass

# Lancer tâche
from backend.tasks.invoices import process_invoice
task = process_invoice.delay(invoice_id=123)
```

---

## Requêtes Base de Données

### Exemples SQLAlchemy

```python
from sqlalchemy import text

# Requête simple
result = db.execute(
    text("SELECT * FROM products WHERE tenant_id = :tid"),
    {"tid": tenant_id}
).fetchall()

# Requête avec agrégation
stats = db.execute(
    text("""
        SELECT
            COUNT(*) as total,
            SUM(montant) as sum_montant
        FROM invoices
        WHERE tenant_id = :tid
    """),
    {"tid": tenant_id}
).fetchone()
```

---

## API Endpoints - Patterns Communs

### Pagination

```python
from fastapi import Query

@router.get("/items")
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant: Tenant = Depends(get_current_tenant)
):
    items = query_items(tenant.id, skip=skip, limit=limit)
    return {"items": items, "skip": skip, "limit": limit}
```

### Filtres

```python
from typing import Optional

@router.get("/products")
def search_products(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    tenant: Tenant = Depends(get_current_tenant)
):
    return search_with_filters(tenant.id, q, category, min_price, max_price)
```

### Validation Pydantic

```python
from pydantic import BaseModel, Field, validator

class ProductCreate(BaseModel):
    nom: str = Field(..., min_length=1, max_length=200)
    prix: float = Field(..., gt=0)
    tva: float = Field(20.0, ge=0, le=100)

    @validator('prix')
    def prix_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Prix doit être positif')
        return v

@router.post("/products")
def create_product(
    payload: ProductCreate,
    tenant: Tenant = Depends(get_current_tenant)
):
    return insert_product(tenant.id, payload.dict())
```

---

## Middleware Utiles

### Performance Tracking

```python
# Activé dans backend/main.py
# Logs automatiquement:
# - Temps de réponse
# - Slow queries
# - Memory usage
```

### Idempotency

```python
# Client envoie header:
# Idempotency-Key: <uuid>

# Si même clé envoyée 2x → même réponse (cache 24h)
```

### Request Context

```python
from backend.middleware.request_context import get_request_id

request_id = get_request_id()  # UUID unique par requête
# Propagé automatiquement dans logs
```

---

## Helpers Finance

### Calculs Courants

```python
from decimal import Decimal, ROUND_HALF_UP

def calculate_ttc(montant_ht: Decimal, tva_pct: Decimal) -> Decimal:
    montant_tva = (montant_ht * tva_pct / 100).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    return montant_ht + montant_tva

def calculate_marge(prix_vente: Decimal, prix_achat: Decimal) -> Decimal:
    if prix_achat == 0:
        return Decimal("0")
    return ((prix_vente - prix_achat) / prix_achat * 100).quantize(
        Decimal("0.01")
    )
```

---

## Helpers Restaurant

### Calculs Coûts

```python
# Coût matière d'un plat
def calculate_cout_matiere(ingredients: list[dict]) -> Decimal:
    """
    ingredients = [
        {"quantite": 0.2, "prix_unitaire": 5.0},  # 200g @ 5€/kg
        {"quantite": 1.0, "prix_unitaire": 2.0},  # 1 unité @ 2€
    ]
    """
    total = sum(
        Decimal(str(ing["quantite"])) * Decimal(str(ing["prix_unitaire"]))
        for ing in ingredients
    )
    return total.quantize(Decimal("0.01"))
```

---

## Aide-Mémoire Rapide

### Imports Essentiels

```python
# Cache
from backend.cache import (
    get_redis_client,
    cached,
    CacheManager,
    cache_key
)

# PDF
from core.pdf_utils import (
    split_pdf_into_invoices,
    render_receipt_pdf,
    sanitize_receipt_text,
    format_currency_line,
    format_quantity
)

# Normalisation
from core.cart_normalizer import normalize_cart_rows
from backend.services.invoice_utils import prepare_invoice_dataframe

# FastAPI
from fastapi import Depends, Query, Body, Path
from backend.dependencies.tenant import get_current_tenant, Tenant

# Database
from sqlalchemy import text

# Decimal
from decimal import Decimal, ROUND_HALF_UP
```

### Commandes Utiles

```bash
# Régénérer la documentation
python3 analyze_functions.py
python3 generate_report.py
python3 generate_stats.py

# Rechercher une fonction
grep -r "def ma_fonction" backend/ core/

# Compter les fonctions dans un fichier
grep -c "^def " backend/cache.py

# Trouver tous les endpoints GET
grep -r "@router.get" backend/api/

# Lister les imports d'un module
grep "^import\|^from" backend/cache.py
```

### Requêtes JSON Catalog

```bash
# Trouver fonction par nom
jq '.functions_by_category[][] | select(.name == "cached")' \
   python_functions_catalog.json

# Lister fonctions d'une catégorie
jq '.functions_by_category.Cache[].name' \
   python_functions_catalog.json

# Compter par réutilisabilité
jq '.functions_by_category[][] | .reusability' \
   python_functions_catalog.json | sort | uniq -c

# Trouver fonctions async
jq '.functions_by_category[][] | select(.is_async == true) | .name' \
   python_functions_catalog.json
```

---

## Références Complètes

- [INDEX.md](./INDEX.md) - Navigation complète
- [FUNCTIONS_CATALOG.md](./FUNCTIONS_CATALOG.md) - Toutes les fonctions
- [API_ENDPOINTS.md](./API_ENDPOINTS.md) - Tous les endpoints
- [HIGH_REUSABILITY_FUNCTIONS.md](./HIGH_REUSABILITY_FUNCTIONS.md) - Fonctions extractibles
- [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md) - Scripts Python

---

**Dernière mise à jour** : 2025-12-21
