# Cycle 0004 — deferred '(вещь)' placeholder cells

- **Report/analysis/proposals:** `0004_proposals.md` / `0004_proposals.json` (54 cells).
- **Approval:** user approved all 54 (2026-11-09).
- **Applied:** 54 native parts in a_adj, u_adj, i_adj, a_ptp via scripted exact-part replace (file + line + id + old part, one hit each, asserted).
- **Unchanged by design:** fem-only plurals ('великие (вещи)', 'ранее (вещи)'), mixed-gender merged parts (a_adj:3/14/23, a_ptp:13/14/29), fem vocatives.
- **Validation:** counts a_adj 36, u_adj 23, i_adj 25, a_ptp 33 rows x 9 cols (baseline); loader totals 286/712/1321; deck script clean; study-tools status unchanged; grammar tests passed.
- **Draft commit message:** `fix: masc/nt placeholder nouns (предмет) and agreement in Pali Class grammar adjective TSVs`
