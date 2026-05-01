"""Tests for cursor-pack generator (Cursor-native delivery bundle)."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GEN = REPO_ROOT / "scripts" / "generate_cursor_pack.py"
SYNC = REPO_ROOT / "scripts" / "sync_cursor_pack.sh"
INIT_CURSOR = REPO_ROOT / "scripts" / "rat-init-cursor-project.sh"


def test_generate_script_exists():
    assert GEN.is_file(), f"Missing {GEN}"


def test_help_exits_zero():
    result = subprocess.run(
        [sys.executable, str(GEN), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "usage" in (result.stdout + result.stderr).lower()


def test_generated_skills_count_matches_ssot(tmp_path):
    skills_ssot = REPO_ROOT / "skills"
    ssot_n = len([d for d in skills_ssot.iterdir() if d.is_dir()])
    out = tmp_path / "cpack"
    subprocess.run(
        [sys.executable, str(GEN), "--out", str(out)],
        cwd=REPO_ROOT,
        check=True,
    )
    gen_skills = out / "skills"
    assert gen_skills.is_dir()
    gen_n = len([d for d in gen_skills.iterdir() if d.is_dir()])
    assert gen_n == ssot_n


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
    result = subprocess.run(
        ["sh", str(gate)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_sync_script_runs():
    assert SYNC.is_file()
    result = subprocess.run(
        ["sh", str(SYNC)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_rat_init_cursor_installs_rules(tmp_path):
    assert INIT_CURSOR.is_file()
    workspace = tmp_path / "proj"
    workspace.mkdir()
    subprocess.run(
        ["sh", str(SYNC)],
        cwd=REPO_ROOT,
        check=True,
    )
    result = subprocess.run(
        ["sh", str(INIT_CURSOR), str(workspace)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (workspace / ".cursor" / "rules" / "rtl-coding-conventions.mdc").is_file()


def test_cursor_pack_skills_parity_committed_tree():
    """cursor-pack/skills must stay in sync with SSOT (regenerate via sync script)."""
    pack_skills = REPO_ROOT / "cursor-pack" / "skills"
    if not pack_skills.is_dir():
        pytest.skip("cursor-pack/ not generated yet")
    ssot_n = len([d for d in (REPO_ROOT / "skills").iterdir() if d.is_dir()])
    gen_n = len([d for d in pack_skills.iterdir() if d.is_dir()])
    assert gen_n == ssot_n
