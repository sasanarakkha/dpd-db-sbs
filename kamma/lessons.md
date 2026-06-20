- 2026-05-03 [POSITIVE] Stage 4 Docs Parity script drastically simplified translation tracking and validation.
- 2026-05-03 [WORKFLOW] Symlinking no-translate docs (e.g., changelog.md) ensures permanent parity with zero maintenance cost.
- 2026-05-03 [BEHAVIOR] The "mechanical executor" quality gate for handoffs between PRO and FAST models prevents implementation drift.
- 2026-04-10 [BEHAVIOR] Use MagicMock for headless GUI initialization tests instead of subprocess.Popen to avoid hanging terminal sessions.
- 2026-04-11 [BEHAVIOR] kamma/archive is git-ignored; do not attempt to track thread archives in git.
2026-04-16 [WORKFLOW] Narrowed search scope (e.g., to thread directory) for issue references avoids noise from unrelated files.
2026-04-26 [POSITIVE] Thread successfully added a third locale (Tamil), proving the shadow/layered pattern scales well.
2026-04-26 [WORKFLOW] Found and fixed registry gaps during implementation; a pre-task 'registry audit' step could prevent this.
- 2026-05-19 [BEHAVIOR] UI migrations (e.g., to `printer.py`) must include a "runtime sweep" to catch undefined variables (NameErrors) in rarely-triggered code paths or GUI callbacks.
- 2026-05-04 [POSITIVE] One-shot scripts can accept minor output nits (e.g., double-prefixes in edge cases) if data is correct and user reviews dry-run before committing.
- 2026-05-28 [WORKFLOW] The MCP Pali analysis feedback-loop thread must not be archived or finalized without an explicit passed review and user confirmation that all issues are resolved.
- 2026-06-01 [WORKFLOW] In tool-driven checks, avoid Fish-only `and`/`or` conditionals unless the shell is verified; shell-neutral probes prevent false command failures.
- 2026-06-06 [POSITIVE] Checker script (sbs_anki_fields_check.py) immediately surfaced a real field-name divergence (examples_or_words vs examples) in anki_csv.py — validating the gate-before-import pattern as highly effective for catching silent drift.
- 2026-06-09 [BEHAVIOR] In Flet, `setattr()` applied post-construction bypasses `__init__` monkeypatches — guard against this by skipping the patched attribute in setattr loops and adding a post-init hook.
- 2026-06-09 [BEHAVIOR] In Flet, setting `ft.TextStyle(size=N)` in `page.theme.text_theme` / `page.theme.tabs_theme` without `color=` bypasses Flutter's color-scheme defaults, causing invisible (white-on-white) text. Constructor patching alone is the safer approach.
- 2026-06-12 [WORKFLOW] Using a long-running "loop" thread for open-ended bug fixing works well but requires a meta-review phase to determine the stopping point (e.g., Findings 1-74).
- 2026-06-12 [BEHAVIOR] When multiple remotes (origin/upstream) exist, `gh` may require explicit repository context (`-R`) to ensure comments and closures target the correct project issue.
- 2026-06-12 [WORKFLOW] For Kamma finalize cleanup, use narrow sequential filesystem commands; combined archive/delete commands can be blocked by execution policy.
- 2026-06-12 [POSITIVE] Freezing regression goldens against a specific commit hash before refactoring ensures high-confidence, byte-identical migrations.
- 2026-06-12 [WORKFLOW] The Audit-before-Port pattern for cross-folder deps effectively prevents "reconcile-everything" bloat by isolating breakage risks to a minimal edit set.
- 2026-06-12 [BEHAVIOR] Ensure the thread review accurately lists ALL changed files, including documentation, to avoid surprises during the final commit proposal.
- 2026-06-13 [POSITIVE] Switching agy transport to stdin (--print -) bypasses OS-level argv limits (MAX_ARG_STRLEN), enabling the analysis of large verses that previously failed.
- 2026-06-13 [POSITIVE] JSON-size-driven chunking with grounded-translation fallback provides a robust safety net for lone oversize sentences without requiring model-specific tokenizers.
- 2026-06-13 [POSITIVE] Anchoring internal module paths to `__file__` and deferring side-effect-heavy initialization (like directory creation) to runtime ensures cross-platform robustness and clean test isolation.
- 2026-06-19 [WORKFLOW] Mixed-hunk file staging via `git add -p` in bash scripts is error-prone; consider documenting/flagging mixed-hunk files during review and either selecting a dedicated tool or accepting simpler constraints (e.g., "exclude this file from commit").
- 2026-06-19 [BEHAVIOR] Pre-existing lint errors in unmodified lines block commits even when only a small help-text change is staged; run a full lint check on the working tree before finalization, not just on staged hunks.
- 2026-06-19 [POSITIVE] Thorough review.md (listing all files, findings, test evidence, and procedural notes) enables efficient finalization even when files have mixed hunks or procedural constraints.
- 2026-06-20 [POSITIVE] Using ask_question to confirm doc updates during finalization ensures smooth, explicit alignment on technical notes.

