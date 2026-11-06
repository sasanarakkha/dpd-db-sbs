"""Tests for the Russian Kindle exporter: form-keyed entries (upstream #217 port),
the KindleDataRu body object, and the kindling build step."""

import re
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from exporter.jinja2_env import get_jinja2_env
from exporter.kindle import kindle_exporter_ru
from exporter.kindle.kindle_exporter_ru import KindleDataRu
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths

RU_TEMPLATES = "exporter/kindle/ru_components/templates"


def _env():
    return get_jinja2_env(RU_TEMPLATES)


def _data(id_: int, lemma_1: str, summary: str = "adj. test") -> KindleDataRu:
    return cast(
        KindleDataRu,
        SimpleNamespace(
            i=SimpleNamespace(id=id_, lemma_1=lemma_1),
            summary=summary,
            grammar_table="",
            examples="",
        ),
    )


def _headword(id_: int, lemma_1: str) -> DpdHeadword:
    return cast(DpdHeadword, SimpleNamespace(id=id_, lemma_1=lemma_1))


def test_letter_files_match_the_static_manifest() -> None:
    files = kindle_exporter_ru._letter_files()
    assert files["a"] == "0_a.xhtml"
    assert len(files) == len(set(files.values()))


def test_headword_aliases_cover_own_forms_and_scripts_but_not_the_label() -> None:
    headword = _headword(7, "gacchati 1")
    aliases = kindle_exporter_ru._headword_aliases(
        headword,
        {7: ["gacchāmi", "gacchati 1"]},
        {"gacchāmi": ["गच्छामि"], "gacchati 1": ["गच्छति"]},
    )
    assert "gacchāmi" in aliases
    assert "गच्छामि" in aliases
    assert "गच्छति" in aliases
    assert "gacchati 1" not in aliases


def test_a_form_entry_lists_every_sense_with_a_link() -> None:
    html = kindle_exporter_ru.render_form_entry_ru(
        _env(),
        1,
        "gacchati",
        [_data(24043, "gacchati 1"), _data(24044, "gacchati 2")],
        [],
        None,
        "",
        {"g": "10_g.xhtml"},
    )
    assert '<idx:orth value="gacchati">' in html
    assert '<a href="10_g.xhtml#hw24043"><b>gacchati 1</b></a>' in html
    assert '<a href="10_g.xhtml#hw24044"><b>gacchati 2</b></a>' in html


def test_a_contested_label_carries_both_the_list_and_the_headword_detail() -> None:
    merged = _data(928, "acca", "masc. a merged headword")
    html = kindle_exporter_ru.render_form_entry_ru(
        _env(),
        2,
        "acca",
        [_data(35345, "accati 1")],
        [],
        merged,
        "",
        {"a": "0_a.xhtml"},
    )
    assert '<idx:orth value="acca">' in html
    assert 'href="0_a.xhtml#hw35345"' in html
    assert 'id="hw928"' in html
    assert "a merged headword" in html


def test_script_spellings_attach_as_aliases() -> None:
    html = kindle_exporter_ru.render_form_entry_ru(
        _env(),
        3,
        "dhammo",
        [_data(1, "dhamma 1")],
        ["धम्मो", "ธมฺโม"],
        None,
        "",
        {"dh": "21_dh.xhtml"},
    )
    assert '<idx:iform value="धम्मो" exact="yes">' in html
    assert '<idx:iform value="ธมฺโม" exact="yes">' in html


def test_a_headword_entry_is_labelled_with_lemma_1_not_lemma_clean() -> None:
    html = kindle_exporter_ru.render_ebook_entry_ru(
        _env(), _data(14657, "uttara 1.1"), ["uttaro"], ""
    )
    assert '<idx:orth value="uttara 1.1">' in html
    assert 'id="hw14657"' in html
    assert '<idx:iform value="uttaro" exact="yes">' in html


def test_niggahita_variants_are_indexed() -> None:
    variants = kindle_exporter_ru._niggahita_variants({"dhammaṃ", "buddha"})
    assert variants == {"dhammaṁ"}


