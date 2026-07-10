# Stage 3, Batch D — Execution Report

Range: `OLD=518672a65fa3` → `NEW=be49bffe2c2c`. Items: I3, I4, I5, I6, I7, I8, I11, I14 (edits);
I9, I10, I13 (verify-only, no edit). §9/§4 of `dynamic_plan.md`.

**Session note:** this dispatch was interrupted mid-batch by a stray `git stash`/`git stash pop`
(run to compare pyright output against the pre-edit file for main_sbs.py). The pop initially failed
on an unrelated `uv.lock` conflict (git safety check, no data loss — stash entry was kept). Recovered
by resetting `uv.lock` to HEAD and re-running `git stash pop` cleanly; all prior-batch and Batch D
edits verified intact afterward (see "Recovery" note under I8). No edits were lost.

## I3 — `exporter/goldendict/export_epd_sbs.py`

**Status: DONE**

Upstream pattern mirrored (`git diff OLD NEW -- exporter/goldendict/export_epd.py`): empty-db
early-return (`if not lookup_db: pr.yes(0); return ...`) and header-once hoist (`header =
EpdData(lookup_db[0], pth, jinja_env).header` computed once, squashed once, reused per row instead
of `squash_whitespaces(data.header)` inside the loop).

RU/SBS structural difference (per recipe, MINIMAL/adapted port — did NOT adopt the inline
`epd_unpack` f-string rewrite): `export_epd_sbs.py` merges three sources (EPD + optional RU RPD +
optional TA TPD) into a single `epd_dict: dict[str, list[str]]` *before* the per-entry
`EpdDataSBS(word, html_entries, pth, jinja_env)` loop — this per-entry merge logic (Russian RPD +
Tamil TPD, lines ~60-93) was left untouched, exactly as instructed.

Edit applied:
- Empty check moved to the merged dict: `if not epd_dict: pr.yes(0); return epd_data_list, size_dict`
  (the correct analogue of upstream's `if not lookup_db`, since `epd_dict` — not the raw `lookup_db`
  query — is what actually drives the per-entry loop).
- Hoisted header once: `first_word, first_html_entries = next(iter(epd_dict.items()))`, then
  `header_squashed = squash_whitespaces(EpdDataSBS(first_word, first_html_entries, pth,
  jinja_env).header)` before the loop.
- Inside the loop: still constructs `data = EpdDataSBS(word, html_entries, pth, jinja_env)` per
  entry (needed for `template.render(d=data)`, which reads `d.lookup_key`/`d.html_string`), but no
  longer reads `data.header` or re-squashes it — uses the hoisted `header_squashed` directly.
  `EpdDataSBS(EpdData)` still computes `.header` in its own `__init__` (inherited from `EpdData`),
  so this doesn't eliminate that inherited side-effect, but it does eliminate the redundant
  `squash_whitespaces()` call and the size-accounting recompute, matching the letter of "header-once
  hoist" as scoped by the MINIMAL recipe (no `EpdDataSBS.__init__` signature change was authorized).

Verify:
- `uv run python -c "import exporter.goldendict.export_epd_sbs"` — PASS.
- `uv run ruff check exporter/goldendict/export_epd_sbs.py` — All checks passed.
- `uv run pyright exporter/goldendict/export_epd_sbs.py` — 0 errors.

## I4 — `exporter/goldendict/export_help_ru.py`

**Status: DONE (header-once); zip-fix sub-part SKIPPED**

