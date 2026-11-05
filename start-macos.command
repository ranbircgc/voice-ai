#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

osascript -e "tell application \"Terminal\" to do script \"cd '$BACKEND' && python3.11 -m venv .venv 2>/dev/null || true; source '$BACKEND/.venv/bin/activate' && pip install -r requirements.txt && uvicorn app:app --reload --host 127.0.0.1 --port 8000\""
osascript -e "tell application \"Terminal\" to do script \"cd '$FRONTEND' && npm install && npm run dev\""
