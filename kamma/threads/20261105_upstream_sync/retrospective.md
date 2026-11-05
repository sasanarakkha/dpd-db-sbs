# Retrospective — Upstream Sync be49bffe2c2c..ee38f7a84

Sync commit `1a74f6480` (2026-11-05). Stage 4 gate released by user ("all tests are good - proceed").

---

## Landed
*Issues fixed in code during this sync. Already in the repo.*

- Local pyrefly pre-commit hook now blocks on errors only, and its `exclude:` mirrors `[tool.pyrefly] project-excludes`. It no longer blocks on upstream-excluded trees (518 errors / 90 warnings, none in our files). The registry `local_changes` was updated to match.
- Shadow-parity drift fixed by porting rather than whitelisting: `families_to_json_ru`, `utils_sbs`, `db_rebuild_from_tsv_dps`, and `character_replacer_sbs`. Pre-existing pyrefly errors in `db_rebuild_from_tsv_dps` were fixed using a typed tuple list.
- Deliberate parity skips are whitelisted with decision comments in `tests/test_shadow_parity.py`: `kindle_ru`, `tpr_ru`, `data_classes_ru`, `ru_spelling`, `version_ru`, `dps_example_field`, `dps_meaning_field`, and `backup_dps`.
- Namespace-isolation failure fixed: the C1 helper was renamed to `read_tsv_as_dict_with_different_key_ru`.
- Upstream `tests/gui2/test_main.py` change (`"DPS"` tab) recorded in the `gui2/main.py` registry `watch_for`, because `tests/` is skip_sync and can't hold a registry entry.
- `.github/workflows/anki_release.yml` updated: the retired deconstructor-tarball unzip was replaced with the Generate Deconstructor step (2a had missed it).

## Promote
*Patterns worth turning into guide rules, validators, or archive entries. Done: `archive_improvements.md` §24–§29.*

- §24 `execute_sync.py` P0 `propagate_upstream_deletions`: `Path.unlink()` crashes on gitlink/submodule dirs (EPERM), and `git diff --name-only` without `-z` silently skips non-ASCII paths. Also, `--dry-run` refuses a dirty tree, and `verify_manifest` rejects stale acknowledged blockers.
- §25 Sync tooling reads the wrong tree or ignores registry categories:
  - `test_shadow_cleanup.py` reads `ls-tree HEAD`, so it reports staged deletions as orphans. It also ignores `inspired_by_upstream` and `skip_sync_patterns`.
  - `sync_status.py` infers the stage from which files exist, so it reported "Stage 3" during 2b and again at Stage 4.
  - `validate_registry.py` existence check fails before the pull for repointed upstream paths.
  - prep_report wording "register them" conflicts with the mirror-without-registry policy.
- §26 Subagent lint commands must use literal file paths. sync-fast chained an empty `f=` var after a failing step, which ran `ruff --fix`/`ruff format` across the whole repo, submodules included. Byte-exact repair was needed.
- §27 `tests/` being skip_sync hides three things: pre-range test orphans (36 found manually), upstream tests that hard-code local-extended lists, and shadow-impossible golden tests. 2a must scan `tests/` explicitly.
- §28 Re-verify 2a/2b facts before writing 2c recipes. These were wrong:
  - `submodules_update.yml` reported absent
  - RU kindle nav "dead links" claimed but absent
  - Kindle blocker mapped to a non-existent RU path
  - `skip_sync_patterns` misread as "local keep"
  - D1 "verbatim .gitignore" missed the `.claude/` conflict

  Plan Verify commands must be dry-run when written. These were wrong: the flet version attr, `curl -sI` on a GET route, the `dhamma 1` query, the `show_tbw` count, and `test_kindle_jinja` (has no tests).
- §29 Framework-version migrations (Flet 0.x→1.0) need an AST scan of `ft.*` calls plus pinned-version probes (`uv run --no-project --with flet==1.0.1`). Grep missed instance-method removals and silent renames. Related shell gotcha: zsh `$VAR:x` modifier expansion mangles `git show $SHA:path`, so always write `${SHA}:path`.
- Kamma spec-gate hook blocks all non-kamma edits when any thread dir lacks spec/plan. Draft threads belong in `kamma/drafts/`. This is folded into §28's "Stage 3 environment" note.

## Drop
*Genuine one-offs that do not warrant a process change. State the reason.*

- `stage1.py` exits 1 when triage finds blockers/discuss paths. This is intended behaviour, documented in the session 1 note.
- "Local commits since OLD" counts are misleading because the file-based sync means `be49bffe2c2c` is not an ancestor of HEAD. This is inherent to the sync model, and nothing acts on the count.
- Root `typescript` (6.5 MB `script(1)` recording) surfaced because upstream `.gitignore` stopped ignoring it. It was a stray personal file and has been deleted.
- `data_classes.py` / `models.py` `--3way` conflicts: one-time collisions between upstream permalink/import changes and local `show_ru_data`/`or_` additions. They were resolved by hand.
- Upstream configger auto-added `dictionary: show_tbw = no` to `config.ini` on import. That is the expected upstream behaviour for a new key.

## Open after finalize (not blockers to acceptance)

- `docs_rus/how_to_cite.md` does not exist yet. The RU webapp/GoldenDict «Как цитировать» links (`https://devamitta.github.io/dpd.rus/how_to_cite/`) 404 until the Docs Track translates it (queue line 22).
- Session 9 RU link edits are uncommitted: `exporter/webapp/ru_templates/{dpd_headword,home}.html` and `exporter/goldendict/ru_components/javascript/ru_feedback_template.js`.
- `.git/config` still has a stale `[submodule "resources/deconstructor_output"]` section. It is harmless; remove it on user request.
- Pre-existing failures not caused by this sync: `sutta_central_exporter_ru` parity, and `tests/test_dps_kindle_rpd.py` (4 failing tests that import absent `render_rpd_*`).
