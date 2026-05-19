# Handoff: MCP Pāḷi Analysis Pipeline

## Session 22 — Phase 15 Complete

All three DHP25 fixes implemented, tested, and verified. Ready for next issue.

---

## Phase 15: Summary (Done)

Three bugs fixed in `scripts/change_in_db/fill_dhp_examples.py` and `preview_dhp_changes.py`:

### Fix 1: Existence gate (Task 1)
- **Where:** Main loop in both `fill_dhp_examples.py` and `preview_dhp_changes.py`, after dedup check, before SBS lookup.
- **Code:** `if component_pali not in apos_word.replace("'", ""): skipped_count += 1; continue`
- **Result:** `dvi` (ID 34379) no longer appears as NEW for `dīpaṃ`

### Fix 2: Exact match step 0 in bold_component_in_token (Task 2)
- **Where:** `bold_component_in_token()`, inserted as step 0 before DB inflection lookup.
- **Logic:** If `component_pali` is a direct substring of `apos_token`, bold it immediately without consulting DB.
- **Result:** `appamādena` (ID 6981) now bolds `<b>appamādena</b>` not `<b>appamāde</b>appamāde`

### Fix 3: is_top_level flag for whole-token bolding (Task 3)
- **Where:** `collect_all_ids()` return type extended to 5-tuple adding `is_top_level = (depth == 0)`.
- **New function:** `bold_word_toplevel(apos_token)` → `f"<b>{apos_token}</b>"`
- **Routing:** `bold_word_in_verse()` now takes `is_top_level: bool = False`; routes to `bold_word_toplevel()` when True.
- **Result:** `nābhikīrati` (ID 36392) appearing as `n'ābhikīrati` in verse now bolds as `<b>n'ābhikīrati</b>`

---

## Verification Command

```bash
uv run python scripts/change_in_db/preview_dhp_changes.py --book kn2 --verse DHP25 --force
```

Expected (verified in Session 22):
- dvi (34379): absent from Proposed SBS Changes table (filtered by gate)
- appamādena (6981): `uṭṭhānen'<b>appamādena</b>` ✓
- nābhikīrati (36392): `<b>n'ābhikīrati</b>` ✓

**Tests:** 36 pass. Ruff + pyright clean.

---

## Key Codebase Facts

- `kn2_analysis.json` is stateful — always re-run batch for affected verse after any `analyzer.py` fix
- `DpdHeadword.example_1/2` has bold tags — strip with `re.sub(r"</?b>", "", text)`
- `mano` in compounds → resolves to `manas` (id=51099) via `get_in_comp_forms()` in `analyzer.py`
- Never run bare `uv run pytest` — always specify file path
- `collect_all_ids()` now returns 5-tuples: `(headword_id, component_pali, word_in_verse, is_first_component, is_top_level)`
- `bold_word_in_verse()` now accepts `is_top_level: bool = False` as 7th parameter

---

## Errors / Repeated Mistakes Log

- **Attempted to remove `!` stem filter** — wrong, intentional. Fix belonged in `get_in_comp_forms()`.
- **Attempted overly broad lookup fallback** — would allow inflected forms as compound parts. Reverted.
- **`source_to_apos_verse` poisoning** — fixed by text validation before accepting. Now replaced entirely by `speech_marks.json` approach.
- **Attempted to strip `ṃ`** — WRONG. `ṃ` is a Pāḷi letter (niggahīta), never strip it.
- **Session 18: Fake intelligent suffix stripping** — Initial approach used `_extract_possible_bases()` to guess base forms by stripping case endings. WRONG. User correctly rejected: inflections already exist in DB, no guessing needed. Reverted to simple, honest search of actual inflections_list. Lesson: don't optimize with fake intelligence; use the data you have.
- **Session 19: Greedy regex across cell boundaries** — Initial regex patterns for extracting grammar from inflections_html matched across `</td>...<td>` boundaries, getting wrong title attribute (nom sg instead of abl sg). Solution: locate form position first, then work backwards to nearest `<td>` opening tag (no greedy cross-boundary matching). Lesson: when parsing nested HTML, understand the structure before writing patterns; greedy matching can skip necessary delimiters.
