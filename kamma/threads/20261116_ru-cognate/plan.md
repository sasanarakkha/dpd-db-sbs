# plan.md — Populate `russian.ru_cognate` (issue #10)

**Issue:** local issue #10 — https://github.com/sasanarakkha/dpd-db-sbs/issues/10
**Spec:** `spec.md` in this folder. Read it fully before starting.

## Architecture Decisions
- **Five files in `scripts/ru_cognate/`** (`ru_cognate_sound.py`, the code-side sound label, added by spec 7
  amendment 2026-11-17 e): `ru_cognate_etyma.py` (pure dump parsing),
  `ru_cognate_ledger.py` (units + join + ledger I/O; one-shot CLI plus `--add-new`), `ru_cognate_ai.py`
  (`propose` / `verify` batches), `ru_cognate_write.py` (DB write). Ledger I/O lives in
  `ru_cognate_ledger.py` and is imported by the other two.
- **The ledger TSV is the only state.** Resumable by `status`; atomic rewrite after each batch.
- **Reuse, don't copy:** `AIManager` (`tools/ai_manager.py`, model chains from `tools/ai_models.json`),
  `JSONParser` (`tools/ai_json_parser.py`), `require_offpeak` (`kamma/translate/scripts/offpeak.py`),
  `AllowableCharacters.ru_meaning_allowed` (`db_tests/single/sbs_test_allowable_characters.py`).
- **Inspect before coding:** unverified data facts are settled from real data in Phase 1; a contradiction
  with the spec stops the run for a Pro-model amendment (task 1.6).
- **Streaming parse with substring prefilter** (`"ine-pro"` / `"sla-pro"` in the raw line before
  `json.loads`) — the Russian dump is 948 MB.
- **No download code, no new dependencies.** Nothing shared enough to justify a `tools/` module.
- **Executor:** Sonnet runs every phase. Cognate judgments are made by the deepseek models in
  `ai_models.json`, not by the executor.

## User stop points
1.2 sheet edit · 1.6 escalation (only if triggered) · 6.1 pilot results · 7.1 ledger review ·
8.3 go-ahead for the DB write · 9.0 translate-overhaul thread still open.

## Phase 1 — Data, sheet, inspection
- [x] 1.1 Download into `temp/ru_cognate/`:
  `https://kaikki.org/dictionary/Sanskrit/kaikki.org-dictionary-Sanskrit.jsonl`,
  `https://kaikki.org/dictionary/Pali/kaikki.org-dictionary-Pali.jsonl`,
  `https://kaikki.org/dictionary/Russian/kaikki.org-dictionary-Russian.jsonl`,
  `https://kaikki.org/dictionary/Proto-Slavic/kaikki.org-dictionary-ProtoSlavic.jsonl`, and the sheet CSV
  `https://docs.google.com/spreadsheets/d/11QwooFKuN7CY14BFHJ84lW7u_0XWcbIA1z00NX7OXfI/export?format=csv`.
  → verify: 5 files present; each JSONL's first line parses with `json.loads`.
- [x] 1.2 Copy the CSV verbatim to `shared_data/ru_cognate/sheet_snapshot.csv`. **STOP: ask the user to
  edit it (remove rows) and wait for confirmation.**
  → verify: user confirmed; final `wc -l` recorded on this line.
- [x] 1.3 Inspect the dumps; write `## Inspection` in `baseline.md` answering:
  (a) Proto-Slavic entry `word` vs the `sla-pro` term in Russian `inh` templates (`*` prefix?);
  (b) the PIE term for брат, мать, дверь, три, новый as written in the Sanskrit-or-Pali, Proto-Slavic and
  Russian entries — **quote the actual strings for all 5**, then state identical or not;
  (c) for 10 DPD roots incl. `√budh`, `√ñā`, `√dvar`: does a Sanskrit entry's IAST `romanization`
  (accents stripped) equal `sanskrit_root` without `√`;
  (d) all borrowing template names found in Russian etymologies, with counts;
  (e) read `tools/ai_openai_compat.py` and the deepseek path in `tools/ai_manager.py`: what `grounding=True`
  does for deepseek; decide whether `verify` uses `grounding=True` or walks `grounded_models` explicitly
  via `provider_preference`/`model`.
  → verify: `## Inspection` answers (a)–(e), each with a quoted example or a file:line reference.
- [x] 1.4 Cut real-line fixtures into `tests/scripts/ru_cognate/fixtures/` (one JSONL per language): gold
  entries for дверь/брат/новый/будить with their Sanskrit/Pali and Proto-Slavic counterparts — incl. Skt
  `द्वार` (keys only via `etymon` hop + text) and `द्वार्`, Skt `नव` adj (PIE only in text), PSL `novъ`
  (text only), PSL `bratrъ` (template), Skt `बुध्` root (term in arg 4), Pali `mātar` + Skt `मातृ` (pi→sa hop);
  negatives: Pali `rosa` (`pi`→`pi` root), a Sanskrit `sa`→`sa` root entry, both Skt `kṛ` roots
  (homonyms), one Russian `bor+` entry, one Russian `calque` entry.
  → verify: every fixture line parses with `json.loads`; total size < 200 KB.
  **Done 2026-11-16 (drift from the list above, forced by the 200 KB cap and the real data):** Skt `नव` is the
  noun line (dump idx 1324, same text-only PIE as the adj, 9.9 KB vs 21 KB); Skt `मातृ` = two homonym lines (idx 152
  carries `*méh₂tēr` in text, idx 153 is the `sa`→`sa` `मा` root entry with no PIE) — so Pali `mātar` reaches
  `méh₂tēr` only via the homonym union; PSL `mati` and `trьje` NOT included (PSL fixture = `bratrъ`, `novъ`, `dvьrь`);
  Pali `dvāra`/`bhātar` not included; Russian negatives `лук` (`bor+`) and `новояз` (`calque`). 18 lines, 203,870 bytes.
- [x] 1.5 Phase check → verify: 1.1–1.4 ticked; `git status --short` shows no root-level files.
- [x] 1.6 **Escalation check.** TRIGGERED (see `baseline.md`); spec items 3, 4, 7 amended 2026-11-16 by
  the Pro session — term-string keys, `etymology_text` harvest, one-hop `etymon`/`pi`→`sa`, union for
  homonyms, join = candidate generator, `grounding=True` = chain selection only. User approved 2026-11-16. If any 1.3 finding contradicts the spec — PIE terms differ between
  languages for the same etymon, the Proto-Slavic key cannot be matched mechanically, or `grounding=True`
  fails or does nothing useful for deepseek — **STOP and ask the user to switch to the Pro model** for a
  spec/plan amendment before Phase 2. Otherwise continue.
  → verify: `## Inspection` ends with "Escalation: none" or lists what triggered it.

## Phase 2 — Etymon parser (`scripts/ru_cognate/ru_cognate_etyma.py`)
- [x] 2.1 Tests first, then code: `pie_keys(entry) -> set[tuple[str, str]]`, `is_loan(entry) -> bool`,
  `strip_accents(text) -> str`, `norm_pie(term) -> str`, per spec 3 (amended).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v` passes: `rosa` → no keys;
  `sa`→`sa` root → no keys; `बुध्` → `bʰudʰs` (arg 4); Skt `नव` adj → `newos` from text only;
  `*dʰwṓr` and `dʰwṓr` normalise equal, `*dʰwer-` → `dʰwer`; `bor+` and `calque` entries → loan;
  `буди́ть`→`будить`; `buddhá`→`buddha`.
- [x] 2.2 Tests first, then code: streaming indexers — Sanskrit (romanization → keys, plus one hop through
  the `sa`→`sa` root or `etymon` target; homonyms unioned), Pali (`word` → keys, plus one `pi`→`sa` hop),
  Russian (word → keys, direct or via the Proto-Slavic entry incl. its text-only keys; loans dropped).
  → verify: same test file passes new cases: брат and новый reach their PIE key only through the
  Proto-Slavic fixture; `द्वार` gets `dʰwṓr` via the `etymon` hop; Pali `mātar` gets `méh₂tēr`-normalised key
  via `मातृ`; both `kṛ` keys present; the `bor+` word is absent from the index.
- [x] 2.3 Phase check → verify: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright`
  (`--project /dev/null` for test files), `uv run --with pyrefly pyrefly check --min-severity warn` on the
  module and its test — all clean.

**Phase 2 done 2026-11-16 — drift recorded:** `pie_keys` returns `set[str]` (term only, not `(term, id)`). Suffix terms (leading `-`, e.g. `*-s` in Skt `द्वार` text) are skipped, else a bogus key `s` joins everything. `is_loan` counts a borrowing template only when its arg 1 equals the entry's own `lang_code` (a borrowing at an older stage, e.g. an `orv` ancestor, does not exclude). PSL `novъ` also carries `*nu` from text (legitimate second mention). Indexers take `Iterable[str]` lines: `index_sanskrit -> (by_romanization, by_devanagari)`, `index_pali(lines, skt_by_word)`, `index_protoslavic(lines)`, `index_russian(lines, psl) -> {pie_key: {words}}`. Sanskrit/Pali are not prefiltered (small); PSL/Russian are. Quality gates clean (ruff, pyright, pyrefly); 15 tests pass.

