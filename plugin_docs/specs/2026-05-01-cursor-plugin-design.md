# Cursor-Native Delivery Pack — Design Spec

- **Date**: 2026-05-01
- **Status**: Draft — pending written-spec review
- **Related**: Claude Code plugin (`rtl-agent-team`), `rat-init-project`, hooks under `hooks/`

## 1. Summary

Deliver this repository’s RTL pipeline (rules, skills, agents, phase semantics, and
quality gates) as a **Cursor-native bundle**: no `.vsix` extension; installation
via **project-local** assets (recommended) with **optional global** symlink or
one-shot scripts. Enforcement targets **near-hard** gate behavior using **POSIX
shell scripts** and **`.rat/state/`** markers, matching existing hook intent where
possible. **MCP is out of scope by default**; add only if a capability gap is proven
during implementation.

The first release (**M3**) aims for **coverage parity** with the Claude Code plugin:
rules, skills, and agent prompts **reachable** from Cursor workflows without
maintaining two divergent prose corpora — achieved via **single source of truth
(SSOT)** in this repo plus **generated Cursor-facing artifacts** validated in CI.

## 2. Motivation

- Users working in **Cursor** cannot consume `.claude-plugin/plugin.json` or
  Claude Code hooks directly; they still need the same pipeline semantics.
- Duplicating 97 skills and 97 agents by hand guarantees drift (**rejected**).
- Cursor lacks Claude Code’s SessionStart / Stop hook events; **behavioral parity**
  uses documented command contracts and executable checks instead of invisible
  interception.

## 3. Goals and Non-Goals

### 3.1 Goals

| ID | Goal |
|----|------|
| G1 | **Project-first install**: deploy generated rules + instructions into a user RTL repo’s `.cursor/` (and related paths per Cursor version). |
| G2 | **Optional global install**: scripts/docs support mirroring or symlinking the same bundle into user-level Cursor config; **project overrides global**. |
| G3 | **M3 parity**: rules + skills + agents **cover the same surface** as the Claude Code plugin (counts and naming aligned; discovery paths documented). |
| G4 | **SSOT + generation**: Claude-layout sources remain authoritative; Cursor pack is **generated and CI-checked**. |
| G5 | **Gate approximation**: scripts + `.rat/state/` implement checks equivalent to critical hooks (especially verification-before-completion semantics); users/agents follow mandatory commands in docs. |
| G6 | **Version alignment**: Cursor pack version tracks existing semver sources (`package.json`, `.claude-plugin/plugin.json`, marketplace metadata). |

### 3.2 Non-Goals

| ID | Non-goal |
|----|----------|
| NG1 | **Byte-identical** hook timing vs Claude Code (no Stop event injection in Cursor). |
| NG2 | **MCP-first** or MCP-required architecture (optional future only). |
| NG3 | **Bundling SystemVerilog LSP** inside this pack; document recommended LSP setup separately (same upstream lineage as `systemverilog-lsp` sub-plugin). |
| NG4 | **Open VSX / VSIX** publication as the primary delivery mechanism. |

## 4. Architecture

### 4.1 Single source of truth (SSOT)

- **Skills**: `skills/*/SKILL.md` and related assets.
- **Agents**: `agents/*.md` and `agents/lib/*.md`.
- **Deployable rules/guides**: `skills/rat-init-project/templates/` (and other
  rat-init sources as applicable).
- **Hook semantics**: `hooks/*.sh` and `hooks/lib/*.sh` define **expected state
  transitions and checks**; Cursor does not execute these hooks — **gate scripts**
  embed or call equivalent checks.

### 4.2 Generated Cursor pack

Introduce a **generated output tree** (exact directory name fixed at
implementation time; examples: `cursor-pack/`, `dist/cursor/`). Contents include:

- Cursor **rules** (format follows Cursor’s supported rule file conventions at
  implementation time, e.g. `.mdc` with frontmatter).
- Cursor-discoverable **skills** (full copies or thin wrappers — **prefer full
  generated copies** for reliable discovery).
- **Install manifest** listing files and target paths for project vs global layout.
- **Gate scripts** directory: POSIX `sh` where possible; invoke existing helpers
  under `scripts/` when sharing logic avoids duplication.

**Generation entrypoint**: `scripts/sync_cursor_pack.sh` (name tentative).

**CI**: fail if SSOT changes without regenerated pack or if generator output
drifts from committed artifacts.

### 4.3 Behavioral mapping (hooks → gates)

