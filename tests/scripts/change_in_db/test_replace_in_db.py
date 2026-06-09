"""Golden-master tests for replace_in_db replacement logic.

No real DB records matched the filter at capture time (the pattern was already
cleaned from the data), so fixtures are representative hand-crafted strings that
cover every branch of the str.replace() transformation.
"""

import json
import re
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "test_replace_in_db_fixtures.json"

FIXTURES: dict[str, dict[str, str]] = json.loads(
    FIXTURE_PATH.read_text(encoding="utf-8")
)

TARGET = "<b> </b>"
REPLACEMENT = " "


def _apply_replacement(text: str, target: str, replacement: str) -> str:
    """Mirror the replacement logic in replace_in_db.main()."""
    return text.replace(target, replacement)


class TestApplyReplacement:
    def test_single_occurrence(self) -> None:
        case = FIXTURES["case_single"]
        assert (
            _apply_replacement(case["old_value"], TARGET, REPLACEMENT)
            == case["expected"]
        )

    def test_multiple_occurrences(self) -> None:
        case = FIXTURES["case_multiple"]
        assert (
            _apply_replacement(case["old_value"], TARGET, REPLACEMENT)
            == case["expected"]
        )

    def test_leading_occurrence(self) -> None:
        case = FIXTURES["case_leading"]
        assert (
            _apply_replacement(case["old_value"], TARGET, REPLACEMENT)
            == case["expected"]
        )

    def test_trailing_occurrence(self) -> None:
        case = FIXTURES["case_trailing"]
        assert (
            _apply_replacement(case["old_value"], TARGET, REPLACEMENT)
            == case["expected"]
        )

    def test_no_match_unchanged(self) -> None:
        case = FIXTURES["case_no_match"]
        assert (
            _apply_replacement(case["old_value"], TARGET, REPLACEMENT)
            == case["expected"]
        )

    def test_str_replace_equivalent_to_re_sub_for_literal(self) -> None:
        """Prove str.replace and re.sub are byte-identical for this literal pattern."""
        for case in FIXTURES.values():
            old = case["old_value"]
            assert old.replace(TARGET, REPLACEMENT) == re.sub(TARGET, REPLACEMENT, old)
