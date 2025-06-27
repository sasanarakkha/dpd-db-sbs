# inference.py
import os
import json
import pandas as pd

from tools.file_utils import search_pali_in_csv, load_exercise_data_from_file, load_discourse_sutta_data
from tools.ai_llm_factory import LLMFactory
from tools.configger import config_read


# --- DeepSeek Caching Configuration ---
# Define the directory for DeepSeek API context caching
DEEPSEEK_CACHE_DIR = "shared_data/deepseek_cache"
# --- End DeepSeek Caching Configuration ---

# --- Prompt Definitions ---

SYSTEM_PROMPT_UNIFIED = """
You are an AI assistant specialized in Pali language processing. Your primary task is to extract **full sentences** from an exercise dataset based on a given Pali word. Follow these instructions meticulously and in order:

**Phase 1: Word Identification and Sentence Selection**

1.  **Diligent and Flexible Search for the Pali Word:**
    *   Your primary goal is to find a sentence in the exercise dataset that contains the **given Pali word**.
    *   **Crucial for Word Recognition - Morphological Variants**: The **given Pali word** might appear in the sentence in a different grammatical form (a morphological variant, such as a different declension, conjugation, or with different endings). You **MUST** be able to recognize these variants. Conceptually, think about stemming or lemmatizing the words in the exercise text to match the base form of the **given Pali word**, or vice-versa.
        *   *Example*: If the given `pali` word is 'bhāsati', you should look for forms like 'bhāsissāmi', 'bhāsitaṃ', etc., in the exercise text.
        *   **Key to Success**: Finding *any* valid morphological variant of the **given Pali word** within a sentence that meets the criteria below is the key to a successful extraction for that word.
            *   If you find such a variant, this exact form found in the text will become your `selected_pali_word`.
    *   **Handling Compound Words (Sandhi)**: Be aware that the Pali word might be part of a compound word in the exercise text. Your search should try to identify the given word even if it's joined with another word. If found as part of a compound, the `selected_pali_word` should be the part of the compound that matches the given word or its variant.
    *   **No Guessing `selected_pali_word`**: The `selected_pali_word` MUST be the exact string of characters as it appears in the exercise text. Do not infer or reconstruct a base form for this field; use what you find.


2.  **Sentence Criteria:**
   - Extract **full Pali sentences** that provide meaningful context. Do **not** return single-word outputs (e.g., "<b>Anussarati</b>").
   - A valid **sutta reference number** (also known as the **sutta number**) must be **explicitly present within the selected sentence**.
   - **STRICT RULE**: 
      - If the **sutta reference number** (e.g., "AN 3.71") is **not found directly in the selected sentence itself**, **discard the selected sentence**.
   - Remove any **sutta reference number** from the selected sentence (e.g., "AN 3.71", "AN 3.71 (simpl)", or similar citation formats) once identified.
   - Store the **sutta reference number** in the `"class_source"` field.
   - **Handling `(simpl)` in `class_source` Formatting:**
         - If the extracted **sutta reference number** contains **"(simpl)"**, preserve it (e.g., `"DN 19.7 (simpl)"`).
         - If **"(simpl)"** is **not present**, return only the core sutta number (e.g., `"DN 19.7"`).
   - **Handling "extra" part of sentences:**
      - When searching for sentences corresponding to any given Pali word, **first and foremost look to extract an example from the main part**. 
      - Only if no sentences can be found in the main part should sentences from the "extra" part be considered.
         - This is an important distinction, do not extract sentences from the "extra" part unless absolutely necessary.
      - If sentences from the extra part are used, the `class_source` should still only contain the sutta reference number (e.g., `"DN 19.7"`), but the "extra" field should be marked "yes".

**Phase 2: Output Formatting (Only if a valid sentence was found and `selected_pali_word` identified)**

3.  **Highlighting the `selected_pali_word` in `class_example`:**
    *   This is a **CRITICAL and MANDATORY** step.
    *   **ABSOLUTELY ESSENTIAL**: The `class_example` field **MUST** contain the full, original Pali sentence (with sutta ref removed) and the `selected_pali_word` within it **MUST** be wrapped in `<b>...</b>` tags.
    *   In the cleaned Pali sentence (that will become `class_example`), the `selected_pali_word` (the exact form you identified in Step 1) **MUST be highlighted ALONE** within `<b>...</b>` tags.
    *   **Precision is Key**: Ensure only the `selected_pali_word` itself is bolded. Do NOT include surrounding punctuation or other words within the `<b>...</b>` tags.
        *   *Correct Example*: If `selected_pali_word` is "buddho", `class_example` should contain "... <b>buddho</b> ...".
        *   *Incorrect Example*: "... <b>buddho.</b> ..." or "... <b>kira buddho</b> ...".
    *   **If this highlighting cannot be done correctly and precisely, the entire result is invalid, and you MUST return the empty JSON structure.**
   - The capitalization of the entire Pali sentence must remain exactly as in the exercise dataset.

4.  **`\"class_example\"` Content Rule:**
    *   The `\"class_example\"` field **MUST** contain the Pali sentence only. It **MUST NOT** contain the English translation.
   
5.  **`\"pali\"` Field (Original Given Word):**  
   - The `\"pali\"` field **must always** match the **exact given Pali word**, including numbering if present (e.g., `\"anussarati 1.1\"`).
   - Even if the extracted sentence contains a different **morphological form**, the `\"pali\"` field must **not** be altered.


6.  **`\"selected_pali_word\"` Field (Form Found and Highlighted):**
    *   This field must contain the **exact morphological variant** that you identified in the sentence (from Step 1) and which you successfully highlighted in `class_example` (Step 3).

**Phase 3: JSON Output Generation**

7.  **Output Structure and Formatting:**
   - If a valid sentence is found and the sutta reference number is explicitly present within it, return the output in **JSON format** with the following structure:
      {{
         "id": "<Given Pali ID>",
         "pali": "<Given Pali word>",
         "selected_pali_word": "<Selected Pali word>",
         "class_source": "<Sutta Reference Number>",
         "extra": "<Marked 'yes' if the sentences from 'extra' part>",
         "class_example": "<A full Pali sentence with <b>Selected Pali word</b> highlighted, ONLY taken from original example, preserving original capitalization>",
         "english_translation": "<English translation>",
      }}
   - If the sutta reference number is missing from the selected sentence or no valid sentence is found, return a **JSON object** with empty values for all fields except "id" and "pali":
      {{
         "id": "<Given Pali ID>",
         "pali": "<Given Pali word>",
         "selected_pali_word": "",
         "class_source": "",
         "extra": "",
         "class_example": "",
         "english_translation": "",
      }}

8. **Strict JSON Output rules:**
   **IMPORTANT: FOLLOW THESE RULES STRICTLY**
   - **DO NOT** wrap the JSON output in Markdown formatting (e.g., ` ```json ... ``` `).
   - **DO NOT** add any extra text before or after the JSON response.
   - **Make sure you use the exact name found within the prompt for the 'example', do not try to re-write it.**
   - **Make sure** that the "class_example" is sentences on Pali language, but not the English traslation.
   - **DO NOT** format the output as a code block.
   - **ONLY RETURN A PLAIN JSON OBJECT.**
   - **Failure to follow these rules will result in an invalid response.**


9. **FINAL, ABSOLUTELY CRITICAL VERIFICATION**: Before finalizing the response, meticulously review ALL rules above. Specifically, ensure:
1. The `selected_pali_word` is correctly identified.
2. The `class_example` contains the full, original Pali sentence (with sutta ref removed).
3. The `selected_pali_word` (and ONLY it) is correctly highlighted with `<b>...</b>` tags within the `class_example`.
4. The `class_example` contains ONLY the Pali sentence, NOT the English translation.
5. The `class_source` and `extra` fields are correctly populated based on the source sentence.
+If ANY of these checks fail, you MUST return the empty-value JSON structure as specified in Phase 3, Rule 6 (the second JSON example).

"""

