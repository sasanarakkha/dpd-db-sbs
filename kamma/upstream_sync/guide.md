# Upstream Sync Protocol

> This is the canonical protocol for running `/update-upstream`. For per-file merge
> guidance, see `smd/index.md`. For accumulated lessons, see `archive_improvements.md`.

All local sync-process documentation must stay inside `kamma/upstream_sync/`. The upstream-owned
`docs/` tree is not a place for local sync-process instructions.

## Pre-Sync Entrypoint

Run `scripts/cl_dps/dpd-kamma-sync` before Stage 1. This is the only sync-related Bash entrypoint.
It backs up DPS localization tables, commits only the backup TSV changes as `backup dps data`, and
creates the Kamma thread through `kamma/upstream_sync/scripts/init_sync_thread.py`.

Git commit/push policy is inherited from the global rules.

After that wrapper finishes, all sync work must use the Python scripts in
`kamma/upstream_sync/scripts/` and the 5-stage workflow below. Do not use legacy shell sync wrappers.

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

Each stage runs in its own fresh session. The chat history is never the source of truth; the thread
folder is. At every hard stop, the current agent must save enough state for the next fresh session to
continue from files only.

**Prefer frequent restarts.** Shorter sessions are better. Starting a fresh session is cheap; a degraded context window is expensive and causes errors. Bias toward stopping early and handing off rather than completing "one more task" in a heavy session.

**Required hard-stop artifacts:**
- `<thread_dir>/handoff.md`
- The current stage output:
  - Stage 1: `prep_report.md` and `prep_manifest.json`
  - Stage 2: `dynamic_plan.md`
  - Stage 3: updated execution status and command/test evidence in `handoff.md`
  - Stage 4.A: `docs_parity_report.md` and `docs_translation_plan.md`
  - Stage 4.B: translation execution status in `handoff.md`
  - Stage 5: verification/finalization notes in `handoff.md`
- `<thread_dir>/stage_state.json` only when a script or later session needs machine-readable state.

**`handoff.md` must include:**
- Current stage and owner model (`FAST` or `ADVANCED`).
- Completed work.
- Exact commands already run.
- Exact outputs or failures summarized.
- Files changed.
- Open decisions.
- Errors, issues, and repeated mistakes.
- Next model to use.
- Exact restart prompt for a fresh session.
- Explicit instruction: "Do not continue in this session."

**Hard Stop Triggers (mandatory fresh-session split):**
- After completing any full Stage (1, 2, 3, 4.A, 4.B, or 5).
- After preparing ANY commit message (Commit 1, 2, 3, or docs). Preparing a Commit is always a session boundary: update `handoff.md` and write a restart prompt naming the exact model and `/kamma:2-do` command before ending.
- When FAST needs analysis, planning, judgment, or conflict resolution.
- When ADVANCED needs mechanical editing, command execution, file copying, formatting, testing, or bulk research.
- After every 5 implementation items in Stage 3.
- After every 5 translation files in Stage 4.B.
- If output is too large, context feels stale, failures repeat, state becomes unclear, or the agent is relying on memory instead of files.

Hard stop procedure: save artifacts -> update `handoff.md` -> state the exact restart prompt and required model -> STOP. Do not continue in the same session.

**Commit-closeout checklist (mandatory after each commit lands):** Before writing the restart prompt, update `handoff.md` Status + Next Action to reflect the commit that just landed, and mark resolved ledger/approval items DONE. A restart prompt written before the handoff is updated causes the next session to re-do already-finished work.

**Context-handoff prompt template** (used when a thread spans sessions for context-size reasons):

```text
Start a fresh session.

Continue upstream sync thread: <thread_dir>.
First read:
1. <thread_dir>/handoff.md
2. kamma/upstream_sync/guide.md
3. <stage-specific file>

Your task:
<exact next task>

Do not perform <forbidden model responsibility>.
Stop if <specific stop condition>.
```

