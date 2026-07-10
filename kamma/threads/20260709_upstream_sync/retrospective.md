# Retrospective — Upstream Sync 518672a6..be49bffe

Stage 4 acceptance retrospective. User verification passed 2026-07-10 ("all is good,
proceed"), including the Batch E `joinedload(DpdHeadword.rt)` root-rendering watch item.

---

## Landed
*Issues fixed in code during this sync. Already in the repo (or committed working tree).*

- **Batch E architecture port** — `exporter/goldendict/export_dpd_ru.py` + `export_dpd_sbs.py`
  ported from `multiprocessing.Process` to the new upstream `ProcessPoolExecutor` /
  `_worker_init` / `_render_batch` skeleton, re-layering all RU/SBS specializations. Dropped
  `joinedload(DpdHeadword.rt)` to match the new upstream pattern (`.rt` now lazy-loaded in the
  main-process extraction step; perf-only). **User confirmed root/root-family data still renders.**
- **pyrefly TypedDict-spread fix** — `{**render_data, "pth": ..., "jinja_env": ...}` literals in
  `_worker_init` and the `RenderedSizes` append sites (`main_sbs.py`) tripped pyrefly's
  TypedDict-spread limitation. Resolved with localized `cast(...)` at the boundaries (runtime
  no-op). Applied uniformly across `export_dpd_ru.py`, `export_dpd_sbs.py`, `main_sbs.py`.
- **D7 Atomic Rename miss — FIXED.** D7 renamed `shared_data/help_ru/` → `shared_data/reference_ru/`
  and updated `tools/paths_ru.py` but MISSED the sibling `tools/paths_dps.py` (DPSPaths). Surfaced
  as a runtime `FileNotFoundError` in the SBS build. Fixed all 5 TSV paths + comment in
  `paths_dps.py`. Grep-verified no other stale `help_ru` path references remain.
- **Go deconstructor db-population bugs (3) — FIXED (local stopgaps, NOT registered).**
  1. `go_modules/dpdDb/model.go` `Lookup` struct missing `AbbrevOther` (upstream #77 added
     `abbrev_other` to `db/models.py` but never mirrored it to Go) + this fork's local `Tpd`.
  2. `go_modules/deconstructor/data/matchdata.go` `SaveToDb()` ignored `.Error` on
     `CreateInBatches`/`Commit`, so a NOT-NULL insert failure exited 0 and shipped an emptied
     `lookup` table silently. Now `HardCheck`'d with `Rollback()`.
  3. Batch size 2000→1500 to stay under SQLite's 32766 variable limit (18 cols × 2000 = 36000
     overflowed). Treated as plain upstream bugs to reconcile once upstream fixes them; write-up in
     `upstream_issue_suggestion_go_lookup_struct.md`.
- **Pre-existing broken tests fixed inside Commit 2** — `test_shadow_parity.py` +
  `test_namespace_isolation.py` helpers iterated the rich-object registry schema as if it were the
  old string schema. Fixed the helpers; 3 intentional divergences whitelisted (user-authorized).
- **pyrefly gate on `gui2/dps_example_field.py`** — 18 pre-existing errors fixed with `cast()`
  accessors + a `get_fields`→`get_fields_dps` rename (child-overridden; behavior preserved).
- **Kindle mobi "256 KB" — investigated, CLOSED as non-issue.** Local macOS build produces a broken
  ~256 KB `.mobi` because Calibre `ebook-convert` strips Kindle dictionary markup (`idx:entry`);
  the bundled `kindlegen` is a Linux ELF that can't run on macOS. CI (`ru_release.yml`, ubuntu) uses
  kindlegen and produces the valid **73 MB** mobi (confirmed against the 2026-06-02 release asset).
  Not sync-caused (upstream mobi equally broken pre-sync). Added a `pr.amber(...)` warning to the
  macOS branch of `make_mobi` in `kindle_exporter_ru.py` so the broken local stub isn't mistaken for
  a success. No CI impact, no registry change.

## Promote
*Patterns worth turning into guide rules, validators, or archive entries. Done now — see
`archive_improvements.md` §21–§23.*

- **Atomic Rename must sweep ALL `tools/paths_*.py` siblings.** The D7 miss (paths_ru updated,
  paths_dps missed) is exactly the class of bug the Atomic Rename Protocol exists to prevent, yet the
  grep step didn't cover the sibling path module. → §21.
- **Go struct ↔ `db/models.py` column parity check.** Two of the three Go bugs stem from the Go
  `Lookup` struct silently drifting from the Python model (`abbrev_other` never mirrored; the struct
  sits at ~97% of SQLite's variable ceiling so any new column trips it). → §22.
- **macOS local kindle builds are not authoritative.** Document that Calibre cannot compile Kindle
  dictionary mobis; only kindlegen (Linux/CI) can. Now enforced by an in-code warning. → §23.

## Drop
*Genuine one-offs that do not warrant a process change.*

- **`scripts/build/tarball_db.py` macOS `tar -I "xz -9e -T0"` failure.** GNU-tar-only syntax; the
  file is upstream-only and runs on Linux CI where it works. Only failed because the user ran the
  full `dpd-makedict` locally on macOS. Reverted a local patch attempt to pristine upstream; user
  commented out the local call themselves. One-time local-env mismatch, no recurring risk.
- **`audio/db_release_download.py` "no archive found".** External `dpd-audio` GitHub release
  transiently had no `.tar.gz` asset. File untouched by the sync; build continued gracefully.
- **`registry.json` stale `(help_ru)` prose parenthetical (~line 388).** Should read `reference_ru`
  post-D7. Doc-only, does not affect `validate_registry.py` or runtime. Cosmetic nit, not a process
  change.
