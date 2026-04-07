from typing import Set, Optional
from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilySet,
    FamilyWord,
    SuttaInfo,
    Lookup,
    Russian,
    SBS,
)
from tools.paths import ProjectPaths
from tools.meaning_construction import make_grammar_line, make_meaning_combo_html
from tools.pos import CONJUGATIONS, DECLENSIONS
from exporter.goldendict.helpers import TODAY
from tools.date_and_time import year_month_day_dash
from tools.css_manager import CSSManager
from tools.pali_sort_key import pali_sort_key
from tools.tools_for_ru_exporter import (
    ru_replace_abbreviations,
    make_ru_meaning_html,
    ru_make_grammar_line,
)
from tools.degree_of_completion_ru import degree_of_completion_ru
from tools.meaning_construction import summarize_construction


class HeadwordData:
    def __init__(
        self,
        i: DpdHeadword,
        rt: DpdRoot,
        fr: FamilyRoot,
        fw: FamilyWord,
        fc: list[FamilyCompound],
        fi: list[FamilyIdiom],
        fs: list[FamilySet],
        su: SuttaInfo,
        pth: ProjectPaths,
        jinja_env,
        cf_set: Set[str],
        idioms_set: Set[str],
        show_id: bool,
        ru: Optional[Russian] = None,
        sbs: Optional[SBS] = None,
        show_grammar: bool = False,
        show_sbs_data: bool = False,
        show_ru_data: bool = False,
    ):
        self.i = self._convert_newlines(i)
        self.rt = rt
        self.fr = fr
        self.fw = fw
        self.fc = fc
        self.fi = fi
        self.fs = fs
        self.su = su
        self.pth = pth
        self.jinja_env = jinja_env
        self.cf_set = cf_set
        self.idioms_set = idioms_set
        self.show_id = show_id
        self.show_grammar = show_grammar
        self.show_sbs_data = show_sbs_data
        self.show_ru_data = show_ru_data
        self.ru = self._convert_newlines_ru(ru) if ru else None
        self.sbs = self._convert_newlines_sbs(sbs) if sbs else None
        self.today = TODAY
        self.date = year_month_day_dash()
        self.grammar = make_grammar_line(i)
        self.meaning_combo_html = i.meaning_combo_html
        self.declensions = DECLENSIONS
        self.conjugations = CONJUGATIONS
        self.app_name = "GoldenDict"

        # Russian fields
        if ru:
            self.ru_pos = ru_replace_abbreviations(i.pos)
            self.ru_plus_case = (
                ru_replace_abbreviations(i.plus_case) if i.plus_case else ""
            )
            self.ru_meaning = make_ru_meaning_html(i, ru) or make_meaning_combo_html(i)
            self.ru_summary = summarize_construction(i)
            self.ru_complete = degree_of_completion_ru(i)
            self.ru_grammar = ru_make_grammar_line(i)
            self.ru_base = ru_replace_abbreviations(i.root_base, "base")
            self.ru_phonetic = ru_replace_abbreviations(i.phonetic, "phonetic")
            self.ru_inflections_html = ru_replace_abbreviations(
                i.inflections_html, "inflect"
            )
            self.ru_is_ai_translation = not ru.ru_meaning and ru.ru_meaning_raw

        # SBS fields
        if sbs:
            self.sbs_meaning = sbs.sbs_meaning
            self.sbs_notes = sbs.sbs_notes
            self.sbs_index = sbs.sbs_index
            self.sbs_class = sbs.sbs_class
            self.sbs_chant_link_1 = sbs.sbs_chant_link_1
            self.sbs_chant_link_2 = sbs.sbs_chant_link_2
            self.sbs_class_link = sbs.sbs_class_link
            self.needs_sbs_example_button = sbs.needs_sbs_example_button
            self.needs_sbs_example = sbs.needs_sbs_example
            self.needs_dhp_example = sbs.needs_dhp_example
            self.needs_pat_example = sbs.needs_pat_example
            self.needs_vib_example = sbs.needs_vib_example
            self.needs_class_example = sbs.needs_class_example
            self.needs_discourses_example = sbs.needs_discourses_example

        self.header = self._generate_header()

    @staticmethod
    def _convert_newlines(obj):
        attrs = [
            "meaning_1",
            "sanskrit",
            "phonetic",
            "compound_construction",
            "commentary",
            "sutta_1",
            "sutta_2",
            "example_1",
            "example_2",
            "notes",
        ]
        for attr_name in attrs:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
                try:
                    setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                except AttributeError:
                    continue
        return obj

    @staticmethod
    def _convert_newlines_ru(obj):
        if obj and hasattr(obj, "ru_notes") and obj.ru_notes:
            obj.ru_notes = obj.ru_notes.replace("\n, ", "<br>")
        return obj

    @staticmethod
    def _convert_newlines_sbs(obj):
        attrs = [
            "sbs_meaning",
            "sbs_notes",
            "sbs_example_1",
            "sbs_example_2",
            "dhp_example",
            "pat_example",
            "vib_example",
            "class_example",
            "discourses_example",
            "extra_example",
        ]
        for attr_name in attrs:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
                try:
                    setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                except AttributeError:
                    continue
        return obj

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header.jinja")
        html_header = template.render(d=self)
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "dpd")


