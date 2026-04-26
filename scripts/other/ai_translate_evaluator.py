#!/usr/bin/env python3

"""
Reusable evaluation workflow for AI-assisted dictionary translation.

Usage Examples:
# List available models for the active provider:
   uv run python scripts/other/ai_translate_evaluator.py --list

# Generate recommendation prompt for Russian:
   uv run python scripts/other/ai_translate_evaluator.py --prompt --lang ru

# Generate recommendation prompt for Tamil:
   uv run python scripts/other/ai_translate_evaluator.py --prompt --lang ta

# Evaluate models for Russian (default):
   uv run python scripts/other/ai_translate_evaluator.py --eval gpt-4o-mini gpt-5-mini --limit 10

# Evaluate models for Tamil:
   uv run python scripts/other/ai_translate_evaluator.py --eval gpt-4o-mini gpt-5-mini --lang ta --limit 10

# Batch API (OpenAI only):
   uv run python scripts/other/ai_translate_evaluator.py --eval gpt-4o-mini --batch --lang ta

Outputs:
- Raw JSON results: temp/ai_eval/eval_raw_<provider>_<timestamp>.json
- Markdown comparison report: temp/ai_eval/eval_report_<provider>_<timestamp>.md
"""

import datetime
import json
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

import requests

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.ai_manager import AIManager
from tools.ai_related import (
    generate_messages_for_meaning,
    generate_messages_for_meaning_ta,
    load_ai_config,
    load_translation_examples,
    replace_abbreviations,
)
from tools.meaning_construction import make_meaning_combo
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


def get_available_models(provider: str, api_key: str | None) -> List[str]:
    """Fetch available models for the given provider."""
    models = []
    if not api_key:
        pr.error(f"API key missing for provider: {provider}")
        return []

    if provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        try:
            response = client.models.list()
            models = [m.id for m in response.data]
            models.sort()
        except Exception as e:
            pr.error(f"Failed to fetch OpenAI models: {e}")
    elif provider == "openrouter":
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            models = [m["id"] for m in data["data"]]
            models.sort()
        except Exception as e:
            pr.error(f"Failed to fetch OpenRouter models: {e}")
    else:
        pr.warning(f"Model discovery not implemented for provider: {provider}")
    return models


TARGET_POS = [
    "abs",
    "adj",
    "aor",
    "fem",
    "ger",
    "idiom",
    "ind",
    "inf",
    "masc",
    "nt",
    "pp",
    "pr",
    "pron",
    "prp",
    "ptp",
    "sandhi",
]


def select_evaluation_sample(
    db_session,
    lang: str = "ru",
    limit: Optional[int] = None,
) -> List[DpdHeadword]:
    """Select three representative words per POS at ranks 20, 40, 60.

    Args:
        db_session: Database session.
        lang: Target language ('ru' or 'ta').
        limit: Optional limit on total samples.

    Returns:
        List of DpdHeadword objects, 3 per POS at indices 19, 39, 59.
    """
    sample = []

    # For evaluation, we sample any word with English meaning - no filter on existing translations
    eligible_filter = DpdHeadword.meaning_1 != ""

    for pos in TARGET_POS:
        words = (
            db_session.query(DpdHeadword)
            .filter(eligible_filter)
            .filter(DpdHeadword.pos == pos)
            .order_by(DpdHeadword.ebt_count.desc(), DpdHeadword.lemma_1.asc())
            .all()
        )

        if not words:
            continue

        word_count = len(words)
        # Select indices 19, 39, 59 (ranks 20, 40, 60)
        indices_to_select = []
        for idx in [19, 39, 59]:
            if idx < word_count:
                indices_to_select.append(idx)
            elif word_count >= 3:
                # Fallback: evenly distribute remaining if fewer than 60
                fallback_idx = (idx * word_count) // 60
                if fallback_idx < word_count and fallback_idx not in indices_to_select:
                    indices_to_select.append(fallback_idx)

        # Add selected words (limit to 3)
        for idx in indices_to_select[:3]:
            sample.append(words[idx])

    if limit:
        sample = sample[:limit]

    return sample