**Pre-Authorized Commands:**
All commands listed in this guide (`uv run`, `rg`, `git diff`, `git log`, `ruff`, `pytest`, `python temp/`) are pre-authorized for the entire sync session. Use `rg` for repo searches. Write all ad-hoc logic to `temp/<name>.py` and run via `uv run python temp/<name>.py`. Never use inline `python -c "..."`. Delete temp files when done.

---

## Model Responsibility Contract

The sync workflow is split by responsibility, not convenience.

**FAST model owns mechanical work only:**
- Run commands and scripted checks.
- Read files named by the protocol or current plan.
- Generate factual reports.
- Apply literal edits from an approved plan.
- Run formatting and tests.
- Record exact failures.

FAST must stop when it needs to decide strategy, classify risk, interpret ambiguous failures, resolve conflicts, choose between alternatives, or edit beyond the literal plan.

**ADVANCED model owns analysis and planning only:**
- Interpret FAST outputs.
- Classify risk and impact.
- Resolve `discuss` items with the user.
- Decide port/preserve/skip/translate strategy.
- Write self-contained execution plans.
- Review evidence and decide whether the sync is ready for user verification.

ADVANCED must stop when mechanical work is needed: broad file reading, command execution, copying files, applying merges, formatting, testing, or bulk translation.

**Boundary examples:**
- FAST finds a missing anchor in `dynamic_plan.md` -> stop and hand off to ADVANCED.
- FAST sees a test failure that is not explicitly covered by the plan -> stop and hand off to ADVANCED.
- ADVANCED decides a shadow must be updated -> write exact instructions, then stop and hand off to FAST.
- ADVANCED sees docs need translation -> write `docs_translation_plan.md`, then stop and hand off to FAST.

**Subagent Dispatch (Primary Path):**

The orchestrating session (Opus / ADVANCED) dispatches mechanical work to the `sync-fast` subagent (`.claude/agents/sync-fast.md`):
- **Stage 1** (entire stage): dispatch to `sync-fast` after thread init.
- **Stage 3** (batches of ≤5 plan items): dispatch sequential batches to `sync-fast`.
- **Stage 4.B** (entire docs translation stage): dispatch to `sync-fast`.

All user-facing gates remain in the orchestrating session: Stage 2 approval, Stage 4.A discussion, commit gates, and Stage 5 acceptance. Subagent work is verified from files — read `handoff.md` and stage outputs after each dispatch; subagent self-reports are not trusted.

**Stage ownership:**
- **Stage 1 (Prep)** — FAST; factual collection only.
- **Stage 2 (Analysis)** — ADVANCED; strategic planning, resolve `discuss` flags, draft `dynamic_plan.md`.
- **Stage 3 (Execution)** — FAST; mechanical implementation item-by-item per the plan.
- **Stage 4.A (Docs Analysis)** — ADVANCED; read FAST outputs, decide terminology and translation strategy, draft `docs_translation_plan.md`.
- **Stage 4.B (Docs Translation)** — FAST; execute `docs_translation_plan.md` file-by-file — translate or update each file, then prepare the commit message.
- **Stage 5 (Verification + After-sync)** — ADVANCED for acceptance decisions; hand off to FAST for any mechanical finalization.

**Handoff quality gate (ADVANCED -> FAST, Stage 2 -> 3):** Before switching to FAST for Stage 3, ADVANCED must verify that `dynamic_plan.md` passes this test: *"Could a mechanical executor complete every item without reading any file not explicitly referenced in the plan?"* If the answer is no, expand the plan before handing off. FAST must never be asked to analyze, judge, or discover — only execute.

**Handoff quality gate (ADVANCED -> FAST, Stage 4.A -> 4.B):** Before switching to FAST for Stage 4.B, ADVANCED must verify that `docs_translation_plan.md` includes: (1) a terminology glossary, (2) per-file instructions specifying source path, target path, and whether it is a full translation or a targeted update, (3) explicit rules for what to keep untranslated (Pali terms, product names, image paths, code blocks, URLs). FAST must never decide what to translate — only execute the plan.

