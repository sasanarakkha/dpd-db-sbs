# Pipeline Improvement Skill

## Purpose

Slowly and continuously improve the DPS fork's unique scripts — one honest change at a time.
Review everything; change only what genuinely needs it. Coverage over churn.

**Scope**: local unique Python scripts — files listed in the `unique_paths` section of
`kamma/upstream_sync/registry.json`. The queue is in `kamma/improve/queue.md`.

## Procedure

### 1. Read state

Read `kamma/improve/queue.md` (lean — Pointer + checklist only).
Find the current **Pointer** value. That is the next script to review. The verbose
decision history lives in `kamma/improve/log.md`; read it only on
demand (e.g. to check a prior precedent), never by default.

### 2. Archive check

Run the zero-LLM archive-check script before any review work:

```bash
uv run python3 kamma/improve/scripts/archive_check.py <file_path>
```

This outputs compact JSON covering:
- **What it does** — docstring / purpose.
- **Where it fits** — what calls it, what it imports. `_find_callers()` already greps
  both the basename and the rel-path repo-wide with `rg` (no language filter), so this
  already covers shell scripts, CI configs, and Makefiles — no separate manual
  cross-check grep is needed.
- **Current status** — size, registry membership, test presence, entrypoint.

This summary is **reused verbatim** as the "What it does" block in the step 4 output
template — do not re-derive it.

Then present the summary to the user with a recommendation (Improve or Archive, derived
from the callers/registry/breakage findings above) and ask the user to reply `improve`
or `archive`:

> **Proceed with improvement, or move to archive?**
> - **Improve** — continue with the full review below.
> - **Archive** — move the file, update the queue, end session.

Do not run the second-opinion review until the user has chosen Improve — on Archive,
no API call is made.

**If the user chooses Archive:**

1. Determine the target:
   - File is under `scripts/` → move to `scripts/dps_archive/`
   - File is under any other folder → move to `archive/`
2. Run `git mv <source> <target>` to move it.
3. Remove the file's old path from `unique_paths` in `kamma/upstream_sync/registry.json`.
   `scripts/dps_archive/` and `archive/` are already covered by their own wildcard
   entries — do not add the new path, just delete the stale old-path entry. Skipping
   this step leaves a dead entry that `validate_registry.py` will not catch (it
   checks structure, not path existence).
4. Mark the script `[x] archived` in the queue and advance the Pointer.
5. Append a terse decision line to `kamma/improve/log.md`:
   `YYYY-MM-DD | #N path | archived | <one-line reason>`.
