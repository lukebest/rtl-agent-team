#!/usr/bin/env python3
"""Regenerate cursor-pack/ for Cursor IDE (.cursor-plugin layout + runtime hooks)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "cursor-pack"


def _read_version() -> str:
    pkg = ROOT / "package.json"
    data = json.loads(pkg.read_text(encoding="utf-8"))
    return str(data.get("version", "0.0.0"))


def _rsync_delete(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise SystemExit(f"missing source: {src}")
    subprocess.run(
        ["rsync", "-a", "--delete", str(src) + "/", str(dst) + "/"],
        check=True,
    )


def _sync_rules_from_templates() -> None:
    """Emit cursor-pack/rules/*.mdc from rat-init templates + Cursor frontmatter."""
    tpl_dir = ROOT / "skills" / "rat-init-project" / "templates" / "rules"
    out_dir = PACK / "rules"
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "rtl-coding-conventions.md": "rtl-coding-conventions.mdc",
        "rtl-verification-gate.md": "rtl-verification-gate.mdc",
    }
    for src_name, dst_name in mapping.items():
        src = tpl_dir / src_name
        if not src.exists():
            continue
        body = src.read_text(encoding="utf-8")
        if dst_name == "rtl-coding-conventions.mdc":
            header = (
                "---\n"
                'description: RAT — rtl coding conventions\nglobs:\n'
                '  - "**/*.sv"\n'
                "---\n"
                "---\n"
                "paths:\n"
                '  - "rtl/**/*.sv"\n'
                '  - "rtl/**/*.svh"\n'
                '  - "rtl/**/*.v"\n'
                '  - "rtl/**/*.vh"\n'
                "---\n\n"
            )
        else:
            header = (
                "---\n"
                'description: RAT — rtl verification gate\nglobs:\n'
                '  - "**/*.sv"\n'
                "---\n\n"
            )
        (out_dir / dst_name).write_text(header + body.lstrip(), encoding="utf-8")


