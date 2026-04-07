# Spec: Implement Upstream Sync Process Improvements

## Goal

Implement the refactored `kamma/upstream_sync/` process, registry schema, and validation tooling designed in the `improvement_sync_proccess` thread. This will establish a 3-stage workflow (Prep, Analysis, Execution) and clarify the distinction between strict shadows and files inspired by upstream.

## Deliverables

1. **Registry Schema Update**: Implement `inspired_by_upstream` and `skip_sync_patterns` in `registry.json`.
2. **Registry Migration**: Reclassify files based on the audit results.
3. **Validator Improvements**: Update `validate_registry.py` to enforce the new schema.
4. **SMD Restructuring**: Split `smd.md` into domain-specific files under `kamma/upstream_sync/smd/`.
5. **Process Documentation**: Rewrite `guide.md` and create stage-specific templates in `kamma/upstream_sync/stages/`.
6. **New Validation Tests**: Implement `tests/test_namespace_isolation.py` and template syntax drift tests.
7. **Prep Analyzer**: Implement the script for generating factual upstream diff reports.
8. **Tooling Updates**: Narrow `test_shadow_parity.py` and update `verify_smd_coverage.py` and cleanup tests.

## Non-Goals

1. Performing an actual upstream sync.
2. Changing the core logic of the DPD database or exporters beyond synchronization parity.

## Acceptance Criteria

1. `validate_registry.py` correctly enforces `divergence_reason` for inspired-by files and rejects `ignored_files`.
2. `verify_smd_coverage.py` correctly handles split SMD files in `smd/`.
3. `tests/test_namespace_isolation.py` correctly identifies non-prefixed global variables in localized copies.
4. The new `guide.md` accurately describes the 3-stage workflow.
5. `test_shadow_parity.py` ignores files in the `inspired_by_upstream` category.
6. The prep analyzer produces a structured report of upstream changes relevant to the registry.
