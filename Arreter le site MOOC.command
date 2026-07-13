#!/bin/zsh

ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT=8080
STOPPED=0

if [ -f "${ROOT}/.local-server.pid" ]; then
  PID="$(cat "${ROOT}/.local-server.pid")"
  if kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}"
    STOPPED=1
  fi
  rm -f "${ROOT}/.local-server.pid"
fi

if lsof -nP -iTCP:${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
  kill "$(lsof -nP -iTCP:${PORT} -sTCP:LISTEN -t)" 2>/dev/null && STOPPED=1
fi

if [ "${STOPPED}" -eq 1 ]; then
  echo "Serveur local arrete (port ${PORT})."
else
  echo "Aucun serveur local actif sur le port ${PORT}."
fi

sleep 2
