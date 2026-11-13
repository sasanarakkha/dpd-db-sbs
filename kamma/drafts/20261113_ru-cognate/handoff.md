# handoff.md — Populate `russian.ru_cognate` (Russian cognates for DPD words)

- **Origin:** planning conversation on 2026-11-13. No thread exists yet.
- **Status:** draft. Nothing below is implemented. No code, DB, registry or skill file was changed; only this file was created.
- **Next session:** turn this into a proper kamma thread with `/kamma:1-plan` (Thread 1 only — see "Suggested thread split").
- **Issue:** local issue #10 (https://github.com/sasanarakkha/dpd-db-sbs/issues/10), title "add ru_cognate to db". Reference it in spec, plan and commit messages.

Issue text, in full: a new column `ru_cognate` exists in the Russian table and needs to be populated; start from a Google Sheet (`https://docs.google.com/spreadsheets/d/11QwooFKuN7CY14BFHJ84lW7u_0XWcbIA1z00NX7OXfI`); later an exporter to something available online can be organised.

## Read this first (instructions for the planning agent)

- Markers: **(user)** = decided by the user, fixed. **(proposed)** = this session's recommendation; show it in the plan summary for approval, do not treat it as approved. **(verified)** = checked against the live DB or the live source on 2026-11-13. **(unverified)** = not checked; verify before relying on it.
- Counts were taken from the live `dpd.db` on 2026-11-13. Re-run the queries; do not copy the numbers into a spec as facts.
- Line numbers are from 2026-11-13. Re-locate by the quoted name, not by number.
- Present the spec/plan to the user as inline markdown for approval. Do not use a multiple-choice question tool for approval.
- Plan only Thread 1. Do not fold the later threads in.

## Goal

Fill `russian.ru_cognate` with Russian words that are true etymological cognates of the Pāḷi word, for every DPD word that has one — with a cited source for each claim, and human review before anything reaches the DB.

Most Pāḷi words have **no** Russian cognate. "No cognate" is a normal, expected result, not a failure.

## Decisions (user, 2026-11-13)

1. **What counts as a cognate:** inherited words only — the Pāḷi word and the Russian word descend from the same Proto-Indo-European (PIE) root. Loanwords are excluded (e.g. `карма`, `будда`, `нирвана` are loans from Indic, not cognates).
2. **How many per entry:** 1–3 Russian words, the most recognisable first.
3. **Granularity:** one value for the whole root / word family, with an optional per-headword override.
4. **Method:** deterministic join first, then agent gap-fill, then independent verification, then human review, then a propagation script. Not a per-headword LLM pass over the whole dictionary.
5. **Orchestration:** agent-driven, done part by part (batches), resumable.

## Core idea (why the work is small)

A cognate belongs to the etymon (the PIE root), not to the headword. So the unit of research is the root or word family — about 1,500–2,500 units — and a script copies the result to the headwords. The dictionary has ~89.8k headwords; researching each one separately would be slow, costly and inconsistent inside one family.

LLMs invent plausible etymologies. So the LLM must not be the source of truth: sources are Wiktionary data and an etymological dictionary; the agent proposes with a citation, a second agent checks the citation, the user approves.

## Verified facts — the database (2026-11-13)

Use `sqlite3 dpd.db` or `get_db_session`. `db/backup_tsv/` is a backup, not the source of truth.

| Fact | Value |
| --- | --- |
| `dpd_headwords` rows | 89,789 |
| `russian` rows | 89,050 |
| headwords with **no** `russian` row | 739 |
| `russian.ru_cognate` non-empty | 3 (all `дверь`, on `dvāra 1`, `dvāra 2`, `dvāra 4`, root `√dvar`) |
| `dpd_roots` rows | 753 |
| roots with a usable `sanskrit_root` (not `''`, not `'-'`) | 743 |
| headwords with `root_key` | 37,137 |
| headwords without `root_key` but with `family_word` | 5,850 (854 distinct `family_word` values) |
| headwords with neither `root_key` nor `family_word` | 46,802 (33,662 of them have `sanskrit`) |
| headwords with `sanskrit` filled | 75,730 (51,264 distinct values) |
| upstream English `cognate` filled | 564 headwords, 78 distinct values |
| — of which rooted | 340 headwords, 36 roots |
| — of which rootless | 224 headwords, 31 word families |
| headwords with `non_ia` filled | 83 |

