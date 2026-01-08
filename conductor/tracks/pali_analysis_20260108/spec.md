# Track Specification: Advanced Pāḷi Analysis Tool & GUI Integration

## 1. Overview
This track implements a comprehensive Pāḷi sentence analysis pipeline involving three key components: a pure Python analyzer, an AI-powered translation enhancer, and a GUI integration for interactive user review. The goal is to finish the development of tools described in upstream issue #197, enabling word-by-word grammatical analysis, context-aware AI translation, and direct dictionary mapping.

## 2. Components & Stages

### Stage 1: Refine `exporter/mcp/analyzer.py`
*   **Goal:** Create a robust, deterministic Python-based analyzer.
*   **Functionality:**
    *   Take a Pāḷi sentence as input.
    *   Tokenize and analyze each word using existing `grammar` and `deconstructor` logic.
    *   Identify all grammatical possibilities for each word (Case, Gender, Root, Construction, etc.).
    *   **Output:** A structured JSON object containing all "raw" possibilities for every word in the sentence.
*   **Verification & Gating:**
    *   Utilize and expand `tests/test_analyze_sentence.py`.
    *   **Critical Gate:** This stage requires extensive testing with various sentence structures and parts of speech. Work on Stage 2 will NOT begin until the user explicitly approves the accuracy of Stage 1 output on a diverse test set.

### Stage 2: Refine `exporter/mcp/ai_pali_translate.py`
*   **Goal:** Create a hybrid AI tool that "decorates" the analyzer's output without risking data corruption.
*   **Functionality:**
    *   **Input:** The JSON output from Stage 1 + the original sentence.
    *   **AI Logic (Safe Merge Pattern):**
        *   The AI does **NOT** rewrite the full JSON.
        *   The AI returns a lightweight response containing only:
            1.  The sentence translation.
            2.  A list of "selected indices" (or IDs) corresponding to the most likely grammatical option for each word.
    *   **Python Logic:** A Python script safely merges these AI selections into the master JSON structure, ensuring no grammatical data is lost or hallucinated.
    *   **Verification:** Utilize and expand `tests/test_ai_pali_translate.py`.
*   **Verification & Gating:**
    *   **Critical Gate:** Work on the GUI will NOT begin until the user explicitly approves the accuracy of the Stage 2 hybrid AI results.

### Stage 3: GUI Integration (`gui2/`)
*   **Goal:** A user-friendly interface for the analysis workflow, building upon the draft `gui2/analysis_view.py`.
*   **UI Elements:**
    *   **Input Area:** Text box for Pāḷi sentences.
    *   **Sutta Selector:** Feature to pick a whole Sutta by Pāḷi name (reusing logic like `make_words_to_add_list_sutta`).
    *   **Analysis View:**
        *   **Default View:** Shows results from the pure Python analyzer (Stage 1). Fast, free, offline.
        *   **"AI Assist" Button:** Invokes Stage 2 to re-order/highlight options and provide a translation using the stored API key.
        *   **User Selection:**
            *   **Primary Interaction:** User clicks/selects from the *existing* list of grammatical possibilities provided by Stage 1.
            *   **Edge Case:** Manual entry fields are available *only* for rare cases where Stage 1 fails to recognize a word. Frequent use of this implies a Stage 1 failure.
        *   **"Re-Translate" Button:** Triggers a fresh AI translation based *specifically* on the user's manual word choices.
    *   **Export:**
        *   Export the full analysis to Markdown.
        *   Export word list to CSV.

### Stage 4: Webapp Integration
*   **Goal:** Port the `gui2` experience to the web.
*   **Scope:** Enable the same interactive analysis features in `exporter/webapp/main.py`. This is to be completed after the local GUI is functional.

### Stage 5: Future/Advanced (Potential "Pass 3")
*   **Goal:** Audit the text against the dictionary (beneficial side effect).
*   **Functionality:**
    *   Attribute each word in the text to a specific DPD headword.
    *   Flag words that are missing examples in the dictionary.
    *   Flag words that are missing meanings or are completely unknown.
    *   Could potentially be used for "Pass 3" dictionary development overseen by a developer.

## 3. Technical Constraints & Logic
*   **Hybrid AI Approach:**
    *   First pass is ALWAYS pure Python (lookup tables + deconstructor).
    *   AI is an optional enhancement layer, not the primary engine.
*   **Data Integrity:** The "Safe Merge" pattern must be used. The AI never output the full JSON blob, only specific fields to be merged by Python.
*   **Existing Code:**
    *   Leverage `db/grammar/grammar_to_lookup.py` for mapping logic.
    *   Use `gui/functions_db_dps.py` logic for Sutta extraction.
    *   Use existing API key management in `gui2/main.py`.
    *   Build on `gui2/analysis_view.py`.

## 4. Acceptance Criteria
*   [ ] `exporter/mcp/analyzer.py` passes all regression tests in `tests/test_analyze_sentence.py` and manual verification by the user.
*   [ ] `exporter/mcp/ai_pali_translate.py` implements the "Safe Merge" pattern (no hallucinated JSON structure) and passes user approval.
*   [ ] `gui2` tab (`analysis_view.py`) allows selecting from Stage 1 options and toggling AI assistance.
*   [ ] Manual overrides are correctly handled and can trigger a re-translation.
*   [ ] Analysis data can be exported to MD and CSV.
*   [ ] Webapp implementation reflects local GUI features.
