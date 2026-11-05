# Handoff: Upstream Sync 2026-11-05

## Status

Stage 1 COMPLETE. 2a COMPLETE. 2b COMPLETE (D1–D12 RESOLVED). 2c IN PROGRESS (sessions 4–5): §9A pre-pull gate, §9B restored files (D1/D2/D3/D5), §9C small ports + data + deletions (S1,S3,S4,S12–S15,S18, D7,D8,D9, openai retire, stale refs) WRITTEN. §9D webapp (D11, D12-webapp, S19–S21) WRITTEN. §9E goldendict/RU plural/kindle (D12, S5–S7, S11, I1–I3) WRITTEN (session 5). §9F gui2 Flet 1.0 (D4, D10, S2, S22, I10) WRITTEN (session 6) → **2c COMPLETE**. 2d approval PENDING. `execute_sync.py` NOT yet run.

## Current Stage

Stage 2 COMPLETE — 2d APPROVED (user, 2026-11-05, "proceed all": deviations 1–4 and 9–11 approved).

**Stage 3 session 7 (2026-11-05):** §9A A0 DONE (registry edits 1–8 applied by sync-fast). A1 DONE: prep rerun (blockers now only B1 — B2 cleared by the repoint; discuss_paths were the 5 resolved D-items → cleared to `[]`), `run_acknowledged_blockers.txt` written (B1+B2; extra line harmless, `sync_runtime.py` subtracts acknowledged from blockers). Notes: (a) standalone `validate_registry.py` reports 1 EXPECTED pre-pull error `sbs_copies: upstream source 'scripts/server_dpdict/update-dpd.sh' does not exist` (repo-root existence check; prep uses `validate_registry_core` without repo_root, no pre-commit hook) — must pass after A3; (b) `execute_sync.py --dry-run` also refuses a dirty tree, so the A1 dry-run verify moves to after A2. **Blocked on A2 (⛔ USER commit).** Dirty files NOT from this sync: `tools/ai_models.json` (model/grounded_models edits — user's), `resources/*` submodules (excluded from commit scope).

## Last upstream sync

- **Commit / tag**: `be49bffe2c2c`
- **Full SHA**: `be49bffe2c2c85971784337d4e09915ad1f42800`
- **Date**: `2026-07-08T20:38:18+02:00`
- **Ref**: `upstream/main`

## Completed Work

- Sync thread initialized.
- Backup commit `c1d2c26eb` `backup dps data` (2 TSVs) made by dpd-kamma-sync (user-approved).
- Stage 1 chain ran: shadow health OK, F821 lint OK, registry valid, `git fetch upstream` OK, prep_analyzer OK (range be49bffe2c2c..c54f942ee3f6).
- Triage verdict -> Stage 2.
- Blockers: `exporter/kindle/templates/ebook_deconstructor_entry.jinja`, `scripts/server/update-dpd.sh`.
- Discuss paths: `.gitignore`, `AGENTS.md`, `db/models.py`, `gui2/main.py`, `pyproject.toml`.

## Commands Already Run

- `scripts/cl_dps/dpd-kamma-sync`
- `uv run python3 kamma/upstream_sync/scripts/stage1.py kamma/threads/20261105_upstream_sync` (exit 1 only because triage reports blocker/discuss paths; all prior steps OK)

## Files Changed

- `plan.md`, `spec.md`, `handoff.md`
- `prep_report.md`, `prep_manifest.json` (new)
- `kamma/upstream_sync/docs_translation_queue.md` (modified by prep_analyzer)
- `dynamic_plan.md`, `stage2a_findings/*` (new, session 2)

## Open Decisions

- Blockers B1/B2 resolved by analysis (dynamic_plan.md §1) — acknowledge both before execute_sync.
- D1–D12 RESOLVED (session 3). Summary: D1 take upstream .gitignore + drop local `exporter/mcp/input/*`; D2 additive AGENTS.md bullets (7 items, 2 conflicts keep local); D3 models verbatim + live-db UPDATE 70815→`hatthaka 4` + NOCASE index; D4 adopt Flet 1.0; D5 upstream pyproject + num2words, port subprocess-git into backup_dps.py, retire openai batch script to archive/dps/; D6 keep kindlegen via unique_paths + `epub:type` port, #217 deferred to DRAFT thread `kamma/threads/20261105_kindle_ru_217_port/`; D7 stop automatic RU TPR export (keep code); D8 mirror upstream decon generation, remove `resources/deconstructor_output` submodule (user approved resources/ exception); D9 git rm 36 pre-range test orphans; D10 pass2_add_view pulled verbatim, dps_view MUST keep `/sbs/` request_dpd_server; D11 webapp parity + licence + lookups_take_turns + permalinks (RU «Постоянная ссылка»/«Как цитировать») + IndexStaticFiles; D12 RU 3-form plural (`ruPlural`/`ru_plural`) — 2c must show RU strings for user review.
- Registry edits BEFORE `execute_sync.py`: remove `gui2/pass2_add_view.py` from `modified_upstream_files`; add `exporter/kindle/kindlegen` to `unique_paths`; repoint B2 upstream path. Then rerun prep → clear discuss_paths → `run_acknowledged_blockers.txt` (B1, B2).
- 2a session (2026-11-05, ADVANCED): per-domain analyses saved in `stage2a_findings/`; confirmed 3 new import breakages (S1 help_abbrev_add_to_lookup_ru, S2 dps_example_field, S3 list_of_words_from_txt) via AST scan; pre-existing breakages listed in §5 (out of scope).

## Errors, Issues, And Repeated Mistakes

- 2c session 4 raised 4 ⚠ 2c-DEVIATIONs for 2d approval: (1) D1 keep local `.gitignore` line 5 `.claude/scheduled_tasks.lock` (upstream `.claude/` would block tracked `.claude/` re-includes); (2) D3 use upstream `tools/prepare_webapp_lookup.py` for the NOCASE index; (3) B2 include `prepare_webapp_lookup.py` in update-dpd-sbs.sh (D11 adopted NOCASE); (4) §6 correction: `submodules_update.yml` IS present locally (registered unique) → unregister so P0 deletes it; also unregister + `git rm scripts/cl/dpd-gui2`.
- Session 5 (§9E) items for 2d: (5) E-12 RU citation help entry SKIP (recommendation); (6) E-11 drops the local `cast` in `_worker_init` for upstream's TypedDict constructor (strict parity; STOP if type checkers reject); (7) RU-strings table at end of §9E incl. open choice «идиома» vs «идиоматическое выражение»; (8) out-of-scope report: `webapp/ru_templates/root.html:44-46` «слов(а)» (upstream unchanged). S11 nav.xhtml = SKIP (no dead links in RU nav, verified). **Items 5–8 RESOLVED (user, 2026-11-05):** 5 SKIP approved; 6 approved; 7 GD idioms = «идиома, содержащая / идиомы, содержащие / идиом, содержащих» (E-3 updated; webapp keeps «идиоматическое выражение»); 8 acknowledged, no action. At 2d only the 4 session-4 deviations remain to approve.
- Session 6 (§9F) raised 3 new ⚠ 2c-DEVIATIONs for 2d: (9) add DPS index 17 to `_WARMUP_TAB_ORDER` (pre-build like the old eager construction); (10) edit local golden test `tests/gui2/test_dps_field_mapping.py` serializer + deterministic fixture transform (breaks on pull anyway: `flet.core.*` → `flet.controls.material.*`, border → `field_border`); (11) shadow upstream `tests/gui2/test_main.py` (`"DPS"` appended to its TAB_LABELS) + register it in `modified_upstream_files`. Also 2a corrections recorded in §9F header: missed `Page.set_clipboard` (dps_view) and bare-TextField `error_text`→`error` (dps_test_manager, dps_fields); `if clean_word:` guard needs no local edit. Accepted cosmetic: DPS example/meaning inner fields render grey borders (upstream `DpdTextField.before_update`).
- **Q1 RESOLVED** (user, 2026-11-05): RU permalinks = `https://ru.dpdict.net/<id>`; §9D D-3 rewritten (local `RU_PERMALINK_BASE` constant in `data_classes_ru.py`, no upstream `make_permalink` import, registry note). RU plural strings drafted in §9D D-7.4 (webapp) — present together with §9E GoldenDict strings at 2d.

- None yet.

## Next Model

ADVANCED

## Restart Prompt

```text
Dispatch Stage 1 to the sync-fast subagent (.claude/agents/sync-fast.md).

Continue upstream sync thread: <thread_dir>.
First read:
1. <thread_dir>/handoff.md
2. Run `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir> --instructions` for the current stage's guide section.
3. <thread_dir>/plan.md

Task: run `uv run python3 kamma/upstream_sync/scripts/stage1.py <thread_dir>`.
Do not perform analysis or strategic planning.
Stop before Stage 2 and update handoff.md.
```

## Friction notes

(append-only — one bullet per session; harvested into retrospective.md at Stage 4)

- Session 6 (2c §9F): zsh `${N}` brace rule bit again (`$N:gui2/...` → `:g` modifier). 2a's grep-based Flet 1.0 audit missed instance-method removals (`Page.set_clipboard`) and silent renames (`TextField.error_text`); an AST scan of `ft.*` calls + targeted `uv run --no-project --with flet==1.0.1` probes caught them — use that method for future framework-version migrations. New upstream tests that hard-code local-extended lists (`tests/gui2/test_main.py` TAB_LABELS) are invisible to prep because `tests/` is skip_sync.
- Session 5 (2c §9E): zsh `$O:e…` modifier expansion mangled `git show $O:exporter/...` (use `${O}`); bare `=====` in zsh `echo` triggers equals-expansion error. 2a kindle finding "nav dead-link cleanup" was wrong for RU (RU nav has no dead links) — re-verify 2a PORT claims before writing recipes.

- Session 4 (2c A–D): §6 had a factual error (`submodules_update.yml` claimed absent; it is present and registered unique) — 2a/2b facts must be re-verified in 2c before writing recipes. D1 'verbatim .gitignore' missed the `.claude/` tracking conflict.
- Session 3 (2b): `sync_status.py --instructions` reported "Stage 3" during 2b — it infers stage from `dynamic_plan.md` existence, ignoring the sub-stage status line / plan.md 2.2–2.4 checkboxes. 2a mis-proposed keeping `exporter/chrome_extension/node_modules/` by reading `skip_sync_patterns` as "local keep" (it is analysis-only; guide.md:478). Orphan "local commits since OLD" counts are misleading because `be49bffe2c2c` is not an ancestor of HEAD (file-based sync).
- Session 2 (2a): prep_report's `Needs Classification` says "register them" but policy is mirror-without-registry — wording conflict in prep_analyzer. Kindle blocker mapped to a non-existent RU path (registry is dir-level for kindle templates). tests/ is skip_sync, so pre-range test orphans are invisible to prep (found 36 manually).
- Session 1: none. (stage1.py exits 1 when triage finds blockers/discuss paths even though prep succeeded — expected.)

## Next session

- **Model:** ADVANCED (Opus)
- **User action required first:** §9A A2 — commit pre-pull files and resolve `tools/ai_models.json` + `resources/tpr_downloads` dirt so the tree is clean. Then resume at A1 dry-run verify → A3.
- **Start prompt:** `/update-upstream` — resume thread `kamma/threads/20261105_upstream_sync`, **Stage 3**. ADVANCED orchestrates; dispatch mechanical batches to `sync-fast` (sonnet) in plan order: §9A pre-pull gate (registry edits → rerun prep → clear `discuss_paths` → `run_acknowledged_blockers.txt` B1/B2 → `execute_sync.py`), then §9B → §9F, then §8 verification battery. Stop on any STOP rule in the plan. Exclude dirty `resources/*` submodule pointers from any commit scope.

Do not continue in this session.
