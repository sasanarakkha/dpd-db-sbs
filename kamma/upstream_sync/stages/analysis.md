# Stage 2: Analysis

## Contract
- **Input**: `prep_report.md`, `prep_manifest.json`, and `registry.json`.
- **Output**: `dynamic_plan.md` in the thread folder.

## Required Report Sections
- **Manual Merges**: Logic to port into `modified_upstream_files`.
- **Shadow Updates**: Parity changes for `*_ru.py`, `*_sbs.py`, etc.
- **Inspired Backports**: Select improvements to port into `inspired_by_upstream`.
- **Manifest Coverage**: every changed upstream path in `prep_manifest.json` accounted for.
- **Discuss Logs**: Outcomes of any `discuss: true` flags.

## Checklist
- [ ] Every modified upstream file has a corresponding local action.
- [ ] All `discuss` flags resolved and recorded.
- [ ] `dynamic_plan.md` presented and approved by user.
