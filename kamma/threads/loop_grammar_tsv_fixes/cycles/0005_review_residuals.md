# Cycle 0005 — review residuals (from review.md)

## Report
`review.md` listed half-finished cells left by cycles 0003/0004 plus one untouched cell. User approved items 1–6 plus decision 1 (two same-family `a_pp` cells). Out of scope by decision: abbreviations fixture, `samasa.tsv`, `anta_prp` plural/singular mix, `е`/`ё` mix.

## Implementation
Scripted part-level replace (key: file + id + exact old part, assert one hit, line-scoped field edit). 8 cells:

| File | id | Old part | New part |
|---|---|---|---|
| a_pp | 37337 | (чего-то) возник | (чего-то) возникшего |
| a_pp | 3728 | (чего-либо) возникло | (чего-либо) возникших |
| a_pp | 3730 | (чего-либо) возник | (чего-либо) возникшего |
| a_pp | 3707 | завершенного (чем-то) | завершенного (чего-то) |
| a_pp | 3736 | среди (чего-либо) возникло | среди (чего-либо) возникших |
| a_pp | 37037 | в (чем-либо) с соломенной крышей | в (чём-либо) с соломенной крышей |
| u_adj | 40240 | в упрямом (одном) | в упрямой (одной) |
| pers_pron | 995 | ваши | ваш |

## Validation
- Pre/post diff of the 3 files: exactly these 8 cells changed; line counts equal (40/24/31); `<br>` part counts unchanged.
- `git diff --check` clean.
- `uv run pytest tests/test_anki_class_grammar.py tests/test_anki_class_grammar_feedback.py` → 4 passed.
- Deck script not run (writes to external repo); loader totals unaffected since row and part counts are unchanged.

## Outcome
Done, uncommitted.

## Draft commit message
fix: finish participle/adjective/pronoun case agreement in grammar TSVs

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
