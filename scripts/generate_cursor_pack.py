#!/usr/bin/env python3
"""Generate cursor-pack/ from SSOT. Invoked by scripts/sync_cursor_pack.sh."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

RULE_TEMPLATE_DIR = Path("skills/rat-init-project/templates/rules")

GATE_VERIFY_STOP = """#!/bin/sh
# Run RTL verify stop check using bundled hooks (same semantics as Claude Code Stop hook).
# stdin contract matches tests/unit/test_hooks.py (minimal {"cwd":...}).
# Usage: sh gates/cursor-verify-stop.sh  (from user project root)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
printf '{"cwd":"%s"}\\n' "$(pwd)" | sh "$ROOT/runtime/hooks/rtl-verify-stop-gate.sh"
"""


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def _write_mdc(out_rules: Path, name: str, body_md: str, glob_pat: str) -> None:
    out_rules.mkdir(parents=True, exist_ok=True)
    title = name.replace("-", " ")
    mdc = f"""---
description: RAT — {title}
globs:
  - "{glob_pat}"
---
{body_md}
"""
    (out_rules / f"{name}.mdc").write_text(mdc, encoding="utf-8")


def _emit_rules(out: Path, repo: Path) -> None:
    tpl = repo / RULE_TEMPLATE_DIR
    conv = (tpl / "rtl-coding-conventions.md").read_text(encoding="utf-8")
    gate = (tpl / "rtl-verification-gate.md").read_text(encoding="utf-8")
    _write_mdc(out / "rules", "rtl-coding-conventions", conv, "**/*.sv")
    _write_mdc(out / "rules", "rtl-verification-gate", gate, "**/*.sv")


def _emit_gates(out: Path) -> None:
    gd = out / "gates"
    gd.mkdir(parents=True, exist_ok=True)
    script_path = gd / "cursor-verify-stop.sh"
    script_path.write_text(GATE_VERIFY_STOP, encoding="utf-8")
    os.chmod(script_path, 0o755)


def _read_version(repo: Path) -> str:
    pkg = repo / "package.json"
    if not pkg.is_file():
        return "unknown"
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        return str(data.get("version", "unknown"))
    except (json.JSONDecodeError, OSError):
        return "unknown"


def build_pack(out: Path, repo: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _copy_tree(repo / "skills", out / "skills")
    _copy_tree(repo / "agents", out / "agents")
    _copy_tree(repo / "domain-packages", out / "domain-packages")
    _copy_tree(repo / "hooks", out / "runtime" / "hooks")
    _emit_rules(out, repo)
    _emit_gates(out)
    version = _read_version(repo)
    (out / "README.md").write_text(
        f"# cursor-pack (generated)\n\n"
        f"**Version:** {version}\n\n"
        "Do not edit files in this directory by hand.\n\n"
        "Regenerate from repository root:\n\n"
        "```bash\nsh scripts/sync_cursor_pack.sh\n```\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build cursor-pack from rtl-agent-team SSOT.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "cursor-pack",
        help="Output directory (default: ./cursor-pack)",
    )
    args = parser.parse_args()
    build_pack(args.out.resolve(), REPO_ROOT)


if __name__ == "__main__":
    main()
