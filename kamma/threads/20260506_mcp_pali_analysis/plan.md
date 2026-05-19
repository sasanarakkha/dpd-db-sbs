# Plan: MCP Pāḷi Analysis Pipeline — Continuous Feedback Loop

**This thread never finalizes. Workflow: user reports issue → we implement & test → update handoff → restart session.**

---

## Completed Work Summary

| Phase | Issue | Fix | Status |
|-------|-------|-----|--------|
| 1-3 | Pipeline architecture | Built 3-script pipeline (book_to_verses → ai_batch_translate → fill_dhp_examples) | ✓ |
| 4 | Apostrophes | Added `speech_marks.json` lookup in `book_to_verses.py` | ✓ |
| 5 | Preview reports | Created `preview_dhp_changes.py` for human review | ✓ |
| 6 | Report quality | Cleaned grammar columns, added headings, limited recursion | ✓ |
| 7 | Component lookup & POS | Enhanced component selection for nouns in compounds | ✓ |
| 8 | Negative kammadhāraya, collect_all_ids gate, component bolding | Three analyzer & bolding fixes for DHP23 | ✓ |
| 9 | Bolding uses real inflections | Use `DpdHeadword.inflections_list` instead of regex | ✓ |
| 10 | (Session 19) Grammar extraction | Extract grammar from inflections_html for compound parts | ✓ |
| 11 | (Session 20) Malformed AI JSON | Graceful fallback for incomplete JSON responses with template placeholders | ✓ |
| 12 | (Session 21) Component lookup prioritizes Lookup table | Trust Lookup table as authoritative for component lookup; skip inflections_html validation when Lookup finds a result | ✓ |
| 15 | (Session 22) DHP25 bolding & validation | Gate on word existence; exact match step 0; is_top_level flag for whole-token bolding of sandhi top-level words | ✓ |

**All tests pass (36). Ruff/pyright clean.**

---

## Next Phase

Report the next issue. Describe the verse, the word, and what the preview report shows vs. what is expected.
