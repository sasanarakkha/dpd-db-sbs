# Stage 3 — Batch A execution report (D1, D2, D3, D4, D5, D6, D13)

Executed by sync-fast (mechanical FAST executor) per dispatched Stage 3 instructions.
Range: `OLD=518672a65fa3` → `NEW=be49bffe2c2c`. All changes left UNSTAGED in the worktree
(no `git add`/`commit`/`stash`/`restore` run).

## D1 — `.gitignore` — DONE

Applied all 5 upstream additions into the local file, DPS/SBS/RU block untouched.

- `dpd.db.tar.bz2` → `dpd.db.tar.xz`
- added `exporter/pdf/typst_chunk_*` (near `typst_data_lite.typ`)
- added `gui2/data/commentary_stash.json` (near `gui2/data/daily_log.json`)
- added `gui2/pass2x/data/` + its comment, and `/scripts/fix/pass2exceptions.json` (appended at end)

Files changed: `.gitignore`.
Verify: visual diff only (no verify command specified for D1); confirmed all 5 tokens present via `grep`/read-back.

## D2 — `.pre-commit-config.yaml` — DONE (no-op, already satisfied)

Checked `exclude:` line: `^(archive|scripts/bash|tools/writemdict|scripts/archive|scripts/dps_archive)/`.
Upstream's only edit was adding `scripts/archive` to the exclude alternation — already present in
the local line (merged with local's own `scripts/dps_archive` entry, order differs but regex
alternation is order-independent). Local pyrefly hook already present after pyright (lines 25–30).
No edit made.

Files changed: none.
Verify: `grep -n "exclude:" .pre-commit-config.yaml` → confirms `scripts/archive` present; hook block read-back confirms pyrefly after pyright.

## D3 — `AGENTS.md` + `CLAUDE.md` — DONE

Discovered `CLAUDE.md` is a symlink to `AGENTS.md` (gitignored, not git-tracked as its own blob) —
editing `AGENTS.md` satisfies both "AGENTS.md" and "CLAUDE.md" targets in the recipe simultaneously.
The local "Project Rules (from original upstream)" section is a condensed digest (not upstream's
literal section structure), so the KEEP items were added as new `##` sections at the end of that
portion (before the `# Localized Rules (local fork)` divider), using upstream's verbatim text:

- `## Data Verification` (verbatim)
- `## Dependencies` > `### Optional/transitive deps belong to their parent...` (verbatim)
- `## Testing` (slow-tests bullet, verbatim)
- `## Pre-commit gate` (TOUCH A FILE = OWN ITS LINT bullet + hook-coverage note bullet, verbatim)
- `## Performance Work` (narrow one-line rule only: never `INSERT OR REPLACE` on `lookup`, use
  `_raw_sql_sync` pattern) — surrounding benchmarking prose dropped per DROP list

DROP list confirmed satisfied: no Go build rule, no Codebase Sweeps/Audits section, no
other-dictionaries submodule section, no Performance Work bulk prose, no "Update Gemini CLI"
section (grep confirms zero "Gemini" occurrences in `AGENTS.md`).

Files changed: `AGENTS.md` (also visible via `CLAUDE.md` symlink).
Verify: `grep -n "^## " CLAUDE.md` confirms all 5 new headings present; `grep -n "Gemini" AGENTS.md` → no matches.

## D4 — `db/models.py` — DONE

Applied the 3 upstream hunks exactly:
1. `import inspect` added.
2. Module-level `transliterate.getmembers = lru_cache(maxsize=None)(inspect.getmembers)` + its
   comment block, inserted before `class DpdHeadword`.
3. New `@lru_cache(maxsize=None) def _lemma_ipa_transliterate(lemma_clean: str) -> str` helper;
   `lemma_ipa` property body replaced with `return _lemma_ipa_transliterate(self.lemma_clean)`.

Local SBS/Russian/Tamil/Sinhala tables, relationships, and `paragraphs_are_similar_sbs` import
untouched. No rebuild performed (none required).

Files changed: `db/models.py`.
Verify commands run:
- `uv run python -c "import db.models"` → **PASS** (no output/exit 0).
- `uv run ruff check db/models.py` → **18 errors reported** (pre-existing debt: confirmed via
  `git stash` isolation that **17 of these errors already existed before the D4 edit** on the
  untouched file; the 18th is `UP033` flagging the upstream-mandated `@lru_cache(maxsize=None)`
  decorator itself — not fixed, since the plan requires the exact upstream form, not a stylistic
  rewrite to `@cache`). None of the 18 errors are caused by the D4 diff hunks. Not auto-fixed —
  out of scope for the literal D4 recipe (no adjacent cleanup per project scope rules). Flagging
  for ADVANCED/user awareness, not treated as a D4 failure.
- `uv run ruff format --check db/models.py` → **PASS** ("already formatted").

## D5 — `gui2/main.py` — DONE

Applied all upstream hunks per the RESOLUTION (2c COUNTED tab order, verified against actual
local tabs before editing):
- `import re` added.
- `from gui2.pass2x.in_commentary_view import Pass2xInCommentaryView` imported and instantiated
  (`self.pass2x_view`).
