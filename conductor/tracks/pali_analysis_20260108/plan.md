# Implementation Plan - Advanced Pāḷi Analysis Tool & GUI Integration

## Phase 1: Robust Python Analyzer (Stage 1)
- [ ] Task: Create `tests/test_analyze_sentence.py` with a comprehensive suite of Pāḷi sentences covering various grammatical structures (compounds, sandhi, inflections).
- [ ] Task: Refine `exporter/mcp/analyzer.py` to ensure it deterministically returns all grammatical possibilities in the standard JSON structure.
- [ ] Task: Run regression tests and verify output against manual expectations.
- [ ] Task: **User Approval Gate:** Present Stage 1 results to the user for explicit sign-off before proceeding.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Robust Python Analyzer (Stage 1)' (Protocol in workflow.md)

## Phase 2: Hybrid AI Translation (Stage 2)
- [ ] Task: Create `tests/test_ai_pali_translate.py` to test the "Safe Merge" logic (mocking the AI response).
- [ ] Task: Implement the "Safe Merge" pattern in `exporter/mcp/ai_pali_translate.py`:
    - [ ] Define the strict lightweight JSON schema for the AI response (translation + option indices).
    - [ ] Implement the Python logic to merge AI selections into the master analyzer JSON.
- [ ] Task: Integrate the actual LLM call (using existing API keys) to populate the lightweight response.
- [ ] Task: Verify that the AI tool never corrupts the grammatical data structure.
- [ ] Task: **User Approval Gate:** Present Stage 2 hybrid results to the user for explicit sign-off before proceeding.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Hybrid AI Translation (Stage 2)' (Protocol in workflow.md)

## Phase 3: Local GUI Integration (Stage 3)
- [ ] Task: Scaffold the `AnalysisView` in `gui2/analysis_view.py` building upon the existing draft, with the main layout: Input, Sutta Selector, Analysis Table.
- [ ] Task: Implement the "Default View" logic: Call `analyzer.py` and populate the table with raw options.
- [ ] Task: Implement "AI Assist" button: Call `ai_pali_translate.py` and update the UI to highlight AI-selected options and show the translation.
- [ ] Task: Implement interactive option selection:
    - [ ] Allow users to click/select alternative grammatical options in the table.
    - [ ] Update the internal state to reflect user choices.
- [ ] Task: Implement "Re-Translate" button: Send the user's specific word choices back to the AI for a refined sentence translation.
- [ ] Task: Implement Export functionality (Markdown and CSV).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Local GUI Integration (Stage 3)' (Protocol in workflow.md)

## Phase 4: Webapp Port (Stage 4)
- [ ] Task: Port the core `gui2` interaction logic to the `exporter/webapp/` framework.
- [ ] Task: Create the frontend template/components for the Analysis tab in the webapp.
- [ ] Task: Connect the webapp backend to the `analyzer.py` and `ai_pali_translate.py` modules.
- [ ] Task: Verify that the web experience matches the local GUI functionality.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Webapp Port (Stage 4)' (Protocol in workflow.md)

## Phase 5: Future/Advanced (Optional "Pass 3")
- [ ] Task: (Placeholder) Explore DPD entry attribution and "Pass 3" gap analysis using the developed tools.