def test_headword_aliases_include_the_niggahita_spelling() -> None:
    headword = _headword(3, "dhamma 1")
    aliases = kindle_exporter_ru._headword_aliases(headword, {3: ["dhammaṃ"]}, {})
    assert "dhammaṃ" in aliases
    assert "dhammaṁ" in aliases


def test_a_headword_entry_uses_each_id_once() -> None:
    html = kindle_exporter_ru.render_ebook_entry_ru(_env(), _data(928, "acca"), [], "")
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids)), ids
    assert "hw928" in ids


def test_a_merged_headword_is_not_also_listed_as_a_link_to_itself() -> None:
    merged = _data(928, "acca")
    html = kindle_exporter_ru.render_form_entry_ru(
        _env(),
        1,
        "acca",
        [merged, _data(35345, "accati 1")],
        [],
        merged,
        "",
        {"a": "0_a.xhtml"},
    )
    assert 'href="0_a.xhtml#hw928"' not in html
    assert 'href="0_a.xhtml#hw35345"' in html
    assert html.count('id="hw928"') == 1


def test_a_headword_entry_renders_a_deconstruction_when_given_one() -> None:
    html = kindle_exporter_ru.render_ebook_entry_ru(
        _env(), _data(5, "abhibhosmi"), [], "abhibhū + asmi"
    )
    assert "abhibhū + asmi" in html


def test_no_deconstructor_entry_renderer_remains() -> None:
    assert not hasattr(kindle_exporter_ru, "render_deconstructor_entry_ru")


@pytest.fixture(scope="module")
def real_headword() -> Iterator[DpdHeadword]:
    """A real headword with a Russian meaning, an example and a root."""
    session = get_db_session(ProjectPaths().dpd_db_path)
    headword = (
        session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.id == 8)
        .one()
    )
    assert headword.ru is not None and headword.ru.ru_meaning
    yield headword
    session.close()


def test_kindle_data_ru_summary_is_russian(real_headword: DpdHeadword) -> None:
    data = KindleDataRu(real_headword, _env(), real_headword.id, [])
    assert real_headword.ru is not None
    assert real_headword.ru.ru_meaning in data.summary
    assert " & " not in data.summary


def test_kindle_data_ru_grammar_table_is_russian(real_headword: DpdHeadword) -> None:
    data = KindleDataRu(real_headword, _env(), real_headword.id, [])
    assert "Грамматика" in data.grammar_table


def test_kindle_data_ru_renders_examples(real_headword: DpdHeadword) -> None:
    data = KindleDataRu(real_headword, _env(), real_headword.id, [])
    assert data.examples


def test_kindle_data_ru_does_not_mutate_the_headword(
    real_headword: DpdHeadword,
) -> None:
    before = real_headword.example_1
    KindleDataRu(real_headword, _env(), real_headword.id, [])
    assert real_headword.example_1 == before


class _FakeProcess:
    def __init__(self, returncode: int) -> None:
        self.stdout = iter(["building\n", "done\n"])
        self._returncode = returncode

    def wait(self) -> int:
        return self._returncode


def _ru_paths(tmp_path: Path, mode: int | None = 0o755) -> RuPaths:
    binary = tmp_path / "kindling-cli"
    if mode is not None:
        binary.write_text("")
        binary.chmod(mode)
    return cast(
        RuPaths,
        SimpleNamespace(
            kindling_path=binary,
            epub_content_opf_path=tmp_path / "content.opf",
            dpd_mobi_path=tmp_path / "ru-dpd-kindle.mobi",
        ),
    )


def _capture(
    monkeypatch: pytest.MonkeyPatch, returncode: int = 0
) -> list[tuple[list[str], dict[str, Any]]]:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_popen(command: list[str], **kwargs: Any) -> _FakeProcess:
        calls.append((command, kwargs))
        return _FakeProcess(returncode)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    return calls


def test_ru_paths_really_exposes_kindling_path() -> None:
    """The other tests fake RuPaths; this one pins the real attribute, and that
    it is the same binary upstream uses."""
    assert RuPaths().kindling_path.name == "kindling-cli"
    assert RuPaths().kindling_path == ProjectPaths().kindling_path


def test_ru_paths_has_no_kindlegen_attributes() -> None:
    rupth = RuPaths()
    assert not hasattr(rupth, "kindlegen_path")
    assert not hasattr(rupth, "ebook_deconstructor_templ_path")


