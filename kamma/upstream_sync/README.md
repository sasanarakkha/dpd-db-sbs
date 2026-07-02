# Upstream Sync Infrastructure

Canonical sync process and tooling for the DPD SBS-RU fork.

All local sync-process documentation lives in `kamma/upstream_sync/`. Do not add sync-process
docs under upstream-owned `docs/`. Git commit/push policy is inherited from the global rules.

For the full protocol, model responsibilities, registry categories, and the Iron Rule, see
[guide.md](./guide.md).

## Entry Commands

- **Start a new sync**: run `scripts/cl_dps/dpd-kamma-sync`. This is the only sync-related Bash
  entrypoint — it backs up DPS localization tables, commits only the backup TSV changes, and
  initializes the Kamma sync thread through `kamma/upstream_sync/scripts/init_sync_thread.py`.
  All actual sync execution then runs through the Python scripts in
  `kamma/upstream_sync/scripts/`.
- **Resume a lost thread**: run
  `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir>` to print the current
  stage and next command (add `--instructions` for the matching guide.md section).

## Core Files

| File | Purpose |
|---|---|
| `guide.md` | Canonical protocol: Iron Rule, model responsibilities, registry categories. See **[guide.md § Registry Categories](./guide.md#registry-categories)**. |
| `registry.json` | Source of truth for file mappings, categories, and per-file merge guidance. |
| `accepted_sync.json` | Last accepted upstream SHA/date/ref. |
| `reviewed_shadow_noops.json` | Reviewed no-op ledger for upstream shadow-source changes that intentionally need no local edit. |
| `docs_translation_queue.md` | Pending `docs/` paths for the async Docs Translation Track. |
| `archive_improvements.md` | Accumulated lessons from past sync runs. |
| `templates/` | `plan.md` / `spec.md` starters for new sync Kamma threads. |
| `scripts/` | All sync Python scripts (`stage1.py`, `sync_status.py`, `execute_sync.py`, `finalize_accepted_sync.py`, `validate_registry.py`, etc). |
