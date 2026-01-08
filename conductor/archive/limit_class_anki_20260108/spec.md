# Specification: Filter SBS.class_anki Display Range

## Overview
This track aims to restrict the display of `SBS.class_anki` in specific dictionary templates. Currently, the value is shown whenever it exists. The new requirement is to display it only if the value is <= 29.

## Functional Requirements
1.  **Conditional Display Logic:** Update the following templates to show `class_anki` data ONLY if `class_anki <= 29`.
    -   `exporter/goldendict/sbs_templates/sbs_example.html`
    -   `exporter/goldendict/sbs_templates/dpd_definition.html`
    -   `exporter/webapp/sbs_templates/dpd_headword.html`
2.  **Maintain Existing Links/Styles:** Ensure that when displayed, the links (e.g., to `sbs_class_link`) and formatting (e.g., `cl.`, `*` for `class_extra`) remain unchanged.

## Non-Functional Requirements
- **Template Compatibility:** The logic must be compatible with the template engines used (Mako for GoldenDict, Jinja2 for WebApp).

## Acceptance Criteria
- [ ] In GoldenDict `sbs_example.html`, `class_anki` and associated translation/source are hidden if `class_anki` is > 29.
- [ ] In GoldenDict `dpd_definition.html`, the class link and separator are hidden if `class_anki` is > 29.
- [ ] In WebApp `dpd_headword.html`, the class link and separator are hidden if `class_anki` is > 29.
- [ ] Values <= 29 continue to be displayed correctly.

## Out of Scope
- Modifying the database schema or values.
- Updating other SBS-related fields unless directly dependent on `class_anki`'s display logic.
