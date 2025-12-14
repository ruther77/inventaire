#!/bin/bash
# =====================================================
# Script d'acces mobile via localhost
# =====================================================
# Ce script permet d'acceder a l'application depuis
# un appareil mobile sur le meme reseau local.
#
# Usage: ./scripts/mobile_access.sh [start|stop|status]
# =====================================================

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ports par defaut
FRONTEND_PORT=${FRONTEND_PORT:-5175}
API_PORT=${API_PORT:-8000}

get_local_ip() {
    # Tente plusieurs methodes pour obtenir l'IP locale
    local ip=""

    # Linux avec hostname
    if command -v hostname &> /dev/null; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    # Fallback avec ip command
    if [ -z "$ip" ] && command -v ip &> /dev/null; then
        ip=$(ip route get 1 2>/dev/null | awk '{print $7}' | head -1)
    fi

    # Fallback avec ifconfig
    if [ -z "$ip" ] && command -v ifconfig &> /dev/null; then
        ip=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi

    echo "$ip"
}

show_qrcode() {
    local url="$1"

    if command -v qrencode &> /dev/null; then
        echo -e "\n${BLUE}QR Code pour l'acces mobile:${NC}"
        qrencode -t ANSIUTF8 "$url"
    else
        echo -e "\n${YELLOW}Tip: Installez qrencode pour afficher un QR code${NC}"
        echo -e "    sudo apt install qrencode  # Debian/Ubuntu"
        echo -e "    brew install qrencode      # macOS"
    fi
}

check_firewall() {
    echo -e "\n${BLUE}Verification du pare-feu...${NC}"

    # UFW (Ubuntu/Debian)
    if command -v ufw &> /dev/null; then
        if ufw status 2>/dev/null | grep -q "Status: active"; then
            echo -e "${YELLOW}UFW est actif. Assurez-vous que les ports sont ouverts:${NC}"
            echo "    sudo ufw allow $FRONTEND_PORT/tcp"
            echo "    sudo ufw allow $API_PORT/tcp"
        fi
    fi

    # firewalld (Fedora/RHEL)
    if command -v firewall-cmd &> /dev/null; then
        if firewall-cmd --state 2>/dev/null | grep -q "running"; then
            echo -e "${YELLOW}firewalld est actif. Pour ouvrir les ports:${NC}"
            echo "    sudo firewall-cmd --add-port=$FRONTEND_PORT/tcp --permanent"
            echo "    sudo firewall-cmd --add-port=$API_PORT/tcp --permanent"
            echo "    sudo firewall-cmd --reload"
        fi
    fi
}

start_mobile_access() {
    local ip=$(get_local_ip)

    if [ -z "$ip" ]; then
        echo -e "${RED}Impossible de determiner l'adresse IP locale${NC}"
        exit 1
    fi

    echo -e "${GREEN}=======================================${NC}"
    echo -e "${GREEN}   ACCES MOBILE CONFIGURE${NC}"
    echo -e "${GREEN}=======================================${NC}"
    echo ""
    echo -e "${BLUE}Adresse IP locale:${NC} $ip"
    echo ""
    echo -e "${BLUE}URLs d'acces depuis votre mobile:${NC}"
    echo ""
    echo -e "  ${GREEN}Frontend:${NC} http://$ip:$FRONTEND_PORT"
    echo -e "  ${GREEN}API:${NC}      http://$ip:$API_PORT"
    echo -e "  ${GREEN}API Docs:${NC} http://$ip:$API_PORT/docs"
    echo ""

    # Afficher le QR code pour le frontend
    show_qrcode "http://$ip:$FRONTEND_PORT"

    check_firewall

    echo ""
    echo -e "${YELLOW}Instructions:${NC}"
    echo "1. Assurez-vous que votre mobile est sur le meme reseau Wi-Fi"
    echo "2. Ouvrez l'URL du frontend dans le navigateur mobile"
    echo "3. Acceptez le certificat si necessaire (HTTPS)"
    echo ""
    echo -e "${YELLOW}Configuration CORS requise dans .env:${NC}"
    echo "  CORS_ALLOWED_ORIGINS=http://localhost:5175,http://$ip:$FRONTEND_PORT"
    echo ""
    echo -e "${YELLOW}Configuration Frontend (frontend/.env.local):${NC}"
    echo "  VITE_API_BASE_URL=http://$ip:$API_PORT"
    echo ""

    # Generer un fichier de config mobile
    cat > /tmp/mobile_access_config.txt << EOF
# Configuration Mobile Access
# Genere le $(date)

IP_LOCALE=$ip
FRONTEND_URL=http://$ip:$FRONTEND_PORT
API_URL=http://$ip:$API_PORT

# Ajouter a .env pour CORS:
CORS_ALLOWED_ORIGINS=http://localhost:5175,http://$ip:$FRONTEND_PORT

# Ajouter a frontend/.env.local:
VITE_API_BASE_URL=http://$ip:$API_PORT
EOF

    echo -e "${GREEN}Configuration sauvegardee dans /tmp/mobile_access_config.txt${NC}"
}

show_status() {
    local ip=$(get_local_ip)

    echo -e "${BLUE}Status de l'acces mobile${NC}"
    echo ""
    echo -e "IP Locale: ${GREEN}$ip${NC}"
    echo ""

    # Verifier si les services tournent
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        echo -e "Frontend (port $FRONTEND_PORT): ${GREEN}EN LIGNE${NC}"
    else
        echo -e "Frontend (port $FRONTEND_PORT): ${RED}HORS LIGNE${NC}"
    fi

    if curl -s "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
        echo -e "API (port $API_PORT): ${GREEN}EN LIGNE${NC}"
    else
        echo -e "API (port $API_PORT): ${RED}HORS LIGNE${NC}"
    fi

    echo ""

    # Verifier l'accessibilite reseau
    echo -e "${BLUE}Test d'accessibilite reseau:${NC}"
    if [ -n "$ip" ]; then
        if curl -s --connect-timeout 2 "http://$ip:$FRONTEND_PORT" > /dev/null 2>&1; then
            echo -e "  Frontend accessible depuis le reseau: ${GREEN}OUI${NC}"
        else
            echo -e "  Frontend accessible depuis le reseau: ${RED}NON${NC}"
        fi

        if curl -s --connect-timeout 2 "http://$ip:$API_PORT/health" > /dev/null 2>&1; then
            echo -e "  API accessible depuis le reseau: ${GREEN}OUI${NC}"
        else
            echo -e "  API accessible depuis le reseau: ${RED}NON${NC}"
        fi
    fi
}

show_help() {
    echo "Usage: $0 [commande]"
    echo ""
    echo "Commandes:"
    echo "  start   Affiche les informations de connexion mobile"
    echo "  status  Verifie l'etat des services"
    echo "  help    Affiche cette aide"
    echo ""
    echo "Variables d'environnement:"
    echo "  FRONTEND_PORT  Port du frontend (defaut: 5175)"
    echo "  API_PORT       Port de l'API (defaut: 8000)"
}

# Main
case "${1:-start}" in
    start)
        start_mobile_access
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Commande inconnue: $1${NC}"
        show_help
        exit 1
        ;;
esac
