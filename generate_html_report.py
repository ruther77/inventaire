#!/usr/bin/env python3
"""
Génère un rapport HTML interactif à partir de l'analyse JSON.
"""

import json
import os


def generate_html_report(json_path: str, output_path: str):
    """Génère un rapport HTML interactif."""

    # Charger le JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyse Approfondie - Top 30 Fonctions Réutilisables</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .filters {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .filter-group {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}

        .filter-group label {{
            font-weight: 600;
            margin-right: 10px;
        }}

        select, input {{
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
        }}

        select:focus, input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .function-list {{
            display: grid;
            gap: 20px;
        }}

        .function-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .function-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .function-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 15px;
        }}

        .function-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
            font-family: 'Courier New', monospace;
        }}

        .function-meta {{
            text-align: right;
            font-size: 0.9em;
            color: #666;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
        }}

        .badge-domain {{
            background: #e3f2fd;
            color: #1976d2;
        }}

        .badge-pattern {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}

        .badge-tech {{
            background: #e8f5e9;
            color: #388e3c;
        }}

        .section {{
            margin-bottom: 20px;
        }}

        .section h4 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        .risk-item {{
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 5px;
            border-left: 4px solid;
        }}

        .risk-critical {{
            background: #ffebee;
            border-color: #c62828;
            color: #c62828;
        }}

        .risk-warning {{
            background: #fff3e0;
            border-color: #ef6c00;
            color: #e65100;
        }}

        .risk-info {{
            background: #e3f2fd;
            border-color: #1976d2;
            color: #0d47a1;
        }}

        .risk-ok {{
            background: #e8f5e9;
            border-color: #388e3c;
            color: #1b5e20;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}

        .metric {{
            background: #f5f5f5;
            padding: 12px;
            border-radius: 5px;
            text-align: center;
        }}

        .metric-label {{
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }}

        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .code-toggle {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            margin-right: 10px;
            margin-bottom: 10px;
            transition: background 0.2s;
        }}

        .code-toggle:hover {{
            background: #5568d3;
        }}

        .code-block {{
            display: none;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }}

        .code-block.show {{
            display: block;
        }}

        pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}

        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-weight: 600;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }}

        .tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .list-item {{
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}

        .list-item:last-child {{
            border-bottom: none;
        }}

        footer {{
            margin-top: 50px;
            padding: 30px;
            background: white;
            border-radius: 10px;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Analyse Approfondie des Fonctions</h1>
            <p>Top 30 Fonctions les Plus Réutilisables</p>
            <p style="opacity: 0.9; margin-top: 10px;">
                Généré le {data['metadata']['generated_at']} |
                Projet: {data['metadata']['project_root']}
            </p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <h3>Fonctions Analysées</h3>
                <div class="number">{data['metadata']['total_functions_analyzed']}</div>
            </div>
            <div class="stat-card">
                <h3>Bugs Potentiels</h3>
                <div class="number" style="color: #c62828;">{data['summary']['total_bugs_identified']}</div>
            </div>
            <div class="stat-card">
                <h3>Problèmes Performance</h3>
                <div class="number" style="color: #ef6c00;">{data['summary']['total_performance_issues']}</div>
            </div>
            <div class="stat-card">
                <h3>Risques Sécurité</h3>
                <div class="number" style="color: #f57c00;">{data['summary']['total_security_risks']}</div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label>🔍 Recherche:</label>
                <input type="text" id="searchInput" placeholder="Nom de fonction...">
            </div>
            <div class="filter-group">
                <label>🏢 Domaine Métier:</label>
                <select id="businessDomainFilter">
                    <option value="">Tous</option>
"""

    # Ajouter les options de domaine métier
    for domain in sorted(data['summary']['business_domains'].keys()):
        html += f'                    <option value="{domain}">{domain}</option>\n'

    html += """                </select>
            </div>
            <div class="filter-group">
                <label>⚙️ Domaine Technique:</label>
                <select id="technicalDomainFilter">
                    <option value="">Tous</option>
"""

    # Ajouter les options de domaine technique
    for domain in sorted(data['summary']['technical_domains'].keys()):
        html += f'                    <option value="{domain}">{domain}</option>\n'

    html += """                </select>
            </div>
            <div class="filter-group">
                <label>🎨 Pattern:</label>
                <select id="patternFilter">
                    <option value="">Tous</option>
"""

    # Ajouter les options de patterns
    for pattern in sorted(data['summary']['design_patterns'].keys()):
        html += f'                    <option value="{pattern}">{pattern}</option>\n'

    html += """                </select>
            </div>
        </div>

        <div class="function-list" id="functionList">
"""

    # Générer les cartes de fonctions
    for func in data['functions']:
        # Déterminer la couleur du risque
        has_critical = any('CRITICAL' in item for item in func['potential_bugs'] + func['security_risks'])
        has_warning = any('RISK' in item or 'WARNING' in item for item in func['potential_bugs'] + func['performance_issues'] + func['security_risks'])

        html += f"""
            <div class="function-card"
                 data-business="{func['business_domain']}"
                 data-technical="{func['technical_domain']}"
                 data-pattern="{func['design_pattern']}"
                 data-name="{func['name'].lower()}">

                <div class="function-header">
                    <div>
                        <div class="function-name">{func['name']}()</div>
                        <div style="margin-top: 10px;">
                            <span class="badge badge-domain">{func['business_domain']}</span>
                            <span class="badge badge-tech">{func['technical_domain']}</span>
                            <span class="badge badge-pattern">{func['design_pattern']}</span>
                        </div>
                    </div>
                    <div class="function-meta">
                        <div><strong>Fichier:</strong> {func['file_path']}</div>
                        <div><strong>Ligne:</strong> {func['line_number']}</div>
                    </div>
                </div>

                <div class="tabs">
                    <button class="tab active" onclick="switchTab(event, 'overview-{func['name']}')">Vue d'ensemble</button>
                    <button class="tab" onclick="switchTab(event, 'risks-{func['name']}')">Risques</button>
                    <button class="tab" onclick="switchTab(event, 'tests-{func['name']}')">Tests</button>
                    <button class="tab" onclick="switchTab(event, 'code-{func['name']}')">Code</button>
                </div>

                <div id="overview-{func['name']}" class="tab-content active">
                    <div class="section">
                        <h4>📝 Description</h4>
                        <p>{func['role_description']}</p>
                        <p style="color: #666; margin-top: 8px;"><em>{func['business_context']}</em></p>
                    </div>

                    <div class="section">
                        <h4>📋 Préconditions</h4>
"""
        for pre in func['preconditions']:
            html += f"                        <div class='list-item'>• {pre}</div>\n"

        html += """                    </div>

                    <div class="section">
                        <h4>✅ Postconditions</h4>
"""
        for post in func['postconditions']:
            html += f"                        <div class='list-item'>• {post}</div>\n"

        html += """                    </div>

                    <div class="section">
                        <h4>📦 Dépendances</h4>
"""
        if func['external_dependencies']:
            html += "                        <p><strong>Externes:</strong></p>\n"
            for dep in func['external_dependencies']:
                html += f"                        <div class='list-item'><code>{dep}</code></div>\n"

        if func['internal_dependencies']:
            html += "                        <p><strong>Internes:</strong></p>\n"
            for dep in func['internal_dependencies']:
                html += f"                        <div class='list-item'><code>{dep}</code></div>\n"

        html += """                    </div>
                </div>

                <div id="risks-{func['name']}" class="tab-content">
                    <div class="section">
                        <h4>⚠️ Bugs Potentiels</h4>
"""
        for bug in func['potential_bugs']:
            risk_class = 'risk-critical' if 'CRITICAL' in bug else 'risk-warning' if 'RISK' in bug else 'risk-info'
            html += f"                        <div class='{risk_class} risk-item'>{bug}</div>\n"

        html += f"""                    </div>

                    <div class="section">
                        <h4>⚡ Performance</h4>
                        <div class="metric-grid">
                            <div class="metric">
                                <div class="metric-label">Complexité</div>
                                <div class="metric-value">{func['complexity_metrics']['cyclomatic_complexity']}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Lignes</div>
                                <div class="metric-value">{func['complexity_metrics']['lines_of_code']}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Boucles</div>
                                <div class="metric-value">{func['complexity_metrics']['number_of_loops']}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Conditions</div>
                                <div class="metric-value">{func['complexity_metrics']['number_of_conditions']}</div>
                            </div>
                        </div>
"""

        for issue in func['performance_issues']:
            html += f"                        <div class='risk-warning risk-item'>{issue}</div>\n"

        html += """                    </div>

                    <div class="section">
                        <h4>🔒 Sécurité</h4>
"""
        for risk in func['security_risks']:
            risk_class = 'risk-critical' if 'CRITICAL' in risk else 'risk-warning'
            html += f"                        <div class='{risk_class} risk-item'>{risk}</div>\n"

        html += """                    </div>

                    <div class="section">
                        <h4>✨ Améliorations Proposées</h4>
"""
        for improvement in func['refactoring_improvements']:
            html += f"                        <div class='risk-ok risk-item'>✅ {improvement}</div>\n"

        html += """                    </div>
                </div>

                <div id="tests-{func['name']}" class="tab-content">
                    <div class="section">
                        <h4>🧪 Cas de Test</h4>
"""
        for test in func['test_cases']:
            html += f"                        <div class='list-item'><strong>{test['name']}</strong> ({test['type']}): {test['description']}</div>\n"

        html += f"""                    </div>

                    <button class="code-toggle" onclick="toggleCode('test-code-{func['name']}')">
                        Voir le code des tests
                    </button>
                    <div id="test-code-{func['name']}" class="code-block">
                        <pre>{func['test_code']}</pre>
                    </div>
                </div>

                <div id="code-{func['name']}" class="tab-content">
                    <button class="code-toggle" onclick="toggleCode('original-{func['name']}')">
                        Code Original
                    </button>
                    <button class="code-toggle" onclick="toggleCode('refactored-{func['name']}')">
                        Code Refactorisé
                    </button>

                    <div id="original-{func['name']}" class="code-block">
                        <pre>{func['source_code']}</pre>
                    </div>

                    <div id="refactored-{func['name']}" class="code-block">
                        <pre>{func['refactored_code']}</pre>
                    </div>
                </div>

            </div>
"""

    html += """        </div>

        <footer>
            <p><strong>Méthodologie:</strong> Analyse statique via AST Python | Détection de patterns | Analyse de complexité</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Généré automatiquement par l'outil d'analyse de code
            </p>
        </footer>
    </div>

    <script>
        function switchTab(event, tabId) {
            // Get the function card
            const card = event.target.closest('.function-card');

            // Hide all tab contents in this card
            card.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all tabs in this card
            card.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab content
            document.getElementById(tabId).classList.add('active');

            // Add active class to clicked tab
            event.target.classList.add('active');
        }

        function toggleCode(id) {
            const codeBlock = document.getElementById(id);
            codeBlock.classList.toggle('show');
        }

        // Filters
        const searchInput = document.getElementById('searchInput');
        const businessFilter = document.getElementById('businessDomainFilter');
        const technicalFilter = document.getElementById('technicalDomainFilter');
        const patternFilter = document.getElementById('patternFilter');

        function applyFilters() {
            const searchTerm = searchInput.value.toLowerCase();
            const businessDomain = businessFilter.value;
            const technicalDomain = technicalFilter.value;
            const pattern = patternFilter.value;

            document.querySelectorAll('.function-card').forEach(card => {
                const name = card.dataset.name;
                const business = card.dataset.business;
                const technical = card.dataset.technical;
                const cardPattern = card.dataset.pattern;

                const matchesSearch = !searchTerm || name.includes(searchTerm);
                const matchesBusiness = !businessDomain || business === businessDomain;
                const matchesTechnical = !technicalDomain || technical === technicalDomain;
                const matchesPattern = !pattern || cardPattern === pattern;

                if (matchesSearch && matchesBusiness && matchesTechnical && matchesPattern) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        searchInput.addEventListener('input', applyFilters);
        businessFilter.addEventListener('change', applyFilters);
        technicalFilter.addEventListener('change', applyFilters);
        patternFilter.addEventListener('change', applyFilters);
    </script>
</body>
</html>
"""

    # Écrire le fichier
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Rapport HTML généré: {output_path}")
    print(f"Taille: {len(html)} caractères")


def main():
    """Point d'entrée principal."""
    json_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.json'
    output_path = '/home/ruuuzer/Documents/bibliotheque-maison/docs/detailed_analysis.html'

    generate_html_report(json_path, output_path)


if __name__ == '__main__':
    main()
