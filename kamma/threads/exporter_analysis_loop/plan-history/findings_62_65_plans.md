# Findings 62-65: Proposed Queue (manual analysis of final_eval_56_61 artifacts)

Status: **PROPOSED — NOT APPROVED, NOT IMPLEMENTED.**
Written 2026-06-12 after manual review of:
- `temp/tier_eval/final_eval_56_61_low/`
- `temp/tier_eval/final_eval_56_61_deepseek/`

The next session must get explicit user approval for this queue (or a subset)
before any code edit, per the loop's planning gate.

Findings 62-64 are **pipeline defects with hard evidence**, not model
limitations. Finding 65 is a deferred design question. GitHub issue: `#197`.

---

## Shared evidence: the avijjānīvaraṇānaṃ case (SN15.1_p2)

The clearest single case demonstrating Findings 62 and 63 together.

1. `pre_match_db_examples` (`translate_core.py:274`) found that the DPD
   curated example for headword 10531 overlaps the passage, and promoted
   **all six** grammar-variant options (`10531_0`..`10531_5`, masc/fem/nt ×
   dat/gen pl) to `ai_score = 10` before the AI call.
2. DeepSeek nevertheless disambiguated correctly. Raw response
   (`final_eval_56_61_deepseek/SN15.1_p2_ai_raw.txt`, lines ~51 and ~774-800):
   it gave `10531_4` (fem **gen** pl) score 10 with contextual meaning
   "hindered by ignorance; obstructed by not understanding", and score 0 with
   `"contextual_meaning": "", "selected_pos": ""` to every other variant
   (DeepSeek echoes all keys with empty strings; second chunk picked
   `10531_3`, masc gen pl — also fine).
3. `_apply_deterministic_scores_to_map` (`translate_core.py:732`) then
   stomped the map: every `db_example_match` option was forced back to
   score 10, and the inline field-copy loop (~line 752,
   `if field in existing_score`) preserved the **empty strings** onto the
   demoted-then-re-promoted entries.
4. `merge_ai_selections` (`translate_core.py:1791`) copied
   `contextual_meaning` into `meaning_combo` with only an
   `if "contextual_meaning" in update:` membership check (~line 1820), so the
   empty strings **erased the dictionary fallback text**.
5. `_select_best_option` / `_option_rank` (`translate_core.py:1639`) sees six
   options tied at 10 with identical rank components and `max()` returns the
   first: `10531_0`, masc **dat** pl, `meaning_combo = ""`.

Net result in the shipped report: wrong grammar (dat pl instead of gen pl)
AND a blank Meaning cell, even though the model had returned the right answer.

Re-verify with:

```sh
jq '.final_scores | to_entries[] | select(.key | startswith("10531_"))' \
  temp/tier_eval/final_eval_56_61_deepseek/SN15.1_p2_ai_debug.json
jq '[.analysis[] | select(.word=="avijjānīvaraṇānaṃ") | .data[]
     | {key, grammar, ai_score, meaning_combo}]' \
  temp/tier_eval/final_eval_56_61_deepseek/SN15.1_p2_study.json
```

Same flattening produced wrong "dat pl" rows in **both** models' SN15.1
reports for `avijjānīvaraṇānaṃ` (10531), `taṇhāsaṃyojanānaṃ` (29404),
`sandhāvataṃ` (58457), `saṃsarataṃ` (61773); correct agreement with
`sattānaṃ` (gen pl) is genitive.

---

## Finding 62 — empty AI strings overwrite report meanings

**Symptom.** Blank Meaning cells in DeepSeek reports:
- `MN41_p2_study.md` row `nu` (38664) — raw response had
  `"38664_default": {"score": 10, "contextual_meaning": "", "selected_pos": "ind"}`.
- `SN15.1_p2_study.md` — ~10 blank cells (`anamata`, `avijjānīvaraṇānaṃ`,
  `taṇhāsaṃyojanānaṃ`, `sandhāvataṃ`, `saṃsarataṃ`, repeated in the refrain).

The Low run rendered the same rows with raw dictionary fallback text because
Low omitted those keys entirely, so nothing overwrote `meaning_combo`.

**Root cause.** Two unguarded copies of empty strings:
- `merge_ai_selections`, ~`translate_core.py:1819-1822`:
  `if "contextual_meaning" in update: item["meaning_combo"] = update["contextual_meaning"]`
  (same for `selected_pos`). Membership check, not content check.
- `_apply_deterministic_scores_to_map`, ~`translate_core.py:750-754`: inline
  `for field in (...): if field in existing_score:` copies `""` values. Note
  the existing helper `_copy_score_context_fields` (~line 671) already does
  the right truthiness check — reuse it here.

**Fix (minimal).**
1. In `merge_ai_selections`: assign `meaning_combo` only when the update's
   `contextual_meaning` is a `str` and non-empty after `.strip()`; same guard
   for `selected_pos`. Use explicit `isinstance(value, str)` so pyright
   narrows.
