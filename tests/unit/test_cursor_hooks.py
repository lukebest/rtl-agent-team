"""Cursor IDE hook envelope tests (RTL_HOOK_OUTPUT_FORMAT=cursor)."""

import json
import os

import pytest

from tests.conftest import HOOKS_DIR, REPO_ROOT, run_hook


class TestCursorWorkspaceRoots:
    """stdin may carry workspace_roots instead of cwd (Cursor common schema)."""

    def test_resolve_cwd_from_workspace_roots_verify_gate(self, tmp_project):
        hook = HOOKS_DIR / "rtl-verify-stop-gate.sh"
        env = {**os.environ, "RTL_HOOK_OUTPUT_FORMAT": "cursor"}
        payload = {"workspace_roots": [str(tmp_project)]}
        result = run_hook(hook, payload, env=env)
        assert result == {}

    def test_resolve_cwd_workspace_roots_orchestrator_no_marker(self, tmp_path):
        hook = HOOKS_DIR / "rtl-orchestrator-inject.sh"
        env = {**os.environ, "RTL_HOOK_OUTPUT_FORMAT": "cursor"}
        payload = {"workspace_roots": [str(tmp_path)]}
        result = run_hook(hook, payload, env=env)
        assert result == {}


class TestCursorHookJsonEnvelope:
    def test_stop_gate_followup_message_cursor(self, tmp_project):
        hook = HOOKS_DIR / "rtl-verify-stop-gate.sh"
        track = tmp_project / ".rat" / "state" / "rtl-modified-files.txt"
        track.parent.mkdir(parents=True, exist_ok=True)
        track.write_text("rtl/top.sv\n")
        env = {**os.environ, "RTL_HOOK_OUTPUT_FORMAT": "cursor"}
        result = run_hook(hook, {"cwd": str(tmp_project)}, env=env)
        assert "followup_message" in result
        assert "RTL Verify Gate" in result["followup_message"]

    def test_session_start_additional_context_cursor(self, tmp_project):
        hook = HOOKS_DIR / "rtl-orchestrator-inject.sh"
        env = {**os.environ, "RTL_HOOK_OUTPUT_FORMAT": "cursor"}
        result = run_hook(hook, {"cwd": str(tmp_project)}, env=env)
        assert "additional_context" in result
        assert "RTL Agent Team" in result["additional_context"]


class TestCursorPackHooksJson:
    """Generated Cursor hooks.json is valid."""

    def test_cursor_pack_hooks_schema(self):
        p = REPO_ROOT / "cursor-pack" / "hooks" / "hooks.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("version") == 1
        assert "hooks" in data
        assert "sessionStart" in data["hooks"]
