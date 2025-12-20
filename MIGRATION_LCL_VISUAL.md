# Visualisation de la migration LCL

## Vue d'ensemble du problème

```
AVANT MIGRATION:
┌─────────────────────────────────────────────────────────────────┐
│                    SITUATION INCORRECTE                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│  Compte 15: LCL Principal       │     │  Compte 16: LCL Noutam          │
│  ─────────────────────────      │     │  ──────────────────────         │
│  • 2243 transactions            │     │  • 1683 transactions            │
│  • 2023-12-31 → 2025-12-31      │     │  • 2023-11-30 → 2025-12-31      │
│  • Source: COMPTECOURANT_*.pdf  │     │  • Source: autres imports       │
│    (ERREUR!)                    │     │                                 │
└─────────────────────────────────┘     └─────────────────────────────────┘
           │                                          │
           └──────────────────┬───────────────────────┘
                              │
                      ┌───────▼────────┐
                      │  319 DOUBLONS  │
                      │  (même date +  │
                      │   même montant)│
                      └────────────────┘

EN RÉALITÉ: Les deux comptes représentent LE MÊME COMPTE BANCAIRE!
```

## Architecture de la solution

```
MIGRATION EN 12 ÉTAPES:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  [1] Analyse préliminaire                                       │
│      └─> Compter transactions et identifier doublons           │
│                                                                  │
│  [2] Créer table temporaire doublons                           │
│      └─> Identifier avec priorités (compte 16 > 15)            │
│                                                                  │
│  [3] Sauvegarder avant suppression                             │
│      └─> Audit trail pour traçabilité                          │
│                                                                  │
│  [4] Supprimer relations (foreign keys)                        │
│      └─> Nettoyer payments, reconciliations, etc.              │
│                                                                  │
│  [5] Supprimer les doublons                                    │
│      └─> Garder la meilleure version de chaque doublon         │
│                                                                  │
│  [6] Migrer transactions restantes 15 → 16                     │
│      └─> Tous les tx du compte 15 vers le 16                   │
│                                                                  │
│  [7] Mettre à jour counterparty_account_id                     │
│      └─> Corriger les références croisées                      │
│                                                                  │
│  [8] Créer index optimisés                                     │
│      └─> ix_finance_tx_dedup, ix_..._stmtline                  │
│                                                                  │
│  [9] Créer trigger de protection                               │
│      └─> Détection automatique futurs doublons                 │
│                                                                  │
│  [10] Désactiver compte 15                                     │
│      └─> Marquer comme obsolète                                │
│                                                                  │
│  [11] Vérifications post-migration                             │
│      └─> Intégrité, continuité, statistiques                   │
│                                                                  │
│  [12] Nettoyage tables temporaires                             │
│      └─> Supprimer les tables temp_*                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Résultat final

```
APRÈS MIGRATION:
┌─────────────────────────────────────────────────────────────────┐
│                    SITUATION CORRIGÉE                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│  Compte 15: LCL Principal       │     │  Compte 16: LCL Noutam          │
│  [OBSOLETE - MERGED TO 16]      │     │  ──────────────────────         │
│  ─────────────────────────      │     │  • 3607 transactions            │
│  • 0 transactions               │     │  • 2023-11-30 → 2025-12-31      │
│  • is_active = FALSE            │     │  • Toutes sources consolidées   │
│  • Désactivé                    │     │  • SANS DOUBLONS                │
└─────────────────────────────────┘     └─────────────────────────────────┘
           (inactif)                                  (actif)
                                                      │
                                              ┌───────▼────────┐
                                              │  PROTECTION:   │
                                              │  • Trigger     │
                                              │  • Index       │
                                              └────────────────┘
```

## Flux de déduplication

```
LOGIQUE DE CHOIX POUR LES DOUBLONS:

Pour chaque paire (date_operation + amount identiques):

┌─────────────────────────────────────────────────────────┐
│  Transaction A          vs          Transaction B       │
│  (Compte 15)                       (Compte 16)          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Priorité 1: Account ID        │
        │  Préférer account_id = 16      │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Priorité 2: Référence         │
        │  Éviter ref_externe "stmtline:"│
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Priorité 3: Label             │
        │  Préférer label plus long      │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Priorité 4: Date création     │
        │  Préférer created_at DESC      │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │     TRANSACTION À GARDER       │
        └────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │  Autre transaction → SUPPRIMÉE  │
        └─────────────────────────────────┘
