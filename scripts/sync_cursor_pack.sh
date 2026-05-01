#!/bin/sh
# Regenerate cursor-pack/ from SSOT. Requires python3.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"
if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 required" >&2
  exit 1
fi
exec python3 "$ROOT_DIR/scripts/generate_cursor_pack.py" --out "$ROOT_DIR/cursor-pack"