def _write_plugin_json(version: str) -> None:
    d = PACK / ".cursor-plugin"
    d.mkdir(parents=True, exist_ok=True)
    logo_rel = "assets/logo.jpg"
    assets = PACK / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    logo_use = logo_rel if (PACK / logo_rel).exists() else "../rat_logo.jpg"
    manifest = {
        "name": "rtl-agent-team",
        "version": version,
        "description": (
            "97-agent RTL design pipeline with 97 skills for 6-Phase hardware "
            "design automation (Research → Architecture → μArch → RTL → Verify → Design Note)"
        ),
        "author": {"name": "babyworm"},
        "repository": "https://github.com/babyworm/rtl-agent-team",
        "homepage": "https://github.com/babyworm/rtl-agent-team",
        "license": "MIT",
        "keywords": [
            "rtl",
            "hdl",
            "verilog",
            "systemverilog",
            "fpga",
            "asic",
            "eda",
            "verification",
            "formal",
            "uvm",
            "cocotb",
        ],
        "logo": logo_use,
        "rules": "./rules/",
        "skills": "./skills/",
        "agents": "./agents/",
        "hooks": "./hooks/hooks.json",
    }
    (d / "plugin.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def _write_cursor_hooks_json() -> None:
    """Cursor hooks schema version 1 — paths relative to cursor-pack/."""
    hook_dir = PACK / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    rt = "runtime/hooks"
    env = 'env RTL_HOOK_OUTPUT_FORMAT=cursor sh '
    # Relative paths: Cursor runs hooks with plugin root as cwd

    def hc(cmd: str, timeout: int, matcher: str | None = None) -> dict:
        h: dict = {"type": "command", "command": cmd, "timeout": timeout}
        if matcher:
            h["matcher"] = matcher
        return h

    cmds = {
        "sessionStart": [
            hc(f'{env}"{rt}/rtl-orchestrator-inject.sh"', 30),
            hc(f'{env}"{rt}/rtl-audit-init.sh"', 30),
        ],
        "postToolUse": [
            hc(f'{env}"{rt}/rtl-edit-tracker.sh"', 60, "Write|Shell"),
            hc(f'{env}"{rt}/rtl-team-progress.sh"', 30, "TaskUpdate"),
            hc(f'{env}"{rt}/rtl-audit-spawn-complete.sh"', 30, "TaskCreate"),
        ],
        "preToolUse": [
            hc(f'{env}"{rt}/rtl-phase-state-bootstrap.sh"', 60, "Skill"),
            hc(f'{env}"{rt}/rtl-skill-activation.sh"', 60, "Skill"),
            hc(f'{env}"{rt}/rtl-spawn-context.sh"', 30, "TaskCreate"),
        ],
        "subagentStart": [
            hc(f'{env}"{rt}/rtl-audit-subagent.sh"', 30),
        ],
        "subagentStop": [
            hc(f'{env}"{rt}/rtl-audit-subagent.sh"', 30),
        ],
        "stop": [
            hc(f'{env}"{rt}/rtl-verify-stop-gate.sh"', 60),
            hc(f'{env}"{rt}/rtl-p6-cascade-gate.sh"', 60),
            hc(f'{env}"{rt}/rtl-skill-completion-gate.sh"', 120),
            hc(f'{env}"{rt}/rtl-coverage-exclusion-gate.sh"', 60),
            hc(f'{env}"{rt}/stop-gate.sh"', 120),
        ],
    }
    out = {"version": 1, "hooks": cmds}
    (hook_dir / "hooks.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8"
    )


def _write_root_cursor_marketplace(version: str) -> None:
    """Repo-root .cursor-plugin/marketplace.json for Cursor multi-plugin discovery."""
    d = ROOT / ".cursor-plugin"
    d.mkdir(parents=True, exist_ok=True)
    mpath = d / "marketplace.json"
    doc = {
        "name": "rtl-agent-marketplace",
        "owner": {
            "name": "babyworm",
            "email": "babyworm@users.noreply.github.com",
        },
        "metadata": {
            "description": "RTL design and verification automation for Cursor",
            "version": version,
        },
        "plugins": [
            {
                "name": "rtl-agent-team",
                "source": "cursor-pack",
                "description": (
                    "97-agent RTL design pipeline with 97 skills for 6-Phase hardware "
                    "design automation (Research → Architecture → μArch → RTL → Verify → Design Note)"
                ),
                "version": version,
                "author": {"name": "babyworm"},
                "homepage": "https://github.com/babyworm/rtl-agent-team",
                "repository": "https://github.com/babyworm/rtl-agent-team",
                "license": "MIT",
                "category": "development",
                "tags": [
                    "rtl",
                    "hdl",
                    "verilog",
                    "systemverilog",
                    "fpga",
                    "asic",
                    "eda",
                    "verification",
                    "formal",
                    "uvm",
                    "cocotb",
                ],
            },
            {
                "name": "systemverilog-lsp",
                "source": {
                    "source": "github",
                    "repo": "babyworm/systemverilog-lsp",
                    "ref": "v1.1.4",
                    "sha": "a874d3248d08606b50b71376c64ed8af99396c97",
                },
                "description": (
                    "SystemVerilog/Verilog language server powered by slang-server"
                ),
                "author": {"name": "RTL Agent Team contributors"},
                "homepage": "https://github.com/hudson-trading/slang-server",
                "repository": "https://github.com/babyworm/systemverilog-lsp",
                "license": "MIT",
                "category": "development",
                "tags": ["systemverilog", "verilog", "lsp", "hdl", "rtl", "slang"],
            },
        ],
    }
    mpath.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _write_pack_readme(version: str) -> None:
    (PACK / "README.md").write_text(
        f"# cursor-pack (generated)\n\n"
        f"**Version:** {version}\n\n"
        "Do not edit files in this directory by hand.\n\n"
        "Regenerate from repository root:\n\n"
        "```bash\n"
        "sh scripts/sync_cursor_pack.sh\n"
        "```\n",
        encoding="utf-8",
    )


def _sync_orchestrator_inject() -> None:
    """Run SSOT sync so rtl-orchestrator-inject.sh embed matches SKILL.md."""
    sync = ROOT / "scripts" / "sync_orchestrator_inject.sh"
    if sync.is_file():
        subprocess.run(["sh", str(sync)], cwd=str(ROOT), check=True)


def main() -> None:
    os.chdir(ROOT)
    version = _read_version()
    PACK.mkdir(exist_ok=True)
    _sync_orchestrator_inject()
    _rsync_delete(ROOT / "skills", PACK / "skills")
    _rsync_delete(ROOT / "agents", PACK / "agents")
    _rsync_delete(ROOT / "domain-packages", PACK / "domain-packages")
    rh_dst = PACK / "runtime" / "hooks"
    if rh_dst.exists():
        shutil.rmtree(rh_dst)
    rh_dst.mkdir(parents=True)
    for name in os.listdir(ROOT / "hooks"):
        if name == "hooks.json":
            continue
        src = ROOT / "hooks" / name
        dst = rh_dst / name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    _sync_rules_from_templates()
    _write_plugin_json(version)
    _write_cursor_hooks_json()
    _write_root_cursor_marketplace(version)
    _write_pack_readme(version)
    jpg = ROOT / "rat_logo.jpg"
    if jpg.exists():
        shutil.copy2(jpg, PACK / "assets" / "logo.jpg")
    print(f"cursor-pack regenerated (version {version})", file=sys.stderr)


if __name__ == "__main__":
    main()
