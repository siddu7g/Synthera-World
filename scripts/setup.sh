#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m venv "${ROOT_DIR}/backend/venv"
source "${ROOT_DIR}/backend/venv/bin/activate"
pip install --upgrade pip
pip install -r "${ROOT_DIR}/backend/requirements.txt"

echo "Backend environment ready."
echo "Next:"
echo "  1) cp .env.example .env (if available in your local setup)"
echo "  2) source backend/venv/bin/activate"
echo "  3) uvicorn main:app --reload --port 8765 (run from backend/)"