Important consequences:

- **Roots alone are not enough.** Many of the best cognates sit on rootless words: `ti` (three), `nava` (new), `nāma` (name), `bhātar` (brother), `bhamu` (brow), plus two, six, eight, mother, father, widow, moon. They are grouped by `family_word` and carry a Sanskrit form in `sanskrit` (`tri`, `nāman`, `bhrātṛ`, `bhrū`).
- **`sanskrit` is not a clean lemma.** Samples: `akarkaśa (na + karkaśa)`, `na + (kaścid, kiṃcid)`, `akṛta + yūṣa`, `navaka +`, `na , a, an`. It needs parsing; values with ` + ` are compound analyses.
- **`dpd_roots.sanskrit_root` can hold several roots** separated by a space: `√argh √arh`, `√añc √ac`. Split on whitespace; each starts with `√`.
- **Upstream varies the value inside one family**: `√kus 1` has both `cuss` and `cussing`; `√div` has two different lists. This is the precedent for the per-headword override.
- **`non_ia`** marks non-Indo-Aryan words (loans from Dravidian, Munda, etc.). A unit whose words carry `non_ia` cannot have an inherited Russian cognate — set it to "none" without research.
- The 36 roots + 31 word families that already have an English `cognate` almost certainly have a PIE etymon. Use them as the regression set (see "Gold set").

### Where `ru_cognate` is already used (verified)

No exporter work is needed to display the value; these already read it:

- `db/models.py` — `ru_cognate: Mapped[str] = mapped_column(default="")` in the `Russian` model.
- `exporter/goldendict/ru_components/templates/dpd_headword_ru.jinja` — shows `d.ru.ru_cognate`; falls back to "English Cognate" (`d.i.cognate`) only when `ru_cognate` is empty (`{% elif %}`).
- `exporter/goldendict/sbs_templates/dpd_headword_sbs.jinja` and `exporter/webapp/sbs_templates/dpd_headword.html` — show both.
- `exporter/tpr/templates/tpr_headword_ru.jinja` — row label `Родствен.`.
- `scripts/export/dps_anki_updater.py` — `note["ru_cognate"] = str(i.ru.ru_cognate)`.
- `gui2/dps_field_mapping.py` — field `dps_ru_cognate`, tooltip "Russian word which close sounding".
- `db_tests/single/sbs_test_allowable_characters.py` — `("ru_cognate", ru_meaning_allowed)`.

Consequences:

- **Allowed characters.** `ru_cognate` is tested against `ru_meaning_allowed` (Cyrillic letters, digits and some punctuation — read the full list in that file). Latin letters and PIE notation such as `*dʰwer-` are probably not allowed **(unverified — read the list)**. So the DB value is plain Russian words; the PIE root and the source stay in the ledger file, not in the DB.
- **Stress marks.** Wiktionary Russian forms carry an acute accent (`буди́ть`). Strip U+0301 before storing. Decide how to treat `ё` and keep it consistent.
- **The GUI tooltip** shows the original intent: a Russian word the reader recognises by sound. This supports decision 2 — rank the most transparent word first (`дверь` for `dvāra`), not the most learned one.
- **Russian rows are saved by** `uv run python3 db/backup_tsv/backup_dps.py` (function `backup_ru`), into `db/backup_tsv/russian.tsv`.

## Verified facts — the Wiktionary dumps (2026-11-13)

kaikki.org publishes machine-readable English-Wiktionary extracts, one JSON object per line. These URLs returned HTTP 200:

| Language | URL | Size |
| --- | --- | --- |
| Russian | `https://kaikki.org/dictionary/Russian/kaikki.org-dictionary-Russian.jsonl` | 948 MB |
| Sanskrit | `https://kaikki.org/dictionary/Sanskrit/kaikki.org-dictionary-Sanskrit.jsonl` | 148 MB |
| Pali | `https://kaikki.org/dictionary/Pali/kaikki.org-dictionary-Pali.jsonl` | 37 MB |

Inspected: the whole Pali dump and the first 60 MB of the Russian dump. The Sanskrit dump was **not** inspected.

- Useful keys per entry: `word`, `pos`, `lang_code`, `etymology_text`, `etymology_templates`, `senses`. Entries without an etymology have no `etymology_templates` key.
- `etymology_templates` is a list of `{"name": ..., "args": {...}}`. The PIE root is given by the `root` template:
  - Pali `yotta`: `{"name": "root", "args": {"1": "pi", "2": "ine-pro", "3": "*yewg-"}}`
  - Russian `баять`: `{"name": "root", "args": {"1": "ru", "2": "ine-pro", "3": "*bʰeh₂-", "id": "speak"}}`