**The agent MUST stop at the end of each Stage and explicitly write the handoff note before ending the session. Never begin the next stage in the same session that completed the previous stage.**

---

## The 5-Stage Sync Workflow

Stage 4 is split into two model-bound substages: ADVANCED analysis and FAST translation execution.

### Stage 1: Prep (FAST Factual Collection)
**Goal**: Establish a baseline, validate the environment, and identify what changed upstream.
**Owner**: FAST only.
**FAST must stop and request ADVANCED if** registry errors need policy interpretation, new files need classification, a `discuss: true` file changed, command output is ambiguous, or it cannot decide whether something is local, upstream-only, skipped, unique, or shadow.
0. **Pre-sync Shadow Health Check (MANDATORY GATE)**:
   - Run `uv run python3 tests/check_shadow_modifications.py`
   - The output must be **clean** (zero modifications reported) before continuing.
   - If drift is found: **STOP**. Inspect the upstream diff and either fix the drifted shadow files first
     (message: `#pre-sync: fix shadow drift in <filenames>`) or, if ADVANCED confirms the change is intentionally irrelevant to the shadow, add an exact entry to `kamma/upstream_sync/reviewed_shadow_noops.json` and rerun the check.
   - A reviewed no-op entry must include the exact `sync_commit`, `source`, `shadow`, full `changed_paths` list, and a concrete `reason`. Do not use `unique_paths` for shadow no-ops.
   - If the user confirms the warning is intentionally a no-op but gives no specific reason, use this reason exactly: "User reviewed and confirmed this upstream change does not need to be ported to the shadow."
   - Rationale: accumulated shadow drift that slips through one sync becomes a multi-hour
     remediation in the next sync (see Stage 3.5 in the April 2026 sync thread).
1. **Environmental Validation**:
   - Run `git fetch upstream` — always fetch before any analysis. No need to search for new commits manually; the scripts derive the range from `accepted_sync.json`.
   - Run `uv run ruff check tools/ scripts/ db/ exporter/ --select F821,E999 --quiet` — catch undefined names and syntax/API breakage before sync work begins.
   - Run `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
   - Run `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`
   - Ensure `kamma/upstream_sync/accepted_sync.json` points at the last accepted upstream sync.
2. **Factual Diff**:
   - Run `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>`.
   - Generate `prep_report.md` and `prep_manifest.json` from the explicit upstream range in `accepted_sync.json`.
   - Identify all modified, added, and deleted upstream files relative to the registry.
   - If `prep_manifest.json.discuss_paths` is non-empty, STOP before `execute_sync.py`.
   - If `prep_manifest.json.needs_classification_paths` is non-empty, those upstream additions have no local collision; register them in `registry.json`/SMD during Stage 2. They do NOT block `execute_sync.py`.
   - `prep_analyzer.py` also performs a full local-tree audit (independent of the commit-range diff) by comparing every git-tracked local file against the upstream tree and full upstream history at the target SHA:
     - If `prep_manifest.json.unregistered_local_paths` is non-empty, those local files have no upstream counterpart (current or historical) and are not covered by any registry category; register them in `registry.json`/SMD during Stage 2 (typically `unique_paths`, or a shadow/inspired category). They do NOT block `execute_sync.py`.
     - If `prep_manifest.json.upstream_deleted_orphans` is non-empty, those local files match a path upstream once had but has since deleted; decide during Stage 2 whether to keep them as an intentional fork divergence (register the decision) or delete them locally to match upstream. They do NOT block `execute_sync.py`.
   - If `prep_manifest.json.blocker_paths` is non-empty, STOP before `execute_sync.py`. Deletion blockers may be acknowledged by creating `<thread_dir>/run_acknowledged_blockers.txt` (one path per line; `#` comments allowed); `verify_manifest` warns but does not block on acknowledged paths. Collision blockers require registry/SMD changes before `execute_sync.py`.