6. Stage the move, the registry update, the queue update, and the log update:
   `git add <target> kamma/upstream_sync/registry.json kamma/improve/queue.md kamma/improve/log.md`
   (use `git mv`'s staged result for the source/target rename — no separate `git rm` needed).
7. Show the proposed commit message:
   ```
   pipeline: archive <file> (#N)

   - <one-line reason>
   ```
   State the recommendation to commit and ask the user to reply `yes` or `no`.
8. If **yes**: run `git commit -m` with that message (no heredoc — user runs Fish shell).
9. Output exactly:
   > **Archived.** `<source>` → `<target>`. Queue pointer advanced to #N.
   > Start a fresh session and run `/pipeline-improvement` to continue.
10. **Stop. Do not proceed to the review steps.**

**If the user chooses Improve:** continue to step 3.

---

### 3. Review forward

Starting from the Pointer, review each pending `[ ]` script in order.
For each script:

**a. Read the file** (and any files it imports from this repo).

**b. Review across all five angles:**

1. **Role** — what does this script do? Does it do exactly that and no more?
   Does its name match its actual job?

2. **Project fit** — does it follow project conventions (modern type hints, pathlib.Path,
   no sys.path hacks, icecream for debugging, uv for deps)? Is there overlap with other
   modules that suggests better reuse? Console output must go through the printer module
   (`from tools.printer import printer as pr`) — convert any raw `rich.print` / `print()`
   to the matching `pr.*` method (`pr.red`, `pr.green`, `pr.cyan`, `pr.white`, `pr.amber`,
   `pr.yellow_title`, etc.). The printer wraps rich internally and also writes a structured
   TSV line to the build log, which raw prints bypass. Keep any rich-markup escaping intact,
   since `pr.*` still feeds rich underneath.

   **Bash scripts:** never use `echo` for terminal output. All output must go through
   `tools/ask.py`. Colors: `red`, `green`, `yellow`, `blue`, `magenta`, `cyan` (default), `white`.
   - Statements (no pause): `uv run tools/ask.py --print [-c <color>] "message"`
   - Interactive prompts (single keypress, `q` aborts): `answer=$(uv run tools/ask.py [-c <color>] "question?")`

3. **Dependencies** — what does it import? Are all imports used? What does it call, and
   what calls it? Are any dependencies stale, redundant, or pointing at the wrong
   abstraction? Check for dead code revealed by tracing the call graph.

4. **Quality** — needless complexity, missing type hints, obvious simplifications,
   unused variables, redundant logic, anything that would make a reader pause.

5. **Approach** — is there a significantly simpler or more elegant way to achieve the
   exact same result? Only raise this when the gain is substantial (e.g. hand-rolled loop
   → stdlib one-liner, 50 lines → 10, custom parser → existing utility). Do NOT raise
   for marginal style differences. If the user approves, implement it in this same session
   alongside the other changes. Surface it in the summary with both the benefit and the
   drawbacks — the user decides case by case. If there is any risk of subtle behaviour
   change, that is a drawback and must be stated.

**c. Dynamic pattern guardrails — these are NOT dead code:**
- SQLAlchemy `@cached_property` helpers
- JSON `*_pack` / `*_unpack` patterns
- Flet event handlers and callbacks
- Functions dispatched via config flags (`config_read` / `config_test`)
- `uv run -m` entrypoints and CLI main blocks

**d. Decide:**
- **Clean** → log it as `passed` in the decisions log. Advance the Pointer. Continue
  to the next script.
- **Needs a change** → stop. Do not review further. Go to step 4.

### 4. Present all changes for this file

Now that a change is needed, run the second-opinion review (substitute the actual
file path for `<file>`):

```bash
uv run python3 kamma/improve/scripts/second_opinion.py --approach-only <file>
```

`--approach-only` is the default — it only flags a significantly simpler approach and
skips style/type-hint/naming commentary, matching what actually gets accepted (see
`log.md`). If this file's own Step 3 review judged its logic unusually complex (not
just a style/convention issue), the agent may instead run the full review as an
explicit opt-in:

```bash
uv run python3 kamma/improve/scripts/second_opinion.py <file>
```

The review goes through `tools/ai_manager.py`'s `AIManager`, not a direct `agy` CLI
call. `AIManager.request()` walks the model list in `tools/ai_models.json` (antigravity_cli,
openrouter, deepseek, etc., in the order listed there) and automatically
falls through to the next model on failure — no model names need to be hardcoded or
updated in this skill file. To change the fallback order or add/remove models, edit
`tools/ai_models.json` directly.

If `response.content` is `None` (every model in `tools/ai_models.json` failed):
- **Stop and report loudly to the user:**
  `🚨 AUTOMATED REVIEW UNAVAILABLE — all models in tools/ai_models.json failed: <status_message>`
- **DO NOT proceed without a review.** Wait for the user to fix the model/network issue
  or explicitly instruct you to skip the review for this file. Never silently omit the
  reviewer cross-check.

Validate every finding from whichever model responded against the actual code.
**Do this validation silently / internally — it is your reasoning, not the
report.** Keep the conclusion for each (kept / rejected) but do NOT make the
adjudication of the reviewer the narrative. The user has no context for "this one
sticks, this one doesn't" before they even know what the findings are.

#### Output template — use this EXACT structure, in this order, every time

> **Mandatory:** Write the complete summary below — all sections, including Approach
> suggestion and Decisions — before presenting the approval block. Do not show the
> approval options until every applicable section is written.

Lead with conclusions the user can act on. The reviewer cross-check is an audit
footnote at the very bottom, never the opening.

