#!/usr/bin/env python3

"""Validate WHITELIST entries in test_shadow_parity.py are live (filter real upstream symbols).

A whitelist entry is "dead" when its token no longer appears in the upstream file's AST —
typically caused by upstream switching from relative to absolute import paths, or removing
the symbol altogether. Dead entries silently fail to filter the parity check.
"""

from pathlib import Path

import pytest

from tests.test_shadow_parity import (
    WHITELIST,
    extract_ast_info,
    get_python_pairs,
    whitelist_values,
)


def _is_live_entry(
    upstream_info: dict[str, set[str]], entry: dict[str, object]
) -> list[str]:
    """Check one whitelist entry dict against upstream AST. Returns list of stale tokens."""
    stale: list[str] = []
    for category in ("imports", "functions", "classes"):
        for token in whitelist_values(entry, category):  # type: ignore[arg-type]
            if token not in upstream_info[category]:
                stale.append(f"{category}:{token}")
    return stale


def check_whitelist_liveness() -> list[str]:
    """Check every real WHITELIST entry against its upstream file.

    Returns a list of `shadow:category:token` strings for dead entries.
    Entries with `"missing": True` are exempt (upstream file not yet shadowed).
    """
    shadow_to_upstream = dict(get_python_pairs())
    dead: list[str] = []

    for shadow, entry in WHITELIST.items():
        if entry.get("missing"):
            continue  # shadow file not yet created; exempt

        upstream = shadow_to_upstream.get(shadow)
        if upstream is None:
            continue  # not a registered shadow pair; skip

        upstream_info = extract_ast_info(upstream)
        if upstream_info is None:
            continue  # upstream file absent; skip silently

        for tok in _is_live_entry(upstream_info, entry):  # type: ignore[arg-type]
            dead.append(f"{shadow}:{tok}")

    return dead


# ---------------------------------------------------------------------------
# Synthetic fixture tests (use crafted temp files, not the real project)
# ---------------------------------------------------------------------------


def _upstream_ast(content: str, tmp_path: Path) -> dict[str, set[str]]:
    p = tmp_path / "_up.py"
    p.write_text(content)
    info = extract_ast_info(str(p))
    assert info is not None
    return info


def test_relative_import_in_whitelist_is_stale(tmp_path: Path) -> None:
    """A whitelist entry in relative form ('bar') flags as stale when upstream uses 'foo.bar'."""
    upstream_info = _upstream_ast("from foo import bar\n", tmp_path)
    # upstream_info["imports"] should contain "foo.bar", NOT bare "bar"
    assert "foo.bar" in upstream_info["imports"]
    assert "bar" not in upstream_info["imports"]

    stale_entry: dict[str, object] = {"imports": ["bar"]}  # relative form — stale
    stale = _is_live_entry(upstream_info, stale_entry)  # type: ignore[name-defined]  # noqa: F821
    assert stale, "relative import 'bar' should be flagged as stale"
    assert any("bar" in tok for tok in stale)


def test_fq_import_in_whitelist_passes(tmp_path: Path) -> None:
    """A whitelist entry in FQ form ('foo.bar') is live when upstream has 'from foo import bar'."""
    upstream_info = _upstream_ast("from foo import bar\n", tmp_path)

    good_entry: dict[str, object] = {"imports": ["foo.bar"]}  # FQ form — live
    stale = _is_live_entry(upstream_info, good_entry)  # type: ignore[name-defined]  # noqa: F821
    assert not stale, f"FQ entry should be live, but got: {stale}"


def test_stale_function_token_flagged(tmp_path: Path) -> None:
    """A whitelist functions entry for a function that's gone upstream is flagged."""
    upstream_info = _upstream_ast("def current_func(): pass\n", tmp_path)

    stale_entry: dict[str, object] = {"functions": ["old_func"]}
    stale = _is_live_entry(upstream_info, stale_entry)  # type: ignore[name-defined]  # noqa: F821
    assert any("old_func" in tok for tok in stale)


def test_good_function_token_passes(tmp_path: Path) -> None:
    """A whitelist functions entry for a function still present in upstream passes."""
    upstream_info = _upstream_ast("def current_func(): pass\n", tmp_path)

    good_entry: dict[str, object] = {"functions": ["current_func"]}
    stale = _is_live_entry(upstream_info, good_entry)  # type: ignore[name-defined]  # noqa: F821
    assert not stale


# ---------------------------------------------------------------------------
# Real-whitelist integration test
# ---------------------------------------------------------------------------


def test_real_whitelist_is_live() -> None:
    """All real WHITELIST entries (excluding missing=True) match actual upstream symbols."""
    dead = check_whitelist_liveness()  # type: ignore[name-defined]  # noqa: F821
    if dead:
        report = "\n  ".join(dead)
        pytest.fail(
            f"Dead whitelist entries detected (token no longer in upstream AST):\n  {report}\n"
            "Fix by updating the token to the current FQ import form, or removing the entry."
        )