3. **Automated Pull**:
   - Perform the automated sync by running `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>`.
   - Review and add any run-specific exclusions to `<thread_dir>/run_exclusions.txt` before execution if needed.
   - `execute_sync.py` pins `as_upstream` directly to the verified manifest SHA without switching branches.
   - (Commit 1 gate). Message format: `#sync: upstream pull <from>..<to>, <N> files, YYYY-MM-DD`
   - `execute_sync.py <thread_dir>` leaves changes unstaged by default. Review `git diff` before manual staging; use `--stage` only when you intentionally want the script to run `git add .`.
   - **Upstream deletions propagate.** After the exclusion-restore step, `execute_sync.py` runs `propagate_upstream_deletions` which computes `git diff --no-renames --diff-filter=D <last_accepted_sha>..<target_sha>` and removes any resulting candidate that is not in the protected set (shadows, `no_sync_files`, `modified_upstream_files`, `unique_paths`, and run-specific exclusions). Each removal is worktree-only (`Path.unlink`), never staged — it surfaces as an unstaged deletion in `git diff` for human review before Commit 1. Renamed-away files are covered because `--no-renames` decomposes renames into add+delete.
   - **Staging rule:** NEVER use `git add -A -- <file list>` — gitignore'd paths will trigger errors. If you stage all sync changes manually, use `git add .` which respects `.gitignore` automatically. If you must stage selectively, pre-filter with `git add <file>` one path at a time or check first with `git check-ignore -v <path>`.
4. **Fast-path triage (advisory):**
   - After `prep_manifest.json` exists, run `uv run python3 kamma/upstream_sync/scripts/sync_triage.py <thread_dir>`.
   - It prints the fast-path verdict: pass means no entry in `mapped_actions` has a `category` in `modified_upstream_files`, `russian_copies`, `sbs_copies`, `dps_copies`, `tamil_copies`, or `inspired_by_upstream`; `discuss_paths`, `needs_classification_paths`, `blocker_paths`, `unregistered_local_paths`, and `upstream_deleted_orphans` are all empty; and no `changed_upstream_paths` is under `docs/`.
   - If the verdict passes, this sync touches nothing localized: skip Stages 2-4 and go straight to Stage 5 (retrospective + `finalize_accepted_sync.py`) after Commit 1.
   - The triage verdict is advisory only — it never runs Stage 5 or any destructive step automatically. ADVANCED still makes the acceptance decision.

### Stage 2: Analysis (ADVANCED Strategic Planning)
**Goal**: Determine how to integrate upstream changes into localized files.
**Owner**: ADVANCED only.
**ADVANCED must stop and request FAST if** files need to be copied, generated, formatted, tested, translated in bulk, or mechanically edited.

**Stage 2 sub-stage splitting (context safety):** Stage 2 routinely exceeds one session's context. Split it into restartable sub-stages, updating `handoff.md` and writing a restart prompt at each boundary so a fresh session can resume from files alone:
- **2a — Impact assessment:** read `prep_report.md` + `prep_manifest.json`; classify every changed path (port / mirror / preserve / discuss / inspired / skip / docs) in `dynamic_plan.md`, then hard stop. Also classify every path in `unregistered_local_paths` (register in the appropriate registry category) and `upstream_deleted_orphans` (keep-as-divergence or delete-to-match-upstream).
- **2b — Discuss resolution:** resolve each `discuss: true` item with the user one at a time; record each as RESOLVED in `dynamic_plan.md`, then hard stop.
- **2c — Literal plan authoring:** write self-contained per-file instructions (anchors, literal edits, verify commands); split again after each major domain if context grows, then hard stop.
- **2d — Approval gate:** present `dynamic_plan.md` for approval.
A session must be restartable at any sub-stage boundary from files alone — never rely on chat history.