## Phase 3 — Units, join, ledger (`scripts/ru_cognate/ru_cognate_ledger.py`)
- [x] 3.1 Tests first, then code: `build_units(roots, headwords)` from plain row data (spec 1);
  `read_ledger` / `write_ledger` (atomic: temp file + `Path.replace`; column order per spec "Ledger").
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ledger.py -v` passes: `√argh √arh` →
  2 Sanskrit roots; family `mātar` collects `mātar, mātṛ`; ` + ` value dropped; `non_ia` → `none`;
  `read_ledger(write_ledger(x)) == x`.
- [x] 3.2 Tests first, then code: join (spec 4) + CLI `--dumps DIR`; refuse if the ledger exists.
  → verify: same file passes: a test family unit with Sanskrit side `dvāra` → `дверь`; family `nava1` (Skt `nava`) →
  `новый`; `√budh` and `√dvar` stay `pending` (known misses); a different term (`*bʰeh₂-` vs `*bʰewdʰ-`) does not join; candidates capped
  at 10 with `+N more`; second invocation exits non-zero and the file is unchanged.
- [x] 3.3 Phase check → verify: quality gates (as 2.3) clean on module and test.

**Phase 3 done 2026-11-16 — drift recorded:** `build_units` returns `list[Unit]` (dataclass: `row` + `sanskrit_terms` + `pali_words`; the join needs the Pāḷi/Sanskrit lookup terms, which are not ledger columns). Family Sanskrit cleaning also strips `[...]` (`dvāra [dvṛ]` → `dvāra`) and drops any value containing `+` (covers trailing `dvaya +`). `non_ia` rule = ANY headword of the unit has a non-empty `non_ia` (spec literal): live DB gives 7 roots and 18 families flagged (all-members rule would give 0 roots / 2 families) — flagged units can be reset to `pending` by hand. Join looks up Sanskrit terms in the romanization index and Pāḷi lemmas (no homonym number) in the Pāḷi index; `pie_root` = keys that hit a Russian word. Entry point: `run_full_join(dumps, ledger)`; `--add-new` comes in 9.1. Gates clean; 14 tests pass.

## Phase 4 — Join run and baseline
- [x] 4.1 Run `uv run python scripts/ru_cognate/ru_cognate_ledger.py --dumps temp/ru_cognate`.
  → verify: row count = 753 + `sqlite3 dpd.db "select count(distinct family_word) from dpd_headwords where root_key='' and family_word!=''"`;
  printed totals (proposed / pending / none) sum to it; no `none` row has candidates;
  `grep -cE 'карма|будда|нирвана|шаман'` on the `ru_candidates` column = 0.
- [x] 4.2 Complete `baseline.md`: unit counts; resolved units per type and source; Russian entries reaching
  PIE direct vs via Proto-Slavic; gold-set table (13 pairs: found / miss + reason); sheet pairs reproduced;
  AI request estimate recomputed from the real `pending` and `proposed` counts.
  → verify: every number in `baseline.md` has the command that reproduces it next to it.
- [x] 4.3 Delete the dumps in `temp/ru_cognate/`. → verify: `temp/ru_cognate` absent.

**Phase 4 done 2026-11-16:** ledger 1,607 rows (560 proposed / 1,022 pending / 25 none); gold 12/13 (miss `cha`→шесть explained in `baseline.md`). Two bugs found by the gold check and fixed with tests: `is_loan` (inherited word + later-sense calque, e.g. имя) and the Russian prefilter now also accepts `Proto-Indo-European`. `temp/ru_cognate/` deleted (the `baseline_stats.py` recipe is described in `baseline.md`; re-download via the README curl lines once written in 10.1).

## Phase 5 — AI batch script (`scripts/ru_cognate/ru_cognate_ai.py`)
- [x] 5.1 Tests first, then code: prompt builders (`propose` per spec 6, reading member headwords
  read-only from the DB; `verify` per spec 7 — claim only), response validation (spec 8) using
  `JSONParser`, ledger update rules (spec 6–7). `AIManager` mocked.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py -v` passes: the verify prompt has
  no confidence or proposer reasoning; unknown `unit_key`, >3 words, a Latin word → row unchanged;
  `none` → `status none`; `rejected` / `cannot_verify` → `disputed`; `confirmed` fills `ru_final`.
- [x] 5.2 Tests first, then code: CLI `propose|verify --batch-size 25 --max-batches N --allow-peak`;
  `require_offpeak` imported from `kamma/translate/scripts/offpeak.py` and called before each batch (first
  blocked → exit 1; mid-run peak → "peak hours started — stopping", exit 0); no-content batch → exit 2;
  atomic ledger write after each batch; model selection per the 1.3(e) decision.
  → verify: same file passes: peak before batch 2 stops after batch 1 with exit 0 and batch 1 saved; the
  exit-2 path leaves the ledger as after the last good batch;
  `grep -n "from kamma.translate.scripts.offpeak import" scripts/ru_cognate/ru_cognate_ai.py` matches.
- [x] 5.3 Phase check → verify: quality gates clean on module and test;
  `uv run python scripts/ru_cognate/ru_cognate_ai.py --help` shows `propose`, `verify`, `--allow-peak`.

**Phase 5 done 2026-11-16 — drift recorded:** `JSONParser` only extracts JSON containing a `"comparisons"` key, so both prompts ask for `{"comparisons": [...]}`. The AI call is an injected `ask(prompt, system, grounding)` callable (`make_ask()` wraps `AIManager.request`; propose = default chain, verify = `grounding=True`), so tests need no AIManager patching. `run_batches(mode, ledger, ask, members, batch_size, max_batches, allow_peak)` skips rows already attempted this session (an unparseable batch cannot loop). Extra validation beyond spec 8: `cognate`/`unsure` need ≥1 word, `confirmed` needs ≥1 `ru_final` word, `verifier_note` non-empty, confidence int 1–10; `ru_final` is ignored unless `confirmed`; words may be hyphenated. Member headwords come from `load_members()` (≤5 per unit, shortest lemma first, read-only DB). Gates clean (ruff, pyright, pyrefly); 35 tests pass; `--help` shows `propose`, `verify`, `--allow-peak`.

## Phase 6 — AI runs (real calls, off-peak)
- [~] 6.1 Pilot: `propose --max-batches 1` on a batch containing gold/sheet units, then
  `verify --max-batches 1`. **STOP: show the user the changed rows and wait before continuing.**
  → verify: rows changed only from allowed statuses; gold units in the batch match expectations or are
  noted; user said continue.
  **Pilot done 2026-11-16 (awaiting user "continue"):** propose batch 1 → 23 rows changed (20 `none`, 3 `proposed`), 2 `unsure` with no words left `pending`. Verify batch 1 (25 rows) applied: 14 confirmed, 11 rejected. No gold unit was in either batch (`√dvar`/`√budh` were join hits, not pending; verify takes the first 25 `proposed`). Prompt defect found and fixed with a test: the unit line `unit_key: X (root)` made the model echo `(root)`, so the first verify reply matched nothing; the saved reply was applied locally (key suffix stripped), no AI re-run.
  **Decisions 2026-11-16 (user approved; executed by Fast in 6.1a–6.1c):** (1) tighten `VERIFY_RULES`;
  (2) `unsure` with no words → `status none`; (3) no gold-targeting flag — gold units are checked in the full
  verify run and reported at 6.4.
- [x] 6.1a Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py`:
  (i) append to `VERIFY_RULES` exactly:
  "Confirm a word only if a standard etymology (Vasmer, Derksen, Wiktionary) derives that word itself from
  the same PIE root as the Pāḷi/Sanskrit side. Judge each word separately: drop any word whose root differs
  or is uncertain, even if others in the list are good. If no word survives, the verdict is \"rejected\".
  Do not list a word that is only a derivative of a word already listed (дать, not дарить + даровать). Put
  first the word an ordinary Russian reader knows best. Your verifier_note must name the PIE root of each
  word you keep."
  (ii) `apply_propose`: verdict `unsure` with 0 words → `status = none` (`method = agent`), not a
  validation failure; `cognate` with 0 words stays a validation failure.
  Then set the 2 rows `√añch`, `√udrabh` (currently `pending` from the pilot) to `none` by local edit
  (no AI re-run).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py -v` passes with new tests: verify
  prompt contains "name the PIE root of each word you keep"; `unsure` + `[]` → `none`; `cognate` + `[]` →
  row unchanged; quality gates (as 2.3) clean on module and test.
- [x] 6.1b Snapshot the 25 pilot verify rows (status `verified`/`disputed`: key, `ru_final`,
  `verifier_verdict`) to the session scratchpad, then reset them locally to `status = proposed` with
  `verifier_verdict`, `verifier_note`, `ru_final` cleared. Move them to the top of the verify order only if
  `verify` would not pick them first — check `run_batches` order before editing (ledger order = they are
  the first `√a…`/`√i…` roots, so they should come first). Run `verify --max-batches 1` (off-peak).
  → verify: exactly those 25 rows changed; none left `proposed`.
- [x] 6.1c **STOP:** show the user a before/after table for the 25 rows (old vs new `ru_final` and verdict);
  check specifically `√as 1` (must not keep ещё/забыть) and `√ar`; good sets (око, огонь, есть/еда, дать,
  идти, искать, гнать) should survive. Wait for "continue" before 6.2. Record result in `baseline.md` →
  `## AI runs`.
  → verify: user said continue.
  **6.1c result 2026-11-16:** user rejected keeping semantically distant cognates → spec 7 amended (sound +
  meaning similarity, judged against member headwords). Executed in 6.1d–6.1f.
- [x] 6.1d Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py`: `build_verify_prompt(rows,
  members)` lists member headwords; `VERIFY_RULES` gains the sound + meaning rule (judged against the member
  headwords, `√ādā`/`√dā 1` example); `run_batches` passes members to verify; `main` loads members for both
  modes.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py -v` passes with new tests (verify
  prompt has member headwords and no confidence; rules mention member-headword meaning); quality gates (as 2.3)
  clean on module and test.
- [x] 6.1e Reset the 25 pilot rows (`verified`/`disputed`) to `proposed` (clear `verifier_verdict`,
  `verifier_note`, `ru_final`) by local edit; run `verify --max-batches 1` (off-peak).
  → verify: exactly those 25 rows changed; none left `proposed` among them.
