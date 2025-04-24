# No need to import unicodedata for this basic range check
from aksharamukha import transliterate
from typing import List # Added for type hint in main

from tools.printer import printer as pr
from tools.pali_alphabet import pali_alphabet


def is_cyrillic(text: str) -> bool:
    """Checks if the string contains any Cyrillic characters."""
    # Basic Cyrillic Unicode block: U+0400 to U+04FF
    # This covers most common Cyrillic scripts like Russian, Ukrainian, etc.
    # Add other ranges (e.g., Supplement U+0500–U+052F) if needed for less common Cyrillic chars.
    return any('\u0400' <= char <= '\u04FF' for char in text)


def auto_translit_to_roman(text: str) -> str:
    """
    Transliterates text to Roman script (IAST Pali),
    but leaves Roman Pali and Cyrillic scripts untouched.
    """
    if not text: # Handle empty string case
        return ""

    # 1. Check if already Roman Pali
    # Assuming pali_alphabet contains Roman characters used in Pali transliteration
    if text[0] in pali_alphabet:
        return text

    # 2. Check if Cyrillic
    if is_cyrillic(text):
        return text

    # 3. If not Roman Pali or Cyrillic, attempt transliteration
    else:
        try:
            # REMOVE the ': str | None' hint from this line
            transliterated_text = transliterate.process(
                "autodetect", "IASTPali", text, post_options=["AnusvaratoNasalASTISO"]
            )
            if transliterated_text:
                # Apply post-processing replacements
                transliterated_text = (
                    transliterated_text.replace("ï", "i")
                    .replace("ü", "u")
                    .replace("ĕ", "e")
                    .replace("ŏ", "o")
                    .replace("l̤", "ḷ")
                )
                return transliterated_text
            else:
                # Return original text if transliteration result is empty or None
                return text
        except Exception as e:
            # Using print for compatibility with original code, consider logging
            # Also adding type hint for e
            print(f"Error during Aksharamukha transliteration: {e!s}") # Use !s for string representation
            return text


def main() -> None: # Added return type hint
    pr.green_title("transliterating timer")

    test_list: List[List[str]] = [ # Added type hint
        ["māḷā"],
        ["dhamma", "धम्म", "ဓမ္မ", "ธมฺม", "ධම්ම"],
        ["buddha", "बुद्ध", "ဗုဒ္ဓ", "พุทฺธ", "බුද්ධ"],
        ["saṅgha", "सङ्घ", "သံဃ", "สงฺฆ", "සංඝ"],
        ["mettā", "मेत्ता", "မေတ္တာ", "เมตฺตา", "මෙත්තා"],
        ["anicca", "अनिच्च", "အနိစ္စ", "อนิจฺจ", "අනිච්ච"],
        ["dukkha", "दुक्ख", "ဒုက္ခ", "ทุกฺข", "දුක්ඛ"],
        ["anattā", "अनत्ता", "အနတ္တာ", "อนตฺตา", "අනත්තා"],
        ["kamma", "कम्म", "ကမ္မ", "กมฺม", "කම්ම"],
        ["nibbāna", "निब्बान", "နိဗ္ဗာန", "นิพฺพาน", "නිබ්බාන"],
        ["sīla", "सील", "သီလ", "สีล", "සීල"],
        ["samādhi", "समाधि", "သမာဓိ", "สมาธิ", "සමාධි"],
        ["paññā", "पञ्ञा", "ပညာ", "ปญฺญา", "පඤ්ඤා"],
        ["sutta", "सुत्त", "သုတ္တ", "สุตฺต", "සුත්ත"],
        ["bhikkhu", "भिक्खु", "ဘိက္ခု", "ภิกฺขุ", "භික්ඛු"],
        ["jhāna", "झान", "ဈာန", "ฌาน", "ඣාන"],
        ["vipassanā", "विपस्सना", "ဝိပဿနာ", "วิปสฺสนา", "විපස්සනා"],
        ["sacca", "सच्च", "သစ္စ", "สจฺจ", "සච්ච"],
        ["vinaya", "विनय", "ဝိနယ", "วินย", "විනය"],
        ["abhidhamma", "अभिधम्म", "အဘိဓမ္မ", "อภิธมฺม", "අභිධම්ම"],
        ["karuṇā", "करुणा", "ကရုဏာ", "กรุณา", "කරුණා"],
        # Add a Cyrillic test case
        ["привет мир"] # Example: "hello world" in Russian
    ]
    counter: int = 1 # Added type hint
    total_words: int = sum(len(sublist) for sublist in test_list) # Calculate total words for counter

    # Using enumerate on test_list directly, index is not used
    for word_list in test_list:
        for word in word_list:
            roman: str = auto_translit_to_roman(word)
            # Ensure counter reflects total words correctly
            pr.counter(counter, total_words, f"Original: '{word}', Transliterated: '{roman}'")
            counter += 1


if __name__ == "__main__":
    main()
