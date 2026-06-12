"""Shared prompt-building and analysis utilities for Pāḷi AI translation."""

import copy
import json
import re
from collections.abc import Callable, Iterator
from typing import Any, cast

from sqlalchemy.orm import Session

from exporter.analysis.analyzer import analyze_sentence, tokenize_sentence
from tools.ai_manager import AIManager
from tools.printer import printer as pr


MAX_FIRST_CONTEXT_CHARS = 250_000
REFORMAT_MAX_CHARS = 3000
REFORMAT_KEYS_MAX_CHARS = 6000
MAX_RETRY_CONTEXT_CHARS = 60_000
MAX_RETRY_BATCHES = 8
CHUNK_FIRST_PASS_ATTEMPTS = 2
PREVIOUS_TRANSLATION_CONTEXT_CHARS = 1200
NO_TOOLS_INSTRUCTION = (
    "Do not use tools, do not plan tasks, and do not wait for anything. "
    "Produce the complete JSON directly in this single response."
)
NO_GRAMMAR_NOTES_INSTRUCTION = (
    "Provide ONLY the core meaning. Do NOT append grammatical case notes in "
    "parentheses."
)
COMMON_PALI_RULES = """### Common Pāḷi Disambiguation Rules:
- In the stock phrase `kāyassa bhedā paraṃ maraṇā`, `kāyassa` is genitive, `bhedā` and `maraṇā` are ablative singular, and `paraṃ` is the indeclinable preposition "after" — never nominative plurals.
- Final-vowel lengthening before quotative `'ti` is sandhi: prefer the deconstruction restoring the short final vowel (e.g., `upapajjanti + iti`) at the end of a quotation unless context clearly requires a long-vowel reading.
- In `yena <person/place> tena upasaṅkami`, `yena` and `tena` are adverbial "where ... there" rows, not plain instrumental pronouns.
- Inside direct speech, a comma-set-off word addressing the listener (e.g., `bho` or a teacher's name) is usually vocative.
- Counted time-spans such as `paṇṇavīsativassāni` / `vassāni` ("for twenty-five years") are accusative of duration, not nominative.
- When dative and genitive variants of the same surface form are offered, prefer the genitive for possession or relation ("of X"); select dative only when the context expresses a recipient, purpose, or benefit ("for/to X").
"""
_GRAMMAR_ANNOTATION_KEYWORDS = (
    "nominative",
    "accusative",
    "genitive",
    "dative",
    "instrumental",
    "locative",
    "ablative",
    "vocative",
    "singular",
    "plural",
    "masculine",
    "feminine",
    "neuter",
    "enclitic",
    "particle",
    "indeclinable",
    "optative",
    "aorist",
    "participle",
    "component of",
    "grammatical",
    "interrogative",
)
_GRAMMAR_ABBREVIATION_RE = re.compile(
    r"\b(?:masc|fem|nt|nom|acc|gen|dat|abl|instr|loc|voc|sg|pl)\."
)
_TRAILING_PUNCTUATION = '.,;:!?)]}”’"'
_RETRY_OPTION_FIELDS = (
    "key",
    "id",
    "pali",
    "pos",
    "grammar",
    "meaning_1",
    "meaning_combo",
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_SELECTION_LIST_KEYS = ("disambiguation", "sentence_analysis", "selected_meanings")
_SELECTION_KEY_FIELDS = ("selected_key", "selected_lemma_key", "key")
_FINITE_VERB_GRAMMAR_RE = re.compile(
    r"\b(?:pr|aor|fut|cond|imp|opt)\s+\d(?:st|nd|rd)\b"
)
_QUOTATIVE_TI_SELECTION_SOURCE = "deterministic_quotative_ti_deconstruction"
_PARENT_MEANING_TOKEN_RE = re.compile(r"[a-z][a-z'’-]*")
_PARENT_MEANING_STOPWORDS = {"of", "the", "a", "an", "to", "in", "is", "one's"}
_OCCURRENCE_KEY_PREFIX_RE = re.compile(r"^w\d+_(.+)$")
_RETRY_EQUIVALENT_KEY_GROUPS = "_equivalent_missing_key_groups"
_DECONSTRUCTED_PLACEHOLDER = "[Deconstructed]"
_DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE = "db_example_all_variants_tied"
_DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE = "db_example_variant_not_selected"


def extract_variant_options(text: str) -> tuple[str, dict[str, list[str]]]:
    """Resolve GUI-style // variants to first choices and collect options."""
    parts = re.split(r"(\s+)", text)
    options: dict[str, list[str]] = {}
    resolved_parts: list[str] = []

    for part in parts:
        if "//" not in part:
            resolved_parts.append(part)
            continue

        suffix = ""
        core = part
        while core and core[-1] in _TRAILING_PUNCTUATION:
            suffix = core[-1] + suffix
            core = core[:-1]

        variants = [variant for variant in core.split("//") if variant]
        if not variants:
            resolved_parts.append(part)
            continue

        options[variants[0]] = variants
        resolved_parts.append(f"{variants[0]}{suffix}")

    return "".join(resolved_parts), options


def apply_variant_choices(
    text: str,
    speech_mark_options: dict[str, list[str]],
    variant_choices: dict[str, Any] | None,
) -> str:
    """Build final text from original // variants and AI-provided option indexes."""
    if not variant_choices:
        return extract_variant_options(text)[0]

    parts = re.split(r"(\s+)", text)
    resolved_parts: list[str] = []

    for part in parts:
        if "//" not in part:
            resolved_parts.append(part)
            continue

        suffix = ""
        core = part
        while core and core[-1] in _TRAILING_PUNCTUATION:
            suffix = core[-1] + suffix
            core = core[:-1]

        variants = [variant for variant in core.split("//") if variant]
        if not variants:
            resolved_parts.append(part)
            continue

        option_key = variants[0]
        configured_variants = speech_mark_options.get(option_key, variants)
        choice_raw = variant_choices.get(option_key, 0)
        try:
            choice_index = int(choice_raw)
        except (TypeError, ValueError):
            choice_index = 0
        if choice_index < 0 or choice_index >= len(configured_variants):
            choice_index = 0

        resolved_parts.append(f"{configured_variants[choice_index]}{suffix}")

    return "".join(resolved_parts)


def sync_analysis_words_to_sentence(
    analysis: list[dict[str, Any]], sentence: str
) -> list[dict[str, Any]]:
    """Return analysis with top-level words replaced by the final sentence tokens."""
    tokens = tokenize_sentence(sentence)
    synced_analysis = copy.deepcopy(analysis)
    if len(tokens) != len(synced_analysis):
        return synced_analysis

    for token_data, token in zip(synced_analysis, tokens, strict=True):
        token_data["word"] = token
    return synced_analysis


def _normalize_ai_response(ai_data: dict[str, Any]) -> dict[str, Any]:
    """Fix malformed AI responses with nested 'scores' keys.

    Some AI models return scores in a nested structure like {"scores": {"scores": {...}}}.
    This function flattens that to the expected {"scores": {...}} format.
    """
    scores = ai_data.get("scores", {})
    if (
        isinstance(scores, dict)
        and "scores" in scores
        and not any(
            k.startswith(("decon_", "digits")) or "_" in k
            for k in scores.keys()
            if isinstance(k, str)
        )
    ):
        # The outer "scores" key only contains another "scores" key → nested structure
        ai_data["scores"] = scores["scores"]
        scores = ai_data["scores"]
    if isinstance(scores, dict):
        for key, value in list(scores.items()):
            if isinstance(value, int | float) and not isinstance(value, bool):
                scores[key] = {"score": value}
                continue
            if not isinstance(value, dict):
                continue
            contextual_meaning = value.get("contextual_meaning")
            if isinstance(contextual_meaning, str) and contextual_meaning.strip():
                value["contextual_meaning"] = _strip_grammar_annotations(
                    contextual_meaning
                )
    return ai_data


def _coerce_flat_score_map(
    ai_data: dict[str, Any],
    expected_keys: set[str],
) -> dict[str, Any]:
    """Wrap a bare ``{key: {"score": N}}`` response in the ``scores`` contract."""
    if not ai_data or "scores" in ai_data:
        return ai_data

    matched: dict[str, Any] = {}
    for key, value in ai_data.items():
        if key not in expected_keys:
            continue
        if isinstance(value, dict):
            score = value.get("score")
            if isinstance(score, int | float) and not isinstance(score, bool):
                matched[key] = value
        elif isinstance(value, int | float) and not isinstance(value, bool):
            matched[key] = {"score": value}

    if not matched or len(matched) * 2 < len(ai_data):
        return ai_data
    return {"scores": matched}


def _clean_meaning(meaning: str) -> str:
    """Strip trailing grammar parentheticals that duplicate the Grammar column.

    Removes patterns like '(masculine nominative plural of 'X')' and
    '(component of compound 'X')' that the AI inherits from DPD meaning_combo.
    """
    return re.sub(r"\s*\([^)]*'[^']+'\)\s*$", "", meaning).strip()


def _strip_grammar_annotations(text: str) -> str:
    """Remove AI-added grammar parentheticals while preserving meaning notes."""

    def replace_annotation(match: re.Match[str]) -> str:
        content = match.group(1).lower()
        if any(
            keyword in content for keyword in _GRAMMAR_ANNOTATION_KEYWORDS
        ) or _GRAMMAR_ABBREVIATION_RE.search(content):
            return ""
        return match.group(0)

    cleaned = re.sub(r"\s*\(([^()]*)\)", replace_annotation, text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s*[-,;:]\s*$", "", cleaned)
    return cleaned.strip()


def _normalize_example_text(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = text.replace("'", "")
    text = re.sub(r"[^\w]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _texts_overlap(first_text: str, second_text: str) -> bool:
    first = _normalize_example_text(first_text)
    second = _normalize_example_text(second_text)
    return bool(first and second and (first in second or second in first))


def _strip_occurrence_key_prefix(key: str) -> str:
    match = _OCCURRENCE_KEY_PREFIX_RE.match(key)
    if not match:
        return key
    return match.group(1)


def _is_deconstruction_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.startswith("decon_") or "_decon_" in key


def _is_missing_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.startswith("missing_") or "_missing_" in key


def _is_deconstructed_placeholder(meaning: Any) -> bool:
    return isinstance(meaning, str) and meaning.strip() == _DECONSTRUCTED_PLACEHOLDER


def _score_selection_source(score_data: Any) -> str:
    if not isinstance(score_data, dict):
        return ""
    selection_source = score_data.get("selection_source")
    if not isinstance(selection_source, str):
        return ""
    return selection_source


def _is_db_example_tied_score(score_data: Any) -> bool:
    return _score_selection_source(score_data) == _DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE


def _normalize_containment_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _append_unique_text_part(parts: list[str], text: Any) -> None:
    if not isinstance(text, str):
        return
    candidate = re.sub(r"\s+", " ", text).strip()
    if not candidate:
        return
    accumulated = _normalize_containment_text(" ".join(parts))
    candidate_normalized = _normalize_containment_text(candidate)
    if accumulated and candidate_normalized in accumulated:
        return
    parts.append(candidate)


def _previous_translation_block(previous_translation: str) -> str:
    normalized = re.sub(r"\s+", " ", previous_translation).strip()
    if not normalized:
        return ""
    context = normalized[-PREVIOUS_TRANSLATION_CONTEXT_CHARS:]
    return (
        "\n\nEarlier sentences of this passage were already translated as:\n"
        f"{context}\n"
        "Translate ONLY the Pāḷi text given above, as a continuation. Do not "
        "repeat already-translated sentences. Keep names, forms of address "
        "(e.g. 'monks'), and recurring terminology consistent with the earlier "
        "translation."
    )


def _iter_options(options: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for option in options:
        yield option
        for component_group in option.get("components", []):
            if isinstance(component_group, list):
                yield from _iter_options(component_group)


def pre_match_db_examples(
    analysis: list[dict[str, Any]],
    verse_source: str,
    verse_text: str,
) -> None:
    """Mark options whose curated example text overlaps the analyzed passage.

    Mutates `analysis` in-place by setting ``ai_score`` and ``db_example_match``
    on matching options. Does not return a value.
    """
    for token_data in analysis:
        for option in _iter_options(token_data.get("data", [])):
            best_match_type = ""
            for index in (1, 2):
                example = option.get(f"example_{index}", "")
                source = option.get(f"source_{index}", "")
                if not _texts_overlap(example, verse_text):
                    continue
                match_type = (
                    "source_text_overlap"
                    if source and source == verse_source
                    else "text_overlap"
                )
                if match_type == "source_text_overlap":
                    best_match_type = match_type
                    break
                if not best_match_type:
                    best_match_type = match_type

            if best_match_type:
                option["ai_score"] = 10
                option["db_example_match"] = True
                option["db_example_match_type"] = best_match_type
                option["selection_source"] = f"db_example_{best_match_type}"


def _extract_partial_response(response_text: str) -> dict[str, Any]:
    """Extract translation/literal_translation from a malformed JSON response.

    When the AI returns incomplete JSON (e.g., with template placeholders),
    extract what we can and construct a fallback response.
    """
    fallback: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": {},
    }

    # Try to extract translation using regex
    trans_match = re.search(
        r'"translation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', response_text
    )
    if trans_match:
        fallback["translation"] = trans_match.group(1).replace('\\"', '"')

    # Try to extract literal_translation
    lit_match = re.search(
        r'"literal_translation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', response_text
    )
    if lit_match:
        fallback["literal_translation"] = lit_match.group(1).replace('\\"', '"')

    # Try to extract valid score entries (those with numeric scores)
    score_matches = re.finditer(
        r'"([^"]+?)"\s*:\s*\{\s*"score"\s*:\s*(\d+)', response_text
    )
    for match in score_matches:
        key = match.group(1)
        score = int(match.group(2))
        fallback["scores"][key] = {"score": score}

    return fallback


def _parse_ai_json(response_text: str) -> tuple[dict[str, Any], str]:
    json_str = response_text.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:-3].strip()
    elif json_str.startswith("```"):
        json_str = json_str[3:-3].strip()

    try:
        return json.loads(json_str), ""
    except json.JSONDecodeError as exc:
        return _extract_partial_response(response_text), str(exc)


def _collect_option_keys(analysis: list[dict[str, Any]]) -> set[str]:
    """Gather every option `key` (including components/deconstructions) in the analysis."""
    keys: set[str] = set()
    for token_data in analysis:
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            if isinstance(key, str):
                keys.add(key)
    return keys


def _word_keys_overview(analysis: list[dict[str, Any]]) -> str:
    """Build a compact top-level option-key map for the reformat prompt."""
    word_keys: dict[str, list[str]] = {}
    for token_data in analysis:
        word = token_data.get("word")
        options = token_data.get("data", [])
        if not isinstance(word, str) or not word or not isinstance(options, list):
            continue

        keys = word_keys.setdefault(word, [])
        for option in options:
            if not isinstance(option, dict):
                continue
            key = option.get("key")
            if not isinstance(key, str):
                continue
            seen_keys = {display_key.split(" ", 1)[0] for display_key in keys}
            if key in seen_keys:
                continue
            grammar = option.get("grammar")
            if isinstance(grammar, str) and grammar.strip():
                keys.append(f"{key} ({grammar.strip()})")
            else:
                keys.append(key)

        if not keys:
            word_keys.pop(word, None)

    if not word_keys:
        return ""

    overview = json.dumps(word_keys, ensure_ascii=False, separators=(",", ":"))
    if len(overview) > REFORMAT_KEYS_MAX_CHARS:
        return ""
    return overview


def _extract_word_key_map(
    ai_data: dict[str, Any],
    analysis: list[dict[str, Any]],
) -> dict[str, str] | None:
    """Detect a flat or ``{"disambiguation": {...}}`` word-key map.

    Antigravity/Gemini routinely returns this compact shape instead of the required
    ``{translation, literal_translation, scores}`` schema. When the values are real
    option keys from the analysis, the map IS the disambiguation we want. Returns
    ``None`` when the response is not such a map (proper schema, dict-valued, unknown
    keys, or empty).
    """
    if not isinstance(ai_data, dict) or not ai_data:
        return None
    if "scores" in ai_data or "translation" in ai_data:
        return None
    candidate = ai_data
    if set(ai_data) == {"disambiguation"}:
        disambiguation = ai_data["disambiguation"]
        if not isinstance(disambiguation, dict) or not disambiguation:
            return None
        candidate = disambiguation
    valid_keys = _collect_option_keys(analysis)
    if not valid_keys:
        return None
    matched = {
        surface_word: value
        for surface_word, value in candidate.items()
        if isinstance(value, str) and value in valid_keys
    }
    if not matched or len(matched) * 2 < len(candidate):
        return None
    return matched


def _top_level_options_for_word(
    analysis: list[dict[str, Any]], word: str
) -> list[dict[str, Any]]:
    for token_data in analysis:
        if token_data.get("word") != word:
            continue
        options = token_data.get("data", [])
        if not isinstance(options, list):
            return []
        return [option for option in options if isinstance(option, dict)]
    return []


def _matching_key_by_id(
    analysis: list[dict[str, Any]],
    word: str,
    option_id: int,
) -> str | None:
    matched_keys = [
        key
        for option in _top_level_options_for_word(analysis, word)
        if option.get("id") == option_id
        for key in [option.get("key")]
        if isinstance(key, str)
    ]
    if len(matched_keys) == 1:
        return matched_keys[0]
    return None


def _matching_key_by_lemma(
    analysis: list[dict[str, Any]],
    word: str,
    lemma: str,
) -> str | None:
    matched_keys = [
        key
        for option in _top_level_options_for_word(analysis, word)
        if option.get("lemma") == lemma
        for key in [option.get("key")]
        if isinstance(key, str)
    ]
    if len(matched_keys) == 1:
        return matched_keys[0]
    return None


def _structured_selection_result(
    word_key_map: dict[str, str],
    word_meaning_map: dict[str, str],
    candidate_count: int,
) -> tuple[dict[str, str], dict[str, str]] | None:
    if not word_key_map or len(word_key_map) * 2 < candidate_count:
        return None
    return word_key_map, word_meaning_map


def _top_level_key_words(analysis: list[dict[str, Any]]) -> dict[str, set[str]]:
    key_words: dict[str, set[str]] = {}
    for token_data in analysis:
        word = token_data.get("word")
        options = token_data.get("data", [])
        if not isinstance(word, str) or not word or not isinstance(options, list):
            continue
        for option in options:
            if not isinstance(option, dict):
                continue
            key = option.get("key")
            if isinstance(key, str):
                key_words.setdefault(key, set()).add(word)
    return key_words


def _extract_selected_keys_map(
    ai_data: dict[str, Any],
    analysis: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]] | None:
    """Recover a top-level ``selected_keys`` list into a word-key map."""
    if not isinstance(ai_data, dict) or set(ai_data) != {"selected_keys"}:
        return None
    raw_keys = ai_data["selected_keys"]
    if (
        not isinstance(raw_keys, list)
        or not raw_keys
        or not all(isinstance(key, str) for key in raw_keys)
    ):
        return None

    key_words = _top_level_key_words(analysis)
    word_key_map: dict[str, str] = {}
    for raw_key in raw_keys:
        words = key_words.get(raw_key)
        if not words or len(words) != 1:
            continue
        word = next(iter(words))
        if word in word_key_map:
            return None
        word_key_map[word] = raw_key

    return _structured_selection_result(word_key_map, {}, len(raw_keys))


def _extract_structured_selection_map(
    ai_data: dict[str, Any],
    analysis: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]] | None:
    """Recover wrong-schema structured selections into a word-key map."""
    if not isinstance(ai_data, dict) or not ai_data:
        return None
    if "scores" in ai_data or "translation" in ai_data:
        return None

    valid_keys = _collect_option_keys(analysis)
    if not valid_keys:
        return None

    if len(ai_data) == 1:
        list_key = next(iter(ai_data))
        if list_key in _SELECTION_LIST_KEYS:
            raw_items = ai_data[list_key]
            if not isinstance(raw_items, list) or not raw_items:
                return None
            if not all(isinstance(item, dict) for item in raw_items):
                return None

            word_key_map: dict[str, str] = {}
            word_meaning_map: dict[str, str] = {}
            for item in raw_items:
                word = item.get("word")
                if not isinstance(word, str) or not word:
                    continue

                selected_key = None
                for field in _SELECTION_KEY_FIELDS:
                    raw_key = item.get(field)
                    if isinstance(raw_key, str):
                        selected_key = raw_key if raw_key in valid_keys else None
                        break

                if selected_key is None:
                    raw_id = item.get("selected_id", item.get("id"))
                    if isinstance(raw_id, int) and not isinstance(raw_id, bool):
                        selected_key = _matching_key_by_id(analysis, word, raw_id)

                if selected_key is None:
                    continue

                word_key_map[word] = selected_key
                meaning = item.get("meaning")
                if isinstance(meaning, str) and meaning.strip():
                    word_meaning_map[word] = _strip_grammar_annotations(meaning)

            return _structured_selection_result(
                word_key_map, word_meaning_map, len(raw_items)
            )

    lemma_items = [
        (word, value)
        for word, value in ai_data.items()
        if isinstance(word, str)
        and isinstance(value, dict)
        and isinstance(value.get("lemma"), str)
    ]
    if not lemma_items or len(lemma_items) * 2 < len(ai_data):
        return None

    word_key_map = {}
    word_meaning_map = {}
    for word, item in lemma_items:
        lemma = item["lemma"]
        if not isinstance(lemma, str):
            continue
        selected_key = _matching_key_by_lemma(analysis, word, lemma)
        if selected_key is None:
            continue
        word_key_map[word] = selected_key
        meaning = item.get("meaning")
        if isinstance(meaning, str) and meaning.strip():
            word_meaning_map[word] = _strip_grammar_annotations(meaning)

    return _structured_selection_result(
        word_key_map, word_meaning_map, len(lemma_items)
    )


def _build_translation_prompt(
    sentence: str,
    surface_words: list[str] | None = None,
    previous_translation: str = "",
) -> str:
    """Build a lightweight translation-only follow-up prompt.

    Used when the first call returned a usable word→key map but no translation; we only
    need the prose and contextual meanings, so this prompt is small and does not re-send
    the dictionary context.
    """
    surface_words_instruction = ""
    if surface_words:
        surface_words_json = json.dumps(surface_words, ensure_ascii=False)
        surface_words_instruction = (
            f"\nUse exactly these surface-word keys in meanings: {surface_words_json}\n"
        )
    continuation_block = _previous_translation_block(previous_translation)
    continuation_section = f"{continuation_block}\n\n" if continuation_block else ""
    return (
        f'Translate this Pāḷi sentence into English: "{sentence}"\n\n'
        f"{continuation_section}"
        "Return ONLY a JSON object with these three keys and nothing else:\n"
        "{\n"
        '  "translation": "Fluent English translation of the sentence",\n'
        '  "literal_translation": "Literal word-by-word English translation",\n'
        '  "meanings": {"surface_word": "short contextual English meaning"}\n'
        "}\n"
        f"{surface_words_instruction}"
        f"{NO_GRAMMAR_NOTES_INSTRUCTION}\n"
        "No prose, no markdown fences, no scores."
    )


def _is_quotative_ti_token(word: Any) -> bool:
    if not isinstance(word, str):
        return False
    normalized = word.lower().replace("’", "'").rstrip(_TRAILING_PUNCTUATION)
    return normalized.endswith("'ti")


def _construction_parts(option: dict[str, Any]) -> list[str]:
    construction = option.get("construction")
    if not isinstance(construction, str):
        return []
    clean_construction = construction.replace("<b>", "").replace("</b>", "")
    return [
        part.strip().lower().replace("’", "'")
        for part in clean_construction.split("+")
        if part.strip()
    ]


def _is_iti_final_deconstruction(option: dict[str, Any]) -> bool:
    key = option.get("key")
    if not _is_deconstruction_key(key):
        return False
    parts = _construction_parts(option)
    return len(parts) >= 2 and parts[-1] == "iti"


def _finite_verb_first_component(option: dict[str, Any]) -> dict[str, Any] | None:
    components = option.get("components")
    if not isinstance(components, list) or not components:
        return None
    first_group = components[0]
    if not isinstance(first_group, list):
        return None
    for component in first_group:
        if not isinstance(component, dict):
            continue
        pos = component.get("pos")
        grammar = component.get("grammar")
        if (
            isinstance(pos, str)
            and pos.lower() == "verb"
            and isinstance(grammar, str)
            and _FINITE_VERB_GRAMMAR_RE.search(grammar.lower())
        ):
            return component
    return None


def _component_contextual_meaning(component: dict[str, Any]) -> str:
    for field in ("meaning_combo", "meaning_1"):
        meaning = component.get(field)
        if isinstance(meaning, str) and meaning.strip():
            return _strip_grammar_annotations(meaning)
    return ""


def _copy_score_context_fields(
    source_score: Any,
    target_score: dict[str, Any],
) -> None:
    if not isinstance(source_score, dict):
        return
    for field in ("contextual_meaning", "selected_pos"):
        value = source_score.get(field)
        if value:
            target_score[field] = value


def _numeric_score_value(score_data: Any) -> int | float | None:
    if isinstance(score_data, dict):
        score = score_data.get("score")
    else:
        score = score_data
    if isinstance(score, int | float) and not isinstance(score, bool):
        return score
    return None


def _positive_ai_score_value(score_data: Any) -> float | None:
    score = _numeric_score_value(score_data)
    if score is None or score <= 0:
        return None
    return float(score)


def _deterministic_score_value(option: dict[str, Any]) -> int | float | None:
    return _numeric_score_value(option.get("ai_score"))


def _db_example_group_key(option: dict[str, Any]) -> str:
    option_id = option.get("id")
    if isinstance(option_id, int | str) and not isinstance(option_id, bool):
        return str(option_id)
    key = option.get("key")
    if isinstance(key, str):
        return key.split("_", 1)[0]
    return ""


def _deterministic_selection_source(option: dict[str, Any]) -> str:
    selection_source = option.get("selection_source")
    if isinstance(selection_source, str) and selection_source:
        return selection_source
    return "deterministic"


def _apply_quotative_ti_deconstruction_score(
    token_data: dict[str, Any],
    scores_map: dict[str, Any],
) -> None:
    if not _is_quotative_ti_token(token_data.get("word")):
        return

    deconstruction_options = [
        option
        for option in token_data.get("data", [])
        if isinstance(option, dict) and _is_iti_final_deconstruction(option)
    ]
    finite_matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for option in deconstruction_options:
        finite_component = _finite_verb_first_component(option)
        if finite_component:
            finite_matches.append((option, finite_component))

    if len(finite_matches) != 1:
        return

    winning_option, finite_component = finite_matches[0]
    winning_key = winning_option.get("key")
    if not isinstance(winning_key, str):
        return

    winning_score: dict[str, Any] = {
        "score": 10,
        "selection_source": _QUOTATIVE_TI_SELECTION_SOURCE,
    }
    _copy_score_context_fields(scores_map.get(winning_key), winning_score)
    if "contextual_meaning" not in winning_score:
        contextual_meaning = _component_contextual_meaning(finite_component)
        if contextual_meaning:
            winning_score["contextual_meaning"] = contextual_meaning
    scores_map[winning_key] = winning_score

    for option in deconstruction_options:
        key = option.get("key")
        if not isinstance(key, str) or key == winning_key:
            continue
        demoted_score: dict[str, Any] = {
            "score": 0,
            "selection_source": _QUOTATIVE_TI_SELECTION_SOURCE,
        }
        _copy_score_context_fields(scores_map.get(key), demoted_score)
        scores_map[key] = demoted_score


def _apply_deterministic_scores_to_map(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> None:
    for token_data in analysis:
        _apply_quotative_ti_deconstruction_score(token_data, scores_map)
        preexisting_scores = dict(scores_map)
        db_example_groups: dict[str, list[dict[str, Any]]] = {}
        handled_db_keys: set[str] = set()
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            if not isinstance(key, str):
                continue
            score = _deterministic_score_value(option)
            if option.get("db_example_match") and score is not None:
                group_key = _db_example_group_key(option)
                if group_key:
                    db_example_groups.setdefault(group_key, []).append(option)
                    handled_db_keys.add(key)

        for group_options in db_example_groups.values():
            positive_scores: dict[str, float] = {}
            for option in group_options:
                key = option.get("key")
                if not isinstance(key, str):
                    continue
                positive_score = _positive_ai_score_value(preexisting_scores.get(key))
                if positive_score is not None:
                    positive_scores[key] = positive_score

            if positive_scores:
                top_score = max(positive_scores.values())
                winner_keys = {
                    key for key, score in positive_scores.items() if score == top_score
                }
                for option in group_options:
                    key = option.get("key")
                    if not isinstance(key, str):
                        continue
                    if key in winner_keys:
                        deterministic_score: dict[str, Any] = {
                            "score": 10,
                            "selection_source": _deterministic_selection_source(option),
                        }
                        _copy_score_context_fields(
                            preexisting_scores.get(key),
                            deterministic_score,
                        )
                        scores_map[key] = deterministic_score
                    elif key not in preexisting_scores:
                        scores_map[key] = {
                            "score": 0,
                            "selection_source": _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
                        }
                continue

            for option in group_options:
                key = option.get("key")
                score = _deterministic_score_value(option)
                if not isinstance(key, str) or score is None:
                    continue
                selection_source = _deterministic_selection_source(option)
                if len(group_options) > 1:
                    selection_source = _DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE
                deterministic_score = {
                    "score": score,
                    "selection_source": selection_source,
                }
                _copy_score_context_fields(
                    preexisting_scores.get(key),
                    deterministic_score,
                )
                scores_map[key] = deterministic_score

        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            score = _deterministic_score_value(option)
            if (
                isinstance(key, str)
                and key not in handled_db_keys
                and key not in scores_map
                and score is not None
            ):
                scores_map[key] = {
                    "score": score,
                    "selection_source": _deterministic_selection_source(option),
                }


def _find_missing_score_groups(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> list[dict[str, Any]]:
    missing_groups: list[dict[str, Any]] = []
    seen: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}

    def record_equivalent_key_group(
        group: dict[str, Any],
        option_keys: list[str],
    ) -> None:
        equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS)
        if not isinstance(equivalent_groups, list):
            equivalent_groups = []
            group[_RETRY_EQUIVALENT_KEY_GROUPS] = equivalent_groups
        equivalent_groups.append(option_keys)

    def group_needs_scores(option_keys: list[str]) -> bool:
        score_entries = [scores_map[key] for key in option_keys if key in scores_map]
        if not score_entries:
            return True
        if any(_is_db_example_tied_score(score_entry) for score_entry in score_entries):
            return not any(
                _positive_ai_score_value(score_entry) is not None
                and not _is_db_example_tied_score(score_entry)
                for score_entry in score_entries
            )
        return False

    def inspect_group(
        word: str,
        options: list[dict[str, Any]],
        context: str,
    ) -> None:
        if not options:
            return
        option_keys: list[str] = []
        for option in options:
            key = option.get("key")
            if isinstance(key, str):
                option_keys.append(key)
        if option_keys and group_needs_scores(option_keys):
            signature = (
                word,
                tuple(_strip_occurrence_key_prefix(key) for key in option_keys),
            )
            existing_group = seen.get(signature)
            if existing_group is not None:
                record_equivalent_key_group(existing_group, option_keys)
            else:
                group = {
                    "word": word,
                    "context": context,
                    "missing_keys": option_keys,
                    "options": [
                        {
                            key: option.get(key, "")
                            for key in (
                                "key",
                                "id",
                                "pali",
                                "pos",
                                "grammar",
                                "meaning_1",
                                "meaning_combo",
                                "example_1",
                                "source_1",
                                "example_2",
                                "source_2",
                            )
                        }
                        for option in options
                    ],
                }
                record_equivalent_key_group(group, option_keys)
                seen[signature] = group
                missing_groups.append(group)

        for option in options:
            option_context = str(option.get("pali") or option.get("key") or context)
            for component_group in option.get("components", []):
                if isinstance(component_group, list):
                    inspect_group(word, component_group, option_context)

    for token_data in analysis:
        word = str(token_data.get("word", ""))
        inspect_group(word, token_data.get("data", []), word)

    return missing_groups


def _narrow_db_example_tied_groups(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> None:
    for token_data in analysis:
        db_example_groups: dict[str, list[dict[str, Any]]] = {}
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            if not isinstance(key, str):
                continue
            if not option.get("db_example_match"):
                continue
            if _deterministic_score_value(option) is None:
                continue
            group_key = _db_example_group_key(option)
            if group_key:
                db_example_groups.setdefault(group_key, []).append(option)

        for group_options in db_example_groups.values():
            tied_keys = [
                key
                for option in group_options
                if isinstance(key := option.get("key"), str)
                and _is_db_example_tied_score(scores_map.get(key))
            ]
            if not tied_keys:
                continue

            positive_scores: dict[str, float] = {}
            for option in group_options:
                key = option.get("key")
                if not isinstance(key, str):
                    continue
                score_data = scores_map.get(key)
                if _is_db_example_tied_score(score_data):
                    continue
                positive_score = _positive_ai_score_value(score_data)
                if positive_score is not None:
                    positive_scores[key] = positive_score

            if not positive_scores:
                continue

            top_score = max(positive_scores.values())
            winner_keys = {
                key for key, score in positive_scores.items() if score == top_score
            }
            for option in group_options:
                key = option.get("key")
                if not isinstance(key, str):
                    continue
                score_data = scores_map.get(key)
                if key in winner_keys:
                    winning_score: dict[str, Any] = {
                        "score": 10,
                        "selection_source": _deterministic_selection_source(option),
                    }
                    _copy_score_context_fields(score_data, winning_score)
                    scores_map[key] = winning_score
                elif _is_db_example_tied_score(score_data):
                    scores_map[key] = {
                        "score": 0,
                        "selection_source": _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
                    }


def _batch_missing_groups(
    missing_groups: list[dict[str, Any]],
    max_chars: int,
) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_len = 0
    for group in missing_groups:
        group_len = len(json.dumps(group, ensure_ascii=False, separators=(",", ":")))
        if current and current_len + group_len > max_chars:
            batches.append(current)
            current = []
            current_len = 0
        current.append(group)
        current_len += group_len
    if current:
        batches.append(current)
    return batches


def _build_reformat_prompt(
    sentence: str,
    prose_response: str,
    word_keys_json: str = "",
) -> str:
    """Build a follow-up prompt asking the AI to reformat its response into the required JSON schema."""
    keys_block = ""
    if word_keys_json:
        keys_block = (
            '\n\nValid option keys per word (entries may be shown as "key (grammar)"; '
            'keys in "scores" MUST use the key before the first space):\n'
            f"{word_keys_json}"
        )

    return (
        f'Your previous response for the Pāḷi sentence "{sentence}" did not match '
        "the required format. Please reformat it as a JSON object matching this structure exactly:\n\n"
        "{\n"
        '  "translation": "Fluent English translation of the sentence",\n'
        '  "literal_translation": "Literal word-by-word English translation",\n'
        '  "scores": {\n'
        '    "w0_12345_0": {"score": 10, "contextual_meaning": "..."},\n'
        "    ...\n"
        "  }\n"
        "}\n\n"
        "Extract the translation from your previous analysis and convert each selected "
        "lemma to a score entry of 10 with its key. "
        f"{NO_GRAMMAR_NOTES_INSTRUCTION} "
        "Do not invent contextual_meaning; include contextual_meaning only when it "
        "appeared explicitly in the previous analysis for that selected word/key. "
        "Return only the JSON object. No prose, no markdown fences."
        f"{keys_block}\n\n"
        "Your previous analysis:\n"
        f"{prose_response[:REFORMAT_MAX_CHARS]}"
    )


def _has_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _wrong_schema_has_meaning_evidence(ai_data: dict[str, Any]) -> bool:
    scores = ai_data.get("scores")
    if isinstance(scores, dict):
        for value in scores.values():
            if isinstance(value, dict) and _has_non_empty_string(
                value.get("contextual_meaning")
            ):
                return True

    for value in ai_data.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _has_non_empty_string(
                    item.get("meaning")
                ):
                    return True
        elif isinstance(value, dict) and _has_non_empty_string(value.get("meaning")):
            return True
    return False


def _strip_reformat_context_fields(scores: dict[str, Any]) -> None:
    for value in scores.values():
        if isinstance(value, dict):
            value.pop("contextual_meaning", None)
            value.pop("selected_pos", None)


def _trim_groups_for_retry(
    missing_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    for group in missing_groups:
        trimmed_group = {
            "word": group.get("word", ""),
            "context": group.get("context", ""),
            "missing_keys": group.get("missing_keys", []),
            "options": [
                {field: option.get(field, "") for field in _RETRY_OPTION_FIELDS}
                for option in group.get("options", [])
                if isinstance(option, dict)
            ],
        }
        equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS)
        if isinstance(equivalent_groups, list):
            trimmed_group[_RETRY_EQUIVALENT_KEY_GROUPS] = copy.deepcopy(
                equivalent_groups
            )
        trimmed.append(trimmed_group)
    return trimmed


def _retry_prompt_groups(
    missing_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "word": group.get("word", ""),
            "context": group.get("context", ""),
            "missing_keys": group.get("missing_keys", []),
            "options": group.get("options", []),
        }
        for group in missing_groups
    ]


def _build_missing_scores_prompt(
    sentence: str,
    missing_groups: list[dict[str, Any]],
) -> str:
    context = json.dumps(
        _retry_prompt_groups(missing_groups),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    has_decon = any(
        _is_deconstruction_key(key)
        for group in missing_groups
        for key in group.get("missing_keys", [])
    )
    decon_instruction = ""
    if has_decon:
        decon_instruction = (
            '\nFor deconstruction keys containing "decon_", you MUST include "contextual_meaning" '
            "with a full English translation of that sandhi/compound in the context of the sentence. "
            'Example: "w0_decon_okassa_0": {"score": 10, "contextual_meaning": "to the dwelling"}\n'
        )

    return f"""Please supply missing dictionary option scores for this Pāḷi sentence:
{sentence}

Only score the option keys in this focused context. Return JSON with a flat `scores`
object where each value is {{"score": N}} (an integer 0–10). Do not translate again and do not explain.
For the single best option per word (score 10), also include "contextual_meaning": a short English meaning fitted to this sentence.
{NO_GRAMMAR_NOTES_INSTRUCTION}
{decon_instruction}
{COMMON_PALI_RULES}
Missing dictionary option scores:
{context}
"""


def _fan_out_retry_scores(
    retry_scores: dict[str, Any],
    retry_groups: list[dict[str, Any]],
) -> None:
    for group in retry_groups:
        representative_keys = group.get("missing_keys", [])
        equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS, [])
        if not isinstance(representative_keys, list) or not isinstance(
            equivalent_groups, list
        ):
            continue

        for representative_key in representative_keys:
            if not isinstance(representative_key, str):
                continue
            if representative_key not in retry_scores:
                continue
            canonical_key = _strip_occurrence_key_prefix(representative_key)
            for equivalent_group in equivalent_groups:
                if not isinstance(equivalent_group, list):
                    continue
                for equivalent_key in equivalent_group:
                    if (
                        isinstance(equivalent_key, str)
                        and equivalent_key not in retry_scores
                        and _strip_occurrence_key_prefix(equivalent_key)
                        == canonical_key
                    ):
                        retry_scores[equivalent_key] = copy.deepcopy(
                            retry_scores[representative_key]
                        )


def _request_missing_score_retry_pass(
    *,
    resolved_sentence: str,
    missing_groups: list[dict[str, Any]],
    scores_map: dict[str, Any],
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    debug: dict[str, Any] | None,
    pass_number: int,
) -> list[dict[str, Any]]:
    retry_groups = _trim_groups_for_retry(missing_groups)
    batches = _batch_missing_groups(retry_groups, MAX_RETRY_CONTEXT_CHARS)
    skipped_groups = [group for batch in batches[MAX_RETRY_BATCHES:] for group in batch]

    for batch in batches[:MAX_RETRY_BATCHES]:
        batch_keys: list[str] = []
        expected_keys: set[str] = set()
        for group in batch:
            missing_keys = group.get("missing_keys", [])
            if isinstance(missing_keys, list):
                valid_missing_keys = [
                    key for key in missing_keys if isinstance(key, str)
                ]
                batch_keys.extend(valid_missing_keys)
                expected_keys.update(valid_missing_keys)
            equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS, [])
            if isinstance(equivalent_groups, list):
                for equivalent_group in equivalent_groups:
                    if isinstance(equivalent_group, list):
                        expected_keys.update(
                            key for key in equivalent_group if isinstance(key, str)
                        )

        retry_prompt = _build_missing_scores_prompt(resolved_sentence, batch)
        retry_response = ai_manager.request(
            prompt=retry_prompt,
            model=model,
            provider_preference=provider,
            prompt_sys=(
                f"Return only JSON with a flat `scores` object. {NO_TOOLS_INSTRUCTION}"
            ),
        )
        retry_data: dict[str, Any] = {}
        retry_parse_error = ""
        if retry_response.content:
            retry_data, retry_parse_error = _parse_ai_json(retry_response.content)
            retry_data = _normalize_ai_response(retry_data)
            retry_data = _coerce_flat_score_map(retry_data, expected_keys)
            retry_data = _normalize_ai_response(retry_data)
            retry_scores = retry_data.get("scores", {})
            if isinstance(retry_scores, dict):
                _fan_out_retry_scores(retry_scores, batch)
                scores_map.update(retry_scores)
        if debug is not None:
            retry_debug: dict[str, Any] = {
                "prompt": retry_prompt,
                "raw_response": retry_response.content,
                "status_message": retry_response.status_message,
                "parsed_response": copy.deepcopy(retry_data),
                "parse_error": retry_parse_error,
                "missing_keys": batch_keys,
            }
            if pass_number > 1:
                retry_debug["pass"] = pass_number
            debug["retry_requests"].append(retry_debug)

    return skipped_groups


