"""Build localized GoldenDict render data for DPS exporters."""

from jinja2 import Environment

from db.models import (
    SBS,
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilySet,
    FamilyWord,
    Lookup,
    Russian,
    SuttaInfo,
    Tamil,
)
from exporter.goldendict.helpers import TODAY
from tools.css_manager import CSSManager
from tools.date_and_time import year_month_day_dash
from tools.degree_of_completion_ru import degree_of_completion_ru
from tools.meaning_construction import (
    make_grammar_line,
    make_meaning_combo_html,
    summarize_construction,
)
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.paths_ru import RuPaths
from tools.pos import CONJUGATIONS, DECLENSIONS
from tools.tools_for_ru_exporter import (
    make_ru_meaning_html,
    ru_make_grammar_line,
    ru_replace_abbreviations,
)


def _render_header(
    jinja_env: Environment,
    template_name: str,
    style: str,
    context: dict[str, object] | None = None,
) -> str:
    template = jinja_env.get_template(template_name)
    html_header = template.render(**(context or {}))
    css_manager = CSSManager()
    return css_manager.update_style(html_header, style)


def _render_plain_header(jinja_env: Environment, style: str) -> str:
    return _render_header(jinja_env, "dpd_header_plain.jinja", style)


class _NewlineView:
    """Read-only view over a DpdHeadword that renders newlines as ``<br>`` on
    display fields, without mutating the tracked ORM object. Every other
    attribute is delegated unchanged."""

    _NL_ATTRS = frozenset(
        {
            "construction",
            "phonetic",
            "compound_construction",
            "sutta_1",
            "sutta_2",
            "example_1",
            "example_2",
            "commentary",
            "notes",
        }
    )

    def __init__(self, obj: DpdHeadword) -> None:
        object.__setattr__(self, "_obj", obj)

    def __getattr__(self, name: str):
        value = getattr(self._obj, name)
        if name in self._NL_ATTRS and isinstance(value, str) and value:
            return value.replace("\n", "<br>")
        return value


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
        su: SuttaInfo | None,
        pth: ProjectPaths | RuPaths | DPSPaths,
        jinja_env: Environment,
        cf_set: set[str],
        idioms_set: set[str],
        show_id: bool,
        ru: Russian | None = None,
        sbs: SBS | None = None,
        ta: Tamil | None = None,
        show_grammar: bool = False,
        show_sbs_data: bool = False,
        show_ru_data: bool = False,
        show_ta_data: bool = False,
    ) -> None:
        self.construction_summary = i.construction_summary
        self.i = _NewlineView(i)
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
        self.show_ta_data = show_ta_data
        self.ru = self._convert_newlines_ru(ru) if ru else None
        self.sbs = self._convert_newlines_sbs(sbs) if sbs else None
        self.ta: Tamil | None = ta
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
    def _convert_newlines_ru(obj):
        if obj and hasattr(obj, "ru_notes") and obj.ru_notes:
            obj.ru_notes = obj.ru_notes.replace("\n", "<br>")
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
            "class_example_translation",
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
        return _render_header(self.jinja_env, "dpd_header.jinja", "dpd", {"d": self})


class RootsData:
    def __init__(
        self,
        r: DpdRoot,
        roots_count_dict: dict[str, int],
        pth: ProjectPaths | RuPaths | DPSPaths,
        jinja_env: Environment,
        frs: list[FamilyRoot],
    ) -> None:
        self.r = r
        self.pth = pth
        self.jinja_env = jinja_env
        self.today = TODAY
        self.date = year_month_day_dash()
        try:
            self.count = roots_count_dict[r.root]
        except KeyError:
            self.count = 0
        self.frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

        # Russian fields
        self.ru_root_info = ru_replace_abbreviations(r.root_info, "root")
        self.ru_root_matrix = ru_replace_abbreviations(r.root_matrix, "root")

        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_header(self.jinja_env, "root_header.jinja", "root", {"d": self})


class EpdData:
    def __init__(
        self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env: Environment
    ) -> None:
        self.lookup_key = lookup_entry.lookup_key
        self.epd_entries = lookup_entry.epd_unpack
        self.pth = pth
        self.jinja_env = jinja_env
        self.html_string = self._generate_html_string()
        self.header = self._generate_header()

    def _generate_html_string(self) -> str:
        return "<br>".join(
            f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            for lemma_clean, pos, meaning_plus_case in self.epd_entries
        )

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class RpdData(EpdData):
    """RPD is already semantically localized: Russian Pali Dictionary."""

    def __init__(
        self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env: Environment
    ) -> None:
        super().__init__(lookup_entry, pth, jinja_env)
        self.epd_entries = lookup_entry.rpd_unpack
        self.html_string = self._generate_html_string()


class TpdData(EpdData):
    """TPD: Tamil Pāḷi Dictionary. Reserved for future export_tpd.py."""

    def __init__(
        self, lookup_entry: Lookup, pth: ProjectPaths, jinja_env: Environment
    ) -> None:
        super().__init__(lookup_entry, pth, jinja_env)
        self.epd_entries = lookup_entry.tpd_unpack
        self.html_string = self._generate_html_string()


class VariantData:
    def __init__(self, variant: str, main: str, jinja_env: Environment) -> None:
        self.variant = variant
        self.main = main
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class SeeData:
    def __init__(self, see: str, headword: str, jinja_env: Environment) -> None:
        self.see = see
        self.headword = headword
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class SpellingData:
    def __init__(self, mistake: str, correction: str, jinja_env: Environment) -> None:
        self.mistake = mistake
        self.correction = correction
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "primary")


class AbbreviationsData:
    def __init__(self, i, jinja_env: Environment) -> None:
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "secondary")


class AbbrevOtherData:
    def __init__(
        self, abbreviation: str, rows: list[dict[str, str]], jinja_env: Environment
    ) -> None:
        self.abbreviation = abbreviation
        self.rows = rows
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "secondary")


class HelpData:
    def __init__(self, i, jinja_env: Environment) -> None:
        self.i = i
        self.jinja_env = jinja_env
        self.header = self._generate_header()

    def _generate_header(self) -> str:
        return _render_plain_header(self.jinja_env, "secondary")
