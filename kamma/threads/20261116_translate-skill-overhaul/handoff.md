# Handoff — translate-skill-overhaul (written after Phase 3)

## State
Phases 1, 2, 3 are DONE and verified (see `[x]` markers + inline notes in `plan.md`).
**Next: Phase 4, task 4.1** (C3: `processed_ids.json` → `{lang, mode, ids}`; chunk `IN` at 500; grep readers of `ai_processed_ids_json` in `tools/paths_dps.py`). Nothing is marked `[~]`.

## Files touched so far (uncommitted; user commits)
- New: `kamma/translate/scripts/offpeak.py`, `kamma/translate/scripts/session_log.py`, `tests/kamma_tests/translate/test_offpeak.py`
- Changed: `kamma/translate/scripts/{synonym_audit,batch_runner,ai_check_russian_meanings,ai_meaning_checker}.py`, `tools/ai_batch_processor.py`, `tools/ai_models.json`, `kamma/upstream_sync/registry.json`, `kamma/translate/{log.md,state.json}` (header / `window_start` only), thread `spec.md` / `plan.md`
- Tests changed: `tests/kamma_tests/translate/{test_synonym_audit,test_batch_runner,test_ai_check_russian_meanings,test_ai_meaning_checker}.py`, `tests/tools/test_ai_batch_processor.py`
- Unrelated dirty files NOT mine (do not touch): `gui2/data/dps_history.json`, `gui2/data/example_stash.json`, `misc/pat-bi/`.

## Drift from spec/plan (all recorded in plan/spec)
1. `CN_HOLIDAYS` has an empty `2026: []` entry (else every 2026 run would be blocked by the missing-year rule).
2. New shared helper `session_log.py` (session-line format + `update_state`) used by the audit and the runner.
3. `judge_entries` now returns a `JudgeResult` dataclass (existing tests updated for the new return shape).
4. Spec-D "checker commits once per chunk" was done in 3.4.

## Validation notes
- A tool hook blocks pytest commands unless they name one literal test file path: `$VAR` paths, loops, and even the bare phrase in a heredoc get blocked. Run one file per call, literal path, with `-v`.
- zsh does not word-split `$VAR` lists, so pass explicit paths to ruff / pyright / pyrefly.
- PRE-EXISTING, NOT CAUSED BY THIS THREAD: 4 fixture tests in `test_ai_meaning_checker.py` (`..._{meaning,meaning_raw,russian_grammar_meaning_raw,notes_raw}_mode_matches_fixture`): live `dpd.db` English text drifted from the 2026-07-09 fixture. Do not touch or weaken.
- `default_models[0]` is now `deepseek-flash` (DeepSeek `GET /models` lists `deepseek-flash`, `deepseek-v4-pro`). OpenRouter entries unchanged until 7.4.
- A real-DB report-only audit run works; its log line and `last_audit` were removed afterwards as test noise (targeted edit, not git).

## Remaining
- Phase 4 (ids flow, rejects.json, translation check)
- Phase 5 (Op 5 filter, SQL limit, in-process `--status`; removes `build_status_probe_command` / `STATUS_GENERATE_PROBES`)
- Phase 6 (docs; the antigravity grep still hits `pipeline.md`, `.claude/commands/translate.md`, `.agents/skills/translate/SKILL.md`)
- Phase 7 (real AI, off-peak; 7.4 is the only user decision)
- Phase 8
- Before the Phase 7 live calls: `require_offpeak` blocks weekday 01–04 / 06–10 UTC.

## Known issues / failed attempts
None open. One mistake: macOS `sed -i` without `''` failed; use python edits instead.

## Next decision
None for the user until Phase 7.4. Phases 1–3 are ready to commit (message must reference #53).
