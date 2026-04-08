# Handoff: April 2026 Upstream Sync

**Date:** 2026-04-08  
**Branch:** sbs-ru  
**Thread dir:** `kamma/threads/sync_april_2026/`

## Status: Stage 1 Complete — Ready for Stage 2 (Analysis)

### What was done this session

1. `git fetch upstream` — upstream advanced from `89dcdaf3` → `9af5f7ee`
2. Fixed `accepted_sync.json` — was pointing at a local fork SHA; corrected to upstream SHA `89dcdaf3`
3. Updated `guide.md` — added `git fetch upstream` as first step in Environmental Validation
4. Ran `validate_registry.py` — OK
5. Ran `verify_smd_coverage.py` — OK (77 entries, no gaps)
6. Ran `prep_analyzer.py` — generated `prep_report.md` and `prep_manifest.json`
7. Ran `execute_sync.py` — 352 files changed, all staged, no DB schema changes
8. **Commit 1 is staged and ready** — user must commit manually

### Commit 1 (staged, ready to run)

```
git commit -m "#sync: pull upstream 89dcdaf3..9af5f7ee into sbs-ru (stage 1)"
```

### Upstream range

- From: `89dcdaf3` (2026-03-10, "data update")
- To: `9af5f7ee` (upstream/main HEAD, 2026-04-08)

### Key files to port in Stage 2

**Shadow sources changed (require porting local changes onto new upstream base):**
- `db/families/family_compound.py` → `family_compound_ru.py`
- `db/families/family_idiom.py` → `family_idiom_ru.py`
- `db/families/family_root.py` → `family_root_ru.py`
- `db/families/family_set.py` → `family_set_ru.py` (134 line delta — largest change)
- `db/families/family_word.py` → `family_word_ru.py`
- `exporter/deconstructor/deconstructor_exporter.py` → `deconstructor_exporter_ru.py`
- `exporter/goldendict/data_classes.py` → `data_classes_dps.py`
- `exporter/goldendict/templates/dpd_headword.jinja` → `ru_components/templates/`, `sbs_templates/`
- `exporter/grammar_dict/grammar_dict.py` → `grammar_dict_ru.py`
- `exporter/kindle/epub/OEBPS/Text/titlepage.xhtml` → `ru_components/epub/`
- `exporter/kindle/kindle_exporter.py` → `kindle_exporter_ru.py` (24 line delta)
- `exporter/tbw/tbw_exporter.py` → `tbw_exporter_ru.py` (28 line delta)
- `exporter/tpr/tpr_exporter.py` → `tpr_exporter_ru.py` (34 line delta)
- `exporter/webapp/data_classes.py` → `data_classes_ru.py`
- `exporter/webapp/templates/home.html` → `ru_templates/`, `sbs_templates/`
- `scripts/build/db_rebuild_from_tsv.py` → `db_rebuild_from_tsv_dps.py` (15 line delta)
- `scripts/build/families_to_json.py` → `families_to_json_ru.py`
- `scripts/server/update-dpd.sh` → `update-dpd-sbs.sh`
- `tools/version.py` → `version_ru.py`
- `db/backup_tsv/backup_dpd_headwords_and_roots.py` → `scripts/backup/backup_dps.py`

**Tracked modified files (check if local divergences need updating):**
- `exporter/webapp/data_classes.py` — also has `_ru` shadow above
- `exporter/webapp/static/home.js`
- `gui2/main.py`, `gui2/pass2_add_view.py`
- `tools/ai_manager.py`
- `.gitignore`, `AGENTS.md`

**Inspired sources** — mostly docs/newsletter images (cosmetic, low priority). Check:
- `.github/workflows/draft_release.yml` → `ru_release.yml`, `ru_release_test.yml`
- `tools/paths.py` → `paths_ru.py`, `paths_dps.py` (53 line delta — important)
- `exporter/goldendict/main.py` → `main_ru.py`, `main_sbs.py`

### How to start Stage 2

Start a new session and run:
```
/update-upstream
```

Then tell the agent:
> "Stage 1 is complete and committed. We are at Stage 2. Thread is `kamma/threads/sync_april_2026/`. Read the handoff at `kamma/threads/sync_april_2026/handoff.md` and `kamma/threads/sync_april_2026/prep_report.md`, then create `dynamic_plan.md`."
