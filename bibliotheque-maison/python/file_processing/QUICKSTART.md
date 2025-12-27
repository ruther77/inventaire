# Quick Start Guide

Guide de démarrage rapide pour le module `file_processing`.

## Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Vérifier l'installation

```bash
python3 check_installation.py
```

Vous devriez voir:
```
✓ Core installation: OK
✓ PDF support: OK
✓ All checks passed! Module is ready to use.
```

## Utilisation de base

### Extraire du texte d'un PDF

```python
from pathlib import Path
from file_processing import extract_text_from_pdf

# Auto-détection de la meilleure méthode
text = extract_text_from_pdf(Path("facture.pdf"))
print(text)
```

### Lire un CSV avec auto-détection

```python
from pathlib import Path
from file_processing import read_csv_robust

# Détecte automatiquement: encodage, délimiteur, normalise les colonnes
df = read_csv_robust(Path("data.csv"))
print(df.head())
print(df.columns)  # Colonnes normalisées: minuscules, sans accents
```

### Normaliser les noms de colonnes

```python
import pandas as pd
from file_processing import normalize_column_names

df = pd.DataFrame({"Nom Prénom": [1], "Âge (années)": [2]})
df_clean = normalize_column_names(df)
print(df_clean.columns)  # ['nom_prenom', 'age_annees']
```

### Écrire un CSV propre

```python
from pathlib import Path
from file_processing import write_csv_robust

write_csv_robust(df, Path("output.csv"))  # UTF-8, délimiteur ;
```

## Exemples complets

Voir le fichier `examples.py` pour des exemples détaillés:

```bash
python3 examples.py
```

## Tests

Lancer les tests unitaires:

```bash
python3 test_module.py
```

## Use cases typiques

### 1. Traiter des factures PDF

```python
from pathlib import Path
from file_processing import extract_text_from_pdfs

# Extraire tous les PDFs d'un dossier
invoice_dir = Path("factures/")
pdfs = list(invoice_dir.glob("*.pdf"))

# Extraction batch avec gestion d'erreurs
results = extract_text_from_pdfs(
    pdfs,
    use_layout=True,      # Préserve les colonnes
    skip_errors=True      # Continue même si certains échouent
)

for pdf_path, text in results.items():
    print(f"Traité: {pdf_path.name}")
    # Parser le texte...
```

### 2. Importer un catalogue CSV

```python
from pathlib import Path
from file_processing import read_csv_robust

# Lecture robuste d'un CSV externe (encodage inconnu)
df = read_csv_robust(Path("catalogue_fournisseur.csv"))

# Les colonnes sont automatiquement normalisées
if 'nom_produit' in df.columns:
    products = df['nom_produit'].tolist()
```

### 3. Pipeline complet

```python
from pathlib import Path
from file_processing import (
    extract_text_from_pdf,
    read_csv_robust,
    write_csv_robust,
    normalize_column_names
)

# 1. Extraire facture PDF
invoice_text = extract_text_from_pdf(
    Path("facture.pdf"),
    use_layout=True
)

# 2. Parser le texte (votre logique)
# parsed_data = custom_parser(invoice_text)

# 3. Lire catalogue existant
catalog = read_csv_robust(Path("catalogue.csv"))

# 4. Fusionner et traiter
# merged = process(catalog, parsed_data)

# 5. Exporter résultat
# write_csv_robust(merged, Path("resultat.csv"))
```

## Résolution de problèmes

### Erreur: "pypdf not installed"

```bash
pip install pypdf
```

### Erreur: "pdftotext command not found"

```bash
# Debian/Ubuntu
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### Erreur: "Failed to parse CSV"

Le module essaie automatiquement plusieurs encodages. Si ça échoue toujours:

```python
from file_processing import parse_csv_with_encoding

# Spécifier des encodages personnalisés
df = parse_csv_with_encoding(
    Path("data.csv"),
    encodings=['utf-8', 'iso-8859-1', 'windows-1252']
)
```

## Documentation complète

- **README.md**: Vue d'ensemble et exemples
- **TECHNICAL.md**: Architecture et détails techniques
- **examples.py**: Exemples complets
- **test_module.py**: Tests unitaires

## Support

Pour plus d'informations, consultez les docstrings dans le code:

```python
from file_processing import extract_text_from_pdf
help(extract_text_from_pdf)
```
