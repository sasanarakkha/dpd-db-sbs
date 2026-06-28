"""Tests for the unified distribute.py task helpers and task path-building."""

from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.moving import distribute as dist


def test_unzip_extracts_to_dest(tmp_path: Path) -> None:
    src = tmp_path / "a.zip"
    with ZipFile(src, "w") as zf:
        zf.writestr("hello.txt", "content")
    dest = tmp_path / "dest"
    dest.mkdir()

    dist._unzip(src, dest)

    assert (dest / "hello.txt").read_text() == "content"


def test_unzip_missing_src_logs_red(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dist._unzip(tmp_path / "missing.zip", tmp_path / "dest")

    assert "missing" in capsys.readouterr().out.lower()


def test_unzip_member_predicate_filters_members(tmp_path: Path) -> None:
    src = tmp_path / "a.zip"
    with ZipFile(src, "w") as zf:
        zf.writestr("keep/file.txt", "keep")
        zf.writestr("drop/file.txt", "drop")
    dest = tmp_path / "dest"
    dest.mkdir()

    dist._unzip(src, dest, member_predicate=lambda m: m.startswith("keep/"))

    assert (dest / "keep" / "file.txt").exists()
    assert not (dest / "drop" / "file.txt").exists()


def test_copy_file_copies_content(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("content")
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    dist._copy_file(src, dest_dir / "src.txt")

    assert (dest_dir / "src.txt").read_text() == "content"


def test_copy_tree_overwrites_existing_dest(tmp_path: Path) -> None:
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "new.txt").write_text("new")
    dest = tmp_path / "dest_dir"
    dest.mkdir()
    (dest / "stale.txt").write_text("stale")

    dist._copy_tree(src, dest)

    assert (dest / "new.txt").read_text() == "new"
    assert not (dest / "stale.txt").exists()


def test_copy_tree_with_archive_base_creates_zip(tmp_path: Path) -> None:
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "file.txt").write_text("data")
    dest = tmp_path / "dest_dir"
    archive_base = tmp_path / "archived"

    dist._copy_tree(src, dest, archive_base=archive_base)

    assert (dest / "file.txt").read_text() == "data"
    assert (tmp_path / "archived.zip").exists()


def test_move_file_moves_and_removes_source(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("content")
    dest = tmp_path / "dest.txt"

    dist._move_file(src, dest)

    assert dest.read_text() == "content"
    assert not src.exists()


def test_copy_pair_copies_only_when_all_exist(tmp_path: Path) -> None:
    src1 = tmp_path / "a.mdx"
    src1.write_text("mdx")
    src2 = tmp_path / "a.mdd"
    src2.write_text("mdd")
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    dist._copy_pair([(src1, dest_dir), (src2, dest_dir)])

    assert (dest_dir / "a.mdx").read_text() == "mdx"
    assert (dest_dir / "a.mdd").read_text() == "mdd"


def test_copy_pair_skips_all_when_one_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src1 = tmp_path / "a.mdx"
    src1.write_text("mdx")
    missing = tmp_path / "a.mdd"
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    dist._copy_pair([(src1, dest_dir), (missing, dest_dir)])

    assert not (dest_dir / "a.mdx").exists()
    assert "a.mdd" in capsys.readouterr().out


def test_require_dirs_exits_when_missing(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        dist._require_dirs(tmp_path / "nope")


def test_require_dirs_passes_when_present(tmp_path: Path) -> None:
    dist._require_dirs(tmp_path)


def _make_zip(path: Path, members: dict[str, str]) -> None:
    with ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)


def test_task_unzip_dpd_to_filesrv_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))

    downloads_dir = deva_dir / "Downloads" / "DPDs"
    downloads_dir.mkdir(parents=True)
    software_dir = dist._software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Default"
    md_dir = software_dir / "MDict" / "dpd"
    kd_dir = software_dir / "Ebook Readers Dictionary"
    for d in (gd_dir, md_dir, kd_dir):
        d.mkdir(parents=True)

    _make_zip(downloads_dir / "dpd-goldendict.zip", {"gd.txt": "gd"})
    _make_zip(downloads_dir / "dpd-mdict.zip", {"md.txt": "md"})
    (downloads_dir / "dpd-kindle.mobi").write_text("mobi")
    (downloads_dir / "dpd-kindle.epub").write_text("epub")
    (downloads_dir / "dpd-kobo.zip").write_text("kobo")
    _make_zip(downloads_dir / "dpd-pdf.zip", {"pdf.txt": "pdf"})

    dist._task_unzip_dpd_to_filesrv()

    assert (gd_dir / "gd.txt").read_text() == "gd"
    assert (md_dir / "md.txt").read_text() == "md"
    assert (kd_dir / "dpd-kindle.mobi").read_text() == "mobi"
    assert (kd_dir / "dpd-kindle.epub").read_text() == "epub"
    assert (kd_dir / "dpd-kobo.zip").read_text() == "kobo"
    assert (kd_dir / "pdf.txt").read_text() == "pdf"


