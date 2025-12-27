#!/usr/bin/env python3
"""
Script d'analyse exhaustive AVANCÉ des fonctions JavaScript/React
Version 2.0 - Analyse approfondie avec détection de patterns
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter

class AdvancedJSFunctionAnalyzer:
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.catalog = {
            "metadata": {
                "analyzed_at": None,
                "total_files": 0,
                "total_functions": 0,
                "categories": {}
            },
            "functions_by_category": {},
            "functions_flat": {}
        }

        # Patterns de détection avancés
        self.api_patterns = [
            r'fetch', r'axios', r'api\.(get|post|put|patch|delete)',
            r'await\s+\w+\(', r'\.then\(', r'async\s+function'
        ]

        self.query_patterns = [
            r'useQuery', r'useMutation', r'queryKey', r'queryFn',
            r'@tanstack/react-query', r'react-query'
        ]

    def analyze_all_files(self):
        """Analyse tous les fichiers JS/TS dans le répertoire"""
        js_files = list(self.src_dir.rglob("*.js")) + \
                   list(self.src_dir.rglob("*.jsx")) + \
                   list(self.src_dir.rglob("*.ts")) + \
                   list(self.src_dir.rglob("*.tsx"))

        js_files = [f for f in js_files if 'node_modules' not in str(f)]
        self.catalog["metadata"]["total_files"] = len(js_files)

        print(f"📊 Analyse de {len(js_files)} fichiers...")

        for i, file_path in enumerate(sorted(js_files), 1):
            if i % 50 == 0:
                print(f"   Progression: {i}/{len(js_files)} fichiers...")
            self.analyze_file(file_path)

    def extract_imports(self, content: str) -> Dict[str, List[str]]:
        """Extrait les imports avec plus de détails"""
        imports = {
            'packages': [],
            'local': [],
            'react': [],
            'hooks': [],
            'components': [],
            'utils': []
        }

        # import ... from '...'
        for match in re.finditer(r"import\s+({[^}]+}|[\w\s,*]+)\s+from\s+['\"]([^'\"]+)['\"]", content):
            imported_items = match.group(1)
            source = match.group(2)

            if source.startswith('react'):
                imports['react'].append(source)
            elif source.startswith('.'):
                imports['local'].append(source)
                if '/hooks/' in source:
                    imports['hooks'].append(source)
                elif '/components/' in source:
                    imports['components'].append(source)
                elif '/utils/' in source or '/helpers/' in source:
                    imports['utils'].append(source)
            else:
                imports['packages'].append(source)

        return imports

    def analyze_function_body(self, content: str, func_start: int, func_name: str) -> Dict[str, Any]:
        """Analyse le corps d'une fonction pour détecter des patterns"""
        # Trouver la fin approximative de la fonction (simplifi é)
        func_end = min(func_start + 3000, len(content))
        body = content[func_start:func_end]

        analysis = {
            'uses_state': bool(re.search(r'useState|useReducer', body)),
            'uses_effect': bool(re.search(r'useEffect|useLayoutEffect', body)),
            'uses_ref': bool(re.search(r'useRef|useCallback|useMemo', body)),
            'uses_context': bool(re.search(r'useContext|createContext', body)),
            'uses_query': bool(re.search(r'useQuery|useMutation|useQueryClient', body)),
            'has_jsx': bool(re.search(r'<\w+[>\s]|<\/\w+>', body)),
            'is_async': 'async' in body[:100],
            'calls_api': any(re.search(pattern, body) for pattern in self.api_patterns),
            'event_handlers': len(re.findall(r'on[A-Z]\w+', body)),
            'has_conditional_rendering': bool(re.search(r'\?\s*<|&&\s*<', body)),
            'complexity_score': self.estimate_complexity(body),
        }

        return analysis

    def estimate_complexity(self, body: str) -> int:
        """Estime la complexité cyclomatique approximative"""
        complexity = 1  # Base

        # Ajouter pour chaque structure conditionnelle
        complexity += len(re.findall(r'\bif\b', body))
        complexity += len(re.findall(r'\belse\s+if\b', body))
        complexity += len(re.findall(r'\bfor\b', body))
        complexity += len(re.findall(r'\bwhile\b', body))
        complexity += len(re.findall(r'\bswitch\b', body))
        complexity += len(re.findall(r'\bcase\b', body))
        complexity += len(re.findall(r'\bcatch\b', body))
        complexity += len(re.findall(r'\?\s*.*\s*:', body))  # Ternaires
        complexity += len(re.findall(r'&&|\|\|', body)) // 2  # Opérateurs logiques

        return complexity

    def extract_props_from_destructuring(self, params: str) -> List[Dict]:
        """Extrait les props depuis une destructuration"""
        props = []

        # Pattern pour { prop1, prop2, prop3 = default }
        destructure_match = re.search(r'\{\s*([^}]+)\s*\}', params)
        if destructure_match:
            props_str = destructure_match.group(1)
            for prop in props_str.split(','):
                prop = prop.strip()
                if not prop:
                    continue

                # Avec valeur par défaut
                if '=' in prop:
                    name, default = prop.split('=', 1)
                    name = name.strip()
                    default = default.strip()
                    props.append({
                        "name": name,
                        "type": self.infer_type_from_default(default),
                        "default": default,
                        "required": False
                    })
                # Avec renommage (prop: newName)
                elif ':' in prop:
                    old_name, new_name = prop.split(':', 1)
                    props.append({
                        "name": old_name.strip(),
                        "alias": new_name.strip(),
                        "type": "any",
                        "required": True
                    })
                else:
                    props.append({
                        "name": prop,
                        "type": "any",
                        "required": True
                    })

        return props

    def infer_type_from_default(self, default: str) -> str:
        """Infère le type depuis une valeur par défaut"""
        default = default.strip()

        if default in ['true', 'false']:
            return 'boolean'
        elif default in ['null', 'undefined']:
            return 'any'
        elif default == '[]':
            return 'array'
        elif default == '{}':
            return 'object'
        elif default.startswith("'") or default.startswith('"'):
            return 'string'
        elif default.isdigit() or re.match(r'-?\d+\.?\d*', default):
            return 'number'
        elif default.startswith('()'):
            return 'function'
        else:
            return 'any'

    def categorize_advanced(self, name: str, file_path: str, imports: Dict, body_analysis: Dict, jsdoc: str) -> str:
        """Catégorisation avancée basée sur tous les indices"""
        file_lower = file_path.lower()
        name_lower = name.lower()

        # Custom Hooks
        if name.startswith('use'):
            if body_analysis['uses_query'] or any('react-query' in pkg or 'tanstack' in pkg for pkg in imports['packages']):
                return "Hooks/Data Fetching"
            elif body_analysis['uses_state'] or body_analysis['uses_context']:
                return "Hooks/State Management"
            elif body_analysis['event_handlers'] > 0:
                return "Hooks/UI Interaction"
            elif any(x in name_lower for x in ['debounce', 'throttle', 'local', 'session', 'storage']):
                return "Hooks/Utilities"
            elif 'accessibility' in file_lower or 'a11y' in file_lower:
                return "Hooks/Accessibility"
            elif any(x in name_lower for x in ['offline', 'online', 'network']):
                return "Hooks/Network"
            elif any(x in name_lower for x in ['media', 'breakpoint', 'viewport']):
                return "Hooks/Responsive"
            else:
                return "Hooks/Custom"

        # Components React (nom commence par majuscule)
        if name[0].isupper() and body_analysis['has_jsx']:
            if 'modal' in name_lower or 'dialog' in name_lower or 'drawer' in name_lower:
                return "Components/Overlays"
            elif 'toast' in name_lower or 'notification' in name_lower or 'alert' in name_lower:
                return "Components/Feedback"
            elif 'loading' in name_lower or 'skeleton' in name_lower or 'spinner' in name_lower:
                return "Components/Loading"
            elif 'table' in name_lower or 'datagrid' in name_lower or 'list' in name_lower:
                return "Components/Data Display"
            elif 'form' in name_lower or 'input' in name_lower or 'select' in name_lower or 'checkbox' in name_lower:
                return "Components/Forms"
            elif 'button' in name_lower or 'icon' in name_lower or 'badge' in name_lower or 'chip' in name_lower:
                return "Components/UI Elements"
            elif 'layout' in file_lower or 'page' in name_lower or 'shell' in name_lower or 'wrapper' in name_lower:
                return "Components/Layout"
            elif 'card' in name_lower or 'panel' in name_lower:
                return "Components/Containers"
            elif 'nav' in name_lower or 'menu' in name_lower or 'sidebar' in name_lower:
                return "Components/Navigation"
            elif 'animation' in file_lower or 'transition' in name_lower:
                return "Components/Animation"
            elif 'chart' in name_lower or 'graph' in name_lower or 'visualization' in name_lower:
                return "Components/Charts"
            else:
                return "Components/Generic"

        # API Functions
        if body_analysis['calls_api'] or body_analysis['is_async']:
            if 'api' in file_lower or 'client' in file_lower:
                if any(x in name_lower for x in ['fetch', 'get', 'search', 'find']):
                    return "API/Read"
                elif any(x in name_lower for x in ['create', 'post', 'add']):
                    return "API/Create"
                elif any(x in name_lower for x in ['update', 'patch', 'put', 'edit']):
                    return "API/Update"
                elif any(x in name_lower for x in ['delete', 'remove', 'destroy']):
                    return "API/Delete"
                else:
                    return "API/Client"

        # Utils/Helpers
        if 'utils' in file_lower or 'helpers' in file_lower or 'lib' in file_lower:
            if any(x in name_lower for x in ['format', 'parse', 'transform', 'convert']):
                return "Utils/Formatting"
            elif any(x in name_lower for x in ['validate', 'check', 'verify', 'is', 'has']):
                return "Utils/Validation"
            elif any(x in name_lower for x in ['calculate', 'compute', 'aggregate', 'sum', 'count']):
                return "Utils/Calculation"
            elif any(x in name_lower for x in ['sort', 'filter', 'map', 'reduce', 'find']):
                return "Utils/Array"
            elif any(x in name_lower for x in ['date', 'time', 'duration']):
                return "Utils/DateTime"
            elif any(x in name_lower for x in ['currency', 'money', 'price']):
                return "Utils/Currency"
            else:
                return "Utils/Generic"

        # Context
        if 'context' in file_lower or 'provider' in name_lower or body_analysis['uses_context']:
            return "Context/Providers"

        # Event Handlers
        if name.startswith('on') or name.startswith('handle'):
            return "Handlers/Events"

        # Pages/Features
        if 'page' in file_lower and name.endswith('Page'):
            module = self.extract_module_from_path(file_path)
            if module:
                return f"Pages/{module}"
            return "Pages/Generic"

        return "Uncategorized"

    def extract_module_from_path(self, file_path: str) -> str:
        """Extrait le module principal depuis le chemin"""
        parts = file_path.split('/')
        if 'features' in parts:
            idx = parts.index('features')
            if idx + 1 < len(parts):
                return parts[idx + 1].capitalize()
        elif 'modules' in parts:
            idx = parts.index('modules')
            if idx + 1 < len(parts):
                return parts[idx + 1].capitalize()
        return ""

    def assess_reusability_advanced(self, name: str, func_type: str, file_path: str,
                                    imports: Dict, body_analysis: Dict, is_exported: bool) -> Tuple[str, int]:
        """Évalue la réutilisabilité avec un score détaillé"""
        score = 0
        reasons = []

        # Hooks personnalisés = haute réutilisabilité
        if name.startswith('use'):
            score += 3
            reasons.append("Custom hook")

        # Dans des dossiers génériques
        if any(x in file_path.lower() for x in ['utils', 'hooks', 'helpers', 'lib']):
            score += 2
            reasons.append("In reusable directory")

        # Dans components/ui = haute réutilisabilité
        if 'components/ui' in file_path.lower():
            score += 3
            reasons.append("UI component")

        # Exporté
        if is_exported:
            score += 1
            reasons.append("Exported")

        # Pas de dépendances complexes
        if len(imports['packages']) <= 2:
            score += 1
            reasons.append("Few dependencies")

        # Fonction pure (peu de hooks, pas d'effects)
        if not body_analysis['uses_effect'] and body_analysis['complexity_score'] < 5:
            score += 1
            reasons.append("Low complexity")

        # Nom générique
        generic_names = ['format', 'parse', 'validate', 'calculate', 'fetch', 'get', 'set', 'update',
                         'create', 'delete', 'transform', 'convert', 'filter', 'sort']
        if any(x in name.lower() for x in generic_names):
            score += 1
            reasons.append("Generic name")

        # Pas spécifique à une feature
        if not any(x in file_path.lower() for x in ['features/', 'pages/']):
            score += 1
            reasons.append("Not feature-specific")

        if score >= 7:
            level = "High"
        elif score >= 4:
            level = "Medium"
        else:
            level = "Low"

        return level, score

    def extract_jsdoc_details(self, jsdoc: str) -> Dict:
        """Extrait tous les détails du JSDoc"""
        if not jsdoc:
            return {}

        details = {
            'description': '',
            'params': [],
            'returns': None,
            'example': '',
            'deprecated': False,
            'since': None,
            'see': []
        }

        lines = jsdoc.split('\n')
        current_section = 'description'
        desc_lines = []

        for line in lines:
            clean = line.strip().lstrip('*').strip()
            if not clean:
                continue

            if clean.startswith('@param'):
                match = re.match(r'@param\s+{([^}]+)}\s+(\w+)\s*-?\s*(.*)', clean)
                if match:
                    details['params'].append({
                        'type': match.group(1),
                        'name': match.group(2),
                        'description': match.group(3)
                    })
            elif clean.startswith('@returns') or clean.startswith('@return'):
                match = re.match(r'@returns?\s+{([^}]+)}\s*-?\s*(.*)', clean)
                if match:
                    details['returns'] = {
                        'type': match.group(1),
                        'description': match.group(2)
                    }
            elif clean.startswith('@example'):
                current_section = 'example'
            elif clean.startswith('@deprecated'):
                details['deprecated'] = True
            elif clean.startswith('@since'):
                details['since'] = clean.replace('@since', '').strip()
            elif clean.startswith('@see'):
                details['see'].append(clean.replace('@see', '').strip())
            elif current_section == 'description' and not clean.startswith('@'):
                desc_lines.append(clean)
            elif current_section == 'example':
                details['example'] += clean + '\n'

        details['description'] = ' '.join(desc_lines)
        return details

    def analyze_file(self, file_path: Path):
        """Analyse un fichier avec détection avancée"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            return

        relative_path = str(file_path.relative_to(self.src_dir.parent))
        imports = self.extract_imports(content)

        # Patterns avancés pour tous types de fonctions
        patterns = [
            # Function declarations
            (r'(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', 'function'),
            # Arrow functions (export const)
            (r'export\s+const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', 'arrow function'),
            # Arrow functions (const)
            (r'(?:^|\n)\s*const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', 'arrow function'),
            # Arrow functions (let/var)
            (r'(?:let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', 'arrow function'),
        ]

        for pattern, func_type in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                params = match.group(2) if len(match.groups()) > 1 else ""
                func_start = match.start()

                # Analyser le corps de la fonction
                body_analysis = self.analyze_function_body(content, func_start, name)

                # Détecter le type de fonction
                detected_type = func_type
                if name.startswith('use') and name[3].isupper():
                    detected_type = 'custom hook'
                elif name[0].isupper() and body_analysis['has_jsx']:
                    detected_type = 'React component'

                # Extraire JSDoc
                jsdoc = self.extract_jsdoc(content, func_start)
                jsdoc_details = self.extract_jsdoc_details(jsdoc)

                # Catégorisation avancée
                category = self.categorize_advanced(name, relative_path, imports, body_analysis, jsdoc)

                # Évaluer réutilisabilité
                is_exported = 'export' in content[max(0, func_start-100):func_start+100]
                reusability, score = self.assess_reusability_advanced(
                    name, detected_type, relative_path, imports, body_analysis, is_exported
                )

                # Extraire paramètres
                parameters = self.extract_props_from_destructuring(params) if '{' in params else []

                # Si pas de props destructurées, parser normalement
                if not parameters and params.strip():
                    for p in params.split(','):
                        p = p.strip()
                        if p:
                            parameters.append({
                                "name": p.split('=')[0].strip(),
                                "type": "any",
                                "default": p.split('=')[1].strip() if '=' in p else None,
                                "required": '=' not in p
                            })

                func_info = {
                    "name": name,
                    "file": relative_path,
                    "type": detected_type,
                    "signature": f"{name}({params})",
                    "parameters": parameters,
                    "category": category,
                    "description": jsdoc_details.get('description', ''),
                    "dependencies": imports,
                    "body_analysis": body_analysis,
                    "jsdoc_full": jsdoc_details,
                    "reusability": reusability,
                    "reusability_score": score,
                    "is_exported": is_exported,
                    "is_async": body_analysis['is_async'],
                    "complexity_score": body_analysis['complexity_score'],
                    "loc_estimate": len(content[func_start:min(func_start+5000, len(content))].split('\n')),
                }

                func_id = f"{relative_path}::{name}"
                self.catalog["functions_flat"][func_id] = func_info

    def extract_jsdoc(self, content: str, func_start: int) -> str:
        """Extrait le JSDoc précédant une fonction"""
        before = content[max(0, func_start-800):func_start]
        jsdoc_match = re.search(r'/\*\*(.*?)\*/', before, re.DOTALL)
        if jsdoc_match:
            return jsdoc_match.group(0)
        return ""

    def generate_statistics(self):
        """Génère des statistiques détaillées"""
        categories = Counter()
        types = Counter()
        reusability = Counter()
        complexity_dist = Counter()

        for func in self.catalog["functions_flat"].values():
            categories[func["category"]] += 1
            types[func["type"]] += 1
            reusability[func["reusability"]] += 1

            # Distribution de complexité
            complexity = func.get("complexity_score", 0)
            if complexity < 5:
                complexity_dist["Low"] += 1
            elif complexity < 10:
                complexity_dist["Medium"] += 1
            else:
                complexity_dist["High"] += 1

        self.catalog["metadata"]["total_functions"] = len(self.catalog["functions_flat"])
        self.catalog["metadata"]["categories"] = dict(categories)
        self.catalog["metadata"]["types"] = dict(types)
        self.catalog["metadata"]["reusability"] = dict(reusability)
        self.catalog["metadata"]["complexity_distribution"] = dict(complexity_dist)

    def reorganize_by_category(self):
        """Réorganise par catégorie"""
        by_category = defaultdict(list)

        for func_id, func in self.catalog["functions_flat"].items():
            category = func["category"]
            by_category[category].append(func)

        # Trier par nom dans chaque catégorie
        for category in by_category:
            by_category[category].sort(key=lambda x: x["name"])

        return dict(by_category)

    def save_catalog(self, output_path: str):
        """Sauvegarde le catalogue"""
        from datetime import datetime

        self.catalog["metadata"]["analyzed_at"] = datetime.now().isoformat()
        self.generate_statistics()
        self.catalog["functions_by_category"] = self.reorganize_by_category()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.catalog, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Catalogue sauvegardé: {output_path}")
        print(f"  📊 {self.catalog['metadata']['total_files']} fichiers analysés")
        print(f"  🔧 {self.catalog['metadata']['total_functions']} fonctions trouvées")
        print(f"\n  📂 Répartition par catégorie:")
        for cat, count in sorted(self.catalog["metadata"]["categories"].items(), key=lambda x: -x[1])[:20]:
            print(f"    • {cat}: {count}")

        print(f"\n  🎯 Réutilisabilité:")
        for level, count in self.catalog["metadata"]["reusability"].items():
            print(f"    • {level}: {count}")

        print(f"\n  📈 Complexité:")
        for level, count in self.catalog["metadata"]["complexity_distribution"].items():
            print(f"    • {level}: {count}")


if __name__ == "__main__":
    src_dir = "/home/ruuuzer/Documents/monprojet/frontend/src"
    output_path = "/home/ruuuzer/Documents/monprojet/docs/library/javascript_functions_catalog.json"

    print("🔍 Analyse AVANCÉE des fonctions JavaScript/React...")
    print(f"📁 Répertoire: {src_dir}\n")

    analyzer = AdvancedJSFunctionAnalyzer(src_dir)
    analyzer.analyze_all_files()
    analyzer.save_catalog(output_path)

    print("\n✅ Analyse terminée!")
