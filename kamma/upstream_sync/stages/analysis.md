# Stage 2: ADVANCED Analysis

## Contract
- **Owner**: ADVANCED only.
- **Input**: `prep_report.md`, `prep_manifest.json`, `registry.json`, SMD files, and `handoff.md`.
- **Output**: `dynamic_plan.md` and updated `handoff.md`.
- **Boundary**: ADVANCED interprets, decides, and plans. ADVANCED does not perform mechanical edits, formatting, tests, or bulk file operations.

## Required Plan Sections
- **Manual Merges**: Logic to port into `modified_upstream_files`.
- **Shadow Updates**: Exact parity changes for `*_ru.py`, `*_sbs.py`, `*_dps.py`, `*_ta.py`, or locale directories.
- **Inspired Backports**: Select improvements to port into `inspired_by_upstream`.
- **Manifest Coverage**: every changed upstream path in `prep_manifest.json` accounted for.
- **Exact Local Targets**: use `mapped_actions[].local_target_path` when present; fall back to `local_path` only for older manifests.
- **Discuss Logs**: Outcomes of any `discuss: true` flags.
- **Verification Commands**: Exact commands FAST must run after each item or section.

## Plan Quality Gate
Every `dynamic_plan.md` item must include:
- Exact file path(s).
- Exact source path(s).
- Exact anchor string or line reference.
- Literal code/text to insert, replace, or delete.
- Verification command.

If any item requires FAST to "figure out", "determine", "inspect", "decide", or "fix as needed",
the plan is incomplete and ADVANCED must resolve it before handoff.

## Checklist
- [ ] Every modified upstream file has a corresponding local action or documented no-op reason.
- [ ] All `discuss` flags resolved and recorded.
- [ ] `dynamic_plan.md` is self-contained enough for a mechanical executor.
- [ ] `dynamic_plan.md` presented and approved by user.

## Stop Conditions
ADVANCED must stop and request FAST if:
- Files need to be edited, copied, generated, formatted, tested, or translated mechanically.
- A command must be run to collect new factual output.
- Bulk search or broad file reading is needed beyond focused fact-checking.

## Handoff Required
Update `<thread_dir>/handoff.md` with decisions, unresolved issues, errors/issues/repeated mistakes,
next model (`FAST`), and the exact fresh-session restart prompt. Then stop.
