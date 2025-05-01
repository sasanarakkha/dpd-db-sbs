"""Functions for:
1. Summarizing ru meaning and literal meaning,
2. Extract first synonym from ru meaning
3. Replace abbreviations eng to rus
4. Russianize other parts of html for ru_exporter
5. assume corresponding ru names for sets from the tsv
"""


import re
import csv
from rich import print

from db.models import DpdHeadword, Russian
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.meaning_construction import make_meaning_combo
from tools.date_and_time import year_month_day_dash

pth = ProjectPaths()
rupth = RuPaths()
date = year_month_day_dash()

abbreviations_dict = None
compiled_patterns = None


def make_ru_meaning(i: DpdHeadword) -> str:
    """Uses only DpdHeadword input. Compile html of ru_meaning and literal meaning, or return ru_meaning_raw.
    ru_meaning in <b>bold</b>, or return english meaning
    with links for feedback"""

    if i.ru is None:
        ru_meaning: str = f"<a class='link' href='https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500={i.lemma_link}&entry.326955045=Перевод&entry.1433863141=dpdict.net+{date}' target='_blank'>[перевести]</a> {make_meaning_combo(i)}"
        return ru_meaning

    elif i.ru.ru_meaning:
        ru_meaning: str = f"<b>{i.ru.ru_meaning}</b>"
        if i.ru.ru_meaning_lit:
            ru_meaning += f"; досл. {i.ru.ru_meaning_lit}"
        return ru_meaning
    elif i.ru.ru_meaning_raw:
        ru_meaning: str = f"<a class='link' href='https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500={i.lemma_link}&entry.326955045=Перевод&entry.1433863141=dpdict.net+{date}' target='_blank'>[пер. ИИ]</a> {i.ru.ru_meaning_raw}"
        return ru_meaning
    else:
        return ""


def make_ru_meaning_simpl(i: DpdHeadword) -> str:
    """Uses only DpdHeadword input. Compile html of ru_meaning and literal meaning, or return ru_meaning_raw.
    ru_meaning in <b>bold</b>, or return english meaning"""

    if i.ru is None:
        ru_meaning: str = f"{make_meaning_combo(i)}"
        return ru_meaning

    elif i.ru.ru_meaning:
        ru_meaning: str = f"<b>{i.ru.ru_meaning}</b>"
        if i.ru.ru_meaning_lit:
            ru_meaning += f"; досл. {i.ru.ru_meaning_lit}"
        return ru_meaning
    elif i.ru.ru_meaning_raw:
        ru_meaning: str = f"<i>[пер. ИИ]</i> {i.ru.ru_meaning_raw}"
        return ru_meaning
    else:
        return ""


def make_short_ru_meaning(i: DpdHeadword, ru: Russian) -> str:
    """Extract first synonym from ru_meaning or ru_meaning_raw"""
    if ru is None:
        return make_short_meaning(i)
    elif ru.ru_meaning:
        ru_meaning: str = ru.ru_meaning
        first_synonym = get_first_synonym(ru_meaning)
        return first_synonym
    elif ru.ru_meaning_raw:
        first_synonym = get_first_synonym(ru.ru_meaning_raw)
        return first_synonym
    else:
        return ""


def make_ru_meaning_html(i: DpdHeadword, ru: Russian) -> str:
    """Compile html of ru_meaning and literal meaning, or return ru_meaning_raw.
    ru_meaning in <b>bold</b>, or return english meaning"""

    if ru is None:
        ru_meaning: str = make_meaning_combo(i)
        return ru_meaning

    elif ru.ru_meaning:
        ru_meaning: str = f"<b>{ru.ru_meaning}</b>"
        if ru.ru_meaning_lit:
            ru_meaning += f"; досл. {ru.ru_meaning_lit}"
        return ru_meaning
    elif ru.ru_meaning_raw:
        ru_meaning: str = ru.ru_meaning_raw
        return ru_meaning
    else:
        return ""


