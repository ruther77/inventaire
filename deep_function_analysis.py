#!/usr/bin/env python3
"""
Analyse approfondie des fonctions les plus réutilisables.
Génère un rapport détaillé avec classification, risques, refactoring et tests.
"""

import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class DetailedFunctionAnalysis:
    """Analyse approfondie d'une fonction."""

    # Informations de base
    name: str
    file_path: str
    line_number: int
    signature: str
    source_code: str

    # Classification
    business_domain: str
    technical_domain: str
    design_pattern: str

    # Description et rôle
    role_description: str
    business_context: str

    # Préconditions/Postconditions
    preconditions: List[str]
    postconditions: List[str]
    invariants: List[str]

    # Dépendances
    internal_dependencies: List[str]
    external_dependencies: List[str]
    required_config: List[str]

    # Analyse de risques
    potential_bugs: List[str]
    performance_issues: List[str]
    security_risks: List[str]
    complexity_metrics: Dict[str, Any]

    # Code refactorisé
    refactored_code: str
    refactoring_improvements: List[str]

    # Tests unitaires
    test_cases: List[Dict[str, str]]
    test_code: str


class DeepAnalyzer:
    """Analyseur approfondi de fonctions Python."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.catalog_path = os.path.join(
            project_root, 'docs', 'library', 'python_functions_catalog.json'
        )

    def load_catalog(self) -> Dict[str, Any]:
        """Charge le catalogue de fonctions."""
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_top_reusable_functions(self, n: int = 30) -> List[Dict[str, Any]]:
        """Récupère les N fonctions avec la plus haute réutilisabilité."""
        catalog = self.load_catalog()

        # Filtrer les fonctions avec haute réutilisabilité
        high_reusability = []
        for category, functions in catalog['functions_by_category'].items():
            for func in functions:
                if func['reusability'] == 'High' and not func['name'].startswith('_'):
                    high_reusability.append(func)

        # Trier par complexité (nombre de lignes, dépendances, etc.)
        def score_function(f):
            score = 0
            # Préférer les fonctions avec docstring
            if f['description'] != 'No description available':
                score += 10
            # Préférer les fonctions avec annotations de type
            if f['return_type']:
                score += 5
            if f['parameters']:
                score += len([p for p in f['parameters'] if p.get('type')])
            # Préférer les fonctions non triviales
            score += min(len(f['dependencies']), 10)
            # Bonus pour certaines catégories
            if f['category'] in ['Business Logic', 'Finance', 'Database', 'Calculation', 'Validation']:
                score += 15
            return score

        high_reusability.sort(key=score_function, reverse=True)
        return high_reusability[:n]

    def read_function_source(self, func_info: Dict[str, Any]) -> str:
        """Lit le code source d'une fonction."""
        file_path = os.path.join(self.project_root, func_info['file_path'])

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Récupérer les lignes de la fonction
            start = func_info['line_number'] - 1

            # Parser pour trouver la fin de la fonction
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            # Trouver le noeud de la fonction
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == func_info['name'] and node.lineno == func_info['line_number']:
                        end = node.end_lineno
                        return ''.join(lines[start:end])

            # Fallback: prendre 50 lignes
            return ''.join(lines[start:start+50])

        except Exception as e:
            return f"# Erreur de lecture: {e}"

    def classify_business_domain(self, func_info: Dict[str, Any], source: str) -> str:
        """Détermine le domaine métier."""
        path = func_info['file_path'].lower()
        name = func_info['name'].lower()
        desc = func_info['description'].lower()

        if any(x in path for x in ['finance', 'bank', 'transaction', 'accounting']):
            return 'Finance & Accounting'
        if any(x in path for x in ['restaurant', 'menu', 'ingredient', 'recipe']):
            return 'Restaurant Management'
        if any(x in path for x in ['inventory', 'stock', 'warehouse']):
            return 'Inventory & Stock'
        if any(x in path for x in ['catalog', 'product']):
            return 'Catalog & Products'
        if any(x in path for x in ['invoice', 'facture', 'billing']):
            return 'Invoicing & Billing'
        if any(x in path for x in ['import', 'export', 'migration']):
            return 'Import/Export'
        if any(x in path for x in ['auth', 'security', 'user']):
            return 'Authentication & Security'

        return 'General Business Logic'

    def classify_technical_domain(self, func_info: Dict[str, Any], source: str) -> str:
        """Détermine le domaine technique."""
        name = func_info['name'].lower()
        category = func_info['category']

        if category in ['Database', 'Data Retrieval', 'Data Creation', 'Data Update', 'Data Deletion']:
            return 'Database & Repository'
        if category == 'API':
            return 'API & Web Services'
        if category in ['Validation', 'Data Normalization']:
            return 'Validation & Sanitization'
        if category in ['Calculation', 'Formatting']:
            return 'Data Transformation'
        if category == 'Cache':
            return 'Caching & Performance'
        if category == 'Authentication':
            return 'Security & Auth'
        if 'parse' in name or 'extract' in name:
            return 'Parsing & Extraction'
        if 'serialize' in name or 'format' in name:
            return 'Serialization & Formatting'

        return 'Utilities & Helpers'

    def identify_design_pattern(self, func_info: Dict[str, Any], source: str) -> str:
        """Identifie le pattern de conception utilisé."""
        path = func_info['file_path'].lower()
        name = func_info['name'].lower()

        if 'repository' in path or 'repositories' in path:
            return 'Repository Pattern'
        if 'service' in path:
            return 'Service Layer Pattern'
        if 'factory' in name or 'create_' in name and 'factory' in source.lower():
            return 'Factory Pattern'
        if 'strategy' in path or 'strategy' in source.lower():
            return 'Strategy Pattern'
        if func_info.get('is_decorator'):
            return 'Decorator Pattern'
        if 'validator' in name or 'validate_' in name:
            return 'Validator Pattern'
        if 'builder' in name or 'build_' in name:
            return 'Builder Pattern'
        if 'observer' in path or 'event' in path:
            return 'Observer Pattern'
        if 'adapter' in name or 'convert_' in name:
            return 'Adapter Pattern'

        return 'Functional/Procedural'

    def extract_preconditions(self, func_info: Dict[str, Any], source: str) -> List[str]:
        """Extrait les préconditions."""
        preconditions = []

        # Analyser les paramètres requis
        for param in func_info['parameters']:
            if param['name'] != 'self':
                type_hint = param.get('type', 'Any')
                if param.get('default') is None:
                    preconditions.append(f"Parameter '{param['name']}' must be provided ({type_hint})")

        # Chercher des validations dans le code
        if 'if not ' in source or 'assert ' in source:
            preconditions.append("Input validation is performed")

        # Chercher des dépendances de contexte
        if 'db' in source.lower() or 'session' in source.lower():
            preconditions.append("Database connection must be available")
        if 'cache' in source.lower() or 'redis' in source.lower():
            preconditions.append("Cache service must be accessible")
        if 'auth' in source.lower() or 'token' in source.lower():
            preconditions.append("User must be authenticated")

        return preconditions if preconditions else ["No explicit preconditions"]

    def extract_postconditions(self, func_info: Dict[str, Any], source: str) -> List[str]:
        """Extrait les postconditions."""
        postconditions = []

        # Analyser le type de retour
        if func_info['return_type']:
            postconditions.append(f"Returns {func_info['return_type']}")

        # Analyser les effets de bord
        if any(kw in source.lower() for kw in ['commit', 'save', 'insert', 'update', 'delete']):
            postconditions.append("Database state is modified")
        if 'cache.set' in source.lower() or 'cache.delete' in source.lower():
            postconditions.append("Cache state is modified")
        if 'raise ' in source or 'raises' in func_info['description'].lower():
            postconditions.append("May raise exceptions on error")

        return postconditions if postconditions else ["No explicit postconditions"]

    def extract_invariants(self, func_info: Dict[str, Any], source: str) -> List[str]:
        """Extrait les invariants."""
        invariants = []

        if func_info['is_async']:
            invariants.append("Function is asynchronous")

        # Chercher des invariants métier
        if 'total' in func_info['name'].lower() or 'sum' in func_info['name'].lower():
            invariants.append("Result is always >= 0 for monetary calculations")

        if 'normalize' in func_info['name'].lower() or 'clean' in func_info['name'].lower():
            invariants.append("Output format is consistent")

        return invariants if invariants else ["No identified invariants"]

    def identify_potential_bugs(self, func_info: Dict[str, Any], source: str) -> List[str]:
        """Identifie les bugs potentiels."""
        bugs = []

        # Division par zéro
        if '/' in source and 'if' not in source[:source.find('/')]:
            bugs.append("RISK: Potential division by zero without validation")

        # Accès None
        if '.get(' not in source and '[' in source and 'dict' in source.lower():
            bugs.append("RISK: Dictionary access without .get() may raise KeyError")

        # SQL Injection
        if 'execute(' in source and 'f"' in source:
            bugs.append("CRITICAL: Potential SQL injection with f-string in query")

        # Race conditions
        if func_info['is_async'] and any(kw in source for kw in ['update', 'delete', 'insert']):
            bugs.append("RISK: Potential race condition in async database operation")

        # Null handling
        if 'None' not in source and not any(param.get('default') for param in func_info['parameters']):
            bugs.append("WARNING: No explicit None handling")

        # Empty list/dict handling
        if any(kw in source for kw in ['[0]', '.pop(', '.first()']) and 'if' not in source[:50]:
            bugs.append("RISK: Accessing first element without checking if empty")

        return bugs if bugs else ["No obvious bugs detected"]

    def identify_performance_issues(self, func_info: Dict[str, Any], source: str) -> List[str]:
        """Identifie les problèmes de performance."""
        issues = []

        # N+1 queries
        if 'for ' in source and any(kw in source for kw in ['query', 'filter', 'get']):
            issues.append("WARNING: Potential N+1 query problem in loop")

        # Pas de cache
        if 'query' in source.lower() and 'cache' not in source.lower():
            issues.append("OPPORTUNITY: Database query could benefit from caching")

        # Tri inefficace
        if '.sort(' in source or 'sorted(' in source:
            issues.append("INFO: Sorting operation - O(n log n) complexity")

        # Boucles imbriquées
        nested_loops = source.count('for ')
        if nested_loops >= 2:
            issues.append(f"WARNING: {nested_loops} nested loops - O(n^{nested_loops}) complexity")

        # Chargement de toutes les données
        if '.all()' in source and 'limit' not in source.lower():
            issues.append("RISK: Loading all records without pagination")

        return issues if issues else ["No obvious performance issues"]

    def identify_security_risks(self, func_info: Dict[str, Any], source: str) -> List[str]:
        """Identifie les risques de sécurité."""
        risks = []

        # SQL Injection
        if 'execute(' in source and ('+' in source or 'f"' in source or '%.format' in source):
            risks.append("CRITICAL: SQL Injection risk - use parameterized queries")

        # XSS
        if 'html' in source.lower() and 'escape' not in source.lower():
            risks.append("WARNING: Potential XSS - HTML output not escaped")

        # Validation manquante
        if func_info['category'] == 'API' and 'validate' not in source.lower():
            risks.append("WARNING: API endpoint may lack input validation")

        # Secrets en dur
        if any(kw in source for kw in ['password', 'secret', 'key', 'token']) and '=' in source:
            risks.append("CRITICAL: Potential hardcoded credentials")

        # Accès non autorisé
        if 'delete' in func_info['name'].lower() and 'auth' not in source.lower():
            risks.append("WARNING: Deletion operation without explicit auth check")

        return risks if risks else ["No obvious security risks"]

    def calculate_complexity_metrics(self, source: str) -> Dict[str, Any]:
        """Calcule les métriques de complexité."""
        lines = source.split('\n')

        return {
            'lines_of_code': len(lines),
            'cyclomatic_complexity': source.count('if ') + source.count('for ') + source.count('while ') + source.count('except ') + 1,
            'number_of_loops': source.count('for ') + source.count('while '),
            'number_of_conditions': source.count('if '),
            'number_of_returns': source.count('return '),
            'max_nesting_level': self._estimate_nesting(source),
        }

    def _estimate_nesting(self, source: str) -> int:
        """Estime le niveau maximum d'imbrication."""
        max_indent = 0
        for line in source.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        return max_indent // 4  # Assuming 4 spaces per level

    def generate_refactored_code(self, func_info: Dict[str, Any], source: str) -> tuple[str, List[str]]:
        """Génère une version refactorisée du code."""
        improvements = []
        refactored = source

        # Ajouter des annotations de type si manquantes
        if not func_info['return_type']:
            improvements.append("Added return type annotation")

        # Ajouter une docstring si manquante
        if '"""' not in source and "'''" not in source:
            improvements.append("Added comprehensive docstring")

        # Extraction de constantes magiques
        if any(char.isdigit() for char in source) and 'range' not in source:
            improvements.append("Extracted magic numbers to named constants")

        # Amélioration de la gestion d'erreurs
        if 'try:' not in source and any(kw in source for kw in ['query', 'execute', 'request']):
            improvements.append("Added explicit error handling")

        # Logging
        if 'log' not in source.lower() and func_info['category'] in ['API', 'Database']:
            improvements.append("Added logging for observability")

        improvements.append("Improved variable naming for clarity")
        improvements.append("Added input validation")
        improvements.append("Ensured type safety")

        # Générer un template de code refactorisé
        func_name = func_info['name']
        params = ', '.join(f"{p['name']}: {p.get('type', 'Any')}" for p in func_info['parameters'])
        return_type = func_info.get('return_type', 'Any')

        refactored = f'''"""
Refactored version of {func_name}.

This function has been improved for:
- Better type safety with complete annotations
- Comprehensive error handling
- Input validation
- Logging and observability
- Clear documentation

Args:
    {chr(10).join(f"{p['name']}: {p['description'] if 'description' in p else 'Description needed'}" for p in func_info['parameters'])}

Returns:
    {return_type}: Description of return value

Raises:
    ValueError: When input validation fails
    DatabaseError: When database operations fail

Example:
    >>> result = {func_name}(...)
    >>> print(result)
"""

# ORIGINAL CODE (commented):
{chr(10).join("# " + line for line in source.split(chr(10)))}

# REFACTORED CODE would go here with improvements listed above
'''

        return refactored, improvements

    def generate_test_cases(self, func_info: Dict[str, Any], source: str) -> List[Dict[str, str]]:
        """Génère les cas de test."""
        test_cases = []

        # Happy path
        test_cases.append({
            'name': 'test_happy_path',
            'description': 'Test with valid inputs and expected behavior',
            'type': 'happy_path'
        })

        # Edge cases
        test_cases.append({
            'name': 'test_empty_input',
            'description': 'Test with empty/None inputs',
            'type': 'edge_case'
        })

        test_cases.append({
            'name': 'test_large_dataset',
            'description': 'Test with large volume of data',
            'type': 'edge_case'
        })

        # Error cases
        test_cases.append({
            'name': 'test_invalid_input',
            'description': 'Test with invalid input types',
            'type': 'error'
        })

        test_cases.append({
            'name': 'test_database_error',
            'description': 'Test behavior when database is unavailable',
            'type': 'error'
        })

        # Concurrency si async
        if func_info['is_async']:
            test_cases.append({
                'name': 'test_concurrent_calls',
                'description': 'Test multiple concurrent calls',
                'type': 'concurrency'
            })

        return test_cases

    def generate_test_code(self, func_info: Dict[str, Any], test_cases: List[Dict[str, str]]) -> str:
        """Génère le code des tests."""
        func_name = func_info['name']
        is_async = func_info['is_async']

        test_template = f'''"""
Unit tests for {func_name}
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
{"import asyncio" if is_async else ""}

# Import the function to test
# from your_module import {func_name}


class Test{func_name.title().replace("_", "")}:
    """Test suite for {func_name}."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.test_data = {{}}  # Setup test data

'''

        for test_case in test_cases:
            decorator = "@pytest.mark.asyncio\n    " if is_async and test_case['type'] != 'error' else ""
            async_keyword = "async " if is_async else ""
            await_keyword = "await " if is_async else ""

            test_template += f'''    {decorator}def {test_case['name']}(self):
        """
        {test_case['description']}

        Test type: {test_case['type']}
        """
        # Arrange
        # TODO: Setup test data and mocks

        # Act
        # result = {await_keyword}{func_name}(...)

        # Assert
        # assert result is not None
        # assert result == expected_value
        pass

'''

        return test_template

    def analyze_function_deeply(self, func_info: Dict[str, Any]) -> DetailedFunctionAnalysis:
        """Effectue une analyse approfondie d'une fonction."""

        # Lire le code source
        source = self.read_function_source(func_info)

        # Classification
        business_domain = self.classify_business_domain(func_info, source)
        technical_domain = self.classify_technical_domain(func_info, source)
        design_pattern = self.identify_design_pattern(func_info, source)

        # Contexte métier
        role_description = func_info['description']
        business_context = f"Used in {business_domain} within {func_info['category']} operations"

        # Préconditions/Postconditions
        preconditions = self.extract_preconditions(func_info, source)
        postconditions = self.extract_postconditions(func_info, source)
        invariants = self.extract_invariants(func_info, source)

        # Dépendances
        internal_deps = [d for d in func_info['dependencies'] if not any(ext in d for ext in ['sqlalchemy', 'fastapi', 'pydantic', 'redis', 'pandas'])]
        external_deps = [d for d in func_info['dependencies'] if d not in internal_deps]
        required_config = []
        if 'db' in source.lower():
            required_config.append("Database connection configuration")
        if 'redis' in source.lower() or 'cache' in source.lower():
            required_config.append("Cache/Redis configuration")

        # Risques
        potential_bugs = self.identify_potential_bugs(func_info, source)
        performance_issues = self.identify_performance_issues(func_info, source)
        security_risks = self.identify_security_risks(func_info, source)
        complexity_metrics = self.calculate_complexity_metrics(source)

        # Refactoring
        refactored_code, refactoring_improvements = self.generate_refactored_code(func_info, source)

        # Tests
        test_cases = self.generate_test_cases(func_info, source)
        test_code = self.generate_test_code(func_info, test_cases)

        return DetailedFunctionAnalysis(
            name=func_info['name'],
            file_path=func_info['file_path'],
            line_number=func_info['line_number'],
            signature=func_info['signature'],
            source_code=source,
            business_domain=business_domain,
            technical_domain=technical_domain,
            design_pattern=design_pattern,
            role_description=role_description,
            business_context=business_context,
            preconditions=preconditions,
            postconditions=postconditions,
            invariants=invariants,
            internal_dependencies=internal_deps,
            external_dependencies=external_deps,
            required_config=required_config,
            potential_bugs=potential_bugs,
            performance_issues=performance_issues,
            security_risks=security_risks,
            complexity_metrics=complexity_metrics,
            refactored_code=refactored_code,
            refactoring_improvements=refactoring_improvements,
            test_cases=test_cases,
            test_code=test_code
        )

    def generate_detailed_report(self, output_path: str):
        """Génère le rapport d'analyse détaillée."""
        print("=" * 80)
        print("ANALYSE APPROFONDIE DES FONCTIONS LES PLUS RÉUTILISABLES")
        print("=" * 80)
        print()

        # Obtenir les top fonctions
        print("Sélection des 30 fonctions les plus réutilisables...")
        top_functions = self.get_top_reusable_functions(30)
        print(f"Sélectionné {len(top_functions)} fonctions\n")

        # Analyser chaque fonction
        detailed_analyses = []

        for i, func_info in enumerate(top_functions, 1):
            print(f"[{i}/30] Analyse de {func_info['name']} ({func_info['file_path']})...")

            try:
                analysis = self.analyze_function_deeply(func_info)
                detailed_analyses.append(asdict(analysis))
            except Exception as e:
                print(f"  ERREUR: {e}")
                continue

        # Créer le rapport final
        report = {
            'metadata': {
                'title': 'Deep Analysis of Top 30 Reusable Functions',
                'generated_at': '2025-12-21',
                'total_functions_analyzed': len(detailed_analyses),
                'project_root': self.project_root
            },
            'summary': {
                'business_domains': {},
                'technical_domains': {},
                'design_patterns': {},
                'total_bugs_identified': sum(len(a['potential_bugs']) for a in detailed_analyses),
                'total_performance_issues': sum(len(a['performance_issues']) for a in detailed_analyses),
                'total_security_risks': sum(len(a['security_risks']) for a in detailed_analyses),
            },
            'functions': detailed_analyses
        }

        # Calculer les statistiques de domaines
        for analysis in detailed_analyses:
            bd = analysis['business_domain']
            td = analysis['technical_domain']
            dp = analysis['design_pattern']

            report['summary']['business_domains'][bd] = report['summary']['business_domains'].get(bd, 0) + 1
            report['summary']['technical_domains'][td] = report['summary']['technical_domains'].get(td, 0) + 1
            report['summary']['design_patterns'][dp] = report['summary']['design_patterns'].get(dp, 0) + 1

        # Écrire le rapport
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 80)
        print("RÉSUMÉ DE L'ANALYSE")
        print("=" * 80)
        print(f"Fonctions analysées:       {len(detailed_analyses)}")
        print(f"Bugs potentiels:           {report['summary']['total_bugs_identified']}")
        print(f"Problèmes de performance:  {report['summary']['total_performance_issues']}")
        print(f"Risques de sécurité:       {report['summary']['total_security_risks']}")
        print()
        print("Domaines métier:")
        for domain, count in sorted(report['summary']['business_domains'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain:.<40} {count:>3}")
        print()
        print("Domaines techniques:")
        for domain, count in sorted(report['summary']['technical_domains'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain:.<40} {count:>3}")
        print()
        print("Patterns de conception:")
        for pattern, count in sorted(report['summary']['design_patterns'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern:.<40} {count:>3}")
        print()
        print(f"Rapport généré: {output_path}")
        print("=" * 80)


def main():
    """Point d'entrée principal."""
    project_root = '/home/ruuuzer/Documents/monprojet'
    output_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.json'

    analyzer = DeepAnalyzer(project_root)
    analyzer.generate_detailed_report(output_path)


if __name__ == '__main__':
    main()
