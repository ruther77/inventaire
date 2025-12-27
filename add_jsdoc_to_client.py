#!/usr/bin/env python3
"""
Script pour ajouter automatiquement la documentation JSDoc aux fonctions
non documentées du fichier api/client.js
"""

import re

# Template JSDoc générique basé sur la signature de la fonction
def generate_jsdoc(func_name, params_str):
    """Génère un commentaire JSDoc basique pour une fonction"""

    # Parser les paramètres
    has_async = True

    # Déterminer la description basée sur le nom de la fonction
    desc_map = {
        'import': 'Importe',
        'fetch': 'Récupère',
        'create': 'Crée',
        'update': 'Met à jour',
        'delete': 'Supprime',
        'run': 'Exécute',
        'refresh': 'Actualise',
        'download': 'Télécharge',
        'export': 'Exporte',
        'record': 'Enregistre',
        'deduplicate': 'Déduplique',
        'calculate': 'Calcule',
        'forecast': 'Prévoit',
        'scan': 'Scanne',
        'detect': 'Détecte',
        'resolve': 'Résout',
        'generate': 'Génère',
        'search': 'Recherche',
        'classify': 'Classifie',
        'suggest': 'Suggère',
        'bootstrap': 'Initialise',
        'compare': 'Compare',
        'acknowledge': 'Accuse réception',
        'recalculate': 'Recalcule',
    }

    action = 'Effectue'
    for key, value in desc_map.items():
        if func_name.lower().startswith(key):
            action = value
            break

    # Description basique
    resource = func_name.replace('fetch', '').replace('create', '').replace('update', '').replace('delete', '')
    resource = re.sub(r'([A-Z])', r' \1', resource).strip().lower()

    jsdoc = f"""/**
 * {action} {resource}.
 *
 * @async"""

    # Analyser les paramètres
    if params_str and params_str.strip() != '':
        # Patterns communs
        if 'filters' in params_str:
            jsdoc += "\n * @param {Object} [filters={}] - Filtres de recherche"
        elif 'payload' in params_str:
            jsdoc += "\n * @param {Object} payload - Données"
        elif 'params' in params_str:
            jsdoc += "\n * @param {Object} [params={}] - Paramètres"
        else:
            # Essayer de parser les paramètres individuels
            param_matches = re.findall(r'(\w+)(?:\s*[=,]|$)', params_str)
            for param in param_matches:
                if param and param not in ['async', 'await']:
                    jsdoc += f"\n * @param {{*}} {param} - {param}"

    jsdoc += """
 *
 * @returns {Promise<Object>} Résultat de l'opération
 * @throws {AxiosError} Si erreur réseau ou serveur
 */"""

    return jsdoc

# Lire le fichier
file_path = '/home/ruuuzer/Documents/monprojet/frontend/src/api/client.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver toutes les fonctions exportées sans JSDoc avant elles
pattern = r'(?<!/\*\*.*?\*/)(\nexport const (\w+) = async \(([^)]*)\))'

# Compter combien on en trouve
matches = list(re.finditer(pattern, content, re.DOTALL))

print(f"Trouvé {len(matches)} fonctions potentiellement non documentées")

# Pour chaque match, vérifier qu'il n'y a pas déjà un /** avant
documented = 0
undocumented_functions = []

for match in matches:
    func_name = match.group(2)
    params = match.group(3)
    start_pos = match.start()

    # Vérifier les 500 caractères précédents pour un /**
    before_text = content[max(0, start_pos - 500):start_pos]

    # Si pas de /** dans les lignes précédentes (hors whitespace)
    lines_before = before_text.split('\n')
    has_jsdoc = False
    for line in reversed(lines_before[-5:]):  # Check last 5 lines
        stripped = line.strip()
        if stripped.startswith('/**'):
            has_jsdoc = True
            break
        elif stripped and not stripped.startswith('//') and not stripped.startswith('*'):
            # Ligne non-commentaire trouvée avant le jsdoc
            break

    if not has_jsdoc:
        undocumented_functions.append((func_name, params, start_pos, match.group(1)))
    else:
        documented += 1

print(f"Documentées: {documented}")
print(f"Non documentées: {len(undocumented_functions)}")
print(f"\nFonctions non documentées:")
for func_name, params, _, _ in undocumented_functions[:10]:
    print(f"  - {func_name}({params})")

if len(undocumented_functions) > 10:
    print(f"  ... et {len(undocumented_functions) - 10} autres")
