# Spec: Upstream Sync Skill Improvements (Audit Follow-up)

## Overview

A June 2026 audit of `kamma/upstream_sync/` found the core machinery sound
(SHA-anchored range → prep manifest → manifest-verified pull → finalize), but
identified one verified bug, heavy documentation duplication, one
high-friction workflow rule, dead/duplicated script code, and an opportunity
to replace manual model switching with Claude Code subagent dispatch.
This thread implements all accepted audit items.

## What It Should Do

### 1. Fix execute_sync staging behavior (verified bug)

`execute_sync.py:224` runs `git checkout as_upstream -- .`, which updates
**both index and worktree** (empirically confirmed), while `guide.md`,
`README.md`, and `templates/sync_thread_plan.md` claim changes are left
unstaged for `git diff` review.

- Replace the checkout with a `git restore --source as_upstream --worktree -- .`
  equivalent that leaves changes **worktree-only (unstaged)** so the
  documented review-then-stage workflow works as written.
- Verify the `--stage` flag and exclusion-restore logic (step 6) still behave
  correctly with the new command, including files added/deleted upstream.
- Keep docs wording in sync with actual behavior.

### 2. Consolidate duplicated protocol docs

The Iron Rule, model-responsibility contract, stage checklists, and handoff
requirements are restated in 6 places (`guide.md`, `README.md`,
`infrastructure.md`, `stages/*.md`, `templates/sync_thread_plan.md`,
`templates/sync_thread_spec.md`); drift has already started.

- `guide.md` becomes the only canonical protocol document.
- `README.md` shrinks to: quick-start pointer, command table, file inventory
  (absorbing the still-unique parts of `infrastructure.md`).
- Delete `infrastructure.md` and `stages/` (declared legacy in
  `infrastructure.md:21`; superseded by `templates/sync_thread_plan.md`).
- Templates keep only thread-specific content (range, checkboxes, commit
  gates, restart/dispatch prompts) and reference `guide.md` for all rules
  (Iron Rule, model boundaries, handoff structure stated once, in guide.md).
- Update all cross-references repo-wide (Atomic Rename Protocol applies).

### 3. Soften the blanket blocker rule (collision-only + ack file)

Today every added upstream file without a mapping and every upstream deletion
becomes a `blocker_path` that fails `verify_manifest` and halts the automated
pull — forcing a registry-edit round-trip before Commit 1 on nearly every sync.

- `prep_analyzer.py`: an added (`A`) upstream path becomes a blocker **only
  if it collides** with an existing local path or a registered shadow/local
  target; otherwise it is reported under a new "needs classification in
  Stage 2" manifest field + report section.
- Deletions remain blockers but become clearable: a run-scoped
  `<thread_dir>/run_acknowledged_blockers.txt` (same format as
  `run_exclusions.txt`) lists acknowledged paths; `verify_manifest` treats
  acknowledged blockers as resolved. Acknowledged paths must still appear in
  the prep report so Stage 2 plans their handling.
- `guide.md` documents the new semantics and the ack-file workflow.

### 4. Subagent-based FAST dispatch (primary path, manual fallback)

- New `.claude/agents/sync-fast.md` (project-level agent definition,
  `model: sonnet`): mechanical FAST executor with the Iron Rule, files-only
  state discipline, and stop-on-ambiguity rules in its system prompt.
- `guide.md` model-switch protocol rewritten: the orchestrating session
  (Opus/ADVANCED) dispatches Stage 1, Stage 3 (batched ≤5 plan items per
  dispatch), and Stage 4.B to the `sync-fast` subagent as the normal path.
  All user-facing gates (discuss resolution, plan approval, commit gates,
  Stage 5 acceptance) stay in the parent session.
- The existing fresh-session restart-prompt template stays documented as the
  manual fallback (e.g., when running without subagent support).
- `handoff.md` requirements unchanged — subagent work is verified from files,
  not from its self-report.

### 5. Script cleanups

- **Typed round-trip:** `registry_helper.py` returns `sync_schema` dataclasses
  directly instead of validating-then-returning raw dicts; delete the
  `type AcceptedSyncState = dict[str, str]` / `PrepManifest` aliases and the
  defensive re-validation in consumers (`sync_runtime.verify_manifest`,
  `prep_analyzer`, `check_docs_parity`, `finalize_accepted_sync`,
  `execute_sync`, `init_sync_thread`). Consumers switch from key access to
  attribute access. Wide blast radius: ~10 scripts and ~14 test files import
  these helpers (incl. `tests/check_shadow_modifications.py`,
  `test_shadow_parity.py`, `test_namespace_isolation.py`,
  `test_registry_category_naming.py`).
