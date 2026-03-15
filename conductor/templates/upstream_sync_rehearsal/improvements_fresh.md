# Upstream Sync Rehearsal: fresh Improvements Analysis

This document provides an exhaustive post-mortem of the March 2026 Upstream Sync Rehearsal. It identifies recurring friction points, logic gaps, and systemic failures encountered during the process to ensure future synchronizations are more robust and efficient.

## 1. Template Migration & Syntax Integrity (Mako → Jinja2)
**Issue:** During the migration from Mako to Jinja2, several templates (`help_abbrev_ru.jinja`, etc.) were left with invalid Mako syntax (`% if`, `${var}`), causing them to render as raw code rather than data.
**Recommendation:** 
- Future syncs MUST include a mandatory automated syntax validation step that greps for `${` and `%` tags in all localized `.jinja` files.
- The `plan.md` should include an explicit "Syntax Sanity Check" task before the implementation phase is considered complete.

## 2. Absolute Namespace Isolation in GoldenDict
**Issue:** GoldenDict merges scripts and styles from multiple dictionaries into a single web view. Generic class names (`.load_js`), generic HTML IDs (`id="grammar_..."`), and global JS function names (`makeFeedback`) caused catastrophic collisions where SBS buttons wouldn't open or would toggle RU/English content instead.
**Recommendation:**
- **Strict Prefix Mandate:** Every localized dictionary MUST use a unique prefix (`ru_`, `sbs_`, `dps_`) for ALL:
    - JavaScript Data Objects (e.g., `rudata_`, `sbsdata_`).
    - JavaScript Functions (e.g., `ru_loadData`, `sbs_playAudio`).
    - HTML element IDs (e.g., `id="ru_grammar_..."`).
    - Script loader classes (e.g., `class="ru_load_js"`).
- **Template Isolation**: Localized versions should never reference shared global JS files unless they are read-only utilities. They should always bundle their own namespaced versions.

## 3. UI Structural Formatting (`.dpd` vs `.root`)
**Issue:** Localized root dictionary templates used custom classes like `.root`, which bypassed upstream's CSS rules defined for `.dpd`, resulting in missing frames and improper padding.
**Recommendation:**
- Shadow copies MUST strictly adhere to upstream's core CSS class architecture.
- Any deviation from `.dpd` for main content containers must be explicitly justified and accompanied by custom CSS in the localization folder.

## 4. Comprehensive & Performance-Optimized Cleanup
**Issue:** Initial cleanup attempts using per-file grepping timed out. High orphan counts (1,200+) made manual tracking impossible. Additionally, the script initially missed subdirectories and unique registry entries.
**Recommendation:**
- **Recursive Subfolder Protocol**: The `tests/test_shadow_cleanup.py` script must always be run with a recursive directory walker.
- **Branch-to-Branch Comparison**: The script should rely on a direct comparison between the current `HEAD` and the `as_upstream` branch to identify deleted originals.
- **Usage-First Gating**: A file should only be archived if NEITHER the original name nor its associated shadow copy name is referenced anywhere in the active codebase (excluding other archives).
- **Memory-Cached Scanning**: Future cleanup tools should pre-load the codebase into memory to perform near-instant usage checks for thousands of orphans.

## 5. Registry Management & Logic Promotion
**Issue:** Several "ghost" files (orphaned originals) were actually essential for local logic (e.g., `sbs_example.html`).
**Recommendation:**
- Establish a "Promotion" workflow: If an orphaned original is still in use, it must be either re-mapped (if upstream source moved) or promoted to the `unique_paths` section of `dps_sync_registry.json`.
- The registry must be treated as the absolute source of truth for both shadow mappings and unique exclusions.

## 6. Engineering Standards & Maintainability
**Issue:** Rapid iteration during the sync led to a cluttered root directory and confusing, undocumented helper scripts.
**Recommendation:**
- **Clean Root Mandate**: The root directory is a "No-Fly Zone" for temporary artifacts. All session tools must be purged before finalization.
- **Mandatory Header Descriptions**: Every `.py` and `.sh` file MUST start with a one-sentence purpose description. This prevents the accumulation of "mystery scripts."
- **Testable Absolute Imports**: Use `from db.families.root_info import ...` instead of `from root_info import ...`. This ensures scripts run correctly from the project root and within test environments regardless of directory depth.

## 7. Automated Substitution Pitfalls
**Issue:** Bulk replacements (e.g., adding `sbs_` prefixes) accidentally introduced escaped characters like `data-target=\"sbs_...`, which broke HTML attributes.
**Recommendation:**
- Never perform bulk automated replacements on critical templates without a subsequent "Quote Consistency" check.
- The `test_template_structure.py` should be enhanced to catch malformed HTML attributes caused by improper escaping.

## 8. Logic Alignment vs. Guesswork
**Issue:** The agent occasionally attempted to invent new logic when tests failed (e.g., renaming `update_db` functions).
**Recommendation:**
- **Mirror Upstream**: The primary fix for any shadow copy failure is to examine the original upstream source. Most "bugs" in shadow copies are actually missed upstream architectural changes.
- Layer localizations surgically on top of the original logic to keep future diffs manageable.
