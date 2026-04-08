# Upstream Sync Rehearsal: Comprehensive Improvement Analysis

This document provides a unified, exhaustive post-mortem of the Upstream Sync Rehearsal sessions. It identifies friction points, logic gaps, and systemic failures encountered during the process to ensure future synchronizations are more robust, efficient, and maintainable.

## 1. Deep Upstream Diff Analysis Before Modifying Shadow Copies
**Issue:** During the rehearsal, major upstream architectural changes (like the migration from raw HTML strings/Mako to Jinja2 templating) caused massive cascading failures. Shadow copies were updated without fully comprehending the structural shift, leading to missing attributes and `ModuleNotFoundError` exceptions. Agents missed significant upstream changes (especially in template directories) by relying solely on narrow `modified_upstream_files` lists.
**Recommendation:**
- **Pre-Update Diffing**: Always perform a thorough review of the upstream commits or `git diff` before touching the shadow copies (`*_ru.py`, `*_sbs.py`).
- **Intersection Checking**: Phase 2 (Planning) must explicitly instruct the agent to run a `git diff-tree` for the sync commit and mathematically intersect it with *every* mapped source file and directory in the registry.
- **Refactoring over Replacement**: If a structural change is detected (like a new templating engine), plan a dedicated refactoring phase for the shadow files instead of relying on simple string replacements.

## 2. Mandatory Dual-Shadow Parity Enforcement
**Issue:** Agents frequently updated one localized shadow (e.g., SBS) but neglected its sibling (e.g., RU), leading to broken builds and fragmentation.
**Recommendation:**
- Whenever an upstream source is modified, the agent MUST explicitly cross-reference the registry and update *all* mapped shadow copies (both RU and SBS) in the same implementation step.
- Update the track plan to include a mandatory "Dual-Shadow Check" task.

## 3. Strict Upstream Mirroring & Logic Alignment ("No Novel Solutions")
**Issue:** When shadow copies failed, agents occasionally attempted to "guess" fixes or invent new logic or workarounds rather than following the upstream pattern, creating long-term maintenance debt.
**Recommendation:**
- **Mirror Upstream Logic**: The explicit goal of a sync is parity. **Do not invent new solutions.**
- The primary fix for any shadow copy failure is to examine the original upstream source and emulate its logic exactly.
- Layer localizations surgically on top of the original logic to keep future diffs manageable.
- If the required upstream fix is ambiguous, pause and ask the user for clarification.

## 4. UI Namespace Isolation in GoldenDict
**Issue:** GoldenDict merges scripts and styles from multiple dictionaries into a single web view. Generic HTML IDs, CSS classes, and global JS functions caused catastrophic collisions (e.g., SBS buttons failing to open or toggling RU content). The agent erased the uniqueness of localized copies during syncs.
**Recommendation:**
- **Strict Prefix Mandate**: Every localized dictionary MUST use a unique prefix (`ru_`, `sbs_`, `dps_`) for:
    - JavaScript Data Objects (e.g., `rudata_`, `sbsdata_`).
    - JavaScript Functions (e.g., `ru_loadData`, `sbs_playAudio`).
    - HTML element IDs (e.g., `id="ru_grammar_..."`).
    - Script loader classes (e.g., `class="ru_load_js"`).
- **Never blindly overwrite** shadow copies with upstream code if it strips localized uniqueness. Add an explicit validation step before finalizing GoldenDict exporters.
- **Template Isolation**: Localized versions should bundle their own namespaced JS versions rather than referencing shared global files that might change upstream.

## 5. UI Structural Formatting (`.dpd` vs `.root`)
**Issue:** Localized templates using custom classes like `.root` bypassed upstream CSS rules defined for `.dpd`, resulting in missing frames and improper padding.
**Recommendation:**
- Shadow copies MUST strictly adhere to upstream's core CSS class architecture.
- Deviations must be explicitly justified and accompanied by custom CSS in the localization folder.

## 6. Template Migration & Syntax Integrity (Mako → Jinja2)
**Issue:** During the migration from Mako to Jinja2, several templates were left with invalid Mako syntax (`% if`, `${var}`), causing them to render as raw code.
**Recommendation:** 
- Include a mandatory automated syntax validation step that greps for `${` and `%` tags in all localized `.jinja` files.
- The `plan.md` should include an explicit "Syntax Sanity Check" task.

## 7. Dependency, Import Verification & Absolute Imports
**Issue:** Upstream architectural shifts caused `ModuleNotFoundError` in localized scripts. Relative imports also failed in root-level test environments.
**Recommendation:**
- Explicitly verify changed dependencies in shadow copies after any upstream reorganization. Resolve all missing imports before attempting to run full exporters.
- **Absolute Import Mandate**: Enforce absolute imports (`from db.families.root_info import ...`) in all shadow copies to ensure they are runnable from the project root and within tests.

