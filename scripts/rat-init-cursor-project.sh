#!/bin/sh
# Deploy Cursor-style rules from cursor-pack into a user RTL project (non-destructive).
# Does not replace the Cursor plugin install — only copies .mdc rules when missing.
#
# Usage: sh scripts/rat-init-cursor-project.sh [TARGET_DIR]
# Default TARGET_DIR is current directory.
set -eu

TARGET="${1:-.}"
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
RULES_SRC="$ROOT/cursor-pack/rules"

if [ ! -d "$RULES_SRC" ]; then
  echo "error: $RULES_SRC not found — run: sh scripts/sync_cursor_pack.sh" >&2
  exit 1
fi

mkdir -p "$TARGET/.cursor/rules"
deployed=0
for f in "$RULES_SRC"/*.mdc; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  dest="$TARGET/.cursor/rules/$base"
  if [ ! -f "$dest" ]; then
    cp "$f" "$dest"
    deployed=$((deployed + 1))
  fi
done

printf 'rat-init-cursor-project: target=%s deployed_new_rules=%s (skipped existing)\n' "$TARGET" "$deployed"
