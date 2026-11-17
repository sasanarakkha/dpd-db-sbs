# Handoff — 20261116_ru-cognate (issue #10)

## UPDATE 2026-11-18 (LATEST) — waiting for the user's ledger review (plan 7.1)

### State
- Phases 1–6 done (6.1zf, 6.2, 6.3, 6.4 all `[x]`). Phase 7.1 is the open STOP: the user is reviewing
  `shared_data/ru_cognate/ledger.tsv` and will continue in a NEW session after approving everything.
- Ledger (1,607 rows): verified 126, disputed 529, none 951, pending 1 (`parā`: model gave prefix `пере-`, rejected
  by word validation twice; left alone — user may mark it `none` or ignore), proposed 0.
- The 655 verified/disputed rows have `decision = yn` (pre-filled so the user only deletes `y` or `n`). `none`/`pending`
  rows have an empty `decision` on purpose. A row still saying `yn` = undecided.
- Post-AI quality (baseline.md → 6.3, 6.4): 126 rows have kept words, 153 rows flagged words (110 flag-only); no
  loans in `ru_final`. Gold 10/13 in `ru_final` (cha → шестой only, add `шесть` by hand; nāma `имя` and aṭṭha `восемь`
  only flagged, code sound `weak`). Sheet pairs: 7 kept, 3 flagged only.