## 8. Test-Driven Syncs & Automated Parity Verification
**Issue:** Many errors were only discovered deep into the build processes (e.g., running `make_dpd.sh`). `test_shadow_parity.py` often fails due to legitimate, intended localization differences.
**Recommendation:**
- Use `tests/test_shadow_parity.py` as the primary compass. Run it continuously after updating shadow copies.
- Implement an automated "Whitelist Generation" step where the agent can generate a temporary AST-based whitelist for intended divergences, allowing focus on actual regressions.
- Ensure parity scripts cover newly added templates (like checking `.jinja` parity).

## 9. Reinforced Phase Gating & User Approval
**Issue:** Agents sometimes committed partial work, advanced phases, or declared stages complete despite the existence of multiple critical bugs, prompting the user to say: *"I never gave my approval for completing this stage!"*
**Recommendation:**
- **The 3-Commit Rule**:
    1. Commit 1: Auto Sync.
    2. Commit 2: Implementation (post-testing & approval).
    3. Commit 3: Cleanup (post-retesting & approval).
- **Explicit Gating**: Introduce strict, explicit **Approval Gates** in the workflow. Agents are forbidden from committing or moving phases until explicitly asking: "Are you ready to proceed to the next stage?" and receiving a definitive affirmative answer.

## 10. Tooling Reliability, Replacing, and Sub-Agents
**Issue:** Repeated attempts to use unreliable sub-agents (like `generalist`) caused delays. The `replace` tool failed repeatedly due to `0 occurrences found`. Bulk replacements occasionally introduced escaped character artifacts (e.g., `data-target=\"sbs_...`), breaking HTML attributes.
**Recommendation:**
- Always use `read_file` to fetch the exact context before using the `replace` tool to ensure whitespace and indentation match perfectly.
- Never perform bulk replacements on templates without a subsequent "Quote Consistency" check. Enhance `test_template_structure.py` to catch malformed HTML attributes.
- If sub-agents fail or are disabled, immediately pivot to direct codebase analysis using fast shell commands (`grep`, `rg`, `git diff`) and standard file reading tools. Do not repeatedly attempt to invoke failing agents.

## 11. Formalized Cleanup, Archiving & Clean Root
**Issue:** The root directory became cluttered with temporary scripts, and tracking deleted upstream files was disorganized.
**Recommendation:**
- **Recursive Subfolder Protocol**: `tests/test_shadow_cleanup.py` must run recursively folder-by-folder for all monitored paths.
- **Usage-First Gating**: A file should only be archived if NEITHER the original name nor its associated shadow copy is referenced in the active codebase (excluding archives).
- **Archive Protocol**: Scripts move to `scripts/dps_archive/`; data moves to `archive/dps/`.
- **Clean Root Mandate**: All temporary session artifacts MUST be purged before finalization.

## 12. Continuous Template and Registry Management
**Issue:** Essential local files were flagged as orphans because their upstream sources were deleted. Reusable templates fell behind newly discovered requirements.
**Recommendation:**
- Whenever a new sync requirement is discovered, immediately update `kamma/upstream_sync/guide.md` and `kamma/upstream_sync/smd.md`.
- **Promotion Workflow**: If an orphaned original is still in use locally, it must be explicitly promoted to the `unique_paths` section of `kamma/upstream_sync/registry.json`.
- Keep `kamma/upstream_sync/registry.json` meticulously updated as the absolute source of truth for both shadow mappings and unique exclusions.

## 13. Engineering Standards for Maintainability
**Recommendation:**
- **Mandatory Header Descriptions**: EVERY new or modified `.py` and `.sh` file MUST start with a concise one-sentence description of its purpose.
- **Namespace Isolation**: Ensure unique prefixes for all global variables and element IDs to facilitate easier collaboration and multi-dictionary support.


---

## Historical: Legacy 7-Phase Workflow (Pre-April 2026)

The following workflow was replaced by the 3-stage process (Prep, Analysis, Execution) during the April 2026 sync infrastructure refactor. It is preserved here for historical context and to document the evolution of the sync protocol.

### Phase 0 — Pre-flight (Lower model)

1. Read `kamma/upstream_sync/smd.md` end-to-end. **STOP** if any entry is incomplete.
2. Read `kamma/upstream_sync/registry.json` end-to-end.
3. Run `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — **STOP** if any gaps.
4. Run `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — **STOP** if any errors.
5. Verify `sbs-ru` branch is clean: `git status` — **STOP** if dirty, document state.
6. Verify `as_upstream` tracking branch exists: `git branch -a | grep as_upstream`.
7. Create a backup tag: `git tag pre-sync-$(date +%Y%m%d)`.

### Phase 1 — Automated Sync + Commit 1 gate (Lower model)

