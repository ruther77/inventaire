# File Processing Utilities

Module autonome pour le traitement de fichiers PDF et CSV, extrait des patterns utilisés dans le projet.

## Fonctionnalités

### PDF (`pdf_utils.py`)

- **`extract_text_from_pdf(pdf_path, use_layout=False)`**: Extraction de texte avec fallback automatique pypdf → pdftotext
- **`run_pdftotext(pdf_path, layout=True)`**: Wrapper pour pdftotext avec préservation du layout
- **`extract_text_from_pdfs(pdf_paths, ...)`**: Extraction batch de plusieurs PDFs

### CSV (`csv_utils.py`)

- **`parse_csv_with_encoding(file_path, encodings=['utf-8', 'latin-1', 'cp1252'])`**: Lecture CSV avec détection d'encodage
- **`detect_csv_delimiter(content)`**: Détection automatique du délimiteur (`;`, `,`, `\t`, `|`)
- **`normalize_column_names(df)`**: Normalisation des noms de colonnes (minuscules, sans accents, underscores)
- **`read_csv_robust(file_path)`**: Fonction tout-en-un combinant toutes les features ci-dessus
- **`write_csv_robust(df, file_path)`**: Écriture CSV avec defaults européens (UTF-8, `;`)

## Installation

Le module nécessite:
```bash
pip install pandas pypdf
```

Pour pdftotext (optionnel, utilisé en fallback):
```bash
# Debian/Ubuntu
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

## Exemples d'utilisation

### PDF

```python
from pathlib import Path
from file_processing import extract_text_from_pdf, run_pdftotext

# Extraction automatique (pypdf en priorité)
text = extract_text_from_pdf(Path("facture.pdf"))

# Force pdftotext avec layout (pour factures structurées)
text = run_pdftotext(Path("facture.pdf"), layout=True)

# Batch processing
from file_processing import extract_text_from_pdfs
pdfs = list(Path("invoices/").glob("*.pdf"))
results = extract_text_from_pdfs(pdfs, use_layout=True, skip_errors=True)
```

### CSV

```python
from pathlib import Path
from file_processing import read_csv_robust, normalize_column_names

# Lecture robuste (auto-détection encodage + délimiteur + normalisation)
df = read_csv_robust(Path("data.csv"))

# Lecture manuelle avec options
from file_processing import parse_csv_with_encoding
df = parse_csv_with_encoding(
    Path("data.csv"),
    encodings=['utf-8', 'iso-8859-1'],
    delimiter=';',
    skiprows=1
)

# Normalisation seule
df_normalized = normalize_column_names(df, lowercase=True, remove_accents=True)

# Écriture
from file_processing import write_csv_robust
write_csv_robust(df, Path("output.csv"), delimiter=";")
```

## Patterns extraits

Ce module est basé sur les patterns trouvés dans:
- `/home/ruuuzer/Documents/monprojet/scripts/backfill_prices_from_invoices.py` (extraction PDF pypdf)
- `/home/ruuuzer/Documents/monprojet/scripts/catalog/extract_eurociel_invoices.py` (pdftotext wrapper)

Toutes les dépendances métier ont été retirées pour rendre le module standalone et réutilisable.