- [x] 6.1f **STOP:** show the user the kept words for the 25 rows; wait for "continue".
  → verify: user said continue. **Result:** verdicts contradicted notes (√akkh, √agg, √aṅg, √añj 1); user
  approved the fix below and a stricter sound rule (`√ad` → only еда: the root consonant d must be heard;
  есть is dropped).
- [x] 6.1g Tests first, then code in `ru_cognate_ai.py`: verify reply schema puts `verifier_note` first
  (then `verifier_verdict`, `ru_final`); note = one short sentence naming each kept word's PIE root; sound
  rule sharpened: the Russian word must keep the audible root consonant(s) of the Pāḷi word (`√ad` → еда, not
  есть); the verdict must agree with the note (a kept word → "confirmed").
  → verify: test file passes with new tests (schema order, consonant rule text); gates clean.
- [~] 6.1h Reset the 25 pilot rows to `proposed`; run `verify --max-batches 1` (off-peak).
  → verify: no row whose note keeps a word has verdict `rejected`; `√ad` = еда; `√agg` = огонь; report to user.
  **Status 2026-11-16:** 3 pilot re-runs done (attempt limit). Contradictions fixed, `√agg`/`√is` fixed, but run-to-run instability (яд, едкий, найти, ячмень, рост) — STOPPED for the user's choice of a stabiliser (see `baseline.md`).
  **Closed 2026-11-17:** user chose option 2 (thinking for the verifier) without editing upstream files —
  spec 7 amendment 2026-11-17. Executed in 6.1i–6.1k.
- [x] 6.1i (done 2026-11-17; drift: `check_grounded_chain` takes `Sequence[tuple[object, ...]]` and `make_ask` passes `thinking=`/`max_tokens=` by key from `VERIFY_REQUEST_OPTIONS`, because pyright/pyrefly reject `**dict[str, object]` and mixed-type model tuples; 49 tests pass, gates clean, `git diff --stat tools/` empty) Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py` ONLY (do not touch
  `tools/ai_openai_compat.py`, `tools/ai_manager.py`, `tools/ai_models.json`):
  (a) module constant `VERIFY_REQUEST_OPTIONS: dict[str, object] = {"thinking": {"type": "enabled"},
  "max_tokens": 32768}`;
  (b) `check_grounded_chain(models: Sequence[tuple[str, ...]]) -> None` — `pr.red` + `raise SystemExit(1)` if
  `models` is empty or any `model[0] != "deepseek"`;
  (c) `make_ask(manager: AIManager | None = None) -> Ask` — `manager = manager or AIManager()`; inside
  `ask`: if `grounding` → `check_grounded_chain(manager.GROUNDED_MODELS)` then
  `manager.request(prompt=..., prompt_sys=..., grounding=True, **copy.deepcopy(VERIFY_REQUEST_OPTIONS))`;
  else the current call with no extra kwargs. `main` keeps calling `make_ask()`. Update the `make_ask`
  docstring.
  Tests (in `tests/scripts/ru_cognate/test_ru_cognate_ai.py`, a `FakeManager` with a `GROUNDED_MODELS`
  list and a `request(**kwargs)` that records its kwargs and returns
  `AIResponse(content="{}", status_message="Success")` from `tools.ai_manager`): verify call sends
  `grounding=True`, `thinking == {"type": "enabled"}`, `max_tokens == 32768`; propose call sends neither
  `thinking` nor `max_tokens`; a grounded chain containing a non-`deepseek` provider → verify call raises
  `SystemExit` and `request` was never called, while a propose call on the same manager still works; an
  empty grounded chain → `SystemExit`; two verify calls leave `VERIFY_REQUEST_OPTIONS` unchanged.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py -v` passes (44 old + new);
  `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright scripts/ru_cognate/ru_cognate_ai.py`,
  `uv run pyright --project /dev/null tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
  `uv run --with pyrefly pyrefly check --min-severity warn` on both files — all clean;
  `git diff --stat tools/` empty.
- [x] 6.1j (done 2026-11-17; run with `--allow-peak` on the user's explicit instruction; batch 10 #2 hit `finish_reason=length`, remaining 15 rows run at batch 5; see `baseline.md`) Off-peak pilot re-run with thinking. Check off-peak first:
  `uv run python -c "from datetime import datetime, timezone; from kamma.translate.scripts.offpeak import is_deepseek_peak; print(is_deepseek_peak(datetime.now(timezone.utc)))"`
  must print `False` (if `True`, STOP and tell the user when off-peak starts; never pass `--allow-peak`).
  (1) Snapshot run B: write `unit_key, status, verifier_verdict, ru_final, verifier_note` of the 25 pilot
  rows (status `verified`/`disputed` among the first 40 ledger rows) to `temp/ru_cognate_pilot/run_b.tsv`.
  (2) Reset those 25 rows locally: `status = proposed`, clear `verifier_verdict`, `verifier_note`,
  `ru_final` (use `read_ledger`/`write_ledger`, not sed). Confirm they are now the first 25 `proposed` rows
  in ledger order (`run_batches` takes `proposed` rows in ledger order).
  (3) Run exactly 25 rows — batch 10 does not divide 25, so two commands:
  `uv run python scripts/ru_cognate/ru_cognate_ai.py verify --batch-size 10 --max-batches 2`, then
  `uv run python scripts/ru_cognate/ru_cognate_ai.py verify --batch-size 5 --max-batches 1`.
  Record each batch's duration from the `SUCCESS in …s` line and any `finish_reason=` note.
  A row that fails validation stays `proposed` and is picked again by the next command, so before each
  command count the pilot rows still `proposed` (N) and use `--batch-size` ≤ N — never let a batch reach
  past the pilot rows. After the two commands, if pilot rows remain `proposed`, run once more with
  `--batch-size N --max-batches 1`; if any still remain, leave them and report.
  Failure handling: a timeout (`Read timed out` / `ERROR` with no content → exit 2) → re-run that step once
  with `--batch-size 5` (and `--max-batches` covering the rest of the 25); HTTP 400 mentioning `thinking`
  or `max_tokens`, or a second timeout → STOP, record the exact error in `baseline.md`, ask the user. Do
  not edit any `tools/` file to work around it.
  → verify: exactly the 25 pilot rows changed (diff against `run_b.tsv` keys); none of them left
  `proposed`; no non-pilot row changed (`proposed` count back to 538, `pending` 997, `none` 47).
- [x] 6.1k **STOP:** show the user a table of the 25 rows: run B (`ru_final`, verdict) vs run C (thinking)
  (`ru_final`, verdict). Check and call out specifically: `√ad` = еда only; `√i 1` = идти only; `√i 2` =
  none; `√añc`/`√añj 3` = none (no ячмень); `√ar` = none (no рост/расти); `√ādā` = none; `√agg` = огонь;
  `√is` = искать; `√akkh`/`√ikkh` = око; `√aṅg` = угол; `√añj 1` (угол?) flagged for the user. Report
  batch durations. Record the result in `baseline.md` → new section `### 6.1i–6.1j: thinking enabled
  (2026-11-17)`. Delete `temp/ru_cognate_pilot/`. Wait for "continue" (or a further decision: e.g. add
  option 1, two-pass intersection, if still unstable).
  → verify: user said continue; `temp/ru_cognate_pilot` absent.
  **6.1k result 2026-11-17:** user not satisfied with run C. Wrong keeps: `√ad` едкий (derivative, "caustic"),
  `√ar` расти (grow ≠ move); `√an` вонь does NOT sound similar to an/āna and its meaning is questionable.
  `√aṅg`/`√añj 1` угол is not an inconsistency (different member headwords). User chose **per-word labels +
  code-side keep rule** (spec 7 amendment 2026-11-17 b). Executed in 6.1l–6.1o.
- [x] 6.1l (done 2026-11-17; 64 tests pass, counts and cols 1–16 identical, `ru_flagged` empty everywhere, gates clean) Tests first, then code: new ledger column `ru_flagged` (comma-separated Cyrillic words for the
  user to decide at review) inserted in `COLUMNS` of `scripts/ru_cognate/ru_cognate_ledger.py` directly
  after `ru_final`. First copy the ledger to `temp/ru_cognate_pilot/ledger_before.tsv`. Migrate the live
  ledger once: read `shared_data/ru_cognate/ledger.tsv` with
  `csv.DictReader` (old header), add `ru_flagged = ""` to every row, write with `write_ledger` (atomic). Run
  the migration as a one-off `uv run python -c` command (no new file).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ledger.py -v` and
  `tests/scripts/ru_cognate/test_ru_cognate_ai.py -v` pass; `read_ledger` reads the migrated file; row count
  and status counts unchanged (`awk -F'\t' 'NR>1{print $13}' … | sort | uniq -c` before = after:
  538 proposed, 997 pending, 47 none, 9 verified, 16 disputed); every row's `ru_flagged` empty;
  `diff <(cut -f1-16 old) <(cut -f1-16 new)` empty (old snapshot in `temp/ru_cognate_pilot/`).
