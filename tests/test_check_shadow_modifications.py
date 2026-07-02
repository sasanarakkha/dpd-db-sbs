"""Verify shadow-modification checks include every strict-shadow category."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from kamma.upstream_sync.scripts.registry_helper import get_shadow_mappings_by_category
from kamma.upstream_sync.scripts.sync_schema import RegistryData, ShadowCopyEntry


def load_shadow_modification_script() -> ModuleType:
    """Load the shadow modification script as a testable module."""
    script_path = Path("tests/check_shadow_modifications.py")
    spec = importlib.util.spec_from_file_location(
        "check_shadow_modifications_script",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_shadow_mappings_by_category_includes_dps() -> None:
    data = RegistryData(
        modified_upstream_files=[],
        russian_copies={"a_ru.py": ShadowCopyEntry(upstream="a.py")},
        sbs_copies={"a_sbs.py": ShadowCopyEntry(upstream="a.py")},
        dps_copies={"a_dps.py": ShadowCopyEntry(upstream="a.py")},
        tamil_copies={},
        inspired_by_upstream={},
        unique_paths=[],
        no_sync_files=[],
        skip_sync_patterns=[],
    )

    mappings = get_shadow_mappings_by_category(data)

    assert mappings["russian_copies"] == {"a_ru.py": ShadowCopyEntry(upstream="a.py")}
    assert mappings["sbs_copies"] == {"a_sbs.py": ShadowCopyEntry(upstream="a.py")}
    assert mappings["dps_copies"] == {"a_dps.py": ShadowCopyEntry(upstream="a.py")}


def test_get_last_sync_commit_uses_latest_upstream_pull(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_shadow_modification_script()
    mock_run = MagicMock()
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=f"{'a' * 40}\n",
        stderr="",
    )
    monkeypatch.setattr(module.subprocess, "run", mock_run)

    commit = module.get_last_sync_commit()

    assert commit == "a" * 40
    mock_run.assert_called_once_with(
        [
            "git",
            "log",
            "--grep=#sync: upstream pull",
            "--format=%H",
            "-n",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_get_modified_files_runs_git_without_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_shadow_modification_script()
    mock_run = MagicMock()
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="db/models.py\n\nexporter/webapp/main.py\n",
        stderr="",
    )
    monkeypatch.setattr(module.subprocess, "run", mock_run)

    files = module.get_modified_files(
        ["git", "show", "--name-only", "--format=", "abc123"]
    )

    assert files == {"db/models.py", "exporter/webapp/main.py"}
    mock_run.assert_called_once_with(
        ["git", "show", "--name-only", "--format=", "abc123"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_reviewed_noop_requires_exact_match(tmp_path: Path) -> None:
    module = load_shadow_modification_script()
    ledger_path = tmp_path / "reviewed_shadow_noops.json"
    ledger_path.write_text(
        json.dumps(
            [
                {
                    "sync_commit": "a" * 40,
                    "source": "source/",
                    "shadow": "shadow/",
                    "changed_paths": ["source/a.py", "source/b.py"],
                    "reason": "Reviewed and intentionally not ported.",
                }
            ]
        ),
        encoding="utf-8",
    )

    noops = module.load_reviewed_shadow_noops(ledger_path)

    assert module.is_reviewed_noop(
        noops,
        sync_commit="a" * 40,
        source="source/",
        shadow="shadow/",
        changed_paths=["source/b.py", "source/a.py"],
    )
    assert not module.is_reviewed_noop(
        noops,
        sync_commit="a" * 40,
        source="source/",
        shadow="shadow/",
        changed_paths=["source/a.py", "source/c.py"],
    )
    assert not module.is_reviewed_noop(
        noops,
        sync_commit="b" * 40,
        source="source/",
        shadow="shadow/",
        changed_paths=["source/a.py", "source/b.py"],
    )


def test_reviewed_noop_rejects_missing_reason(tmp_path: Path) -> None:
    module = load_shadow_modification_script()
    ledger_path = tmp_path / "reviewed_shadow_noops.json"
    ledger_path.write_text(
        json.dumps(
            [
                {
                    "sync_commit": "a" * 40,
                    "source": "source/",
                    "shadow": "shadow/",
                    "changed_paths": ["source/a.py"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="reason"):
        module.load_reviewed_shadow_noops(ledger_path)


def test_reviewed_noop_rejects_short_sync_commit(tmp_path: Path) -> None:
    module = load_shadow_modification_script()
    ledger_path = tmp_path / "reviewed_shadow_noops.json"
    ledger_path.write_text(
        json.dumps(
            [
                {
                    "sync_commit": "abc123",
                    "source": "source/",
                    "shadow": "shadow/",
                    "changed_paths": ["source/a.py"],
                    "reason": "Reviewed and intentionally not ported.",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="full 40-character lowercase git SHA"):
        module.load_reviewed_shadow_noops(ledger_path)


def test_reviewed_noop_rejects_unsafe_paths(tmp_path: Path) -> None:
    module = load_shadow_modification_script()
    ledger_path = tmp_path / "reviewed_shadow_noops.json"
    ledger_path.write_text(
        json.dumps(
            [
                {
                    "sync_commit": "a" * 40,
                    "source": "source/",
                    "shadow": "shadow/",
                    "changed_paths": ["../source/a.py"],
                    "reason": "Reviewed and intentionally not ported.",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must stay inside the repository"):
        module.load_reviewed_shadow_noops(ledger_path)


def test_check_shadows_skips_reviewed_noop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = load_shadow_modification_script()
    registry_path = tmp_path / "registry.json"
    ledger_path = tmp_path / "reviewed_shadow_noops.json"
    registry_path.write_text(
        json.dumps(
            {
                "modified_upstream_files": [],
                "russian_copies": {
                    "shadow/": {"upstream": "source/", "sync_rule": "MIRROR_EXACTLY"}
                },
                "sbs_copies": {},
                "dps_copies": {},
                "tamil_copies": {},
                "inspired_by_upstream": {},
                "unique_paths": [],
                "no_sync_files": [],
                "skip_sync_patterns": [],
            }
        ),
        encoding="utf-8",
    )
    ledger_path.write_text(
        json.dumps(
            [
                {
                    "sync_commit": "a" * 40,
                    "source": "source/",
                    "shadow": "shadow/",
                    "changed_paths": ["source/a.py"],
                    "reason": "Reviewed and intentionally not ported.",
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(module, "NOOP_LEDGER_PATH", ledger_path)
    monkeypatch.setattr(module, "get_last_sync_commit", lambda: "a" * 40)
    monkeypatch.setattr(
        module,
        "get_modified_files",
        MagicMock(side_effect=[{"source/a.py"}, set()]),
    )
    monkeypatch.setattr(
        module,
        "load_registry",
        lambda: RegistryData(
            modified_upstream_files=[],
            russian_copies={"shadow/": ShadowCopyEntry(upstream="source/")},
            sbs_copies={},
            dps_copies={},
            tamil_copies={},
            inspired_by_upstream={},
            unique_paths=[],
            no_sync_files=[],
            skip_sync_patterns=[],
        ),
    )

    with pytest.raises(SystemExit) as exc_info:
        module.check_shadows()

    assert exc_info.value.code == 0
