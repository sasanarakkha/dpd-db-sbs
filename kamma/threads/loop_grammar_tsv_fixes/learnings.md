# Learnings

## Process
- Each cycle does only what the user explicitly asks; no preliminary scans or extras.

## Gotchas
- Tests do not read the real grammar TSVs; the diff check and deck script run are the real checks.
- Baseline row counts in `baseline.md` come from the exporter's loader; a raw csv count differs on 5 sheets (roots, adv, opt, assim, alph). Compare only touched sheets, or use the loader.
- A scripted replace keyed on file + id + column + full old value (assert exactly one hit) is safe; ids are not unique across sheets, so include the file.
- Parse TSVs with the default `csv` quoting (not QUOTE_NONE): opt/opt_be/adv have quoted cells with embedded newlines/tabs that otherwise look like corrupt split rows. Report physical file lines (`reader.line_num`), not record indexes.
- Audit method that worked: scripted heuristics for part-count/case-preposition/Latin-`o`/paren/whitespace, then hand-read every row; verify doubtful glosses against `dpd.db` (e.g. `vihari 2.1` 'removed', `pare 1`) before calling them errors.
- A scripted cell replace must key on physical line (csv line_num) + id + column + full old value; run mechanical rules (Latin o, trims) only after table rows so they don't conflict.
- Cell edits: key on file + physical line + id + column + exact old *part* (split on `<br>`, assert count == 1); never rely on part index — `eng`/`native` parts are often condensed vs `gramma` labels (a native part can cover several labels), so part-count equality is the only safe alignment test.
- `eng`/`native` placeholder convention for adjective sheets: fem '(вещь)', masc/nt '(предмет)', mixed-gender (masc & fem & nt) rows keep fem 'вещь'; adjective and relative pronoun agree. Plural nouns follow the same split (вещи/предметы).
- 2nd sg is 'ты' (not 'вы'); 2nd pl is 'вы все'.
- Convention (no change): acc sg of animates stays in the nominative lemma-citation form in `native`.
- A user "apply all" can override the per-cell table gate, but still gate by rule (label-checked, aligned rows only) and defer ambiguous cells to a prepared next cycle.
- Raw-text substring counts mislead (an old part like `(чего-то) возник` is a prefix of its fixed form and other cells); edit by splitting the physical line on tab, then the native field on `<br>`.
- Participle placeholders in oblique cases must decline the participle too (gen sg `возникшего`, pl `возникших`), not just drop the preposition.