- [x] 6.1m (done 2026-11-17; drift: `apply_verify` splits into `_parse_labels` + rule code; per-word `note` must be non-empty; `ru_flagged` = reply-order union of flagged and overflow-kept words; `VERIFY_VERDICTS` replaced by four label sets `VERIFY_ETYMON/FORM/SOUND/MEANING`; 82 tests pass in the two files (+ etyma), ruff/pyright/pyrefly clean, `git diff --stat tools/` empty) Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py` only (no `tools/` edit):
  (a) `VERIFY_RULES` rewritten: the model no longer picks a set. For EVERY word in "claimed Russian
  cognates" it returns one object, fields in this order: `word` (copied exactly), `note` (one short
  sentence, written first), `etymon` `same|different|loan|uncertain`, `form` `base|derivative`, `sound`
  `close|weak|none`, `meaning` `close|drifted|far`. Words listed most recognisable first. Label
  definitions: `etymon` = standard etymology (Vasmer, Derksen, Wiktionary) derives this word itself from the
  same PIE root as the Pāḷi/Sanskrit side (PIE string is only a hint — keep the existing hint text);
  `form` = `derivative` if it is built on another Russian word with the same root (идти base; прийти,
  найти derivative); `sound` = how recognisably the whole Russian word sounds like the Pāḷi/Sanskrit word
  (audible root consonants kept and nothing that masks them); `meaning` = compared with the member
  headwords listed for the unit, not the root meaning. Anchors in the prompt (user decisions only):
  `√ad` "eat": еда same/base/close/close; есть sound none; медведь meaning far. `√ādā` "take": дать
  meaning far; `√dā 1` "give": дать close. `√i 1` "go": прийти derivative. `√an` "breathe": вонь sound
  none, meaning drifted. Do NOT add anchors for едкий, расти, угол, ячмень (they test generalisation).
  Reply schema: `{"comparisons": [{"unit_key": "...", "words": [{"word": …, "note": …, "etymon": …,
  "form": …, "sound": …, "meaning": …}]}]}`.
  (b) `apply_verify` validates and derives in code: every candidate word (from `ru_candidates`, split on
  `, `, normalised with the same `strip_accents().strip().lower()` as `parse_words`) labelled exactly once;
  an unknown, missing or duplicate word, or a bad label value → problem, row unchanged.
  keep = `same` + `base` + sound `close` + meaning `close`; flag = `same` + `base` + not keep + sound ≠
  `none` + meaning ≠ `far`; everything else dropped. `ru_final` = first 3 kept words in reply order; kept
  words beyond 3 go to `ru_flagged`; `ru_flagged` = flagged words in reply order.
  `verifier_verdict` = `confirmed` if `ru_final` non-empty else `rejected`; `status` `verified`/`disputed`.
  `verifier_note` = `"; ".join(f"{word} [{etymon}/{form}/sound {sound}/meaning {meaning}]: {note}")`
  (full audit trail, every word). `VERIFY_VERDICTS` reduced to the two derived values.
  (c) Update or remove the old tests that assume the model's verdict/`ru_final` (schema order, confirmed
  without ru_final, note/verdict agreement) — replace them, do not just delete coverage.
  New tests (each fails for a distinct reason): all four keep labels → kept; sound `weak` → flagged; meaning
  `drifted` → flagged; `derivative` → dropped; `different` etymon → dropped; sound `none` + meaning `close`
  → dropped; 4 kept words → 3 in `ru_final`, 4th in `ru_flagged`; only flagged words → `disputed` with
  `ru_flagged` filled; candidate word missing from reply → row unchanged + problem; extra word not in
  candidates → problem; bad label value → problem; accented reply word (`едá`) matches candidate `еда`;
  prompt contains the вонь anchor and no едкий/расти anchor; `verifier_note` lists every word.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py -v` passes; `uv run ruff check
  --fix`, `uv run ruff format`, `uv run pyright scripts/ru_cognate/ru_cognate_ai.py
  scripts/ru_cognate/ru_cognate_ledger.py`, `uv run pyright --project /dev/null` on both test files,
  `uv run --with pyrefly pyrefly check --min-severity warn` on all four files — clean; `git diff --stat
  tools/` empty.
- [x] 6.1n (closed early 2026-11-17 by user decision: D1 partial (20 of 25 rows) is the baseline; D2 and the held-out set are NOT run in thinking-on mode; replaced by 6.1p–6.1t) **STOPPED 2026-11-17 after D1:** batch 4 (√as 4, √āgam, √ādā, √ās, √i 1) hit `finish_reason=length` at batch 5 (456 s, no content) → 5 pilot rows still `proposed`; plan says STOP and not lower further without the user. D1 not snapshotted yet (D1 log: `temp/ru_cognate_pilot/d1.log`; run C snapshot: `run_c.tsv`; keys: `pilot_keys.txt`). Also seen: `-ед` (a suffix from the join) was KEPT for √ad. Testing round. **Peak hours may be ignored for this testing round only** (user, 2026-11-17):
  every 6.1n command runs with `--allow-peak`. This permission does NOT extend to 6.2, 6.3 or any later
  run — those stay off-peak only. All runs `--batch-size 5`.
  (1) Snapshot run C (the 25 pilot rows: `unit_key, status, ru_final, verifier_note`) to
  `temp/ru_cognate_pilot/run_c.tsv`. Reset the 25 pilot rows to `proposed` (clear `verifier_verdict`,
  `verifier_note`, `ru_final`, `ru_flagged`) via `read_ledger`/`write_ledger`; confirm they are the first
  25 `proposed` rows in ledger order.
  (2) **Run D1:** `verify --batch-size 5 --max-batches 5`. Snapshot the 25 rows (+ `ru_flagged`) to
  `temp/ru_cognate_pilot/run_d1.tsv`. Reset them again.
  (3) **Run D2** (stability): same command; snapshot to `run_d2.tsv`. Leave D2 in the ledger.
  (4) **Held-out set:** the next 25 `proposed` rows in ledger order (never seen in any prompt anchor) —
  record their keys first, then `verify --batch-size 5 --max-batches 5`. Leave them verified (real progress).
  Failure handling as 6.1j (a row failing validation stays `proposed`: re-run with `--batch-size N` ≤ the
  pilot rows still `proposed`, once; then report). A `finish_reason=length` at batch 5 → STOP and report
  (do not lower further without the user).
  → verify: only the 25 pilot rows + the 25 recorded held-out rows changed; counts:
  `proposed` = 538 − 25 (held-out) = 513 (+ any rows left `proposed` after failures, reported);
  `pending` 997, `none` 47.
- [x] 6.1o (superseded 2026-11-17 by 6.1t — NOT run) **STOP:** show the user, with batch durations:
  (a) pilot table: unit | run C `ru_final` | D1 kept / flagged | D2 kept / flagged; call out √ad (еда only;
  едкий dropped as derivative), √an (вонь not kept), √ar (расти not kept), √añj 1 / √aṅg (угол), √agg
  огонь, √akkh/√ikkh око, √is искать, √i 1 идти, √i 2 / √ādā none, √añc / √añj 3 no ячмень;
  (b) stability: number of pilot rows where D1 ≠ D2 in kept set, and in flagged set, with the differing
  words and their labels;
  (c) held-out table: unit | member meaning | candidates | kept | flagged | short note — for the user to
  judge as fresh data.
  Record results in `baseline.md` → `### 6.1l–6.1n: per-word labels (2026-11-17)`. Delete
  `temp/ru_cognate_pilot/`. Wait for "continue" (or a further decision).
  → verify: user said continue; `temp/ru_cognate_pilot` absent.