def _analysis_context_len(analysis: list[dict[str, Any]]) -> int:
    return len(json.dumps(analysis, ensure_ascii=False, separators=(",", ":")))


def _split_into_sentence_chunks(
    resolved_sentence: str,
    analysis: list[dict[str, Any]],
    max_context_chars: int,
) -> list[tuple[str, list[dict[str, Any]]]]:
    whole = json.dumps(analysis, ensure_ascii=False, separators=(",", ":"))
    if len(whole) <= max_context_chars:
        return [(resolved_sentence, analysis)]

    sentences = [
        sentence
        for sentence in _SENTENCE_SPLIT_RE.split(resolved_sentence)
        if sentence.strip()
    ]
    if len(sentences) < 2:
        return [(resolved_sentence, analysis)]

    counts = [len(tokenize_sentence(sentence)) for sentence in sentences]
    if sum(counts) != len(analysis):
        return [(resolved_sentence, analysis)]

    sentence_slices: list[tuple[str, list[dict[str, Any]]]] = []
    start = 0
    for sentence, count in zip(sentences, counts, strict=True):
        end = start + count
        sentence_slices.append((sentence, analysis[start:end]))
        start = end

    chunks: list[tuple[str, list[dict[str, Any]]]] = []
    current_sentences: list[str] = []
    current_analysis: list[dict[str, Any]] = []
    for sentence, sentence_analysis in sentence_slices:
        candidate_analysis = [*current_analysis, *sentence_analysis]
        if (
            current_analysis
            and _analysis_context_len(candidate_analysis) > max_context_chars
        ):
            chunks.append((" ".join(current_sentences), current_analysis))
            current_sentences = [sentence]
            current_analysis = list(sentence_analysis)
        else:
            current_sentences.append(sentence)
            current_analysis = candidate_analysis

    if current_sentences:
        chunks.append((" ".join(current_sentences), current_analysis))
    return chunks or [(resolved_sentence, analysis)]


