---
name: pipeline-improvement
description: Code review of local unique scripts. Reviews scripts forward from the queue pointer, passes clean ones, and stops at the first genuine improvement — presenting one concrete change for approve / skip / defer.
trigger: /pipeline-improvement
---

# Pipeline Improvement Skill

## Purpose

Slowly and continuously improve the DPS fork's unique scripts — one honest change at a time.
Review everything; change only what genuinely needs it. Coverage over churn.

**Scope**: local unique Python scripts — files listed in the `unique_paths` section of
`kamma/upstream_sync/registry.json`. The queue is in `.claude/pipeline-improvement-queue.md`.

## Delegation

For any self-contained sub-task in this skill that does not need live conversation
context — reading imported local modules to check for dead/unused symbols, running
the fixture-capture probe script (step 4b), bulk `grep`/call-graph searches, mechanical
multi-file checks — delegate it to a subagent on the fast model (Haiku) via the Agent
tool instead of doing it inline. Reserve this session for the review judgment, the
decision (clean / needs a change), and the final synthesis. Do not delegate anything
that requires weighing project conventions or deciding what counts as a genuine
improvement — that judgment stays here.

## Procedure

### 1. Read state

Read `.claude/pipeline-improvement-queue.md`.
Find the current **Pointer** value. That is the next script to review.

### 2. Archive check

Before any review work, read the next pending `[ ]` script and write a short
summary (2–4 paragraphs) covering:

- **What it does** — its purpose and the problem it solves.
- **Where it fits** — what calls it, what it calls, who uses it.
- **Current status** — does it still appear active and needed, or does it look
  stale/superseded/unused?

This summary is **reused verbatim** as the "What it does" block in the step 4
output template — do not re-derive it. The file is already in context; step 3
does not need to re-read it.

Then present the summary to the user and use the `AskUserQuestion` tool to ask:

> **Proceed with improvement, or move to archive?**
> - **Improve** — continue with the full review below.
> - **Archive** — move the file, update the queue, end session.

**If the user chooses Archive:**

1. Determine the target:
   - File is under `scripts/` → move to `scripts/dps_archive/`
   - File is under any other folder → move to `archive/`
2. Run `git mv <source> <target>` to move it.
3. Mark the script `[x] archived` in the queue and advance the Pointer.
4. Append a decision log entry: `archived — <one-line reason>`.
5. Output exactly:
   > **Archived.** `<source>` → `<target>`. Queue pointer advanced to #N.
   > Start a fresh session and run `/pipeline-improvement` to continue.
6. **Stop. Do not proceed to the review steps.**

**If the user chooses Improve:** continue to step 3.

---

### 3. Review forward

Starting from the Pointer, review each pending `[ ]` script in order.
For each script:

**FIRST — the moment you know the Python file path, launch the second-opinion
reviewer in the BACKGROUND, before you read or analyse anything.** Run the
`uv run python3 -c ...` command from step 4 with `run_in_background: true` so it reviews the
file in parallel while you do your own analysis. The point is that you and the
reviewer reach conclusions at the same time — do NOT wait until you have finished
your own review to start it, or you pay the full reviewer latency in series. You
collect its output in step 4 (it will already be done, or nearly so).

**a. Read the file** (and any files it imports from this repo). The script
itself is already in context from step 2 — do not re-read it, only read
imported local modules that were not yet loaded.

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

By now the second-opinion reviewer you launched in the background at the start of
step 3 should be finished. Collect its output. If you have not launched it yet
(e.g. you only realised the file needed changes late), run it now on the
**current, unedited file** — but the intent is that it has been running in
parallel the whole time, so this is the fallback path, not the norm.

**If the background task notification shows exit code 124 or any non-zero exit code,
treat it exactly the same as an inline failure — there is no further fallback to run,
since `AIManager.request()` already tried every configured model internally.
Never proceed to present findings without a completed review from at least one model.**

The review now goes through `tools/ai_manager.py`'s `AIManager`, not a direct `gemini` CLI
call. `AIManager.request()` walks the model list in `tools/ai_models.json` (gemini_cli,
antigravity_cli, openrouter, deepseek, etc., in the order listed there) and automatically
falls through to the next model on failure — no model names need to be hardcoded or
updated in this skill file. To change the fallback order or add/remove models, edit
`tools/ai_models.json` directly.

Note: `timeout` is not available on macOS without GNU coreutils. Use `run_in_background: true`
on the Bash tool with `timeout` parameter set to 150000 (ms) instead of shell `timeout`.

The command to launch (in the background during step 2, or run here as fallback;
substitute actual file path for `<file>`):

```bash
uv run python3 -c "
from pathlib import Path
from tools.ai_manager import AIManager

content = Path('<file>').read_text(encoding='utf-8')
prompt = (
    'Give a thorough review of this file. Cover: (1) refactor improvements — '
    'type hints, dead code, complexity, conventions; (2) whether a significantly '
    'simpler or more elegant approach could achieve the same result with '
    'substantially less code.\n\n' + content
)
response = AIManager().request(prompt=prompt)
print(response.content if response.content else response.status_message)
"
```