2. In `_apply_deterministic_scores_to_map`: replace the inline field-copy
   loop with `_copy_score_context_fields(existing_score, deterministic_score)`.

**Tests first (red phase), in `tests/exporter/analysis/test_translate_core.py`:**
- `merge_ai_selections` given `{"score": 10, "contextual_meaning": "", "selected_pos": ""}`
  → `meaning_combo` keeps the dictionary value, `selected_pos` not set to `""`.
- `merge_ai_selections` given non-empty contextual meaning → still overwrites
  (regression guard).
- `_apply_deterministic_scores_to_map` with an existing scores-map entry
  carrying `contextual_meaning: ""` → resulting deterministic entry has **no**
  `contextual_meaning` key.

---

## Finding 63 — db-example promotion flattens the AI's grammar-variant choice

**Symptom.** Both models' SN15.1 reports show "masc dat pl" for four words
where the AI chose (or would choose) gen pl. See shared evidence above.

**Root cause.** `_apply_deterministic_scores_to_map` overwrites the
scores-map entry of **every** `db_example_match` option with score 10. The
promotion's legitimate purpose is protecting the headword **id** against
wrong-homonym AI picks; flattening the **intra-id grammar variants** destroys
correct AI disambiguation.

**Fix.** Restructure `_apply_deterministic_scores_to_map` to decide per
group before writing:
1. For each token, collect `db_example_match` options grouped by headword
   `id` (use `_iter_options`; group key `option["id"]`, fall back to the key
   prefix before `_` if id missing).
2. For each group, inspect the **pre-existing AI entries** in `scores_map`
   for the group's keys (must be read before any stomping — hence two-phase):
   a key counts as an AI selection when its value is a dict with a numeric
   `score > 0` (or a bare positive number, given `_normalize_ai_response`
   wraps scalars).
3. If the group has ≥1 AI-positive key: promote **only the top AI-scored
   key(s)** to `{"score": 10, "selection_source": option's db_example_*}`,
   preserving non-empty contextual fields via `_copy_score_context_fields`.
   Leave the other group keys' AI entries untouched (their 0s stand); for
   group keys absent from `scores_map`, write `{"score": 0,
   "selection_source": "db_example_variant_not_selected"}` so the pre-set
   `ai_score = 10` from `pre_match_db_examples` cannot survive through
   `merge_ai_selections`' `else: item["ai_score"] = item.get("ai_score")`
   branch.
4. If the group has **no** AI-positive key (Low's typical case): keep current
   behavior — promote all variants to 10. This preserves the original
   wrong-homonym protection and changes nothing for those runs.
5. The `elif key not in scores_map` fallback branch and the quotative-`ti`
   logic stay as is.

**Interaction check (must reason in tests):** when the AI positively scored a
*different* id than the db-matched one, the db-matched id's winner still gets
promoted to 10 → tie at 10 with the AI's pick → `_db_example_rank` inside
`_option_rank` still makes the db-matched option win. Designed behavior
unchanged.

**Tests first:**
- Token with one id, three db-matched variants pre-promoted; AI map has
  `_1` → score 10 + meaning, `_0`/`_2` → score 0. After apply: `_1` is 10
  with db_example selection_source, `_0`/`_2` remain 0;
  `_select_best_option` picks `_1`.
- Same token but AI map empty for the group → all three promoted to 10
  (current behavior preserved).
- Group keys missing from the map entirely with one AI-positive sibling →
  missing keys get score 0 (so stale `ai_score=10` cannot leak through merge).
- AI picked a different id at 10 → db-matched winner still outranks it via
  `_db_example_rank` (regression guard for the original homonym protection).

---

## Finding 64 — component tie-break prefers `ind`, picks "own; personal; self-" inside "peace of mind"

**Symptom.** Low `TH215_study.md` renders compound component `santi` (inside
`cetosanti` = "peace of mind") as id 61527 `ind` "own; personal; self-".
Correct is 58258 fem "peace; calm; tranquillity" (DeepSeek got it right only
because it happened to score that component). This contradicts the earlier
"Low TH215 is clean" assessment — duration grammar was clean, this component
row is not.

**Root cause.** All 13 `santi` homonym component options sit at
`ai_score = 0` (the missing-score retry returned all zeros — see Finding 65).
On full ties, `_option_rank`'s `component_pos_rank`
(`1 if is_component and option.get("pos") == "ind"`) promotes the
indeclinable homonym, which is right for sandhi particles (`api`, `iti`,
`eva`) but wrong for nominal compound parts.

Verify with:

```sh
jq '[.analysis[] | select(.word | test("cetosanti"))
     | .data[0].components[0][0].components[]?
     | map({key, pali, ai_score, meaning_combo})]' \
  temp/tier_eval/final_eval_56_61_low/TH215_study.json
```

**Fix (deterministic, no AI cost).** Add a parent-meaning-overlap rank for
components:
1. New helper `_parent_meaning_overlap_rank(option, parent_meaning: str) -> int`:
   lowercase, split both the option's `meaning_combo`/`meaning_1` and the
   parent meaning into word tokens, drop a tiny stopword set
   (`of/the/a/an/to/in/is/one's`), return 1 on any shared token else 0.
2. Thread the parent's meaning into selection:
   `_select_best_option(options, is_component=True, parent_meaning=...)`,
   passed from `format_markdown_table.add_rows_recursive`, where the
   enclosing option's `meaning_combo` is available. Default `""` keeps all
   other call sites unchanged.
3. In `_option_rank`, insert the overlap rank **above** `component_pos_rank`
   (after `_direct_key_rank`), keep `component_pos_rank` as the next
   tie-break.

Expected effects: `santi` → "peace" wins ("peace of mind" ∩ "peace; calm;
tranquillity"); `api` inside `mattam'pi` (parent meaning "even a finger-snap
measure") still picks "even" — overlap agrees with the ind-preference there.
When no overlap exists, ranking falls through to existing behavior — no
regression surface.

**Tests first:**
- cetosanti-style fixture (parent meaning "peace of mind", options including
  ind "own; personal; self-" and fem "peace; calm; tranquillity", all
  `ai_score` 0) → "peace" option selected.
- mattam'pi-style fixture (parent "even a finger-snap measure", ind option
  "even") → ind "even" still selected.
- No-overlap fixture → same option as before the change (lock in current
  fallback order).

---

## Finding 65 — DEFERRED: all-zero retry groups count as "resolved"

**Observation.** Low TH215 first pass left the `santi` component group
unscored; the missing-score retry returned **score 0 for all 13 options**;
`_find_missing_score_groups` then reported nothing missing (keys exist in the
map), so the group counts as resolved with no selection. Renderer tie-break
decides (badly — see Finding 64).
`missing_score_groups_after_retry` is `[]` in
`final_eval_56_61_low/TH215_ai_debug.json` despite no selection existing.

**Options (not chosen yet):**
- A. Treat "all options scored 0 by AI" groups as still-missing for one
  supplemental pass with a "you MUST select exactly one option" instruction.
  Risk: more retry tokens; conflicts with the Finding 58 "don't enumerate
  score-0 options" prompt style and DeepSeek's echo-zeros habit (echoed
  zeros would look like deliberate all-zero answers — would need
  `selection: none` semantics, not trivial).