def make_ru_meaning_for_ebook(i: DpdHeadword, ru: Russian) -> str:
    """Compile html of ru_meaning and literal meaning, or return ru_meaning_raw with spesial mark.
    ru_meaning in <b>bold</b>, or return english meaning"""

    if ru is None:
        ru_meaning: str = make_meaning_combo(i)
        return ru_meaning

    elif ru.ru_meaning:
        ru_meaning: str = f"<b>{ru.ru_meaning}</b>"
        if ru.ru_meaning_lit:
            ru_meaning += f"; досл. {ru.ru_meaning_lit}"
        return ru_meaning
    elif ru.ru_meaning_raw:
        ru_meaning: str = f"[пер. ИИ] {ru.ru_meaning_raw}"
        return ru_meaning
    else:
        return ""


def ru_replace_abbreviations(value, kind="meaning"):
    """
    Replace abbreviations in the given value based on the specified kind.
    """
    global abbreviations_dict, compiled_patterns

    # Load abbreviations dictionary and precompile patterns if not already done
    if abbreviations_dict is None or compiled_patterns is None:
        abbreviations_dict = load_abbreviations_dict(pth.abbreviations_tsv_path)
        compiled_patterns = {
            abbr: re.compile(rf'\b\+?{re.escape(abbr)}\b') for abbr in abbreviations_dict
        }

    # Perform basic replacements based on the kind
    if kind == "meaning":
        value = value.replace(' or ', ' или ').replace(', from', ', от').replace(' of ', ' от ').replace('letter', 'буква').replace('form', 'форма').replace('normally', 'обычно').replace('root', 'корень')
    elif kind == "inflect":
        value = value.replace(' is ', ' это ').replace('conjugation', 'класс спряжения').replace('declension', 'класс склонения').replace('like ', 'как ').replace('reflexive', 'возвратный').replace('irregular', 'неправильный')
    elif kind == "root":
        value = value.replace('Pāḷi Root', 'Корень Пали').replace('Sanskrit Root', 'Корень Санскр.').replace('Bases', 'Основы').replace('Base', 'Основа').replace('in Compounds', 'в Составе').replace('Notes', 'Заметки').replace('adverbs', 'наречия').replace('verbs', 'глаголы').replace('participles', 'причастия').replace('nouns', 'существительные').replace('adjectives', 'прилагательные')
    elif kind == "gram":
        value = value.replace('word', 'слово').replace('letter', 'буква').replace('indeclinable', 'несклоняемое').replace('of', 'от').replace('root', 'корень')
    elif kind == "base":
        value = value.replace('pass,', 'страд,').replace('pass)', 'страд)').replace('caus', 'понудит').replace('irreg', 'неправ').replace('desid', 'дезид').replace('deno', 'отымённ').replace('intens', 'усил')
    elif kind == "phonetic":
        value = value.replace('metathesis', 'метатеза').replace('with metrically', 'с метрически').replace('lengthened', 'удлиненным').replace('doubled', 'удвоенным').replace('shortened', 'укороченным').replace('Kacc', 'Качч').replace('contraction', 'сокращение').replace('expansion', 'расширение').replace('under the influence of', 'под влиянием').replace('before', 'перед').replace('nasalization', 'назализация').replace('a vowel', 'гласным').replace('a consonant', 'согласным').replace('aphesis', 'афезис')

    # Replace abbreviations using precompiled patterns
    for abbr, pattern in compiled_patterns.items():
        # Skip replacement for "pass" if kind is "inflect"
        if kind == "inflect" and abbr == "pass":
            continue
        value = pattern.sub(abbreviations_dict[abbr], value)

    return value


def ru_replace_abbreviations_list(grammar):
    ru_grammar = []
    for value in grammar:
        ru_value = ru_replace_abbreviations(value, "no")
        ru_grammar.append(ru_value)
        
    return ru_grammar


