# -*- coding: utf-8 -*-
import threading
from spellchecker import SpellChecker
from tools.paths_dps import DPSPaths
from typing import Dict, List


class RuSpellChecker:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> "RuSpellChecker":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the Russian spell checker with custom dictionary (only once)."""
        if RuSpellChecker._initialized:
            return

        with RuSpellChecker._lock:
            if RuSpellChecker._initialized:
                return

            self.spell = SpellChecker(language="ru")  # Use Russian language
            self.dpspth = DPSPaths()
            self.user_dict = self.dpspth.ru_user_dict_path

            # Load custom Russian dictionary
            try:
                with open(self.user_dict, "r", encoding="utf-8") as f:
                    custom_words = [line.strip() for line in f if line.strip()]
                    self.spell.word_frequency.load_words(custom_words)
            except FileNotFoundError:
                # Create the dictionary file if it doesn't exist
                self.user_dict.parent.mkdir(parents=True, exist_ok=True)
                with open(self.user_dict, "w", encoding="utf-8") as f:
                    pass  # Create empty file

            RuSpellChecker._initialized = True

    def check_sentence(self, sentence: str) -> Dict[str, List[str]]:
        """Check spelling in a Russian sentence and return misspelled words with suggestions."""

        # Use lock to prevent concurrent access to the shared SpellChecker instance
        with RuSpellChecker._lock:
            # Split the sentence into words and remove punctuation
            words = "".join(
                c if c.isalpha() or c.isspace() else " " for c in sentence
            ).split()

            # Find misspelled words
            misspelled = self.spell.unknown(words)

            # Get suggestions for each misspelled word
            results: Dict[str, List[str]] = {}
            for word in misspelled:
                candidates = self.spell.candidates(word)
                results[word] = list(candidates) if candidates else []

            return results

    def add_to_ru_dictionary(self, word: str) -> str:
        """Add a word to both the session dictionary and the Russian custom dictionary file."""
        with RuSpellChecker._lock:
            # Add to the current spell checker session
            self.spell.word_frequency.load_words([word])

            # Add to the Russian custom dictionary file
            if self.user_dict:
                with open(self.user_dict, "a", encoding="utf-8") as f:
                    f.write(f"{word}\n")

        return f"Added Russian word '{word}' to dictionary"
