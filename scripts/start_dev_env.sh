#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

# charge les variables de .env (si présentes)
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# For local execution, override host pointing to Docker container if needed
if [ -n "${DATABASE_URL-}" ] && [[ "$DATABASE_URL" == *"@db:"* ]]; then
  export DATABASE_URL="${DATABASE_URL/@db:/@localhost:}"
fi

# active l'environnement virtuel
# shellcheck disable=SC1091
source .venv/bin/activate

echo "▶️  Bootstrap (schéma + seed restaurant) ..."
python3 scripts/bootstrap_local.py

echo "▶️  Lancement du backend FastAPI (uvicorn)..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

cleanup() {
  echo "▶️  Arrêt du backend (PID: $BACKEND_PID) ..."
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
  wait "$BACKEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "▶️  Démarrage du frontend (npm run dev)..."
cd frontend
npm run dev