def test_make_mobi_builds_from_the_opf_into_the_mobi_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rupth = _ru_paths(tmp_path)
    calls = _capture(monkeypatch)

    kindle_exporter_ru.make_mobi(rupth)

    assert len(calls) == 1
    command, _ = calls[0]
    assert command[0] == str(rupth.kindling_path)
    assert command[1] == "build"
    assert command[2] == str(rupth.epub_content_opf_path)
    assert command[3:] == ["-o", str(rupth.dpd_mobi_path)]
    assert not any(arg.endswith(".epub") for arg in command)


def test_make_mobi_keeps_validation_on_and_accent_folding_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _capture(monkeypatch)

    kindle_exporter_ru.make_mobi(_ru_paths(tmp_path))

    command, _ = calls[0]
    assert "--no-validate" not in command
    assert "--fold-accents" not in command


def test_make_mobi_decodes_and_merges_the_child_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _capture(monkeypatch)
    printed: list[str] = []
    monkeypatch.setattr(
        kindle_exporter_ru.pr, "white", lambda line: printed.append(line)
    )

    kindle_exporter_ru.make_mobi(_ru_paths(tmp_path))

    _, kwargs = calls[0]
    assert kwargs["text"] is True
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.STDOUT
    assert printed == ["building", "done"]


@pytest.mark.parametrize("mode", [None, 0o644], ids=["missing", "not-executable"])
def test_make_mobi_raises_on_an_unusable_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: int | None
) -> None:
    calls = _capture(monkeypatch)

    with pytest.raises(FileNotFoundError):
        kindle_exporter_ru.make_mobi(_ru_paths(tmp_path, mode=mode))

    assert calls == []


def test_make_mobi_raises_on_a_non_zero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capture(monkeypatch, returncode=1)

    with pytest.raises(RuntimeError):
        kindle_exporter_ru.make_mobi(_ru_paths(tmp_path))


OPF = "{http://www.idpf.org/2007/opf}"


def _render_opf(remote_pages: set[str]) -> ET.Element:
    template = _env().get_template("ebook_ru_content_opf.jinja")
    xml = template.render(
        date_time_zulu="2026-01-01T00:00:00Z", remote_pages=remote_pages
    )
    return ET.fromstring(xml.encode("utf-8"))


def test_opf_declares_a_dictionary_with_russian_out_language() -> None:
    root = _render_opf(set())
    metadata = root.find(f"{OPF}metadata")
    assert metadata is not None
    assert metadata.findtext("{http://purl.org/dc/elements/1.1/}type") == "dictionary"
    xm = metadata.find(f"{OPF}x-metadata")
    assert xm is not None
    assert xm.findtext(f"{OPF}DictionaryInLanguage") == "pi"
    assert xm.findtext(f"{OPF}DictionaryOutLanguage") == "ru"
    assert xm.findtext(f"{OPF}DefaultLookupIndex") == "Pali"


def test_opf_default_lookup_index_matches_the_entry_name() -> None:
    """kindling resolves DefaultLookupIndex against idx:entry name=..."""
    html = kindle_exporter_ru.render_ebook_entry_ru(
        _env(), _data(1, "dhamma 1"), [], ""
    )
    assert 'name="Pali"' in html
    assert _render_opf(set()).findtext(f".//{OPF}DefaultLookupIndex") == "Pali"


def test_opf_links_the_ncx_from_manifest_and_spine() -> None:
    root = _render_opf(set())
    ncx = [i for i in root.iter(f"{OPF}item") if i.get("id") == "ncx"]
    assert len(ncx) == 1
    assert ncx[0].get("href") == "toc.ncx"
    assert ncx[0].get("media-type") == "application/x-dtbncx+xml"
    spine = root.find(f"{OPF}spine")
    assert spine is not None
    assert spine.get("toc") == "ncx"


def test_opf_guide_points_the_index_at_the_first_pali_page() -> None:
    """Upstream #217 (a441f918c) added the guide; kindling warns R15.7 without it."""
    refs = _render_opf(set()).findall(f"{OPF}guide/{OPF}reference")
    assert [(r.get("type"), r.get("href")) for r in refs] == [
        ("index", "Text/0_a.xhtml")
    ]


