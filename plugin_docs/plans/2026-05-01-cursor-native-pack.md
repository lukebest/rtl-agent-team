# Cursor-Native Delivery Pack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a generated `cursor-pack/` tree plus installer and gate wrappers so Cursor users get parity (rules, skills, agents, hooks runtime) with the Claude Code plugin, without a `.vsix`, using SSOT in this repo and CI-checked artifacts.

**Architecture:** A Python generator (`scripts/generate_cursor_pack.py`) copies SSOT trees (`skills/`, `agents/`, `domain-packages/`, `hooks/`) into `cursor-pack/`, emits Cursor-style rule files under `cursor-pack/rules/`, and emits thin POSIX gate scripts under `cursor-pack/gates/`. A shell wrapper `scripts/sync_cursor_pack.sh` invokes the generator (mirroring `scripts/sync_orchestrator_inject.sh`). Project install via `scripts/rat-init-cursor-project.sh` merges generated rules into the user workspace non-destructively. Tests assert directory counts and deterministic regeneration.

**Tech stack:** Python 3 (stdlib only: `argparse`, `pathlib`, `shutil`, `hashlib`), POSIX `sh`, `pytest`, existing hook scripts under `hooks/`.

**Authoritative spec:** `plugin_docs/specs/2026-05-01-cursor-plugin-design.md`

---

## File structure (created or modified)

| Path | Role |
|------|------|
| `scripts/generate_cursor_pack.py` | **Create** — SSOT → `cursor-pack/` generator |
| `scripts/sync_cursor_pack.sh` | **Create** — thin wrapper; `set -eu`; calls Python generator |
| `scripts/rat-init-cursor-project.sh` | **Create** — project-local install (merge `.cursor/rules`, optional symlink hints) |
| `cursor-pack/` | **Create (generated, committed)** — output tree; entire dir reproducible from generator |
| `cursor-pack/README.md` | **Generated** — version, install pointer, “do not edit by hand” |
| `cursor-pack/skills/` | **Generated** — copy of `skills/` |
| `cursor-pack/agents/` | **Generated** — copy of `agents/` |
| `cursor-pack/domain-packages/` | **Generated** — copy of `domain-packages/` |
| `cursor-pack/runtime/hooks/` | **Generated** — copy of `hooks/` (so gates work without repo root) |
| `cursor-pack/rules/*.mdc` | **Generated** — Cursor rules from SSOT templates |
| `cursor-pack/gates/*.sh` | **Generated** — thin wrappers calling runtime hooks with synthetic JSON stdin |
| `tests/unit/test_cursor_pack_generator.py` | **Create** — regeneration, counts, rule presence |
| `package.json` | **Modify** — add `cursor-pack` to `files` array |
| `scripts/local-ci-check.sh` | **Modify** — run `sync_cursor_pack.sh` and fail on dirty tree |
| `CHANGELOG.md` | **Modify** — new subsection for Cursor pack |
| `README.md`, `README_kr.md` | **Modify** — short “Cursor” install subsection linking spec |

---

### Task 1: Generator CLI and empty output dir

**Files:**
- Create: `scripts/generate_cursor_pack.py`
- Create: `tests/unit/test_cursor_pack_generator.py`
- Modify: (none yet)

- [ ] **Step 1: Write failing test — script must exist and print usage**

```python
# tests/unit/test_cursor_pack_generator.py
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GEN = REPO_ROOT / "scripts" / "generate_cursor_pack.py"


def test_generate_script_exists():
    assert GEN.is_file(), f"Missing {GEN}"


def test_help_exits_zero():
    r = subprocess.run(
        [sys.executable, str(GEN), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert r.returncode == 0
    assert "usage" in (r.stdout + r.stderr).lower()
```

- [ ] **Step 2: Run test — expect failure on missing script**

Run: `pytest tests/unit/test_cursor_pack_generator.py::test_generate_script_exists -v`

Expected: **FAIL** — `AssertionError: Missing .../generate_cursor_pack.py`

