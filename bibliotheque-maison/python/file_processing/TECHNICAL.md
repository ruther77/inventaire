# Documentation Technique - file_processing

## Architecture

Le module `file_processing` est structuré en deux sous-modules principaux:

```
file_processing/
├── __init__.py          # Exports publics
├── pdf_utils.py         # Utilitaires PDF
├── csv_utils.py         # Utilitaires CSV
├── README.md            # Documentation utilisateur
├── TECHNICAL.md         # Documentation technique (ce fichier)
├── examples.py          # Exemples d'utilisation
└── test_module.py       # Tests unitaires
```

## pdf_utils.py

### Stratégie d'extraction

Le module implémente une stratégie de fallback pour l'extraction de texte PDF:

1. **Priorité 1**: `pypdf` (ou `PyPDF2`) - Pure Python, aucune dépendance système
2. **Fallback**: `pdftotext` - Nécessite poppler-utils, mais meilleure qualité pour PDFs complexes

### Fonctions principales

#### `extract_text_from_pdf(pdf_path, use_layout=False)`

Fonction principale avec fallback automatique.

**Workflow**:
```
1. Vérifier existence du fichier
2. Tenter extraction avec _extract_with_pypdf()
   ├─ Succès → retourner texte
   └─ Échec → Tenter run_pdftotext()
      ├─ Succès → retourner texte
      └─ Échec → Lever RuntimeError avec détails
```

**Pattern extrait de**: `backfill_prices_from_invoices.py:42-54`

#### `run_pdftotext(pdf_path, layout=True)`

Wrapper pour `pdftotext` avec gestion d'erreurs améliorée.

**Flags utilisés**:
- `-layout`: Préserve la disposition spatiale (essentiel pour factures en colonnes)
- `-`: Sortie vers stdout (pas de fichier temporaire)

**Pattern extrait de**: `extract_eurociel_invoices.py:36-44`

**Améliorations par rapport au code source**:
- Gestion explicite de FileNotFoundError avec message d'installation
- Support optionnel du flag `-layout`
- Documentation des cas d'usage

#### `extract_text_from_pdfs(pdf_paths, use_layout=False, skip_errors=True)`

Extraction batch avec gestion d'erreurs.

**Use case**: Traiter un dossier entier de factures PDF.

**Retourne**: `dict[Path, str]` - Seulement les PDFs réussis si `skip_errors=True`

## csv_utils.py

### Philosophie

Le module CSV résout trois problèmes récurrents:

1. **Encodage incertain** → Essai séquentiel d'encodages communs
2. **Délimiteur variable** → Détection automatique basée sur la consistance
3. **Noms de colonnes sales** → Normalisation configurable

### Fonctions principales

#### `parse_csv_with_encoding(file_path, encodings=None, delimiter=None, **kwargs)`

Lecture CSV robuste avec détection d'encodage.

**Encodages par défaut**: `['utf-8', 'latin-1', 'cp1252']`
- Couvre 99% des cas européens
- `utf-8`: Standard moderne
- `latin-1` (ISO-8859-1): Ancien standard européen
- `cp1252`: Windows Europe occidentale

**Workflow**:
```
Pour chaque encodage dans la liste:
  1. Lire échantillon (4096 octets) pour détecter délimiteur si nécessaire
  2. Tenter lecture complète avec pandas.read_csv()
  3. Si succès → retourner DataFrame
  4. Si UnicodeDecodeError ou ParserError → essayer encodage suivant
Si tous échouent → lever ValueError avec détails
```

#### `detect_csv_delimiter(content, candidates=None)`

Détection de délimiteur par analyse statistique.

**Candidats par défaut**: `[';', ',', '\t', '|']`

**Algorithme de scoring**:
```python
Pour chaque délimiteur candidat:
  1. Compter occurrences dans chaque ligne
  2. Calculer moyenne et écart-type
  3. Score = moyenne × consistance
     où consistance = 1 / (1 + écart_type)
```

**Rationale**: Un bon délimiteur apparaît le même nombre de fois sur chaque ligne.

**Exemple**:
```
Ligne 1: "A;B;C"  → 2 occurrences de ';'
Ligne 2: "D;E;F"  → 2 occurrences de ';'
Ligne 3: "G;H;I"  → 2 occurrences de ';'
→ Moyenne = 2, Écart-type = 0, Score élevé
```

#### `normalize_column_names(df, lowercase=True, remove_accents=True, ...)`

Normalisation de noms de colonnes pour accès programmatique.

