from db.models import DpdRoot, Lookup
from tools.tools_for_ru_exporter import (
    make_ru_meaning,
    ru_make_grammar_line,
    ru_replace_abbreviations,
    ru_replace_abbreviations_list,
)
from tools.configger import config_test
from tools.date_and_time import year_month_day_dash
from tools.meaning_construction import (
    degree_of_completion,
    make_grammar_line,
    make_meaning_combo_html,
    rus_degree_of_completion,
    summarize_construction,
)


class HeadwordData:
    def __init__(self, i, fc, fi, fs):
        self.meaning = make_meaning_combo_html(i)
        self.ru_meaning = make_ru_meaning(i)
        self.summary = summarize_construction(i)
        self.complete = degree_of_completion(i)
        self.rus_complete = rus_degree_of_completion(i)
        self.grammar = make_grammar_line(i)
        self.ru_grammar = ru_make_grammar_line(i)
        self.ru_pos = ru_replace_abbreviations(i.pos, "gram")
        self.ru_plus_case = ru_replace_abbreviations(i.plus_case, "gram")
        self.ru_root_base = ru_replace_abbreviations(i.root_base, "base")
        self.ru_phonetic = ru_replace_abbreviations(i.phonetic, "phonetic")
        self.i = self.convert_newlines(i)
        self.i.sbs = self.convert_newlines(i.sbs)
        self.i.ru = self.convert_newlines(i.ru)
        self.fc = fc
        self.fi = fi
        self.fs = fs
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
        self.inflections_html_ru = ru_replace_abbreviations(
            i.inflections_html, "inflect"
        )
        if config_test("dictionary", "make_link", "yes"):
            self.make_link = True
        else:
            self.make_link = False
        if config_test("dictionary", "show_ru_data", "yes"):
            self.show_ru_data = True
        else:
            self.show_ru_data = False

    @staticmethod
    def convert_newlines(obj):
        # Convert all string attributes before session closes
        for attr_name in dir(obj):
            if (
                not attr_name.startswith("_")
                and "html" not in attr_name
                and "data" not in attr_name
            ):
                attr_value = getattr(obj, attr_name)
                if isinstance(attr_value, str):
                    try:
                        setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                    except AttributeError:
                        continue
        return obj


class RootsData:
    def __init__(self, r, frs, roots_count_dict) -> None:
        self.r: DpdRoot = r
        self.frs = frs
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
        self.count = roots_count_dict[self.r.root]
        self.root_info_ru = ru_replace_abbreviations(r.root_info, "root")
        self.root_matrix_ru = ru_replace_abbreviations(r.root_matrix, "root")


class DeconstructorData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.deconstructions = result.deconstructor_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class VariantData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.variants = result.variants_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class SpellingData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.spellings = result.spelling_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class GrammarData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.grammar = result.grammar_unpack
        self.ru_grammar = [
            ru_replace_abbreviations_list(value) for value in self.grammar
        ]


class HelpData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.help = result.help_unpack


class AbbreviationsData:
    def __init__(self, result: Lookup):
        data = result.abbrev_unpack
        self.headword = result.lookup_key
        self.meaning = data["meaning"]
        self.pali = data["pāli"]
        self.example = data["example"]
        self.explanation = data["explanation"]
        self.ru_meaning = data.get("ru_meaning", "")
        self.ru_abbrev = data.get("ru_abbrev", "")
        if config_test("dictionary", "show_ru_data", "yes"):
            self.show_ru_data = True
        else:
            self.show_ru_data = False


class EpdData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.epd = result.epd_unpack


class RpdData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.rpd = result.rpd_unpack