# User Prompt Templates
USER_PROMPT_UNIFIED_BATCH_TEMPLATE = """
For the given Pali word: "{pali}" with ID: "{id}", using the provided exercise data: "{exercise}", extract the relevant information as per the system prompt instructions.
"""

# --- Discourse Task Prompts ---

SYSTEM_PROMPT_DISCOURSE = """
You are an AI assistant specialized in Pali language processing. Your task is to find a Pali word within a structured collection of Sutta texts and extract relevant information.

**Input You Will Receive:**
1.  A `pali_word` to search for.
2.  An `id` associated with that `pali_word`.
3.  `exercise_data`: This will be a JSON string representing a list of Sutta objects. Each Sutta object has the following structure:
    {{
        "sutta_ref": "e.g., sn12.1",
        "sutta_title": "e.g., paṭiccasamuppādasuttaṃ",
        "sentences": ["Pali sentence 1.", "Pali sentence 2.", ...]
    }}

**Your Task - Follow these steps meticulously:**

1.  **Word Search:**
    *   Iterate through each Sutta object in the `exercise_data`.
    *   For each Sutta, iterate through its `sentences`.
    *   Diligently search for the **`pali_word`** (the one provided in the input, including any numbers) within these sentences, considering the following:
    *   **Crucial for Word Recognition - Morphological Variants, Orthography & Compounds**:
        *   **Morphological Variants**: The input `pali_word` might appear in a sentence in a different grammatical form (e.g., different declension or conjugation). You **MUST** recognize these variants.
        *   **Morphological Variants**: The input `pali_word` (which might be a base form, an inflected form, or include a numeric part if that's how it's given) might appear in a sentence in a different grammatical form (a morphological variant, e.g., different declension, conjugation, or with different endings). You **MUST** diligently recognize these variants. Conceptually, this means being flexible enough to match the input `pali_word` to inflected forms in the text, or to understand how inflected forms in the text relate back to the input `pali_word`. Finding *any* such valid morphological variant is key.
            *   *Example*: If the input `pali_word` is 'bhāsati', you should find forms like 'bhāsissāmi', 'bhāsitaṃ'. The form found in the text (e.g., 'bhāsissāmi') becomes the `selected_pali_word`.
        *   **Orthographic Flexibility**: Be flexible with minor orthographic variations. For instance, if the input `pali_word` is "tassime", it should match "tass'ime" (with an apostrophe for elision) in the text. The form found in the text ("tass'ime") becomes the `selected_pali_word`.
        *   **Compound Words (Sandhi)**:
            *   **Input `pali_word` as a component**: The input `pali_word` might be a component of a larger compound word. Your search must identify the input `pali_word` *within* such a compound.
                *   *Example*: If the input `pali_word` is 'kāya', and the sentence contains 'kāyapariyantikaṃ', you should identify 'kāya' within it. In this case, 'kāya' is the `selected_pali_word`.
                *   *Example*: If the input `pali_word` is 'ime', and the sentence contains 'tass'ime', you should identify 'ime' as a component. 'ime' would be the `selected_pali_word`.
            *   **Input `pali_word` IS the compound**: If the input `pali_word` itself is a compound (e.g., "tassime") and is found directly (or with minor orthographic variation like "tass'ime"), then that found form ("tass'ime") is the `selected_pali_word`.
    *   **Defining `selected_pali_word`**: If a match is found (direct, variant, component of compound, or orthographically similar), the `selected_pali_word` is the **exact string of characters as it appears in the sentence text** that corresponds to the identified input `pali_word` or its relevant part/variant.
        *   *Example for elision*: If the input `pali_word` is "tassime" and the text contains "tass'ime" (due to elision), then "tass'ime" (the exact form from the text) is the `selected_pali_word`.
        *   The goal is for `selected_pali_word` to be precisely what needs to be highlighted with `<b>...</b>` tags in the `class_example`.

2.  **Sentence Selection and Information Extraction (If a match is found):**
    *   Select the **full Pali sentence** where the `selected_pali_word` was found.
    *   The `sutta_number` for your output is the `sutta_ref` from the Sutta object where the sentence was found.
    *   The `sutta_name` for your output is the `sutta_title` from the Sutta object where the sentence was found.

3.  **Formatting `class_example`:**
    *   This is a **CRITICAL and MANDATORY** step.
    *   The `selected_pali_word` (the exact form you identified in Step 1, e.g., 'kāya' from 'kāyapariyantikaṃ', or 'musāvādī' as is) **MUST be highlighted ALONE** within `<b>...</b>` tags in the `class_example`.
    *   **Precision is Key**: Ensure only the `selected_pali_word` itself is bolded. Do NOT include surrounding punctuation or other words.
        *   *Correct Example*: "... <b>buddho</b> ..."
        *   *Incorrect Example*: "... <b>buddho.</b> ..."
        *   *Correct Example for Compound*: "... <b>kāya</b>pariyantikaṃ ..." (if 'kāya' was the `selected_pali_word` identified from the compound).
    *   The capitalization of the entire Pali sentence must remain exactly as it was in the input `sentences`.

4.  **Highlighting Verification (Self-Correction Step):**
    *   Before finalizing, re-read the `class_example` you've constructed.
    *   Confirm that the `selected_pali_word` (and *only* that word/segment) is enclosed in `<b>...</b>` tags.
    *   **If the highlighting is missing or incorrect (e.g., bolding extra characters, or not bolding at all), you MUST correct it. If you cannot correct it to perfectly match the rule, then the entire result is invalid, and you MUST return the empty JSON structure as defined below.**

5.  **Output Structure (JSON):**
    *   **If a valid sentence is found and highlighted correctly:**
        {{
            "id": "<Given Pali ID>",
            "pali": "<Given `pali_word`>",
            "selected_pali_word": "<The exact morphological variant found and highlighted>",
            "sutta_number": "<The `sutta_ref` from the Sutta object containing the sentence>",
            "sutta_name": "<The `sutta_title` from the Sutta object containing the sentence>",
            "class_example": "<The full Pali sentence with the `selected_pali_word` correctly bolded>"
        }}
    *   **If no sentence containing the `pali_word` (or its variants) is found in any Sutta, OR if highlighting cannot be done precisely:**
        Return a JSON object with empty values for all fields except "id" and "pali":
        {{
            "id": "<Given Pali ID>", 
            "pali": "<Given `pali_word`>",
            "selected_pali_word": "",
            "sutta_number": "",
            "sutta_name": "",
            "class_example": ""
        }}

6.  **Strict JSON Output Rules:**
    *   **DO NOT** wrap the JSON output in Markdown formatting (e.g., ` ```json ... ``` `).
    *   **DO NOT** add any extra text before or after the JSON response.
    *   **ONLY RETURN A PLAIN JSON OBJECT.**
"""

