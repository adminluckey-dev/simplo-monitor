#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — isi NX_PASSWORD sebelum koneksi live."
fi
exec python3 app.py