def test_task_unzip_dpd_to_filesrv_exits_when_dest_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dist, "_project_paths", lambda: (tmp_path / "dpd-db", tmp_path))

    with pytest.raises(SystemExit):
        dist._task_unzip_dpd_to_filesrv()


def test_task_unzip_dpd_to_gd_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))

    downloads_dir = deva_dir / "Downloads" / "DPDs"
    downloads_dir.mkdir(parents=True)
    _make_zip(downloads_dir / "dpd-goldendict.zip", {"gd.txt": "gd"})
    _make_zip(downloads_dir / "dpd-mdict.zip", {"md.txt": "md"})

    dist._task_unzip_dpd_to_gd()

    assert (deva_dir / "Documents" / "GoldenDict" / "gd.txt").read_text() == "gd"
    assert (deva_dir / "Mdict" / "md.txt").read_text() == "md"


def test_task_unzip_dpd_to_share_filters_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))

    downloads_dir = deva_dir / "Downloads" / "DPDs"
    downloads_dir.mkdir(parents=True)
    share_dir = project_dir / "exporter" / "share"
    share_dir.mkdir(parents=True)

    _make_zip(
        downloads_dir / "dpd-goldendict.zip",
        {
            "dpd-grammar/file.txt": "grammar",
            "dpd-other/file.txt": "other",
        },
    )
    _make_zip(
        downloads_dir / "dpd-mdict.zip",
        {
            "dpd-grammar-mdict.mdx": "mdx",
            "unrelated.txt": "nope",
        },
    )

    dist._task_unzip_dpd_to_share()

    assert (share_dir / "dpd-grammar" / "file.txt").read_text() == "grammar"
    assert not (share_dir / "dpd-other" / "file.txt").exists()
    assert (share_dir / "dpd-grammar-mdict.mdx").read_text() == "mdx"
    assert not (share_dir / "unrelated.txt").exists()


def test_task_unzip_dpd_sbs_to_filesrv_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (tmp_path / "dpd-db", deva_dir))

    downloads_dir = deva_dir / "Downloads" / "DPDs"
    downloads_dir.mkdir(parents=True)
    software_dir = dist._software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Default" / "dpd"
    md_dir = software_dir / "MDict" / "dpd"
    gd_dir.mkdir(parents=True)
    md_dir.mkdir(parents=True)

    _make_zip(downloads_dir / "dpd+sbs-goldendict.zip", {"gd.txt": "gd"})
    _make_zip(downloads_dir / "dpd+sbs-mdict.zip", {"md.txt": "md"})

    dist._task_unzip_dpd_sbs_to_filesrv()

    assert (gd_dir / "gd.txt").read_text() == "gd"
    assert (md_dir / "md.txt").read_text() == "md"


def test_task_unzip_rudpd_to_filesrv_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (tmp_path / "dpd-db", deva_dir))

    downloads_dir = deva_dir / "Downloads" / "DPDs"
    downloads_dir.mkdir(parents=True)
    software_dir = dist._software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Optional"
    md_dir = software_dir / "MDict" / "ru-dpd"
    kd_dir = software_dir / "Ebook Readers Dictionary"
    for d in (gd_dir, md_dir, kd_dir):
        d.mkdir(parents=True)

    _make_zip(downloads_dir / "ru-dpd-goldendict.zip", {"gd.txt": "gd"})
    _make_zip(downloads_dir / "ru-dpd-mdict.zip", {"md.txt": "md"})
    (downloads_dir / "ru-dpd-kindle.mobi").write_text("mobi")
    (downloads_dir / "ru-dpd-kindle.epub").write_text("epub")

    dist._task_unzip_rudpd_to_filesrv()

    assert (gd_dir / "gd.txt").read_text() == "gd"
    assert (md_dir / "md.txt").read_text() == "md"
    assert (kd_dir / "ru-dpd-kindle.mobi").read_text() == "mobi"
    assert (kd_dir / "ru-dpd-kindle.epub").read_text() == "epub"
    # ru-dpd kindle files are copied, not moved, unlike the dpd task
    assert (downloads_dir / "ru-dpd-kindle.mobi").exists()