- **Dead leniency:** make `get_modified_upstream_paths` /
  `get_string_mapping` strict (schema already guarantees shape via
  `RegistryData.from_raw`); remove unreachable lenient branches.
- **Dead CLI:** remove `print-exclusions` / `print-target-ref` subcommands
  from `sync_runtime.py` (no callers since the legacy shell wrapper was
  removed); keep `verify_manifest`. Update `tests/test_sync_state.py` and doc
  references.
- **prep_analyzer dedup:** extract a single `match_sources()` helper for the
  4× copy-pasted dir-or-exact matching loop; fix added-files-in-mapped-dirs
  appearing in both "Shadow Sources" and "New Or Unmapped" report sections.
- **Minor:** drop the redundant `git rev-parse` of an already-full SHA in
  `finalize_accepted_sync.py:70`.

## Assumptions & Uncertainties

- `git restore --source=<ref> --worktree -- .` is the correct unstaged
  equivalent of `git checkout <ref> -- .`; behavior with upstream-deleted
  files matches current behavior (neither deletes). To be verified
  empirically in a temp repo during implementation.
- The `sync-fast` agent file targets Claude Code subagents as documented at
  code.claude.com/docs/en/sub-agents (verified 2026-06-10): `.claude/agents/`,
  frontmatter `name`/`description`/`model`/`tools`, separate context window,
  no mid-run user interaction.
- `kamma/upstream_sync/` docs are local-only (not upstream-shadowed), so doc
  deletion/consolidation needs no registry/SMD changes. The scripts being
  edited are local infrastructure (registry category `no_sync_files` /
  fork-only) — to be confirmed against `registry.json` before editing; if any
  edited file has a registry/SMD entry, update it in the same change.
- `tests/test_upstream_sync_docs_policy.py` and
  `tests/test_thread_rename_references.py` may assert the existence of files
  being deleted/renamed — must be updated in the same phase.
- No sync is currently in flight (no active `*upstream_sync*` thread in
  `kamma/threads/`), so changing manifest semantics is safe now.

## Constraints

- `prep_manifest.json` gains a new field for needs-classification paths;
  `sync_schema.PrepManifest` must validate it. Old manifests in archived
  threads are not migrated.
- Behavior-preserving refactors only, except where the spec explicitly
  changes behavior (items 1, 3) — no new sync features.
- Pre-completion validation per project rules on every changed Python file:
  `ruff check --fix`, `ruff format`, `pyright`, `pyrefly`, targeted pytest.
  Never bare `uv run pytest`.
- `docs/` untouched (upstream-owned). All doc edits stay in
  `kamma/upstream_sync/` and `.claude/agents/`.
- Commit messages prepared per phase; user commits manually.

## How We'll Know It's Done

1. Empirical staging test: after `execute_sync.py` on a fixture repo (or
   dry-run inspection + unit test), `git diff` shows the sync changes and
   `git diff --cached` is empty.
2. The Iron Rule text, model-responsibility table, and handoff requirements
   each appear in exactly one file (`guide.md`); `rg` proves no stale
   references to `infrastructure.md` or `stages/`.
3. A prep manifest containing a non-colliding added upstream file passes
   `verify_manifest`; a colliding one fails; an acknowledged deletion passes;
   an unacknowledged one fails — all covered by tests.
4. `.claude/agents/sync-fast.md` exists; `guide.md` describes dispatch as
   primary and manual restart as fallback; templates reference, not restate.
5. All targeted sync test files pass:
   `tests/test_sync_schema.py`, `test_sync_state.py`, `test_prep_analyzer.py`,
   `test_execute_sync.py`, `test_finalize_accepted_sync.py`,
   `test_check_docs_parity.py`, `test_init_sync_thread.py`,
   `test_gen_smd_scaffold.py`, `test_validate_registry.py`,
   `test_verify_smd_coverage.py`, `test_check_shadow_modifications.py`,
   `test_upstream_sync_docs_policy.py`, `test_thread_rename_references.py`,
   plus `test_shadow_parity.py`, `test_namespace_isolation.py`,
   `test_registry_category_naming.py` (registry-helper consumers).
6. `kamma/tech.md` updated (sync workflow constraint line reflects subagent
   dispatch); `kamma/upstream_sync/README.md` reflects the new file inventory.

## What's Not Included

- No change to the checkout-overlay sync architecture (merge/rebase
  alternatives were evaluated and rejected in the audit).
- No change to registry categories, SMD structure, or shadow-parity tests.
- No dry-run of an actual upstream sync (next real sync validates end-to-end).
- No changes to `scripts/cl_dps/dpd-kamma-sync` beyond what doc consolidation
  requires (none expected).
- No removal of the FAST/ADVANCED role split itself — only its transport
  (subagent dispatch instead of manual restarts).