```
## #N <path>

**What it does:** <reuse the summary written in step 2 — do not rewrite it.>

### Proposed changes
Grouped by theme (e.g. Type safety · Dead code · Consistency · Simplification).
For each: one line — WHAT changes and WHY. No reviewer back-and-forth here.
- <change> — <why>
- <change> — <why>

### Diff
<a single fenced diff covering every change to this file.>

### Not changing
Compact. One line each. Out-of-scope items and anything below the change bar.
- <thing> — <one-line reason>

### Approach suggestion *(omit entirely if none)*
- **What:** <one sentence on the simpler/more elegant approach and the gain>
- **Drawbacks:** <risk of behaviour change, migration cost, readability tradeoffs, anything that could go wrong>

### ⚠️ Special attention — required decisions *(omit entirely if none)*
Items the user MUST decide before work begins. List every genuine either/or choice
that changes what gets written. If this section exists, the user must respond to
each item before `approve` is accepted.
See "Highlighting decisions" below for how to surface these.

---
*Reviewer cross-check (<model>): agreed on <n> (<short list>); raised <m> I did
not apply — <one compressed clause each>.*

---

**STOP. Only show these options after ALL sections above are written.**

**`1` / `approve`** — apply the proposed changes only (no approach rewrite). Tests first, then edits, then commit.
**`2` / `approve all`** — apply proposed changes AND the approach suggestion (if one was listed above). Tests first, then edits, then commit.
**`3` / `skip`** — log `skipped`, advance Pointer.
**`4` / `defer`** — mark `[>]`, log `deferred`, move Pointer past it.
```

#### Highlighting decisions — make choices impossible to miss

A wall of terminal text buries the one thing the user must act on. So:

- If there is a real either/or decision (e.g. "make the cache deterministic but
  change stored output?  yes / no"), present an inline recommendation with the
  concrete options spelled out — give the context and offer the choices. Do not
  bury it in prose.
- If a decision is better left inline, mark it with a leading **`⚠️ DECISION:`**
  so it stands out in the scroll. Never phrase a decision as a buried sentence.
- The final approve / skip / defer prompt is itself a decision: put it last, on its
  own, clearly separated — never trailing a paragraph.

### 4b. Write tests — golden master FIRST, then edit

**Order is not optional. Do these in sequence. Do NOT touch the source file until
step 3 passes against the current, unedited code.**

A characterization test is worthless if written after the change — it would just
freeze whatever the edit produced. The whole point is to freeze the CURRENT output,
then prove the refactor reproduces it. Capture first, edit last.

```
Step 1: capture fixtures from CURRENT code   (source UNCHANGED)
Step 2: write test, run it GREEN             (source UNCHANGED)
Step 3: apply the approved source edits      (source CHANGED)
Step 4: run the pre-commit gate              — tests must still pass
Step 5: run the script live                  — smoke-test the real execution path
```

For a deliberate behaviour change (e.g. fixing a buggy regex): first prove the change
is byte-identical on real data where possible (scan the db), then freeze the OLD
behaviour for the unchanged cases and add explicit literal cases that lock in the NEW
intended behaviour, documenting in the test why old != new.

Tests cover **function outputs and data transformations** — not DB writes, not file I/O.
SQLAlchemy and stdlib are trusted. Test the logic that is specific to this file.

#### Step 1 — Capture fixtures from the CURRENT code (before any edits)

Do this before touching the source file. Run the function under test against real DB data
and save the output as a JSON fixture file alongside the test:

```
tests/<mirror-path>/test_<name>_fixtures.json
```

Use `uv run python3 temp/<descriptive_name>.py` to:
1. Query real headwords / records from `dpd.db` that cover every branch in the code.
2. Run the current function on each one (bypassing `__init__` with `object.__new__` if needed).
3. Dump `{key: {input_params, output}}` to the fixture file with `ensure_ascii=False`.

The existing DB output is user-confirmed correct. The fixture file freezes it. Tests then
assert the refactored code produces byte-identical results — if a change silently alters
output, a test will catch it.

#### Step 2 — Write the test file

Rules:
- No mocks. Ever. Use real data — real DB records, real files.
- Load fixtures with `json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))`.
- Use `object.__new__(ClassName)` to bypass heavy `__init__` and set only the attributes
  the function under test actually reads.
- Cover every branch: each code path needs at least one real-data case.
- Test directory mirrors source: `scripts/export/foo.py` → `tests/scripts/export/test_foo.py`
- One test file + one fixture file per script reviewed.
- After writing, run the pre-commit gate against the test file:

  ```bash
  uv run python3 kamma/improve/scripts/precommit_gate.py <source file> --test <test file>
  ```

  Confirm all pass **against the unedited source**.
- Include both the test file and the fixture file in the commit.

#### Step 3 — Apply the approved source edits (only now)

The test is green against the current code. Now apply the changes from step 4.

#### Step 4 — Re-run the pre-commit gate

Run the pre-commit gate again on BOTH the edited source and the test file:

```bash
uv run python3 kamma/improve/scripts/precommit_gate.py <source file> --test <test file>
```

For a behaviour-preserving refactor the test must still pass unchanged. For a
deliberate behaviour change, only the cases you explicitly updated to the new behaviour
may differ — everything else stays byte-identical.

#### Step 5 — Run the script live (smoke test)

After the gate passes, run the actual script to verify the real execution path works.

**Check for an entry point** — does the file contain `if __name__ == "__main__"` or a
bare `main()` call at module level?

- **Yes → run it:** `uv run python3 <file>`
  Note: Anki scripts require Anki to be **closed** — they write directly to the collection file.
  - Exit 0 with expected-looking output → pass. Proceed to commit.
  - Non-zero exit or traceback → **stop.** Do not suggest the commit. Report the
    error and wait for a fix before logging the change.
  - Script exits 0 but output looks clearly wrong → flag it; the unit tests passed but
    the live run exposed a problem. Investigate before committing.

- **No (support module / library with no entry point)** → skip and note:
  `"no entry point — live run not applicable."`

**Long-running scripts** — if context shows the script loops over the full DB or
compiles Go, warn the user before running: `"this may take several minutes — run live?"`
and wait for confirmation before executing.

After a successful live run (or a confirmed skip):

1. Stage all changed files:
   ```bash
   git add <source file> <test file> <fixture file>
   ```

2. Show the proposed commit message:
   ```
   refactor: <short description> (#157)

   - <bullet per distinct change>
   - add test: tests/<mirror-path>/test_<name>.py
   ```
   State the recommendation to commit and ask the user to reply `yes` or `no`.

3. If **yes**: run `git commit -m` with that message (no heredoc — user runs Fish shell).

4. After the commit (or if declined), **stop immediately.** Do NOT ask about the next script.
   Output exactly:
   > **Done.** Queue updated — pointer is at #N (`path/to/next/script.py`). Start a fresh session and run `/pipeline-improvement` to continue.

### 5. Update the queue and log

After every run (whether a change was made or not):

In `kamma/improve/queue.md` (kept lean — Pointer + checklist only, read
in full at step 1):
- Update the Pointer to the next pending script.
- Mark reviewed-clean scripts `[x] passed`.
- Mark changed scripts `[x] changed`.
- Mark deferred scripts `[>]`.

In `kamma/improve/log.md` (append-only history, NOT read at step 1):
- Append ONE terse decision line: `YYYY-MM-DD | #N path | passed / changed / skipped /
  deferred / archived | one concise clause`. The full rationale already lives in the
  commit message — do not duplicate it here. Keep the log a thin index, not a second
  changelog.

### 6. End-of-queue

If the Pointer reaches the end with no change needed (and no deferred items remain),
report: **"Pipeline review complete — all 80 scripts passed. Queue will reset."**
Then reset all `[x]` items back to `[ ]` and set Pointer to 1 to begin the next cycle.
Deferred items `[>]` are reviewed before the full reset.

---

## Scope rules

- All genuine changes to a file in one pass. This file won't be seen again for months.
- Never touch files outside the script being reviewed.
- Never refactor for its own sake. The bar for a change is: a reader would pause here,
  or the code actively violates a project convention.
- Clean files get a one-line log entry and nothing else. That is a good outcome.
- This skill stages and commits on approval but never pushes.
