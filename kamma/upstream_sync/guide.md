# Upstream Sync Protocol

> This is the canonical protocol for running `/update-upstream`. For per-file merge
> guidance, see `smd/index.md`. For accumulated lessons, see `archive_improvements.md`.

All local sync-process documentation must stay inside `kamma/upstream_sync/`. The upstream-owned
`docs/` tree is not a place for local sync-process instructions.

---

## Iron Rule

**When a shadow file breaks after sync, the ONLY permitted fix is:**
1. Open the upstream source file.
2. See exactly how upstream implements the broken functionality.
3. Copy that exact solution into the shadow.
4. Re-apply ONLY the local changes listed in `smd/` for that file.

**FORBIDDEN:**
- Workarounds, patches, or logic not present in the upstream source.
- Alternative libraries or imports not used by upstream.
- `try/except` blocks that paper over the real issue.
- Restructuring the file differently from upstream.

**The upstream sources are correct and carefully tested.
A broken shadow always means the sync is incomplete or inaccurate — not that the source has a bug.**

---

## Session Management

Each stage runs in its own session. At the end of a stage:
1. Save all outputs to the thread folder.
2. Update `handoff.md` with the current status and what comes next.
3. Prepare the commit (if applicable) and present it to the user.
4. Tell the user: "Restart the session. Next time, say: [exact prompt]."

**Within Stage 3**, if the plan has many items, split across sessions. Track progress by item ID (e.g., "completed through A8, next is A9") in `handoff.md`. Similarly, **within Stage 4.B**, if there are many files to translate, split after every 5 files.

**Hard Stop Triggers (mandatory session split):**
- After completing any full Stage (1, 2, 3, 4, or 5) — always split.
- After every 5 implementation items in Stage 3 — split.
- After every 5 translation files in Stage 4.B — split.
- If context feels stale or responses feel repetitive — split immediately.

Hard stop procedure: update `handoff.md` → state the exact restart prompt → STOP. Do not continue in the same session.

**Pre-Authorized Commands:**
All commands listed in this guide (`uv run`, `grep`, `find`, `git diff`, `git log`, `ruff`, `pytest`, `python temp/`) are pre-authorized for the entire sync session. Write all ad-hoc logic to `temp/<name>.py` and run via `uv run python temp/<name>.py`. Never use inline `python -c "..."`. Delete temp files when done.

---

## Model Switch Protocol

**MANDATORY MODEL SWITCH TRIGGERS — never skip these:**

| Transition | Recommended model | Instruction to give user |
|---|---|---|
| End of Stage 1, before Stage 2 | PRO (smart) | "Please switch to PRO model. Restart. Next prompt: [exact prompt]." |
| End of Stage 2, before Stage 3 | FAST (execution) | "Please switch to FAST model. Restart. Next prompt: [exact prompt]." |
| End of Stage 3, before Stage 4 | PRO (smart) | "Please switch to PRO model. Restart. Next prompt: [exact prompt]." |
| End of Stage 4.A, before Stage 4.B | FAST (execution) | "Please switch to FAST model. Restart. Next prompt: [exact prompt]." |

- **Stage 1 (Prep)** — any model; lightweight validation and scripted analysis.
- **Stage 2 (Analysis)** — PRO model; strategic planning, resolve `discuss` flags, draft `dynamic_plan.md`.
- **Stage 3 (Execution)** — FAST model; mechanical implementation item-by-item per the plan.
- **Stage 4.A (Docs Analysis)** — PRO model; read parity report, sample existing translations for terminology, draft `docs_translation_plan.md`.
- **Stage 4.B (Docs Translation)** — FAST model; execute `docs_translation_plan.md` file-by-file — translate or update each file, then commit.
- **Stage 5 (Verification + After-sync)** — any model; manual verification, update `accepted_sync.json`.

**Handoff quality gate (PRO → FAST, Stage 2 → 3):** Before switching to FAST for Stage 3, PRO must verify that `dynamic_plan.md` passes this test: *"Could a mechanical executor complete every item without reading any file not explicitly referenced in the plan?"* If the answer is no, expand the plan before handing off. FAST must never be asked to analyze, judge, or discover — only execute.