- No DB writes have happened. `dpd.db` untouched. Nothing is committed (git shows the whole thread as untracked:
  `kamma/threads/20261116_ru-cognate/`, `scripts/ru_cognate/`, `shared_data/ru_cognate/`, `tests/scripts/ru_cognate/`;
  `misc/pat-bi/` is NOT this thread's — report only).

### What the user does
(Column order changed 2026-11-18: the last three columns are now `ru_flagged`, `ru_final`, `decision` — the user edits only `ru_final` and `decision`; `COLUMNS` in `ru_cognate_ledger.py` and spec 11 updated, ledger rewritten with identical data. Uncommitted.)
For each verified/disputed row: delete `y` or `n` from `decision`; edit `ru_final` where needed; move any accepted
`ru_flagged` word into `ru_final` (flagged words are never written unless moved). Every `y` row needs a non-empty
`ru_final` that passes the Cyrillic-only check.

### Next session (`/kamma:2-do 20261116_ru-cognate`)
1. 7.1 verify: no verified/disputed row has `decision` other than `y`/`n` (no `yn`, no empty); every `y` row has a
   non-empty Cyrillic `ru_final`. Do not fix silently — report problems to the user. Mark 7.1 `[x]`.
2. Phase 8: 8.1 tests first, then `scripts/ru_cognate/ru_cognate_write.py` per spec 11 (in-memory SQLite);
   8.2 gates; 8.3 read `db/backup_tsv/backup_dps.py`, state side effects, run it, dry-run the writer, **STOP for the
   user's go-ahead**; 8.4 `--apply`, backup again, verify counts (the 3 existing `дверь` rows unchanged).
3. Phase 9 needs thread `20261116_translate-skill-overhaul` finalized first (task 9.0 precondition). Phase 10:
   README, registry `unique_paths`, `validate_registry.py`, final gates, draft commit message in plan 10.2.

### Standing rules
Recommendation inline, never ask to switch models; targeted pytest file paths only (never a bare full-suite run);
agent runs no git; no `tools/` edits (`git diff --stat tools/` empty); off-peak only for any AI call (no
`--allow-peak`); pre-completion gates on every touched file (ruff check --fix, ruff format, pyright —
`--project /dev/null` for tests — pyrefly `--min-severity warn`); `tests/scripts/ru_cognate/` has 4 files, 160 tests pass.

### Files touched this thread (all uncommitted)
`scripts/ru_cognate/{ru_cognate_etyma,ru_cognate_ledger,ru_cognate_sound,ru_cognate_ai}.py`, the 4 test files in
`tests/scripts/ru_cognate/`, `shared_data/ru_cognate/ledger.tsv` (+ `sheet_snapshot.csv`), thread files. `temp/` clean.

### Failed attempts / notes
Strict pass combination (keep needs keep in both passes) loses some true cognates: √thu 1 стоять/стать/ставить,
ahaṃ я, iti и/он/их (code sound `none`), √gas горло/жерло — visible in `verifier_note`; user chose to leave them for
review. An optional looser rule (flag instead of drop when etymon is `same` in both passes) is recomputable offline
from the notes.

(Older updates below.)

## UPDATE 2026-11-17 (latest, after 6.2 propose)
6.2 `propose` ran: 40 batches, 996 rows changed. Ledger: pending 1, none 951, proposed 505, verified 37, disputed 113.
The 1 leftover is `parā` (model gave prefix `пере-`, rejected by `parse_words` twice) — decide: leave `pending`, set
`none` by hand, or ignore. Next: 6.3 `verify --no-thinking --passes 2 --batch-size 5` on the 505 `proposed` rows
(~100 batches × 2 requests × ~16 s ≈ 55 min, off-peak only; resume by re-running). Uncommitted: ai.py, its test,
ledger.tsv, thread files. `temp/ru_cognate_run` deleted.

(Older updates below.)

## UPDATE 2026-11-17 (latest) — validation run done (6.1zd, 6.1ze); 6.1zf waiting for the user's decision
`--units-file` added to `ru_cognate_ai.py` (7 new tests, 160 pass across the 4 test files; ruff, pyright, pyrefly clean).
Ran `verify --no-thinking --passes 2 --batch-size 5 --units-file` off-peak on 100 fresh units (50 roots + 50
families, incl. all 13 gold; seed 20261117; key list in `baseline.md` → `### 6.1zd–6.1zf`). 21 batches, 42 requests
(4.4 / 16.1 / 27.2 s min / median / max); no `finish_reason=length`, no exit 2. Only the 100 listed rows changed.
Ledger: proposed 413, pending 997, none 47, verified 36, disputed 113. No DB writes. Nothing committed.

**Results**
- Gold (13): all as spec amendment g expected. Kept дверь, бдеть/бодрый/будить, знать, брат, новый, три, бровь,
  мать, вдова, два, шестой (cha; no шесть candidate = known join gap). Flagged only (code sound `weak`):
  имя (nāma), восемь (aṭṭha). Also flagged: двор, знамя.
- Roots (50): verified 17 / disputed 33; kept words 23 (17 rows); flagged words 21; 4 flag-only rows
  (√ghaṭ 1, √bhaj 2, √han, √mih 1); 14 rows with `pass 2 differs`.
- Families (50): verified 15 / disputed 35; kept words 15 (15 rows); flagged words 15; 6 flag-only rows
  (nāma, aṭṭha, hima, miñja, loha, loṇa); 13 rows with `pass 2 differs`.
- Near misses (etymon same + form base, dropped): mostly meaning far/drifted or sound weak. Likely real cognates
  lost: √thu 1 стоять/стать/ставить (pass disagreement), ahaṃ я and iti и/он/их (code sound `none`),
  √gas горло/жерло (meaning drifted).
- Recommendation given (confidence 7/10): proceed to 6.2/6.3 unchanged; strict rule held on all gold. Optional
  rule change (flag instead of drop when etymon `same` in both passes) is recomputable offline from
  `verifier_note`; sound `none` cases would need a threshold change in `ru_cognate_sound.py`. Leaning: leave
  for phase 7 review.

**Next decision (user):** proceed to 6.2 (`propose` for 997 pending, off-peak) then 6.3 (`verify --no-thinking
--passes 2 --batch-size 5`; the 100 validation rows are already done), or change the rule first. 6.1zf is `[~]`.
`temp/ru_cognate_check` deleted.

**Uncommitted, ready to commit:** `scripts/ru_cognate/ru_cognate_ai.py`, `tests/scripts/ru_cognate/test_ru_cognate_ai.py`,
`shared_data/ru_cognate/ledger.tsv`, thread files (plan/baseline/handoff).

## State (2026-11-17) — 6.1za–6.1zc DONE, waiting for the user's "continue"
- Strict pass combination implemented (spec 7 amendment f): keep needs keep in both passes, drop if either drops, else flag.
- 50 pilot rows recomputed offline. Ledger: proposed 513, pending 997, none 47, verified 5, disputed 45. No DB writes. Nothing committed.
- Kept: √akkh око; √agg огонь; √ad еда; √is искать; √kās 2 кашель. Flagged: √ad яд; √ādā дар; √i 1 идти; √ikkh око; √ud вода.
- Uncommitted, ready to commit: `scripts/ru_cognate/ru_cognate_ai.py`, `ru_cognate_ledger.py`, `ru_cognate_sound.py`,
  the 4 test files, `shared_data/ru_cognate/ledger.tsv`, thread files (153 tests pass, gates clean).
- Next: 6.2 `propose` for 997 pending (off-peak, no `--allow-peak`), then 6.3
  `verify --no-thinking --passes 2 --batch-size 5`.
- Standing rules: recommendation inline; never ask to switch models; targeted test paths only; agent runs no git; no `tools/` edits.

## Resume
`/kamma:2-do 20261116_ru-cognate` after "continue".

## Results of 6.1za–6.1zc (details in baseline.md → 6.1za–6.1zc)
- Rule: per word, keep only if both passes keep; drop if either drops; else flag. Code in `apply_verify_pair`; 153 tests pass (4 ru_cognate test files); ruff, pyright, pyrefly clean; `git diff --stat tools/` empty.
- 50 pilot rows recomputed offline from their notes (no AI calls; pass-1 outcomes round-trip asserted). Only `status`, `verifier_verdict`, `ru_final`, `ru_flagged` changed.
- Counts: proposed 513, pending 997, none 47, verified 5, disputed 45.
- Kept (5 rows): √akkh око; √agg огонь; √ad еда; √is искать; √kās 2 кашель.
- Flagged (5 rows, user decides at phase 7): √ad яд; √ādā дар; √i 1 идти; √ikkh око; √ud вода.
- Lost vs run G: учить (√uc) and квас (√kaṭh 2) flagged in run G, now dropped (passes disagreed); all other run G flagged words not listed above are dropped too.
- `temp/ru_cognate_pilot` deleted. 6.1zc is `[~]` until the user says "continue".