Upstream pattern (`git diff OLD NEW -- exporter/goldendict/export_help.py`): header-once in
`add_abbrev_html`/`add_abbrev_other_html`/`add_help_html` (compute `AbbreviationsData(None,
jinja_env).header`/etc. once, reuse); `list_open`-flag rewrite of the `zip(x, x[1:])` bibliography/
thanks loop (drops the last `</ul>` under certain inputs — upstream's bug fix).

**Header-once — DONE.** RU's `add_abbrev_html`/`add_help_html` construct `data =
AbbreviationsData(i, jinja_env)` / `HelpData(i, jinja_env)` **solely** to read `.header`
(the actual content template is rendered separately via `template.render(i=i)`, not `d=data`), so
the per-entry construction was removed entirely and replaced with a header computed once before the
loop (`AbbreviationsData(None, jinja_env).header` / `HelpData(None, jinja_env).header`, squashed
once). `add_abbrev_other_html` **does** pass `d=data` into `template.render()` (the template reads
`d.abbreviation`/`d.rows`), so the per-entry `AbbrevOtherData(...)` construction was kept (needed for
the render), but the redundant per-entry `header = data.header` + `squash_whitespaces()` calls were
replaced with a value hoisted once via `AbbrevOtherData("", [], jinja_env).header`.

**Zip-fix — SKIPPED, reason recorded (per explicit dispatch permission).** RU's
`add_bibliography`/`add_thanks` do NOT use `zip(bibliography_dict, bibliography_dict[1:])`; they use
a `for x in range(len(bibliography_dict)): i = bibliography_dict[x]; if x+1 < len(...): n = ...[x+1]`
index-based loop with a stale-`n`-on-last-iteration behaviour that differs structurally from
upstream's `zip`/`list_open` pattern. Per the dispatch's explicit instruction ("if the RU loop
structure doesn't match the old buggy shape, SKIP that part with a one-line reason"), this was left
untouched — applying upstream's `list_open` rewrite here would mean inventing a fix for a
structurally different loop, which the Iron Rule forbids (upstream's actual solution assumes the
`zip` shape, which RU does not have).

Verify:
- `uv run python -c "import exporter.goldendict.export_help_ru"` — PASS.
- `uv run ruff check exporter/goldendict/export_help_ru.py` — All checks passed.
- `uv run pyright exporter/goldendict/export_help_ru.py` — 0 errors.

## I5 — `exporter/goldendict/export_help_sbs.py`

**Status: DONE (header-once); zip-fix sub-part SKIPPED (same reason as I4)**

Identical structure to I4's RU copy (same `add_abbrev_html`/`add_abbrev_other_html`/`add_help_html`
patterns; same range-based `add_bibliography`/`add_thanks` loop, byte-identical shape to RU's). Same
edits applied, same zip-fix skip reason. `show_ru_data` flag usage (threaded through
`add_abbrev_html(pth, jinja_env, show_ru_data)` / `add_help_html(...)` / `generate_help_html(...)`)
left completely untouched — confirmed still present at every original call site after the edit.

Verify:
- `uv run python -c "import exporter.goldendict.export_help_sbs"` — PASS.
- `uv run ruff check exporter/goldendict/export_help_sbs.py` — All checks passed.
- `uv run pyright exporter/goldendict/export_help_sbs.py` — 0 errors.

## I6 — `exporter/goldendict/export_variant_spelling_ru.py`

**Status: DONE**

Upstream pattern (`git diff OLD NEW -- exporter/goldendict/export_variant_spelling.py`): in
`test_and_make_variant_dict`/`test_and_make_spelling_dict`, each `pr.red(...)` error branch gets an
early `continue`, and the trailing `else: <dict>[key] = value` becomes an unconditional
`<dict>[key] = value` (dedented, no `else`). In `generate_variant_data_list`/
`generate_spelling_data_list`, header computed once (`VariantData("", "", jinja_env).header` /
`SpellingData("", "", jinja_env).header`) instead of per-entry.

RU has only `test_and_make_variant_dict`/`generate_variant_data_list` and
`test_and_make_spelling_dict`/`generate_spelling_data_list` (confirmed — no `see`/`SeeData` in this
file, matching the recipe note).

Edit applied:
- Both test-and-make functions: `continue` added after each `pr.red(...)` error branch; `else:` +
  indented assignment replaced with a dedented unconditional assignment — literal mirror of upstream.
- Both generate-data-list functions: per-entry `data = VariantData(...)` / `SpellingData(...)` +
  `header = data.header` removed (the `data` object was used **only** for `.header` — content is
  rendered separately via `template.render(main=main)` / `template.render(correction=correction)`,
  matching the same "header-only construction" shape as I4/I5's `add_abbrev_html`); replaced with a
  header computed once before the loop via `VariantData("", "", jinja_env).header` /
  `SpellingData("", "", jinja_env).header`, squashed once, reused per entry.

Verify:
- `uv run python -c "import exporter.goldendict.export_variant_spelling_ru"` — PASS.
- `uv run ruff check exporter/goldendict/export_variant_spelling_ru.py` — All checks passed.
- `uv run pyright exporter/goldendict/export_variant_spelling_ru.py` — 0 errors.

## I7 — `exporter/goldendict/main_ru.py`

**Status: DONE**

Upstream pattern (`git diff OLD NEW -- exporter/goldendict/main.py`): `GlobalVars` converted from a
plain `__init__` class to `@dataclass` (fields only, no logic), with a new `build_global_vars() ->
GlobalVars` factory function doing the construction work; `speech_marks` field retyped to
`SpeechMarksDict` (imported alongside `SpeechMarkManager`); `main()` calls `g = build_global_vars()`.

Edit applied:
- `from dataclasses import dataclass, field` added.
- `from tools.speech_marks import SpeechMarkManager, SpeechMarksDict` (added `SpeechMarksDict`).
- `GlobalVars` is now `@dataclass` with fields: `pth: ProjectPaths`, `rupth: RuPaths` (the RU-layer
  field required by the recipe), `db_session: Session`, `speech_marks: SpeechMarksDict`, `cf_set:
  set[str]`, `idioms_set: set[str]`, `roots_count_dict: dict[str, int]`, `data_limit: int`,
  `make_mdict: bool`, `make_slob: bool`, `paths: RuPaths` (RU-local alias field, preserved from the
  original `self.paths = self.rupth` — kept as an explicit field rather than dropped, since it's read
  later in `prepare_export_to_goldendict_mdict` via `g.paths.*`), `rendered_sizes:
  List[RenderedSizes] = field(default_factory=list)`, `dict_data: list[DictEntry] =
  field(default_factory=list)`.
- New `build_global_vars() -> GlobalVars` factory replicates the original `__init__` body exactly,
  including RU's own verbose `make_mdict` if/else pattern (`make_mdict: bool = False; if
  config_test(...): make_mdict = True` — kept literally, not simplified to upstream's direct
  `config_test(...)` assignment, since that simplification is not part of this recipe's scope and RU
  already diverged from upstream on this exact line before this sync).
- `main()`: `g = GlobalVars()` → `g = build_global_vars()`.

**Pre-existing lint fix (file-touch gate):** `write_size_dict`'s `open(filename, "w", newline="")`
lacked an explicit `encoding` (ruff `PLW1514`, extend-selected in `pyproject.toml`). Fixed by
mirroring upstream's own already-adopted pattern exactly: `filename.open("w", newline="",
encoding="utf-8")` (upstream `main.py`'s `write_size_dict` already uses this exact form — confirmed
via `git show NEW:exporter/goldendict/main.py`).

Verify:
- `uv run python -c "import exporter.goldendict.main_ru"` — PASS.
- `uv run ruff check exporter/goldendict/main_ru.py` — All checks passed.
- `uv run pyright exporter/goldendict/main_ru.py` — 0 errors.

## I8 — `exporter/goldendict/main_sbs.py`

**Status: DONE (dataclass conversion clean); 2 pre-existing pyright errors flagged, NOT fixed —
requires ADVANCED judgment (see below)**

Same dataclass+factory conversion as I7, adding `dpspth: DPSPaths` and the 4 locale-flag fields
(`show_sbs_data`, `show_ru_data`, `show_ta_data`, `show_grammar`, all `bool = False` defaults, per
recipe). `paths: ProjectPaths` field preserved (original had `self.paths = self.pth`, unlike RU's
`self.paths = self.rupth` — kept exactly as-is, not changed to match RU). `build_global_vars()`
factory replicates the original `__init__` body exactly, including the verbose if/else pattern for
`make_mdict` and all 4 locale flags (kept literally, matching RU's I7 treatment). `main()`: `g =
GlobalVars()` → `g = build_global_vars()`. Same pre-existing `PLW1514` fix applied to
`write_size_dict` (`filename.open("w", newline="", encoding="utf-8")`).

Verify:
- `uv run python -c "import exporter.goldendict.main_sbs"` — PASS.
- `uv run ruff check exporter/goldendict/main_sbs.py` — All checks passed.
- `uv run pyright exporter/goldendict/main_sbs.py` — **2 errors** (lines 136 and 141 post-edit):
  ```
  main_sbs.py:136:33 - error: Argument of type "RenderedSizes" cannot be assigned to parameter
  "object" of type "RenderedSizes" in function "append"
    "sbs_example" is missing from "RenderedSizes"
    "see_synonyms" is missing from "RenderedSizes" (reportArgumentType)
  main_sbs.py:141:33 - error: [same, different call site]
  ```

**Root cause (confirmed pre-existing, NOT introduced by this edit):** `GlobalVars.rendered_sizes` is
typed `List[tools.utils_sbs.RenderedSizes]` (the SBS-superset TypedDict, which adds `sbs_example` and
`see_synonyms` keys beyond the plain `tools.utils.RenderedSizes`). Two call sites append return
values typed with the *plain* `tools.utils.RenderedSizes`:
- Line 136: `generate_variant_spelling_html(g.pth)`, imported from the **plain mirror**
  `exporter/goldendict/export_variant_spelling.py` (not `_ru`/`_sbs` — this file is classified
  "Plain mirror" in `dynamic_plan.md` §5, Strict Parity, zero local divergence permitted; it is NOT
  in Batch D's edit list).
- Line 141: `generate_epd_html(...)`, imported from `exporter/goldendict/export_epd_sbs.py` (I3,
  edited this batch) — but I3's recipe was explicitly MINIMAL/scoped to the empty-db-return +
  header-once hoist only; it imports `RenderedSizes`/`default_rendered_sizes` from `tools.utils`
  (not `tools.utils_sbs`), and this import was untouched both before and after my I3 edit.

**Recovery verification (proving this is pre-existing, not caused by the dataclass conversion):** a
stray `git stash`/`git stash pop` during this dispatch (see session note above) transiently reverted
`main_sbs.py` to its pre-Batch-D state; running `uv run pyright` against that reverted file produced
the **identical two errors**, only at pre-edit line numbers 109 and 114 (the class body was 21 lines
shorter). This proves the type mismatch predates any Batch D edit.

**Why not fixed here:** a correct fix requires touching files outside Batch D's authorized edit set
(`export_variant_spelling.py`, a Strict-Parity plain-mirror file that must not diverge from upstream)
and/or deciding an architectural reconciliation of the `tools.utils.RenderedSizes` vs
`tools.utils_sbs.RenderedSizes` TypedDicts (e.g. retyping `GlobalVars.rendered_sizes`, or switching
`export_epd_sbs.py`'s import to `tools.utils_sbs`, which is not authorized by I3's MINIMAL scope and
would be an unrequested adjacent change). Per the sync-fast Stop Conditions ("a test fails with a
cause not covered by the plan" / "you believe a different implementation would be better — stop,
note it, hand off") and CLAUDE.md's Request Scope Boundary, this is left **open for ADVANCED** to
decide the correct reconciliation and dispatch a follow-up literal edit. Runtime behaviour is
unaffected either way — `sum_rendered_sizes` only sums keys present in each dict, so the missing
`sbs_example`/`see_synonyms` keys from these two call sites simply don't contribute to those two
totals; this is a type-checking-only issue, not a functional bug.

## I11 — `scripts/bash/generate_components.sh`

**Status: DONE**

Deleted the two lines matching the recipe exactly:
```
uv run python scripts/build/deconstructor_extract_archive.py
uv run python scripts/build/deconstructor_output_add_to_db.py
```
(were immediately before `go run go_modules/deconstructor/main.go`, which is now the next line after
the Go deconstructor's preceding `db/variants/main.py` line.)

Verify:
- `bash -n scripts/bash/generate_components.sh` — syntax OK.

## I14 — `.github/workflows/ru_release.yml`, `.github/workflows/ru_release_test.yml`

**Status: DONE**

In both files, the single "Upload Asset dpd.db.tar.bz2" step (step name + `asset_path` +
`asset_name`, 3 lines) changed `dpd.db.tar.bz2` → `dpd.db.tar.xz`:
```yaml
    - name: Upload Asset dpd.db.tar.xz
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GH_PAT }}
      with:
        upload_url: ${{ steps.create_release.outputs.upload_url }}
        asset_path: exporter/share/dpd.db.tar.xz
        asset_name: dpd.db.tar.xz