USER_PROMPT_DISCOURSE_BATCH_TEMPLATE = """
For the given Pali word: "{pali}" with ID: "{id}", using the provided `exercise_data` (which is a JSON string list of Sutta objects): {exercise_data}, extract the relevant information as per the system prompt instructions.
"""


def run_batch_class_inference(vocab_csv_path, exercise_text_file_path, output_csv_path, provider:str):
    """Runs batch inference using provider."""
    print(f"\n--- Running Batch {provider.upper()} Class Inference ---")
    print(f"Vocab: {vocab_csv_path}, Exercise File: {exercise_text_file_path}, Output: {output_csv_path}")

    try:
        vocab_df = pd.read_csv(vocab_csv_path)
    except FileNotFoundError:
        print(f"Error: Vocab file not found at {vocab_csv_path}")
        return
    
    exercise_data_content = load_exercise_data_from_file(exercise_text_file_path)
    if not exercise_data_content:
        print(f"Could not load exercise data. Aborting batch {provider.upper()} inference.")
        return

    batch_input_for_llm = []
    if 'pali' not in vocab_df.columns or 'id' not in vocab_df.columns:
        print(f"Warning: '{vocab_csv_path}' might be missing 'pali' or 'id' columns. Attempting to proceed or use fallback.")
        if 'pali' in vocab_df.columns:
            print("Attempting to find IDs using search_pali_in_csv as 'id' column is missing or for verification...")
            for pali_word in vocab_df["pali"]:
                search_result = search_pali_in_csv(pali_word, vocab_csv_path)
                if search_result["id"] != -1 :
                    batch_input_for_llm.append({
                        "pali": search_result["pali"],
                        "id": str(search_result["id"]),
                        "exercise": exercise_data_content
                    })
                else:
                    print(f"Skipping '{pali_word}' for batch as it was not found by search_pali_in_csv.")
        else:
            print(f"Error: '{vocab_csv_path}' must contain at least a 'pali' column for batch processing.")
            return
    else:
        for _, row in vocab_df.iterrows():
            batch_input_for_llm.append({
                "pali": row["pali"],
                "id": str(row["id"]),
                "exercise": exercise_data_content
            })

    if not batch_input_for_llm:
        print("No valid data for batch processing after preparing inputs.")
        return
    
    # --- LLM Initialization ---
    api_key = config_read("apis", provider)
    if not api_key:
        print(f"Error: API key for {provider.upper()} not found in config. Aborting.")
        return

    llm_instance = LLMFactory(provider, "langchain", "deepseek-chat" if provider == "deepseek" else "gpt-4o-mini", api_key, 0.7).get_llm() # type: ignore

    print(f"Prepared {len(batch_input_for_llm)} items for {provider.upper()} batch processing.")
    
    batch_results_raw = llm_instance.batch_processing(
        SYSTEM_PROMPT_UNIFIED,
        USER_PROMPT_UNIFIED_BATCH_TEMPLATE,
        batch_input_for_llm
    )

    parsed_results = []
    for res_text in batch_results_raw:
        # res_text is already a dictionary from llm_instance.batch_processing
        if isinstance(res_text, dict): 
            original_input = next((item for item in batch_input_for_llm if item['pali'] == res_text.get('pali')), None)
            if original_input and 'id' not in res_text: # Use res_text here
                 res_text['id'] = original_input['id'] # Modify res_text directly
            parsed_results.append(res_text) # Append res_text
        else:
            # This case might indicate an unexpected return type from batch_processing
            parsed_results.append({"error": "unexpected_response_type", "original_data": res_text})

    df_results = pd.DataFrame(parsed_results)
    
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_results.to_csv(output_csv_path, index=False, encoding="utf-8")
    print(f"{provider.upper()} batch results saved to {output_csv_path}")


