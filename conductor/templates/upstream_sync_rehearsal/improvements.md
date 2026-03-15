# Upstream Sync Rehearsal: Improvement Suggestions

Based on a comprehensive analysis of the session history, user feedback, and error reports from the recent synchronization track, the following systemic improvements should be integrated into the workflow and templates (`plan.md`, `guide.md`) to prevent recurring issues in future syncs.

## 1. Automated Non-Interactive Sync Execution
**Issue:** The automated sync script (`scripts/bash/full_sync.sh` or `makedict.py`) originally required interactive user input to select options, causing the AI agent to stall or fail.
**Improvement:** 
- The `plan.md` template must explicitly mandate running sync scripts non-interactively (e.g., using `echo 2 | bash ...` or a dedicated non-interactive script flag). 
- Ensure the agent does not attempt to use interactive shell sessions.

## 2. Mandatory Dual-Shadow Parity Enforcement
**Issue:** The agent frequently updated one localized shadow copy (e.g., `exporter/goldendict/main_sbs.py`) but neglected to update its sibling (e.g., `exporter/goldendict/main_ru.py`).
**Improvement:**
- Enforce a strict **"Dual-Shadow Check"** in `guide.md` and `plan.md`. 
- Whenever an upstream file (e.g., `main.py`) is modified, the agent MUST explicitly cross-reference the registry and update *all* mapped shadow copies (both RU and SBS) in the same implementation step.

## 3. Strict UI Namespace Isolation
**Issue:** During the migration from Mako to Jinja2, the agent lost the unique HTML IDs and JavaScript function names required to run the RU and SBS GoldenDict dictionaries side-by-side. This caused button collisions.
**Improvement:**
- Add a **"Namespace Isolation"** rule to the engineering standards in the template. 
- All HTML IDs, CSS classes, JS data objects, and global functions in localized templates MUST carry a distinct prefix (`ru_`, `sbs_`, `dps_`) to prevent global scope pollution in GoldenDict.

## 4. Comprehensive Source-to-Shadow Diffing
**Issue:** The agent missed significant upstream changes (especially in `exporter/goldendict/templates/`) because it relied too heavily on the narrow `modified_upstream_files` list instead of checking the actual `git diff` of upstream sources.
**Improvement:**
- The Dynamic Planning Phase (Phase 2) must explicitly instruct the PRO model to run a `git diff-tree` for the sync commit and mathematically intersect it with *every* value (upstream source) listed in `russian_copies` and `sbs_copies` in the registry.

## 5. Dependency and Import Verification
**Issue:** Upstream's transition from Mako to Jinja2 caused `ModuleNotFoundError` in localized scripts (`tpr_exporter_ru.py`) because the shadow copies were not updated to reflect the new dependency tree. Furthermore, test imports failed due to relative pathing issues (`root_info`).
**Improvement:**
- Add a step to explicitly verify missing or changed dependencies in shadow copies if an upstream architectural shift is detected.
- Enforce the use of absolute imports (`from db.families.root_info import ...`) in all shadow copies to ensure testability from the project root.

## 6. Sub-Agent Reliability Fallbacks
**Issue:** The agent repeatedly attempted to use a sub-agent (`generalist`) that failed, causing frustration and delays.
**Improvement:**
- The agent should be instructed to rely on direct codebase analysis using fast shell commands (`grep`, `rg`, `git diff`) and standard file reading tools rather than delegating critical semantic analysis to unreliable sub-agents.

## 7. Formalized Cleanup and Archiving
**Issue:** The root directory became cluttered with temporary helper scripts, and tracking deleted upstream files against local shadows was chaotic.
**Improvement:**
- The newly developed `tests/test_shadow_cleanup.py` must become a permanent, mandatory step in the finalization phase (`plan.md`). 
- The **Clean Root Folder Protocol** must be strictly enforced before the final user approval gate.