**Handoff quality gate (PRO → FAST, Stage 4.A → 4.B):** Before switching to FAST for Stage 4.B, PRO must verify that `docs_translation_plan.md` includes: (1) a terminology glossary, (2) per-file instructions specifying source path, target path, and whether it's a full translation or a targeted update, (3) explicit rules for what to keep untranslated (Pali terms, product names, image paths, code blocks, URLs). FAST must never decide what to translate — only execute the plan.

**The agent MUST stop at the end of each Stage and explicitly state the model switch instruction before ending the session. Never begin Stage 2, 3, 4, or 5 in the same session that completed the previous stage.**

---

## The 5-Stage Sync Workflow

### Stage 1: Prep (Factual Analysis)
**Goal**: Establish a baseline, validate the environment, and identify what changed upstream.
<!-- !TODO backup dps first! scripts/backup/backup_dps.py and git add with message "data update"-->
0. **Pre-sync Shadow Health Check (MANDATORY GATE)**:
   - Run `uv run python3 tests/check_shadow_modifications.py`
   - The output must be **clean** (zero modifications reported) before continuing.
   - If drift is found: **STOP**. Fix the drifted shadow files first. Commit the fix separately
     (message: `#pre-sync: fix shadow drift in <filenames>`). Only then proceed to step 1.
   - Rationale: accumulated shadow drift that slips through one sync becomes a multi-hour
     remediation in the next sync (see Stage 3.5 in the April 2026 sync thread).
1. **Environmental Validation**:
   - Run `git fetch upstream` — always fetch before any analysis. No need to search for new commits manually; the scripts derive the range from `accepted_sync.json`.
   - Run `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
   - Run `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`
   - Ensure `kamma/upstream_sync/accepted_sync.json` points at the last accepted upstream sync.
2. **Factual Diff**:
   - Run `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>`.
   - Generate `prep_report.md` and `prep_manifest.json` from the explicit upstream range in `accepted_sync.json`.
   - Identify all modified, added, and deleted upstream files relative to the registry.
3. **Automated Pull**:
   - Perform the automated sync by running `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>`.
   - Review and add any run-specific exclusions to `<thread_dir>/run_exclusions.txt` before execution if needed.
   - (Commit 1 gate). Message format: `#sync: upstream pull <from>..<to>, <N> files, YYYY-MM-DD`
   - **Staging rule:** NEVER use `git add -A -- <file list>` — gitignore'd paths will trigger errors. Always use `git add .` which respects `.gitignore` automatically. If you must stage selectively, pre-filter with `git add <file>` one path at a time or check first with `git check-ignore -v <path>`.

### Stage 2: Analysis (Strategic Planning)
**Goal**: Determine how to integrate upstream changes into localized files.

1. **Dynamic Planning**:
   - Create `dynamic_plan.md` in the thread folder.
   - Use `prep_manifest.json` as the factual source of changed upstream files and mapped local destinations.
   - For every modified upstream file mapped to a shadow/inspired copy, define the merge strategy.
   - **Plan quality requirement (MANDATORY before handing off to Stage 3):** `dynamic_plan.md` must be self-contained enough for a mechanical executor with zero context and zero judgment. Every item must include:
     - Exact file path(s) to edit.
     - Exact anchor string or line reference to locate the change point.
     - Exact code to insert, replace, or delete (literal, not paraphrased).
     - Verification command to confirm the change landed correctly.
   - If any item says "figure out X", "determine Y", or "check Z" — the plan is incomplete. PRO must resolve those before handing off.
2. **Discussion Flags**:
   - Check `discuss` flags in `registry.json`. If `true`, resolve with the user before planning.
   - **Discussion flow**: Discuss each flagged item in chat, one at a time. Do not ask the user to edit any file. Once a decision is reached, mark the item `RESOLVED` in `dynamic_plan.md` with the agreed strategy. Only then proceed.
3. **Draft Plan Review**:
   - Present the `dynamic_plan.md` to the user for approval. Say: "Please review and reply with proceed / skip / or any objection for each item."