def build_translation_prompt(
    word: DpdHeadword, dpspth: DPSPaths, lang: str = "ru"
) -> List[Dict[str, str]]:
    """Wrap the production prompt logic for meaning translation.

    Args:
        word: DpdHeadword entry.
        dpspth: DPSPaths object.
        lang: Target language ('ru' or 'ta').

    Returns:
        List of message dicts for AI API.
    """
    pos_example_map = load_translation_examples(dpspth, lang)
    meaning = make_meaning_combo(word)
    example = word.example_1 if word.example_1 else ""
    translation_example = pos_example_map.get(word.pos, "")
    grammar = replace_abbreviations(word.grammar)

    if lang == "ru":
        return generate_messages_for_meaning(
            word.lemma_1, grammar, meaning, example, translation_example
        )
    elif lang == "ta":
        return generate_messages_for_meaning_ta(
            word.lemma_1, grammar, meaning, example, translation_example
        )
    else:
        pr.error(f"Unsupported language: {lang}")
        return []


def create_batch_jsonl(
    model_name: str, sample: List[DpdHeadword], dpspth: DPSPaths, lang: str = "ru"
) -> Path:
    """Create a JSONL file for OpenAI Batch API."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"eval_{model_name.replace('/', '_')}_{timestamp}.jsonl"
    file_path = dpspth.ai_for_batch_api_dir / file_name

    with open(file_path, "w", encoding="utf-8") as f:
        for word in sample:
            messages = build_translation_prompt(word, dpspth, lang)
            request = {
                "custom_id": f"eval-{word.id}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model_name,
                    "messages": messages,
                },
            }
            f.write(json.dumps(request, ensure_ascii=False) + "\n")

    return file_path


def process_sequential_batch(
    client,
    shortlist: List[str],
    sample: List[DpdHeadword],
    dpspth: DPSPaths,
    results_map: Dict,
    lang: str = "ru",
):
    """Submit, poll, and download results for each model one by one."""
    for model_name in shortlist:
        pr.info(f"--- Starting Sequential Batch for: {model_name} ---")

        # 1. Create and Upload
        jsonl_path = create_batch_jsonl(model_name, sample, dpspth, lang)
        pr.info(f"Created batch file: {jsonl_path.name}")

        with open(jsonl_path, "rb") as file_file:
            batch_input_file = client.files.create(file=file_file, purpose="batch")

        # 2. Create Batch
        batch_response = client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": f"eval batch for {model_name}"},
        )
        batch_id = batch_response.id
        pr.info(f"Batch created. ID: {batch_id}")

        # 3. Polling
        while True:
            batch_status = client.batches.retrieve(batch_id)
            status = batch_status.status

            if status == "completed":
                pr.info(f"Batch {batch_id} completed!")
                break
            elif status in ["failed", "cancelled", "expired"]:
                pr.error(f"Batch {batch_id} failed with status: {status}")
                return

            # Print progress
            counts = batch_status.request_counts
            completed = counts.completed if counts else 0
            total = counts.total if counts else 0
            pr.info(f"  Status: {status} ({completed}/{total} requests)...")
            time.sleep(30)  # Wait 30 seconds before next check

        # 4. Download and Parse
        output_file_id = batch_status.output_file_id
        file_response = client.files.content(output_file_id)

        for line in file_response.text.splitlines():
            decoded = json.loads(line)
            custom_id = decoded.get("custom_id", "")
            word_id_str = custom_id.split("-")[1] if "-" in custom_id else ""
            if word_id_str:
                word_id = int(word_id_str)
                if word_id in results_map:
                    response_data = decoded.get("response", {})
                    choices = response_data.get("body", {}).get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        results_map[word_id]["models"][model_name] = content
                    else:
                        results_map[word_id]["models"][model_name] = "ERROR: No content"


# def build_tamil_prompt(word: DpdHeadword, dpspth: DPSPaths) -> List[Dict[str, str]]:
#     """Placeholder for future Tamil prompt logic."""
#     pass


def generate_markdown_report(
    results: List[Dict], provider: str, shortlist: List[str], lang: str
) -> str:
    """Generate a side-by-side Markdown comparison report."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = "# AI Translation Evaluation Report\n\n"
    md += f"- **Date**: {ts}\n"
    md += f"- **Provider**: {provider}\n"
    md += f"- **Language**: {lang}\n"
    md += f"- **Models**: {', '.join(shortlist)}\n"
    md += "- **Sampling Strategy**: Three representative words per POS at ranks 20, 40, 60\n\n"

    # Table Header
    headers = ["ID", "Pali Word", "POS", "English Meaning"] + shortlist
    md += "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    # Table Rows
    for row in results:
        # Escape pipe characters in content to avoid breaking the table
        def escape_pipe(text: Any) -> str:
            if text is None:
                return ""
            return str(text).replace("|", "\\|").replace("\n", " ")

        cols = [
            str(row["id"]),
            escape_pipe(row["lemma"]),
            escape_pipe(row["pos"]),
            escape_pipe(row["english"]),
        ]
        for model in shortlist:
            cols.append(escape_pipe(row["models"].get(model, "")))

        md += "| " + " | ".join(cols) + " |\n"

    return md


