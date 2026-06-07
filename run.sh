#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "[ocr] Creating venv..."
  python3 -m venv venv
fi

echo "[ocr] Installing dependencies..."
venv/bin/python -m pip install -q -r requirements.txt

echo "[ocr] Starting..."
exec venv/bin/python main.py
