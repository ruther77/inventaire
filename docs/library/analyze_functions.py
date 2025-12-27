#!/usr/bin/env python3
"""
Script d'analyse exhaustive des fonctions JavaScript/React
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Set

class JSFunctionAnalyzer:
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.catalog = {
            "metadata": {
                "analyzed_at": None,
                "total_files": 0,
                "total_functions": 0,
                "categories": {}
            },
            "functions": {}
        }

    def analyze_all_files(self):
        """Analyse tous les fichiers JS/TS dans le répertoire"""
        js_files = list(self.src_dir.rglob("*.js")) + \
                   list(self.src_dir.rglob("*.jsx")) + \
                   list(self.src_dir.rglob("*.ts")) + \
                   list(self.src_dir.rglob("*.tsx"))

        # Filtrer les fichiers de test et stories (optionnel, on les garde)
        js_files = [f for f in js_files if 'node_modules' not in str(f)]

        self.catalog["metadata"]["total_files"] = len(js_files)

        for file_path in sorted(js_files):
            self.analyze_file(file_path)

    def analyze_file(self, file_path: Path):
        """Analyse un fichier et extrait toutes les fonctions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            return

        relative_path = file_path.relative_to(self.src_dir.parent)

        # Extraire les imports
        imports = self.extract_imports(content)

        # Extraire les fonctions
        functions = self.extract_functions(content, str(relative_path), imports)

        for func in functions:
            func_id = f"{relative_path}::{func['name']}"
            self.catalog["functions"][func_id] = func

    def extract_imports(self, content: str) -> List[str]:
        """Extrait les imports du fichier"""
        imports = []

        # import ... from '...'
        import_pattern = r"import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+['\"]([^'\"]+)['\"]"
        imports.extend(re.findall(import_pattern, content))

        # import '...'
        import_pattern2 = r"import\s+['\"]([^'\"]+)['\"]"
        imports.extend(re.findall(import_pattern2, content))

        return list(set(imports))

    def extract_functions(self, content: str, file_path: str, imports: List[str]) -> List[Dict]:
        """Extrait toutes les fonctions du contenu"""
        functions = []

        # Patterns pour différents types de fonctions
        patterns = [
            # React Component (function)
            (r'(?:export\s+(?:default\s+)?)?function\s+(\w+)\s*\(([^)]*)\)\s*{', 'function', 'component'),
            # Arrow function export
            (r'export\s+const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>', 'arrow function', 'component'),
            # const arrow function
            (r'const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>', 'arrow function', 'utility'),
            # Custom hooks (use*)
            (r'(?:export\s+(?:default\s+)?)?function\s+(use\w+)\s*\(([^)]*)\)', 'custom hook', 'hook'),
            (r'export\s+(?:default\s+)?const\s+(use\w+)\s*=\s*\(([^)]*)\)\s*=>', 'custom hook', 'hook'),
        ]

        for pattern, func_type, default_category in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                params = match.group(2) if len(match.groups()) > 1 else ""

                # Extraire JSDoc si présent
                jsdoc = self.extract_jsdoc(content, match.start())

                # Déterminer la catégorie
                category = self.categorize_function(name, func_type, file_path, imports)

                # Déterminer le niveau de réutilisabilité
                reusability = self.assess_reusability(name, func_type, file_path, content)

                func_info = {
                    "name": name,
                    "file": file_path,
                    "type": func_type,
                    "signature": f"{name}({params})",
                    "parameters": self.parse_parameters(params, jsdoc),
                    "category": category,
                    "description": self.extract_description(jsdoc),
                    "dependencies": imports,
                    "jsdoc": jsdoc,
                    "reusability": reusability,
                    "is_exported": "export" in content[max(0, match.start()-50):match.start()],
                }

                functions.append(func_info)

        return functions

    def extract_jsdoc(self, content: str, func_start: int) -> str:
        """Extrait le JSDoc précédant une fonction"""
        # Chercher en arrière pour trouver le JSDoc
        before = content[max(0, func_start-500):func_start]
        jsdoc_match = re.search(r'/\*\*(.*?)\*/', before, re.DOTALL)
        if jsdoc_match:
            return jsdoc_match.group(0)
        return ""

    def extract_description(self, jsdoc: str) -> str:
        """Extrait la description du JSDoc"""
        if not jsdoc:
            return ""
        # Première ligne après /**
        lines = jsdoc.split('\n')
        for line in lines[1:]:
            clean = line.strip().lstrip('*').strip()
            if clean and not clean.startswith('@'):
                return clean
        return ""

    def parse_parameters(self, params_str: str, jsdoc: str) -> List[Dict]:
        """Parse les paramètres d'une fonction"""
        if not params_str.strip():
            return []

        params = []
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue

            # Extraire nom et valeur par défaut
            default_match = re.search(r'(\w+)\s*=\s*(.+)', param)
            if default_match:
                name = default_match.group(1)
                default = default_match.group(2)
            else:
                name = re.sub(r'[:{}\[\]].*', '', param).strip()
                default = None

            # Chercher le type dans JSDoc
            param_type = "any"
            if jsdoc:
                type_match = re.search(rf'@param\s+{{([^}}]+)}}\s+{name}', jsdoc)
                if type_match:
                    param_type = type_match.group(1)

            params.append({
                "name": name,
                "type": param_type,
                "default": default,
                "required": default is None
            })

        return params

    def categorize_function(self, name: str, func_type: str, file_path: str, imports: List[str]) -> str:
        """Catégorise une fonction selon son nom, type et contexte"""
        file_lower = file_path.lower()
        name_lower = name.lower()

        # Hooks
        if name.startswith('use'):
            if any(x in imports for x in ['react-query', '@tanstack/react-query']):
                if 'mutation' in name_lower or 'query' in name_lower:
                    return "Hooks/Data Fetching"
            if 'state' in name_lower or 'reducer' in name_lower:
                return "Hooks/State Management"
            if any(x in name_lower for x in ['click', 'key', 'mouse', 'touch', 'gesture', 'scroll']):
                return "Hooks/UI Interaction"
            return "Hooks/Utilities"

        # Components
        if func_type in ['function', 'arrow function']:
            # Majuscule = probablement un composant React
            if name[0].isupper():
                if 'layout' in file_lower or 'page' in name_lower or 'shell' in name_lower:
                    return "Components/Layout"
                if 'form' in file_lower or 'input' in name_lower or 'select' in name_lower:
                    return "Components/Forms"
                if 'table' in name_lower or 'list' in name_lower or 'card' in name_lower:
                    return "Components/Data Display"
                if 'modal' in name_lower or 'toast' in name_lower or 'alert' in name_lower or 'loading' in name_lower:
                    return "Components/Feedback"
                if 'button' in name_lower or 'icon' in name_lower or 'badge' in name_lower:
                    return "Components/UI Elements"
                return "Components/Generic"

        # Utils
        if 'utils' in file_lower or 'helpers' in file_lower:
            if 'format' in name_lower or 'parse' in name_lower:
                return "Utils/Formatting"
            if 'validate' in name_lower or 'check' in name_lower:
                return "Utils/Validation"
            if 'calculate' in name_lower or 'compute' in name_lower:
                return "Utils/Calculation"
            return "Utils/Generic"

        # API
        if 'api' in file_lower or 'client' in file_lower:
            return "API/Client"

        # Context
        if 'context' in file_lower or 'provider' in name_lower:
            return "Context/Providers"

        return "Uncategorized"

    def assess_reusability(self, name: str, func_type: str, file_path: str, content: str) -> str:
        """Évalue le niveau de réutilisabilité"""
        score = 0

        # Hooks personnalisés = haute réutilisabilité
        if name.startswith('use') and 'export' in content:
            score += 3

        # Dans un dossier utils/hooks/components = réutilisable
        if any(x in file_path.lower() for x in ['utils', 'hooks', 'components/ui', 'components/feedback']):
            score += 2

        # Exporté = plus réutilisable
        if 'export' in content:
            score += 1

        # Pas de dépendances spécifiques = plus réutilisable
        if not any(x in file_path.lower() for x in ['features/', 'pages/']):
            score += 1

        # Nom générique
        generic_names = ['format', 'parse', 'validate', 'calculate', 'fetch', 'get', 'set', 'update']
        if any(x in name.lower() for x in generic_names):
            score += 1

        if score >= 5:
            return "High"
        elif score >= 3:
            return "Medium"
        else:
            return "Low"

    def generate_statistics(self):
        """Génère des statistiques par catégorie"""
        from collections import Counter

        categories = Counter()
        types = Counter()
        reusability = Counter()

        for func in self.catalog["functions"].values():
            categories[func["category"]] += 1
            types[func["type"]] += 1
            reusability[func["reusability"]] += 1

        self.catalog["metadata"]["total_functions"] = len(self.catalog["functions"])
        self.catalog["metadata"]["categories"] = dict(categories)
        self.catalog["metadata"]["types"] = dict(types)
        self.catalog["metadata"]["reusability"] = dict(reusability)

    def reorganize_by_category(self):
        """Réorganise le catalog par catégorie"""
        by_category = {}

        for func_id, func in self.catalog["functions"].items():
            category = func["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(func)

        # Trier par nom dans chaque catégorie
        for category in by_category:
            by_category[category].sort(key=lambda x: x["name"])

        return by_category

    def save_catalog(self, output_path: str):
        """Sauvegarde le catalogue en JSON"""
        from datetime import datetime

        self.catalog["metadata"]["analyzed_at"] = datetime.now().isoformat()
        self.generate_statistics()

        # Créer une version organisée par catégorie
        catalog_by_category = {
            "metadata": self.catalog["metadata"],
            "functions_by_category": self.reorganize_by_category(),
            "functions_flat": self.catalog["functions"]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(catalog_by_category, f, indent=2, ensure_ascii=False)

        print(f"✓ Catalogue sauvegardé: {output_path}")
        print(f"  - {self.catalog['metadata']['total_files']} fichiers analysés")
        print(f"  - {self.catalog['metadata']['total_functions']} fonctions trouvées")
        print(f"\n  Répartition par catégorie:")
        for cat, count in sorted(self.catalog["metadata"]["categories"].items()):
            print(f"    • {cat}: {count}")


if __name__ == "__main__":
    import sys

    src_dir = "/home/ruuuzer/Documents/monprojet/frontend/src"
    output_path = "/home/ruuuzer/Documents/monprojet/docs/library/javascript_functions_catalog.json"

    print("🔍 Analyse des fonctions JavaScript/React...")
    print(f"📁 Répertoire: {src_dir}\n")

    analyzer = JSFunctionAnalyzer(src_dir)
    analyzer.analyze_all_files()
    analyzer.save_catalog(output_path)

    print("\n✅ Analyse terminée!")