1. Run `echo 2 | bash scripts/bash/full_sync.sh` (selective sync mode — syncs tracked
   files, skips `modified_upstream_files` and `no_sync_files`).
2. Run `git submodule init && git submodule update`.
3. Spot-check: run `git diff HEAD -- db/models.py gui2/main.py .gitignore` to verify
   protected files were NOT overwritten.
4. Present full `git diff --stat` to user.
5. **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 1".
6. Prepare commit: `sync: automated upstream pull YYYY-MM-DD`
7. Present `git add` + `git commit -m "..."` to user. NEVER run commit yourself.

### Phase 2 — Dynamic Analysis (Higher model)

1. Run `git diff HEAD^` to see what changed in the automated sync.
2. For each file in `modified_upstream_files` registry entries: run
   `git diff as_upstream -- <path>` to see what upstream has changed.
3. Cross-reference every changed upstream file against `russian_copies`,
   `sbs_copies`, and `dps_copies` in registry — list ALL shadow destinations.
4. **Triple Shadow Checklist**: Explicitly check `tools/paths.py`,
   `exporter/goldendict/templates/`, `exporter/webapp/templates/`,
   `exporter/goldendict/export_epd.py`. For each, list both shadow destinations.
5. Check `discuss` flags: for every `discuss: true` file, **STOP** and present
   `git diff as_upstream -- <path>` to user, state the `discuss_reason`, wait for
   decision before including in plan.
6. Output: Create `dynamic_plan.md` in the active thread folder with:
   - Manual Merges: which `modified_upstream_files` changed, what code blocks to port
   - Shadow Updates: each shadow file + exactly what to update + SMD sync rule
   - Documentation: new/updated upstream docs to port to `docs_rus/`

### Phase 3 — Execution (Lower model)

1. Read `dynamic_plan.md` — execute item by item.
2. For each shadow update:
   1. Read the SMD entry for this file from `kamma/upstream_sync/smd.md`.
   2. Read the upstream source file (`git show as_upstream:<path>`).
   3. Read the current shadow copy.
   4. Apply upstream changes while preserving ONLY the local changes listed in SMD.
   5. Verify namespace isolation (`ru_`, `sbs_`, `dps_` prefixes intact).
3. For each modified upstream file:
   1. Run `git diff as_upstream -- <path>` to see upstream delta.
   2. Manually integrate new upstream features while preserving local elements per SMD.
   3. If `discuss: true`, confirm user already approved in Phase 2.
4. **Dual-Shadow Parity Rule**: When updating one shadow, immediately check if a
   sibling shadow exists.
5. Run `uv run pytest tests/test_shadow_parity.py --tb=short -q` after every batch of
   shadow updates.

### Phase 4 — Logic Audit (Higher model)

1. For each `modified_upstream_files` entry: compare final state against `as_upstream`.
2. For each updated shadow copy: compare against upstream source — verify structural parity.
3. Check all `discuss: true` files received explicit user approval in Phase 2.
4. Verify Iron Rule compliance: no workarounds, no novel solutions, no alternative
   libraries not in upstream.

### Phase 5 — Testing + Commit 2 gate (Lower model)

1. Run: `uv run pytest --tb=short -q`.
2. Run: `uv run python3 tests/check_shadow_modifications.py`.
3. Run: `uv run ruff check . && uv run ruff format .`
4. Present test results summary to user.
5. **USER MANUAL VERIFICATION**: Ask user to open GoldenDict/webapp and verify
   dictionaries load correctly.
6. **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 2".
7. Prepare commit: `sync: manual merge resolutions YYYY-MM-DD`
8. Present `git add` + `git commit -m "..."` to user.

### Phase 6 — Cleanup + Orphan Archiving (Lower model)

1. Run `uv run python3 tests/test_shadow_cleanup.py`.
2. Identify orphans: files present locally but missing upstream source in `as_upstream`.
3. For each orphan:
   - Still referenced in codebase? → Promote to `unique_paths` in registry.
   - Unused? → Archive.
4. Update `kamma/upstream_sync/registry.json` with any changes.
5. Root directory audit: `ls -F` on project root — remove any temp artifacts.
6. Update `kamma/upstream_sync/smd.md` if files were added or removed.

### Phase 7 — Final Verification + Commit 3 gate (Lower model)

1. Re-run: `uv run pytest --tb=short -q`.
2. Re-run: `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py --tb=short -q`.
3. Run: `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`.
4. Run: `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`.
5. Run: `uv run ruff check . && uv run ruff format .`
6. Write `kamma/upstream_sync/new_improvements.md`.
7. Delete `dynamic_plan.md` from the active thread folder.
8. **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 3".
9. Prepare commit: `sync: cleanup and finalization YYYY-MM-DD`
10. Present `git add` + `git commit -m "..."` to user.

