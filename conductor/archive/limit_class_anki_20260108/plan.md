# Plan: Filter SBS.class_anki Display Range

## Phase 1: Implementation
Update the specified templates with the conditional logic to restrict `class_anki` display to values <= 29.

- [x] Task: Research current `class_anki` usage and verify template engine syntax (Mako vs Jinja2)
- [x] Task: Update `exporter/goldendict/sbs_templates/sbs_example.html` (Mako)
- [x] Task: Update `exporter/goldendict/sbs_templates/dpd_definition.html` (Mako)
- [x] Task: Update `exporter/webapp/sbs_templates/dpd_headword.html` (Jinja2)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Implementation' (Protocol in workflow.md)

## Phase 2: Verification
Verify that the templates correctly hide/show the data based on the `class_anki` value.

- [x] Task: Write a test script to mock data and verify Mako template rendering for GoldenDict files
- [x] Task: Write a test script to mock data and verify Jinja2 template rendering for WebApp file
- [x] Task: Conductor - User Manual Verification 'Phase 2: Verification' (Protocol in workflow.md)