### Stage 3: Execution & Verification (Implementation)
**Goal**: Apply changes, verify integrity, and clean up.

1. **Implementation**:
   - Execute `dynamic_plan.md` item-by-item following the **Iron Rule**.
2. **Verification**:
   - Run `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v` (Sync-related suites).
   - Run `uv run python3 tests/check_shadow_modifications.py`.
   - Run `uv run python tests/smoke_test_sync.py` — full pipeline smoke test (mini DB + all exporters + webapp + GUI).
   - Perform manual verification (GoldenDict/webapp).
3. **Cleanup**:
   - Run `uv run python3 tests/test_shadow_cleanup.py --folder <folder> [--apply]` to review or archive orphans.
   - Update `registry.json` and `smd/` to reflect the new state.
   - Run `uv run python tests/smoke_test_sync.py` — re-run after orphan archiving to confirm nothing was broken.
4. **Template Audit** (every sync):
   - For each local template dir (`ru_components/templates/`, `sbs_templates/`, `ru_templates/`):
     - List all `.jinja` and `.html` files.
     - For each file, `grep -r` the filename across the entire repo (`.py`, `.jinja`, `.html`, `.js`).
     - Any template with **zero references** is a dead template candidate.
   - For each dead candidate, check if upstream has a corresponding template in its own `templates/` dir:
     - If upstream **does not** have an equivalent → the file is likely a local artefact; delete or archive it.
     - If upstream **does** have an equivalent → investigate: was it replaced by inline rendering? If so, delete the local dead copy.
   - Document findings and decisions in `handoff.md` before deleting anything.

### Stage 4: Docs Translation Parity (Analysis → Execution)
**Goal**: Ensure `docs_rus/` is a complete, up-to-date Russian translation of `docs/`.

`docs/` is upstream-owned and accepted verbatim during sync. `docs_rus/` is the maintained Russian translation — every file in `docs/` must have a counterpart in `docs_rus/` (except `docs_rus/dpd_rus.md`, `docs_rus/contributing/rus_collaboration.md`, and `docs_rus/technical/dpd_headwords_table_ru.md` which are local-only). Never add local content to `docs/`.

**No-translate files (HTML redirect pattern):** Some `docs/` files do not need Russian translation (e.g. `changelog.md` — mostly Pāḷi data and GitHub issue numbers). For these, the canonical approach is an HTML meta-redirect file: `docs_rus/file.md` redirects to an external URL. This satisfies the parity check (file exists) and MkDocs correctly handles it during build. Add such files to `NO_TRANSLATE` in `check_docs_parity.py` to skip staleness checks.

**Stage 4.A — Analysis (PRO model)**:
1. Run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir>` → produces `docs_parity_report.md`.
2. Read 3–5 existing `docs_rus/` files to build a terminology glossary (key EN → RU mappings specific to DPD: headword, inflection template, root family, deconstructor, lookup, etc.).
3. For each stale file listed in the report: run `git diff <accepted_sha> HEAD -- docs/<file>` to capture the exact diff.
4. Write `docs_translation_plan.md` in the thread folder containing:
   - **Terminology glossary** — EN → RU pairs extracted from existing translations.
   - **Translation rules** — keep Pali terms as-is; keep image paths, code blocks, and URLs unchanged; translate heading text and alt text; keep HTML anchor IDs unchanged.
   - **Per-file tasks** — for each missing file: source path, target path, "full translation". For each stale file: source path, target path, the exact diff, "update only changed sections".
5. Present `docs_translation_plan.md` to user for approval.

**Stage 4.B — Translation (FAST model)**:
1. Read `docs_translation_plan.md` — do not read any other file not referenced there.
2. Execute file-by-file in order: missing files first (create + translate), stale files second (targeted update).
3. After all files are written, update `mkdocs_ru.yaml` nav if any new files were added.
4. Prepare commit: `#docs: translate/update docs_rus/ for sync <from>..<to>`.

### Stage 5: Verification & After-sync
**Goal**: Final human verification and close out the sync record.

1. **Full manual verification**
   - Ask user to verify everything and stay back for feedback. After correcting it, do not proceed until user explicitly says "all is good, proceed."
