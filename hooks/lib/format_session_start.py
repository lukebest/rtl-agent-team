#!/usr/bin/env python3
"""Pipe Claude SessionStart JSON from stdin; emit Claude JSON unchanged unless
RTL_HOOK_OUTPUT_FORMAT=cursor, then emit {\"additional_context\": ...}."""
import json
import os
import sys

fmt = os.environ.get("RTL_HOOK_OUTPUT_FORMAT", "claude")
raw = sys.stdin.read()
if fmt == "cursor":
    j = json.loads(raw)
    ctx = j["hookSpecificOutput"]["additionalContext"]
    print(json.dumps({"additional_context": ctx}, ensure_ascii=False))
else:
    sys.stdout.write(raw)
