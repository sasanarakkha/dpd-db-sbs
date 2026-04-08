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

## The 3-Stage Sync Workflow

### Stage 1: Prep (Factual Analysis)
**Goal**: Establish a baseline, validate the environment, and identify what changed upstream.

1. **Environmental Validation**:
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
   - (Commit 1 gate).

### Stage 2: Analysis (Strategic Planning)
**Goal**: Determine how to integrate upstream changes into localized files.

1. **Dynamic Planning**:
   - Create `dynamic_plan.md` in the thread folder.
   - Use `prep_manifest.json` as the factual source of changed upstream files and mapped local destinations.
   - For every modified upstream file mapped to a shadow/inspired copy, define the merge strategy.
2. **Discussion Flags**:
   - Check `discuss` flags in `registry.json`. If `true`, resolve with the user before planning.
3. **Draft Plan Review**:
   - Present the `dynamic_plan.md` to the user for approval.

### Stage 3: Execution & Verification (Implementation)
**Goal**: Apply changes, verify integrity, and clean up.

1. **Implementation**:
   - Execute `dynamic_plan.md` item-by-item following the **Iron Rule**.
2. **Verification**:
   - Run `uv run pytest` (Full suite, including parity and namespace isolation).
   - Run `uv run python3 tests/check_shadow_modifications.py`.
   - Perform manual verification (GoldenDict/webapp).
3. **Cleanup**:
   - Run `uv run python3 tests/test_shadow_cleanup.py --folder <folder> [--apply]` to review or archive orphans.
   - Update `registry.json` and `smd/` to reflect the new state.
   - Update `accepted_sync.json` only after the sync is accepted and verified.
   - Review the temporary `new_improvements.md`, promote items to `archive_improvements.md`, and delete the file.

---

## Registry Categories

| Category | Description |
|---|---|
| `modified_upstream_files` | Upstream files where this fork diverges. Requires manual porting of new features. |
| `russian_copies` | Shadow files mirroring upstream with Russian additions. Strict parity enforced. |
| `sbs_copies` | Shadow files mirroring upstream with SBS additions. Strict parity enforced. |
| `dps_copies` | Shadow files mirroring upstream with DPS additions. Strict parity enforced. |
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

## Symbol Naming Policy

Enforced via `tests/test_namespace_isolation.py`:

1. **Tier 1 — Identical to Upstream**: No locale marker. Keep upstream name exactly.
2. **Tier 2 — Modified from Upstream**: Locale suffix only (`_ru`, `_sbs`, or `_dps`). Never use both a prefix and a suffix.
3. **Tier 3 — New (no upstream counterpart)**: Use descriptive name + locale suffix.
4. **HTML IDs**: Always prefix with locale (`ru_`, `sbs_`, `dps_`).

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