- **Gotcha 1 — the `root` template is also used for Pāḷi-internal roots**: `rosa` has `{"1": "pi", "2": "pi", "3": "rus"}`. Keep a `root` template only when `args["2"] == "ine-pro"`.
- **Gotcha 2 — homonymous PIE roots.** `*bʰeh₂-` exists as `id: "shine"` (`баской`) and `id: "speak"` (`баять`). The join key must be the pair (root, id), never the root string alone. A root may list several roots in `args["3"]`, `args["4"]`, …
- **Gotcha 3 — most Russian entries stop at Proto-Slavic.** In the 60 MB sample: 5,754 entries with an etymology; 682 mention PIE (`ine-pro`); 1,320 mention only Proto-Slavic (`sla-pro`). A direct Russian→PIE join therefore misses about two thirds. A second hop Russian → Proto-Slavic lemma → PIE is needed. Whether kaikki offers the Proto-Slavic reconstruction entries as a dump is **(unverified)**.
- **Gotcha 4 — Pali coverage is thin.** 10,706 Pali entries; 344 reference PIE at all; 242 have a `root` template. Only 3 Pali entries name a Slavic cognate directly (`jānāti` → Old Church Slavonic `знати`; `bujjhati` → Russian `буди́ть`). The Sanskrit dump should cover more, and the agent gap-fill stage will carry a large share of the work.
- Other template names seen: `inh`, `inh+` (inherited from), `der` (derived), `bor+` (borrowed — signals a loan, exclude), `cog` (cognate mention), `af`, `etymon`.

## Units of work

A **unit** is one etymological group that gets one researched answer. **(proposed)**

| Unit type | Key | Source of the Sanskrit side | Approx. count |
| --- | --- | --- | --- |
| `root` | `dpd_roots.root` (e.g. `√dvar`) | `dpd_roots.sanskrit_root` | 753 |
| `family` | `family_word` of rootless headwords (e.g. `bhātar`) | `sanskrit` of the family's headwords | 854 |
| `lemma` | cleaned Sanskrit lemma of a headword with no root and no family | `sanskrit` | to be measured |

- Process `root` and `family` units in full.
- For `lemma` units **(proposed)**: run only the free deterministic join, skip values containing ` + ` (compounds — their cognates belong to the components), and do not spend agent time on the misses. Most of the 46,802 rootless, family-less headwords are compounds or derivatives; measure before deciding more.
- Homonymous roots (`√acc 1`, `√acc 2`, `√kus 1`) are separate units — they can have different etymons.

## Pipeline

### Stage 0 — spike (measure before building)

Answer with numbers, in the thread's `baseline.md`:

1. How many `root` units get a PIE root from the Sanskrit dump via `sanskrit_root`? From the Pali dump via member headwords?
2. How many `family` units get one via `sanskrit`?
3. How many Russian entries reach PIE directly, and how many more through the Proto-Slavic hop? Is a Proto-Slavic dump available?
4. How does Wiktionary write Sanskrit roots and lemmas (Devanagari vs IAST, with or without `√`)? DPD stores IAST (`√akṣ`, `bhrātṛ`). The same normalisation must be applied to both sides of the join.
5. What does the Google Sheet from the issue contain? (Not read this session — see "Open questions".)

### Stage 1 — deterministic etymon table (no AI)

A script reads the three dumps and the DB and writes the ledger (below). Join: DPD unit → Sanskrit/Pali Wiktionary entry → (PIE root, id) → Russian entries with the same (PIE root, id), excluding entries whose etymology is a borrowing.

Every row produced here gets `method = join` and a source naming the Wiktionary entries used. Candidates are **proposals**, not approved values — they still go through verification and review.

### Stage 2 — agent gap-fill

For units the join did not resolve. One batch = about 25 units, one subagent, one self-contained prompt. Batch input per unit: unit key, Pāḷi root/lemma, meaning, Sanskrit root/lemma and meaning, 3–5 example headwords with meanings, the upstream English `cognate` when present.

Batch output per unit — strict, one TSV row:

