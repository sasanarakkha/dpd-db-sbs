"""Tests for gui2/dps_ai_service.py prompt builders.

Content tests pass against both old and new code.
Whitespace tests (no leading tabs) lock in the new textwrap.dedent behaviour.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from gui2.dps_ai_service import _build_meaning_prompt, _build_notes_prompt
from tools.paths_dps import DPSPaths

FIXTURE_PATH = Path(__file__).parent / "test_dps_ai_service_fixtures.json"

FIXTURES: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

DPSPTH = DPSPaths()

MEANING_SYS = "You are a skilled assistant that translates English text to Russian with grammatical accuracy, contextual relevance, and strict adherence to rules."
NOTES_SYS = "You are a helpful assistant that translates English text to Russian considering the context."


def _make_headword(**kwargs: Any) -> Any:
    """Duck-typed headword; the prompt builders only read plain string attributes."""
    return SimpleNamespace(
        lemma_1=kwargs.get("lemma_1", ""),
        grammar=kwargs.get("grammar", ""),
        meaning_1=kwargs.get("meaning_1", ""),
        example_1=kwargs.get("example_1", ""),
        pos=kwargs.get("pos", ""),
        notes=kwargs.get("notes", ""),
    )


@pytest.fixture(params=list(FIXTURES.keys()))
def fixture_case(request: pytest.FixtureRequest) -> dict:
    return FIXTURES[request.param]


# ---------------------------------------------------------------------------
# _build_meaning_prompt — content tests (pass old and new code)
# ---------------------------------------------------------------------------


class TestBuildMeaningPromptContent:
    def test_returns_two_strings(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        result = _build_meaning_prompt(hw, DPSPTH)
        assert isinstance(result, tuple) and len(result) == 2
        assert all(isinstance(s, str) for s in result)

    def test_system_prompt_unchanged(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        sys_prompt, _ = _build_meaning_prompt(hw, DPSPTH)
        assert sys_prompt == MEANING_SYS

    def test_lemma_1_present_in_user_prompt(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        assert fixture_case["input"]["lemma_1"] in user_prompt

    def test_meaning_1_present_in_user_prompt(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        assert fixture_case["input"]["meaning_1"] in user_prompt

    def test_translate_instruction_present_by_default(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH, synonyms=False)
        assert "Translate the English definition" in user_prompt

    def test_synonyms_instruction_present_when_flag_set(
        self, fixture_case: dict
    ) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH, synonyms=True)
        assert "synonyms" in user_prompt
        assert "nine (9)" in user_prompt

    def test_example_appended_when_present(self) -> None:
        data = FIXTURES["full"]["input"]
        hw = _make_headword(**data)
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        assert "Consider Pali context" in user_prompt
        assert data["example_1"][:20] in user_prompt

    def test_example_absent_when_empty(self) -> None:
        hw = _make_headword(**FIXTURES["no_example"]["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        assert "Consider Pali context" not in user_prompt


# ---------------------------------------------------------------------------
# _build_meaning_prompt — new behaviour (whitespace + None guard)
# ---------------------------------------------------------------------------


class TestBuildMeaningPromptNewBehaviour:
    def test_user_prompt_no_leading_whitespace(self, fixture_case: dict) -> None:
        """New: textwrap.dedent().strip() removes the leading \\n\\t from old code."""
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        assert not user_prompt.startswith(("\t", "\n", " "))

    def test_no_tab_prefix_on_lines(self, fixture_case: dict) -> None:
        """New: prompt lines must not start with a tab character."""
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        for line in user_prompt.splitlines():
            assert not line.startswith("\t"), f"Tab-prefixed line found: {line!r}"

    def test_lemma_1_none_renders_as_empty_string(self) -> None:
        """New: lemma_1 or '' prevents 'None' appearing in the prompt."""
        hw = _make_headword(
            lemma_1=None,  # type: ignore[arg-type]
            grammar="adj",
            meaning_1="not rough",
            example_1="",
            pos="adj",
        )
        _, user_prompt = _build_meaning_prompt(hw, DPSPTH)
        assert "None" not in user_prompt
        assert "**Pali Term**:" in user_prompt


# ---------------------------------------------------------------------------
# _build_notes_prompt — content tests
# ---------------------------------------------------------------------------


class TestBuildNotesPromptContent:
    def test_returns_two_strings(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        result = _build_notes_prompt(hw)
        assert isinstance(result, tuple) and len(result) == 2
        assert all(isinstance(s, str) for s in result)

    def test_system_prompt_unchanged(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        sys_prompt, _ = _build_notes_prompt(hw)
        assert sys_prompt == NOTES_SYS

    def test_lemma_1_present(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_notes_prompt(hw)
        assert fixture_case["input"]["lemma_1"] in user_prompt

    def test_notes_present(self) -> None:
        data = FIXTURES["full"]["input"]
        hw = _make_headword(**data)
        _, user_prompt = _build_notes_prompt(hw)
        assert data["notes"] in user_prompt


# ---------------------------------------------------------------------------
# _build_notes_prompt — new behaviour
# ---------------------------------------------------------------------------


class TestBuildNotesPromptNewBehaviour:
    def test_user_prompt_no_leading_whitespace(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_notes_prompt(hw)
        assert not user_prompt.startswith(("\t", "\n", " "))

    def test_no_tab_prefix_on_lines(self, fixture_case: dict) -> None:
        hw = _make_headword(**fixture_case["input"])
        _, user_prompt = _build_notes_prompt(hw)
        for line in user_prompt.splitlines():
            assert not line.startswith("\t"), f"Tab-prefixed line found: {line!r}"

    def test_lemma_1_none_renders_as_empty_string(self) -> None:
        hw = _make_headword(
            lemma_1=None,  # type: ignore[arg-type]
            grammar="masc",
            notes="some notes",
        )
        _, user_prompt = _build_notes_prompt(hw)
        assert "None" not in user_prompt
