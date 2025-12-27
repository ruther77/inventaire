# Module Manifest - file_processing

## Structure du module

```
file_processing/
├── __init__.py                  # Exports publics du module
├── pdf_utils.py                 # Utilitaires extraction PDF
├── csv_utils.py                 # Utilitaires parsing CSV
├── requirements.txt             # Dépendances Python
├── README.md                    # Documentation utilisateur
├── QUICKSTART.md                # Guide démarrage rapide
├── TECHNICAL.md                 # Documentation technique
├── MANIFEST.md                  # Ce fichier
├── examples.py                  # Exemples d'utilisation
├── test_module.py               # Tests unitaires
└── check_installation.py        # Vérificateur d'installation
```

## Fichiers principaux

### Code source

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `__init__.py` | ~50 | Exports publics et version |
| `pdf_utils.py` | ~200 | Extraction PDF (pypdf + pdftotext) |
| `csv_utils.py` | ~300 | Parsing CSV robuste |

**Total code**: ~550 lignes

### Documentation

| Fichier | Type | Description |
|---------|------|-------------|
| `README.md` | Guide utilisateur | Vue d'ensemble et exemples de base |
| `QUICKSTART.md` | Tutoriel | Démarrage rapide en 5 minutes |
| `TECHNICAL.md` | Documentation technique | Architecture et patterns |
| `MANIFEST.md` | Index | Ce fichier |

### Utilitaires

| Fichier | Description |
|---------|-------------|
| `examples.py` | Exemples complets et use cases |
| `test_module.py` | Tests unitaires (5 tests) |
| `check_installation.py` | Vérificateur de dépendances |
| `requirements.txt` | Liste des dépendances pip |

## Fonctions exportées

### PDF (`pdf_utils.py`)

```python
extract_text_from_pdf(pdf_path, use_layout=False) -> str
run_pdftotext(pdf_path, layout=True) -> str
extract_text_from_pdfs(pdf_paths, use_layout=False, skip_errors=True) -> dict
```

### CSV (`csv_utils.py`)

```python
parse_csv_with_encoding(file_path, encodings=None, delimiter=None, **kwargs) -> pd.DataFrame
detect_csv_delimiter(content, candidates=None) -> str
normalize_column_names(df, lowercase=True, remove_accents=True, ...) -> pd.DataFrame
read_csv_robust(file_path, normalize_columns=True, ...) -> pd.DataFrame
write_csv_robust(df, file_path, encoding='utf-8', delimiter=';', ...) -> None
```

## Dépendances

### Requises
- `pandas >= 1.5.0`

### Optionnelles (au moins une recommandée)
- `pypdf >= 3.0.0` OU `PyPDF2 >= 2.0.0`
- `pdftotext` (via poppler-utils)

## Patterns sources

Extrait de:
- `/home/ruuuzer/Documents/monprojet/scripts/backfill_prices_from_invoices.py`
  - Fonction `extract_text_from_pdf()` (lignes 42-54)

- `/home/ruuuzer/Documents/monprojet/scripts/catalog/extract_eurociel_invoices.py`
  - Fonction `run_pdftotext()` (lignes 36-44)

## Tests

5 tests unitaires dans `test_module.py`:

1. `test_csv_delimiter_detection()` - Détection `;`, `,`, `\t`, `|`
2. `test_column_normalization()` - Normalisation noms colonnes
3. `test_csv_write_read()` - Roundtrip écriture/lecture
4. `test_csv_encoding_detection()` - Auto-détection encodage
5. `test_pdf_imports()` - Import des fonctions PDF

**Coverage**: ~80% du code (CSV complet, PDF imports seulement)

## Statistiques

- **Fichiers**: 11 (dont 3 source, 4 docs, 4 utils)
- **Lignes de code**: ~550
- **Lignes de documentation**: ~1000
- **Tests**: 5
- **Dépendances**: 1 requise, 2 optionnelles

## Version

**1.0.0** - Première version stable

## Licence

Code standalone extrait du projet `bibliotheque-maison`.
Pas de dépendances métier, utilisable dans n'importe quel projet.

## Usage rapide

```bash
# Installation
pip install -r requirements.txt

# Vérification
python3 check_installation.py

# Tests
python3 test_module.py

# Exemples
python3 examples.py
```

## Import du module

```python
# Dans un script Python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/home/ruuuzer/Documents/bibliotheque-maison/python")))

from file_processing import extract_text_from_pdf, read_csv_robust
```

Ou copier le dossier `file_processing/` dans votre projet.
