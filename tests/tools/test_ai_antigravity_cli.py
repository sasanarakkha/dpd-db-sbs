"""Tests for the Antigravity CLI provider prompt transport guard."""

from pathlib import Path

import pytest

import tools.ai_antigravity_cli as antigravity_cli
from tools.antigravity_cli_models import RunResult


def _patch_agy(monkeypatch: pytest.MonkeyPatch, stdout: str) -> None:
    monkeypatch.setattr(
        antigravity_cli, "_locate_antigravity", lambda: Path("/usr/bin/true")
    )
    monkeypatch.setattr(
        antigravity_cli,
        "run_antigravity_print",
        lambda *args, **kwargs: RunResult(returncode=0, stdout=stdout, stderr=""),
    )


def test_prompt_size_budget_is_safe_margin() -> None:
    assert antigravity_cli.MAX_ARGV_PROMPT_BYTES == 700_000


def test_request_rejects_oversized_prompt_before_locating_agy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_locate() -> Path:
        raise AssertionError("agy lookup should not run for oversized prompts")

    monkeypatch.setattr(antigravity_cli, "_locate_antigravity", fail_locate)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="x" * 800_000,
        prompt_sys="s",
    )

    assert response.content is None
    assert "too large for argv transport" in response.status_message


def test_small_prompt_fits_prompt_budget() -> None:
    prompt = antigravity_cli._build_prompt(
        contents="x" * 100,
        system_instruction="s",
        max_output_tokens=32768,
        temperature=0.1,
    )

    assert len(prompt.encode("utf-8")) < antigravity_cli.MAX_ARGV_PROMPT_BYTES


def test_request_classifies_timeout_text_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(monkeypatch, "Error: timed out waiting for response")

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content is None
    assert "timed out waiting for response" in response.status_message


def test_request_classifies_auth_prompt_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(
        monkeypatch,
        "Authentication required. Please visit the URL to log in:\n"
        "  https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=x",
    )

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content is None
    assert "authentication required" in response.status_message


def test_request_keeps_normal_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_agy(monkeypatch, '{"translation": "x", "scores": {}}')

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content == '{"translation": "x", "scores": {}}'


def test_request_keeps_multiline_content_mentioning_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = '{"translation": "Error: this is part of a translation",\n "scores": {}}'
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content == stdout