- B. Accept tie-break-only resolution and rely on Finding 64's overlap rank.
- C. Record all-zero groups in the debug JSON (`all_zero_groups`) for
  observability only.

**Recommendation:** implement Findings 62-64 first; B+C is likely enough.
Decide on A only if blank/wrong component homonyms still show up in the next
live evaluation.

---

## Observed but NOT actionable (model/content limitations — no code change)

- DeepSeek SN15.1 free translation **dropped the negation** in
  `apariyādinnā'va` ("grandmothers would be exhausted" — sense inverted).
  Word-level row was correct. Model limitation; noted for model comparisons.
- DeepSeek TH215 nominative duration residual — existing open decision in
  `handoff.md`, unchanged by this queue (41672 has no db-example overlap, so
  Finding 63 does not touch it).
- `kaṭā` = "winning dice" inside the SN15.1 bracketed commentary gloss
  (`[kaṭasi kaṭā chavā sayan'ti etthā'ti kaṭasī]`) on **both** models —
  editorial apparatus analyzed as passage text; out of scope without a new
  approved plan.
- `yena` in MN41 means "where" in the approach idiom and "by which" in the
  question, but one-selection-per-surface-word forces a single choice (Low
  chose "by which" everywhere, DeepSeek "where" everywhere). Known structural
  limitation, same family as the AN3.33 `bhagavā` case.
- Low MN41 `sammodanīyaṃ`/`sāraṇīyaṃ` acc vs DeepSeek nom — agreement with
  fem `kathaṃ` is imperfect in DPD's option inventory either way; not
  pipeline-caused.

## Validation gates for the implementing session

For `exporter/analysis/translate_core.py` and
`tests/exporter/analysis/test_translate_core.py`, run each separately:
- `uv run ruff check --fix <file>`
- `uv run ruff format <file>`
- `uv run pyright <file>`
- `uv run --with pyrefly pyrefly check --min-severity warn <file>`
- `uv run pytest tests/exporter/analysis/test_translate_core.py -v`

Confirm the red phase for every new test before implementing. Optional live
proof (user decision — costs AI calls): re-run `SN15.1_p2` on Low and
DeepSeek and check (a) zero empty Meaning cells, (b) gen pl on the four
refrain words, (c) `santi` = "peace" in TH215 on Low. If `uv run` hits
`/Users/deva/.cache/uv` permission problems, retry with
`UV_CACHE_DIR=/private/tmp/uv-cache`. Any commit must reference `#197`.