def load_abbreviations_dict(tsv_file_path):
    """Load abbreviations from a TSV file and precompile regex patterns."""
    global abbreviations_dict, compiled_patterns
    if abbreviations_dict is None:
        abbreviations_dict = {}
        with open(tsv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            for row in reader:
                if len(row) >= 6 and row[5]:  # Check if the row has a Russian equivalent
                    abbreviations_dict[row[0]] = row[5]
        # Sort abbreviations by length (longer first) to avoid partial matches
        abbreviations_dict = dict(sorted(abbreviations_dict.items(), key=lambda x: len(x[0]), reverse=True))

    # Precompile regex patterns
    if compiled_patterns is None:
        compiled_patterns = {
            abbr: re.compile(rf'\b\+?{re.escape(abbr)}\b') for abbr in abbreviations_dict
        }

    return abbreviations_dict



def replace_english(value, kind = "freq"):
    # Perform basic replacements
    if kind == "freq":
        value = value.replace('There are no matches of', 'Нет совпадений со словом').replace('in any corpus.', 'ни в одной из версий текста').replace('Frequency of', 'График частоты совпадений слова').replace('and its', 'и его форм').replace('declensions', 'склонений').replace('conjugations', 'спряжений')
    return value


def ru_make_grammar_line(i: DpdHeadword) -> str:
    """Compile grammar line and replace values with ru"""
    
    grammar = ru_replace_abbreviations(i.grammar)
    if i.neg:
        grammar += f", {ru_replace_abbreviations(i.neg)}"
    if i.verb:
        grammar += f", {ru_replace_abbreviations(i.verb)}"
    if i.trans:
        grammar += f", {ru_replace_abbreviations(i.trans)}"
    if i.plus_case:
        grammar += f" ({ru_replace_abbreviations(i.plus_case)})"
    return grammar


def get_first_synonym(synonyms_str: str, delimiter: str = ';') -> str:
    """Extract the first synonym from a string of synonyms separated by a delimiter."""
    synonyms = synonyms_str.split(delimiter)
    return synonyms[0] if synonyms else ''


def make_short_meaning(i: DpdHeadword) -> str:
	"""Extract first synonim from meaning_1 or meaning_2."""
	if i.meaning_1:
		meaning: str = i.meaning_1
		first_synonym = get_first_synonym(meaning)
		return first_synonym
	elif i.meaning_2:
		meaning: str = i.meaning_2
		first_synonym = get_first_synonym(meaning)
		return first_synonym
	else:
		return ""


def read_set_ru_from_tsv():
    set_ru_dict = {}
    with open(rupth.sets_ru_path, 'r', newline='') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            set_name, set_ru = row
            set_ru_dict[set_name] = set_ru
    return set_ru_dict


def write_set_to_tsv(fs):
    # Write unique sets to a TSV file
    with open('unique_sets.tsv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for set_name in fs:
            writer.writerow([set_name])


def populate_set_ru_and_check_errors(sets_dict):
    set_ru_dict = read_set_ru_from_tsv()
    errors_list = []
    for sf in sets_dict:
        if sf in set_ru_dict:
            sets_dict[sf]["set_ru"] = set_ru_dict[sf]
        else:
            errors_list.append(sf)
            print(f"[bright_red]ERROR: No corresponding set_ru found for set: {sf}")
    if errors_list == []:
        print("[green]All sets have russian equivalents")
    return errors_list


mdict_ru_description = """

    <p>Электронный Словарь Пали Дост. Бодхираса</p>
    <p>Переведен на русский Бхиккху Дэвамитта</p>
    <p>Для более детальной информации можено посетить
    <a href=\"https://devamitta.github.io/pali/pali_dict.html\">
    сайт Пали Словаря</a></p>
    и оригинальный сайт <a href=\"https://digitalpalidictionary.github.io\">
    Digital Pāḷi Dictionary</a></p>

"""

mdict_ru_title = "Электронный Словарь Пали"

gdict_ru_info = {
    "bookname": "Пали Словарь",
    "author": "Bodhirasa, переведено Devamitta",
    "description": "",
    "website": "https://digitalpalidictionary.github.io/rus", 
    }



def sbs_related_sign(i: DpdHeadword):
    """Return html styled letter of which category of examples related to SBS."""
    html = """<span color: #ab7b38>"""
    if i.sbs:
        if i.sbs.sbs_category:
            html += "A "
        if i.sbs.sbs_class_anki:
            html += "C "
        if i.sbs.sbs_patimokkha == "pat":
            html += "P "
        if i.sbs.sbs_patimokkha == "vib":
            html += "V "
        if i.sbs.sbs_index:
            html += "S"
    html += """</span>"""
    return html