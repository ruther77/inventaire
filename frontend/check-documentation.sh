#!/bin/bash

# Script de vérification de la documentation JSDoc
# Usage: ./check-documentation.sh

echo "==================================="
echo "Vérification Documentation JSDoc"
echo "==================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Répertoire frontend
FRONTEND_DIR="./src"

# Compter tous les fichiers JS/JSX
TOTAL_FILES=$(find "$FRONTEND_DIR" -name "*.js" -o -name "*.jsx" 2>/dev/null | wc -l | tr -d ' ')
echo "📁 Total fichiers JS/JSX: $TOTAL_FILES"

# Compter les fichiers avec @module
DOCUMENTED_FILES=$(find "$FRONTEND_DIR" \( -name "*.js" -o -name "*.jsx" \) -exec grep -l "@module" {} \; 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}✅ Fichiers documentés: $DOCUMENTED_FILES${NC}"

# Calculer le pourcentage
PERCENTAGE=$(echo "scale=1; ($DOCUMENTED_FILES * 100) / $TOTAL_FILES" | bc)
echo -e "${YELLOW}📊 Progression: $PERCENTAGE%${NC}"

echo ""
REMAINING=$((TOTAL_FILES - DOCUMENTED_FILES))
echo -e "${RED}⏳ Fichiers restants: $REMAINING${NC}"

echo ""
echo "==================================="
echo "Détails par dossier"
echo "==================================="
echo ""

# Fonction pour vérifier un dossier
check_folder() {
    local folder=$1
    local name=$2

    if [ -d "$FRONTEND_DIR/$folder" ]; then
        local total=$(find "$FRONTEND_DIR/$folder" -name "*.js" -o -name "*.jsx" 2>/dev/null | wc -l | tr -d ' ')
        local documented=$(find "$FRONTEND_DIR/$folder" \( -name "*.js" -o -name "*.jsx" \) -exec grep -l "@module" {} \; 2>/dev/null | wc -l | tr -d ' ')
        local percent=$(echo "scale=1; ($documented * 100) / $total" | bc 2>/dev/null || echo "0")

        printf "%-20s %3d/%3d (%5s%%)\n" "$name" "$documented" "$total" "$percent"
    fi
}

# Vérifier chaque dossier
check_folder "hooks" "Hooks"
check_folder "features" "Features"
check_folder "components" "Components"
check_folder "api" "API"
check_folder "app" "App"
check_folder "utils" "Utils"
check_folder "contexts" "Contexts"
check_folder "modules" "Modules"
check_folder "newCMS" "NewCMS"

echo ""
echo "==================================="
echo "Hooks non documentés"
echo "==================================="
echo ""

# Lister les hooks non documentés
if [ -d "$FRONTEND_DIR/hooks" ]; then
    find "$FRONTEND_DIR/hooks" -name "*.js" 2>/dev/null | while read file; do
        if ! grep -q "@module" "$file" 2>/dev/null; then
            basename "$file"
        fi
    done | head -20

    UNDOC_HOOKS=$(find "$FRONTEND_DIR/hooks" -name "*.js" -exec grep -L "@module" {} \; 2>/dev/null | wc -l | tr -d ' ')
    if [ "$UNDOC_HOOKS" -gt 20 ]; then
        echo "... et $((UNDOC_HOOKS - 20)) autres"
    fi
fi

echo ""
echo "==================================="
echo "Validation JSDoc"
echo "==================================="
echo ""

# Vérifier si JSDoc est installé
if command -v jsdoc &> /dev/null; then
    echo "✅ JSDoc est installé"
    echo "   Générer la doc: npx jsdoc -r $FRONTEND_DIR -d docs/jsdoc"
else
    echo "⚠️  JSDoc non installé"
    echo "   Installer: npm install -D jsdoc"
fi

echo ""
echo "==================================="
echo "Prochaines étapes"
echo "==================================="
echo ""
echo "1. Consulter: GUIDE_DOCUMENTATION_JSDOC.md"
echo "2. Documenter les hooks prioritaires (voir FICHIERS_A_DOCUMENTER.md)"
echo "3. Utiliser les hooks documentés comme référence"
echo "4. Relancer ce script pour voir la progression"
echo ""

# Calculer estimation temps restant (5 min par fichier en moyenne)
MINUTES_REMAINING=$((REMAINING * 5))
HOURS=$((MINUTES_REMAINING / 60))
echo "⏱️  Estimation temps restant: ~$HOURS heures (à 5 min/fichier)"
echo ""