- `pie_root` (with gloss) or empty
- `ru_candidates` — 0–3 Russian words, most recognisable first
- `source` — the exact entry cited (dictionary + headword, or Wiktionary page)
- `confidence` — 1–10
- `verdict` — `cognate` / `none` / `unsure`

Rules that must be in the batch prompt:

- "None" is the expected answer for most units. Never stretch to find a match.
- Inherited cognates only. A Russian word borrowed from Sanskrit, Greek, Latin, German, etc. is not a cognate.
- Sound resemblance is not evidence. A claim without a citable source is `unsure`, not `cognate`.
- No DB access, no file writes outside the batch's output file.

### Stage 3 — independent verification

A second agent receives only the claim (unit, PIE root, Russian words, cited source) — not the first agent's reasoning — and checks it against the cited source. Output: `confirmed` / `rejected` / `cannot_verify`, plus a one-line reason. Applies to Stage 1 rows too.

`rejected` and `cannot_verify` go to the review queue with both opinions visible; they are never silently dropped or silently accepted.

### Stage 4 — human review

The user reviews the ledger (a few hundred rows with a candidate). Protocol **(proposed)**: put `y` in `decision` to approve, `n` to reject; `ru_final` may be hand-edited. Only rows with `decision = y` are ever written to the DB.

### Stage 5 — propagation script

Writes `ru_final` to `russian.ru_cognate` for the headwords of each approved unit. Rules **(proposed)**:

- `root` unit → all headwords with that `root_key`. `family` unit → all rootless headwords with that `family_word`. `lemma` unit → headwords with that cleaned `sanskrit` lemma.
- **Never overwrite a non-empty `ru_cognate`** (the 3 `dvāra` rows today, and any future manual entry). A manual value is the per-headword override.
- A headword with no `russian` row (739 today): skip and report. Do not create the row — see "Open questions" 3.
- Idempotent: a second run changes nothing.
- Append `id, old, new` to an undo record as each row is written.
- Dry-run mode that prints totals (would write / already set / no russian row / skipped) and writes nothing.

## Ledger (state of the whole job)

One tracked TSV, one row per unit; it is the resumable state. **(proposed)** location: `shared_data/ru_cognate/ledger.tsv` (precedent: tracked working TSVs in `shared_data/pali_class/grammar/`, see `kamma/tech.md`). Columns, in order:

`unit_type`, `unit_key`, `pali_meaning`, `sanskrit`, `headword_count`, `en_cognate`, `pie_root`, `pie_id`, `ru_candidates`, `source`, `method`, `confidence`, `status`, `verifier_verdict`, `verifier_note`, `ru_final`, `decision`

- `method`: `join` / `agent` / `sheet` / `manual`.
- `status`: `pending` → `proposed` → `verified` → `approved` → `written`; or `none` (no cognate, with the reason in `verifier_note`).
- A batch takes the next N rows with `status = pending`. Rows are never deleted.

The dumps (1.1 GB) are scratch: download to `temp/ru_cognate/`, extract what is needed, delete. Do not commit them.

## Gold set (accuracy check before the full run)

Before trusting any stage, run it on units whose answer is known and report precision:

- Pairs that are standard, well-attested cognates: `√dvar`/`dvāra` → `дверь`; `bhātar` → `брат`; `nāma` → `имя`; `nava` → `новый`; `ti` → `три`; `bhamu` (Skt `bhrū`) → `бровь`; mother → `мать`; widow → `вдова`; two → `два`; six → `шесть`; eight → `восемь`; `√budh` (`bujjhati`) → `будить`; `√ñā` (`jānāti`) → `знать`.
- The 36 roots + 31 families with an upstream English `cognate`: each should resolve to a PIE root. A unit there that comes back `none` needs a second look.
- The Google Sheet rows, once readable.
- Add known negatives: units with `non_ia`, and a few roots with no Slavic reflex, to confirm the pipeline returns `none`.

## Suggested thread split

1. **Thread 1 — spike + deterministic join.** Stage 0 and Stage 1: download/parse script, unit builder, join, ledger writer, tests, `baseline.md` with coverage numbers. No AI, no DB writes. **Plan this one.**
2. **Thread 2 — agent gap-fill + verification** (Stages 2–3). A standing loop thread (`/kamma:loop`): each cycle takes the next batch from the ledger. Needs Thread 1's numbers to size it.
3. **Thread 3 — review + propagation** (Stages 4–5). Propagation script, data test, the DB write, backup.
4. **Later — the issue's last line**: an exporter "to something available online". Not specified; ask the user when the data exists.