def _merge_chunk_ai_data(chunk_datas: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": {},
        "variant_choices": {},
    }
    translations: list[str] = []
    literals: list[str] = []
    for data in chunk_datas:
        translation = data.get("translation")
        _append_unique_text_part(translations, translation)
        literal = data.get("literal_translation")
        _append_unique_text_part(literals, literal)
        scores = data.get("scores")
        if isinstance(scores, dict):
            for key, value in scores.items():
                merged["scores"].setdefault(key, value)
        variant_choices = data.get("variant_choices")
        if isinstance(variant_choices, dict):
            for key, value in variant_choices.items():
                merged["variant_choices"].setdefault(key, value)
    merged["translation"] = " ".join(translations)
    merged["literal_translation"] = " ".join(literals)
    return merged


def _handle_compact_map_response(
    *,
    chunk_sentence: str,
    word_key_map: dict[str, str],
    word_meanings: dict[str, str] | None = None,
    previous_translation: str = "",
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
) -> dict[str, Any]:
    if verbose:
        pr.amber(
            "  Word→key disambiguation map detected — using it for scores, "
            "fetching translation only"
        )
    word_key_scores: dict[str, Any] = {
        key: {"score": 10} for key in word_key_map.values()
    }
    if word_meanings:
        for surface_word, key in word_key_map.items():
            contextual_meaning = word_meanings.get(surface_word)
            if isinstance(contextual_meaning, str) and contextual_meaning.strip():
                word_key_scores[key]["contextual_meaning"] = contextual_meaning.strip()
    ai_data: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": word_key_scores,
    }
    if progress:
        progress("ai_translation_start")
    translation_response = ai_manager.request(
        prompt=_build_translation_prompt(
            chunk_sentence,
            list(word_key_map),
            previous_translation=previous_translation,
        ),
        model=model,
        provider_preference=provider,
        prompt_sys=(
            "Return only a JSON object with translation, literal_translation, "
            f"and meanings. No prose. No markdown. {NO_TOOLS_INSTRUCTION}"
        ),
    )
    if progress:
        progress("ai_translation_done")
    if verbose:
        pr.green(f"  Translation response: {translation_response.status_message}")
    translation_data: dict[str, Any] = {}
    translation_error = ""
    if translation_response.content:
        translation_data, translation_error = _parse_ai_json(
            translation_response.content
        )
        if isinstance(translation_data, dict):
            ai_data["translation"] = translation_data.get("translation", "") or ""
            ai_data["literal_translation"] = (
                translation_data.get("literal_translation", "") or ""
            )
            meanings = translation_data.get("meanings", {})
            if isinstance(meanings, dict):
                for surface_word, key in word_key_map.items():
                    contextual_meaning = meanings.get(surface_word)
                    if (
                        isinstance(contextual_meaning, str)
                        and contextual_meaning.strip()
                    ):
                        word_key_scores[key]["contextual_meaning"] = (
                            contextual_meaning.strip()
                        )
    if debug is not None:
        debug["translation_raw_response"] = translation_response.content
        debug["translation_status_message"] = translation_response.status_message
        debug["translation_parsed_response"] = copy.deepcopy(translation_data)
        debug["translation_parse_error"] = translation_error
    return ai_data


