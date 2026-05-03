# Plan: Upstream Sync 2026-05-02

> **Executing model**: Follow the 5-Stage workflow defined in `kamma/upstream_sync/guide.md`.
> Mark tasks `[~]` before starting, `[x]` on completion.

---

## Stage 1: Prep — COMPLETE

- [x] Environmental validation, registry check, SMD coverage check
- [x] `prep_analyzer.py` → `prep_report.md` + `prep_manifest.json`
- [x] **Commit 1** (cc60ac42): `#sync: upstream pull 9af5f7ee..44a8a005, 133 files, 2026-05-02`

---

## Stage 2: Analysis — COMPLETE

- [x] `dynamic_plan.md` created and approved
- [x] Discussion flags resolved

---

## Stage 3: Execution & Verification — COMPLETE

- [x] All `dynamic_plan.md` items executed (Iron Rule followed)
- [x] **Commit 2** (1f5a4f75): `#sync: manual merge resolutions 2026-05-02`
- [x] **Commit 3** (8e72746a): `#sync: fix namespace violations and dead code in shadow copies`
- [x] **Commit 4** (27d4372e): `#sync: fix cleanup script and registry unique_paths`
- [x] **Commit 5** (bc7ac5e9): `#sync: archive legacy html templates replaced by jinja2 upstream`
- [x] **Commit 6** (3db2afeb): `#fix: replace removed Printer methods`
- [x] Tests pass: 232 passed, 1 skipped
- [x] Manual verification complete

---

## Stage 4: Docs Translation Parity — COMPLETE

### Stage 4.A — Analysis (PRO model)

- [x] **4.1** Parity check run — 2 missing (`install/dpd_app.md`, `newsletters.md`), 0 stale
- [x] **4.2** Terminology glossary extracted from existing `docs_rus/` files
- [x] **4.3** `docs_translation_plan.md` written with glossary, rules, per-file tasks
- [x] **4.4** Plan approved by user
- [x] `check_docs_parity.py` script created in `kamma/upstream_sync/scripts/`

### Stage 4.B — Translation (FAST model)

- [x] **4.5** `docs_translation_plan.md` read
- [x] **4.6** `docs_rus/install/dpd_app.md` — full Russian translation created
- [x] **4.7** `docs_rus/newsletters.md` — symlink to `../docs/newsletters.md` (NO_TRANSLATE)
- [x] **4.7b** `docs_rus/changelog.md` — converted to symlink `../docs/changelog.md` (NO_TRANSLATE)
- [x] **4.8** `mkdocs_ru.yaml` nav — 3 insertions: DPD Приложение, Changelog, Новостные рассылки
- [x] **4.9** Commit ready: `#docs: translate missing docs_rus/ pages for sync 9af5f7ee..44a8a005`

---

## Stage 5: Verification & After-sync — COMPLETE

- [x] Manual verification passed
- [x] `accepted_sync.json` updated to `44a8a005`
- [x] `new_improvements.md` promoted to `archive_improvements.md`