2. **After sync**
   - Update `accepted_sync.json` only after the sync is accepted and verified.
   - Review the temporary `new_improvements.md`, promote accepted items to `archive_improvements.md`, and delete the file.

---

## Registry Categories

| Category | Description |
|---|---|
| `modified_upstream_files` | Upstream files where this fork diverges. Requires manual porting of new features. |
| `russian_copies` | Shadow files mirroring upstream with Russian additions. Strict parity enforced. |
| `sbs_copies` | Shadow files mirroring upstream with SBS additions. Strict parity enforced. |
| `dps_copies` | Shadow files mirroring upstream with DPS additions. Strict parity enforced. |
| `tamil_copies` | Shadow files mirroring upstream with Tamil additions. Strict parity enforced. Primary shadow: `db/tpd/tpd_to_lookup.py` → `db/epd/epd_to_lookup.py`. |
| `inspired_by_upstream` | Local files derived from upstream but structurally diverged. No strict parity; backport useful improvements only. |
| `unique_paths` | Fork-only files/dirs. Never synced. |
| `no_sync_files` | Infrastructure files that must never be overwritten. |
| `skip_sync_patterns` | Glob patterns ignored during sync scanning. |

---

## SMD (Sync Metadata) Structure

Merge rules are no longer in a monolithic file. See the `kamma/upstream_sync/smd/` directory:
- `index.md`: Entry point and directory of all entries.
- `db.md`, `exporter.md`, `gui.md`, `scripts.md`, `tools.md`: Domain-specific merge rules.

Every entry must define a `Sync Rule` (`PORT`, `MIRROR_EXACTLY`, `PRESERVE`, `DISCUSS`, or `inspired_only`).

---

## Sync Scope

This fork supports **four locales**: Russian (`_ru`), SBS (`_sbs`), DPS (`_dps`), and Tamil (`_ta`).
**ALL four locales are always in scope.** "Pre-existing" namespace isolation failures, ruff errors,
or test failures in ANY locale are NOT acceptable and MUST be fixed, not deferred.

- Shadow copy failures (ruff errors, unused imports, dead code) in `*_ru.py`, `*_sbs.py`, `*_dps.py`
  files are in scope regardless of when they were introduced.
- Tamil symbols (`_ta`, `ta_`, etc.) in `_dps` files are valid and the test enforces them — fix
  violations, never whitelist them.

---

## Symbol Naming Policy

Enforced via `tests/test_namespace_isolation.py`:

1. **Tier 1 — Identical to Upstream**: No locale marker. Keep upstream name exactly.
2. **Tier 2 — Modified from Upstream**: Locale suffix only (`_ru`, `_sbs`, `_dps`, or `_ta`). Never use both a prefix and a suffix.
3. **Tier 3 — New (no upstream counterpart)**: Use descriptive name + locale suffix.
4. **HTML IDs**: Always prefix with locale (`ru_`, `sbs_`, `dps_`, `ta_`).
5. **Intrinsic semantic markers** (e.g., `RpdData`, `TpdData`): allowed without added suffix — listed
   in `EXCEPTIONS` in `test_namespace_isolation.py`. Do not add to exceptions without clear justification.

**DPS files (`*_dps.py`)** may contain Tamil-specific symbols with `_ta` marker — the test accepts
`_dps`, `_ru`, `_sbs`, and `_ta` as valid markers for these files.

**Locale flags** (in `config.ini [dictionary]`): `show_ru_data`, `show_sbs_data`, `show_ta_data` — each threads through the same call chain via `main_sbs.py`.

---

## Discussion Flag Protocol

If a file has `discuss: true` in `registry.json`:
1. **STOP**. Do not modify.
2. Present the relevant upstream diff from the active Prep range and the `discuss_reason` to the user.
3. Wait for explicit approval before proceeding.

---

## Sync State Artifacts

- `accepted_sync.json`: durable record of the last accepted upstream SHA, date, and ref.
- `prep_manifest.json`: Stage 1 machine-readable snapshot of the active upstream range.

These files support the 3-stage workflow. They are not a fourth stage.
