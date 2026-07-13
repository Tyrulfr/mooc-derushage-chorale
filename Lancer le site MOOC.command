#!/bin/zsh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=============================================="
echo "  Derushage MOOC — serveur local"
echo "=============================================="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Erreur : python3 est introuvable."
  read "?Appuyez sur Entree pour fermer..."
  exit 1
fi

echo "Mise a jour du site..."
python3 scripts/build_site.py
echo ""

PORT=8080
URL="http://localhost:${PORT}/index.html"

if lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Un serveur ecoute deja sur le port ${PORT}."
else
  echo "Demarrage du serveur sur ${URL}"
  cd site
  python3 -m http.server "${PORT}" >/dev/null 2>&1 &
  SERVER_PID=$!
  echo "${SERVER_PID}" > "${ROOT}/.local-server.pid"
  cd "$ROOT"
  sleep 1
fi

open "${URL}"

echo ""
echo "Site ouvert dans le navigateur : ${URL}"
echo ""
echo "Pour arreter le serveur : fermez cette fenetre"
echo "ou double-cliquez sur « Arreter le site MOOC.command »."
echo ""
read "?Appuyez sur Entree pour arreter le serveur et fermer..."

if [ -f "${ROOT}/.local-server.pid" ]; then
  PID="$(cat "${ROOT}/.local-server.pid")"
  if kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}"
    echo "Serveur arrete."
  fi
  rm -f "${ROOT}/.local-server.pid"
fi
