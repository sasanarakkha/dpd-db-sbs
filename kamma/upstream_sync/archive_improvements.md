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

## Summary
To succeed in future syncs, the agent must act as a **careful translator** rather than an autonomous inventor. It must thoroughly diff upstream changes, translate them into the localized (RU/SBS) context while strictly preserving isolated namespaces, continuously verify with `test_shadow_parity.py`, maintain a clean environment, and unequivocally wait for explicit user sign-off at every major milestone.