def test_task_unzip_classes_to_filesrv_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (tmp_path / "dpd-db", deva_dir))

    downloads_dir = deva_dir / "Downloads" / "Pali_classes"
    downloads_dir.mkdir(parents=True)
    materials_dir = (
        deva_dir
        / "filesrv1"
        / "share1"
        / "Sharing between users"
        / "13 For Pāli class"
        / "offline materials"
    )
    beginner_dir = materials_dir / "beginner"
    intermediate_dir = materials_dir / "intermediate"
    beginner_dir.mkdir(parents=True)
    intermediate_dir.mkdir(parents=True)

    _make_zip(
        downloads_dir / "beginner_pali_course_exercises_docx.zip", {"b1.txt": "b1"}
    )
    _make_zip(downloads_dir / "beginner_pali_course_pdfs.zip", {"b2.txt": "b2"})
    _make_zip(
        downloads_dir / "intermediate_pali_course_exercises_docx.zip",
        {"i1.txt": "i1"},
    )
    _make_zip(downloads_dir / "intermediate_pali_course_pdfs.zip", {"i2.txt": "i2"})

    dist._task_unzip_classes_to_filesrv()

    assert (beginner_dir / "b1.txt").read_text() == "b1"
    assert (beginner_dir / "b2.txt").read_text() == "b2"
    assert (intermediate_dir / "i1.txt").read_text() == "i1"
    assert (intermediate_dir / "i2.txt").read_text() == "i2"


def test_task_move_mdict_skips_when_config_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(dist, "_project_paths", lambda: (tmp_path / "dpd-db", tmp_path))
    monkeypatch.setattr(dist, "config_test", lambda *a, **k: False)

    dist._task_move_mdict()

    assert "disabled" in capsys.readouterr().out.lower()


def test_task_move_mdict_unzips_when_config_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))
    monkeypatch.setattr(dist, "config_test", lambda *a, **k: True)

    share_dir = project_dir / "exporter" / "share"
    share_dir.mkdir(parents=True)
    _make_zip(share_dir / "dpd-mdict.zip", {"mdict.txt": "data"})

    dist._task_move_mdict()

    sync_dir = (
        deva_dir / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "MDict"
    )
    assert (sync_dir / "mdict.txt").read_text() == "data"


def test_task_move_mdict_ru_uses_documents_subfolder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))
    monkeypatch.setattr(dist, "config_test", lambda *a, **k: True)

    share_dir = project_dir / "exporter" / "share"
    share_dir.mkdir(parents=True)
    _make_zip(share_dir / "ru-dpd-mdict.zip", {"mdict.txt": "ru-data"})

    dist._task_move_mdict_ru()

    sync_dir = (
        deva_dir
        / "Library"
        / "Mobile Documents"
        / "com~apple~CloudDocs"
        / "Documents"
        / "MDict"
    )
    assert (sync_dir / "mdict.txt").read_text() == "ru-data"


def test_task_copy_dpdsbs_from_sbs2filesrv_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))

    share_sbs_dir = project_dir / "exporter" / "share" / "SBS"
    share_sbs_dir.mkdir(parents=True)
    software_dir = dist._software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Default"
    md_dir = software_dir / "MDict" / "dpd"
    gd_dir.mkdir(parents=True)
    md_dir.mkdir(parents=True)

    _make_zip(share_sbs_dir / "dpd.zip", {"dpd.txt": "dpd"})
    (share_sbs_dir / "dpd-mdict.mdx").write_text("mdx")
    (share_sbs_dir / "dpd-mdict.mdd").write_text("mdd")

    dist._task_copy_dpdsbs_from_sbs2filesrv()

    assert (gd_dir / "dpd" / "dpd.txt").read_text() == "dpd"
    assert (md_dir / "dpd-mdict.mdx").read_text() == "mdx"
    assert (md_dir / "dpd-mdict.mdd").read_text() == "mdd"


def test_task_copy_dpdsbs_from_share2sbs_archives_dpd_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, tmp_path))

    share_dir = project_dir / "exporter" / "share"
    dpd_src = share_dir / "dpd"
    dpd_src.mkdir(parents=True)
    (dpd_src / "entry.txt").write_text("entry")
    (share_dir / "dpd-mdict.mdx").write_text("mdx")
    (share_dir / "dpd-mdict.mdd").write_text("mdd")

    dist._task_copy_dpdsbs_from_share2sbs()

    sbs_dir = share_dir / "SBS"
    assert (sbs_dir / "dpd" / "entry.txt").read_text() == "entry"
    assert (sbs_dir / "dpd.zip").exists()
    assert (sbs_dir / "dpd-mdict.mdx").read_text() == "mdx"
    assert (sbs_dir / "dpd-mdict.mdd").read_text() == "mdd"


