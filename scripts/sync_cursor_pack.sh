#!/bin/sh
# Regenerate cursor-pack/ from repository SSOT (requires python3, rsync).
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/generate_cursor_pack.py