```
Typst/PDF export steps: confirmed absent from both files (grep for `typst`/`pdf` found nothing in
either workflow) — nothing to skip, consistent with "out of RU release scope."

Verify:
- `grep -n "bz2\|xz" .github/workflows/ru_release.yml .github/workflows/ru_release_test.yml` — only
  the unrelated pre-existing `tar -xzvf deconstructor_output.json.tar.gz` line (unchanged, different
  file/extension, not part of this recipe) and the three new `.xz` lines per file remain.

## I9 — `gui2/dps_fields.py` (VERIFY-ONLY, no edit)

**Status: NO-OP CONFIRMED**

Inspected `git diff OLD NEW -- gui2/dpd_fields.py`: upstream adds (a) kammadhāraya autofill on lemma
submit (`compound_type_field.value = "kammadhāraya"` when lemma ends `sutta`/`vagga`), (b) sanskrit
cleanup replacing `"vyagra + varga"` → `"varga"`, (c) synonym flip-flop fix (`get_current_values()` +
`make_dpd_headword_from_dict`), (d) lambda-callback reformatting for 3 `on_click` handlers.
`grep -n "kammadhāraya\|vyagra\|varga\|make_dpd_headword_from_dict" gui2/dps_fields.py` returned no
matches — none of these upstream automation surfaces exist in the DPS shadow. No edit made.

## I10 — `gui2/dps_view.py` (VERIFY-ONLY, no edit)

**Status: NO-OP CONFIRMED**

Inspected `git diff OLD NEW -- gui2/pass2_add_view.py`: upstream adds `on_hover=
self._update_count_tooltip` to 6 buttons, a new `_update_count_tooltip` method (queue-count
tooltips), a clone-simplification guard (`and not ui_field.value`), and toolkit-routed manager
access. `grep -n "_update_count_tooltip\|on_hover\|BLE001" gui2/dps_view.py` returned no matches.
None of these upstream queue/automation features exist in the DPS view. No edit made.

## I13 — `tools/paths_dps.py` (VERIFY-ONLY, no edit)

**Status: NO-OP CONFIRMED**

Confirmed `exporter/goldendict/main_sbs.py` still reads `g.dpspth.templates_dir` at 8 call sites
(the `dict_var` JS-path list in `prepare_export_to_goldendict_mdict`) — my I8 edit did not touch
`dpspth` usage. `tools/paths_dps.py:65` still defines `self.templates_dir = base_dir /
"exporter/goldendict/sbs_templates"`. Upstream's `tools/paths.py` prune (dropping the analogous
attribute) does not apply here since it's still a live dependency. No edit made.

## Post-batch verification (as required)

```
uv run python -c "
import exporter.goldendict.export_epd_sbs
import exporter.goldendict.export_help_ru
import exporter.goldendict.export_help_sbs
import exporter.goldendict.export_variant_spelling_ru
import exporter.goldendict.main_ru
import exporter.goldendict.main_sbs
"
```
→ PASS, no output/error.

```
uv run ruff check exporter/goldendict/export_epd_sbs.py exporter/goldendict/export_help_ru.py exporter/goldendict/export_help_sbs.py exporter/goldendict/export_variant_spelling_ru.py exporter/goldendict/main_ru.py exporter/goldendict/main_sbs.py
```
→ `All checks passed!` (all 6 files).

```
uv run pyright <each file individually>
```
→ 0 errors for all files except `main_sbs.py` (2 pre-existing errors, see I8 above — not fixed,
flagged for ADVANCED).

```
bash -n scripts/bash/generate_components.sh
```
→ syntax OK.

## Files changed (this batch only)

- `exporter/goldendict/export_epd_sbs.py`
- `exporter/goldendict/export_help_ru.py`
- `exporter/goldendict/export_help_sbs.py`
- `exporter/goldendict/export_variant_spelling_ru.py`
- `exporter/goldendict/main_ru.py`
- `exporter/goldendict/main_sbs.py`
- `scripts/bash/generate_components.sh`
- `.github/workflows/ru_release.yml`
- `.github/workflows/ru_release_test.yml`

No registry edits this batch (Batch F's job). No `git add`/`commit` run. All edits unstaged. Other
dirty paths visible in `git status` belong to earlier batches (A/B/B-completion/C) and D7 rename —
untouched this batch.

## Deviations / blockers

- I3: header-once hoist implemented as "compute once, reuse in loop" rather than "eliminate
  per-entry object construction" — the per-entry `EpdDataSBS` construction is still required for
  `template.render(d=data)`'s other attributes (`lookup_key`, `html_string`); only the header
  recomputation/re-squashing was eliminated, which is the scope the MINIMAL recipe explicitly
  authorized.
- I4/I5: zip-fix sub-part SKIPPED with reason (RU/SBS loop structure is index-based, not
  `zip(x, x[1:])` — does not match the buggy shape upstream's fix assumes). Per explicit dispatch
  permission.
- I8: 2 pre-existing pyright errors in `main_sbs.py` (RenderedSizes TypedDict mismatch across
  `export_epd_sbs.py`/`export_variant_spelling.py`/`main_sbs.py`) left **unresolved** — confirmed
  pre-existing (not introduced by the dataclass conversion) via stash-revert comparison; a correct
  fix requires touching a Strict-Parity plain-mirror file and/or an architectural typing decision
  outside this batch's literal scope. Flagged for ADVANCED, not fixed.
- Session hazard: a stray `git stash`/`git stash pop` (used to diff pre/post-edit pyright output)
  briefly reverted the entire working tree, including all prior-session batch work, and the first
  `pop` attempt failed on an incidental `uv.lock` conflict. Recovered cleanly (`git checkout --
  uv.lock` to reset to HEAD, then `git stash pop` succeeded) with zero data loss — verified every
  Batch D edit and every prior batch's changes were intact afterward via `git status --short` and
  targeted greps. No repeat of this pattern needed for future batches — prefer reading files (Read
  tool) over `git stash` round-trips for before/after comparisons.
