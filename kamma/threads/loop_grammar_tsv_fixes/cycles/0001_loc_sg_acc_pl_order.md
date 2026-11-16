# Cycle 0001: acc pl / loc sg order in eng and native

## Report
User: in `a_masc` dhamme/kāye/loke have grammar "acc pl<br>loc sg" but eng is reversed ("in teaching<br>teachings"). Fix, and scan all grammar TSVs for similar order inconsistencies. After the dry run the user also approved fixing the known Russian (`native`) issues on the same rows.

## Analysis
Scan: all rows with >=2 `<br>` parts in `gramma` and equal part count in `eng`; case class from gramma (nom/acc = bare, loc/instr/abl/dat/gen/voc) vs leading preposition in eng. Flag when same multiset, different order. Result: 4 eng hits (a_masc 342/343/39943, as_masc 51512 mane). Rows with differing part counts skipped (structural, out of scope). Not checked: sg/pl or meaning correctness beyond the Russian rows below.

## Approval
Approved: 4 eng reorderings + all known Russian issues (3 reversals, plus number/content errors on the same rows).

## Implementation
Scripted exact-match replace (file + id + column + full old value, asserted exactly one hit each); 8 cells:
- a_masc 343: eng -> `teachings<br>in teaching`; native -> `преподавания<br>в преподавании`
- a_masc 342: eng -> `bodies<br>in body`; native -> `тела<br>в теле`
- a_masc 39943: eng -> `worlds<br>in world`; native `в мировых мирах` -> `миры<br>в мире` (was a single value)
- as_masc 51512: eng -> `minds<br>in mind`; native -> `умы<br>в уме`

## Validation
- `git diff`: only a_masc.tsv (3 lines) and as_masc.tsv (1 line), exactly the 8 cells; `git diff --check` clean.
- Rows x cols: a_masc 50x9, as_masc 17x9 unchanged.
- Deck script: exit 0, no amber/red, rows 286/712/1321 = baseline.
- study-tools status: unchanged (only pre-existing untracked `kamma/draft/`).
- Loader tests (2 files): 4 passed.
- Re-scan after edit: 0 eng hits, 0 ru hits.

## Outcome
Done. Russian wording chosen by the agent (keeps each row's existing lemma, fixes number/order); a native-speaker check is advisable.