```

## Timeline des données

```
COUVERTURE TEMPORELLE:

2023-11 ▼
        ├─────┤ Compte 16 (1 tx)
2023-12 │
        ├─────┤ Compte 16 (126 tx)
2024-01 │
        ├──────────────────┤ Compte 15 (157 tx)
2024-02 │
        ├──────────────────┤ Compte 15 (148 tx)
        ├─────┤ Compte 16 (147 tx) [CHEVAUCHEMENT]
2024-03 │
        ├──────────────────┤ Compte 15 (157 tx)
...     │
2025-01 │
        ├──────────────────┤ Compte 15 (170 tx)
        ├─────┤ Compte 16 (169 tx) [CHEVAUCHEMENT]
2025-02 │
        ├──────────────────┤ Compte 15 (144 tx)
2025-03 │
        ├─────┤ Compte 16 (172 tx)
...     │
2025-10 │
        ├─────┤ Compte 16 (151 tx)
2025-12 │
        └─────┤ Compte 16 + Compte 15 (1 tx chacun)

APRÈS MIGRATION:
2023-11 ▼
2025-12 ├─────────────────────────────────┤ Compte 16 (3607 tx)
        └────────────────────────────────────────────────►
                 CONTINUITÉ COMPLÈTE
```

## Protection contre futurs doublons

```
SYSTÈME DE PROTECTION:

┌─────────────────────────────────────────────────────────┐
│               NOUVELLE TRANSACTION                      │
│               (INSERT ou UPDATE)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  TRIGGER: check_duplicate_     │
        │          transaction()         │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  Vérifier existence dans DB:   │
        │  • Même account_id             │
        │  • Même date_operation         │
        │  • Même amount                 │
        │  • Même label                  │
        └────────────┬───────────────────┘
                     │
            ┌────────┴────────┐
            │                 │
    ┌───────▼──────┐   ┌─────▼──────────┐
    │  Doublon     │   │  Transaction   │
    │  détecté     │   │  unique        │
    └───────┬──────┘   └─────┬──────────┘
            │                │
            ▼                ▼
    ┌───────────────┐   ┌────────────┐
    │ ⚠ WARNING     │   │ ✓ INSERT   │
    │ Log alerte    │   │   OK       │
    │ (n'empêche    │   └────────────┘
    │  pas l'insert)│
    └───────────────┘
```

## Index créés

```
INDEX OPTIMISÉS:

1. ix_finance_tx_dedup
   ┌─────────────────────────────────────────┐
   │  (account_id, date_operation, amount)   │
   │  ───────────────────────────────────    │
   │  Permet de trouver rapidement les       │
   │  doublons potentiels lors d'un import   │
   │                                         │
   │  Exemple de requête optimisée:         │
   │  SELECT * FROM finance_transactions    │
   │  WHERE account_id = 16                 │
   │    AND date_operation = '2025-01-15'   │
   │    AND amount = 123.45;                │
   └─────────────────────────────────────────┘

2. ix_finance_tx_ref_externe_stmtline
   ┌─────────────────────────────────────────┐
   │  (ref_externe)                          │
   │  WHERE ref_externe LIKE 'stmtline:%'    │
   │  ───────────────────────────────────    │
   │  Permet d'identifier rapidement les     │
   │  transactions avec référence stmtline   │
   │  (souvent moins descriptives)           │
   │                                         │
   │  Exemple de requête optimisée:         │
   │  SELECT * FROM finance_transactions    │
   │  WHERE ref_externe LIKE 'stmtline:%';  │
   └─────────────────────────────────────────┘
```

## Exemples de transactions traitées

```
EXEMPLE DE DOUBLON RÉSOLU:

┌─────────────────────────────────────────────────────────────────┐
│  Date: 2025-01-31 | Montant: 87.37 EUR                         │
└─────────────────────────────────────────────────────────────────┘

Transaction A (Compte 15):                [SUPPRIMÉE]
  ID: 136235
  Label: "PRLV SEPA PREFILOC CAPITAL"
  ref_externe: "stmtline:136235"
  created_at: 2025-01-31 10:00:00
  ❌ Critères: compte 15, ref_externe stmtline

Transaction B (Compte 16):                [CONSERVÉE]
  ID: 135890
  Label: "PRLV SEPA PREFILOC CAPITAL LIBELLE:F250064865 REF.CLIENT:..."
  ref_externe: NULL
  created_at: 2025-01-31 09:30:00
  ✓ Critères: compte 16, pas de stmtline, label plus descriptif

Résultat: Transaction B conservée (plus d'informations)
```

```
EXEMPLE DE TRANSACTION MIGRÉE:

Transaction originale (Compte 15):
  ID: 125678
  account_id: 15
  date_operation: 2024-06-15
  amount: 234.56
  label: "VIR SEPA FOURNISSEUR XYZ"
  note: NULL

Transaction après migration (Compte 16):
  ID: 125678 (même ID conservé)
  account_id: 16  ← MODIFIÉ
  date_operation: 2024-06-15
  amount: 234.56
  label: "VIR SEPA FOURNISSEUR XYZ"
  note: "Migrated from account 15 (LCL Principal) to 16 (LCL Noutam)"  ← AJOUTÉ
```

## Statistiques attendues

```
AVANT:
┌──────────────┬─────────────┬──────────────┐
│   Compte     │  Nb Trans   │   Période    │
├──────────────┼─────────────┼──────────────┤
│  15 (Princ)  │    2243     │ 2023-12 →    │
│  16 (Noutam) │    1683     │ 2023-11 →    │
│  TOTAL       │    3926     │              │
│  Doublons    │     319     │              │
└──────────────┴─────────────┴──────────────┘

APRÈS:
┌──────────────┬─────────────┬──────────────┐
│   Compte     │  Nb Trans   │   Période    │
├──────────────┼─────────────┼──────────────┤
│  15 (Princ)  │       0     │ (désactivé)  │
│  16 (Noutam) │    3607     │ 2023-11 →    │
│  TOTAL       │    3607     │              │
│  Doublons    │       0     │              │
└──────────────┴─────────────┴──────────────┘

CALCUL: 2243 + 1683 - 319 = 3607 ✓
```

## Checklist visuelle

```
VÉRIFICATIONS POST-MIGRATION:

┌─────────────────────────────────────────────────────┐
│  État du système                        Status      │
├─────────────────────────────────────────────────────┤
│  □ Compte 15 a 0 transactions           [ ]         │
│  □ Compte 16 a ~3607 transactions       [ ]         │
│  □ Aucun doublon restant                [ ]         │
│  □ Compte 15 is_active = FALSE          [ ]         │
│  □ Trigger créé et fonctionnel          [ ]         │
│  □ Index ix_finance_tx_dedup existe     [ ]         │
│  □ Index ix_...stmtline existe          [ ]         │
│  □ Continuité temporelle OK             [ ]         │
│  □ Sauvegarde créée                     [ ]         │
│  □ Tests de vérification passés         [ ]         │
└─────────────────────────────────────────────────────┘

Pour cocher:
  docker exec ... psql ... -f verify_lcl_merge.sql
```

## Architecture des fichiers

```
monprojet/
├── db/
│   └── migrations/
│       ├── 004_merge_lcl_accounts.sql           ← Migration principale
│       └── 004_merge_lcl_accounts_README.md     ← Documentation détaillée
│
├── scripts/
│   ├── run_lcl_merge_migration.sh               ← Script d'exécution
│   └── verify_lcl_merge.sql                     ← Script de vérification
│
├── GUIDE_EXECUTION_MIGRATION_LCL.md             ← Guide rapide
└── MIGRATION_LCL_VISUAL.md                      ← Ce fichier (visualisation)
```

---

**Légende des symboles:**
- ✓ : Succès / Validé
- ❌ : Erreur / Supprimé
- ⚠ : Attention / Warning
- ← : Modification
- → : Transformation
- ▼ : Début de période
- □ : À vérifier
- ☑ : Vérifié

---

**Date**: 2025-12-17
**Version**: 1.0
**Auteur**: Assistant Claude