### Thread 1 — notes for the spec

- **Files (proposed, all new):** a script folder for the job; the ledger at `shared_data/ru_cognate/ledger.tsv`; tests under `tests/`. Choose the script location by reading how existing local scripts are organised (`scripts/`, `kamma/translate/scripts/`) and get the user's approval.
- Each new `.py` starts with a one-sentence purpose docstring, uses `pathlib`, modern type hints, `tools/printer.py` for output, paths anchored to `__file__` or taken from `tools/paths_dps.py`. No downloads or directory creation at import time.
- New fork-local files must be registered in `kamma/upstream_sync/registry.json` (`unique_paths`), then `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` must pass. (`kamma/` itself is already listed, so this handoff file needs no entry.)
- Tests are zero-network: commit small fixture `.jsonl` files (a few dump lines each) under `tests/`; never parse the real dumps in a default test. A test that does must be marked `@pytest.mark.slow`. Never run `ruff format` on `.json` fixtures.
- Test cases worth having: the Pāḷi-internal `root` template is ignored; homonymous roots with different `id` do not join; a `bor+` Russian entry is excluded; several roots in `sanskrit_root` are split; stress marks are stripped; the same normalisation is applied to both sides of the join.

## Guardrails (project rules that apply to every task)

- No DB write before a fresh `uv run python3 db/backup_tsv/backup_dps.py` and the user's explicit go-ahead. Threads 1 and 2 write nothing to the DB.
- Never `INSERT OR REPLACE`; update the single column.
- `dpd.db` is in WAL mode: do not use the file's timestamp to tell whether it changed.
- Do not commit. Prepare a draft commit message. Never stage `resources/` submodule changes.
- Never run `git stash`, `git checkout -- <path>`, `git restore` or `git reset --hard` (shared working tree).
- Tests: targeted files only, never bare `uv run pytest`.
- Every touched `.py` must pass: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>` (for files under `tests/`: `uv run pyright --project /dev/null <file>`), `uv run --with pyrefly pyrefly check --min-severity warn <file>`.
- Scratch only under `temp/<task>/`, deleted before the final report. Nothing new in the repo root.
- `uv run python scripts/foo.py` — never with `PYTHONPATH=.`. Fish shell: no heredocs in commands given to the user.
- Never re-run AI batches for formatting fixes; use local text manipulation on the ledger.
- A new dependency or tool must be recorded in `kamma/tech.md` before implementation.

## Open questions (for the user)

1. **The Google Sheet.** Not read this session. What does it hold — a curated list of Pāḷi–Russian pairs? If so it is the first gold set and its rows enter the ledger with `method = sheet`. An export into `temp/ru_cognate/` is enough.
2. **Etymological dictionary for the verifier.** Vasmer's dictionary (Фасмер) is the standard reference for Russian etymology. Whether a machine-readable or reliably fetchable copy is available to an agent is **(unverified)**. Without it the verifier has only Wiktionary.
3. **Headwords without a `russian` row (739).** Proposed: skip and report. Creating a row that holds only `ru_cognate` may affect code that treats "has a `russian` row" as "is translated" — **(unverified)**; check the translate pipeline and the exporters before choosing otherwise.
4. **Which model runs the batches.** Proposed: a cheaper model for Stage 2 proposals, a stronger one for Stage 3 verification, since the verifier is the quality gate.
5. **Value format.** Proposed: words separated by `, `, lower case, no stress marks, nothing but the Russian words. Confirm, including the treatment of `ё`.
6. **Is the English `cognate` fallback wanted?** In the RU GoldenDict template the English cognate shows only when `ru_cognate` is empty. Filling `ru_cognate` will hide the English one there. Probably intended; confirm.

## Not done / not known

- Sanskrit dump not inspected; its coverage of the 743 Sanskrit roots is unknown. This is the largest uncertainty in the estimate "150–250 of 753 roots have a Russian cognate", which is a guess, not a measurement.
- Only the first 60 MB of the Russian dump was sampled; the ratios in Gotcha 3 are from that sample.
- No abandoned approaches yet. Rejected at the planning stage: a per-headword LLM pass over all 89.8k headwords (slow, costly, inconsistent inside a family, and unsourced); a pure LLM-per-root pass without sources (review would be of unsourced claims).