def _handle_reformat_response(
    *,
    chunk_sentence: str,
    raw_response: str,
    analysis: list[dict[str, Any]],
    ai_data: dict[str, Any],
    parse_error: str,
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
) -> dict[str, Any]:
    if verbose:
        if parse_error:
            pr.amber(f"  Non-JSON response — parse error: {parse_error}")
        else:
            pr.amber(
                "  Valid JSON but wrong schema — "
                f"scores key is {type(ai_data.get('scores')).__name__}, expected dict"
            )
        pr.amber("  Full raw response:")
        pr.amber(raw_response)
        pr.amber("  Reformatting...")
    if progress:
        progress("ai_reformat_start")
    reformat_response = ai_manager.request(
        prompt=_build_reformat_prompt(
            chunk_sentence,
            raw_response,
            _word_keys_overview(analysis),
        ),
        model=model,
        provider_preference=provider,
        prompt_sys=(
            "Return only a valid JSON object. No prose. No markdown. "
            f"{NO_TOOLS_INSTRUCTION}"
        ),
    )
    if progress:
        progress("ai_reformat_done")
    if verbose:
        pr.green(f"  Reformat response: {reformat_response.status_message}")
    if reformat_response.content:
        reformat_data, reformat_error = _parse_ai_json(reformat_response.content)
        reformat_scores = reformat_data.get("scores")
        reformat_ok = not reformat_error and isinstance(reformat_scores, dict)
        if reformat_ok:
            reformat_scores = cast(dict[str, Any], reformat_scores)
            if not parse_error and not _wrong_schema_has_meaning_evidence(ai_data):
                _strip_reformat_context_fields(reformat_scores)
            salvaged_scores = ai_data.get("scores")
            if isinstance(salvaged_scores, dict) and salvaged_scores:
                reformat_data["scores"] = {
                    **reformat_scores,
                    **salvaged_scores,
                }
            ai_data = reformat_data
            if verbose:
                pr.yes("  Reformat succeeded — scores dict present")
        else:
            if verbose:
                pr.no(
                    f"  Reformat failed — parse_error={reformat_error!r}, "
                    f"scores type={type(reformat_data.get('scores')).__name__}"
                )
        if debug is not None:
            debug["reformat_raw_response"] = reformat_response.content
            debug["reformat_status_message"] = reformat_response.status_message
            debug["reformat_parsed_response"] = copy.deepcopy(reformat_data)
            debug["reformat_parse_error"] = reformat_error

    return ai_data