- New "Pass2x" tab inserted between "Pass2Pre" and "Pass2Auto".
- `_get_current_lemma` docstring + body updated to return `lemma_clean` via `re.sub(r" \d.*$", "", lemma_1)`.
- `tab_to_view` map updated to `{3: self.pass1_add_view, 7: self.pass2_add_view}` (recount
  confirmed correct: DpsView sits after pass2_add, unaffected by the new Pass2x tab insertion).
- Removed the `print(f"snakeviz {profile_file}")` line.
- Local DpsView tab, font-scaler patch, and `fast_api_utils_dps` import left untouched.

Files changed: `gui2/main.py`.
Verify commands run:
- `uv run python -c "import gui2.main"` → **PASS** (no output/exit 0). Confirmed
  `gui2/pass2x/in_commentary_view.py` exists (pulled via mirror per §5).
- `uv run ruff check gui2/main.py` → **4 errors reported** (2× B009 `getattr`, 1× SIM102, 1×
  BLE001), all on lines untouched by the D5 diff (`on_keyboard`'s pre-existing
  `hasattr`/`getattr`/`except Exception` block). Confirmed pre-existing via `git diff` — the D5
  diff hunks do not touch those lines. Not fixed — out of scope for the literal D5 recipe.
- `uv run ruff format --check gui2/main.py` → **PASS** ("already formatted").

## D6 — `pyproject.toml` — DONE

3-way diff confirmed local `[project].dependencies` was **already** upstream-verbatim plus the two
local-only deps (someone/an earlier step had already applied this half). Remaining work:
- Replaced `[dependency-groups].dev` and `.tools` wholesale with upstream-NEW verbatim (drops
  black/flake8/bandit/pylint/pip/timeout-decorator/psutil-dup/flask/flask-sqlalchemy/tomlkit/
  pandoc/dbf/marimo/snakeviz/natsort-dup/indic-transliteration/modelcontextprotocol/elevenlabs/gtts;
  adds `prompt-toolkit>=3.0.52`; adds ownership comments on `httpx2`/`openpyxl`).
- Replaced `[tool.pyright].exclude`, `[tool.ruff].exclude`, `[tool.ruff.lint].select`,
  `[tool.pytest.ini_options].addopts`+`markers` with upstream-NEW verbatim (confirmed
  `gui/PySimpleGUI.py` in the old ruff-exclude was itself an **upstream** entry that upstream
  removed, not a local-only addition — correctly dropped, not preserved).
- `num2words>=0.5.14` and `pyrefly>=1.1.1` remain in `[project].dependencies` (final `diff` against
  upstream-NEW confirms these are the ONLY delta).
- Local pyrefly pre-commit hook (D2) untouched — still present after pyright.
- Ran `uv lock` → succeeded (dependency tree rebuilt to match new pyproject.toml).
- Ran `uv sync --all-groups` → succeeded (old deps removed, `prompt-toolkit`/`wcwidth` added).

Files changed: `pyproject.toml`, `uv.lock` (regenerated, left UNSTAGED as instructed).
Verify: `uv run python -c "import psutil, natsort, num2words"` → **PASS** (no output/exit 0).
Final `diff` of `pyproject.toml` against upstream-NEW shows only the 2 expected extra lines
(`num2words>=0.5.14`, `pyrefly>=1.1.1`).

## D13 — `.github/workflows/pdf_test.yml` — DONE (no-op / already mirrored)

`git show HEAD:.github/workflows/pdf_test.yml` confirms the file is present at HEAD, trigger is
`on: workflow_dispatch` only (not `push`) — matches "PULL FULLY / VERBATIM" resolution, no
exclusion or edit needed.

Files changed: none.
Verify: `git show HEAD:.github/workflows/pdf_test.yml | head -20` → file present, correct trigger.

---

## Summary of files changed this batch

`.gitignore`, `AGENTS.md` (== `CLAUDE.md` via symlink), `db/models.py`, `gui2/main.py`,
`pyproject.toml`, `uv.lock`. All UNSTAGED. `.pre-commit-config.yaml` and
`.github/workflows/pdf_test.yml` required no edits (already correct).

## Open items for ADVANCED / user

1. `db/models.py` ruff check: 17 pre-existing lint errors (List/Optional typing, TRY002, BLE001,
   SIM103, import-sort) unrelated to D4, plus 1 new `UP033` suggestion against the
   upstream-mandated `@lru_cache(maxsize=None)` decorator (not changed — matches upstream exactly
   per Iron Rule). Not fixed — out of D4's scope.
2. `gui2/main.py` ruff check: 4 pre-existing lint errors (getattr/SIM102/BLE001 in `on_keyboard`)
   unrelated to D5. Not fixed — out of D5's scope.
3. Neither of the above blocks D4/D5 per their literal verify commands (import + ruff-check-run,
   not ruff-check-clean). Flagging per "TOUCH A FILE = OWN ITS LINT" (newly merged into AGENTS.md
   by this same batch, D3) for a follow-up decision — whether Stage 3's later verification battery
   (§8.5: `ruff check` + `ruff format` + `pyright` on every hand-edited file) is expected to be
   clean, which would require fixing this pre-existing debt (out of literal D4/D5 scope; needs
   explicit authorization).

## Next action

Batch A (D1–D6, D13) complete. Hand back to ADVANCED orchestrator for the next batch
(S1–S13 shadow ports / I1–I15 inspired backports / remaining D7/D9–D12 items) and eventual §8
verification battery + Commit 2 gate. Do not continue in this session.
