# Maquettes UI/UX Améliorées

Ce dossier contient les maquettes HTML/CSS des pages principales du projet, redesignées selon les recommandations de l'analyse UI/UX.

## Pages disponibles

1. **cockpit.html** - Page d'accueil Cockpit (Morning Brief)
2. **operations.html** - Dashboard Opérations
3. **finances.html** - Vue Trésorerie
4. **restaurant.html** - Vue unifiée Restaurant (avec onglets)
5. **intelligence.html** - Intelligence IA/ML

## Comment visualiser

Ouvrir les fichiers `.html` directement dans un navigateur moderne (Chrome, Firefox, Safari, Edge).

## Changements principaux par rapport à l'existant

### 1. Cockpit
- ✅ KPIs critiques visibles immédiatement (sans clic)
- ✅ Alertes en sidebar sticky
- ✅ Morning Brief en section collapsible
- ✅ Actions rapides vers pages clés

### 2. Opérations
- ✅ Breadcrumbs pour navigation claire
- ✅ Graphiques avec contrôles de période
- ✅ Actions inline sur listes (Commander, Modifier)
- ✅ Drill-down sur graphiques

### 3. Finances
- ✅ Solde global affiché dans header
- ✅ Évolution trésorerie en grand graphique
- ✅ Top dépenses + prochains paiements
- ✅ Gradient gold/amber (signature finance)

### 4. Restaurant
- ✅ Vue unifiée avec 3 onglets principaux (au lieu de 8 pages)
- ✅ Fiche plat inline avec ingrédients
- ✅ Food Cost % en badge coloré
- ✅ Actions rapides intégrées

### 5. Intelligence
- ✅ 4 onglets (au lieu de 6)
- ✅ Pédagogie IA avec tooltips "Comment ça marche"
- ✅ AIConfidenceBadge sur toutes suggestions
- ✅ Gradient cyan/blue (tech)

## Améliorations transversales

- **Contraste:** Texte plus clair (`text-slate-300` au lieu de `text-slate-400`)
- **Glass morphism:** Blur réduit (8px au lieu de 16px)
- **Gradients:** 1 seul par page (signature visuelle)
- **Typographie:** Titres plus grands (H1: 48px, H2: 32px)
- **Espacement:** Plus généreux entre sections (64px)
- **Micro-interactions:** Hover states prononcés
- **Accessibilité:** Labels ARIA, contraste WCAG AA

## Technologies utilisées

- HTML5 sémantique
- CSS3 (Grid, Flexbox, Custom Properties)
- Google Fonts (Inter, Sora)
- SVG pour icônes/mini-charts
- Pas de JavaScript (maquettes statiques)

---

*Maquettes créées le 23 décembre 2025*
*Basées sur l'analyse UI/UX complète*