1. **Dynamic Planning**:
   - Create `dynamic_plan.md` in the thread folder.
   - Use `prep_manifest.json` as the factual source of changed upstream files and mapped local destinations.
   - For every modified upstream file mapped to a shadow/inspired copy, define the merge strategy.
   - Use `mapped_actions[].local_target_path` when present for exact shadow/template target paths; use `local_path` only as a backward-compatible fallback.
   - **Plan quality requirement (MANDATORY before handing off to Stage 3):** `dynamic_plan.md` must be self-contained enough for a mechanical executor with zero context and zero judgment. Every item must include:
     - Exact file path(s) to edit.
     - Exact anchor string or line reference to locate the change point.
     - Exact code to insert, replace, or delete (literal, not paraphrased).
     - Verification command to confirm the change landed correctly.
   - If any item says "figure out X", "determine Y", or "check Z" — the plan is incomplete. ADVANCED must resolve those before handing off.
   - **Coupled `.jinja` template pre-registration (MANDATORY):** For every Python shadow in the plan, check `registry.json` for a coupled `.jinja` template (same base name, different extension). If one is found, pre-register the coupled .jinja template in `registry.json` and add it to the plan. Jinja templates silently break when their paired Python file is updated without them.
   - **Union-type propagation (MANDATORY):** When an upstream type or union changes (e.g., a `TypeAlias`, `Literal`, or `TypedDict` field), propagate the change to ALL sibling localized data classes (`_ru`, `_sbs`, `_dps`, `_ta`). Applying the change to only one sibling silently breaks the others.
   - **Shadow/inspired refactor porting check (MANDATORY when upstream change is structural):** For every upstream file in the dynamic plan whose diff shows structural refactoring — type hint modernisation, `os` → `pathlib`, `print()` / `rich.print()` → `pr.*`, dead code removal, method signature cleanup, or similar quality improvements — check `registry.json` for registered shadow copies (`russian_copies`, `sbs_copies`, `dps_copies`, `tamil_copies`) and `inspired_by_upstream` entries with that file as counterpart. If any exist, the `dynamic_plan.md` item for each copy must include those structural changes in addition to any feature change. Do not port a feature change in isolation when the upstream source was also structurally improved in the same commit range.
2. **Discussion Flags**:
   - Check `discuss` flags in `registry.json`. If `true`, resolve with the user before planning.
   - **Discussion flow**: Discuss each flagged item in chat, one at a time. Do not ask the user to edit any file. Once a decision is reached, mark the item `RESOLVED` in `dynamic_plan.md` with the agreed strategy. Only then proceed.
3. **Draft Plan Review**:
   - Present the `dynamic_plan.md` to the user for approval. Say: "Please review and reply with proceed / skip / or any objection for each item."

**Shadow category rule**: one local shadow path may appear in exactly one registry category. `dps_copies` is the single category for mixed/shared fork shadows, including files that combine Russian, SBS, Tamil, or general DPS behavior. Do not duplicate a DPS shadow into `russian_copies`, `sbs_copies`, or `tamil_copies`.

### Stage 3: Execution & Verification (FAST Implementation)
**Goal**: Apply changes, verify integrity, and clean up.
**Owner**: FAST only.
**FAST must stop and request ADVANCED if** a plan item is incomplete, an expected anchor is missing, a merge conflict requires judgment, a test failure is not covered by the plan, or it believes a different implementation would be better.

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
     - For each file, use `rg` to search the filename across the entire repo (`.py`, `.jinja`, `.html`, `.js`).
     - Any template with **zero references** is a dead template candidate.
   - For each dead candidate, check if upstream has a corresponding template in its own `templates/` dir:
     - If upstream **does not** have an equivalent → the file is likely a local artefact; delete or archive it.
     - If upstream **does** have an equivalent → investigate: was it replaced by inline rendering? If so, delete the local dead copy.
   - Document findings and decisions in `handoff.md` before deleting anything.

### Stage 4: Docs Translation Parity (Async Queue)
**Goal**: Track `docs/` changes that need Russian translation without blocking the code sync.

**Stage 4 is decoupled from the code sync.** During Stage 3, FAST appends any changed `docs/`
paths to `kamma/upstream_sync/docs_translation_queue.md` (one unchecked item per path). The
code sync commit does **not** block on translation — the queue is drained in a separate session.
ADVANCED reviews the queue and assigns a strategy (full translation, targeted update, or
no-translate redirect); FAST executes translations and checks items off.