def main():
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    api_key, provider, current_model = load_ai_config()
    pr.info(f"Active provider: {provider}")

    # Mode selection
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate AI translation models.")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models for the active provider.",
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="Generate a detailed prompt for an external AI to recommend models from the fetched list.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Use OpenAI Batch API sequentially for evaluation.",
    )
    parser.add_argument("--eval", nargs="+", help="Shortlist of models to evaluate.")
    parser.add_argument(
        "--limit", type=int, help="Limit the number of words in the evaluation sample."
    )
    parser.add_argument(
        "--lang",
        default="ru",
        choices=["ru", "ta"],
        help="Target language (default: ru).",
    )

    args = parser.parse_args()

    if args.list:
        pr.info(f"Fetching models for {provider}...")
        models = get_available_models(provider, api_key)
        for m in models:
            print(m)
        pr.info(
            "\nNOTE: You can copy this list to an external AI (like Claude or GPT-4o) to get recommendations."
        )
        pr.info(
            "External recommendations are ADVISORY ONLY. Use the chosen models with --eval to see empirical results."
        )
        return

    if args.prompt:
        pr.info(f"Fetching models for {provider} to generate recommendation prompt...")
        models = get_available_models(provider, api_key)
        model_list_str = "\n".join(f"- {m}" for m in models)

        if args.lang == "ru":
            external_prompt = f"""I need you to recommend the best AI models for a specific dictionary translation task.

### The Task
We are translating a Pali-English dictionary into Russian. The AI needs to translate the English definitions of Pali terms into Russian, taking into account the Pali context, grammatical structure, and specific dictionary formatting rules.

### Input Format
The AI receives:
- **Pali Term**: The original word (e.g., "buddha").
- **Grammar**: Grammatical properties (e.g., "pp").
- **Definition**: The English meaning (e.g., "awakened; woke up; understood").
- **Context**: (Optional) A Pali sentence showing usage.

### Translation Rules
- Translate all bracketed text (e.g., "(gram)" → "(грам)", "(comm)" → "(комм)", "(vinaya)" → "(виная)").
- Separate synonyms with `;`.
- Match the grammatical structure of the Pali term (noun, verb, etc.).
- Use lowercase unless it's a proper noun.
- Translate "lit." as "досл.".
- Retain clarifications if any (e.g., "(of trap) laid down" → "(о капкане) установленный").
- Translate idioms to Russian equivalents.
- Ensure no English remains untranslated, including within brackets.
- Output only the translation of the Definition, without labels like "Перевод" etc, without any comments, and in one line.

### Request
Below is a list of available models from our API provider ({provider}). Please recommend the top 3-5 models from this list that offer the best balance of:
1. **High translation quality**: Excellent understanding of context, grammar, and nuances in Russian.
2. **Cost-efficiency**: Avoid massive/expensive models if smaller/cheaper ones can perform this specific dictionary translation task equally well.

Please provide a brief justification for each recommendation.

### Available Models:
{model_list_str}
"""
        elif args.lang == "ta":
            external_prompt = f"""I need you to recommend the best AI models for a specific dictionary translation task.

### The Task
We are translating a Pali-English dictionary into Tamil. The AI needs to translate the English definitions of Pali terms into Tamil, taking into account the Pali context, grammatical structure, and specific dictionary formatting rules.

### Input Format
The AI receives:
- **Pali Term**: The original word (e.g., "buddha").
- **Grammar**: Grammatical properties (e.g., "pp").
- **Definition**: The English meaning (e.g., "awakened; woke up; understood").
- **Context**: (Optional) A Pali sentence showing usage.

### Translation Rules
- Translate all bracketed text (e.g., "(gram)" → "(இலக்கணம்)", "(comm)" → "(வி)", "(vinaya)" → "(வினய)").
- Separate synonyms with `;`.
- Match the grammatical structure of the Pali term (noun, verb, etc.).
- Use lowercase unless it's a proper noun.
- Retain clarifications if any.
- Translate idioms to Tamil equivalents.
- Ensure no English remains untranslated, including within brackets.
- Output only the translation of the Definition, without labels, without any comments, and in one line.

### Request
Below is a list of available models from our API provider ({provider}). Please recommend the top 3-5 models from this list that offer the best balance of:
1. **High translation quality**: Excellent understanding of context, grammar, and nuances in Tamil.
2. **Cost-efficiency**: Avoid massive/expensive models if smaller/cheaper ones can perform this specific dictionary translation task equally well.

Please provide a brief justification for each recommendation.

### Available Models:
{model_list_str}
"""
        else:
            pr.error(f"Unsupported language: {args.lang}")
            return

        print("\n" + "=" * 40 + " EXTERNAL AI PROMPT " + "=" * 40)
        print(external_prompt)
        print("=" * 100 + "\n")
        return

    if args.eval:
        shortlist = args.eval
        pr.info(f"Evaluating models: {shortlist}")

        sample = select_evaluation_sample(db_session, lang=args.lang, limit=args.limit)
        pr.info(f"Selected sample size: {len(sample)} words")

        ai_manager = AIManager()
        # Initialize results structure with word info
        results_map = {}
        for word in sample:
            results_map[word.id] = {
                "id": word.id,
                "lemma": word.lemma_1,
                "pos": word.pos,
                "english": make_meaning_combo(word),
                "models": {},
            }

        if args.batch and provider == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            process_sequential_batch(
                client, shortlist, sample, dpspth, results_map, args.lang
            )
        else:
            if args.batch:
                pr.warning(
                    "Batch API is only supported for OpenAI. Falling back to one-by-one."
                )

            # Process per model, then per word
            for model_name in shortlist:
                pr.info(f"Starting model: {model_name}")
                for word in sample:
                    pr.info(f"  Processing: {word.lemma_1} ({word.pos})")

                    messages = build_translation_prompt(word, dpspth, args.lang)

                    # We use ai_manager.request which handles rate limiting
                    # but we specify the provider and model
                    response = ai_manager.request(
                        prompt=messages[1]["content"],
                        prompt_sys=messages[0]["content"],
                        provider_preference=provider,
                        model=model_name,
                    )

                    results_map[word.id]["models"][model_name] = (
                        response.content
                        if response.content
                        else f"ERROR: {response.status_message}"
                    )

        results = list(results_map.values())

        # Save results
        output_dir = dpspth.temp_dir / "ai_eval"
        output_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw JSON
        raw_file = output_dir / f"eval_raw_{provider}_{ts}.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        pr.info(f"Raw results saved to {raw_file}")

        # Save Markdown report
        md_report = generate_markdown_report(results, provider, shortlist, args.lang)
        md_file = output_dir / f"eval_report_{provider}_{ts}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_report)
        pr.info(f"Markdown report saved to {md_file}")

    else:
        pr.warning(
            "No action specified. Use --list to see models or --eval [models...] to run evaluation."
        )

    db_session.close()


if __name__ == "__main__":
    main()
