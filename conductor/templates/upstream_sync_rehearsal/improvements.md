# Upstream Sync Rehearsal: Comprehensive Improvement Analysis

This document provides a unified, exhaustive post-mortem of the Upstream Sync Rehearsal sessions. It identifies friction points, logic gaps, and systemic failures encountered during the process to ensure future synchronizations are more robust, efficient, and maintainable.

## 1. Mandatory Dual-Shadow Parity Enforcement
**Issue:** Agents frequently updated one localized shadow (e.g., SBS) but neglected its sibling (e.g., RU), leading to broken builds and fragmentation.
**Recommendation:**
- Whenever an upstream source is modified, the agent MUST explicitly cross-reference the registry and update *all* mapped shadow copies (both RU and SBS) in the same implementation step.
- Update the track plan to include a mandatory "Dual-Shadow Check" task.

## 2. Strict Upstream Mirroring & Logic Alignment
**Issue:** When shadow copies failed, agents occasionally attempted to "guess" fixes or invent new logic that diverged from upstream, creating long-term maintenance debt.
**Recommendation:**
- **Mirror Upstream Logic**: The primary fix for any shadow copy failure is to examine the original upstream source and emulate its logic exactly.
- Layer localizations surgically on top of the original logic to keep future diffs manageable.
- Discourage arbitrary "cleanup" or refactoring during sync unless it aligns with upstream shifts.

## 3. UI Namespace Isolation in GoldenDict
**Issue:** GoldenDict merges scripts and styles from multiple dictionaries into a single web view. Generic HTML IDs, CSS classes, and global JS functions caused catastrophic collisions (e.g., SBS buttons failing to open or toggling RU content).
**Recommendation:**
- **Strict Prefix Mandate**: Every localized dictionary MUST use a unique prefix (`ru_`, `sbs_`, `dps_`) for:
    - JavaScript Data Objects (e.g., `rudata_`, `sbsdata_`).
    - JavaScript Functions (e.g., `ru_loadData`, `sbs_playAudio`).
    - HTML element IDs (e.g., `id="ru_grammar_..."`).
    - Script loader classes (e.g., `class="ru_load_js"`).
- **Template Isolation**: Localized versions should bundle their own namespaced JS versions rather than referencing shared global files that might change upstream.

## 4. UI Structural Formatting (`.dpd` vs `.root`)
**Issue:** Localized templates using custom classes like `.root` bypassed upstream CSS rules defined for `.dpd`, resulting in missing frames and improper padding.
**Recommendation:**
- Shadow copies MUST strictly adhere to upstream's core CSS class architecture.
- Deviations must be explicitly justified and accompanied by custom CSS in the localization folder.

## 5. Template Migration & Syntax Integrity (Mako → Jinja2)
**Issue:** During the migration from Mako to Jinja2, several templates were left with invalid Mako syntax (`% if`, `${var}`), causing them to render as raw code.
**Recommendation:** 
- Include a mandatory automated syntax validation step that greps for `${` and `%` tags in all localized `.jinja` files.
- The `plan.md` should include an explicit "Syntax Sanity Check" task.

## 6. Comprehensive Source-to-Shadow Diffing
**Issue:** Agents missed significant upstream changes (especially in template directories) by relying solely on narrow `modified_upstream_files` lists.
**Recommendation:**
- Phase 2 (Planning) must explicitly instruct the agent to run a `git diff-tree` for the sync commit and mathematically intersect it with *every* mapped source file and directory in the registry.

## 7. Dependency, Import Verification & absolute imports
**Issue:** Upstream architectural shifts (like Mako to Jinja2) caused `ModuleNotFoundError` in localized scripts. Relative imports also failed in root-level test environments.
**Recommendation:**
- Explicitly verify changed dependencies in shadow copies after any upstream reorganization.
- **Absolute Import Mandate**: Enforce absolute imports (`from db.families.root_info import ...`) in all shadow copies to ensure they are runnable from the project root and within tests.

## 8. Automated Parity Verification & Whitelisting
**Issue:** `test_shadow_parity.py` often fails due to legitimate, intended localization differences.
**Recommendation:**
- Implement an automated "Whitelist Generation" step where the agent can generate a temporary AST-based whitelist for intended divergences, allowing focus on actual regressions.

## 9. Formalized Cleanup, Archiving & Clean Root
**Issue:** The root directory became cluttered with temporary scripts, and tracking deleted upstream files was disorganized.
**Recommendation:**
- **Recursive Subfolder Protocol**: `tests/test_shadow_cleanup.py` must run recursively folder-by-folder for all monitored paths.
- **Usage-First Gating**: A file should only be archived if NEITHER the original name nor its associated shadow copy is referenced in the active codebase (excluding archives).
- **Archive Protocol**: Scripts move to `scripts/dps_archive/`; data moves to `archive/dps/`.
- **Clean Root Mandate**: All temporary session artifacts MUST be purged before finalization.

## 10. Registry Management & Logic Promotion
**Issue:** Essential local files were flagged as orphans because their upstream sources were deleted.
**Recommendation:**
- **Promotion Workflow**: If an orphaned original is still in use, it must be promoted to the `unique_paths` section of `dps_sync_registry.json`.
- The registry is the absolute source of truth for both shadow mappings and unique exclusions.

## 11. Reinforced Phase Gating & User Approval
**Issue:** Agents sometimes committed partial work or advanced phases while critical bugs remained.
**Recommendation:**
- **The 3-Commit Rule**:
    1. Commit 1: Auto Sync.
    2. Commit 2: Implementation (post-testing & approval).
    3. Commit 3: Cleanup (post-retesting & approval).
- **Explicit Gating**: Agents are forbidden from committing or moving phases until the user explicitly provides a signal (e.g., "Proceed with second commit").

## 12. Sub-Agent Reliability Fallbacks
**Issue:** Repeated attempts to use unreliable sub-agents caused delays.
**Recommendation:**
- Agents should rely on direct codebase analysis using fast shell commands (`grep`, `rg`, `git diff`) and standard file reading tools rather than delegating critical analysis to sub-agents.

## 13. Automated Substitution Pitfalls
**Issue:** Bulk replacements occasionally introduced escaped character artifacts (e.g., `data-target=\"sbs_...`), breaking HTML attributes.
**Recommendation:**
- Never perform bulk replacements on templates without a subsequent "Quote Consistency" check.
- Enhance `test_template_structure.py` to catch malformed HTML attributes.

## 14. Engineering Standards for Maintainability
**Recommendation:**
- **Mandatory Header Descriptions**: EVERY new or modified `.py` and `.sh` file MUST start with a concise one-sentence description of its purpose.
- **Namespace Isolation**: Ensure unique prefixes for all global variables and element IDs to facilitate easier collaboration and multi-dictionary support.