| Claude Code concept | Cursor pack replacement |
|---------------------|-------------------------|
| SessionStart injection | Rule files + onboarding doc (“read routing table from …”) |
| PreToolUse / PostToolUse hooks | Not replicated inside the editor; **optional** local git hooks documented separately |
| Stop / verify gates | **Mandatory** shell scripts + `.rat/state/` checks; documented **must-run** before claiming completion |
| Team mode hooks | Out of band; document Cursor-native team patterns if applicable |

## 5. Installation Model

### 5.1 Project-level (recommended)

- Command surface (name tentative): `rat-init-cursor-project` or equivalent shell
  entry under `scripts/` that:
  - Copies or merges generated rules into `<project>/.cursor/rules/` (or current
    Cursor equivalent).
  - Ensures `.rat/` state directory conventions match existing plugin docs.
  - Does **not** overwrite user-owned files without prompt or merge strategy
    (follow `rat-init-project` non-destructive norms).

### 5.2 Global-level (optional)

- Document + script: symlink or copy the **same generated bundle** into the user’s
  global Cursor rules/skills location. Exact paths **must** be read from Cursor
  documentation at implementation time and encapsulated in one shell helper to
  avoid scattering path literals.

### 5.3 Precedence

- **Project overrides global** for conflicting rule content.

## 6. Rules, Skills, and Agents Mapping

### 6.1 Rules

- Map `rat-init-project` template rules and pipeline-critical excerpts from
  `CLAUDE.md` / `.claude/rules` analogs into generated Cursor rules.
- Preserve **English-only** LLM-consumed text per project policy.

### 6.2 Skills

- Every action/policy skill in SSOT has a **generated** Cursor-facing SKILL with
  stable name and description for discovery.
- Routing SSOT remains `skills/rtl-orchestrate/SKILL.md`; generation includes
  condensed routing for Cursor session bootstrap where applicable.

### 6.3 Agents

- Cursor may not have first-class “agents”; generated skills **reference** agent
  files by path (e.g. “Assume role per `agents/<name>.md`”).
- All `agents/*.md` remain in-repo and are **included or referenced** such that M3
  coverage is satisfied.

## 7. Gate Enforcement (No MCP by Default)

- **State files**: Continue using `.rat/state/` filenames and semantics aligned
  with existing hooks (`rtl-verify-done`, waivers, etc.) — **no parallel Cursor-only
  state vocabulary** unless unavoidable (if introduced, document explicit mapping).
- **Scripts**: Provide explicit commands users/agents run after RTL edits, before
  session wrap-up, or in CI; mirror escalation ladders from existing stop gates
  **behaviorally** (not necessarily identical message text).
- **Git hooks**: Offer **optional** `pre-commit` / `pre-push` snippets in docs only;
  do not enable silently.
- **MCP**: Only if a required check cannot be implemented via shell + repo state;
  requires separate mini-spec and explicit version gate.

## 8. LSP and Tooling

- Document installation/configuration for SystemVerilog LSP consistent with the
  existing `systemverilog-lsp` sub-plugin lineage (slang/slang-server).
- Do not vendor LSP binaries inside this repository’s Cursor pack.

## 9. Testing and CI

- Extend unit tests to cover:
  - Generator idempotency and file counts vs SSOT expectations.
  - No forbidden Claude-only path references in generated Cursor rules when
    inappropriate for user-project CWD.
  - Critical frontmatter fields present on generated skills/rules.
- Integration smoke: run generator in CI and diff against committed tree.

## 10. Documentation and Release

- **CHANGELOG.md**: Cursor pack section per release.
- **README.md / README_kr.md**: Short “Cursor installation” subsection linking to
  `plugin_docs/specs/2026-05-01-cursor-plugin-design.md` implementation notes once
  shipped.

## 11. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Cursor changes rules/skill discovery format | Encapsulate paths and formats in generator + pin Cursor compatibility note in README |
| Generator drift | CI gate on `sync_cursor_pack` output |
| Users skip gate scripts | Strong wording in rules + optional git hooks |
| Scope creep (MCP) | Require design amendment before adding MCP |

## 12. Open Points (Implementation Phase)

These are **not** ambiguities in approved intent; they are deferred to the
implementation plan where Cursor’s current docs define exact filenames:

- Exact Cursor rule file extension and frontmatter schema for the target Cursor
  release.
- Exact global vs workspace skill directory names for that release.
- Final name for `scripts/sync_cursor_pack.sh` and init script entrypoints.

## 13. Approval Record

- **Brainstorming approval**: 2026-05-01 — user confirmed all design sections
  (Cursor-native B model, dual install 3, gate level C, MCP minimal 3, M3 scope).

---

*Next step after written-spec review: implementation plan via `writing-plans`
workflow (separate session/skill per project process).*