def _request_first_pass(
    chunk_sentence: str,
    full_sentence: str,
    analysis: list[dict[str, Any]],
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    speech_mark_options: dict[str, list[str]] | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
    previous_translation: str = "",
) -> dict[str, Any]:
    sys_prompt = build_system_prompt(analysis, speech_mark_options)
    continuation_block = _previous_translation_block(previous_translation)
    if chunk_sentence == full_sentence:
        user_prompt = f"Return JSON for: {chunk_sentence}"
    else:
        user_prompt = (
            f"Return JSON for: {chunk_sentence}\n"
            "Full passage for context (score ONLY the words in your part): "
            f"{full_sentence}"
        )
    if continuation_block:
        user_prompt = f"{user_prompt}{continuation_block}"
    if debug is not None:
        debug["chunk_sentence"] = chunk_sentence
        debug["system_prompt"] = sys_prompt
        debug["user_prompt"] = user_prompt

    if progress:
        progress("ai_start")
    response = ai_manager.request(
        prompt=user_prompt,
        model=model,
        provider_preference=provider,
        prompt_sys=sys_prompt,
    )
    if progress:
        progress("ai_done")

    if not response.content:
        raise ValueError(f"AI Request Failed: {response.status_message}")

    if verbose:
        pr.green(f"  AI response: {response.status_message}")

    ai_data, parse_error = _parse_ai_json(response.content)
    if debug is not None:
        debug["raw_response"] = response.content
        debug["status_message"] = response.status_message
        debug["parsed_response"] = copy.deepcopy(ai_data)
        debug["parse_error"] = parse_error

    word_key_map = _extract_word_key_map(ai_data, analysis) if not parse_error else None
    word_meanings: dict[str, str] = {}
    if word_key_map is None and not parse_error:
        structured = _extract_structured_selection_map(ai_data, analysis)
        if structured is not None:
            word_key_map, word_meanings = structured
    if word_key_map is None and not parse_error:
        selected_keys = _extract_selected_keys_map(ai_data, analysis)
        if selected_keys is not None:
            word_key_map, word_meanings = selected_keys

    if word_key_map is not None:
        ai_data = _handle_compact_map_response(
            chunk_sentence=chunk_sentence,
            word_key_map=word_key_map,
            word_meanings=word_meanings,
            previous_translation=previous_translation,
            ai_manager=ai_manager,
            model=model,
            provider=provider,
            progress=progress,
            verbose=verbose,
            debug=debug,
        )
        needs_reformat = False
    else:
        needs_reformat = bool(
            parse_error or not isinstance(ai_data.get("scores"), dict)
        )

    if needs_reformat and response.content:
        ai_data = _handle_reformat_response(
            chunk_sentence=chunk_sentence,
            raw_response=response.content,
            analysis=analysis,
            ai_data=ai_data,
            parse_error=parse_error,
            ai_manager=ai_manager,
            model=model,
            provider=provider,
            progress=progress,
            verbose=verbose,
            debug=debug,
        )

    return ai_data


