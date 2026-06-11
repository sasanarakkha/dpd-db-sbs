# Plan: Historical Sweep of Upstream-Deleted Leftovers

Thread: `20260611_upstream_deletion_sweep`
Spec: `spec.md` (same folder). Follow-up from
`kamma/threads/20260610_sync_skill_improvements/review.md`.

## Architecture Decisions

- **Throwaway tooling, not a product.** The sweep script lives in
  `temp/upstream_deletion_sweep/sweep.py` and is deleted before thread close
  (user decision). It is NOT added to `kamma/upstream_sync/scripts/`, gets no
  registry/SMD entry, and gets no permanent test in `tests/` — this is a
  deliberate deviation from the TDD lifecycle, justified because the script's
  entire output (the candidate list) is empirically cross-checked against the
  planning probe (97 raw candidates) and every downstream artifact
  (registry edits, deletions) is verified by existing validators.
- **Baseline = accepted sync SHA** `0ea5883380f56b682cf8574043afb8e66cca3260`
  read from `kamma/upstream_sync/accepted_sync.json` at runtime — never
  `upstream/main` HEAD, so the sweep cannot pre-empt the next sync.
- **Registry filtering reuses `registry_helper.py`** (`load_registry` /
  typed accessors) from `kamma/upstream_sync/scripts/` — no duplicated
  registry-parsing logic. Filtering matches exact paths AND directory prefixes
  (registry contains both forms).
- **Deletions are plain filesystem deletes** (`Path.unlink`) of tracked files
  so they appear as *unstaged* deletions in `git status` — NOT `git rm`,
  which would stage them. Nothing is staged or committed.
- **Classification errs toward keep.** Any candidate with a plausible local
  reference (or dynamic-load suspicion, e.g. `gui2/data/*.json`) is kept and
  registered in `unique_paths` rather than deleted. `docs/` leftovers are
  always delete candidates (upstream-only tree).
- **Docs scope is removal/alignment only.** The propagation note at
  `kamma/upstream_sync/guide.md:216` stays; the deletion-blocker + ack-file
  flow in `prep_analyzer.py`/`sync_runtime.py` is untouched (user decision).

## Phase 1: Sweep script and raw candidate report

- [ ] 1.1 Write `temp/upstream_deletion_sweep/sweep.py` (one-sentence purpose
      docstring, pathlib, modern type hints). It must:
      - read the baseline SHA from `kamma/upstream_sync/accepted_sync.json`;
      - compute `upstream_tree` (`git ls-tree -r --name-only <sha>`),
        `ever_deleted_upstream` (`git log --diff-filter=D --name-only
        --pretty=format: <sha>`), `local_tracked` (`git ls-files -z`, so
        paths with spaces/unicode like
        `shared_data/abbreviations/Pāli canon editions.docx` survive);
      - compute raw candidates = `local_tracked ∩ ever_deleted_upstream −
        upstream_tree`;
      - load `kamma/upstream_sync/registry.json` via `registry_helper.py` and
        subtract every path registered in ANY category
        (`modified_upstream_files`, `russian_copies`, `sbs_copies`,
        `dps_copies`, `tamil_copies`, `inspired_by_upstream`, `unique_paths`,
        `no_sync_files`), matching exact paths and directory prefixes;
      - write `kamma/threads/20260611_upstream_deletion_sweep/sweep_report.md`
        with two sections: "Filtered by registry" (path + matching category)
        and "Needs classification" (path + upstream commit that deleted it,
        via `git log --diff-filter=D -1 --format=%h -- <path> <sha>`).
      → verify: `uv run python temp/upstream_deletion_sweep/sweep.py` exits 0;
        raw candidate count is exactly 97 (cross-check against the planning
        probe); every "Filtered by registry" line names a real registry
        category; `uv run ruff check --fix` + `ruff format` + `pyright` +
        pyrefly clean on `sweep.py`.

## Phase 2: Classification and apply

- [ ] 2.1 Classify every "Needs classification" candidate. For each path, run
      `rg -l --fixed-strings "<basename>"` (and for `.py` files also the
      module name as an import string) across the repo, excluding
      `scripts/archive/`, `scripts/dps_archive/`, `archive/`, `temp/`,
      `kamma/threads/`, and the candidate itself. Record in
      `sweep_report.md` per file: classification (`keep` / `delete`), evidence
      (reference hits or "none"), and rationale. Dynamic-data suspicion
      (e.g. `gui2/data/*.json` written at runtime) ⇒ `keep`. Anything under
      `docs/` ⇒ `delete`.
      → verify: every "Needs classification" path in `sweep_report.md` has a
        classification + evidence line; zero unclassified rows remain.
- [ ] 2.2 Register all `keep` files in `registry.json` `unique_paths`
      (no SMD entry required for `unique_paths` per
      `kamma/upstream_sync/guide.md` Registry Categories table).
      → verify: `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
        exits 0 and
        `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`
        exits 0.
- [ ] 2.3 Delete all `delete` files via `Path.unlink` (filesystem delete,
      NOT `git rm`). List every deleted path in `sweep_report.md`.
      → verify: `git status --porcelain` shows each deleted path as an
        unstaged ` D` entry and nothing staged; re-running
        `uv run python temp/upstream_deletion_sweep/sweep.py` reports zero
        "Needs classification" candidates.
- [ ] 2.4 Phase sanity check: confirm nothing load-bearing broke.
      → verify: `uv run ruff check tools/ scripts/ db/ exporter/
        --select F821,E999 --quiet` exits 0;
        `uv run pytest tests/test_shadow_cleanup.py -v` passes.

## Phase 3: Docs retirement, cleanup, and close-out

- [ ] 3.1 Sweep `kamma/upstream_sync/guide.md`, `kamma/upstream_sync/README.md`,
      and `kamma/upstream_sync/templates/*.md` for any remaining wording that
      implies a manual verify-then-remove pass for upstream-deleted files;
      remove or align it with the "deletions propagate" reality. Keep the
      propagation note (guide.md:216) and the deletion-blocker/ack-file
      instructions (out of scope) intact.
      → verify: `rg -n -i "verify.?then.?remove" kamma/upstream_sync/` returns
        no results (or only the intentional propagation note in guide.md);
        `uv run pytest tests/test_upstream_sync_docs_policy.py -v` passes.
- [ ] 3.2 Delete `temp/upstream_deletion_sweep/` (script has fulfilled its
      purpose; findings live in `sweep_report.md`).
      → verify: `git status --short` shows no `temp/` entries and no new
        root-level untracked files.
- [ ] 3.3 Final report + draft commit message
      (`chore(sync): remove upstream-deleted leftovers, register keepers`),
      explicitly excluding dirty `resources/*` submodule pointers from the
      proposed commit scope. User commits manually.
      → verify: summary lists counts (filtered / kept / deleted), all
        validators green, deletions still unstaged for user review.
