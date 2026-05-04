import pytest
from scripts.change_in_db.update_yojana_km import (
    words_to_num,
    recalculate_meaning_en,
    recalculate_meaning_ru,
    format_ru_km,
)


@pytest.mark.parametrize(
    "phrase, expected",
    [
        ("ten", 10),
        ("twenty", 20),
        ("forty", 40),
        ("sixty", 60),
        ("eighty", 80),
        ("one hundred", 100),
        ("one hundred and twenty", 120),
        ("one hundred and forty", 140),
        ("one hundred and fifty", 150),
        ("two hundred", 200),
        ("two hundred and forty", 240),
        ("three hundred", 300),
        ("three hundred and twenty", 320),
        ("one thousand", 1000),
        ("one thousand two hundred", 1200),
        ("two thousand", 2000),
        ("two thousand four hundred", 2400),
        ("three thousand", 3000),
        ("twenty thousand", 20000),
        ("forty thousand", 40000),
        ("two hundred thousand", 200000),
        ("one million six hundred and eighty thousand", 1680000),
        ("one billion three hundred and sixty million", 1360000000),
    ],
)
def test_words_to_num(phrase, expected):
    assert words_to_num(phrase) == expected


@pytest.mark.parametrize(
    "meaning, old_base, new_base, expected",
    [
        (
            "approximately twenty kilometres",
            20,
            14,
            "approximately fourteen kilometres",
        ),
        (
            "three yojanas; approximately sixty kilometres",
            20,
            14,
            "three yojanas; approximately forty-two kilometres",
        ),
        (
            "two yojanas; approximately forty kilometres",
            20,
            14,
            "two yojanas; approximately twenty-eight kilometres",
        ),
        ("twenty kilometres high", 20, 14, "fourteen kilometres high"),
        (
            "approximately twenty to forty kilometres away",
            20,
            14,
            "approximately fourteen to twenty-eight kilometres away",
        ),
        (
            "approximately five to ten kilometres",
            20,
            14,
            "approximately four to seven kilometres",
        ),
        (
            "one hundred yojanas; approximately two thousand kilometres",
            20,
            14,
            "one hundred yojanas; approximately one thousand four hundred kilometres",
        ),
    ],
)
def test_recalculate_meaning_en(meaning, old_base, new_base, expected):
    assert recalculate_meaning_en(meaning, old_base, new_base) == expected


@pytest.mark.parametrize(
    "meaning, old_base, new_base, expected",
    [
        ("мера длинны; примерно 20 км", 20, 14, "мера длинны; примерно 14 км"),
        (
            "мера длинны; три йоджаны; примерно 60 км",
            20,
            14,
            "мера длинны; три йоджаны; примерно 42 км",
        ),
        (
            "два йоджана; приблизительно сорок километров",
            20,
            14,
            "два йоджана; примерно 28 км",
        ),
        (
            "максимум три йоджаны; шестьдесят километров самое большее",
            20,
            14,
            "максимум три йоджаны; примерно 42 км самое большее",
        ),
        ("около ста сорока километров", 20, 14, "примерно 98 км"),
        ("примерно тысяча километров", 20, 14, "примерно 700 км"),
        ("примерно двадцать километров в размере", 20, 14, "примерно 14 км в размере"),
        (
            "приблизительно один миллион шестьсот восемьдесят тысяч километров в высоту",
            20,
            14,
            "примерно 1.176 миллиона км в высоту",
        ),
        ("примерно двадцать до сорока километров", 20, 14, "примерно 14–28 км"),
        (
            "в пределах примерно шестидесяти километров",
            20,
            14,
            "в пределах примерно 42 км",
        ),
        (
            "более чем примерно шестидесяти километров",
            20,
            14,
            "более чем примерно 42 км",
        ),
        (
            "менее чем примерно шестьдесят километров",
            20,
            14,
            "менее чем примерно 42 км",
        ),
        ("примерно восемь тысяч километров", 20, 14, "примерно 5.6 тысячи км"),
    ],
)
def test_recalculate_meaning_ru(meaning, old_base, new_base, expected):
    assert recalculate_meaning_ru(meaning, old_base, new_base) == expected


@pytest.mark.parametrize(
    "km, expected",
    [
        # Genitive plural (ends in 5-9, 0, or 11-19)
        (200000, "200 тысяч км"),
        (140000, "140 тысяч км"),
        (28000, "28 тысяч км"),
        (14000, "14 тысяч км"),  # 11-19 range
        (7000, "7 тысяч км"),
        (5000, "5 тысяч км"),
        (6000, "6 тысяч км"),
        (8000, "8 тысяч км"),
        (9000, "9 тысяч км"),
        (11000, "11 тысяч км"),
        (15000, "15 тысяч км"),
        (20000, "20 тысяч км"),
        (25000, "25 тысяч км"),
        # Genitive singular (ends in 2, 3, 4, or x2-x4 where x != 1)
        (4000, "4 тысячи км"),
        (3000, "3 тысячи км"),
        (2000, "2 тысячи км"),
        (42000, "42 тысячи км"),
        (23000, "23 тысячи км"),
        (34000, "34 тысячи км"),
        # Nominative (ends in 1, but not 11)
        (1000, "1 тысяча км"),
        (21000, "21 тысяча км"),
        (31000, "31 тысяча км"),
        # Decimal values (тысячи is standard)
        (1400, "1.4 тысячи км"),
        (2800, "2.8 тысячи км"),
        (4200, "4.2 тысячи км"),
        (5600, "5.6 тысячи км"),
        (8400, "8.4 тысячи км"),
        # Non-thousands
        (500, "500 км"),
        (100, "100 км"),
        # Millions
        (1176000, "1.176 миллиона км"),
        (952000000, "952 миллиона км"),
    ],
)
def test_format_ru_km(km, expected):
    assert format_ru_km(km) == expected