**6.1p–6.1t: candidate cleanup + thinking-off two-pass pilot (user decision 2026-11-17; spec 7 amendment
2026-11-17 c).** Context for the executor: D1 (thinking on, batch 5) is correct on keeps but ~5 min per
5 rows and ~1 in 5 batches hits `finish_reason=length` → ~10 h for the full run. Option 2 = clean the
candidate lists in code; option 3 = verify twice with thinking OFF and keep only what both passes keep.
Files allowed to change: `scripts/ru_cognate/ru_cognate_ledger.py`, `scripts/ru_cognate/ru_cognate_ai.py`,
`tests/scripts/ru_cognate/test_ru_cognate_ledger.py`, `tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
`shared_data/ru_cognate/ledger.tsv` (via the commands below only), this thread's `plan.md`/`baseline.md`/
`handoff.md`. **Do NOT edit anything under `tools/`** (`git diff --stat tools/` must stay empty). No new
files in the repo (scratch only under `temp/ru_cognate_pilot/`). No DB writes. No commits.
**Peak hours:** the user allowed `--allow-peak` for the 6.1n testing round; 6.1s is the same testing round
and uses `--allow-peak` ONLY if the user confirmed it when approving this plan (see handoff) — otherwise run
6.1s off-peak only (drop the flag; the script exits 1 in peak hours → wait).

- [x] 6.1p (done 2026-11-17; verify passed) Snapshot D1 and reset the pilot rows. Keys are in `temp/ru_cognate_pilot/pilot_keys.txt`
  (25 lines). (1) Write `temp/ru_cognate_pilot/run_d1.tsv` (header + 25 rows, tab-separated:
  `unit_key, status, ru_final, ru_flagged, verifier_note`) from the live ledger via `read_ledger`, in
  pilot-key order. (2) Copy the ledger to `temp/ru_cognate_pilot/ledger_before_clean.tsv`. (3) Reset the
  25 pilot rows to `status = proposed` and clear `verifier_verdict`, `verifier_note`, `ru_final`,
  `ru_flagged` (via `read_ledger`/`write_ledger`, one-off `uv run python -c`, no new file).
  → verify: `run_d1.tsv` has 26 lines; status counts = `proposed 563, pending 997, none 47` (no
  `verified`/`disputed`); the first 25 `proposed` rows in ledger order are exactly the pilot keys (print
  both lists and compare); no other column of any row changed (diff against `ledger_before_clean.tsv`
  for non-pilot rows = identical).

- [x] 6.1q (done 2026-11-17; 39 tests pass, live ledger (92, 149), counts unchanged, gates clean) Tests first, then code: candidate cleanup in `scripts/ru_cognate/ru_cognate_ledger.py`.
  (a) Module constant `CLOSED_CLASS_RU: frozenset[str]` with exactly these 74 words:
  `и а но да ли бы же ни не абы ещё он она оно они его её их им ему я ты мы вы то тот этот сей сям там тут
  здесь где как кто что когда вот вон уж уже в во на о об обо у к ко с со из от до по за над под при про без
  для или либо ибо аж чтобы ведь вне сквозь через между перед`. Comment above it: DPD roots are verbal, so
  closed-class Russian words are never a root's cognate; family units keep them (e.g. family `ka` → кто).
  (b) `clean_candidates(words: list[str], unit_type: str) -> list[str]`: for each word, normalise with
  `strip_accents(w).strip().lower()`; skip empty; skip if it starts or ends with `-` (an internal hyphen
  stays); skip duplicates of an already-kept word; skip if `unit_type == "root"` and the word is in
  `CLOSED_CLASS_RU`; keep input order.
  (c) `join_units`: build `ordered` as now (sorted by length, then word), then
  `ordered = clean_candidates(ordered, row["unit_type"])` BEFORE the `MAX_CANDIDATES` cut; if it is empty,
  `continue` (row stays `pending`, untouched — same as a join miss). The `source` text uses the cleaned
  `shown` list (it already does, since it is built from `shown`).
  (d) `clean_ledger(rows: list[Row]) -> tuple[int, int]`: only rows with `status == "proposed"`; set
  `ru_candidates = ", ".join(clean_candidates(old split on ", ", unit_type))`; if the result is empty set
  `status = "pending"` and clear `pie_root`, `ru_candidates`, `source`, `method` (a join miss looks like
  that). Leave `source` text otherwise unchanged (it records what the join saw). Return
  `(rows_changed, words_dropped)`. Never touch rows in any other status.
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_ledger.py` (each fails for a distinct reason):
  1. leading-hyphen `-ед` and trailing-hyphen `су-` dropped; `кое-что` kept;
  2. `кто` dropped for `unit_type="root"`, kept for `"family"`;
  3. `е́да` and `еда` → one `еда` (accent-strip dedupe), order preserved;
  4. `join_units`: a root unit whose Russian key maps to 10 closed-class words plus one longer real word
     gets the real word in `ru_candidates` (proves cleaning happens before the 10-cap);
  5. `join_units`: a root unit whose only Russian words are closed-class stays `pending` with empty
     `ru_candidates`;
  6. `clean_ledger`: a `verified` row containing `-ед` is untouched; a `proposed` row is cleaned; the
     return value counts rows and words correctly;
  7. `clean_ledger`: a `proposed` row left with no words becomes `pending` with `pie_root`, `source`,
     `method`, `ru_candidates` empty.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ledger.py
  tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v` passes (all old tests too).
  Then apply once to the live ledger (one-off, no new file):
  `uv run python -c "from scripts.ru_cognate.ru_cognate_ledger import LEDGER_PATH, read_ledger, write_ledger, clean_ledger; rows = read_ledger(LEDGER_PATH); print(clean_ledger(rows)); write_ledger(LEDGER_PATH, rows)"`
  → verify: prints `(92, 149)` (measured 2026-11-17 with the same rules on all 563 candidate rows; a
  different number → STOP and report, do not adjust the word list); counts still `proposed 563,
  pending 997, none 47`; no `ru_candidates` word starts or ends with `-` (check with a short
  `uv run python -c` over `read_ledger`);
  √ad candidates no longer contain `-ед`; √i 1 no longer contains `и, их, он`; family rows unchanged
  except affixes/duplicates.

- [x] 6.1r (done 2026-11-17; 121 tests pass across ai/ledger/etyma, ruff/pyright/pyrefly clean, tools/ diff empty; drift: none — apply_verify refactored to _outcome/_candidates/_note/_set_result helpers, behaviour unchanged) Tests first, then code: thinking-off and two-pass verify in `scripts/ru_cognate/ru_cognate_ai.py`.
  (a) Constant `VERIFY_NO_THINKING: dict[str, str] = {"type": "disabled"}`.
  (b) `make_ask(manager: AIManager | None = None, thinking: bool = True) -> Ask`: unchanged for propose
  and for verify with `thinking=True`. Verify with `thinking=False`: still `check_grounded_chain(...)`,
  then `manager.request(prompt=..., prompt_sys=..., grounding=True, thinking=copy.deepcopy(VERIFY_NO_THINKING))`
  — NO `max_tokens` kwarg (provider default 8192 applies).
  (c) Refactor only: extract `_outcome(entry: dict[str, str]) -> str` returning `"keep"`, `"flag"` or
  `"drop"` with exactly the current rule (keep = same + base + sound close + meaning close; flag = same +
  base + not keep + sound ≠ none + meaning ≠ far; else drop). `apply_verify` uses it; its behaviour must
  not change (all existing `apply_verify` tests pass unedited).
  (d) `apply_verify_pair(rows: list[Row], items_a: list[Item], items_b: list[Item]) -> tuple[int, list[str]]`:
  match each pass with `_match`; prefix every problem with `pass 1: ` / `pass 2: `. A row changes only when
  BOTH passes give valid labels via `_parse_labels` (otherwise unchanged + problem). Per word: outcome
  `keep` if keep in both; `drop` if drop in both; else `flag`. Kept words in pass-1 label order; first
  `MAX_WORDS` → `ru_final`, overflow joins flagged (as in `apply_verify`); `ru_flagged` in pass-1 label
  order. `verifier_verdict`/`status` as in `apply_verify`. `verifier_note` = the same per-word string
  `apply_verify` builds from pass-1 labels, plus — only if some word's two outcomes differ —
  ` || pass 2 differs: <word> <out1>/<out2>, ...` (e.g. `едкий flag/drop`).
  (e) `run_batches(..., passes: int = 1)`: for `mode == "verify"` and `passes == 2`, call `ask` twice with
  the identical prompt/system; if either returns `None` → red message, exit 2, rows unchanged (same as now);
  if either fails `parse_response` → `unparseable response (pass N), <k> rows unchanged`, count problems,
  `continue`; else `apply_verify_pair`. `passes == 1` path is unchanged.
  (f) CLI: `--no-thinking` (store_true) and `--passes` (int, choices 1, 2, default 1). In `main`, if
  `mode == "propose"` and (`--no-thinking` or `--passes 2`) → `parser.error(...)`. Pass
  `make_ask(thinking=not args.no_thinking)` and `passes=args.passes`.
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_ai.py` (each fails for a distinct reason; reuse
  `FakeAsk`, `FakeManager`, `make_row`):
  1. `make_ask(manager, thinking=False)` verify call: `grounding is True`, `thinking == {"type": "disabled"}`,
     `"max_tokens" not in call`;
  2. `make_ask(manager, thinking=False)` still refuses a non-deepseek grounded chain (SystemExit, no call);
  3. pair: keep/keep → word in `ru_final`, status `verified`;
  4. pair: keep/flag → word in `ru_flagged` only;
  5. pair: keep/drop → word in `ru_flagged` only;
  6. pair: drop/drop → word in neither; row `disputed`; note has no `pass 2 differs`;
  7. pair: flag/flag → `ru_flagged`;
  8. pair: pass 2 misses a candidate word → row unchanged, one problem starting `pass 2: `;
  9. pair: disagreement note → `verifier_note` ends with ` || pass 2 differs: <word> keep/drop`;
  10. pair: 4 words keep/keep → 3 in `ru_final`, 4th in `ru_flagged`;
  11. `run_batches(..., passes=2)` with 3 rows, batch 3: `FakeAsk` called exactly twice with identical
      prompts, ledger shows the intersection;
  12. `run_batches(..., passes=2)`: second reply unparseable → rows stay `proposed`, problems counted,
      exit 0;
  13. `run_batches(..., passes=2)`: second reply `None` → exit 2, rows unchanged;
  14. `main` rejects `propose --passes 2` and `propose --no-thinking` (SystemExit from `parser.error`;
      monkeypatch `sys.argv`, and stub `require_offpeak`/`load_members` so nothing real runs).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py
  tests/scripts/ru_cognate/test_ru_cognate_ledger.py tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v`
  passes. Gates on all four touched files: `uv run ruff check --fix`, `uv run ruff format`,
  `uv run pyright scripts/ru_cognate/ru_cognate_ai.py scripts/ru_cognate/ru_cognate_ledger.py`,
  `uv run pyright --project /dev/null tests/scripts/ru_cognate/test_ru_cognate_ai.py
  tests/scripts/ru_cognate/test_ru_cognate_ledger.py`, `uv run --with pyrefly pyrefly check
  --min-severity warn <all four files>` — clean; `git diff --stat tools/` empty. Never run bare
  `uv run pytest`.

- [x] 6.1s (done 2026-11-17; see baseline.md) Pilot E: thinking off, two passes, on the cleaned candidates. Each command tees its log;
  read per-request seconds from the `SUCCESS in` lines. Peak-hour flag: see the note above 6.1p.
  (1) **E1:** confirm again the first 25 `proposed` rows are the pilot keys, then
  `uv run python scripts/ru_cognate/ru_cognate_ai.py verify --no-thinking --passes 2 --batch-size 5
  --max-batches 5 [--allow-peak] 2>&1 | tee temp/ru_cognate_pilot/e1.log`.
  Failure handling: any `finish_reason=length` or unparseable batch → after the run, re-run ONCE for the
  pilot rows still `proposed` with `--batch-size 3 --max-batches <ceil(left/3)>`; confirm first that the
  first `proposed` rows are those pilot rows. Still failing → STOP and report.
  Snapshot the 25 pilot rows to `temp/ru_cognate_pilot/run_e1.tsv` (same columns as `run_d1.tsv`).
  Reset them (as 6.1p step 3).
  (2) **E2** (stability): same command, log `e2.log`, same failure handling; snapshot `run_e2.tsv`.
  Leave E2 in the ledger.
  (3) **Held-out:** confirm no pilot row is `proposed`; record the first 25 `proposed` keys to
  `temp/ru_cognate_pilot/heldout_keys.txt`; run the same command once (log `h1.log`); leave them in the
  ledger.
  → verify: only the 25 pilot + 25 held-out rows changed in columns `status`, `verifier_verdict`,
  `verifier_note`, `ru_final`, `ru_flagged` (diff against `ledger_before_clean.tsv` after cleaning:
  `ru_candidates`/`status` differences elsewhere come only from 6.1q); counts `proposed` 563 − 50 = 513
  (+ rows left `proposed` after failures, reported), `pending` 997, `none` 47.

- [x] 6.1t (done 2026-11-17: user approved thinking-off two-pass with the "keep in either pass" combination
  and the tighter flag rule — spec 7 amendment 2026-11-17 d; executed in 6.1u–6.1w) **STOP:** show the user:
  (a) pilot table: unit | expected (below) | D1 kept / flagged | E1 kept / flagged | E2 kept / flagged.
  Expected (user, 6.1k + D1 review): √ad еда only (no `-ед`, едкий not kept); √akkh, √ikkh око; √agg огонь;
  √is искать (kept or flagged); √i 1 идти; √i 2 none kept; √ādā none kept; √an вонь not kept; √ar
  рост/расти/растить not kept; √añc, √añj 3 no ячмень; √aṅg / √añj 1 угол → open question for the user.
  Call out every row where E kept a word D1 did not, and vice versa.
  (b) stability: pilot rows where E1 ≠ E2 in kept set and in flagged set (words + their two-pass notes);
  number of words with `pass 2 differs` in E1 and E2.
  (c) held-out table: unit | member meaning | candidates | kept | flagged | short note.
  (d) cost: per-request seconds (min/median/max) for E vs D1 (D1: 199, 337, 361, 410, 456-fail);
  failures; projected full-run time for the 513 remaining `proposed` rows + the propose output, at batch 5.
  (e) a recommendation for 6.3's mode (thinking-off two-pass vs thinking-on single pass, and batch size).
  Record in `baseline.md` → `### 6.1p–6.1s: candidate cleanup + thinking-off two-pass pilot (2026-11-17)`
  (include the cleanup result `(92, 149)` and that the dumps-based join fix is deferred). Delete
  `temp/ru_cognate_pilot/`. Update `handoff.md`. Wait for the user's decision.
  → verify: user decided; `temp/ru_cognate_pilot` absent.

