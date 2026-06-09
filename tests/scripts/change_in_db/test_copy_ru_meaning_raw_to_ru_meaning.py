"""Tests for scripts/change_in_db/copy_ru_meaning_raw_to_ru_meaning.py."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from db.models import DpdHeadword, Russian
from scripts.change_in_db.copy_ru_meaning_raw_to_ru_meaning import read_ids_from_tsv

FIXTURE_PATH = (
    Path(__file__).parent / "test_copy_ru_meaning_raw_to_ru_meaning_fixtures.json"
)

_LITERAL_SEP = "; досл."


def _load_fixtures() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_ru(ru_meaning: str, ru_meaning_lit: str, ru_meaning_raw: str) -> Russian:
    return cast(
        Russian,
        SimpleNamespace(
            ru_meaning=ru_meaning,
            ru_meaning_lit=ru_meaning_lit,
            ru_meaning_raw=ru_meaning_raw,
        ),
    )


def _make_word(word_id: int, ru: Russian | None) -> DpdHeadword:
    return cast(DpdHeadword, SimpleNamespace(id=word_id, ru=ru))


def _apply_transform(word: DpdHeadword) -> bool:
    """Replicates the per-word transformation logic from copy_raw_to_meaning."""
    if not (word.ru and word.ru.ru_meaning_raw):  # type: ignore[union-attr]
        return False
    raw = word.ru.ru_meaning_raw  # type: ignore[union-attr]
    if (
        not word.ru.ru_meaning  # type: ignore[union-attr]
        and not word.ru.ru_meaning_lit  # type: ignore[union-attr]
        and _LITERAL_SEP in raw
    ):
        parts = raw.split(_LITERAL_SEP, 1)
        word.ru.ru_meaning = parts[0].strip()  # type: ignore[union-attr]
        word.ru.ru_meaning_lit = parts[1].strip()  # type: ignore[union-attr]
        return True
    if not word.ru.ru_meaning:  # type: ignore[union-attr]
        word.ru.ru_meaning = raw  # type: ignore[union-attr]
        return True
    return False


# --- read_ids_from_tsv ---


def test_read_ids_from_tsv_basic() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tsv", encoding="utf-8", delete=False
    ) as f:
        f.write("id\tother\n31\tfoo\n15\tbar\n1\tbaz\n")
        tmp = Path(f.name)

    try:
        result = read_ids_from_tsv(tmp)
        assert result == [31, 15, 1]
    finally:
        tmp.unlink()


def test_read_ids_from_tsv_utf8_sig() -> None:
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".tsv", delete=False) as f:
        content = "id\tother\n42\tfoo\n".encode("utf-8-sig")
        f.write(content)
        tmp = Path(f.name)

    try:
        result = read_ids_from_tsv(tmp)
        assert result == [42]
    finally:
        tmp.unlink()


# --- transformation branches ---


def test_split_branch() -> None:
    fixtures = _load_fixtures()
    case = fixtures["split_case"]

    ru = _make_ru(
        ru_meaning=case["ru_meaning_in"],
        ru_meaning_lit=case["ru_meaning_lit_in"],
        ru_meaning_raw=case["ru_meaning_raw"],
    )
    word = _make_word(case["id"], ru)

    updated = _apply_transform(word)

    assert updated is True
    assert ru.ru_meaning == case["expected_ru_meaning"]
    assert ru.ru_meaning_lit == case["expected_ru_meaning_lit"]


def test_raw_copy_branch() -> None:
    fixtures = _load_fixtures()
    case = fixtures["raw_copy_case"]

    ru = _make_ru(
        ru_meaning=case["ru_meaning_in"],
        ru_meaning_lit=case["ru_meaning_lit_in"],
        ru_meaning_raw=case["ru_meaning_raw"],
    )
    word = _make_word(case["id"], ru)

    updated = _apply_transform(word)

    assert updated is True
    assert ru.ru_meaning == case["expected_ru_meaning"]
    assert ru.ru_meaning_lit == case["ru_meaning_lit_in"]


def test_skip_when_ru_meaning_already_set() -> None:
    fixtures = _load_fixtures()
    case = fixtures["skip_case"]

    ru = _make_ru(
        ru_meaning=case["ru_meaning_in"],
        ru_meaning_lit=case["ru_meaning_lit_in"],
        ru_meaning_raw=case["ru_meaning_raw"],
    )
    word = _make_word(case["id"], ru)
    original_meaning = ru.ru_meaning

    updated = _apply_transform(word)

    assert updated is False
    assert ru.ru_meaning == original_meaning


def test_skip_when_no_ru_relation() -> None:
    fixtures = _load_fixtures()
    case = fixtures["no_ru_case"]

    word = _make_word(case["id"], ru=None)

    updated = _apply_transform(word)

    assert updated is False


def test_skip_when_ru_meaning_raw_empty() -> None:
    ru = _make_ru(ru_meaning="", ru_meaning_lit="", ru_meaning_raw="")
    word = _make_word(999, ru)

    updated = _apply_transform(word)

    assert updated is False
    assert ru.ru_meaning == ""


def test_split_separator_appears_once() -> None:
    """split(sep, 1) always yields exactly 2 parts when sep is in string."""
    raw = "simple meaning; досл. literal meaning"
    ru = _make_ru(ru_meaning="", ru_meaning_lit="", ru_meaning_raw=raw)
    word = _make_word(1, ru)

    _apply_transform(word)

    assert ru.ru_meaning == "simple meaning"
    assert ru.ru_meaning_lit == "literal meaning"
