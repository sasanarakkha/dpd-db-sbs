# spec.md — Populate `russian.ru_cognate` with Russian cognates

**Issue:** local issue #10 — https://github.com/sasanarakkha/dpd-db-sbs/issues/10 ("add ru_cognate to db")
**Background:** `kamma/drafts/20261113_ru-cognate/handoff.md` (planning notes; this spec supersedes its
thread split — the whole job is this one thread).

## Overview
Fill `russian.ru_cognate` with 1–3 Russian words that are **inherited** cognates of the Pāḷi word (same
Proto-Indo-European (PIE) etymon). Loans (`карма`, `будда`, `шаман`) and sound-alikes are not cognates.
Most Pāḷi words have none; "none" is a normal result. Today 3 rows are filled (`дверь` on `dvāra 1/2/4`).
Exporters, GUI, TPR and Anki already read the column — no display work.

A cognate belongs to an etymon, so the unit of work is a **root** or **word family**; one approved answer
per unit is copied to its headwords. Stages, all in this thread:
1. Deterministic Wiktionary join (no AI) → ledger + baseline.
2. AI proposals for unresolved units, then independent AI verification of every claim.
3. User review of the ledger.
4. Backup, dry-run, then write `ru_cognate` for approved units.
5. Add a "cognates for new words" operation to the translate skill.

## What it should do
1. **Units** (one ledger row each, from live `dpd.db`, read-only):
   - `root` — every `dpd_roots.root` (homonyms such as `√kus 1`/`√kus 2` stay separate). Sanskrit side:
     `sanskrit_root` split on whitespace, `√` stripped.
   - `family` — every distinct `family_word` of headwords with empty `root_key`. Sanskrit side: members'
     `sanskrit` split on `, `, values containing ` + ` or empty dropped. Pali side: members' `lemma_1`
     without the homonym number.
   - Any unit whose headwords carry `non_ia` → `status = none`, `verifier_note = non-IA`.
2. **Sheet.** The issue's Google Sheet is saved verbatim to `shared_data/ru_cognate/sheet_snapshot.csv`;
   the user then edits it (may remove rows). It is an evaluation set only — never sent to the AI and
   never written to the DB directly.
3. **Etymon index (kaikki.org Wiktionary JSONL: Sanskrit, Pali, Russian, Proto-Slavic)**, downloaded once
   to `temp/ru_cognate/` (scratch, deleted after the join run):
   - PIE key = normalised **term string** (`id` is ignored — inspection found it absent). Harvested from
     (i) `root` / `inh` / `inh+` / `der` templates whose source is `ine-pro` — term in arg 3, or arg 4
     when arg 3 is empty (Skt `बुध्`); a `root` template may list several terms (args 3, 4, …); and
     (ii) every `Proto-Indo-European *X` mention in `etymology_text` (many entries carry PIE only there:
     Skt `nava`, PSL `novъ`, `mati`, `trьje`). Normalisation, applied identically to every source: NFC,
     strip U+0300/U+0301, strip `*` and leading/trailing `-`. No ablaut or laryngeal folding (false joins).
   - Hops (one each, no chains): a Sanskrit lemma inherits the keys of the Sanskrit entry named in its
     `sa`→`sa` `root` template or its `etymon` template (`द्वार`→`द्वार्`); a Pāḷi entry inherits the keys of
     the Sanskrit entry named in its `pi`→`sa` `inh`/`der` template (matched on Devanagari `word`).
     Pāḷi-internal (`pi`→`pi`) and Sanskrit-internal roots are never keys themselves.
   - Homonymous Sanskrit entries (`kṛ`: `*kʷer-` and `*kreH-`) contribute the **union** of their keys; the
     verifier, not the join, removes wrong ones.
   - Sanskrit matched via its IAST `romanization` form; NFC + strip U+0300/U+0301 on **both** sides.
   - Russian → PIE directly or via `inh` → `sla-pro` → Proto-Slavic entry (match: strip `*` and accents
     from the template term; PSL `word` has neither). Russian entries with a non-inherited template (`bor`,
     `bor+`, `lbor`, `ubor`, `obor`, `learned borrowing`, `unadapted borrowing`, `calque`, `clq`, `pclq`,
     `translit`) are excluded. Stress marks stripped; `ё` kept.
   - The join is a **candidate generator, not a source of truth**: every join hit is verified by the AI
     (spec 7), and a miss falls to AI proposal (spec 6). Known misses after normalisation: `√budh`
     (Skt `*bʰúdʰs` vs RU `*bʰewdʰ-`); `√dvar` (DPD `sanskrit_root` `√dvṛ` has no Sanskrit entry; the
     `dvāra` headwords sit under this root, so дверь comes from the AI stage).