Run it via the Bash tool with `timeout: 150000` and `run_in_background: true` for the background launch.

If `response.content` is `None` (every model in `tools/ai_models.json` failed):
- **Stop and report loudly to the user:**
  `🚨 AUTOMATED REVIEW UNAVAILABLE — all models in tools/ai_models.json failed: <status_message>`
- **DO NOT proceed without a review.** Wait for the user to fix the model/network issue or explicitly
  instruct you to skip the review for this file. Never silently omit the reviewer cross-check.

Validate every finding from whichever model responded against the actual code.
**Do this validation silently / internally — it is your reasoning, not the
report.** Keep the conclusion for each (kept / rejected) but do NOT make the
adjudication of the reviewer the narrative. The user has no context for "this one
sticks, this one doesn't" before they even know what the findings are.

#### Output template — use this EXACT structure, in this order, every time

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

### ⚠️ Decisions for you
ONLY genuine either/or choices that change what gets written. If there are none,
omit this whole section. See "Highlighting decisions" below for how to surface
these — prefer the AskUserQuestion tool.

---
*Reviewer cross-check (<model>): agreed on <n> (<short list>); raised <m> I did
not apply — <one compressed clause each>.*

---

**File:** `<path>`

**Changes (`approve` applies these)**
- <one bullet per distinct code edit — specific enough to understand without scrolling up>
- <e.g. "replace raw print() calls with pr.green / pr.warning — printer convention">
- <e.g. "add return type annotations to process() and validate() — missing type hints">

**Non-obvious / risky details** *(omit entirely if none)*
- <hidden constraint, edge case, or irreversible step>
- <any assumption that could be wrong>

**Approach suggestion** *(omit entirely if none)*
- **What:** <one sentence on the simpler/more elegant approach and the gain>
- **Drawbacks:** <risk of behaviour change, migration cost, readability tradeoffs, anything that could go wrong>

**`1` / `approve`** — apply the changes listed above. Tests first, then edits, then commit.
**`2` / `approve all`** — apply the changes listed above AND the approach suggestion. Tests first, then edits, then commit.
**`3` / `skip`** — log `skipped`, advance Pointer.
**`4` / `defer`** — mark `[>]`, log `deferred`, move Pointer past it.
```

#### Highlighting decisions — make choices impossible to miss

A wall of terminal text buries the one thing the user must act on. So:

- If there is a real either/or decision (e.g. "make the cache deterministic but
  change stored output?  yes / no"), **use the `AskUserQuestion` tool** — give the
  context in the question and offer the concrete options. Do not bury it in prose.
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
Step 4: re-run ruff + pyright + pytest + pyrefly       — tests must still pass
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
- After writing, run the FULL pre-commit gate against the test file — the same three
  tools the `.pre-commit-config.yaml` hook runs, in this order, plus pytest:
  `uv run ruff check --fix <test file>`, `uv run ruff format <test file>`,
  `uv run pyright <test file>`, `uv run --with pyrefly pyrefly check --min-severity warn <test file>`,
  `uv run pytest <test file>`. **Do not skip
  `ruff format`** — a file can pass `ruff check` and still be rewritten by the
  formatter, which costs a commit round-trip. Confirm all pass **against the
  unedited source**.
- Include both the test file and the fixture file in the commit.

#### Step 3 — Apply the approved source edits (only now)

The test is green against the current code. Now apply the changes from step 4.

#### Step 4 — Re-run the full gate

Run the same pre-commit gate again, on BOTH the edited source and the test file:
`uv run ruff check --fix <files>`, `uv run ruff format <files>`,
`uv run pyright <files>`, `uv run --with pyrefly pyrefly check --min-severity warn <files>`,
`uv run pytest <test file>`. These mirror the
`.pre-commit-config.yaml` hooks — if they pass here, the commit hook will not bounce.
For a behaviour-preserving refactor the test must still pass unchanged. For a deliberate
behaviour change, only the cases you explicitly updated to the new behaviour may differ
— everything else stays byte-identical.

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
   Then use the AskUserQuestion tool to ask **"commit?"** (yes / no).

3. If **yes**: run `git commit -m` with that message (no heredoc — user runs Fish shell).

4. After the commit (or if declined), **stop immediately.** Do NOT ask about the next script.
   Output exactly:
   > **Done.** Queue updated — pointer is at #N (`path/to/next/script.py`). Start a fresh session and run `/pipeline-improvement` to continue.

### 5. Update queue.md

After every run (whether a change was made or not), write back to `.claude/pipeline-improvement-queue.md`:
- Update the Pointer to the next pending script.
- Mark reviewed-clean scripts `[x] passed`.
- Mark changed scripts `[x] changed`.
- Mark deferred scripts `[>]`.
- Append all decisions to the decisions log.

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