- [ ] **Step 3: Minimal generator with `--help` and `--out` default**

```python
#!/usr/bin/env python3
"""Generate cursor-pack/ from SSOT. Invoked by scripts/sync_cursor_pack.sh."""
from __future__ import annotations

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    p = argparse.ArgumentParser(description="Build cursor-pack from rtl-agent-team SSOT.")
    p.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "cursor-pack",
        help="Output directory (default: ./cursor-pack)",
    )
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text(
        "# cursor-pack (generated)\n\nRun: `sh scripts/sync_cursor_pack.sh`\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_cursor_pack_generator.py -v`

Expected: **PASS**

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_cursor_pack.py tests/unit/test_cursor_pack_generator.py
git commit -m "feat(cursor-pack): add generator stub and tests"
```

---

### Task 2: Copy SSOT trees into cursor-pack

**Files:**
- Modify: `scripts/generate_cursor_pack.py`
- Modify: `tests/unit/test_cursor_pack_generator.py`

- [ ] **Step 1: Write failing test — expect skill dir count 97 after generate**

Append to `test_cursor_pack_generator.py`:

```python
import shutil


def test_generated_skills_count_matches_ssot(tmp_path):
    skills_ssot = REPO_ROOT / "skills"
    ssot_n = len([d for d in skills_ssot.iterdir() if d.is_dir()])
    out = tmp_path / "cpack"
    r = subprocess.run(
        [sys.executable, str(GEN), "--out", str(out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    gen_skills = out / "skills"
    assert gen_skills.is_dir()
    gen_n = len([d for d in gen_skills.iterdir() if d.is_dir()])
    assert gen_n == ssot_n
```

- [ ] **Step 2: Run test — expect FAIL** until copy logic exists.

Run: `pytest tests/unit/test_cursor_pack_generator.py::test_generated_skills_count_matches_ssot -v`

Expected: **FAIL** — missing `skills/` under output or wrong count.

- [ ] **Step 3: Implement `_copy_tree` and copy `skills`, `agents`, `domain-packages`**

Add to `generate_cursor_pack.py` (keep `main()` calling these after mkdir):

```python
import shutil


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def build_pack(out: Path, repo: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _copy_tree(repo / "skills", out / "skills")
    _copy_tree(repo / "agents", out / "agents")
    _copy_tree(repo / "domain-packages", out / "domain-packages")
    (out / "README.md").write_text(
        "# cursor-pack (generated)\n\n"
        "Do not edit files here by hand. "
        "Regenerate: `sh scripts/sync_cursor_pack.sh`\n",
        encoding="utf-8",
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Build cursor-pack from rtl-agent-team SSOT.")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "cursor-pack")
    args = p.parse_args()
    build_pack(args.out.resolve(), REPO_ROOT)
```

Wire `argparse` to call `build_pack` instead of only writing README.

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_cursor_pack_generator.py -v`

Expected: **PASS**

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_cursor_pack.py tests/unit/test_cursor_pack_generator.py
git commit -m "feat(cursor-pack): copy skills, agents, domain-packages into output"
```

---

### Task 3: Copy hooks runtime + parity tests for agents

**Files:**
- Modify: `scripts/generate_cursor_pack.py`
- Modify: `tests/unit/test_cursor_pack_generator.py`

- [ ] **Step 1: Add test for `runtime/hooks` and agent file count**

```python
def test_runtime_hooks_and_agents_parity(tmp_path):
    agents_ssot = len(list((REPO_ROOT / "agents").glob("*.md")))
    out = tmp_path / "cpack"
    subprocess.run(
        [sys.executable, str(GEN), "--out", str(out)],
        cwd=REPO_ROOT,
        check=True,
    )
    rh = out / "runtime" / "hooks"
    assert rh.is_dir()
    assert (rh / "rtl-verify-stop-gate.sh").is_file()
    gen_agents = len(list((out / "agents").glob("*.md")))
    assert gen_agents == agents_ssot
```

- [ ] **Step 2: Run test — FAIL** until hooks copied.

- [ ] **Step 3: Copy `hooks/` to `out / "runtime" / "hooks"`** inside `build_pack`:

```python
    _copy_tree(repo / "hooks", out / "runtime" / "hooks")
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_cursor_pack.py tests/unit/test_cursor_pack_generator.py
git commit -m "feat(cursor-pack): bundle hooks under runtime/hooks for gate scripts"
```

---

### Task 4: Generated Cursor rules (.mdc)

**Files:**
- Modify: `scripts/generate_cursor_pack.py`
- Modify: `tests/unit/test_cursor_pack_generator.py`

**Rule:** Cursor rule files use `.mdc` extension; include YAML frontmatter with `description` and optional `globs`. Exact schema may vary by Cursor version — keep frontmatter minimal and document in README.

- [ ] **Step 1: Test asserts two core rules exist**

```python
def test_rules_mdc_generated(tmp_path):
    out = tmp_path / "cpack"
    subprocess.run(
        [sys.executable, str(GEN), "--out", str(out)],
        cwd=REPO_ROOT,
        check=True,
    )
    rules = out / "rules"
    assert (rules / "rtl-coding-conventions.mdc").is_file()
    assert (rules / "rtl-verification-gate.mdc").is_file()
    body = (rules / "rtl-coding-conventions.mdc").read_text(encoding="utf-8")
    assert body.startswith("---")
    assert "description:" in body
```

- [ ] **Step 2: Run test — FAIL**

- [ ] **Step 3: Implement `rules/` generation** — read SSOT template text from `skills/rat-init-project/templates/rules/rtl-coding-conventions.md` and `rtl-verification-gate.md`, wrap each in `.mdc` frontmatter:

```python
RULE_TEMPLATE_DIR = "skills/rat-init-project/templates/rules"


def _write_mdc(out_rules: Path, name: str, body_md: str, globs: str | None) -> None:
    out_rules.mkdir(parents=True, exist_ok=True)
    globs_line = f"globs:\n  - {globs}\n" if globs else "globs:\n  - \"**/*\"\n"
    mdc = f"""---
description: RAT — {name.replace('-', ' ')}
{globs_line}---
{body_md}
"""
    (out_rules / f"{name}.mdc").write_text(mdc, encoding="utf-8")


def _emit_rules(out: Path, repo: Path) -> None:
    tpl = repo / RULE_TEMPLATE_DIR
    conv = (tpl / "rtl-coding-conventions.md").read_text(encoding="utf-8")
    gate = (tpl / "rtl-verification-gate.md").read_text(encoding="utf-8")
    _write_mdc(out / "rules", "rtl-coding-conventions", conv, "**/*.sv")
    _write_mdc(out / "rules", "rtl-verification-gate", gate, "**/*.sv")
```

Call `_emit_rules(out, repo)` from `build_pack`.

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_cursor_pack.py tests/unit/test_cursor_pack_generator.py
git commit -m "feat(cursor-pack): emit .mdc rules from rat-init templates"
```

---

### Task 5: Gate wrapper scripts (verify stop)

**Files:**
- Modify: `scripts/generate_cursor_pack.py`
- Modify: `tests/unit/test_cursor_pack_generator.py`

- [ ] **Step 1: Test — gate script exists and runs hook with cwd JSON**

```python
def test_verify_gate_wrapper_no_rat_project(tmp_path, monkeypatch):
    out = tmp_path / "cpack"
    subprocess.run(
        [sys.executable, str(GEN), "--out", str(out)],
        cwd=REPO_ROOT,
        check=True,
    )
    gate = out / "gates" / "cursor-verify-stop.sh"
    assert gate.is_file()
    monkeypatch.chdir(tmp_path)
    r = subprocess.run(
        ["sh", str(gate)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
```

Matches `TestLegacyDirFallback.test_hooks_exit_cleanly_in_non_project`: hooks return exit 0 and JSON `continue: true` when no `.rat` marker path — `run_hook` parses JSON; the hook script’s exit code should still be 0. If not, align wrapper or assert documented rc from `subprocess` vs `run_hook` parity.

- [ ] **Step 2: Run test — FAIL** until `gates/cursor-verify-stop.sh` generated.

- [ ] **Step 3: Emit `gates/cursor-verify-stop.sh`** as static text from generator:

```python
import os

GATE_VERIFY_STOP = """#!/bin/sh
# Run RTL verify stop check using bundled hooks (same semantics as Claude Code Stop hook).
# stdin contract matches tests/unit/test_hooks.py (minimal {"cwd":...}).
# Usage: sh gates/cursor-verify-stop.sh  (from user project root)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
printf '{"cwd":"%s"}\\n' "$(pwd)" | sh "$ROOT/runtime/hooks/rtl-verify-stop-gate.sh"
"""


def _emit_gates(out: Path) -> None:
    gd = out / "gates"
    gd.mkdir(parents=True, exist_ok=True)
    p = gd / "cursor-verify-stop.sh"
    p.write_text(GATE_VERIFY_STOP, encoding="utf-8")
    os.chmod(p, 0o755)
```

Call `_emit_gates(out)` from `build_pack`. Cross-check stdin with `tests/unit/test_hooks.py` (`run_hook` + `{"cwd": ...}`).

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_cursor_pack.py tests/unit/test_cursor_pack_generator.py
git commit -m "feat(cursor-pack): add cursor-verify-stop gate wrapper"
```

---

### Task 6: `sync_cursor_pack.sh` and regenerate committed tree

**Files:**
- Create: `scripts/sync_cursor_pack.sh`
- Modify: `scripts/generate_cursor_pack.py` (only if wrapper passes args — optional `--repo` for testing)

- [ ] **Step 1: Add integration test — sync script exits 0**

```python
def test_sync_script_runs():
    sync = REPO_ROOT / "scripts" / "sync_cursor_pack.sh"
    assert sync.is_file()
    r = subprocess.run(["sh", str(sync)], cwd=REPO_ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
```

- [ ] **Step 2: Run test — FAIL** until script exists.

- [ ] **Step 3: Create `scripts/sync_cursor_pack.sh`**

```sh
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
```

`chmod +x scripts/sync_cursor_pack.sh`

- [ ] **Step 4: Run `sh scripts/sync_cursor_pack.sh`** — creates `cursor-pack/` with full content; add entire `cursor-pack/` to git.

Run: `pytest tests/unit/test_cursor_pack_generator.py::test_sync_script_runs -v`

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_cursor_pack.sh cursor-pack/
git commit -m "feat(cursor-pack): add sync script and generated cursor-pack bundle"
```

---

### Task 7: `rat-init-cursor-project.sh` (project install)

**Files:**
- Create: `scripts/rat-init-cursor-project.sh`
- Modify: `tests/unit/test_cursor_pack_generator.py` or new test file

- [ ] **Step 1: Test installs rules into temp project**

```python
def test_rat_init_cursor_installs_rules(tmp_path):
    init = REPO_ROOT / "scripts" / "rat-init-cursor-project.sh"
    assert init.is_file()
    ws = tmp_path / "proj"
    ws.mkdir()
    r = subprocess.run(
        ["sh", str(init), str(ws)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert (ws / ".cursor" / "rules" / "rtl-coding-conventions.mdc").is_file()
```

- [ ] **Step 2: Run — FAIL** until script exists.

- [ ] **Step 3: Implement non-destructive copy** — same spirit as `skills/rat-init-project/scripts/install_project_templates.sh`: if destination `.cursor/rules/*.mdc` exists, skip or use `rat-version` compare if you add markers to generated rules in a follow-up. **Minimal v1:** skip if file exists.

```sh
#!/bin/sh
# Install Cursor rules from generated cursor-pack into a user workspace.
# Usage: sh scripts/rat-init-cursor-project.sh [workspace]
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WS="${1:-$(pwd)}"
SRC_RULES="$ROOT_DIR/cursor-pack/rules"
DST_RULES="$WS/.cursor/rules"
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
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit**

```bash
git add scripts/rat-init-cursor-project.sh tests/unit/test_cursor_pack_generator.py
git commit -m "feat(cursor): add rat-init-cursor-project workspace installer"
```

---

### Task 8: CI gate + package.json + docs

**Files:**
- Modify: `scripts/local-ci-check.sh`
- Modify: `package.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`, `README_kr.md`

- [ ] **Step 1: Extend local-ci-check** — after existing checks, add:

```sh
if command -v python3 >/dev/null 2>&1; then
  sh scripts/sync_cursor_pack.sh
  if ! git diff --exit-code cursor-pack/; then
    echo "error: cursor-pack/ out of date; run sh scripts/sync_cursor_pack.sh" >&2
    exit 1
  fi
fi
```

(Use the repo’s existing style for `git diff`; if `local-ci-check.sh` uses `set -e`, ensure compatibility.)

- [ ] **Step 2: Add `"cursor-pack"` to `package.json` → `files` array**

- [ ] **Step 3: CHANGELOG** — under `[Unreleased]` or new version section: “Cursor-native `cursor-pack/` bundle + `sync_cursor_pack.sh` + `rat-init-cursor-project.sh`”.

- [ ] **Step 4: README** — 5–10 lines: prerequisites (Python 3), `sh scripts/sync_cursor_pack.sh`, `sh scripts/rat-init-cursor-project.sh /path/to/rtl-project`, link `plugin_docs/specs/2026-05-01-cursor-plugin-design.md`.

- [ ] **Step 5: Commit**

```bash
git add scripts/local-ci-check.sh package.json CHANGELOG.md README.md README_kr.md
git commit -m "chore(cursor-pack): ci drift check, npm files list, and docs"
```

---

### Task 9: Extend structural tests + full pytest

**Files:**
- Modify: `tests/unit/test_agent_skill_structure.py` (optional: add one test importing cursor-pack skill count)
- Run: full unit suite per CLAUDE.md (`pytest tests/unit/ -x -q`)

- [ ] **Step 1: Add `test_cursor_pack_skills_parity`** asserting `cursor-pack/skills` dir count equals `skills/` (97).

- [ ] **Step 2: Run `pytest tests/unit/test_cursor_pack_generator.py -v`**

- [ ] **Step 3: Run `pytest tests/unit/ -x -q`**

Expected: all green.

- [ ] **Step 4: Fix any drift or hook JSON mismatch**

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_cursor_pack_generator.py
git commit -m "test(cursor-pack): parity assertions and suite green"
```

---

## Spec coverage checklist (self-review)

| Spec § | Requirement | Task(s) |
|--------|-------------|---------|
| G1 | Project-first rules install | 7 |
| G2 | Global install (optional symlink) | Document only in README Task 8 (exact paths version-dependent per spec §12) |
| G3 | M3 parity skills/agents | 2, 3, 9 |
| G4 | SSOT + CI-checked generation | 6, 8 |
| G5 | Gate approximation | 5, 3 |
| G6 | Version alignment | README points to semver; optional: emit `VERSION` file in `cursor-pack/` in Task 6 reading `package.json` — add if gap found |
| NG3 | LSP documented, not bundled | README Task 8 |

**Gap / optional follow-up:** Global symlink installer script (spec §5.2) — add small `scripts/cursor-global-link.sh` in a later PR once Cursor global paths are pinned for a supported Cursor release.

---

## Execution handoff

**Plan complete and saved to `plugin_docs/plans/2026-05-01-cursor-native-pack.md`. Two execution options:**

**1. Subagent-driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development.

**2. Inline execution** — Run tasks in one session with checkpoints. **REQUIRED SUB-SKILL:** superpowers:executing-plans.

**Which approach?**
