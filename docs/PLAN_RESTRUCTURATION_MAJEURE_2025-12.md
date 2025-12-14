# Plan de Restructuration Majeure

**Date**: 9 décembre 2025
**Version**: 1.0
**Objectif**: Transformer une application fragmentée en plateforme unifiée et cohérente

---

## Table des Matières

1. [Diagnostic et Vision](#1-diagnostic-et-vision)
2. [Nouvelle Architecture](#2-nouvelle-architecture)
3. [Phase 1 - Fondations BDD](#3-phase-1---fondations-bdd)
4. [Phase 2 - Core Services Avancés](#4-phase-2---core-services-avancés)
5. [Phase 3 - Backend API Unifié](#5-phase-3---backend-api-unifié)
6. [Phase 4 - Refonte UX/Navigation](#6-phase-4---refonte-uxnavigation)
7. [Phase 5 - Intelligence & Analytics](#7-phase-5---intelligence--analytics)
8. [Calendrier & Priorités](#8-calendrier--priorités)
9. [Métriques de Succès](#9-métriques-de-succès)

---

## 1. Diagnostic et Vision

### 1.1 État Actuel - Les Problèmes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIAGNOSTIC ACTUEL                                    │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │   ÉPICERIE    │     │  RESTAURANT   │     │  TRÉSORERIE   │
    │      HQ       │     │      HQ       │     │      HQ       │
    └───────────────┘     └───────────────┘     └───────────────┘
           │                     │                     │
           │    SILOS ISOLÉS     │    REDONDANCES      │
           │    PAS DE LIENS     │    UX INCOHÉRENTE   │
           │                     │                     │
    ┌──────┴──────┐       ┌──────┴──────┐       ┌──────┴──────┐
    │ Dashboard   │       │ Dashboard   │       │ Dashboard   │
    │ (similaire) │       │ (similaire) │       │ (similaire) │
    │ Inventaire  │       │ Recettes    │       │ Transactions│
    │ Catalogue   │       │ Coûts       │       │ Relevés     │
    │ Prix        │       │ Marges      │       │ Capital     │
    └─────────────┘       └─────────────┘       └─────────────┘
           │                     │                     │
           └─────────────────────┴─────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   INTELLIGENCE HQ     │
                    │   (Embryonnaire)      │
                    │   - Pas de données    │
                    │   - Modules dormants  │
                    │   - core/finance/*    │
                    │     non utilisés      │
                    └───────────────────────┘
```

### 1.2 Problèmes Identifiés

| Catégorie | Problème | Impact |
|-----------|----------|--------|
| **Navigation** | 4 HQ isolés, pas de fil conducteur | Utilisateur perdu |
| **Données** | Silos entre Épicerie/Restaurant/Finance | Analyses impossibles |
| **Redondance** | Dashboards similaires x3 | Maintenance difficile |
| **Core** | 12 modules finance dormants | Code mort |
| **UX** | Pas de scénario utilisateur | Clics sans but |
| **Liens** | Facture → Stock → Finance non liés | Valeur perdue |

### 1.3 Vision Cible

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VISION CIBLE                                         │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────┐
                    │      COCKPIT CENTRAL        │
                    │     (Vue 360° Business)     │
                    │                             │
                    │  ┌─────┐ ┌─────┐ ┌─────┐   │
                    │  │KPI  │ │Alert│ │Quick│   │
                    │  │Live │ │s    │ │Act  │   │
                    │  └─────┘ └─────┘ └─────┘   │
                    └────────────┬────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OPÉRATIONS    │    │    FINANCES     │    │  INTELLIGENCE   │
│                 │    │                 │    │                 │
│ • Épicerie      │───▶│ • Trésorerie    │◀───│ • Prévisions    │
│ • Restaurant    │    │ • Marges        │    │ • Anomalies     │
│ • Inventaire    │    │ • Cash Flow     │    │ • Insights      │
│ • Recettes      │    │ • Rapprochement │    │ • Scoring       │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │    DONNÉES UNIFIÉES   │
                    │                       │
                    │  Event Sourcing       │
                    │  Audit Trail          │
                    │  Multi-tenant sécurisé│
                    └───────────────────────┘
```

### 1.4 Principes Directeurs

1. **Un flux, pas des silos** : Facture → Stock → Finance → Insights
2. **Une action = une valeur** : Chaque clic apporte une information
3. **Intelligence proactive** : L'app propose, l'utilisateur décide
4. **Cohérence absolue** : Une seule façon de faire chaque chose
5. **Traçabilité totale** : Event sourcing pour tout

---

## 2. Nouvelle Architecture

### 2.1 Architecture Cible

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NOUVELLE ARCHITECTURE                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        COCKPIT (Dashboard Unifié)                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ KPI Live │  │ Alertes  │  │ Actions  │  │ Prévision│  │ Santé    │ │ │
│  │  │ Stream   │  │ Critiques│  │ Rapides  │  │ 7/30j    │  │ Globale  │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│         ┌───────────────────────────┼───────────────────────────┐           │
│         ▼                           ▼                           ▼           │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐       │
│  │ OPÉRATIONS  │           │  FINANCES   │           │INTELLIGENCE │       │
│  │             │           │             │           │             │       │
│  │ /operations │           │  /finances  │           │  /insights  │       │
│  │  /epicerie  │           │  /tresorerie│           │  /forecast  │       │
│  │  /restaurant│           │  /marges    │           │  /anomalies │       │
│  │  /inventory │           │  /rapproch  │           │  /scoring   │       │
│  └─────────────┘           └─────────────┘           └─────────────┘       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      COMPOSANTS PARTAGÉS                               │ │
│  │  DataTable │ Charts │ Forms │ Modals │ Filters │ Timeline │ Cards     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                              API Gateway
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API ROUTERS                                  │   │
│  │  /cockpit │ /operations │ /finances │ /intelligence │ /admin        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SERVICES MÉTIER                                 │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Operations   │  │  Finance     │  │ Intelligence │              │   │
│  │  │ Service      │  │  Service     │  │ Service      │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Rules Engine │  │ Forecast     │  │ Reconciliation│             │   │
│  │  │              │  │ Engine       │  │ Engine        │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      EVENT BUS                                       │   │
│  │  INVOICE_IMPORTED │ STOCK_MOVED │ EXPENSE_CATEGORIZED │ ALERT_FIRED │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE                                        │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   OPERATIONAL   │  │    FINANCIAL    │  │   ANALYTICS     │             │
│  │   TABLES        │  │    TABLES       │  │   TABLES        │             │
│  │                 │  │                 │  │                 │             │
│  │ • products      │  │ • transactions  │  │ • event_log     │             │
│  │ • inventory     │  │ • categories    │  │ • forecast_cache│             │
│  │ • invoices      │  │ • rules         │  │ • audit_trail   │             │
│  │ • recipes       │  │ • bank_accounts │  │ • analytics_axis│             │
│  │ • movements     │  │ • reconciliation│  │ • supplier_score│             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Nouvelle Structure des Dossiers

```
monprojet/
│
├── frontend/src/
│   ├── app/
│   │   ├── routes.tsx                 # Routes TypeScript
│   │   └── Layout.tsx                 # Layout unifié
│   │
│   ├── modules/                       # Remplace features/
│   │   ├── cockpit/                   # Dashboard central
│   │   │   ├── CockpitPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── KPIStream.tsx
│   │   │   │   ├── AlertsPanel.tsx
│   │   │   │   ├── QuickActions.tsx
│   │   │   │   └── HealthScore.tsx
│   │   │   └── hooks/
│   │   │
│   │   ├── operations/                # Épicerie + Restaurant + Inventory
│   │   │   ├── OperationsLayout.tsx
│   │   │   ├── epicerie/
│   │   │   ├── restaurant/
│   │   │   ├── inventory/
│   │   │   └── shared/                # Composants communs operations
│   │   │
│   │   ├── finances/                  # Trésorerie + Marges + Rapprochement
│   │   │   ├── FinancesLayout.tsx
│   │   │   ├── tresorerie/
│   │   │   ├── marges/
│   │   │   ├── rapprochement/
│   │   │   └── shared/
│   │   │
│   │   └── intelligence/              # Prévisions + Anomalies + Scoring
│   │       ├── IntelligenceLayout.tsx
│   │       ├── forecast/
│   │       ├── anomalies/
│   │       ├── scoring/
│   │       └── insights/
│   │
│   ├── shared/                        # Composants globaux
│   │   ├── components/
│   │   │   ├── DataTable/
│   │   │   ├── Charts/
│   │   │   ├── Forms/
│   │   │   └── Layout/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── types/
│   │
│   └── api/
│       └── client.ts                  # API client TypeScript
│
├── backend/
│   ├── api/
│   │   ├── cockpit.py                 # /cockpit/*
│   │   ├── operations.py              # /operations/*
│   │   ├── finances.py                # /finances/*
│   │   └── intelligence.py            # /intelligence/*
│   │
│   └── services/
│       ├── operations/
│       ├── finances/
│       └── intelligence/
│
└── core/
    ├── engines/                       # Moteurs actifs
    │   ├── rules_engine.py            # Catégorisation auto
    │   ├── forecast_engine.py         # Prévisions
    │   ├── reconciliation_engine.py   # Rapprochement bancaire
    │   └── scoring_engine.py          # Scoring fournisseurs
    │
    ├── services/                      # Services métier
    │   ├── inventory_intelligence.py
    │   ├── margin_calculator.py
    │   └── anomaly_detector.py
    │
    └── infrastructure/                # Infrastructure
        ├── event_bus.py
        ├── audit_trail.py
        └── data_repository.py
```

---

## 3. Phase 1 - Fondations BDD

### 3.1 Nouvelles Tables Requises

#### 3.1.1 Event Sourcing

```sql
-- Table centrale pour l'event sourcing
CREATE TABLE event_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    event_type VARCHAR(50) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,  -- 'invoice', 'stock', 'transaction'
    aggregate_id INTEGER NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Index pour requêtes fréquentes
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_event_log_tenant ON event_log(tenant_id);
CREATE INDEX idx_event_log_type ON event_log(event_type);
CREATE INDEX idx_event_log_aggregate ON event_log(aggregate_type, aggregate_id);
CREATE INDEX idx_event_log_created ON event_log(created_at DESC);

-- Types d'événements
COMMENT ON TABLE event_log IS 'Event types:
  INVOICE_IMPORTED, INVOICE_VALIDATED, INVOICE_PAID
  STOCK_RECEIVED, STOCK_CONSUMED, STOCK_ADJUSTED
  EXPENSE_CREATED, EXPENSE_CATEGORIZED, EXPENSE_RECONCILED
  PRICE_UPDATED, PRICE_ALERT_TRIGGERED
  FORECAST_GENERATED, ANOMALY_DETECTED
';
```

#### 3.1.2 Audit Trail

```sql
-- Piste d'audit complète
CREATE TABLE audit_trail (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    user_id INTEGER,
    user_ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_trail(tenant_id);
CREATE INDEX idx_audit_table ON audit_trail(table_name, record_id);
CREATE INDEX idx_audit_user ON audit_trail(user_id);
CREATE INDEX idx_audit_date ON audit_trail(created_at DESC);

-- Trigger automatique pour audit
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (tenant_id, table_name, record_id, action, new_data)
        VALUES (NEW.tenant_id, TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (tenant_id, table_name, record_id, action, old_data, new_data)
        VALUES (NEW.tenant_id, TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (tenant_id, table_name, record_id, action, old_data)
        VALUES (OLD.tenant_id, TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

#### 3.1.3 Financial Rules Engine

```sql
-- Règles de catégorisation financière
CREATE TABLE financial_rules (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    priority INTEGER DEFAULT 100,  -- Plus bas = plus prioritaire
    is_active BOOLEAN DEFAULT true,

    -- Conditions (JSONB pour flexibilité)
    conditions JSONB NOT NULL,
    /*
    Exemple conditions:
    {
      "vendor_pattern": "METRO.*",
      "amount_min": 100,
      "amount_max": 5000,
      "description_keywords": ["alimentaire", "frais"]
    }
    */

    -- Actions
    target_category_id INTEGER REFERENCES finance_categories(id),
    auto_validate BOOLEAN DEFAULT false,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.80,

    -- Stats d'apprentissage
    times_applied INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rules_tenant_active ON financial_rules(tenant_id, is_active, priority);

-- Historique des applications de règles
CREATE TABLE rule_applications (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES financial_rules(id),
    transaction_id INTEGER NOT NULL,
    confidence_score DECIMAL(3,2),
    was_confirmed BOOLEAN,
    user_feedback VARCHAR(20),  -- 'confirmed', 'rejected', 'modified'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.1.4 Comptabilité Analytique

```sql
-- Axes analytiques
CREATE TABLE analytic_axes (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    axis_type VARCHAR(50) NOT NULL,  -- 'entity', 'category', 'project', 'cost_center'
    parent_id INTEGER REFERENCES analytic_axes(id),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',

    UNIQUE(tenant_id, code)
);

-- Affectations analytiques
CREATE TABLE analytic_assignments (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'transaction', 'invoice_line', 'stock_movement'
    source_id INTEGER NOT NULL,
    axis_id INTEGER REFERENCES analytic_axes(id),
    amount DECIMAL(15,2) NOT NULL,
    percentage DECIMAL(5,2),  -- Pour ventilation

    UNIQUE(source_type, source_id, axis_id)
);

CREATE INDEX idx_analytic_source ON analytic_assignments(source_type, source_id);
CREATE INDEX idx_analytic_axis ON analytic_assignments(axis_id);
```

#### 3.1.5 Prévisions (Forecasting)

```sql
-- Cache des prévisions
CREATE TABLE forecast_cache (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    forecast_type VARCHAR(50) NOT NULL,  -- 'sales', 'cashflow', 'stock', 'price'
    target_entity VARCHAR(100),  -- product_id, category, global
    target_id INTEGER,

    -- Résultats
    forecast_date DATE NOT NULL,
    predicted_value DECIMAL(15,2),
    confidence_lower DECIMAL(15,2),
    confidence_upper DECIMAL(15,2),
    confidence_level DECIMAL(3,2) DEFAULT 0.95,

    -- Méthode utilisée
    model_type VARCHAR(50),  -- 'prophet', 'holt_winters', 'regression'
    model_params JSONB,

    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    UNIQUE(tenant_id, forecast_type, target_entity, target_id, forecast_date)
);

CREATE INDEX idx_forecast_lookup ON forecast_cache(tenant_id, forecast_type, target_entity);
CREATE INDEX idx_forecast_date ON forecast_cache(forecast_date);
```

#### 3.1.6 Scoring Fournisseurs

```sql
-- Scores fournisseurs
CREATE TABLE supplier_scores (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,  -- vendor_id

    -- Composantes du score
    price_volatility_score DECIMAL(3,2),  -- 0-1, bas = stable = bien
    delivery_reliability_score DECIMAL(3,2),  -- 0-1, haut = fiable
    invoice_accuracy_score DECIMAL(3,2),  -- 0-1, haut = précis
    stock_variance_score DECIMAL(3,2),  -- 0-1, bas = peu d'écarts
    payment_terms_score DECIMAL(3,2),  -- 0-1, haut = bonnes conditions

    -- Score global pondéré
    overall_score DECIMAL(3,2),
    score_trend VARCHAR(20),  -- 'improving', 'stable', 'declining'

    -- Données de calcul
    calculation_date DATE,
    data_points INTEGER,
    calculation_params JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, supplier_id, calculation_date)
);

-- Historique des scores
CREATE TABLE supplier_score_history (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    score_date DATE NOT NULL,
    overall_score DECIMAL(3,2),
    components JSONB,

    UNIQUE(tenant_id, supplier_id, score_date)
);
```

#### 3.1.7 Rapprochement Bancaire Avancé

```sql
-- Rapprochements bancaires
CREATE TABLE bank_reconciliations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    bank_statement_id INTEGER NOT NULL,

    -- Liens multiples (1 relevé = N factures possible)
    matched_items JSONB NOT NULL,
    /*
    [
      {"type": "invoice", "id": 123, "amount": 450.00, "match_score": 0.95},
      {"type": "invoice", "id": 124, "amount": 50.00, "match_score": 0.88}
    ]
    */

    -- Scoring du matching
    match_method VARCHAR(50),  -- 'exact', 'fuzzy_amount', 'fuzzy_date', 'vendor_alias'
    total_confidence DECIMAL(3,2),

    -- État
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'validated', 'rejected', 'partial'
    validated_by INTEGER REFERENCES users(id),
    validated_at TIMESTAMPTZ,

    -- Alertes
    has_discrepancy BOOLEAN DEFAULT false,
    discrepancy_amount DECIMAL(15,2),
    discrepancy_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alias fournisseurs pour matching
CREATE TABLE vendor_aliases (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    alias_pattern VARCHAR(200) NOT NULL,  -- Regex pattern
    source VARCHAR(50),  -- 'bank_lcl', 'bank_bnp', 'manual'
    confidence DECIMAL(3,2) DEFAULT 1.0,

    UNIQUE(tenant_id, alias_pattern)
);
```

#### 3.1.8 Calcul de Marges

```sql
-- Snapshots de marges
CREATE TABLE margin_snapshots (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'product', 'recipe', 'category', 'global'
    entity_id INTEGER,

    -- Coûts
    purchase_cost DECIMAL(15,2),  -- PAMP
    direct_cost DECIMAL(15,2),    -- Coût matière
    indirect_cost DECIMAL(15,2),  -- Charges indirectes proratisées
    total_cost DECIMAL(15,2),

    -- Revenus
    revenue DECIMAL(15,2),
    quantity_sold DECIMAL(10,2),

    -- Marges
    gross_margin DECIMAL(15,2),
    gross_margin_pct DECIMAL(5,2),
    operating_margin DECIMAL(15,2),
    operating_margin_pct DECIMAL(5,2),

    -- Pertes
    waste_value DECIMAL(15,2),
    waste_pct DECIMAL(5,2),

    -- TVA
    tva_rate DECIMAL(4,2),
    tva_amount DECIMAL(15,2),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, snapshot_date, entity_type, entity_id)
);
```

#### 3.1.9 Inventaire Intelligent

```sql
-- Paramètres de stock
CREATE TABLE inventory_intelligence (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,

    -- Stock de sécurité
    safety_stock DECIMAL(10,2),
    safety_stock_days INTEGER,

    -- Réapprovisionnement
    reorder_point DECIMAL(10,2),
    economic_order_quantity DECIMAL(10,2),  -- EOQ
    lead_time_days INTEGER,

    -- Rotation
    rotation_rate DECIMAL(6,2),  -- Turns per month
    days_of_stock DECIMAL(6,2),
    is_slow_moving BOOLEAN DEFAULT false,
    is_dead_stock BOOLEAN DEFAULT false,

    -- Prévisions
    predicted_stockout_date DATE,
    predicted_demand_30d DECIMAL(10,2),

    -- Dernière mise à jour
    last_calculated TIMESTAMPTZ,

    UNIQUE(tenant_id, product_id)
);

-- Alertes inventaire
CREATE TABLE inventory_alerts (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    /*
    Types: 'low_stock', 'stockout_imminent', 'dead_stock',
           'variance_detected', 'price_spike', 'demand_surge'
    */
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'critical'
    message TEXT,
    data JSONB,

    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Migration Alembic

```python
# alembic/versions/xxx_restructuration_majeure.py

def upgrade():
    # 1. Event sourcing
    op.execute("""
        CREATE TABLE event_log (...);
        CREATE INDEX idx_event_log_tenant ON event_log(tenant_id);
        -- ... autres index
    """)

    # 2. Audit trail
    op.execute("""
        CREATE TABLE audit_trail (...);
        CREATE OR REPLACE FUNCTION audit_trigger_func() ...;
    """)

    # 3. Appliquer triggers audit aux tables existantes
    for table in ['products', 'invoices', 'finance_transactions', 'inventory_items']:
        op.execute(f"""
            CREATE TRIGGER audit_trigger_{table}
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)

    # 4-9. Autres tables...
```

---

## 4. Phase 2 - Core Services Avancés

### 4.1 Activation des Modules Dormants

Les modules dans `core/finance/` existent mais ne sont pas utilisés. Plan d'activation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVATION MODULES CORE/FINANCE                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   EXISTANT (dormant) │ ──▶ │     REFACTORING      │ ──▶ │     ACTIF & TESTÉ    │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘

1. rules_engine.py          │ Connecter à BDD        │ /finance/classify/batch
   (catégorisation auto)    │ Ajouter scoring        │ UI: suggestions catégories

2. forecasting.py           │ Intégrer Prophet       │ /forecast/sales, /cashflow
   (prévisions)             │ Cache forecast_cache   │ UI: graphiques prévisions

3. anomaly_detection.py     │ Seuils configurables   │ /anomalies/detect
   (détection anomalies)    │ Alertes temps réel     │ UI: panel alertes

4. supplier_scoring.py      │ 5 composantes score    │ /suppliers/score/{id}
   (scoring fournisseurs)   │ Historique             │ UI: dashboard fournisseurs

5. bank_reconciliation.py   │ Matching multi-lignes  │ /bank/reconcile/auto
   (rapprochement avancé)   │ Alias fournisseurs     │ UI: interface matching

6. margin_calculator.py     │ PAMP + charges         │ /reports/margins
   (marges brutes/nettes)   │ Snapshots journaliers  │ UI: analyse marges

7. inventory_intelligence.py│ EOQ, safety stock      │ /inventory/intelligence
   (inventaire intelligent) │ Prévisions stockout    │ UI: recommandations
```

### 4.2 Implémentation Rules Engine

```python
# core/engines/rules_engine.py

from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class RuleCondition:
    vendor_pattern: Optional[str] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    description_keywords: Optional[List[str]] = None

@dataclass
class RuleMatch:
    rule_id: int
    category_id: int
    confidence: float
    reason: str

class FinancialRulesEngine:
    """Moteur de règles pour catégorisation automatique des transactions."""

    def __init__(self, tenant_id: int, db):
        self.tenant_id = tenant_id
        self.db = db
        self._rules = None

    async def load_rules(self):
        """Charge les règles actives triées par priorité."""
        self._rules = await self.db.fetch_all("""
            SELECT * FROM financial_rules
            WHERE tenant_id = $1 AND is_active = true
            ORDER BY priority ASC
        """, self.tenant_id)

    def apply(self, transaction: dict) -> Optional[RuleMatch]:
        """Applique les règles à une transaction."""
        for rule in self._rules:
            match = self._evaluate_rule(rule, transaction)
            if match and match.confidence >= rule['confidence_threshold']:
                return match
        return None

    def _evaluate_rule(self, rule: dict, txn: dict) -> Optional[RuleMatch]:
        """Évalue une règle contre une transaction."""
        conditions = rule['conditions']
        scores = []

        # Pattern vendeur
        if 'vendor_pattern' in conditions:
            if re.match(conditions['vendor_pattern'], txn.get('vendor', ''), re.I):
                scores.append(1.0)
            else:
                return None  # Condition obligatoire non remplie

        # Montant
        if 'amount_min' in conditions:
            if txn['amount'] < conditions['amount_min']:
                return None
            scores.append(0.8)

        if 'amount_max' in conditions:
            if txn['amount'] > conditions['amount_max']:
                return None
            scores.append(0.8)

        # Mots-clés description
        if 'description_keywords' in conditions:
            desc = txn.get('description', '').lower()
            matches = sum(1 for kw in conditions['description_keywords'] if kw.lower() in desc)
            if matches > 0:
                scores.append(matches / len(conditions['description_keywords']))

        if not scores:
            return None

        confidence = sum(scores) / len(scores)

        return RuleMatch(
            rule_id=rule['id'],
            category_id=rule['target_category_id'],
            confidence=confidence,
            reason=f"Règle '{rule['name']}' matchée avec {confidence:.0%} confiance"
        )

    async def batch_classify(self, transactions: List[dict]) -> List[dict]:
        """Classifie un batch de transactions."""
        await self.load_rules()

        results = []
        for txn in transactions:
            match = self.apply(txn)
            results.append({
                'transaction_id': txn['id'],
                'suggested_category_id': match.category_id if match else None,
                'confidence': match.confidence if match else 0,
                'reason': match.reason if match else 'Aucune règle applicable',
                'auto_validated': match and match.confidence >= 0.95
            })

        return results

    async def learn_from_feedback(self, rule_id: int, was_confirmed: bool):
        """Apprentissage à partir du feedback utilisateur."""
        if was_confirmed:
            await self.db.execute("""
                UPDATE financial_rules
                SET times_confirmed = times_confirmed + 1,
                    times_applied = times_applied + 1
                WHERE id = $1
            """, rule_id)
        else:
            await self.db.execute("""
                UPDATE financial_rules
                SET times_rejected = times_rejected + 1,
                    times_applied = times_applied + 1
                WHERE id = $1
            """, rule_id)
```

### 4.3 Implémentation Forecast Engine

```python
# core/engines/forecast_engine.py

from datetime import date, timedelta
from typing import List, Optional
import numpy as np

class ForecastEngine:
    """Moteur de prévisions pour ventes, cash flow, stock, prix."""

    MODELS = ['moving_average', 'holt_winters', 'regression']

    def __init__(self, tenant_id: int, db):
        self.tenant_id = tenant_id
        self.db = db

    async def forecast_sales(
        self,
        days_ahead: int = 30,
        product_id: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[dict]:
        """Prévision des ventes."""

        # Récupérer historique
        history = await self._get_sales_history(product_id, category)

        if len(history) < 30:
            return self._simple_forecast(history, days_ahead)

        # Utiliser Holt-Winters pour séries avec saisonnalité
        forecasts = self._holt_winters_forecast(history, days_ahead)

        # Sauvegarder en cache
        await self._cache_forecasts('sales', forecasts, product_id or category)

        return forecasts

    async def forecast_cashflow(self, days_ahead: int = 30) -> List[dict]:
        """Prévision de trésorerie."""

        # Entrées prévues (factures clients attendues)
        expected_inflows = await self._get_expected_inflows()

        # Sorties prévues (factures fournisseurs à payer)
        expected_outflows = await self._get_expected_outflows()

        # Solde actuel
        current_balance = await self._get_current_balance()

        forecasts = []
        running_balance = current_balance

        for i in range(days_ahead):
            forecast_date = date.today() + timedelta(days=i)
            day_inflows = sum(f['amount'] for f in expected_inflows if f['expected_date'] == forecast_date)
            day_outflows = sum(f['amount'] for f in expected_outflows if f['due_date'] == forecast_date)

            running_balance += day_inflows - day_outflows

            forecasts.append({
                'date': forecast_date,
                'predicted_balance': running_balance,
                'inflows': day_inflows,
                'outflows': day_outflows,
                'confidence': 0.85 - (i * 0.01)  # Confiance décroissante
            })

        return forecasts

    async def forecast_stockout(self, product_id: int) -> Optional[date]:
        """Prédit la date de rupture de stock."""

        # Stock actuel
        current_stock = await self._get_current_stock(product_id)

        # Consommation moyenne journalière (30 derniers jours)
        avg_daily_consumption = await self._get_avg_consumption(product_id)

        if avg_daily_consumption <= 0:
            return None  # Pas de consommation = pas de rupture

        days_until_stockout = current_stock / avg_daily_consumption

        return date.today() + timedelta(days=int(days_until_stockout))

    async def forecast_price(self, product_id: int, supplier_id: int) -> dict:
        """Prédit l'évolution du prix d'un produit."""

        # Historique des prix
        history = await self._get_price_history(product_id, supplier_id)

        if len(history) < 10:
            return {
                'trend': 'insufficient_data',
                'confidence': 0
            }

        # Calculer tendance
        prices = [h['price'] for h in history]
        trend = self._calculate_trend(prices)

        # Prédiction à 30 jours
        predicted_change = trend * 30

        return {
            'current_price': prices[-1],
            'predicted_price_30d': prices[-1] * (1 + predicted_change),
            'trend': 'up' if trend > 0.01 else 'down' if trend < -0.01 else 'stable',
            'monthly_change_pct': predicted_change * 100,
            'confidence': 0.7
        }

    def _holt_winters_forecast(self, history: List[dict], days_ahead: int) -> List[dict]:
        """Triple exponential smoothing."""
        values = np.array([h['value'] for h in history])

        # Paramètres Holt-Winters
        alpha = 0.3  # Level
        beta = 0.1   # Trend
        gamma = 0.2  # Seasonality
        season_length = 7  # Hebdomadaire

        # ... implémentation Holt-Winters

        return forecasts
```

### 4.4 Implémentation Margin Calculator

```python
# core/services/margin_calculator.py

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List

@dataclass
class MarginResult:
    entity_type: str
    entity_id: int

    # Coûts
    purchase_cost: Decimal
    direct_cost: Decimal
    indirect_cost: Decimal
    total_cost: Decimal

    # Revenus
    revenue: Decimal
    quantity: Decimal

    # Marges
    gross_margin: Decimal
    gross_margin_pct: Decimal
    operating_margin: Decimal
    operating_margin_pct: Decimal

    # Pertes
    waste_value: Decimal
    waste_pct: Decimal

class MarginCalculator:
    """Calcul automatique des marges brutes et opérationnelles."""

    def __init__(self, tenant_id: int, db):
        self.tenant_id = tenant_id
        self.db = db

    async def calculate_product_margin(
        self,
        product_id: int,
        period_start: date,
        period_end: date
    ) -> MarginResult:
        """Calcule la marge d'un produit sur une période."""

        # Prix d'achat moyen pondéré (PAMP)
        pamp = await self._calculate_pamp(product_id, period_end)

        # Quantité vendue
        sales = await self._get_sales(product_id, period_start, period_end)

        # Coûts directs (matière)
        direct_cost = pamp * sales['quantity']

        # Coûts indirects (% des charges fixes)
        indirect_cost = await self._prorate_indirect_costs(
            product_id, sales['revenue'], period_start, period_end
        )

        # Pertes (inventaire)
        waste = await self._get_waste_value(product_id, period_start, period_end)

        # Calculs
        total_cost = direct_cost + indirect_cost + waste
        gross_margin = sales['revenue'] - direct_cost
        operating_margin = sales['revenue'] - total_cost

        return MarginResult(
            entity_type='product',
            entity_id=product_id,
            purchase_cost=pamp,
            direct_cost=direct_cost,
            indirect_cost=indirect_cost,
            total_cost=total_cost,
            revenue=sales['revenue'],
            quantity=sales['quantity'],
            gross_margin=gross_margin,
            gross_margin_pct=(gross_margin / sales['revenue'] * 100) if sales['revenue'] else 0,
            operating_margin=operating_margin,
            operating_margin_pct=(operating_margin / sales['revenue'] * 100) if sales['revenue'] else 0,
            waste_value=waste,
            waste_pct=(waste / direct_cost * 100) if direct_cost else 0
        )

    async def calculate_recipe_margin(self, recipe_id: int) -> MarginResult:
        """Calcule la marge d'une recette restaurant."""

        # Coût matière de la recette
        ingredients = await self.db.fetch_all("""
            SELECT ri.product_id, ri.quantity, ri.unit,
                   p.name,
                   COALESCE(
                       (SELECT price FROM price_history
                        WHERE product_id = ri.product_id
                        ORDER BY date DESC LIMIT 1),
                       0
                   ) as unit_price
            FROM recipe_ingredients ri
            JOIN products p ON p.id = ri.product_id
            WHERE ri.recipe_id = $1
        """, recipe_id)

        direct_cost = sum(i['quantity'] * i['unit_price'] for i in ingredients)

        # Prix de vente
        recipe = await self.db.fetch_one("""
            SELECT name, selling_price, category FROM recipes WHERE id = $1
        """, recipe_id)

        revenue = recipe['selling_price']

        # Coûts indirects (main d'oeuvre ~30%, charges ~10%)
        labor_cost = revenue * Decimal('0.30')
        overhead_cost = revenue * Decimal('0.10')
        indirect_cost = labor_cost + overhead_cost

        gross_margin = revenue - direct_cost
        operating_margin = revenue - direct_cost - indirect_cost

        return MarginResult(
            entity_type='recipe',
            entity_id=recipe_id,
            purchase_cost=direct_cost,
            direct_cost=direct_cost,
            indirect_cost=indirect_cost,
            total_cost=direct_cost + indirect_cost,
            revenue=revenue,
            quantity=Decimal('1'),
            gross_margin=gross_margin,
            gross_margin_pct=(gross_margin / revenue * 100) if revenue else 0,
            operating_margin=operating_margin,
            operating_margin_pct=(operating_margin / revenue * 100) if revenue else 0,
            waste_value=Decimal('0'),
            waste_pct=Decimal('0')
        )

    async def _calculate_pamp(self, product_id: int, as_of: date) -> Decimal:
        """Prix d'Achat Moyen Pondéré."""
        result = await self.db.fetch_one("""
            SELECT
                SUM(quantity * unit_price) / NULLIF(SUM(quantity), 0) as pamp
            FROM invoice_lines il
            JOIN invoices i ON i.id = il.invoice_id
            WHERE il.product_id = $1
              AND i.date <= $2
              AND i.tenant_id = $3
        """, product_id, as_of, self.tenant_id)

        return result['pamp'] or Decimal('0')
```

---

## 5. Phase 3 - Backend API Unifié

### 5.1 Nouveaux Endpoints

```python
# backend/api/cockpit.py

from fastapi import APIRouter, Depends
from typing import List

router = APIRouter(prefix="/cockpit", tags=["Cockpit"])

@router.get("/overview")
async def get_cockpit_overview(tenant_id: int = Depends(get_tenant)):
    """
    Vue d'ensemble du cockpit avec tous les KPIs.

    Returns:
        - KPIs temps réel (CA jour, marge, stock critique)
        - Alertes actives (non acquittées)
        - Actions rapides disponibles
        - Score de santé global
        - Prévisions 7j résumées
    """
    pass

@router.get("/kpis/live")
async def get_live_kpis(tenant_id: int = Depends(get_tenant)):
    """Stream de KPIs en temps réel via SSE."""
    pass

@router.get("/alerts")
async def get_active_alerts(
    severity: str = None,
    limit: int = 20,
    tenant_id: int = Depends(get_tenant)
):
    """Alertes actives triées par sévérité."""
    pass

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, tenant_id: int = Depends(get_tenant)):
    """Acquitter une alerte."""
    pass


# backend/api/intelligence.py

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

@router.get("/forecast/sales")
async def forecast_sales(
    days: int = 30,
    product_id: int = None,
    category: str = None,
    tenant_id: int = Depends(get_tenant)
):
    """Prévision des ventes."""
    engine = ForecastEngine(tenant_id, db)
    return await engine.forecast_sales(days, product_id, category)

@router.get("/forecast/cashflow")
async def forecast_cashflow(days: int = 30, tenant_id: int = Depends(get_tenant)):
    """Prévision de trésorerie."""
    engine = ForecastEngine(tenant_id, db)
    return await engine.forecast_cashflow(days)

@router.get("/anomalies/detect")
async def detect_anomalies(
    scope: str = "all",  # 'transactions', 'prices', 'stock', 'all'
    tenant_id: int = Depends(get_tenant)
):
    """Détection d'anomalies."""
    pass

@router.get("/suppliers/{supplier_id}/score")
async def get_supplier_score(supplier_id: int, tenant_id: int = Depends(get_tenant)):
    """Score qualité d'un fournisseur."""
    pass


# backend/api/finances.py

router = APIRouter(prefix="/finances", tags=["Finances"])

@router.post("/transactions/classify/batch")
async def batch_classify_transactions(
    transaction_ids: List[int],
    tenant_id: int = Depends(get_tenant)
):
    """Classification batch avec le moteur de règles."""
    engine = FinancialRulesEngine(tenant_id, db)
    results = await engine.batch_classify(transactions)
    return results

@router.get("/reconciliation/auto")
async def auto_reconcile(
    statement_id: int = None,
    tenant_id: int = Depends(get_tenant)
):
    """Rapprochement bancaire automatique."""
    pass

@router.get("/margins/report")
async def get_margins_report(
    period: str = "month",  # 'day', 'week', 'month'
    entity_type: str = "global",  # 'product', 'recipe', 'category', 'global'
    tenant_id: int = Depends(get_tenant)
):
    """Rapport de marges."""
    pass

@router.get("/analytics/axes")
async def get_analytic_breakdown(
    axis: str,  # 'entity', 'category', 'project', 'cost_center'
    period_start: date,
    period_end: date,
    tenant_id: int = Depends(get_tenant)
):
    """Ventilation analytique."""
    pass
```

### 5.2 Event Bus

```python
# core/infrastructure/event_bus.py

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List
import asyncio

@dataclass
class Event:
    event_type: str
    aggregate_type: str
    aggregate_id: int
    payload: dict
    tenant_id: int
    created_at: datetime = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow()

class EventBus:
    """Bus d'événements pour event sourcing."""

    def __init__(self, db):
        self.db = db
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Enregistre un handler pour un type d'événement."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event):
        """Publie un événement."""
        # 1. Persister l'événement
        await self.db.execute("""
            INSERT INTO event_log (tenant_id, event_type, aggregate_type, aggregate_id, payload)
            VALUES ($1, $2, $3, $4, $5)
        """, event.tenant_id, event.event_type, event.aggregate_type,
           event.aggregate_id, event.payload)

        # 2. Notifier les handlers
        handlers = self._handlers.get(event.event_type, [])
        handlers += self._handlers.get('*', [])  # Handlers universels

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # Log erreur mais ne pas bloquer
                print(f"Error in event handler: {e}")

    async def replay(self, aggregate_type: str, aggregate_id: int) -> List[Event]:
        """Rejoue l'historique d'un agrégat."""
        rows = await self.db.fetch_all("""
            SELECT * FROM event_log
            WHERE aggregate_type = $1 AND aggregate_id = $2
            ORDER BY created_at ASC
        """, aggregate_type, aggregate_id)

        return [Event(**row) for row in rows]

# Événements prédéfinis
class Events:
    INVOICE_IMPORTED = 'INVOICE_IMPORTED'
    INVOICE_VALIDATED = 'INVOICE_VALIDATED'
    STOCK_RECEIVED = 'STOCK_RECEIVED'
    STOCK_CONSUMED = 'STOCK_CONSUMED'
    EXPENSE_CATEGORIZED = 'EXPENSE_CATEGORIZED'
    PRICE_UPDATED = 'PRICE_UPDATED'
    ANOMALY_DETECTED = 'ANOMALY_DETECTED'
    FORECAST_GENERATED = 'FORECAST_GENERATED'
    RECONCILIATION_COMPLETED = 'RECONCILIATION_COMPLETED'

# Usage
event_bus = EventBus(db)

# Enregistrer handlers
event_bus.subscribe(Events.INVOICE_IMPORTED, update_stock_handler)
event_bus.subscribe(Events.INVOICE_IMPORTED, update_price_history_handler)
event_bus.subscribe(Events.STOCK_CONSUMED, check_reorder_point_handler)
event_bus.subscribe('*', log_to_audit_trail_handler)

# Publier événement
await event_bus.publish(Event(
    event_type=Events.INVOICE_IMPORTED,
    aggregate_type='invoice',
    aggregate_id=invoice.id,
    payload={'vendor_id': invoice.vendor_id, 'total': invoice.total},
    tenant_id=tenant_id
))
```

---

## 6. Phase 4 - Refonte UX/Navigation

### 6.1 Nouvelle Structure de Navigation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NOUVELLE NAVIGATION                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                                      │
│  [Logo] [Tenant Selector] ──────────────────── [Alerts] [User] [Settings]   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────────────────────────────────┐
│                  │                                                          │
│  SIDEBAR         │  MAIN CONTENT                                            │
│                  │                                                          │
│  ┌────────────┐  │  ┌──────────────────────────────────────────────────┐   │
│  │ COCKPIT    │  │  │                                                   │   │
│  │ Vue 360°   │◀─┼──│  Dashboard/Page active                            │   │
│  └────────────┘  │  │                                                   │   │
│                  │  │                                                   │   │
│  ┌────────────┐  │  │                                                   │   │
│  │ OPÉRATIONS │  │  │                                                   │   │
│  │ ▼          │  │  └──────────────────────────────────────────────────┘   │
│  │  Épicerie  │  │                                                          │
│  │  Restaurant│  │  ┌──────────────────────────────────────────────────┐   │
│  │  Inventaire│  │  │  CONTEXTUAL PANEL (optionnel)                    │   │
│  │  Factures  │  │  │  - Détails item sélectionné                      │   │
│  └────────────┘  │  │  - Actions rapides                               │   │
│                  │  │  - Historique                                     │   │
│  ┌────────────┐  │  └──────────────────────────────────────────────────┘   │
│  │ FINANCES   │  │                                                          │
│  │ ▼          │  │                                                          │
│  │  Trésorerie│  │                                                          │
│  │  Marges    │  │                                                          │
│  │  Rapproch. │  │                                                          │
│  │  Analytique│  │                                                          │
│  └────────────┘  │                                                          │
│                  │                                                          │
│  ┌────────────┐  │                                                          │
│  │ INTELLIGENCE│ │                                                          │
│  │ ▼          │  │                                                          │
│  │  Prévisions│  │                                                          │
│  │  Anomalies │  │                                                          │
│  │  Scoring   │  │                                                          │
│  │  Insights  │  │                                                          │
│  └────────────┘  │                                                          │
│                  │                                                          │
│  ┌────────────┐  │                                                          │
│  │ PARAMÈTRES │  │                                                          │
│  └────────────┘  │                                                          │
│                  │                                                          │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

### 6.2 Nouvelles Routes

```typescript
// frontend/src/app/routes.tsx

const routes = [
  // COCKPIT - Vue d'ensemble
  {
    path: '/',
    element: <CockpitPage />,
    children: []
  },

  // OPÉRATIONS
  {
    path: '/operations',
    element: <OperationsLayout />,
    children: [
      // Épicerie
      { path: 'epicerie', element: <EpicerieDashboard /> },
      { path: 'epicerie/catalogue', element: <CataloguePage /> },
      { path: 'epicerie/commandes', element: <CommandesPage /> },

      // Restaurant
      { path: 'restaurant', element: <RestaurantDashboard /> },
      { path: 'restaurant/recettes', element: <RecettesPage /> },
      { path: 'restaurant/recettes/:id', element: <RecetteDetailPage /> },
      { path: 'restaurant/menus', element: <MenusPage /> },

      // Inventaire (unifié)
      { path: 'inventaire', element: <InventairePage /> },
      { path: 'inventaire/mouvements', element: <MouvementsPage /> },
      { path: 'inventaire/valorisation', element: <ValorisationPage /> },

      // Factures (unifié)
      { path: 'factures', element: <FacturesPage /> },
      { path: 'factures/import', element: <ImportPage /> },
      { path: 'factures/:id', element: <FactureDetailPage /> },
    ]
  },

  // FINANCES
  {
    path: '/finances',
    element: <FinancesLayout />,
    children: [
      // Trésorerie
      { path: 'tresorerie', element: <TresorerieDashboard /> },
      { path: 'tresorerie/transactions', element: <TransactionsPage /> },
      { path: 'tresorerie/releves', element: <RelevesPage /> },
      { path: 'tresorerie/rapprochement', element: <RapprochementPage /> },

      // Marges
      { path: 'marges', element: <MargesDashboard /> },
      { path: 'marges/produits', element: <MargesProduits /> },
      { path: 'marges/recettes', element: <MargesRecettes /> },

      // Analytique
      { path: 'analytique', element: <AnalytiquePage /> },
      { path: 'analytique/axes', element: <AxesPage /> },

      // Capital
      { path: 'capital', element: <CapitalPage /> },
    ]
  },

  // INTELLIGENCE
  {
    path: '/intelligence',
    element: <IntelligenceLayout />,
    children: [
      { path: '', element: <IntelligenceDashboard /> },
      { path: 'previsions', element: <PrevisionsPage /> },
      { path: 'previsions/ventes', element: <PrevisionsVentes /> },
      { path: 'previsions/tresorerie', element: <PrevisionsTresorerie /> },
      { path: 'previsions/stock', element: <PrevisionsStock /> },

      { path: 'anomalies', element: <AnomaliesPage /> },
      { path: 'scoring', element: <ScoringPage /> },
      { path: 'scoring/fournisseurs', element: <ScoringFournisseurs /> },

      { path: 'insights', element: <InsightsPage /> },
    ]
  },

  // PARAMÈTRES
  {
    path: '/parametres',
    element: <ParametresLayout />,
    children: [
      { path: 'regles', element: <ReglesPage /> },
      { path: 'categories', element: <CategoriesPage /> },
      { path: 'fournisseurs', element: <FournisseursPage /> },
      { path: 'utilisateurs', element: <UtilisateursPage /> },
      { path: 'tenant', element: <TenantPage /> },
    ]
  },
];
```

### 6.3 Cockpit - Dashboard Unifié

```typescript
// frontend/src/modules/cockpit/CockpitPage.tsx

export function CockpitPage() {
  const { data: overview } = useQuery(['cockpit', 'overview'], fetchCockpitOverview);
  const { data: alerts } = useQuery(['cockpit', 'alerts'], fetchActiveAlerts);

  return (
    <div className="cockpit-grid">
      {/* Row 1: KPIs principaux */}
      <div className="kpi-row">
        <KPICard
          title="CA Aujourd'hui"
          value={overview?.revenue_today}
          trend={overview?.revenue_trend}
          icon={<Euro />}
        />
        <KPICard
          title="Marge Brute"
          value={overview?.gross_margin_pct}
          trend={overview?.margin_trend}
          format="percent"
          icon={<TrendingUp />}
        />
        <KPICard
          title="Stock Critique"
          value={overview?.critical_stock_count}
          severity={overview?.critical_stock_count > 0 ? 'warning' : 'success'}
          icon={<Package />}
        />
        <KPICard
          title="Factures à Traiter"
          value={overview?.pending_invoices}
          icon={<FileText />}
        />
      </div>

      {/* Row 2: Alertes et Actions */}
      <div className="alerts-actions-row">
        <AlertsPanel alerts={alerts} />
        <QuickActionsPanel />
      </div>

      {/* Row 3: Graphiques */}
      <div className="charts-row">
        <CashFlowChart data={overview?.cashflow_7d} />
        <MarginTrendChart data={overview?.margin_trend_30d} />
      </div>

      {/* Row 4: Prévisions */}
      <div className="forecast-row">
        <ForecastSummary type="sales" horizon="7d" />
        <ForecastSummary type="stock" horizon="7d" />
      </div>

      {/* Row 5: Santé globale */}
      <div className="health-row">
        <HealthScoreGauge score={overview?.health_score} />
        <TopIssuesList issues={overview?.top_issues} />
      </div>
    </div>
  );
}
```

### 6.4 Scénarios Utilisateur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCÉNARIO 1: Import Facture → Stock → Finance             │
└─────────────────────────────────────────────────────────────────────────────┘

   1. Import Facture PDF                    2. Extraction automatique
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /operations/       │                 │  Core: invoice_     │
   │  factures/import    │ ───────────────▶│  extractor.py       │
   │                     │                 │                     │
   │  [Drop PDF]         │                 │  → Lignes extraites │
   │                     │                 │  → Produits matchés │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Mise à jour Stock                    4. Catégorisation Finance
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Event:             │                 │  Rules Engine:      │
   │  INVOICE_IMPORTED   │ ───────────────▶│  Catégorisation     │
   │                     │                 │  automatique        │
   │  → +Stock reçu      │                 │                     │
   │  → Prix MAJ         │                 │  → 94% confiance    │
   │  → Alerte si écart  │                 │  → Auto-validé      │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   5. Notification Cockpit                 6. Récapitulatif
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  AlertsPanel:       │                 │  Toast:             │
   │  "Facture METRO     │                 │  "✓ Facture METRO   │
   │   importée"         │                 │   traitée           │
   │                     │                 │   - 12 produits     │
   │  → Voir détail      │                 │   - Stock MAJ       │
   │  → Corriger         │                 │   - Catégorisé"     │
   └─────────────────────┘                 └─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│               SCÉNARIO 2: Alerte Stock → Commande → Prévision               │
└─────────────────────────────────────────────────────────────────────────────┘

   1. Alerte Cockpit                       2. Détail Produit
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  AlertsPanel:       │                 │  /operations/       │
   │  "⚠️ Stock critique │ ───────────────▶│  inventaire/        │
   │   Tomates: 2 jours" │                 │  produit/123        │
   │                     │                 │                     │
   │  [Voir]             │                 │  Stock: 5kg         │
   │                     │                 │  Conso moy: 2.5kg/j │
   └─────────────────────┘                 │  Rupture: 2 jours   │
                                           └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Recommandation EOQ                   4. Création Commande
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Intelligence:      │                 │  Action:            │
   │  "Commander 50kg    │ ───────────────▶│  Créer bon de       │
   │   chez METRO        │                 │  commande           │
   │   (EOQ optimal)"    │                 │                     │
   │                     │                 │  → Pré-rempli       │
   │  Score METRO: 8.5   │                 │  → Fournisseur      │
   │  Score SYSCO: 7.2   │                 │  → Quantité EOQ     │
   └─────────────────────┘                 └─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│            SCÉNARIO 3: Anomalie Prix → Investigation → Action               │
└─────────────────────────────────────────────────────────────────────────────┘

   1. Détection Anomalie                   2. Alerte Intelligence
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Core:              │                 │  /intelligence/     │
   │  anomaly_detection  │ ───────────────▶│  anomalies          │
   │                     │                 │                     │
   │  "Huile d'olive     │                 │  Anomalie #456      │
   │   +35% vs moyenne"  │                 │  Sévérité: HAUTE    │
   │                     │                 │  Impact: 450€/mois  │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Investigation                        4. Action Corrective
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Contexte:          │                 │  Options:           │
   │  - Historique prix  │                 │  □ Changer fournis. │
   │  - Comparatif       │ ───────────────▶│  □ Négocier prix    │
   │    fournisseurs     │                 │  □ Produit subst.   │
   │  - Impact marge     │                 │  □ Ignorer (motif)  │
   │                     │                 │                     │
   │  [Voir détail]      │                 │  [Appliquer]        │
   └─────────────────────┘                 └─────────────────────┘
```

---

## 7. Phase 5 - Intelligence & Analytics

### 7.1 Dashboard Intelligence

```typescript
// frontend/src/modules/intelligence/IntelligenceDashboard.tsx

export function IntelligenceDashboard() {
  return (
    <div className="intelligence-dashboard">
      {/* Score de santé global */}
      <HealthSection>
        <HealthGauge score={85} label="Santé Business" />
        <HealthBreakdown>
          <Metric label="Stock" score={78} />
          <Metric label="Marges" score={92} />
          <Metric label="Trésorerie" score={88} />
          <Metric label="Fournisseurs" score={82} />
        </HealthBreakdown>
      </HealthSection>

      {/* Prévisions résumées */}
      <ForecastSection>
        <ForecastCard
          type="Ventes 7j"
          predicted={12500}
          confidence={0.85}
          trend="up"
        />
        <ForecastCard
          type="Cash Flow 30j"
          predicted={-2300}
          confidence={0.72}
          trend="down"
          warning
        />
        <ForecastCard
          type="Ruptures Stock"
          predicted={3}
          items={['Tomates', 'Huile', 'Sel']}
          trend="stable"
        />
      </ForecastSection>

      {/* Anomalies actives */}
      <AnomaliesSection>
        <AnomalyList
          anomalies={anomalies}
          onInvestigate={handleInvestigate}
          onDismiss={handleDismiss}
        />
      </AnomaliesSection>

      {/* Top insights IA */}
      <InsightsSection>
        <InsightCard
          title="Optimisation suggérée"
          insight="Réduire les commandes de beurre de 20% -
                   Stock moyen 45 jours vs 15 recommandés"
          impact="+1200€ trésorerie"
          confidence={0.91}
        />
        <InsightCard
          title="Alerte marge"
          insight="Menu Burger a perdu 8 points de marge ce mois
                   (coût viande +22%)"
          impact="-340€/mois"
          confidence={0.88}
        />
      </InsightsSection>

      {/* Scoring fournisseurs */}
      <SuppliersSection>
        <SupplierRanking suppliers={topSuppliers} />
        <SupplierAlerts alerts={supplierAlerts} />
      </SuppliersSection>
    </div>
  );
}
```

### 7.2 Prévisions Interactives

```typescript
// frontend/src/modules/intelligence/forecast/PrevisionsPage.tsx

export function PrevisionsPage() {
  const [horizon, setHorizon] = useState<'7d' | '30d' | '90d'>('30d');
  const [forecastType, setForecastType] = useState<'sales' | 'cashflow' | 'stock'>('sales');

  const { data: forecast } = useQuery(
    ['forecast', forecastType, horizon],
    () => fetchForecast(forecastType, horizon)
  );

  return (
    <div className="forecast-page">
      {/* Contrôles */}
      <div className="controls">
        <SegmentedControl
          options={['Ventes', 'Trésorerie', 'Stock']}
          value={forecastType}
          onChange={setForecastType}
        />
        <SegmentedControl
          options={['7 jours', '30 jours', '90 jours']}
          value={horizon}
          onChange={setHorizon}
        />
      </div>

      {/* Graphique principal */}
      <ForecastChart
        data={forecast}
        showConfidenceInterval
        showActuals
        interactive
      />

      {/* Détails */}
      <div className="forecast-details">
        <MetricCard label="Valeur prédite" value={forecast?.predicted} />
        <MetricCard label="Intervalle confiance" value={`${forecast?.lower} - ${forecast?.upper}`} />
        <MetricCard label="Confiance" value={`${forecast?.confidence * 100}%`} />
        <MetricCard label="Modèle" value={forecast?.model} />
      </div>

      {/* Facteurs */}
      <FactorsPanel factors={forecast?.factors} />

      {/* Actions recommandées */}
      <RecommendationsPanel
        recommendations={forecast?.recommendations}
        onApply={handleApplyRecommendation}
      />
    </div>
  );
}
```

### 7.3 Détection d'Anomalies en Temps Réel

```typescript
// frontend/src/modules/intelligence/anomalies/AnomaliesPage.tsx

export function AnomaliesPage() {
  const { data: anomalies } = useQuery(['anomalies'], fetchAnomalies, {
    refetchInterval: 30000 // Refresh toutes les 30s
  });

  return (
    <div className="anomalies-page">
      {/* Filtres */}
      <FiltersBar>
        <TypeFilter options={['Prix', 'Stock', 'Transaction', 'Fournisseur']} />
        <SeverityFilter options={['Critique', 'Haute', 'Moyenne', 'Basse']} />
        <StatusFilter options={['Nouveau', 'En cours', 'Résolu', 'Ignoré']} />
      </FiltersBar>

      {/* Stats */}
      <StatsRow>
        <Stat label="Total actives" value={anomalies?.total} />
        <Stat label="Critiques" value={anomalies?.critical} severity="critical" />
        <Stat label="Impact estimé" value={anomalies?.totalImpact} format="currency" />
      </StatsRow>

      {/* Liste */}
      <AnomalyList>
        {anomalies?.items.map(anomaly => (
          <AnomalyCard
            key={anomaly.id}
            anomaly={anomaly}
            onInvestigate={() => openInvestigation(anomaly)}
            onResolve={() => resolveAnomaly(anomaly)}
            onIgnore={() => ignoreAnomaly(anomaly)}
          />
        ))}
      </AnomalyList>

      {/* Panel investigation */}
      <InvestigationPanel
        anomaly={selectedAnomaly}
        onClose={closeInvestigation}
      >
        <Timeline events={selectedAnomaly?.events} />
        <ImpactAnalysis impact={selectedAnomaly?.impact} />
        <SuggestedActions actions={selectedAnomaly?.suggestedActions} />
      </InvestigationPanel>
    </div>
  );
}
```

---

## 8. Calendrier & Priorités

### 8.1 Planning Macro

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLANNING DE RESTRUCTURATION                          │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: FONDATIONS BDD (Semaines 1-3)
═══════════════════════════════════════
S1  │ Migration event_log + audit_trail
    │ Triggers audit sur tables existantes
────┼─────────────────────────────────────
S2  │ Tables financial_rules + analytic_axes
    │ Tables forecast_cache + supplier_scores
────┼─────────────────────────────────────
S3  │ Tables reconciliation + margin_snapshots
    │ Tables inventory_intelligence
    │ Tests migrations + rollback

PHASE 2: CORE SERVICES (Semaines 4-7)
═══════════════════════════════════════
S4  │ Activation Rules Engine
    │ Tests unitaires + intégration
────┼─────────────────────────────────────
S5  │ Activation Forecast Engine
    │ Intégration Prophet/Holt-Winters
────┼─────────────────────────────────────
S6  │ Activation Margin Calculator
    │ Activation Supplier Scoring
────┼─────────────────────────────────────
S7  │ Event Bus + handlers
    │ Anomaly Detection service
    │ Tests E2E services

PHASE 3: BACKEND API (Semaines 8-10)
═══════════════════════════════════════
S8  │ API /cockpit/*
    │ API /intelligence/*
────┼─────────────────────────────────────
S9  │ API /finances/* (nouvelles routes)
    │ API /operations/* (unification)
────┼─────────────────────────────────────
S10 │ Tests API
    │ Documentation OpenAPI
    │ Rate limiting + sécurité

PHASE 4: FRONTEND UX (Semaines 11-15)
═══════════════════════════════════════
S11 │ Migration TypeScript (api/client)
    │ Nouvelle structure modules/
────┼─────────────────────────────────────
S12 │ Cockpit Dashboard
    │ Composants partagés
────┼─────────────────────────────────────
S13 │ Module Opérations unifié
    │ Module Finances unifié
────┼─────────────────────────────────────
S14 │ Module Intelligence
    │ Graphiques prévisions
────┼─────────────────────────────────────
S15 │ Navigation unifiée
    │ Tests E2E Cypress
    │ Polish UX

PHASE 5: STABILISATION (Semaines 16-18)
═══════════════════════════════════════
S16 │ Bug fixes
    │ Performance optimization
────┼─────────────────────────────────────
S17 │ Documentation utilisateur
    │ Formation
────┼─────────────────────────────────────
S18 │ Déploiement progressif
    │ Monitoring
```

### 8.2 Priorités par Valeur Business

| Priorité | Fonctionnalité | Valeur Business | Complexité | ROI |
|----------|----------------|-----------------|------------|-----|
| **P0** | Cockpit unifié | Visibilité 360° | Moyenne | Élevé |
| **P0** | Rules Engine | -80% temps catégorisation | Moyenne | Très élevé |
| **P1** | Prévisions ventes | Anticipation stocks | Haute | Élevé |
| **P1** | Détection anomalies | -50% pertes | Haute | Très élevé |
| **P1** | Rapprochement auto | -90% temps compta | Moyenne | Très élevé |
| **P2** | Scoring fournisseurs | Négociations optimisées | Basse | Moyen |
| **P2** | Marges temps réel | Décisions pricing | Moyenne | Élevé |
| **P2** | Inventaire intelligent | -30% ruptures | Haute | Élevé |
| **P3** | Event sourcing | Audit + debug | Basse | Moyen |
| **P3** | Analytique multi-axes | Reporting avancé | Moyenne | Moyen |

---

## 9. Métriques de Succès

### 9.1 KPIs Techniques

| Métrique | Baseline | Objectif | Comment mesurer |
|----------|----------|----------|-----------------|
| Couverture tests | 5% | 50% | Jest + Pytest coverage |
| Temps chargement page | 3.2s | <1s | Lighthouse |
| Erreurs 500 / jour | 12 | <2 | Monitoring |
| Dead code | ~40% | <5% | SonarQube |
| TypeScript adoption | 0% | 80% | LOC ratio |

### 9.2 KPIs Business

| Métrique | Baseline | Objectif | Comment mesurer |
|----------|----------|----------|-----------------|
| Temps catégorisation / facture | 5 min | 30s | Analytics |
| Taux catégorisation auto | 0% | 80% | Rules Engine stats |
| Temps rapprochement bancaire | 2h/jour | 15min | User tracking |
| Ruptures stock non anticipées | 8/mois | 2/mois | Inventory alerts |
| Utilisateurs actifs quotidiens | - | +50% | Analytics |

### 9.3 KPIs UX

| Métrique | Baseline | Objectif | Comment mesurer |
|----------|----------|----------|-----------------|
| Clics pour action courante | 6 | 2 | User tracking |
| Taux de rebond | 35% | <15% | Analytics |
| NPS utilisateurs | - | >40 | Sondage |
| Tickets support / mois | 25 | <10 | Zendesk |

---

## Annexes

### A. Fichiers à Supprimer/Archiver

```
À SUPPRIMER (code mort confirmé):
- frontend/src/features/*/components/README*.md (redondants)
- COMPONENT_SUMMARY.md
- FICHIERS_CREES.md
- docs/_archive/* (déplacer vers git history)

À ARCHIVER (peut être utile):
- _archive/backend_services_restaurant_monolith.py → git archive

À FUSIONNER:
- 4 dashboards → 1 Cockpit
- features/epicerie + restaurant → modules/operations
- features/finance → modules/finances
```

### B. Dépendances à Ajouter

```json
// Frontend - package.json
{
  "dependencies": {
    "@tanstack/react-query": "^5.x",  // Déjà présent
    "recharts": "^2.x",               // Déjà présent
    "framer-motion": "^10.x",         // Animations
    "date-fns": "^3.x",               // Dates
    "@radix-ui/react-*": "^1.x"       // Composants accessibles
  },
  "devDependencies": {
    "typescript": "^5.x",
    "@types/react": "^18.x",
    "vitest": "^1.x",
    "@testing-library/react": "^14.x"
  }
}

// Backend - requirements.txt
prophet==1.1.5          # Forecasting
scikit-learn==1.4.0     # ML
redis==5.0.0            # Cache
celery==5.3.0           # Background tasks
```

### C. Variables d'Environnement Nouvelles

```env
# Intelligence
FORECAST_MODEL=prophet        # prophet | holt_winters
ANOMALY_THRESHOLD=0.95
RULES_MIN_CONFIDENCE=0.80

# Event Bus
EVENT_BUS_ENABLED=true
EVENT_RETENTION_DAYS=365

# Cache
REDIS_URL=redis://localhost:6379
FORECAST_CACHE_TTL=3600
```

---

**Document créé le 9 décembre 2025**
**Version 1.0**

*Ce plan est un document vivant qui sera mis à jour au fur et à mesure de l'avancement.*
