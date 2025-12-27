#!/usr/bin/env python3
"""
Script d'analyse exhaustive des fonctions Python.
Extrait toutes les fonctions avec leurs métadonnées complètes.
"""

import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Optional
from dataclasses import dataclass, asdict


@dataclass
class FunctionInfo:
    """Information complète sur une fonction."""
    name: str
    file_path: str
    line_number: int
    signature: str
    category: str
    description: str
    dependencies: List[str]
    reusability: str
    is_async: bool
    is_method: bool
    is_decorator: bool
    decorators: List[str]
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]


class FunctionAnalyzer(ast.NodeVisitor):
    """Analyseur AST pour extraire les informations des fonctions."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.functions: List[FunctionInfo] = []
        self.imports: Set[str] = set()
        self.current_class = None

    def visit_Import(self, node: ast.Import):
        """Extrait les imports."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Extrait les imports from."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visite les classes pour marquer les méthodes."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extrait les informations d'une fonction."""
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Extrait les informations d'une fonction async."""
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def _process_function(self, node, is_async: bool):
        """Traite une fonction et extrait toutes ses métadonnées."""

        # Ignorer les fonctions privées imbriquées
        if node.name.startswith('_') and self.current_class is None:
            # Garder seulement __init__, __str__, etc.
            if not (node.name.startswith('__') and node.name.endswith('__')):
                return

        # Extraire la signature
        signature = self._extract_signature(node)

        # Extraire la docstring
        docstring = ast.get_docstring(node) or ""
        description = self._extract_description(docstring)

        # Extraire les paramètres
        parameters = self._extract_parameters(node)

        # Extraire le type de retour
        return_type = self._extract_return_type(node)

        # Extraire les décorateurs
        decorators = self._extract_decorators(node)

        # Déterminer les dépendances
        dependencies = self._extract_dependencies(node)

        # Catégoriser la fonction
        category = self._categorize_function(node, docstring, self.file_path)

        # Évaluer la réutilisabilité
        reusability = self._assess_reusability(node, dependencies)

        # Détecter si c'est un décorateur
        is_decorator = self._is_decorator_function(node)

        func_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            signature=signature,
            category=category,
            description=description,
            dependencies=dependencies,
            reusability=reusability,
            is_async=is_async,
            is_method=self.current_class is not None,
            is_decorator=is_decorator,
            decorators=decorators,
            parameters=parameters,
            return_type=return_type
        )

        self.functions.append(func_info)

    def _extract_signature(self, node) -> str:
        """Extrait la signature complète de la fonction."""
        try:
            # Récupérer les lignes du code source
            start = node.lineno - 1
            # Trouver la fin de la signature (ligne avec ':')
            end = start
            while end < len(self.source_lines):
                line = self.source_lines[end]
                if ':' in line and 'def ' in self.source_lines[start]:
                    break
                end += 1

            signature_lines = self.source_lines[start:end+1]
            signature = ' '.join(line.strip() for line in signature_lines)

            # Nettoyer la signature
            signature = re.sub(r'\s+', ' ', signature)
            return signature
        except:
            # Fallback basique
            params = ', '.join(arg.arg for arg in node.args.args)
            return f"def {node.name}({params})"

    def _extract_description(self, docstring: str) -> str:
        """Extrait une description courte de la docstring."""
        if not docstring:
            return "No description available"

        # Prendre la première phrase ou ligne non vide
        lines = docstring.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Args:', 'Returns:', 'Raises:', 'Example:')):
                # Limiter à 200 caractères
                return line[:200] + ('...' if len(line) > 200 else '')

        return docstring[:200]

    def _extract_parameters(self, node) -> List[Dict[str, Any]]:
        """Extrait les informations sur les paramètres."""
        params = []

        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': None
            }
            params.append(param_info)

        # Ajouter les valeurs par défaut
        defaults = node.args.defaults
        if defaults:
            # Les defaults s'appliquent aux derniers paramètres
            offset = len(params) - len(defaults)
            for i, default in enumerate(defaults):
                try:
                    params[offset + i]['default'] = ast.unparse(default)
                except:
                    params[offset + i]['default'] = '<complex default>'

        return params

    def _extract_return_type(self, node) -> Optional[str]:
        """Extrait le type de retour annoté."""
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except:
                return None
        return None

    def _extract_decorators(self, node) -> List[str]:
        """Extrait la liste des décorateurs."""
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except:
                decorators.append('<unknown>')
        return decorators

    def _extract_dependencies(self, node) -> List[str]:
        """Extrait les dépendances (imports utilisés dans la fonction)."""
        deps = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                # Vérifier si c'est un import connu
                for imp in self.imports:
                    if child.id in imp or imp.endswith(f'.{child.id}'):
                        deps.add(imp)

        return sorted(list(deps))

    def _categorize_function(self, node, docstring: str, file_path: str) -> str:
        """Catégorise la fonction selon son rôle."""

        name_lower = node.name.lower()
        doc_lower = docstring.lower()
        path_lower = file_path.lower()

        # Catégories basées sur le chemin
        if 'api/' in path_lower or 'routes' in path_lower:
            return 'API'
        if 'database' in path_lower or 'repositories' in path_lower or 'db' in path_lower:
            return 'Database'
        if 'auth' in path_lower or 'authentication' in path_lower:
            return 'Authentication'
        if 'cache' in path_lower:
            return 'Cache'
        if 'finance' in path_lower:
            return 'Finance'
        if 'restaurant' in path_lower:
            return 'Restaurant'
        if 'invoice' in path_lower or 'facture' in path_lower:
            return 'Invoicing'
        if 'service' in path_lower:
            return 'Business Logic'
        if 'middleware' in path_lower:
            return 'Middleware'
        if 'task' in path_lower or 'worker' in path_lower:
            return 'Background Tasks'
        if 'schema' in path_lower:
            return 'Data Schema'
        if 'util' in path_lower or 'helper' in path_lower:
            return 'Utilities'

        # Catégories basées sur le nom
        if any(x in name_lower for x in ['get_', 'fetch_', 'load_', 'read_', 'retrieve_']):
            return 'Data Retrieval'
        if any(x in name_lower for x in ['create_', 'insert_', 'add_', 'save_', 'store_']):
            return 'Data Creation'
        if any(x in name_lower for x in ['update_', 'modify_', 'change_', 'edit_']):
            return 'Data Update'
        if any(x in name_lower for x in ['delete_', 'remove_', 'drop_']):
            return 'Data Deletion'
        if any(x in name_lower for x in ['validate_', 'check_', 'verify_', 'ensure_']):
            return 'Validation'
        if any(x in name_lower for x in ['calculate_', 'compute_', 'sum_', 'total_']):
            return 'Calculation'
        if any(x in name_lower for x in ['format_', 'render_', 'serialize_', 'parse_']):
            return 'Formatting'
        if any(x in name_lower for x in ['normalize_', 'clean_', 'sanitize_']):
            return 'Data Normalization'
        if 'cache' in name_lower:
            return 'Cache'
        if 'auth' in name_lower or 'login' in name_lower or 'token' in name_lower:
            return 'Authentication'

        # Catégories basées sur la docstring
        if any(x in doc_lower for x in ['database', 'query', 'sql']):
            return 'Database'
        if any(x in doc_lower for x in ['api', 'endpoint', 'route']):
            return 'API'
        if any(x in doc_lower for x in ['cache', 'redis']):
            return 'Cache'
        if any(x in doc_lower for x in ['pdf', 'document']):
            return 'Document Processing'
        if any(x in doc_lower for x in ['email', 'mail']):
            return 'Communication'

        return 'General'

    def _assess_reusability(self, node, dependencies: List[str]) -> str:
        """Évalue le niveau de réutilisabilité de la fonction."""

        # Critères de haute réutilisabilité:
        # - Pas de dépendances externes complexes
        # - Fonction pure (pas d'effets de bord évidents)
        # - Paramètres bien typés
        # - Pas de références à des globals ou des singletons

        score = 0

        # Bonus si la fonction a des annotations de type
        if node.args.args and any(arg.annotation for arg in node.args.args):
            score += 2

        if node.returns:
            score += 1

        # Malus si beaucoup de dépendances
        if len(dependencies) > 5:
            score -= 2
        elif len(dependencies) > 2:
            score -= 1

        # Malus si la fonction accède à des globals
        has_global = False
        for child in ast.walk(node):
            if isinstance(child, ast.Global):
                has_global = True
                score -= 2
                break

        # Bonus si c'est une fonction courte (moins de 50 lignes)
        if hasattr(node, 'end_lineno'):
            lines = node.end_lineno - node.lineno
            if lines < 20:
                score += 2
            elif lines < 50:
                score += 1
            elif lines > 100:
                score -= 1

        # Malus si c'est une méthode de classe (dépend de l'état)
        if self.current_class:
            score -= 1

        if score >= 3:
            return 'High'
        elif score >= 0:
            return 'Medium'
        else:
            return 'Low'

    def _is_decorator_function(self, node) -> bool:
        """Détecte si la fonction est un décorateur."""
        # Un décorateur retourne typiquement une fonction
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if isinstance(child.value, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    return True
                # Chercher des patterns comme "return wrapper"
                if isinstance(child.value, ast.Name):
                    return True

        # Vérifier si la fonction contient une fonction imbriquée
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return True

        return False


def analyze_file(file_path: str, base_path: str) -> List[FunctionInfo]:
    """Analyse un fichier Python et retourne toutes les fonctions trouvées."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Parser le code
        tree = ast.parse(source_code)

        # Analyser
        relative_path = os.path.relpath(file_path, base_path)
        analyzer = FunctionAnalyzer(relative_path, source_code)
        analyzer.visit(tree)

        return analyzer.functions

    except SyntaxError as e:
        print(f"  Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"  Error analyzing {file_path}: {e}")
        return []


def find_python_files(root_dirs: List[str]) -> List[str]:
    """Trouve tous les fichiers Python dans les répertoires donnés."""
    python_files = []

    for root_dir in root_dirs:
        for root, dirs, files in os.walk(root_dir):
            # Exclure certains répertoires
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]

            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    full_path = os.path.join(root, file)
                    python_files.append(full_path)

    return sorted(python_files)


def main():
    """Fonction principale."""

    base_path = '/home/ruuuzer/Documents/monprojet'
    backend_path = os.path.join(base_path, 'backend')
    core_path = os.path.join(base_path, 'core')

    print("=" * 80)
    print("ANALYSE EXHAUSTIVE DES FONCTIONS PYTHON")
    print("=" * 80)
    print()

    # Trouver tous les fichiers
    print("Recherche des fichiers Python...")
    python_files = find_python_files([backend_path, core_path])
    print(f"  Trouvé {len(python_files)} fichiers Python\n")

    # Analyser chaque fichier
    all_functions: List[FunctionInfo] = []

    print("Analyse en cours...")
    for i, file_path in enumerate(python_files, 1):
        relative = os.path.relpath(file_path, base_path)
        print(f"  [{i}/{len(python_files)}] {relative}")

        functions = analyze_file(file_path, base_path)
        all_functions.extend(functions)

    print(f"\nTrouvé {len(all_functions)} fonctions au total\n")

    # Organiser par catégorie
    by_category: Dict[str, List[Dict[str, Any]]] = {}

    for func in all_functions:
        func_dict = asdict(func)
        category = func.category

        if category not in by_category:
            by_category[category] = []

        by_category[category].append(func_dict)

    # Trier chaque catégorie
    for category in by_category:
        by_category[category].sort(key=lambda x: (x['file_path'], x['line_number']))

    # Créer le résultat final
    result = {
        'metadata': {
            'total_functions': len(all_functions),
            'total_files': len(python_files),
            'categories': list(by_category.keys()),
            'base_path': base_path
        },
        'statistics': {
            'by_category': {cat: len(funcs) for cat, funcs in by_category.items()},
            'async_functions': sum(1 for f in all_functions if f.is_async),
            'class_methods': sum(1 for f in all_functions if f.is_method),
            'decorators': sum(1 for f in all_functions if f.is_decorator),
            'high_reusability': sum(1 for f in all_functions if f.reusability == 'High'),
        },
        'functions_by_category': by_category
    }

    # Écrire le résultat
    output_dir = os.path.join(base_path, 'docs', 'library')
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'python_functions_catalog.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Fonctions totales:        {result['metadata']['total_functions']}")
    print(f"Fichiers analysés:        {result['metadata']['total_files']}")
    print(f"Catégories:               {len(by_category)}")
    print(f"Fonctions async:          {result['statistics']['async_functions']}")
    print(f"Méthodes de classe:       {result['statistics']['class_methods']}")
    print(f"Décorateurs:              {result['statistics']['decorators']}")
    print(f"Haute réutilisabilité:    {result['statistics']['high_reusability']}")
    print()
    print("Top 10 catégories:")
    top_cats = sorted(result['statistics']['by_category'].items(), key=lambda x: x[1], reverse=True)[:10]
    for cat, count in top_cats:
        print(f"  {cat:.<30} {count:>4}")
    print()
    print(f"Résultat écrit dans: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
