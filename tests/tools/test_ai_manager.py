"""Unit tests for AIManager request behavior, focused on the per-request timeout."""

from typing import Any, NamedTuple

from tools.ai_manager import AIManager, _load_models_from_json


class _StubResponse(NamedTuple):
    content: str | None
    status_message: str


class _RecordingProvider:
    """Provider stub that records the timeout it was called with."""

    def __init__(self, status_message: str = "stub") -> None:
        self.received_timeout: float | None = None
        self.status_message = status_message

    def request(self, **kwargs: Any) -> _StubResponse:
        self.received_timeout = kwargs.get("timeout")
        return _StubResponse(content="ok", status_message=self.status_message)


class _FailingProvider:
    """Provider stub that records a failed provider attempt."""

    def request(self, **kwargs: Any) -> _StubResponse:
        return _StubResponse(content=None, status_message="first provider failed")


def _make_manager(
    provider: _RecordingProvider,
    timeout: float = 150.0,
) -> AIManager:
    """Build an AIManager without running its heavy __init__ provider setup."""
    manager = object.__new__(AIManager)
    manager.providers = {"stub": provider}
    manager.DEFAULT_MODELS = [("stub", "stub-model", 0, timeout)]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}
    return manager


def _make_fallback_manager(
    failing_provider: _FailingProvider,
    success_provider: _RecordingProvider,
) -> AIManager:
    """Build an AIManager with one failing provider before one successful provider."""
    manager = object.__new__(AIManager)
    manager.providers = {"failing": failing_provider, "stub": success_provider}
    manager.DEFAULT_MODELS = [
        ("failing", "failing-model", 0, 150.0),
        ("stub", "stub-model", 0, 150.0),
    ]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}
    return manager


def test_request_passes_150s_timeout_to_provider() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider, timeout=150.0)

    response = manager.request(prompt="hi", prompt_sys="sys")

    assert response.content == "ok"
    assert provider.received_timeout == 150.0


def test_request_clean_success_omits_failed_attempt_suffix() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert response.status_message.startswith("SUCCESS")
    assert "failed attempt" not in response.status_message


def test_request_success_status_names_provider_and_model() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "stub/stub-model" in response.status_message


def test_request_success_after_failure_includes_failed_attempt_details() -> None:
    failing_provider = _FailingProvider()
    success_provider = _RecordingProvider()
    manager = _make_fallback_manager(failing_provider, success_provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert response.status_message.startswith("SUCCESS")
    assert "after 1 failed attempt(s):" in response.status_message
    assert "failing/failing-model ERROR" in response.status_message
    assert "first provider failed" in response.status_message


def test_request_fallback_success_names_succeeding_provider() -> None:
    manager = _make_fallback_manager(_FailingProvider(), _RecordingProvider())

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "stub/stub-model" in response.status_message
    assert "after 1 failed attempt(s):" in response.status_message


def test_request_drops_bland_success_provider_detail() -> None:
    provider = _RecordingProvider(status_message="Success in 1.00s")
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "(Success" not in response.status_message


def test_request_keeps_informative_success_provider_detail() -> None:
    provider = _RecordingProvider(status_message="model: special-variant")
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "(model: special-variant)" in response.status_message


def test_antigravity_has_per_model_timeout() -> None:
    """antigravity_cli model entry must carry a 150s per-model timeout."""
    models = _load_models_from_json()
    agy_entries = [m for m in models["default"] if m[0] == "antigravity_cli"]
    assert len(agy_entries) == 1, (
        "expected exactly one antigravity_cli entry in default chain"
    )
    assert len(agy_entries[0]) == 4, (
        "model tuple must be (provider, model, delay, timeout)"
    )
    assert agy_entries[0][3] == 150.0


def test_request_uses_per_model_timeout() -> None:
    """request() must pass the per-model timeout to the provider, not the hardcoded 150s."""
    provider = _RecordingProvider()
    manager = _make_manager(provider, timeout=90.0)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert provider.received_timeout == 90.0