**6.1u–6.1w: new pass combination + tighter flag rule (spec 7 amendment 2026-11-17 d).** Files allowed to
change: `scripts/ru_cognate/ru_cognate_ai.py`, `tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
`shared_data/ru_cognate/ledger.tsv` (via the commands below only), this thread's `plan.md`/`baseline.md`/
`handoff.md`. No `tools/` edits, no new repo files, no DB writes, no commits. Off-peak only (no `--allow-peak`).

- [x] 6.1u Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py`:
  (a) `_outcome`: flag additionally requires `sound == "close" or meaning == "close"`; keep rule and drop
  cases otherwise unchanged. Update the `_outcome` docstring.
  (b) `apply_verify_pair`: per word, `keep` if either pass is `keep`; `drop` if both are `drop`; else
  `flag`. Everything else (ordering, `MAX_WORDS` overflow, verdict/status, `|| pass 2 differs:` note) unchanged.
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_ai.py` (each fails for a distinct reason):
  1. NEW `apply_verify`: sound `weak` + meaning `drifted` → dropped (neither `ru_final` nor `ru_flagged`);
  2. existing `test_weak_sound_is_flagged_not_kept` and `test_drifted_meaning_is_flagged_not_kept` pass
     unedited (one label off `close` still flags);
  3. existing `test_only_flagged_words_make_the_row_disputed_with_flagged_filled` passes unedited;
  4. REPLACE `test_pair_keep_flag_is_flagged_only` → `test_pair_keep_flag_is_kept` (`ru_final` = дверь,
     status `verified`, note ends ` || pass 2 differs: дверь keep/flag`);
  5. REPLACE `test_pair_keep_drop_is_flagged_only` → `test_pair_keep_drop_is_kept`;
  6. NEW pair: drop/keep (keep only in pass 2) → kept;
  7. NEW pair: flag/drop → `ru_flagged` only;
  8. `test_run_batches_two_passes_asks_twice_and_keeps_intersection` → rename to `..._combines_passes`;
     row `b` (keep/drop) now has `ru_final` = дверь and empty `ru_flagged`; add a row-level check that a
     drop/drop row stays out of both columns (change the fake replies as needed).
  `test_pair_disagreement_is_noted` still passes unedited.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py
  tests/scripts/ru_cognate/test_ru_cognate_ledger.py tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v`
  passes; `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright scripts/ru_cognate/ru_cognate_ai.py`,
  `uv run pyright --project /dev/null tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
  `uv run --with pyrefly pyrefly check --min-severity warn` on both files — clean; `git diff --stat tools/` empty.
- [x] 6.1v Re-verify the 50 `disputed` rows (25 pilot + 25 held-out) with the new rules. Off-peak check first
  (as 6.1j; `True` → STOP, tell the user when off-peak starts). (1) Snapshot the 50 rows (`unit_key, ru_final,
  ru_flagged, verifier_note`) to `temp/ru_cognate_pilot/run_e.tsv`. (2) Reset them to `proposed` (clear
  `verifier_verdict`, `verifier_note`, `ru_final`, `ru_flagged`) via `read_ledger`/`write_ledger`; confirm the
  first 50 `proposed` rows in ledger order are exactly those keys. (3) Run
  `uv run python scripts/ru_cognate/ru_cognate_ai.py verify --no-thinking --passes 2 --batch-size 5
  --max-batches 10 2>&1 | tee temp/ru_cognate_pilot/f1.log`. Failure handling: rows left `proposed` among the
  50 → re-run once with `--batch-size N` (N ≤ those rows still `proposed`, confirm they are first in order);
  still failing → STOP and report.
  → verify: only those 50 rows changed; counts `proposed 513, pending 997, none 47` + `verified`/`disputed`
  summing to 50.
- [x] 6.1w **STOP:** show the user a table of the 50 rows: unit | run E kept / flagged | run F kept / flagged;
  call out every kept word, and check the expectations: √ad еда only; √akkh око; √agg огонь; √is искать;
  √kās 2 кашель; √i 2, √ādā none kept; no ячмень, яд, язь, кон/чадо/щенок, кой/чей, чары kept. Report flagged
  word and row counts (offline estimate was 17 words / 13 rows) and per-request seconds. Record in
  `baseline.md` → `### 6.1u–6.1w: new pass combination + flag rule (2026-11-17)`. Delete
  `temp/ru_cognate_pilot/`. Update `handoff.md`. Wait for "continue".
  → verify: user said continue; `temp/ru_cognate_pilot` absent.

**6.1x–6.1z: code-side sound label (spec 7 amendment 2026-11-17 e).** Files allowed to change: new
`scripts/ru_cognate/ru_cognate_sound.py` and `tests/scripts/ru_cognate/test_ru_cognate_sound.py`;
`scripts/ru_cognate/ru_cognate_ai.py`, `tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
`shared_data/ru_cognate/ledger.tsv` (via the commands below only), this thread's `plan.md`/`baseline.md`/
`handoff.md`. No `tools/` edits, no DB writes, no commits. Off-peak only. Both new files fall under the
`scripts/ru_cognate/` and `tests/scripts/ru_cognate/` entries that 10.1 registers.

- [x] 6.1x Tests first, then code: `scripts/ru_cognate/ru_cognate_sound.py` (one-sentence purpose docstring,
  pure, no imports beyond stdlib) with `sound_label(unit_key: str, sanskrit: str, word: str) -> str` exactly
  per spec 7 amendment e (class table, aspirate `h` skip, collapse, first 2 classes, close/weak/none, best over
  sources). Helpers `skeleton(source: str) -> list[str]` and `sources(unit_key: str, sanskrit: str) -> list[str]`.
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_sound.py`, parametrized `(unit_key, sanskrit, word,
  expected)`: close — (`√agg`,`ag`,огонь), (`√akkh`,`akṣ`,око), (`√ad`,`ad`,еда), (`√is`,`iṣ`,искать),
  (`√kās 2`,`kās`,кашель), (`bhātar`,`bhrātṛ`,брат), (`mātar`,`mātar, mātṛ`,мать), (`dvi`,`dvi, dva`,два),
  (`ti`,`tri`,три), (`nava1`,`nava`,новый), (`√dvar`,`dvṛ`,дверь), (`√budh`,`budh`,будить),
  (`√ñā`,`jñā`,знать), (`bhū`,`bhrū`,бровь), (`cha`,`ṣaḍ, ṣaṭka < ṣaṣ`,шесть), (`dhava`,`vidhavā`,вдова);
  weak — (`√ud`,`ud`,вода), (`√an`,`an`,вонь), (`√i 1`,`i`,идти), (`aṭṭha`,`aṣṭan`,восемь),
  (`nāma`,`nāma, nāman`,имя), (`√ad`,`ad`,медведь), (`√kath`,`kath`,кой); none — (`√ad`,`ad`,есть).
  Plus unit tests: `skeleton("akkh") == ["K"]` (collapse + aspirate skip); `skeleton("bhātar") == ["B","T"]`;
  `skeleton("i") == []`; `sources("√kus 2", "kuṣ √kus")` == `["kus", "kuṣ", "kus"]` (homonym number and `√`
  stripped; order kept).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_sound.py -v` passes; `uv run ruff check
  --fix`, `uv run ruff format`, `uv run pyright scripts/ru_cognate/ru_cognate_sound.py`, `uv run pyright
  --project /dev/null tests/scripts/ru_cognate/test_ru_cognate_sound.py`, `uv run --with pyrefly pyrefly check
  --min-severity warn` on both — clean.
- [x] 6.1y Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py`:
  (a) `VERIFY_RULES`: remove the `sound` label definition, `"sound"` from the reply schema, and the sound
  anchors (`есть has sound "none"…`, `вонь has sound "none"`); keep the meaning/form anchors (медведь far;
  √ādā/√dā 1 дать; прийти derivative; вонь meaning "drifted"). Drop `VERIFY_SOUND` from `_parse_labels`
  validation (a reply that still contains `sound` is accepted; the value is ignored).
  (b) In `apply_verify` and `apply_verify_pair`, after `_parse_labels`, set `entry["sound"] =
  sound_label(row["unit_key"], row["sanskrit"], entry["word"])` for every entry of every pass, then the
  existing `_outcome` / combination code runs unchanged. `_note` writes `sound <x> (code)`.
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_ai.py`: change the `verify_row` / `pair_row` helpers to
  `make_row("a", "proposed", ru_candidates=..., sanskrit="dvāra")` so `дверь` is code-`close`; tests that
  used `sound="weak"` / `sound="none"` instead use candidate words whose code label is weak (`ворота`) or none
  (`мама`), with the candidate list adjusted; `label()` no longer emits `sound`. Each existing behaviour stays
  covered (keep, weak→flag, drifted→flag, weak+drifted→drop, none→drop, far→drop, overflow, pass
  combinations). New tests: (1) a reply word labelled with `sound: "none"` by the model but code-`close` is
  kept (model sound ignored); (2) the verify prompt has no `"sound"` key in its schema and no `есть has sound`
  anchor; (3) `verifier_note` contains `sound close (code)`.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py
  tests/scripts/ru_cognate/test_ru_cognate_sound.py tests/scripts/ru_cognate/test_ru_cognate_ledger.py
  tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v` passes; gates (ruff check --fix, ruff format,
  pyright — `--project /dev/null` for tests — pyrefly `--min-severity warn`) clean on `ru_cognate_ai.py` and
  its test; `git diff --stat tools/` empty.