**Transformations**:
1. **Suppression accents**: Décomposition Unicode NFKD + filtrage diacritiques
2. **Lowercase**: Conversion en minuscules
3. **Remplacement espaces**: Par underscore (configurable)
4. **Suppression caractères spéciaux**: Regex `[^a-zA-Z0-9_]`
5. **Nettoyage underscores**: Collapsage multiples, suppression début/fin

**Exemple de transformation**:
```
"Prix d'achat HT (€)"
  → "Prix d'achat HT (€)"        # Original
  → "Prix d'achat HT ()"         # Suppression €
  → "prix d'achat ht ()"         # Lowercase
  → "prix_d'achat_ht_()"         # Remplacement espaces
  → "prix_dachat_ht_"            # Suppression spéciaux
  → "prix_dachat_ht"             # Nettoyage final
```

#### `read_csv_robust(file_path, normalize_columns=True, ...)`

Fonction tout-en-un combinant toutes les features.

**Équivalent à**:
```python
df = parse_csv_with_encoding(file_path, encodings, delimiter, **kwargs)
if normalize_columns:
    df = normalize_column_names(df)
return df
```

**Use case principal**: Lecture de fichiers CSV tiers avec format inconnu.

#### `write_csv_robust(df, file_path, encoding='utf-8', delimiter=';', ...)`

Écriture CSV avec defaults européens.

**Defaults**:
- `encoding='utf-8'`: Standard universel
- `delimiter=';'`: Excel européen utilise `;` par défaut
- `index=False`: Pas d'index de ligne par défaut

**Crée automatiquement** les dossiers parents si nécessaire.

## Patterns extraits

### Extraction PDF (backfill_prices_from_invoices.py)

```python
# Original (lignes 42-54)
def extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader

    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
```

**Améliorations apportées**:
- Fallback vers `pdftotext` si pypdf échoue
- Gestion d'erreurs explicite avec messages d'aide
- Support batch avec `extract_text_from_pdfs()`

### Wrapper pdftotext (extract_eurociel_invoices.py)

```python
# Original (lignes 36-44)
def run_pdftotext(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
```

**Améliorations apportées**:
- Flag `-layout` optionnel via paramètre
- Gestion FileNotFoundError avec instructions d'installation
- Documentation des use cases (factures vs texte continu)

## Dépendances

### Requises
```
pandas>=1.0.0
```

### Optionnelles
```
pypdf>=3.0.0  # ou PyPDF2>=2.0.0
```

### Système (optionnel)
```bash
# pdftotext (fallback si pypdf non disponible)
sudo apt-get install poppler-utils  # Debian/Ubuntu
brew install poppler                # macOS
```

## Tests

Exécuter les tests:
```bash
python3 file_processing/test_module.py
```

Tests couverts:
- Détection de délimiteur (`;`, `,`, `\t`, `|`)
- Normalisation de colonnes (accents, espaces, caractères spéciaux)
- Roundtrip écriture/lecture CSV
- Détection automatique d'encodage (UTF-8, Latin-1)
- Import des fonctions PDF

## Usage en production

### Pattern recommandé pour factures PDF

```python
from pathlib import Path
from file_processing import extract_text_from_pdf

def process_invoice(pdf_path: Path) -> dict:
    # Utiliser layout=True pour préserver colonnes
    text = extract_text_from_pdf(pdf_path, use_layout=True)

    # Parser le texte structuré...
    return parsed_data
```

### Pattern recommandé pour CSV tiers

```python
from pathlib import Path
from file_processing import read_csv_robust

def import_catalog(csv_path: Path) -> pd.DataFrame:
    # Auto-détection complète
    df = read_csv_robust(csv_path)

    # Colonnes normalisées accessibles facilement
    if 'nom_produit' in df.columns:
        products = df['nom_produit'].tolist()

    return df
```

## Performance

### PDF
- `pypdf`: ~0.5-2s par page (Python pur)
- `pdftotext`: ~0.1-0.5s par page (natif C++)

**Recommandation**: Laisser le fallback automatique décider.

### CSV
- Détection délimiteur: O(n) sur échantillon (premières 10 lignes)
- Détection encodage: O(k×n) où k = nombre d'encodages testés (max 3)
- Normalisation colonnes: O(m) où m = nombre de colonnes

**Impact négligeable** sur fichiers < 100 MB.

## Évolutions futures possibles

1. **PDF**:
   - Support OCR pour PDFs scannés (tesseract)
   - Extraction de tableaux structurés (camelot, tabula)
   - Extraction de métadonnées (date, auteur)

2. **CSV**:
   - Détection automatique de types de colonnes
   - Validation de schéma (pandera)
   - Support streaming pour gros fichiers (chunksize)

3. **Général**:
   - Support Excel (openpyxl)
   - Support JSON avec normalisation
   - Cache pour éviter re-parsing