def test_opf_marks_only_the_pages_with_web_links_as_remote() -> None:
    root = _render_opf({"0_a.xhtml", "rpd_0.xhtml"})
    remote = {
        i.get("href", "").removeprefix("Text/")
        for i in root.iter(f"{OPF}item")
        if i.get("properties") == "remote-resources"
    }
    assert remote == {"0_a.xhtml", "rpd_0.xhtml"}
    assert not _render_opf(set()).findall(
        f".//{OPF}item[@properties='remote-resources']"
    )


def test_find_pages_with_web_links(tmp_path: Path) -> None:
    (tmp_path / "a.xhtml").write_text('<a href="https://x.org">x</a>', encoding="utf-8")
    (tmp_path / "b.xhtml").write_text('<a href="b.xhtml#hw1">x</a>', encoding="utf-8")
    rupth = cast(RuPaths, SimpleNamespace(epub_text_dir=tmp_path))
    assert kindle_exporter_ru.find_pages_with_web_links(rupth) == {"a.xhtml"}


EPUB_DIR = Path("exporter/kindle/ru_components/epub")
RU_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def _generated_pages() -> set[str]:
    """Every page file the exporter writes or the epub ships statically."""
    pages = set(kindle_exporter_ru._letter_files().values())
    pages |= {f"rpd_{i}.xhtml" for i in range(len(RU_ALPHABET))}
    pages |= {"abbreviations.xhtml", "titlepage.xhtml", "cover.xhtml", "imprint.xhtml"}
    return pages


def test_ncx_points_only_at_generated_pages() -> None:
    ns = {"n": "http://www.daisy.org/z3986/2005/ncx/"}
    root = ET.parse(EPUB_DIR / "OEBPS/toc.ncx").getroot()
    srcs = [c.get("src", "") for c in root.iterfind(".//n:content", ns)]
    assert srcs
    for src in srcs:
        assert src.startswith("Text/"), src
        assert src.removeprefix("Text/") in _generated_pages(), src


def test_ncx_is_russian_and_has_both_dictionaries() -> None:
    ns = {"n": "http://www.daisy.org/z3986/2005/ncx/"}
    root = ET.parse(EPUB_DIR / "OEBPS/toc.ncx").getroot()
    labels = [t.text for t in root.iterfind(".//n:navLabel/n:text", ns)]
    assert "Сокращения" in labels
    assert "Пали-Русский" in labels
    assert "Русский-Пали" in labels
    assert (
        root.findtext(".//n:docTitle/n:text", namespaces=ns) == "Цифровой Словарь Пали"
    )
    srcs = [c.get("src") for c in root.iterfind(".//n:content", ns)]
    assert sum(1 for s in srcs if s and "rpd_" in s) == 34  # parent + 33 letters
    play = [int(p.get("playOrder", 0)) for p in root.iterfind(".//n:navPoint", ns)]
    assert play == list(range(1, len(play) + 1))


def test_ncx_uid_matches_the_opf_book_id() -> None:
    ns = {"n": "http://www.daisy.org/z3986/2005/ncx/"}
    ncx = ET.parse(EPUB_DIR / "OEBPS/toc.ncx").getroot()
    uid = next(
        m.get("content")
        for m in ncx.iterfind(".//n:meta", ns)
        if m.get("name") == "dtb:uid"
    )
    book_id = _render_opf(set()).findtext(
        ".//{http://purl.org/dc/elements/1.1/}identifier"
    )
    assert uid == book_id


def test_nav_has_no_dead_links() -> None:
    """Every href in nav.xhtml must name a manifest item of the OPF."""
    html = (EPUB_DIR / "OEBPS/Text/nav.xhtml").read_text(encoding="utf-8")
    hrefs = re.findall(r'href="([^"#]+)', html)
    assert hrefs
    manifest = {
        i.get("href", "").removeprefix("Text/")
        for i in _render_opf(set()).iter(f"{OPF}item")
    }
    for href in hrefs:
        assert href in manifest, href
    assert "titlepage.xhtml" not in hrefs