- [x] 6.1z Re-verify the 50 `verified`/`disputed` rows exactly as 6.1v (off-peak check; snapshot to
  `temp/ru_cognate_pilot/run_f.tsv`; reset; `verify --no-thinking --passes 2 --batch-size 5 --max-batches 10`,
  log `g1.log`; same failure handling). Then **STOP:** show the user a table of the 50 rows: unit | run F
  kept / flagged | run G kept / flagged; call out every kept word; check: √ad еда; √akkh око; √agg огонь;
  √is искать; √kās 2 кашель; √i 2 none; no ячмень, яд, язь, кон/чадо/щенок, кой/чей, чары kept; report √ādā
  (дар/дань expected kept by the meaning-label error — the user decides). Report kept/flagged word and row
  counts and per-request seconds. Record in `baseline.md` → `### 6.1x–6.1z: code-side sound (2026-11-17)`.
  Delete `temp/ru_cognate_pilot/`. Update `handoff.md`. Wait for "continue".
  → verify: only the 50 rows changed; counts `proposed 513, pending 997, none 47`, verified + disputed = 50;
  user said continue; `temp/ru_cognate_pilot` absent.
  **6.1z result 2026-11-17:** user chose a stricter pass combination (spec 7 amendment 2026-11-17 f),
  executed in 6.1za–6.1zc.

**6.1za–6.1zc: strict pass combination (spec 7 amendment 2026-11-17 f).** Files allowed to change:
`scripts/ru_cognate/ru_cognate_ai.py`, `tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
`shared_data/ru_cognate/ledger.tsv` (via the command below only), this thread's `plan.md`/`baseline.md`/
`handoff.md`; one scratch script under `temp/ru_cognate_pilot/` (deleted at 6.1zc). No AI calls, no `tools/`
edits, no DB writes, no commits.

- [x] 6.1za Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py`, `apply_verify_pair` only: when
  the two outcomes differ, the word's outcome is `"drop"` if either is `"drop"`, else `"flag"` (so keep needs
  keep in both). Equal outcomes and the `|| pass 2 differs:` note are unchanged. Update the docstring to
  "keep if both keep, drop if either drops, else flag".
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_ai.py` (replace, do not just delete):
  1. `test_pair_keep_flag_is_kept` → `test_pair_keep_flag_is_flagged`: `("", "дверь")`, status `disputed`,
     note still ends ` || pass 2 differs: дверь keep/flag`;
  2. `test_pair_keep_drop_is_kept` → `test_pair_keep_drop_is_dropped`: `("", "")`;
  3. `test_pair_drop_keep_is_kept` → `test_pair_drop_keep_is_dropped`: `("", "")`;
  4. `test_pair_flag_drop_is_flagged_only` → `test_pair_flag_drop_is_dropped`: `("", "")`;
  5. `test_run_batches_two_passes_asks_twice_and_combines_passes`: row `b` (keep/drop) now has
     `ru_final == ""` and `ru_flagged == ""`; row `a` still kept, row `c` still dropped;
  `test_pair_keep_keep_is_kept`, `test_pair_flag_flag_is_flagged`, `test_pair_drop_drop_…`,
  `test_pair_disagreement_is_noted`, `test_pair_fourth_kept_word_overflows_to_flagged` pass unedited.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py
  tests/scripts/ru_cognate/test_ru_cognate_sound.py tests/scripts/ru_cognate/test_ru_cognate_ledger.py
  tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v` passes; gates (ruff check --fix, ruff format,
  pyright — `--project /dev/null` for the test — pyrefly `--min-severity warn`) clean on both files;
  `git diff --stat tools/` empty.
- [x] 6.1zb Recompute the 50 `verified`/`disputed` rows offline. Copy the ledger to
  `temp/ru_cognate_pilot/ledger_before_f.tsv`. Scratch script `temp/ru_cognate_pilot/recombine.py`
  (one-sentence purpose docstring; imports `read_ledger`, `write_ledger`, `LEDGER_PATH` from
  `scripts.ru_cognate.ru_cognate_ledger` and `_outcome`, `_set_result` from
  `scripts.ru_cognate.ru_cognate_ai`): for each `verified`/`disputed` row, split `verifier_note` on
  ` || pass 2 differs: `; parse every word's labels from the main part with the regex
  `(?:^|; )(\S+) \[(\w+)/(\w+)/sound (\w+) \(code\)/meaning (\w+)\]: (.*?)(?=; \S+ \[|$)` into label dicts
  (`word, etymon, form, sound, meaning, note`); pass-1 outcome = `_outcome(labels)`; pass-2 outcome = the
  second value of `<word> <o1>/<o2>` from the differs part if listed, else the pass-1 outcome. **Assert** each
  listed `<o1>` equals the recomputed pass-1 outcome (else STOP and report — the note does not round-trip).
  Combine per amendment f and call `_set_result(row, labels, outcomes, row["verifier_note"])` (note kept
  verbatim). Write with `write_ledger`. Run with `uv run python temp/ru_cognate_pilot/recombine.py`.
  → verify: only `status`, `verifier_verdict`, `ru_final`, `ru_flagged` of those 50 rows changed (diff vs
  `ledger_before_f.tsv`); kept = √akkh око, √agg огонь, √ad еда, √is искать, √kās 2 кашель; flagged = √ādā дар,
  √ikkh око, √ad яд, √i 1 идти, √ud вода; counts `proposed 513, pending 997, none 47, verified 5, disputed 45`.
  A different result → STOP and report (do not adjust the rule).
- [x] 6.1zc Record in `baseline.md` → `### 6.1za–6.1zc: strict pass combination (2026-11-17)` (rule, kept and
  flagged lists, the учить/квас loss). Delete `temp/ru_cognate_pilot/`. Update `handoff.md` (next: 6.2).
  **STOP:** report to the user and wait for "continue".
  → verify: user said continue; `temp/ru_cognate_pilot` absent; `git status --short` shows no root-level files.
  **6.1zc result 2026-11-17:** user chose a validation run on 50 fresh roots + 50 fresh families (incl. all 13
  gold units) before the full verify — spec 7 amendment 2026-11-17 g. Executed in 6.1zd–6.1zf.

**6.1zd–6.1zf: validation run on 50 roots + 50 families (spec 7 amendment 2026-11-17 g).** Files allowed to
change: `scripts/ru_cognate/ru_cognate_ai.py`, `tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
`shared_data/ru_cognate/ledger.tsv` (via the AI run only), this thread's `plan.md`/`baseline.md`/`handoff.md`;
scratch only under `temp/ru_cognate_check/` (deleted at 6.1zf). No `tools/` edits, no DB writes, no commits.
Off-peak only (no `--allow-peak`).

- [x] 6.1zd Tests first, then code in `scripts/ru_cognate/ru_cognate_ai.py`:
  (a) `read_units(path: Path) -> set[str]`: read UTF-8, `strip()` each line, drop empty lines.
  (b) `run_batches(..., passes: int = 1, units: set[str] | None = None)`: if `units` is not None, before the
  first `_peak_gate`/`ask`: `unknown = units - {all ledger unit_keys}` → `pr.red` naming them, return 1
  (ledger untouched); `skipped = {listed keys whose status != wanted}` → `pr.yellow` naming them; the batch
  filter adds `r["unit_key"] in units`; if no listed row is eligible → `pr.yellow("nothing to do")`, return 0.
  `units=None` → current behaviour unchanged.
  (c) CLI `--units-file` (`type=Path`, default None, help "only these unit_keys, one per line"); `main`
  passes `read_units(args.units_file) if args.units_file else None`.
  Tests in `tests/scripts/ru_cognate/test_ru_cognate_ai.py` (reuse the `ledger` fixture, `FakeAsk`,
  `no_peak`, `verify_item`, `wrap`; each fails for a distinct reason):
  1. `read_units`: file `"√kus 2\n\n  b  \n"` → `{"√kus 2", "b"}`;
  2. verify with `units={"b"}` on 3 `proposed` rows: `FakeAsk` called once, the prompt contains `b` and not
     `a`/`c`; `a` and `c` stay `proposed`; `b` changed;
  3. `units={"b", "zzz"}` → returns 1, `FakeAsk.calls == []`, ledger file bytes identical before/after;
  4. `units={"a", "b"}` with `a` already `verified` → `a` untouched, `b` processed, return 0;
  5. `units={"a"}` with `a` `verified` → return 0, `FakeAsk.calls == []`;
  6. `units` given with `batch_size=1`: rows processed in ledger order, not set order (two listed rows →
     prompts in ledger order).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ai.py
  tests/scripts/ru_cognate/test_ru_cognate_sound.py tests/scripts/ru_cognate/test_ru_cognate_ledger.py
  tests/scripts/ru_cognate/test_ru_cognate_etyma.py -v` passes; gates (ruff check --fix, ruff format,
  pyright — `--project /dev/null` for the test — pyrefly `--min-severity warn`) clean on both files;
  `git diff --stat tools/` empty; `uv run python scripts/ru_cognate/ru_cognate_ai.py --help` shows
  `--units-file`.
