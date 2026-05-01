#!/bin/sh
# Run RTL verify stop check using bundled hooks (same semantics as Claude Code Stop hook).
# stdin contract matches tests/unit/test_hooks.py (minimal {"cwd":...}).
# Usage: sh gates/cursor-verify-stop.sh  (from user project root)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
printf '{"cwd":"%s"}\n' "$(pwd)" | sh "$ROOT/runtime/hooks/rtl-verify-stop-gate.sh"