4. **Join** → `method = join`, `status = proposed`, `pie_root` (matched keys, `, `-joined), `pie_id` left
   empty, `ru_candidates` (dedup, shortest first, max 10, `, `-joined, lower case), `source` (entries used,
   `+N more` when capped). Miss → `pending`.
5. **Baseline** `baseline.md` (thread folder): coverage by unit type and source, Proto-Slavic hop share,
   gold set, sheet pairs reproduced, AI request estimate from the real `pending`/`proposed` counts.
6. **AI proposals** (`pending` rows) — batches of 25 units via `AIManager.request` with the
   `default_models` chain (`tools/ai_models.json`). Per unit the prompt gives: unit key, Pāḷi meaning,
   Sanskrit side, 3–5 member headwords with meanings, upstream English `cognate` if any. Rules in the
   prompt: "none" is expected; inherited only, loans are not cognates; sound resemblance is not evidence;
   no citable source → `unsure`. Output JSON per unit: `unit_key`, `pie_root`, `ru_candidates` (0–3, most
   recognisable first), `source`, `confidence` 1–10, `verdict` `cognate|none|unsure`.
   `cognate`/`unsure` → `status = proposed`, `method = agent`; `none` → `status = none`. `unsure` with no
   words → `status = none` (amended 2026-11-16 after the pilot: nothing to review, and leaving it `pending`
   re-asks it every run).