See the queue file for pending items: `kamma/upstream_sync/docs_translation_queue.md`.

**Original goal (still applies when draining the queue):** Ensure `docs_rus/` is a complete, up-to-date Russian translation of `docs/`.

`docs/` is upstream-owned and accepted verbatim during sync. `docs_rus/` is the maintained Russian translation — every file in `docs/` must have a counterpart in `docs_rus/` (except `docs_rus/dpd_rus.md`, `docs_rus/contributing/rus_collaboration.md`, and `docs_rus/technical/dpd_headwords_table_ru.md` which are local-only). Never add local content to `docs/`.

**No-translate files (HTML redirect pattern):** Some `docs/` files do not need Russian translation (e.g. `changelog.md` — mostly Pāḷi data and GitHub issue numbers). For these, the canonical approach is an HTML meta-redirect file: `docs_rus/file.md` redirects to an external URL. This satisfies the parity check (file exists) and MkDocs correctly handles it during build. Add such files to `NO_TRANSLATE` in `check_docs_parity.py` to skip staleness checks.

**Stage 4.A — Analysis (ADVANCED model)**:
FAST must run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir>` before handing off to Stage 4.A.
The script reads `<thread_dir>/prep_manifest.json` and reports docs changes from the exact
`from_upstream_sha -> to_upstream_sha` sync range, not from a moving `HEAD` range.

1. Read `docs_parity_report.md`.
2. Read 3–5 existing `docs_rus/` files to build a terminology glossary (key EN → RU mappings specific to DPD: headword, inflection template, root family, deconstructor, lookup, etc.).
3. For each stale file listed in the report, use the exact diff evidence in `docs_parity_report.md`. If the diff evidence is missing, stop and request FAST.
4. Write `docs_translation_plan.md` in the thread folder containing:
   - **Terminology glossary** — EN → RU pairs extracted from existing translations.
   - **Translation rules** — keep Pali terms as-is; keep image paths, code blocks, and URLs unchanged; translate heading text and alt text; keep HTML anchor IDs unchanged.
   - **Per-file tasks** — for each missing file: source path, target path, "full translation". For each stale file: source path, target path, the exact diff evidence from `docs_parity_report.md`, "update only changed sections".
5. Present `docs_translation_plan.md` to user for approval.

**Stage 4.B — Translation (FAST model)**:
1. Read `docs_translation_plan.md` — do not read any other file not referenced there.
2. Execute file-by-file in order: missing files first (create + translate), stale files second (targeted update).
3. After all files are written, update `mkdocs_ru.yaml` nav if any new files were added.
4. Run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir> --strict` and record the result in `handoff.md`.
5. Prepare commit: `#docs: translate/update docs_rus/ for sync <from>..<to>`.
6. Stop and request ADVANCED if terminology, scope, or source diff interpretation is unclear.

### Stage 5: Verification & After-sync (ADVANCED Acceptance)
**Goal**: Final human verification and close out the sync record.
**Owner**: ADVANCED for acceptance decisions. If mechanical finalization is needed, ADVANCED writes exact instructions and hands off to FAST.
**ADVANCED hard stop (Stage 5):** ADVANCED reads outputs, makes the acceptance decision, and writes exact FAST instructions ONLY. It MUST NOT run any command that mutates state, builds, or runs tests (no `uv sync`, no exporters, no `pytest`, no `finalize_accepted_sync.py`, no source edits). If ADVANCED finds itself about to run such a command, STOP and hand off to FAST immediately. All verification commands and finalization belong to FAST.

1. **Full manual verification**
   - Ask user to verify everything and stay back for feedback. After correcting it, do not proceed until user explicitly says "all is good, proceed."
2. **Write retrospective.md (REQUIRED before finalize)**
   - Copy `kamma/upstream_sync/templates/retrospective.md` to `<thread_dir>/retrospective.md`.
   - Fill the three buckets: **landed** (fixed in code this sync), **promote** (becomes a guide rule / validator / archive entry — do it now), **drop** (genuine one-off, with reason).
   - Promote any `promote` items to `archive_improvements.md` before running finalize.
   - `finalize_accepted_sync.py` will refuse to run if `retrospective.md` is absent (hard code gate).
