#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "[reset] drop + recreate db..."
docker compose down -v
docker compose up -d
sleep 3
echo "[migrate]..."
python manage.py migrate
echo "[seed] demo data..."
python scripts/seed_demo_data.py
python scripts/seed_chroma_recall.py
python knowledge/ingest.py
echo "[done]"