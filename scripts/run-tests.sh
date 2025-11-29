#!/usr/bin/env bash
set -euo pipefail

# Ce script orchestre :
# 1. le bootstrap du service de test (Postgres via docker compose)
# 2. l'exécution pytest du backend avec la base de test
# 3. le build du frontend (npm install + npm run build)
# 4. l'arrêt et le nettoyage des conteneurs

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker est requis pour lancer la base de test." >&2
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "Python n'est pas disponible dans ce shell." >&2
  exit 1
fi

export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-inventaire-tests}

source "$PROJECT_ROOT/.env.test"

echo "▶️  Démarrage de la base de tests..."
docker compose --env-file .env.test up -d db-test

echo "⏳ Attente du démarrage de Postgres..."
for _ in {1..30}; do
  if docker compose --env-file .env.test exec -T db-test pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

export DATABASE_URL="postgresql+psycopg2://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:55432/$POSTGRES_DB"

echo "🧪 Tests backend (pytest)..."
python -m pytest

echo "🧱 Build frontend..."
pushd frontend >/dev/null
npm install >/dev/null
npm run build >/dev/null
popd >/dev/null

echo "🧹 Nettoyage..."
docker compose --env-file .env.test down -v

echo "✅ Tests terminés."