def test_task_copy_rudpd_from_share2filesrv_uses_expected_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))

    share_dir = project_dir / "exporter" / "share"
    ru_dpd_src = share_dir / "ru-dpd"
    ru_dpd_src.mkdir(parents=True)
    (ru_dpd_src / "entry.txt").write_text("entry")
    (share_dir / "ru-dpd-mdict.mdx").write_text("mdx")
    (share_dir / "ru-dpd-mdict.mdd").write_text("mdd")

    software_dir = dist._software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Optional"
    md_dir = software_dir / "MDict" / "ru-dpd"
    gd_dir.mkdir(parents=True)
    md_dir.mkdir(parents=True)

    dist._task_copy_rudpd_from_share2filesrv()

    assert (gd_dir / "ru-dpd" / "entry.txt").read_text() == "entry"
    assert (md_dir / "ru-dpd-mdict.mdx").read_text() == "mdx"
    assert (md_dir / "ru-dpd-mdict.mdd").read_text() == "mdd"


# safe_copy tests


def test_safe_copy_file_to_new_dest(tmp_path: Path) -> None:
    src = tmp_path / "src.db"
    src.write_text("db contents")
    dest = tmp_path / "dest.db"

    dist.safe_copy(src, dest)

    assert dest.read_text() == "db contents"


def test_safe_copy_file_overwrites_existing_dest(tmp_path: Path) -> None:
    src = tmp_path / "src.db"
    src.write_text("new contents")
    dest = tmp_path / "dest.db"
    dest.write_text("old contents")

    dist.safe_copy(src, dest)

    assert dest.read_text() == "new contents"


def test_safe_copy_dir_to_new_dest(tmp_path: Path) -> None:
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "file.txt").write_text("hello")
    dest = tmp_path / "dest_dir"

    dist.safe_copy(src, dest)

    assert (dest / "file.txt").read_text() == "hello"


def test_safe_copy_dir_overwrites_existing_dest_dir(tmp_path: Path) -> None:
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "new.txt").write_text("new")
    dest = tmp_path / "dest_dir"
    dest.mkdir()
    (dest / "stale.txt").write_text("stale")

    dist.safe_copy(src, dest)

    assert (dest / "new.txt").read_text() == "new"
    assert not (dest / "stale.txt").exists()


def test_safe_copy_logs_red_on_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "src.db"
    src.write_text("db contents")
    dest = tmp_path / "missing_parent" / "dest.db"

    dist.safe_copy(src, dest)

    assert "Failed to copy" in capsys.readouterr().out
    assert not dest.exists()


# copy_dpd_for_classes task tests


def test_task_copy_dpd_for_classes_copies_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))

    tpr_db = tmp_path / "tipitaka.db"
    tpr_db.write_text("tpr")
    monkeypatch.setattr(dist, "config_read", lambda *a: str(tpr_db))

    share_dir = project_dir / "exporter" / "share"
    dpd_src = share_dir / "dpd"
    dpd_src.mkdir(parents=True)
    (dpd_src / "entry.txt").write_text("entry")

    bash_script = project_dir / "scripts" / "bash" / "copy_tpr_db.sh"
    bash_script.parent.mkdir(parents=True)
    bash_script.write_text("#!/bin/bash")

    dest_dir = (
        deva_dir
        / "filesrv1"
        / "share1"
        / "Sharing between users"
        / "For A. Deva"
        / "for_classes"
    )
    dest_dir.mkdir(parents=True)

    dist._task_copy_dpd_for_classes()

    assert (dest_dir / "tipitaka_pali.db").read_text() == "tpr"
    assert (dest_dir / "dpd" / "entry.txt").read_text() == "entry"
    assert (dest_dir / "copy_tpr_db.sh").exists()


def test_task_copy_dpd_for_classes_exits_when_dest_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dist, "_project_paths", lambda: (tmp_path / "dpd-db", tmp_path))
    monkeypatch.setattr(dist, "config_read", lambda *a: None)

    with pytest.raises(SystemExit):
        dist._task_copy_dpd_for_classes()


def test_task_copy_dpd_for_classes_skips_missing_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_dir = tmp_path / "dpd-db"
    deva_dir = tmp_path
    monkeypatch.setattr(dist, "_project_paths", lambda: (project_dir, deva_dir))
    monkeypatch.setattr(dist, "config_read", lambda *a: None)

    dest_dir = (
        deva_dir
        / "filesrv1"
        / "share1"
        / "Sharing between users"
        / "For A. Deva"
        / "for_classes"
    )
    dest_dir.mkdir(parents=True)

    dist._task_copy_dpd_for_classes()

    out = capsys.readouterr().out
    assert "Missing source" in out
