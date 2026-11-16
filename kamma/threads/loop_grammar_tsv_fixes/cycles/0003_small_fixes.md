# Cycle 0003 — backlog items 5-7 (small fixes)

- **Approval:** user approved all backlog suggestions (2026-11-09). Items 5-7 had exact values, so applied directly; items 3, 1, 2 still need a proposal table (match list) approved before editing; 4 and 8: no action.
- **Applied (5 cells, scripted exact-match on file + line + id + column + old value):**
  - ii_masc:14 udāyinā (proper name Udāyī, confirmed in dpd.db `udāyī 1/2/3`): eng 'with Udāyī<br>from Udāyī'; native 'с Удайи<br>от Удайи'.
  - ii_masc:26 medhāvī: eng 'wise man<br>wise men<br>o wise man(s)!'; native 'мудрец<br>мудрецы<br>о мудрец(ы)!' (3 parts, matches gramma).
  - a2_masc:3 attānaṃ native 'себя<br>для самих себя<br>самих себя'.
- **Validation:** only those 5 cells differ from the pre-cycle state; ii_masc 25x9, a2_masc 11x9 (baseline); deck script exit 0, no amber/red; study-tools status unchanged (`?? kamma/draft/` pre-existing); the two grammar test files: 4 passed.
- **Draft commit message:** `fix: Udāyī proper name, medhāvī part count and attānaṃ gloss in Pali Class grammar TSVs`

## Item 3 — 'вы' → 'ты' for 2nd sg (applied 2026-11-09)
- 25 native cells (fut 4, opt 3, perf 1, pr 13, pr_aor_be 1, reflx 3) with verb/adjective agreement; opt:15 → 'ты мог бы видеть' (approved). 2nd pl 'вы все' untouched.
- Scripted exact-match (file + line + id + part, assert one hit each); re-scan finds 0 remaining 'вы' for 2nd sg.
- Validation: loader totals 286/712/1321 (baseline); deck script clean; study-tools status unchanged; grammar tests 4 passed.
- Draft commit message: `fix: use ты for 2nd person singular in Pali Class grammar TSV native column`

## Items 1 and 2 (applied 2026-11-09 on user's blanket "apply all"; no per-cell table review)
- **Item 1 ('(вещь)' gender), 26 cells in a_adj/u_adj/i_adj/a_ptp:** only unambiguous cells — rows where gramma and native have equal part counts and the gramma label is masc/nt-only (no fem) — got предмет forms ('с большим (предметом)', 'в большом (предмете)', 'для большого (предмета)'); masc/nt nom sg 'X (вещь)' → 'X (предмет)'. Fem and mixed-gender cells untouched.
- **Not applied (ambiguous, deferred):** all mixed-gender / misaligned cells (gramma and native part counts differ; the native part is shared by several labels), a_ptp relative-clause forms '(вещи, которые)…', i_adj fem/masc 'страстный (вещь)' cells, u_adj:8 'большой (вещь)'.
- **Item 2 (uninflected participles), 19 cells in a_pp only:** participle/placeholder put in the case required by the preposition ('из (чего-то) истощённого', 'с (чем-то) возникшим'). 'о …' vocative cells left. a_ptp skipped: its '(тем, к кому) следует…' relative clauses are grammatical, not uninflected participles.
- Judgment calls to eyeball: a_pp:17 'от воздержавшегося (одного)' (label was mixed), a_pp:7 'в завершённом (чём-то)' (label fem, adjective still masc ending).
- **Validation:** 45 cells changed; counts a_adj 36, u_adj 23, i_adj 25, a_ptp 33, a_pp 39 rows × 9 cols (baseline); loader totals 286/712/1321; deck script clean; study-tools status unchanged; grammar tests 4 passed.
- Draft commit message: `fix: gender and case agreement of placeholder nouns and participles in Pali Class grammar TSVs`