def run_batch_discourse_inference(vocab_csv_path, sutta_text_file_path, output_csv_path, provider: str):
    """Runs batch inference for a discourse text using provider."""
    print(f"\n--- Running Batch {provider.upper()} Discourse Inference ---")
    print(f"Vocab: {vocab_csv_path}, Sutta File: {sutta_text_file_path}, Output: {output_csv_path}")

    try:
        vocab_df = pd.read_csv(vocab_csv_path)
        if 'pali' not in vocab_df.columns or 'id' not in vocab_df.columns:
            print(f"Error: Vocab CSV '{vocab_csv_path}' must contain 'pali' and 'id' columns.")
            return
    except FileNotFoundError:
        print(f"Error: Vocab file not found at {vocab_csv_path}")
        return
    except Exception as e:
        print(f"Error reading vocab CSV '{vocab_csv_path}': {e}")
        return

    sutta_data_list = load_discourse_sutta_data(sutta_text_file_path)
    if not sutta_data_list:
        print(f"Could not load or parse sutta data from {sutta_text_file_path}. Aborting.")
        return
    
    # Convert the list of sutta objects to a JSON string to pass to the LLM
    exercise_data_json_str = json.dumps(sutta_data_list, ensure_ascii=False)

    batch_input_for_llm = []
    for _, row in vocab_df.iterrows():
        batch_input_for_llm.append({
            "pali": str(row["pali"]),
            "id": str(row["id"]),
            "exercise_data": exercise_data_json_str # Pass the structured JSON string
        })

    if not batch_input_for_llm:
        print("No valid data for batch processing after preparing inputs.")
        return
    
    # Initialize LLM instance based on provider
    api_key = config_read("apis", provider)
    if not api_key:
        print(f"Error: API key for {provider.upper()} not found in config. Aborting.")
        return
    
    llm_instance = LLMFactory(provider, "langchain", "deepseek-chat" if provider == "deepseek" else "gpt-4o-mini", api_key, 0.7).get_llm() # type: ignore

    print(f"Prepared {len(batch_input_for_llm)} items for {provider.upper()} batch discourse processing.")
    
    batch_results_raw = llm_instance.batch_processing(
        SYSTEM_PROMPT_DISCOURSE,
        USER_PROMPT_DISCOURSE_BATCH_TEMPLATE,
        batch_input_for_llm
    )

    parsed_results = []
    for i, res_text_dict in enumerate(batch_results_raw):
        # res_text_dict should already be a dictionary from llm_instance.batch_processing
        # which internally calls parse_llm_response on the raw LLM output for each item.
        if isinstance(res_text_dict, dict):
            # Ensure 'id' and 'pali' from the original request are present if not returned by LLM
            # (though the SYSTEM_PROMPT_DISCOURSE asks LLM to return them)
            if 'id' not in res_text_dict and i < len(batch_input_for_llm):
                res_text_dict['id'] = batch_input_for_llm[i]['id']
            if 'pali' not in res_text_dict and i < len(batch_input_for_llm):
                res_text_dict['pali'] = batch_input_for_llm[i]['pali']
            parsed_results.append(res_text_dict)
        else:
            # Fallback for unexpected response type
            error_id = batch_input_for_llm[i]['id'] if i < len(batch_input_for_llm) else "unknown_id"
            error_pali = batch_input_for_llm[i]['pali'] if i < len(batch_input_for_llm) else "unknown_pali"
            parsed_results.append({
                "id": error_id,
                "pali": error_pali,
                "error": "unexpected_response_type_from_llm",
                "original_data": str(res_text_dict)
            })


    df_results = pd.DataFrame(parsed_results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_results.to_csv(output_csv_path, index=False, encoding="utf-8")
    print(f"{provider.upper()} batch discourse results saved to {output_csv_path}")




if __name__ == "__main__":
    # --- Script Usage Guide ---
    #
    # This script can now be run directly.
    # You'll need to configure the `task_to_run` variable and the
    # corresponding file paths below.
    #
    # Example for Batch Class Inference:
    # task_to_run = "batch_class_inference"
    # vocab_csv_for_batch = "path/to/your/vocab.csv"
    # exercise_file_for_batch = "path/to/your/exercise.txt"
    # output_csv_for_batch = "path/to/your/output_batch.csv"
    #
    # Example for Batch Discourse Inference:
    # task_to_run = "batch_discourse_inference"
    # discourse_vocab_csv_path = "path/to/your/discourse_vocab.csv"
    # sutta_text_file_for_discourse = "path/to/your/sutta.txt"
    # output_csv_for_discourse = "path/to/your/output_discourse.csv"
    # --- End Script Usage Guide ---

    # --- Configuration for direct script run ---
    # Choose which task to run by uncommenting one of the following:
    task_to_run = "batch_class_inference"
    # task_to_run = "batch_discourse_inference"

    provider = "deepseek"
    # provider = "openai"

    # --- Default paths for "batch_class_inference" ---
    class_num = "29"
    vocab_csv_for_batch = f"shared_data/pali_class/vocab/vocab_class_{class_num}.csv"
    exercise_file_for_batch = f"shared_data/pali_class/exercises/exercises_class_{class_num}.txt"
    output_csv_for_batch = f"shared_data/pali_class/output/class_{class_num}_output2.csv" 

    # --- Default paths for "batch_discourse_inference" ---
    sutta_code = "sn56"
    discourse_vocab_csv_path = f"shared_data/discourses/vocab/vocab_rest.csv"
    sutta_text_file_for_discourse = f"shared_data/discourses/suttas/{sutta_code}.txt"
    output_csv_for_discourse = f"shared_data/discourses/output/rest_{sutta_code}_output.csv"
    # --- End Configuration ---

    # Ensure cache directory exists
    os.makedirs(DEEPSEEK_CACHE_DIR, exist_ok=True)

    if task_to_run == "batch_class_inference":
        run_batch_class_inference(vocab_csv_for_batch, exercise_file_for_batch, output_csv_for_batch, provider)
    elif task_to_run == "batch_discourse_inference":
        run_batch_discourse_inference(discourse_vocab_csv_path, sutta_text_file_for_discourse, output_csv_for_discourse, provider)
    else:
        print(f"Unknown task: {task_to_run}. Please set 'task_to_run' to 'batch_class_inference' or 'batch_discourse_inference'.")

    print("\n--- Script Finished ---")