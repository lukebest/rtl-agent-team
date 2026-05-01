# Cursor Marketplace Plugin — Design Summary

This document records the Cursor IDE packaging for **rtl-agent-team**. User-facing install/uninstall steps are maintained in [README.md](../../README.md) (English), [README_kr.md](../../README_kr.md) (Korean), and [README_zh.md](../../README_zh.md) (Simplified Chinese).

## Layout

| Path | Purpose |
|------|---------|
| `cursor-pack/.cursor-plugin/plugin.json` | Cursor plugin manifest ([Plugins reference](https://cursor.com/docs/reference/plugins)) |
| `cursor-pack/hooks/hooks.json` | Cursor hook schema `version: 1`, events `sessionStart`, `postToolUse`, `preToolUse`, `subagentStart`, `subagentStop`, `stop` |
| `cursor-pack/runtime/hooks/` | Copy of repository `hooks/` (POSIX scripts + `lib/`), excluding Claude `hooks.json` |
| `cursor-pack/skills/`, `agents/`, `domain-packages/` | Synced SSOT copies |
| `cursor-pack/rules/*.mdc` | Cursor rules generated from `skills/rat-init-project/templates/rules/` |
| `.cursor-plugin/marketplace.json` (repo root) | Multi-plugin marketplace listing (`rtl-agent-team` → `cursor-pack`, plus `systemverilog-lsp` GitHub pin) |

## Hook bridging

- **`RTL_HOOK_OUTPUT_FORMAT=cursor`** is set by `cursor-pack/hooks/hooks.json` commands so [`hooks/lib/hook-output-util.sh`](../../hooks/lib/hook-output-util.sh) emits Cursor JSON (`additional_context`, `permission`, `followup_message`, `{}`) instead of Claude `hookSpecificOutput`.
- **Workspace root**: [`hooks/lib/json-util.sh`](../../hooks/lib/json-util.sh) `jsonu_resolve_cwd_from_hook_input` prefers `cwd`, then `workspace_roots[0]` (Cursor common schema).
- **SessionStart routing**: [`hooks/rtl-orchestrator-inject.sh`](../../hooks/rtl-orchestrator-inject.sh) embeds the Claude envelope in a heredoc and pipes it through [`hooks/lib/format_session_start.py`](../../hooks/lib/format_session_start.py) to emit `additional_context` when `RTL_HOOK_OUTPUT_FORMAT=cursor`. Regeneration is driven by [`scripts/sync_orchestrator_inject.sh`](../../scripts/sync_orchestrator_inject.sh).

## Regeneration

From repo root:

```bash
sh scripts/sync_cursor_pack.sh
```

Uses [`scripts/generate_cursor_pack.py`](../../scripts/generate_cursor_pack.sh), runs `sync_orchestrator_inject.sh`, rsyncs SSOT trees, and rewrites manifests.

## Marketplace submission

Follow [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish): valid `.cursor-plugin/plugin.json`, documented README, hooks tested under Linux CI (`pytest tests/unit/`).