3. **After sync**
   - If accepted, write exact FAST handoff instructions to run `uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>`.
   - Review the temporary `new_improvements.md`, promote accepted items to `archive_improvements.md`, and delete the file.

---

## Stage 3 gotchas

Recurring pitfalls captured from past sync runs. Check these before declaring a shadow clean.

- **SBS files may need an explicit `from tools.utils import …` (F-2).** When upstream adds a
  utility import, the SBS shadow does not inherit it automatically. If upstream adds
  `from tools.utils import some_helper`, also add `from tools.utils import some_helper` to the
  SBS shadow manually — do not assume it comes for free via the restore.

- **Use `\bopen\(` or `[^.]open\(` when grepping for bare `open()` (F-3).** A plain `grep open`
  also matches `pathlib.Path.open(`, `re.compile("open")`, and method names like `is_open`.
  Use `rg '\bopen\('` or `rg '[^.]open\('` to find only unqualified `open()` calls that may need
  to be ported to `Path.open()` or `pathlib.Path.open`.

- **Dropping an upstream import requires a parity whitelist addition (F-5).** If the shadow
  intentionally omits an import that upstream retains (e.g., a deprecated helper that the
  shadow replaces with its own logic), add a `WHITELIST` entry to
  `tests/test_shadow_parity.py` for that import, or the parity test will fail on every future
  sync. Run `uv run pytest tests/test_whitelist_liveness.py` afterward to confirm the entry is
  in the correct FQ form.

---

## Registry Categories

| Category | Description |
|---|---|
| `modified_upstream_files` | Upstream files where this fork diverges. Requires manual porting of new features. |
| `russian_copies` | Shadow files mirroring upstream with Russian additions. Strict parity enforced. |
| `sbs_copies` | Shadow files mirroring upstream with SBS additions. Strict parity enforced. |
| `dps_copies` | Shadow files mirroring upstream with shared DPS fork additions. Strict parity enforced. `dps_copies` is the single category for mixed/shared fork shadows and for local upstream shadows that are not cleanly Russian-only, SBS-only, or Tamil-only. |
| `tamil_copies` | Shadow files mirroring upstream with Tamil additions. Strict parity enforced. Primary shadow: `db/tpd/tpd_to_lookup.py` → `db/epd/epd_to_lookup.py`. |
| `inspired_by_upstream` | Local files derived from upstream but structurally diverged. No strict parity; backport useful improvements only. |
| `unique_paths` | Fork-only cleanup inventory, not sync targets; no SMD entry required. |
| `no_sync_files` | Infrastructure files that must never be overwritten. |
| `skip_sync_patterns` | Upstream-owned or irrelevant paths excluded from Stage 1 analysis only. They are still synced unless also listed in `no_sync_files`. |

---

## SMD (Sync Metadata) Structure

Merge rules are no longer in a monolithic file. See the `kamma/upstream_sync/smd/` directory:
- `index.md`: Entry point and directory of all entries.
- `db.md`, `exporter.md`, `gui.md`, `scripts.md`, `tools.md`: Domain-specific merge rules.

Every entry must define a `Sync Rule` (`PORT`, `MIRROR_EXACTLY`, `PRESERVE`, `DISCUSS`, or `inspired_only`). Every sync-relevant SMD entry must use the exact same `Category` as its `registry.json` entry.

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
- `prep_manifest.json`: Stage 1 machine-readable snapshot of the active upstream range, including `blocker_paths` that must be resolved before automated pull.
- `reviewed_shadow_noops.json`: durable ledger of reviewed upstream shadow changes that intentionally needed no local edit. Entries are exact to the upstream-pull commit and changed path set, so future upstream changes to the same source still get flagged.

These files support the 5-stage workflow. They are not a separate stage.
