# Implementation Plan - Advanced Pāḷi Analysis Tool & GUI Integration

**IMPORTANT:** Before proceeding to ANY next phase, the user MUST explicitly state: "Good - go to the next Stage".

## Phase 1: Robust Python Analyzer (Stage 1)
- [x] Task: Make use of `tests/test_analyze_sentence.py` with a comprehensive suite of Pāḷi sentences covering various grammatical structures (compounds, sandhi, inflections).
- [x] Task: Make use of `exporter/analysis/analyzer.py` to ensure it deterministically returns all grammatical possibilities in the standard JSON structure.
- [x] Task: Run regression tests and verify output against manual expectations. The output is stored in `temp/debug_analysis_dump.json` it is a huge json file and on this stage we would need to read it a lot, so better to use flash model for reading huge debug files.
- [~] Task: **User Approval Gate:** Present Stage 1 results to the user for explicit sign-off before proceeding.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Robust Python Analyzer (Stage 1)' (Protocol in workflow.md)

## Phase 2: Hybrid AI Translation (Stage 2)
- [x] Task: Make use of `tests/test_ai_pali_translate.py` to test the "Safe Merge" logic (mocking the AI response).
- [x] Task: Make use of `exporter/analysis/ai_pali_translate.py` to implement the "Safe Merge" pattern:
    - [x] Define the strict lightweight JSON schema for the AI response (translation + option indices).
    - [x] Implement the Python logic to merge AI selections into the master analyzer JSON.
- [x] Task: Integrate the actual LLM call (using existing API keys) to populate the lightweight response.
- [x] Task: Verify that the AI tool never corrupts the grammatical data structure.
- [~] Task: **User Approval Gate:** Present Stage 2 hybrid results to the user for explicit sign-off before proceeding.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Hybrid AI Translation (Stage 2)' (Protocol in workflow.md)

## Phase 3: Local GUI Integration (Stage 3)
- [x] Task: Make use of the `AnalysisView` in `gui2/analysis_view.py` building upon the existing draft, with the main layout: Input, Sutta Selector, Analysis Table.
- [x] Task: Implement the "Default View" logic: Call `analyzer.py` and populate the table with raw options.
- [x] Task: Implement "AI Assist" button: Call `ai_pali_translate.py` and update the UI to highlight AI-selected options and show the translation.
- [x] Task: Implement interactive option selection:
    - [x] Allow users to click/select alternative grammatical options in the table.
    - [x] Update the internal state to reflect user choices.
- [x] Task: Implement "Re-Translate" button: Send the user's specific word choices back to the AI for a refined sentence translation.
- [x] Task: Implement Export functionality (Markdown and CSV).
- [~] Task: **User Approval Gate:** Present Stage 3 results to the user for explicit sign-off before proceeding.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Local GUI Integration (Stage 3)' (Protocol in workflow.md)

## Phase 4: Webapp Port (Stage 4)
- [ ] Task: Port the core `gui2` interaction logic to the `exporter/webapp/` framework.
- [ ] Task: Create the frontend template/components for the Analysis tab in the webapp.
- [ ] Task: Connect the webapp backend to the `analyzer.py` and `ai_pali_translate.py` modules.
- [ ] Task: Verify that the web experience matches the local GUI functionality.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Webapp Port (Stage 4)' (Protocol in workflow.md)

## Phase 5: Future/Advanced (Optional "Pass 3")
- [ ] Task: (Placeholder) Explore DPD entry attribution and "Pass 3" gap analysis using the developed tools.
