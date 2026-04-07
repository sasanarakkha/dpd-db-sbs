# Analysis Summary: Upstream Sync Process Improvements

This document summarizes the analysis and design decisions made in the `improvement_sync_proccess` thread.

## 1. Triage of Suggestions
Based on `suggestions_gemini.md`, several key improvements were accepted:
- **Automated Prep Analyzer**: Formalizing diff generation before planning.
- **Namespace Linter**: Enforcing localized prefixes (`ru_`, `sbs_`, `dps_`) in JS and HTML.
- **SMD Splitting**: Fragmenting the monolithic `smd.md` for better maintainability.
- **Template Syntax Enforcement**: Detecting legacy Mako syntax in Jinja2 templates.

One suggestion (upstream "hooks") was rejected as out-of-scope for the current spec because the planning thread explicitly excludes upstream architecture redesign.

The triage outcome is durable process input rather than implementation work:
- Accepted items were mapped into the planning thread's Phase 3 design and test deliverables.
- Rejected items were still preserved in `archive_improvements.md` so future sync work retains the rationale.
- The implementation thread should treat the archived triage as locked context, not as an open brainstorming list.

## 2. Reclassification Criteria
We defined three categories for registry entries:
- **strict_shadow**: Upstream-first logic, high structural parity, parity tests mandatory.
- **inspired_by_upstream**: Local-first logic, originally a shadow but now diverged. Porting is creative/manual, not mechanical. Parity tests skipped. Requires a `divergence_reason`.
- **unique_paths**: Fork-only code with no upstream counterpart.

The criteria were locked with a concrete decision table so different reviewers could classify the same file consistently. The deciding signals are:
- logic authority
- structural match
- language match
- localization depth
- sync effort
- SMD requirement

The SMD rules differ by category:
- `strict_shadow` entries use `parity_enforced` and must enumerate exact injection points or structural deltas.
- `inspired_by_upstream` entries use `inspired_only`, must explain why divergence is intentional, and only track high-value upstream areas to watch.
- `unique_paths` do not participate in parity review.

## 3. Registry Audit & Migration List
The audit in `audit_results.md` identified these high-confidence candidates for `inspired_by_upstream`:
- **Bash Scripts**: `generate_components.sh`, `make_dpd.sh`, `make_ru_dpd.sh`, `update-dpd-sbs.sh`.
- **Documentation**: `docs_rus/` and `mkdocs_ru.yaml`.
- **CI Workflows**: `.github/workflows/ru_static.yml`.
- **Exporters & Entry Points**: `exporter/goldendict/export_*.py`, `exporter/goldendict/main_*.py`, `tools/paths_*.py`.

Field Consumer Map findings:
- `ignored_files`: Unused. To be replaced by `skip_sync_patterns`.
- `folders_to_check`: Unused. To be removed.
- `no_sync_files`: Consumed by `test_shadow_cleanup.py`.

The audit also established several broader conclusions the implementation thread must preserve:
- `modified_upstream_files` are currently enforced mostly through SMD prose, not robust parity automation.
- `unique_paths` are consumed in deduplication and cleanup logic, so schema changes cannot ignore those consumers.
- Reclassification is not universal; many RU and SBS copies remain true `strict_shadow` files.

Two entries were left as discussion-sensitive rather than automatically reclassified:
- `db/models.py`, because the localized schema additions are large and important but still conceptually shadow upstream structure.
- `exporter/goldendict/data_classes_dps.py`, because it serves both RU and SBS variants and cannot be classified casually.

## 4. 3-Stage Process Design
The new sync workflow consists of:
1. **Prep**: Factual data gathering (registry/SMD validation, diff analysis).
2. **Boundary Action**: Manual git merge.
3. **Analysis**: Decision-locked implementation planning.
4. **Execution + Verification**: Code implementation and quality gate verification.

Each stage has explicit inputs, outputs, and approval gates:
- **Prep** inputs: registry, SMD set, and upstream diff state. Output: `prep_report.md`. Safe to rerun.
- **Analysis** inputs: `prep_report.md` and current post-sync workspace state. Output: `analysis_report.md`. Safe to rerun if prep is unchanged.
- **Execution + Verification** input: `analysis_report.md`. Outputs: code changes plus `execution_report.md`. Requires fresh analysis if the plan changes.

