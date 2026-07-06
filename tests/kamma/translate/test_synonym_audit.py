from kamma.translate.scripts.synonym_audit import (
    find_exact_dups,
    find_near_dups,
    normalize,
    rebuild_field,
    split_meanings,
)


def test_split_meanings_strips_and_drops_empties():
    assert split_meanings("готовый; завершённый; ; собранный") == [
        "готовый",
        "завершённый",
        "собранный",
    ]


def test_split_meanings_single_part_no_semicolon():
    assert split_meanings("готовый") == ["готовый"]


def test_split_meanings_all_empty():
    assert split_meanings("  ; ; ") == []


def test_normalize_lowercases_and_collapses_yo():
    assert normalize("Ёлка") == "елка"


def test_normalize_strips_bracketed_segments():
    assert normalize("готовый (разг.)") == "готовый"


def test_normalize_collapses_whitespace():
    assert normalize("готовый   собранный") == "готовый собранный"


def test_normalize_strips_trailing_dot():
    assert normalize("готовый.") == "готовый"


def test_normalize_equal_after_case_and_yo_variants():
    assert normalize("Готовый") == normalize("готовый")
    assert normalize("ёлка") == normalize("елка")


def test_find_exact_dups_collapses_case_and_yo_variants():
    parts = ["готовый", "Готовый", "ёлка", "елка", "собранный"]
    assert find_exact_dups(parts) == [1, 3]


def test_find_exact_dups_no_duplicates():
    parts = ["готовый", "завершённый", "собранный"]
    assert find_exact_dups(parts) == []


def test_find_exact_dups_bracket_and_dot_variants_collapse():
    parts = ["готовый (разг.)", "готовый."]
    assert find_exact_dups(parts) == [1]


def test_find_near_dups_flags_near_identical_pair():
    parts = ["готовый", "готовенький"]
    pairs = find_near_dups(parts, threshold=0.6)
    assert len(pairs) == 1
    i, j, ratio = pairs[0]
    assert (i, j) == (0, 1)
    assert ratio >= 0.6


def test_find_near_dups_does_not_flag_distinct_meanings():
    parts = ["готовый", "завершённый"]
    assert find_near_dups(parts, threshold=0.85) == []


def test_find_near_dups_excludes_exact_dups_already_flagged():
    parts = ["готовый", "Готовый", "готовенький"]
    pairs = find_near_dups(parts, threshold=0.6)
    assert len(pairs) == 1
    i, j, _ratio = pairs[0]
    assert (i, j) == (0, 2)


def test_find_near_dups_respects_threshold():
    parts = ["готовый", "готовенький"]
    assert find_near_dups(parts, threshold=0.99) == []


def test_rebuild_field_preserves_order_and_casing():
    parts = ["Готовый", "завершённый", "Собранный"]
    assert rebuild_field(parts, drop=set()) == "Готовый; завершённый; Собранный"


def test_rebuild_field_drops_given_indexes():
    parts = ["готовый", "Готовый", "собранный"]
    assert rebuild_field(parts, drop={1}) == "готовый; собранный"


def test_rebuild_field_empty_after_dropping_all():
    parts = ["готовый", "Готовый"]
    assert rebuild_field(parts, drop={0, 1}) == ""
