# Handoff

## State (2026-11-09)
Cycles 0001-0005 done and validated; ALL UNCOMMITTED. Backlog empty. Thread stays open (loop) for future user-requested corrections.

## Uncommitted work
- shared_data/pali_class/grammar/*.tsv (cycles 0001-0005; `samasa.tsv` was dirty BEFORE this thread — do not touch)
- kamma/threads/20261109_grammar_tsv_fixes/ (records, learnings, handoff)
Draft commit messages are at the end of each `cycles/000N_*.md`. Stage by explicit file list; never stage `resources/` submodules.

## Closed decisions (no action)
- Acc sg of animates stays nominative lemma form (convention, see learnings).
- cond.tsv native column empty (12 rows): translation task, use the `translate` skill, not this loop.
- Fem-only plurals, mixed-gender merged parts (a_adj:3/14/23, a_ptp:13/14/29): left as-is by design (cycle 0004).
- Noticed, not touched: 'ранее (вещи)' (a_adj:35) uses an adverb for 'earlier'.

## Open (not done, user decision)
- Abbreviations golden fixture (`tests/tools/test_docs_update_abbreviations_fixtures.json`) still has pre-existing `a compoun` drift; outside this thread.
- `anta_prp` plural/singular and `е`/`ё` mixes left as-is.

## Next
When the user declares all fixes done: run the **Pre-Commit Cross-Check** (see plan.md) — remind the user to switch to another model in a new session before the final commit.

Wait for the user's next explicit correction; run the normal cycle (Report -> Analyze -> Approval -> Implement -> Validate -> Record -> Handoff -> Learn).
