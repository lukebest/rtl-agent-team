#!/bin/sh
# Install Cursor rules from generated cursor-pack into a user workspace (non-destructive).
# Usage: sh scripts/rat-init-cursor-project.sh [workspace]
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WS="${1:-$(pwd)}"
SRC_RULES="$ROOT_DIR/cursor-pack/rules"
DST_RULES="$WS/.cursor/rules"
if [ ! -d "$SRC_RULES" ]; then
  echo "error: missing $SRC_RULES — run: sh scripts/sync_cursor_pack.sh" >&2
  exit 1
fi
mkdir -p "$DST_RULES"
for f in "$SRC_RULES"/*.mdc; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  if [ -f "$DST_RULES/$base" ]; then
    echo "skip existing: $DST_RULES/$base" >&2
    continue
  fi
  cp "$f" "$DST_RULES/$base"
done
echo "Installed rules into $DST_RULES"
