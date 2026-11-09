# Cycle 0002 — audit of sg/pl, case, part-count and meaning errors

- **Report:** `0002_audit_report.md` (279 proposed cells); proposals: `0002_proposals.json`.
- **Approval:** user approved all rows, the three mechanical rules, and all suggestions in "Needs your decision".
- **Applied (2026-11-09):** scripted exact-match replace (file + physical line + id + column + full old value, all asserted):
  1. 279 table cells.
  2. 24 cells from the decision list: aor 36-38 'lived', santappesuṃ, app:9 gramma/eng/native (dat+gen), atta voc, a_nt pahānāya, i_fem āpattiyā, raja_masc царей→королей, у→в (go_masc, raja_masc), gihī voc, sikkhitabba 'осваивать', perf agacchaṃ.
  3. Rules: whitespace/typo trims (9 rows, incl. `fam`→`fem`), Latin `o`→`о` (50 cells left after table), `из ` dropped from gen parts (7 cells left after table).
- **Not applied (no concrete per-cell proposal):** systemic items — '(вещь)' gender convention, uninflected participles after prepositions, 'вы' for 2nd sg, acc sg of animates in nominative; ii_masc:14 udāyinā, ii_masc:26 medhāvī part count, a2_masc:3 attānaṃ; cond.tsv native empty (untranslated).
- **Validation:** 365 cells changed (native 330, eng 27, gramma 5, pali 3); row/column counts unchanged for all 61 sheets (loader totals 286/712/1321 match baseline); deck script exit 0, no amber/red lines; study-tools status unchanged; `tests/test_anki_class_grammar*.py` 4 passed. `samasa.tsv` untouched by this thread (pre-dirty).
- **Draft commit message:** `fix: correct number, case, part-count and meaning errors in Pali Class grammar TSVs (eng + native)`