- [x] 6.1ze Select and run. (1) Scratch `temp/ru_cognate_check/select.py` (one-sentence docstring) reads the
  ledger with `read_ledger` and writes `temp/ru_cognate_check/units.txt`: gold roots `√dvar`, `√budh`, `√ñā`;
  47 more from `random.Random(20261117).sample(sorted(other proposed root keys), 47)`; gold families `bhātar`,
  `nāma`, `nava1`, `ti`, `bhū`, `mātar`, `dhava`, `dvi`, `cha`, `aṭṭha`; 40 more from a NEW
  `random.Random(20261117).sample(sorted(other proposed family keys), 40)`. It asserts all 13 gold units are
  `proposed` and that the file has exactly 100 distinct keys (50 `root`, 50 `family`). Copy the ledger to
  `temp/ru_cognate_check/ledger_before.tsv`. Record the 100 keys in `baseline.md` (two lines: roots,
  families) so the set is reproducible after `temp/` is deleted.
  (2) Off-peak check (as 6.1j; `True` → STOP and tell the user when off-peak starts).
  (3) `uv run python scripts/ru_cognate/ru_cognate_ai.py verify --no-thinking --passes 2 --batch-size 5
  --units-file temp/ru_cognate_check/units.txt 2>&1 | tee temp/ru_cognate_check/v1.log` (20 batches,
  ~40 requests, ~10 min). If listed rows are still `proposed` afterwards, run the same command once more
  (log `v2.log`; it only picks the leftovers); still failing → leave them and report. Any
  `finish_reason=length` or exit 2 → STOP and report.
  → verify: only the 100 listed rows changed (diff vs `ledger_before.tsv`, columns `status`,
  `verifier_verdict`, `verifier_note`, `ru_final`, `ru_flagged`); counts `proposed 413` (513 − 100, plus any
  leftovers reported), `pending 997`, `none 47`, verified + disputed = 150.
- [x] 6.1zf **STOP:** show the user:
  (a) gold table (13 units): unit | expected word | result (kept / flagged / dropped / not a candidate) | that
  word's labels from `verifier_note` (etymon/form/sound (code)/meaning + pass-2 difference). Expected per
  spec amendment g.
  (b) roots (50) and families (50) separately: rows with kept words (`unit | member meaning (first member,
  short) | kept | flagged`), then rows with only flagged words; counts of verified / disputed rows and kept /
  flagged words per group; words with `pass 2 differs`.
  (c) dropped words whose labels were etymon `same` + form `base` (the near misses), per group, with labels —
  so the user sees what the strict rule throws away.
  (d) per-request seconds (min/median/max), problems, leftovers.
  (e) a recommendation: proceed to 6.2/6.3 unchanged, or a specific rule change (if a change, say whether it
  can be recomputed offline from the notes).
  Record (a), the counts from (b), and the timing in `baseline.md` → `### 6.1zd–6.1zf: validation run, 50 roots +
  50 families (2026-11-17)`. Delete `temp/ru_cognate_check/`. Update `handoff.md`. Wait for the user's decision.
  → verify: user decided; `temp/ru_cognate_check` absent; `git status --short` shows no root-level files.
- [x] 6.2 (propose done 2026-11-17: 1 `pending` left, `parā`, see baseline.md → 6.2) Run `propose` until no `pending` rows remain (resume across sessions; record each session's
  batches and totals in `baseline.md` → `## AI runs`).
  → verify: `pending` count = 0 (count of the `status` column).
- [x] 6.3 Run `verify --no-thinking --passes 2 --batch-size 5` until no `proposed` rows remain (user choice
  at 6.1t; spec 7 amendments 2026-11-17 a–g; failure handling as 6.1s; the 100 validation rows are already
  done). Off-peak only.
  → verify: `proposed` count = 0; every `verified`/`disputed` row has `verifier_verdict` and `verifier_note`.
- [x] 6.4 Phase check → verify: gold-set and sheet tables in `baseline.md` updated with post-AI results; no
  loan (`карма|будда|нирвана|шаман`) in any `ru_final`.

## Phase 7 — User review
- [ ] 7.1 **STOP: ask the user to review `shared_data/ru_cognate/ledger.tsv`** — set `decision` `y`/`n` on
  `verified` and `disputed` rows, edit `ru_final` where needed; move any `ru_flagged` word the user accepts
  into `ru_final` (flagged words are never written unless moved). Wait for confirmation.
  **Amended 2026-11-18 (spec 10, review sentinel):** ledger pre-filled — every verified/disputed row has
  `decision = y`, rows without a kept word have `ru_final = non` (= no word; `final_words()` in
  `ru_cognate_ledger.py`). The user changes `y` → `n` to reject and edits `ru_final` to correct.
  → verify: every verified/disputed row has `decision` `y` or `n`; every row with words (`final_words`) passes the
  Cyrillic-only check; `ru_final` is either `non`/empty or all-Cyrillic words (anything else is reported, not
  fixed); `y` on a no-word row is only reported as a warning.

## Phase 8 — Write to the DB (`scripts/ru_cognate/ru_cognate_write.py`)
- [ ] 8.1 Tests first, then code per spec 11 (in-memory SQLite with `DpdHeadword` / `Russian` rows).
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_write.py -v` passes: dry-run writes
  nothing; existing `ru_cognate` kept; missing `russian` row skipped and reported; a Latin value aborts
  before any write; second apply writes 0; `undo.tsv` lines match the changes; only `decision = y` units
  written.
- [ ] 8.2 Phase check → verify: quality gates clean on module and test.
- [ ] 8.3 Read the `db/backup_tsv/backup_dps.py` entrypoint, state its side effects, run it; run
  `ru_cognate_write.py` (dry-run) and show its totals. **STOP: ask the user for the go-ahead.**
  → verify: backup ran without error; dry-run totals reported; user said go.
- [ ] 8.4 Run `ru_cognate_write.py --apply`, then `backup_dps.py` again.
  → verify: `sqlite3 dpd.db "select count(*) from russian where ru_cognate != ''"` = 3 + "would write";
  `sqlite3 dpd.db "select ru_cognate from russian where id in (34348, 34349, 78698)"` = `дверь` ×3; second
  `--apply` reports 0 writes; `undo.tsv` row count = writes.

## Phase 9 — Translate-skill integration
- [ ] 9.0 **Precondition:** thread `20261116_translate-skill-overhaul` is finalized. If
  `kamma/threads/20261116_translate-skill-overhaul/` still exists or `git status --short kamma/translate`
  is not clean, **STOP and ask the user.**
  → verify: folder absent and `kamma/translate` clean, or user instruction recorded here.
- [ ] 9.1 Tests first, then code: `ru_cognate_ledger.py --add-new` (spec 12) — appends missing units as
  `pending`, existing rows byte-identical, no dumps required.
  → verify: `uv run pytest tests/scripts/ru_cognate/test_ru_cognate_ledger.py -v` passes: a new root → 1
  new `pending` row; existing rows unchanged; a second run adds 0.
- [ ] 9.2 Add "Op 7 — Cognates for new words" to `kamma/translate/pipeline.md` (menu entry + procedure:
  `--add-new` → `propose` → `verify`, off-peak → STOP for user review → backup → dry-run → STOP for
  go-ahead → `--apply`). Add one line about it to the descriptions in `.claude/commands/translate.md` and
  `.agents/skills/translate/SKILL.md`.
  → verify: `pipeline.md` menu lists Op 7; every command in Op 7 matches the scripts' `--help` output.
- [ ] 9.3 Phase check → verify: quality gates clean on `ru_cognate_ledger.py` and its test.

## Phase 10 — Registration and close-out
- [ ] 10.1 Write `scripts/ru_cognate/README.md` (purpose, `curl` lines, commands, ledger columns, statuses,
  review protocol, Op 7 pointer). Add `scripts/ru_cognate/`, `shared_data/ru_cognate/`,
  `tests/scripts/ru_cognate/` to `unique_paths` in `kamma/upstream_sync/registry.json`.
  → verify: `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- [ ] 10.2 Final gates: all 4 test files pass (each by path); linters clean on every new or touched `.py`;
  `temp/ru_cognate/` absent; `git status --short` shows no scratch; draft commit message
  `#10 feat(ru-cognate): fill russian.ru_cognate from Wiktionary join + verified AI cognates`
  (Phase 9 may be committed separately if the user prefers).
  → verify: all commands clean.