class RootsData:
    def __init__(
        self,
        r: DpdRoot,
        roots_count_dict: dict[str, int],
        pth: ProjectPaths,
        jinja_env,
        frs: list[FamilyRoot],
    ):
        self.r = self._convert_newlines(r)
        self.pth = pth
        self.jinja_env = jinja_env
        self.today = TODAY
        self.date = str(TODAY)
        try:
            self.count = roots_count_dict[r.root]
        except KeyError:
            self.count = 0
        self.frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

        # Russian fields
        self.ru_root_info = ru_replace_abbreviations(r.root_info, "root")
        self.ru_root_matrix = ru_replace_abbreviations(r.root_matrix, "root")

        self.header = self._generate_header()

    @staticmethod
    def _convert_newlines(obj):
        attrs = ["panini_root", "panini_sanskrit", "panini_english"]
        for attr_name in attrs:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
                try:
                    setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                except AttributeError:
                    continue
        return obj

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("root_header.jinja")
        html_header = template.render(d=self)
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "root")


class EpdData:
    def __init__(self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env):
        self.lookup_key = lookup_entry.lookup_key
        self.epd_entries = lookup_entry.epd_unpack
        self.pth = pth
        self.jinja_env = jinja_env
        self.html_string = self._generate_html_string()
        self.header = self._generate_header()

    def _generate_html_string(self) -> str:
        html_entries = []
        for lemma_clean, pos, meaning_plus_case in self.epd_entries:
            entry_html = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            html_entries.append(entry_html)
        return "<br>".join(html_entries)

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class RpdData(EpdData):
    """RPD is already semantically localized: Russian Pali Dictionary."""

    def __init__(self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env):
        super().__init__(lookup_entry, pth, jinja_env)
        self.epd_entries = lookup_entry.rpd_unpack
        self.html_string = self._generate_html_string()


class VariantData:
    def __init__(self, variant: str, main: str, jinja_env):
        self.variant = variant
        self.main = main
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class SeeData:
    def __init__(self, see: str, headword: str, jinja_env):
        self.see = see
        self.headword = headword
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class SpellingData:
    def __init__(self, mistake: str, correction: str, jinja_env):
        self.mistake = mistake
        self.correction = correction
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "primary")


class AbbreviationsData:
    def __init__(self, i, jinja_env):
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "secondary")


class HelpData:
    def __init__(self, i, jinja_env):
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        template = self.jinja_env.get_template("dpd_header_plain.jinja")
        html_header = template.render()
        css_manager = CSSManager()
        return css_manager.update_style(html_header, "secondary")
