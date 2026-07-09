# Skill/Guide Improvement Suggestions — Sync Merge Scope

> Captured during Stage 2b of the 2026-07-09 upstream sync, at the user's request.
> A separate future task will apply these to the sync skill/guide. Do NOT act on this
> during the current sync run beyond what the 2b resolutions already record.

## The problem observed

Stage 2a analysis treated several **unregistered upstream files** as if they had
"local divergences worth preserving," and surfaced them as discuss items (D9
`exporter/analysis/`, D10 `tools/ai_antigravity_cli.py`, D11 `docs/pics/kindle/*.png`
and `scripts/*/README.md`, D12 `audio/bhashini/*`, D13 `pdf_test.yml`). The user
corrected this: those paths are not registered, so they are simply pulled and
overwritten — no analysis, no preservation, no discussion.

Root cause: a "local-commit sweep" (`git log --since <last-sync> --name-only`
intersected with changed upstream paths) was used to *preserve* every local edit it
found, instead of only using it to *detect files that should have been registered but
weren't*.

## The rule that must be crisp in the guide

**The registry is the sole source of truth for what gets merged.** The decision is
binary, per path:

1. **Registered as a maintained local special** — appears in `registry.json` under
   `modified_upstream_files`, `unique_paths`, `inspired_by_upstream`, `russian_copies`,
   `sbs_copies`, `dps_copies`, or `tamil_copies`.
   → **3-way merge.** Layer local changes on top of upstream; preserve local content.

2. **Not registered** — everything else.
   → **Pull and overwrite verbatim.** Zero permitted local divergence. No divergence
   analysis. No discuss item. If the checkout would clobber a local edit, that edit was
   never sanctioned; discard it.

There is no third "found a local edit, so preserve it" category. A genuine local edit
in an unregistered file means one of two things:
- it should be a registered special → register it (this is the ONLY correct use of the
  local-commit sweep; e.g. `tools/ai_models.json` → D8), or
- it should not exist → overwrite it (e.g. the `example_bolding.py` crash fix — if
  still valid, PR it upstream, don't keep a local delta).

## Area-specific policies to state explicitly

- **`docs/` is upstream-only, mirrored exactly.** Never register local files under
  `docs/`. The only maintained docs surface is `docs_rus/` (a direct translation of
  `docs/` with the few documented no-translate exceptions). Local files that have crept
  into `docs/` (e.g. `docs/pics/kindle/*.png`) are removed to match upstream unless
  something local references them.
- **`audio/` is always synced with upstream.** No local audio scripts are maintained;
  upstream-deleted audio files are deleted locally to match.
- **`scripts/*` folders are plain upstream sync targets.** Local-only READMEs or helper
  files added into upstream script dirs are removed, not registered, unless they are a
  deliberate registered `unique_paths` fork feature.
- **`AGENTS.md` merge is scope-filtered.** Only merge upstream rule additions that
  govern files/areas we actually maintain (registered specials) or our own sync process.
  Do not adopt upstream-only workflow rules for work we do not perform. This flows from
  the project mission (sync + shadows/translations), which should be stated in
  `kamma/project.md` and referenced from the sync guide.

## Suggested guide edits (for the future task)

1. Add a **"Merge scope vs. verbatim pull"** subsection to the sync guide's Stage 2
   classification section stating the binary rule above, with the registry categories
   enumerated.
2. Rewrite the local-commit sweep's documented purpose: it detects **missing
   registrations**, not divergences to preserve. Output should be phrased as "these
   unregistered files have local edits — register them or let them be overwritten," not
   "preserve these."
3. Add the four area-specific policies (`docs/`, `audio/`, `scripts/*`, `AGENTS.md`) as
   explicit bullets so an agent does not re-derive them per sync.
4. Consider a Stage 2a guardrail: before flagging any path as discuss/preserve, assert
   it is present in the registry; if not, auto-classify as verbatim-pull (or as a
   registration candidate) and do not open a discuss item.
5. Restate in `kamma/project.md` the one-line mission so `AGENTS.md` scope-filtering has
   an anchor: "We keep upstream sync and maintain localized shadows/translations; we do
   not perform upstream's full development workflow."