The boundary action is intentionally not a long-lived stage. The user performs the sync script or merge outside the durable stage documents so mechanical git activity stays separate from model reasoning.

Approval gates are part of the design, not optional process commentary:
- user review after Prep
- user review after Analysis
- final review after Execution + Verification

The thread also introduced a formal `[DISCUSS]` protocol. If a file cannot be handled within the locked classification and planning rules, the active stage must stop and raise a discussion flag instead of improvising.

## 5. SMD and Documentation Strategy
- `smd.md` will be split into a `kamma/upstream_sync/smd/` folder by domain (db, exporter, gui, scripts, tools, root).
- `guide.md` will be refactored into a concise 3-stage operator guide, with history moved to `archive_improvements.md`.
- New stage templates will be added to `kamma/upstream_sync/stages/`.
- Thread templates will be updated to reflect the 3-stage plan structure.

The documentation split was defined more precisely than this summary originally captured:
- `README.md` remains the quick-start entry point and links to the authoritative guide.
- `guide.md` becomes the operator manual for the durable workflow and category semantics.
- `stages/prep.md`, `stages/analysis.md`, and `stages/execution.md` hold stage-specific checklists and report templates.
- `archive_improvements.md` stores historical lessons and triaged improvement intake.
- `new_improvements.md` stays as a temporary intake surface during individual sync runs.

The SMD split is domain-based rather than one-file-per-entry. The implementation must preserve current coverage expectations while moving to aggregated multi-file validation.

## 6. Testing Strategy
- **Namespace Linter**: Using AST/Regex to detect non-prefixed globals and IDs.
- **Syntax Drift**: Grepping for Mako tags in localized Jinja templates.
- **Narrowed Parity**: Updating `test_shadow_parity.py` to honor the new registry category.
- **Registry Validator**: Unit tests for schema enforcement.

Additional implementation-critical test requirements were locked in the planning thread:
- `verify_smd_coverage.py` must aggregate all `smd/*.md` files, enforce uniqueness across them, and keep the current quality rubric.
- `tests/test_shadow_cleanup.py` must honor `skip_sync_patterns` instead of the unused `ignored_files` concept.
- `tests/test_prep_analyzer.py` must validate factual diff reporting from mocked git outputs.
- Validator tests must cover missing `divergence_reason`, legacy `ignored_files`, and invalid `skip_sync_patterns` values.

## 7. Expected File Surface For Implementation
The implementation thread is expected to touch at least these areas:
- `kamma/upstream_sync/registry.json`
- `kamma/upstream_sync/validate_registry.py`
- `kamma/upstream_sync/verify_smd_coverage.py`
- `kamma/upstream_sync/prep_analyzer.py`
- `kamma/upstream_sync/guide.md`
- `kamma/upstream_sync/README.md`
- `kamma/upstream_sync/stages/*`
- `kamma/upstream_sync/templates/sync_thread_spec.md`
- `kamma/upstream_sync/templates/sync_thread_plan.md`
- `kamma/upstream_sync/smd/index.md`
- `kamma/upstream_sync/smd/*.md`
- `tests/test_validate_registry.py`
- `tests/test_namespace_isolation.py`
- `tests/test_template_syntax.py`
- `tests/test_shadow_parity.py`
- `tests/test_shadow_cleanup.py`
- `tests/test_prep_analyzer.py`

## 8. Execution Guidance For The Next Reviewer Or Implementer
The planning thread was intended to remove design ambiguity before implementation starts. The next agent should therefore treat the following as locked:
- the 3-stage workflow and its approval gates
- the category model (`strict_shadow`, `inspired_by_upstream`, `unique_paths`)
- replacement of `ignored_files` with `skip_sync_patterns`
- domain-based SMD splitting
- parity narrowing so only true strict shadows receive parity enforcement

The next agent should not reopen these design decisions unless new evidence forces a `[DISCUSS]` stop. The main execution risks are migration correctness, SMD coverage drift during the split, and accidentally applying strict-shadow rules to files that are only inspired by upstream.