def translate_sentence(
    sentence: str,
    db_session: Session,
    ai_manager: AIManager | None = None,
    model: str | None = None,
    provider: str | None = None,
    verse_source: str | None = None,
    speech_mark_options: dict[str, list[str]] | None = None,
    progress: Callable[[str], None] | None = None,
    verbose: bool = False,
    debug: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full pipeline: Analyze → AI Translate → Merge. Returns the enriched analysis object."""
    if ai_manager is None:
        ai_manager = AIManager()

    resolved_sentence, extracted_options = extract_variant_options(sentence)
    if speech_mark_options:
        speech_mark_options = {**extracted_options, **speech_mark_options}
    else:
        speech_mark_options = extracted_options or None

    if progress:
        progress("json_start")
    analysis = cast(
        list[dict[str, Any]], analyze_sentence(resolved_sentence, db_session)
    )

    if verse_source:
        pre_match_db_examples(analysis, verse_source, resolved_sentence)

    if progress:
        progress("json_done")

    chunks = _split_into_sentence_chunks(
        resolved_sentence,
        analysis,
        MAX_FIRST_CONTEXT_CHARS,
    )
    if len(chunks) == 1:
        ai_data = _request_first_pass(
            resolved_sentence,
            resolved_sentence,
            analysis,
            ai_manager,
            model,
            provider,
            speech_mark_options,
            progress,
            verbose,
            debug,
        )
    else:
        chunk_debugs: list[dict[str, Any]] = []
        chunk_datas: list[dict[str, Any]] = []
        previous_translation_parts: list[str] = []
        last_chunk_error: ValueError | None = None
        for chunk_index, (chunk_text, chunk_analysis) in enumerate(chunks, start=1):
            chunk_data: dict[str, Any] | None = None
            chunk_debug: dict[str, Any] | None = None
            first_error: ValueError | None = None
            previous_translation = " ".join(previous_translation_parts)
            for attempt in range(1, CHUNK_FIRST_PASS_ATTEMPTS + 1):
                attempt_debug: dict[str, Any] | None = {} if debug is not None else None
                try:
                    chunk_data = _request_first_pass(
                        chunk_text,
                        resolved_sentence,
                        chunk_analysis,
                        ai_manager,
                        model,
                        provider,
                        speech_mark_options,
                        progress,
                        verbose,
                        attempt_debug,
                        previous_translation=previous_translation,
                    )
                except ValueError as error:
                    if attempt == 1:
                        first_error = error
                    last_chunk_error = error
                    if attempt < CHUNK_FIRST_PASS_ATTEMPTS:
                        continue
                    if debug is not None:
                        error_debug = attempt_debug if attempt_debug is not None else {}
                        error_debug.setdefault("chunk_sentence", chunk_text)
                        if first_error is not None:
                            error_debug["chunk_error_attempt_1"] = str(first_error)
                        error_debug["chunk_error"] = str(error)
                        chunk_debugs.append(error_debug)
                    if verbose:
                        pr.amber(
                            f"  Skipping chunk {chunk_index}/{len(chunks)} after AI failure: {error}"
                        )
                    break
                else:
                    chunk_debug = attempt_debug
                    if chunk_debug is not None and first_error is not None:
                        chunk_debug["chunk_error_attempt_1"] = str(first_error)
                    break
            if chunk_data is None:
                continue
            normalized_chunk_data = _normalize_ai_response(chunk_data)
            chunk_datas.append(normalized_chunk_data)
            _append_unique_text_part(
                previous_translation_parts,
                normalized_chunk_data.get("translation"),
            )
            if chunk_debug is not None:
                chunk_debugs.append(chunk_debug)
        if not chunk_datas and last_chunk_error is not None:
            raise last_chunk_error
        ai_data = _merge_chunk_ai_data(chunk_datas)
        if debug is not None:
            debug["chunk_requests"] = chunk_debugs

    if debug is not None:
        debug["retry_requests"] = []

    ai_data = _normalize_ai_response(ai_data)
    scores_map = ai_data.setdefault("scores", {})
    if not isinstance(scores_map, dict):
        scores_map = {}
        ai_data["scores"] = scores_map
    _apply_deterministic_scores_to_map(analysis, scores_map)

    missing_groups = _find_missing_score_groups(analysis, scores_map)
    if debug is not None:
        debug["missing_score_groups_after_first_response"] = missing_groups
    retry_skipped_groups: list[dict[str, Any]] = []
    if missing_groups:
        retry_skipped_groups = _request_missing_score_retry_pass(
            resolved_sentence=resolved_sentence,
            missing_groups=missing_groups,
            scores_map=scores_map,
            ai_manager=ai_manager,
            model=model,
            provider=provider,
            debug=debug,
            pass_number=1,
        )
        missing_groups_after_retry = _find_missing_score_groups(analysis, scores_map)
        if missing_groups_after_retry:
            retry_skipped_groups = _request_missing_score_retry_pass(
                resolved_sentence=resolved_sentence,
                missing_groups=missing_groups_after_retry,
                scores_map=scores_map,
                ai_manager=ai_manager,
                model=model,
                provider=provider,
                debug=debug,
                pass_number=2,
            )

    _narrow_db_example_tied_groups(analysis, scores_map)

    if debug is not None:
        if retry_skipped_groups:
            debug["retry_skipped_groups"] = retry_skipped_groups
        debug["missing_score_groups_after_retry"] = _find_missing_score_groups(
            analysis, scores_map
        )
        debug["final_scores"] = copy.deepcopy(scores_map)
    merged = merge_ai_selections(analysis, ai_data)
    merged["speech_mark_options"] = speech_mark_options or {}
    merged["variant_choices"] = ai_data.get("variant_choices", {})
    if speech_mark_options:
        merged["verse_text"] = apply_variant_choices(
            sentence,
            speech_mark_options,
            merged["variant_choices"],
        )
        merged["analysis"] = sync_analysis_words_to_sentence(
            merged["analysis"],
            merged["verse_text"],
        )
    return merged


def generate_markdown_report(
    merged_result: dict[str, Any],
    sentence: str,
    verse_id: str = "",
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Render a merged analysis result as a markdown document."""
    if speech_mark_options is None:
        speech_mark_options = merged_result.get("speech_mark_options") or None
    if speech_mark_options:
        display_sentence = apply_variant_choices(
            sentence,
            speech_mark_options,
            merged_result.get("variant_choices"),
        )
    else:
        display_sentence = sentence
    display_analysis = sync_analysis_words_to_sentence(
        merged_result["analysis"],
        display_sentence,
    )

    if verse_id:
        parts: list[str] = [f"# Analysis of: {verse_id}", display_sentence]
    else:
        parts = [f"# Analysis of: {display_sentence}"]
    parts += [
        "### English Translation",
        f"**Translation:** {merged_result.get('translation', '')}",
        f"**Literal Translation:** {merged_result.get('literal_translation', '')}",
    ]
    if speech_mark_options:
        variant_lines = [
            "//".join(variants) for variants in speech_mark_options.values()
        ]
        parts += ["### Variants", "\n\n".join(variant_lines)]
    parts += [
        "### Word-by-Word Analysis",
        format_markdown_table(display_analysis),
    ]
    return "\n\n".join(parts)


def build_system_prompt(
    analysis: list[dict[str, Any]],
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Build a comprehensive system prompt with the Pāḷi dictionary context."""

    context_str = json.dumps(analysis, ensure_ascii=False, separators=(",", ":"))

    disambiguation_block = ""
    verse_text_field = ""
    if speech_mark_options:
        options_lines = "\n".join(
            f"- '{word}': {variants}" for word, variants in speech_mark_options.items()
        )
        disambiguation_block = f"""
### Passage Text Disambiguation
The following words in this passage have multiple possible apostrophe/hyphen/sandhi forms.
Based on your grammatical analysis, choose the correct form for each. Return only the
zero-based option index for each key in the `variant_choices` field. Do not return the
full passage text.
{options_lines}
"""
        verse_text_field = '\n  "variant_choices": {"variant option key": 0},'

    prompt = f"""IMPORTANT: Your response MUST be a valid JSON object only. Do NOT write prose, markdown, explanations, or any text outside the JSON. Start your response with {{ and end with }}. {NO_TOOLS_INSTRUCTION}

You are an expert Pāḷi translator and grammarian with deep knowledge of the Tipitaka.
Your task is to analyze a Pāḷi sentence and perform word-sense disambiguation using the provided dictionary analysis.

### Dictionary Context (Word-by-Word Analysis Options)
{context_str}

### Instructions:
1. **Analyze the Sentence:** Use the context to understand grammatical relationships.
2. **Disambiguate:** For each word in the sentence, identify the correct dictionary option (`key`). Some keys include a word-occurrence prefix; always echo the full key verbatim.
3. **Score Options:**
   - Assign a score of **10** to the correct `key` for the context.
   - If multiple keys share the same id, treat them as grammar variants; choose the variant whose grammar matches your parse because the score-10 variant's grammar is what readers see in the table.
   - Assign lower scores (1-9) only to genuinely plausible alternatives if there is ambiguity.
   - Do not list options you would score 0; omitted options are treated as unselected.
   - Assign **10** to the correct `key` for *components* of compounds as well.
4. **Contextualize:**
   - **`contextual_meaning`**: Adjust the dictionary `meaning_combo` to fit the grammar (e.g., "dwells" -> "I would dwell").
     - **CRITICAL:** Do this for the main word AND for any components that are **sandhi** (pos: "sandhi").
     - You do NOT need to adjust meanings for standard compound components unless necessary for clarity.
     - **CRITICAL:** Provide ONLY the core meaning. Do NOT append grammatical case notes in parentheses — never add phrases like "(masculine nominative plural of 'X')" or "(component of compound 'X')". The Grammar column already shows this information.
   - **`selected_pos`**: If `pos` is "sandhi/compound", specify "sandhi" or "compound".
5. **Handle Deconstructions (MANDATORY):** If an option key contains `decon_` or has `meaning_combo: "[Deconstructed]"`, you **MUST** provide a full English translation of that sandhi/compound in the `contextual_meaning` field.
   - **NEVER** leave a deconstruction key with a score of 10 without providing its `contextual_meaning`.
   - **Example:** If `okassa` is deconstructed as `oka + assa`, `contextual_meaning` should be something like "to the house" or "of the dwelling".
6. **Use Existing Examples for Disambiguation:**
   - Each option includes `example_1`/`source_1` and `example_2`/`source_2` — real curated examples from the dictionary that illustrate the exact meaning of that entry.
   - Options marked `db_example_match: true` already have this exact verse as their curated example. **Strongly prefer them** — they represent the editor-validated meaning for this context. Their `ai_score` is pre-set to 10; confirm by scoring them 10 in your output as well.
   - For options without `db_example_match`, use the examples to understand which meaning best fits the verse context before assigning scores.
{COMMON_PALI_RULES}
{disambiguation_block}
### Output Format:
Return a JSON object with translations and a flat map of **scores** keyed by the option `key`.

{{
  "translation": "Fluent English translation",
  "literal_translation": "Literal English translation",{verse_text_field}
  "scores": {{
    "w0_decon_word_0": {{
      "score": 10,
      "contextual_meaning": "Full meaning of the deconstruction",
      "selected_pos": "sandhi"
    }},
    "w0_12345_0": {{
      "score": 10,
      "contextual_meaning": "I would dwell",
      "selected_pos": "verb"
    }}
  }}
}}
**CRITICAL:**
- **Keys in `scores` MUST match the `key` values in the Dictionary Context.**
- Only output the JSON object. Do not explain.
Your response MUST be exactly one JSON object with translation, literal_translation, and scores.
"""
    return prompt


def _is_numeric_score(score: Any) -> bool:
    return isinstance(score, int | float) and not isinstance(score, bool)


def _direct_key_rank(option: dict[str, Any]) -> int:
    key = str(option.get("key", ""))
    if not key or _is_deconstruction_key(key) or _is_missing_key(key):
        return 0
    if key.endswith(("_default", "_inflection")):
        return 0
    return 1 if "_" in key else 0


def _db_example_rank(option: dict[str, Any]) -> int:
    match_type = option.get("db_example_match_type", "")
    if match_type == "source_text_overlap":
        return 2
    if match_type == "text_overlap":
        return 1
    return 0


def _dictionary_quality_rank(option: dict[str, Any]) -> int:
    if not option.get("meaning_1"):
        return 0
    if option.get("example_1") or option.get("example_2"):
        return 2
    return 1


def _meaning_tokens(text: str) -> set[str]:
    return {
        token
        for token in _PARENT_MEANING_TOKEN_RE.findall(text.lower())
        if token not in _PARENT_MEANING_STOPWORDS
    }


def _parent_meaning_overlap_rank(
    option: dict[str, Any],
    parent_meaning: str,
) -> int:
    parent_tokens = _meaning_tokens(parent_meaning)
    if not parent_tokens:
        return 0
    option_tokens: set[str] = set()
    for field in ("meaning_combo", "meaning_1"):
        meaning = option.get(field)
        if isinstance(meaning, str):
            option_tokens.update(_meaning_tokens(meaning))
    return 1 if parent_tokens & option_tokens else 0


def _option_rank(
    option: dict[str, Any],
    is_component: bool = False,
    parent_meaning: str = "",
) -> tuple:
    ai_score = option.get("ai_score")
    numeric_score_rank = 1 if _is_numeric_score(ai_score) else 0
    score = ai_score if _is_numeric_score(ai_score) else -1
    component_pos_rank = 1 if is_component and option.get("pos") == "ind" else 0
    option_id = option.get("id")
    stable_id_rank = -option_id if isinstance(option_id, int) else 0
    return (
        numeric_score_rank,
        score,
        _db_example_rank(option),
        _direct_key_rank(option),
        _parent_meaning_overlap_rank(option, parent_meaning),
        component_pos_rank,
        _dictionary_quality_rank(option),
        option.get("score", 0),
        stable_id_rank,
    )


def _select_best_option(
    options: list[dict[str, Any]],
    is_component: bool = False,
    parent_meaning: str = "",
) -> dict[str, Any] | None:
    return max(
        options,
        key=lambda option: _option_rank(
            option,
            is_component=is_component,
            parent_meaning=parent_meaning,
        ),
        default=None,
    )


def _first_meaning_sense(option: dict[str, Any]) -> str:
    for field in ("meaning_combo", "meaning_1"):
        meaning = option.get(field)
        if not isinstance(meaning, str):
            continue
        first_sense = meaning.split(";", maxsplit=1)[0]
        cleaned = _clean_meaning(_strip_grammar_annotations(first_sense))
        if cleaned and not _is_deconstructed_placeholder(cleaned):
            return cleaned
    return ""


def _component_join_fallback_meaning(option: dict[str, Any]) -> str:
    components = option.get("components")
    if not isinstance(components, list):
        return ""
    parent_meaning = option.get("meaning_combo", "")
    if not isinstance(parent_meaning, str):
        parent_meaning = ""

    meanings: list[str] = []
    for component_group in components:
        if not isinstance(component_group, list):
            continue
        best_part = _select_best_option(
            component_group,
            is_component=True,
            parent_meaning=parent_meaning,
        )
        if best_part is None:
            continue
        meaning = _first_meaning_sense(best_part)
        if meaning:
            meanings.append(meaning)
    return " + ".join(meanings)


def _deconstruction_fallback_meaning(option: dict[str, Any]) -> str:
    meaning = _component_join_fallback_meaning(option)
    if meaning:
        return meaning
    return "*(AI analysis of deconstruction)*"


def format_markdown_table(enriched_analysis: list[dict[str, Any]]) -> str:
    """
    Reconstruct the Markdown table using the enriched Python structure.
    We iterate through the Python data (which contains all components)
    and simply pick the highest-scored option to display.
    """

    table_rows = [
        "| ID | Word in Sentence | Grammar | Meaning | Construction | Root |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    def add_rows_recursive(option: dict[str, Any], depth: int, parent_pos: str = ""):
        if "components" in option:
            for part_options in option["components"]:
                if not part_options:
                    continue

                # Each part has multiple lookups (homonyms). Pick the best scored one.
                # If all options have the same ai_score (e.g., 0 for sub-components),
                # prefer noun forms when parent is a noun compound.
                parent_meaning = option.get("meaning_combo", "")
                if not isinstance(parent_meaning, str):
                    parent_meaning = ""
                best_part = _select_best_option(
                    part_options,
                    is_component=True,
                    parent_meaning=parent_meaning,
                )
                if not best_part:
                    continue

                # Format component row
                clean_comp_word = best_part.get("pali", "").replace("- ", "").strip()
                indent_prefix = "- " * depth

                comp_meaning = best_part.get("meaning_combo", "")

                # Cleanup if AI failed to provide a meaning for a deconstruction
                if (
                    not comp_meaning or _is_deconstructed_placeholder(comp_meaning)
                ) and _is_deconstruction_key(best_part.get("key")):
                    comp_meaning = _deconstruction_fallback_meaning(best_part)

                comp_meaning = _clean_meaning(comp_meaning)

                # Prefer grammar (for sandhi/comp vb), fallback to POS (for pure compound parts)
                comp_grammar = best_part.get("grammar") or best_part.get("pos", "")

                if "selected_pos" in best_part and best_part["selected_pos"]:
                    if comp_grammar == "sandhi/compound":
                        comp_grammar = best_part["selected_pos"]

                # Construction Column: prefer compound_construction if available, else construction
                comp_construction = best_part.get("compound_construction", "")
                if not comp_construction:
                    comp_construction = best_part.get("construction", "")
                # Clean up formatting if needed (though analyzer usually sends clean strings for construction)
                comp_construction = comp_construction.replace("<b>", "").replace(
                    "</b>", ""
                )

                table_rows.append(
                    f"| {best_part.get('id', '')} | {indent_prefix}{clean_comp_word} | {comp_grammar} | {comp_meaning} | {comp_construction} | {best_part.get('root_key', '')} |"
                )

                # Only recurse into components of real compounds/sandhi, not etymological breakdowns
                if (
                    best_part.get("compound_type", "")
                    or best_part.get("pos", "") in {"sandhi", "sandhi/compound"}
                    or _is_deconstruction_key(best_part.get("key"))
                ):
                    add_rows_recursive(best_part, depth + 1, best_part.get("pos", ""))

    for token_data in enriched_analysis:
        word = token_data["word"]
        options = token_data["data"]

        if not options:
            table_rows.append(f"| | {word} | | | | |")
            continue

        # Sort options by AI score (desc), then by completeness/original score
        # We assume 'ai_score' has been merged into the options. Default to 0.
        best_option = _select_best_option(options)
        if not best_option:
            table_rows.append(f"| | {word} | | | | |")
            continue

        # Determine values to display
        hw_id = best_option.get("id", "")
        meaning = best_option.get("meaning_combo", "")

        # Cleanup if AI failed to provide a meaning for a deconstruction
        if (
            not meaning or _is_deconstructed_placeholder(meaning)
        ) and _is_deconstruction_key(best_option.get("key")):
            meaning = _deconstruction_fallback_meaning(best_option)

        meaning = _clean_meaning(meaning)

        grammar = best_option.get("grammar", "")

        # Handle POS override
        if "selected_pos" in best_option and best_option["selected_pos"]:
            if grammar == "sandhi/compound":
                grammar = best_option["selected_pos"]

        # Prepend adj POS when grammar exists but doesn't already label the word class
        if (
            best_option.get("pos", "") == "adj"
            and grammar
            and not grammar.startswith("adj")
        ):
            grammar = f"adj, {grammar}"

        # Construction Column: prefer compound_construction if available
        construction = best_option.get("compound_construction", "")
        if not construction:
            construction = best_option.get("construction", "")
        construction = construction.replace("<b>", "").replace("</b>", "")

        table_rows.append(
            f"| {hw_id} | {word} | {grammar} | {meaning} | {construction} | {best_option.get('root_key', '')} |"
        )

        # Start Recursion
        add_rows_recursive(best_option, 1, best_option.get("pos", ""))

    return "\n".join(table_rows)


def merge_ai_selections(
    analysis_data: list[dict[str, Any]], ai_response: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge AI scores and meanings into the analysis data structure.
    Returns a new object containing translation and the enriched analysis.
    """
    # Create a deep copy to avoid mutating the original input
    enriched_analysis = copy.deepcopy(analysis_data)
    scores_map = ai_response.get("scores", {})

    # Helper to traverse and update
    def update_entries(data_list):
        for item in data_list:
            key = item.get("key")
            if key in scores_map:
                update = scores_map[key]
                if not isinstance(update, dict):
                    # AI returned a bare scalar instead of a score object
                    item["ai_score"] = (
                        int(update) if isinstance(update, (int, float)) else 0
                    )
                else:
                    item["ai_score"] = update.get("score", 0)
                    if "selection_source" in update:
                        item["selection_source"] = update["selection_source"]

                    # Apply contextual info if score is positive (implying relevance)
                    if update.get("score", 0) > 0:
                        contextual_meaning = update.get("contextual_meaning")
                        if (
                            isinstance(contextual_meaning, str)
                            and contextual_meaning.strip()
                        ):
                            item["meaning_combo"] = contextual_meaning
                        selected_pos = update.get("selected_pos")
                        if isinstance(selected_pos, str) and selected_pos.strip():
                            item["selected_pos"] = selected_pos
            else:
                item["ai_score"] = item.get("ai_score")

            # Recursively update components
            if "components" in item:
                for comp_list in item["components"]:
                    if isinstance(comp_list, list):
                        update_entries(comp_list)

    for word_obj in enriched_analysis:
        update_entries(word_obj["data"])

    return {
        "translation": ai_response.get("translation", ""),
        "literal_translation": ai_response.get("literal_translation", ""),
        "analysis": enriched_analysis,
    }
