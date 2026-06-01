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