7. **AI verification** (every `proposed` row, join and agent) — batches via `AIManager.request(...,
   grounding=True)`, which only selects the `grounded_models` chain (`deepseek-v4-pro`); deepseek does no
   web search (`tools/ai_openai_compat.py:232`), so the verifier works from model knowledge plus the cited
   Wiktionary source, and nothing calls it "grounded" or "web-verified". The verifier sees only the claim (unit, Pāḷi/Sanskrit side, PIE root, Russian words, cited source), not
   the proposer's reasoning or confidence. Output: `verifier_verdict` `confirmed|rejected|cannot_verify`,
   one-line `verifier_note`, and `ru_final` = the confirmed words, 0–3, most recognisable first.
   `confirmed` → `verified`; otherwise → `disputed`. Nothing is dropped silently.
   Amended 2026-11-16 after the pilot (verifier confirmed mixed-root sets, e.g. `√as 1` → ещё, забыть): the
   verifier judges each word separately against a standard etymology, drops uncertain/different-root words,
   drops mere derivatives of a listed word, orders by recognisability, and names each kept word's PIE root
   in `verifier_note`. The 25 pilot rows are re-verified with these rules.
   Amended 2026-11-16 (user, after the 6.1c review): a confirmed word must also **sound recognisably
   similar** to the Pāḷi/Sanskrit word and have a **similar meaning to the member headwords that will
   receive the value** (not to the root's `root_meaning`: DPD files `aggi` "fire" under `√agg` "move
   crookedly", and огонь is right for those headwords). Same cognate, different meaning is dropped: `√ādā`
   "take" → no дать; `√dā 1` "give" → дать. So the verify prompt also lists the unit's member headwords
   (≤5, `lemma (pos) meaning`, the same list the propose prompt gets). Still no confidence or proposer
   reasoning. The 25 pilot rows are re-verified again.
   Amended 2026-11-16 (user, after 6.1f): "sounds similar" means the Russian word keeps the audible root
   consonant(s) of the Pāḷi word (`√ad` → еда, not есть). The verify reply puts `verifier_note` (one short
   sentence naming each kept word's PIE root) before `verifier_verdict` and `ru_final`, so the verdict is
   given after the reasoning; a pilot run showed notes arguing "keep" under a `rejected` verdict.
   Amended 2026-11-17 (user chose stabiliser option 2 after 6.1h): verify runs with DeepSeek **thinking
   enabled**. No upstream file is edited (`tools/ai_openai_compat.py`, `tools/ai_manager.py`,
   `tools/ai_models.json` stay unchanged): `AIManager.request(**kwargs)` forwards extra kwargs to
   `OpenAiCompatManager.request`, which applies them after the provider defaults (`payload.update(kwargs)`),
   so `ru_cognate_ai.py` passes `thinking={"type": "enabled"}` and `max_tokens=32768` on verify calls only
   (thinking tokens count against `max_tokens`; the default 8192 risks truncated JSON). Propose is unchanged
   (default chain, thinking off). Guard: these kwargs are DeepSeek-specific, so a verify call refuses to run
   (exit with a red message, no ledger change) if the `grounded_models` chain is empty or contains a
   non-`deepseek` provider. The request timeout comes from `ai_models.json` (150 s default) and cannot be
   overridden by the caller, so verify runs use `--batch-size 10` (CLI default stays 25).
   Amended 2026-11-17 b (user, after the 6.1k review of run C: едкий and расти wrongly kept; вонь does not
   sound like an/āna): the verifier no longer picks the final set. It labels **every candidate word**
   separately — `note` (written first), `etymon` `same|different|loan|uncertain`, `form`
   `base|derivative`, `sound` `close|weak|none` (whole word recognisably like the Pāḷi/Sanskrit word),
   `meaning` `close|drifted|far` (against the member headwords) — words listed most recognisable first.
   Code applies the rule: keep = same + base + sound close + meaning close (first 3 → `ru_final`); flag =
   same + base + not keep + sound not none + meaning not far → new ledger column `ru_flagged`, decided by
   the user at review and never written unless moved into `ru_final`; everything else dropped.
   `verifier_verdict` is derived (`confirmed` iff `ru_final` non-empty); `verifier_note` keeps every word's
   labels and note as the audit trail. Thinking stays on; verify runs use `--batch-size 5` (batch 10
   exhausted the 32k token budget in 6.1j). Tested on the 25 pilot rows twice (stability) plus 25 held-out
   rows before the full run.
   Amended 2026-11-17 c (user, after D1: thinking-on batches of 5 take 200–460 s and ~1 in 5 hits
   `finish_reason=length` → ~10 h for the full run): (i) **candidate cleanup in code**, before any AI call:
   drop affixes (word starts or ends with `-`; an internal hyphen such as `кое-что` stays), drop duplicates
   after accent strip + lower case, and for **root units only** drop Russian closed-class words (list
   `CLOSED_CLASS_RU` in `ru_cognate_ledger.py`; DPD roots are verbal, pronoun/particle cognates belong to
   family units). Applied in `join_units` (before the 10-candidate cap) and once to the live ledger's
   `proposed` rows. Measured on the ledger before cleaning: 2,728 candidate words → 2,579 (88 affixes,
   61 closed-class), no row emptied — a small cut; the large junk sets (e.g. √as 1–4 / √ās
   добыча, забыть, забавный) need a join-level key fix that requires the dumps and is deferred.
   (ii) **thinking-off two-pass verify as an option** (`--no-thinking --passes 2`): the same prompt is
   sent twice with thinking disabled and the provider's default `max_tokens`; per word, keep = kept in both
   passes, drop = dropped in both, everything else → `ru_flagged`. A row changes only when both passes give
   valid labels. Thinking-on single pass stays the default until the pilot (6.1s) decides which mode 6.3 uses.
   Amended 2026-11-17 d (user, after pilot E: 0 of 50 rows kept — pass 1 kept око, огонь, еда, искать,
   кашель and pass 2 downgraded each; 37 flagged words, mostly junk): 6.3 runs **thinking-off two-pass**
   (`--no-thinking --passes 2 --batch-size 5`). (i) **Pass combination:** keep = `keep` in at least one
   pass; drop = `drop` in both; everything else → `ru_flagged`. (ii) **Flag rule** (per pass, in
   `_outcome`, so it also applies to single-pass verify): flag = same + base + not keep + sound ≠ none +
   meaning ≠ far + (sound `close` or meaning `close`); a word with sound `weak` AND meaning `drifted` is
   dropped. The keep rule is unchanged. Measured offline on the 50 pilot rows (pass-1 labels): flagged 37 →
   17 words; √aṅg угол is among those dropped. The 50 pilot + held-out rows are re-verified with the new
   rules (pass-2 labels of agreeing words are not stored, so they cannot be re-derived from the notes).
   Amended 2026-11-17 e (user chose option B after run F: the model's `sound` label flips between runs for
   the same word — око, огонь close in E, weak in F; кашель close/weak between passes): **`sound` is
   computed in code, not by the model.** The verify prompt and reply schema drop `sound` (and the sound
   anchors: есть, вонь); the model labels only `etymon`, `form`, `meaning`. New pure module
   `scripts/ru_cognate/ru_cognate_sound.py`, `sound_label(unit_key, sanskrit, word) -> "close"|"weak"|"none"`:
   - Sources: `unit_key` (strip `√` and a trailing homonym number) plus every value of the ledger `sanskrit`
     column (split on `, `, ` < `, whitespace; strip `√`). The word's label is the best over all sources
     (close > weak > none).
   - Source skeleton: IAST letters mapped to classes — k c → K; g j h → G; ś ṣ s → S; t ṭ → T; d ḍ → D;
     n ṇ ñ ṅ ṃ → N; p → P; b → B; m → M; r ṛ l ḷ → R; v → V; vowels and y ignored; an `h` right after a
     consonant letter (aspirate) ignored; repeated classes collapsed (`akkh` → K); first 2 classes kept.
   - Russian side: its consonant letters (б в г д ж з к л м н п р с т ф х ц ч ш щ) in order. Class → Russian:
     K к ч ц; G г ж з; S с ш х; T т; D д; N н; P п; B б; M м; R р л; V в.
   - `close`: the word's first consonant is in class 1 and (if there is a class 2) a later consonant is in
     class 2. `weak`: not close, but some Russian consonant is in one of the classes; also every source
     with an empty skeleton (vowel-only roots, `√i`). `none`: otherwise. No prothesis rule (`в` before a
     vowel-initial source is not skipped), so вода, вонь, восемь are `weak` — the user's вонь decision holds.
   - Prototype results (2026-11-17): close — огонь, око, еда, искать, кашель, брат, мать, два, три, новый,
     дверь, будить, знать (via `jñā`), бровь (via `bhrū`), шесть (via `ṣaṣ`), вдова; weak — вода, вонь,
     идти, восемь, имя, медведь, кой; none — есть.
   `apply_verify` / `apply_verify_pair` set each word's `sound` from `sound_label` before `_outcome`; keep,
   flag and pass-combination rules are unchanged (amendment d). `verifier_note` writes `sound <x> (code)`.
   Offline estimate on run F's 50 rows (pass-1 model labels + code sound): kept око, огонь, искать, кашель,
   кашлять — but also √ādā дар, дань, дарить, даровать, because the model labelled their meaning `close`
   (take ≠ give); the user decides those at review. еда was kept only when the model's `form` label said
   `base`. The 50 rows are re-verified with the new prompt.
   Amended 2026-11-17 f (user chose option B after run G): with `sound` in code, the lenient pass
   combination of amendment d mostly let noise through (10 of 16 flagged words were one-pass drop / one-pass
   flag; дать was drop/keep). **New pass combination:** keep = `keep` in both passes; drop = `drop` in
   either pass; everything else (keep/flag, flag/flag) → `ru_flagged`. The per-pass `_outcome` rule (keep,
   tighter flag rule, code-side sound) is unchanged. Recomputed exactly on run G (per-pass outcomes from the
   notes): kept око (√akkh), огонь, еда, искать, кашель (√kās 2); flagged дар (√ādā), око (√ikkh), яд, идти,
   вода; known loss: учить, квас (one pass dropped each). The 50 rows are recomputed from their stored
   `verifier_note` without AI calls (labels and code sound of pass 1 are in the note; words whose pass
   outcomes differ are listed after `|| pass 2 differs:`).
   Amended 2026-11-17 g (user, after 6.1zc: the rules were tuned on 50 root rows only; families — where
   most gold cognates sit — were never verified): **validation run on fresh units before the full verify.**
   `ru_cognate_ai.py` gains `--units-file PATH` (both modes): a UTF-8 file, one `unit_key` per line,
   whitespace stripped on every line, blank lines ignored; the run then takes only listed rows (still
   status-filtered, still in ledger order). Before any AI call or off-peak gate: a listed key not in the
   ledger → red message naming it, exit 1, ledger unchanged; a listed key whose row is not in the mode's
   status → yellow warning naming it, skipped; nothing eligible → yellow "nothing to do", exit 0. Without the
   flag behaviour is unchanged. Validation set (100 `proposed` units, never in any pilot): 50 roots = the 3
   gold roots (`√dvar`, `√budh`, `√ñā`) + 47 drawn with `random.Random(20261117).sample` from the other
   `proposed` roots sorted by `unit_key`; 50 families = the 10 gold families (`bhātar`, `nāma`, `nava1`,
   `ti`, `bhū`, `mātar`, `dhava`, `dvi`, `cha`, `aṭṭha`) + 40 drawn the same way from the other `proposed`
   families. Mode as 6.3 (`--no-thinking --passes 2 --batch-size 5`, off-peak). The 100 rows stay verified
   (real progress). Expected gold results: kept дверь, будить, знать, брат, новый, три, бровь, мать, вдова,
   два; имя and восемь at best flagged (code sound `weak`); cha has no шесть candidate (only шестой — known
   join miss).
8. **Response handling.** An unparseable response, or items that fail validation (unknown `unit_key`, bad
   verdict, >3 words, a word that is not Cyrillic after stress strip), leave those rows unchanged and are
   reported. A batch with no content stops the run (exit 2). The ledger is rewritten atomically (temp file
   + replace) after every batch, so any interruption is resumable.
9. **Off-peak gate.** Every AI run imports `require_offpeak(allow_peak)` from
   `kamma/translate/scripts/offpeak.py` (imported, never copied) and calls it before **each** batch, as
   `batch_runner.py` does: first batch blocked → exit 1; peak starting mid-run → print
   "peak hours started — stopping", exit 0; `--allow-peak` bypasses peak, never a missing `CN_HOLIDAYS` year.
10. **Review.** The user sets `decision` = `y`/`n` on `verified` and `disputed` rows; `ru_final` may be
    hand-edited; `ru_flagged` words are moved into `ru_final` only by the user. Only `decision = y` rows are written.
    Amended 2026-11-18 (user): **review sentinel.** `ru_final` = `non` (case-insensitive, or empty) means "no Russian
    word"; `NO_VALUE` and `final_words(row)` in `ru_cognate_ledger.py` are the single definition. The ledger is
    pre-filled: every verified/disputed row has `decision = y` (the user changes it to `n` to reject), and a row
    with no kept word has `ru_final = non`. Rules: a row with no words is never written, whatever `decision` says
    (`y` on it is a warning, not an error); a row with words is written only with `decision = y`; any `ru_final`
    that is neither the sentinel nor all Cyrillic words is an error (the review check and the writer both fail).
    `non` is Latin, so it can never pass as a Russian word.
11. **Write** `scripts/ru_cognate/ru_cognate_write.py` — dry-run by default, `--apply` to write:
    - Targets: `root` unit → headwords with that `root_key`; `family` unit → headwords with empty
      `root_key` and that `family_word`.
    - Never overwrites a non-empty `ru_cognate` (the `dvāra` rows; manual entries = per-headword override).
    - Headword without a `russian` row → skipped and reported (row not created).
    - Every value validated against `AllowableCharacters.ru_meaning_allowed`
      (`db_tests/single/sbs_test_allowable_characters.py`); any failure aborts before any write.
    - Updates only `Russian.ru_cognate` (single column, no `INSERT OR REPLACE`); appends `id, old, new` to
      `shared_data/ru_cognate/undo.tsv`; marks units `written`; a second run writes nothing.
    - Dry-run prints: would write / already set / no russian row / invalid.
    - Run only after a fresh `uv run python3 db/backup_tsv/backup_dps.py` and the user's explicit go-ahead.
12. **New words (translate skill).** `ru_cognate_ledger.py --add-new` appends units missing from the
    ledger as `pending` (no dumps, no join) and never changes existing rows. New headwords of an already
    approved unit need no AI: re-running `ru_cognate_write.py` fills them. `kamma/translate/pipeline.md`
    gets "Op 7 — Cognates for new words": `--add-new` → `propose` → `verify` (off-peak) → user review →
    backup → dry-run → go-ahead → `--apply`.

## Ledger
`shared_data/ru_cognate/ledger.tsv` (tracked), one row per unit, never deleted. Columns, in order:
`unit_type, unit_key, pali_meaning, sanskrit, headword_count, en_cognate, pie_root, pie_id, ru_candidates,
source, method, confidence, status, verifier_verdict, verifier_note, ru_flagged, ru_final, decision` (amended 2026-11-18, user: the two review columns `ru_final` and `decision` come last so only those are edited; `ru_flagged` sits just before them for reference).
- `pie_id` is kept for column stability but stays empty (no `id` in the dumps).
- `method`: `join|agent|manual`.
- `status`: `pending → proposed → verified|disputed → written`, or `none`.
- The full join runs once and refuses to start if the ledger exists; only `--add-new` touches an existing
  ledger. To redo a unit, edit its row back to `pending` by hand.

## Value format
Russian words only, lower case, separated by `, `, no stress marks, `ё` kept, 1–3 words, most
recognisable first (the GUI tooltip's intent: a word the reader recognises).

## Assumptions & uncertainties
- **Verified 2026-11-16 (live DB):** 89,789 headwords; 89,050 `russian` rows; 739 headwords without one;
  `ru_cognate` filled on 3 rows (`дверь`); 753 roots (743 with usable `sanskrit_root`); 854 rootless
  `family_word` values; 46,802 headwords with neither root nor family; 83 `non_ia`.
- **Verified:** gold words sit in families `mātar`, `pitar`, `bhātar`, `dvi` (Skt `dvi, dva`), `ti` (`tri`),
  `cha` (`ṣaḍ`), `aṭṭha` (`aṣṭan`), `nāma`; `bhamu` is in family `bhū` (Skt `bhrū`), `vidhavā` in `dhava`.
  Family keys are not lemmas; the Sanskrit side comes from members' `sanskrit` values, which are messy
  (`mātar, mātṛ`, inflected `mātaram`, compounds with ` + `).
- **Verified:** kaikki dumps return HTTP 200 — Sanskrit, Pali, Russian (948 MB), Proto-Slavic
  (`kaikki.org-dictionary-ProtoSlavic.jsonl`, 52 MB). Sanskrit headwords are Devanagari with an accented IAST
  `romanization` form (`buddhá`); Sanskrit-internal `root` templates look like `{"1":"sa","2":"sa","3":"बुध्"}`.
- **Verified:** the sheet has 58 rows mixing true cognates (Дверь, Мать, Нос), loans (Шаман), sound-alikes
  (пугало, Суп) and rows tagged `Жарг` / `Каз`. Many will not survive the inherited-only rule.
- **Verified:** `ru_cognate` is tested against `ru_meaning_allowed` (Cyrillic incl. `ё`, digits,
  punctuation; no Latin). `sbs_test_allowable_characters.py` `main` is hardcoded to the SBS table, so the
  write script checks the same character set itself.
- **Verified:** `AIManager.request` uses `default_models` when no provider is given and `grounded_models`
  when `grounding=True`; `tools/ai_json_parser.py` `JSONParser.extract_json_from_response` extracts JSON.
- **Verified:** `kamma/translate/scripts/offpeak.py` provides `require_offpeak` and `is_deepseek_peak`.
- **Settled in Phase 1 (`baseline.md` → `## Inspection`), spec amended 2026-11-16:** PIE spellings differ
  across languages for one etymon (дверь `*dʰwṓr`/`*dʰwer-`); `id` is absent; most PSL entries carry PIE
  only in `etymology_text`; `grounding=True` is chain selection only for deepseek.
- **Verified 2026-11-16 (probe on dumps, templates + `etymology_text`, normalised):** keys shared by the
  Sanskrit side and Russian side for дверь, знать, имя, вдова, мать, три, шесть; брат, бровь, новый need
  the PSL hop (RU entries have only `dercat`); `√dvar` misses at unit level (no Skt `dvṛ`); будить misses (`*bʰúdʰs` vs `*bʰewdʰ-`); два and восемь
  unconfirmed (Skt `dvi` gives `*dwi-` vs RU `*dwóh₁`; `aṣṭan` not probed).
- **Estimate (confidence 5/10):** ~100–120 AI requests in total; recomputed from the baseline.
- **Assumed intended:** in the RU GoldenDict template the English `cognate` shows only when `ru_cognate` is
  empty, so filled rows hide it.
- Thread `20261116_translate-skill-overhaul` is currently editing `kamma/translate/`; the translate-skill
  integration waits until it is finalized.

## Constraints
- New paths: `scripts/ru_cognate/` (code + README), `shared_data/ru_cognate/` (ledger, sheet snapshot,
  undo), `tests/scripts/ru_cognate/` (tests + JSONL fixtures). Registered in `registry.json`
  `unique_paths`; `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- Each `.py`: one-sentence purpose docstring, pathlib, modern type hints, `tools.printer`, paths anchored to
  `__file__`, no import-time side effects. No new dependencies. No download code (README holds `curl` lines).
- Tests: no network, no real AI (mocked `AIManager`), small real-line JSONL fixtures; real-dump tests
  marked `slow`; never `ruff format` JSON/JSONL fixtures; targeted pytest paths only.
- No DB write before the review is complete, a fresh backup, and the user's go-ahead. No commits by the agent;
  never stage `resources/`.
- AI batches are never re-run to fix formatting; ledger fixes are local text edits.
- Scratch only under `temp/ru_cognate/`, deleted when done; nothing in the repo root.

## How we'll know it's done
- Every root and family unit has a ledger row with a final state (`written`, `none`, or `decision = n`);
  no `pending`, `proposed`, or undecided `verified`/`disputed` rows remain.
- Gold set (13 pairs: `√dvar`→дверь, `bhātar`→брат, `nāma`→имя, `nava1`→новый (family key carries the homonym digit), `ti`→три, `bhamu`→бровь,
  `mātar`→мать, `vidhavā`→вдова, `dvi`→два, `cha`→шесть, `aṭṭha`→восемь, `√budh`→будить, `√ñā`→знать):
  each written, or its miss explained in `baseline.md`. No loan in any `ru_final`.
- `russian.ru_cognate` filled for the headwords of approved units; the 3 `дверь` rows unchanged; `undo.tsv`
  lists every change; a second `--apply` writes 0; `db/backup_tsv/russian.tsv` refreshed.
- `--add-new` tested; Op 7 documented in `kamma/translate/pipeline.md` with commands matching `--help`.
- All targeted tests pass; ruff/pyright/pyrefly clean on every new or touched `.py`; registry validates;
  no scratch left.

## What's not included
- `lemma` units (rootless, family-less headwords; mostly compounds/derivatives).
- Creating `russian` rows for the 739 headwords without one (reported, not created).
- Sending sheet rows to the AI; Vasmer or other etymological dictionaries.
- Any exporter or GUI change; the online export from the issue's last line.
