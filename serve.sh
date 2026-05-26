#!/usr/bin/env bash
# Serve the public archive locally.
set -euo pipefail

PORT=2104
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is already in use. Stop that server or choose another port with python3 -m http.server." >&2
  exit 1
fi

cd "$ROOT"
echo "Research archive: http://localhost:$PORT/"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
