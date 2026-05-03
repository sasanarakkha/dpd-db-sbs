# Handoff: Upstream Sync 2026-05-02

## Current Status

**ALL STAGES COMPLETE. Pending one final commit.**

### Commits landed
| Commit | Message |
|---|---|
| cc60ac42 | `#sync: upstream pull 9af5f7ee..44a8a005, 133 files, 2026-05-02` |
| 1f5a4f75 | `#sync: manual merge resolutions 2026-05-02` |
| 8e72746a | `#sync: fix namespace violations and dead code in shadow copies` |
| 27d4372e | `#sync: fix cleanup script and registry unique_paths` |
| bc7ac5e9 | `#sync: archive legacy html templates replaced by jinja2 upstream` |
| 3db2afeb | `#fix: replace removed Printer methods` |

`accepted_sync.json` is already updated to `44a8a005`.

---

## Stage 4.B — COMPLETE

**Done:**
- `docs_rus/changelog.md` — symlink → `../docs/changelog.md`
- `docs_rus/newsletters.md` — symlink → `../docs/newsletters.md` (too large/data-heavy for translation)
- `docs_rus/install/dpd_app.md` — full Russian translation created
- `kamma/upstream_sync/scripts/check_docs_parity.py` — `NO_TRANSLATE` updated with `"newsletters.md"`
- `mkdocs_ru.yaml` — 3 nav insertions added (DPD Приложение, Changelog, Новостные рассылки)

**Files staged, commit ready. Present to user:**
```
git commit -m "#docs: translate missing docs_rus/ pages for sync 9af5f7ee..44a8a005"
```

Also stage handoff + plan before committing:
```
git add kamma/threads/20260502_upstream_sync/handoff.md kamma/threads/20260502_upstream_sync/plan.md
```

---

## Errors / Issues (cumulative — append only)

- `is_vagga_sutta` in old handoff: does NOT exist in upstream. Actual new properties are `is_samyutta` and `is_vagga`.
- `_load_sutta_alias_map()` uses `from tools.paths import ProjectPaths` (not paths_ru). Correct for `db/models.py`.
- `DpdHeadword.su` changed to `@cached_property` — no longer part of SQLAlchemy ORM mapping.
- `toolkit_ru.py` has TWO separate `if lookup_results:` blocks — both updated correctly.
- `backup_dps.py` does NOT have `split_tsv_file` — upstream change E doesn't apply.
- Kindle titlepage diff was cosmetic (date stamp only) — skipped.
- Upstream webapp `dpd_headword.html` diff used `d.su.is_vagga` in one place and `is_vagga` variable elsewhere (inconsistency in upstream). Shadow copies all use the `is_vagga` variable form for consistency.
- `paths_dps.py` has no webapp `template_*` section — only needs `abbreviations_other_tsv_path` path entry (done).
- **[FIXED Session 4]** Namespace isolation violations in 4 files.
- **[FIXED Session 4]** Ruff F821 errors in `export_help_ru.py` + `export_help_sbs.py`.
- **[FIXED Session 4]** `ru-dpd.ifo` stale artifact deleted.
- **PROCESS NOTE**: Tamil is NOT out of scope. All four locales always in scope.
- **[Session 5 MISTAKE]** Added `"gui/"` to `unique_paths` — REVERTED. `gui/` is intentionally excluded from sync scope. Do NOT run `test_shadow_cleanup.py` against `gui/`.
- **[Session 5]** `test_shadow_cleanup.py` had `pr.title()` and `pr.warning()` calls that don't exist in Printer API — fixed.
- **[Session 5]** `test_shadow_cleanup.py` only checked `russian_copies` + `sbs_copies` — missing `dps_copies` + `tamil_copies` caused false orphan positives — fixed.
- **[Session 5]** `test_shadow_cleanup.py` directory-level shadow keys (ending in `/`) were not matched against file paths — fixed.
- **[Session 5]** Cleanup scope: `db/`, `exporter/`, `tools/` only. NOT `gui/` (explicitly excluded).
- **[Session 6]** Discovered codebase-wide Printer API breakage (not sync-introduced):
  - `pr.title()` → `pr.green_title()` (52 occurrences)
  - `pr.info()` → `pr.green()` (82 occurrences)
  - `pr.warning()` → `pr.amber()` (35 occurrences)
  - `pr.error()` → `pr.red()` (19 occurrences)
  - Total: 188 fixes in 28 files across tools/, scripts/, db/, gui2/, kamma/, archive/, resources/
- **[Session 7]** Stage 4 (Docs Translation Parity) added to workflow — was not part of original sync. Run as a catch-up. `check_docs_parity.py` script created. 2 missing files found: `install/dpd_app.md`, `newsletters.md`.
