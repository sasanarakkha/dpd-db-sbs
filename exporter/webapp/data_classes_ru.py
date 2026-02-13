from db.models import DpdHeadword, DpdRoot, Lookup
from tools.tools_for_ru_exporter import (
    make_ru_meaning,
    ru_make_grammar_line,
    ru_replace_abbreviations,
)
from tools.date_and_time import year_month_day_dash
from tools.degree_of_completion_ru import rus_degree_of_completion


class HeadwordData:
    def __init__(self, i: DpdHeadword, fc, fi, fs):
        self.meaning = i.meaning_combo_html
        self.ru_meaning = make_ru_meaning(i)
        self.summary = i.construction_summary
        self.rus_complete = rus_degree_of_completion(i)
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
        self.su = i.su
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
        self.inflections_html_ru = ru_replace_abbreviations(
            i.inflections_html, "inflect"
        )

    @staticmethod
    def convert_newlines(obj):
        # Only convert specific string columns to avoid triggering lazy loads
        # of relationships and properties through dir(obj) and getattr()
        string_columns = [
            "meaning_1",
            "meaning_lit",
            "meaning_2",
            "construction",
            "phonetic",
            "compound_construction",
            "commentary",
            "notes",
            "example_1",
            "example_2",
            "ru_meaning",
            "ru_meaning_lit",
            "ru_notes",
        ]
        # We'll return a proxy object or just the modified SQLAlchemy object
        # but with only specific fields changed.
        # Since the session is about to close, modifying the object is usually okay
        # in the webapp, but the dir(obj) was the real killer.
        for attr_name in string_columns:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
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
        # self.grammar = result.grammar_unpack
        self.grammar = self._process_grammar(result.grammar_unpack)
        self.ru_grammar = []
        for item in self.grammar:
            headword, pos, components = item
            ru_headword = ru_replace_abbreviations(headword, "no")
            ru_pos = ru_replace_abbreviations(pos, "gram")
            ru_components = [ru_replace_abbreviations(c, "gram") for c in components]
            self.ru_grammar.append((ru_headword, ru_pos, ru_components))

    def _process_grammar(self, grammar_list):
        processed_list = []
        for item in grammar_list:
            headword, pos, grammar_str = item
            components = []

            if grammar_str.startswith("reflx"):
                parts = grammar_str.split()
                if len(parts) >= 2:
                    components.append(parts[0] + " " + parts[1])
                    components += parts[2:]
                else:
                    components.append(grammar_str)
            elif grammar_str.startswith("in comps"):
                # Handle 'in comps' specifically if needed,
                # but based on my previous fix, we treat it as a normal component
                # and let the template handle empty cells.
                # Actually, for the webapp, let's just split it as is or keep it as one.
                # In grammar_dict.py, I used:
                # html_line += f"<td>{grammar_str}</td>"
                # html_line += "<td class='col_empty'></td>"
                # html_line += "<td class='col_empty'></td>"
                components.append(grammar_str)
            else:
                components = grammar_str.split()

            # Pad with empty strings to ensure 3 components
            while len(components) < 3:
                components.append("")

            processed_list.append((headword, pos, components))
        return processed_list


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


class EpdData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.epd = result.epd_unpack


class RpdData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.rpd = result.rpd_unpack


class ManualVariantData:
    def __init__(self, variant: str, main: str):
        self.headword = variant
        self.main = main
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
