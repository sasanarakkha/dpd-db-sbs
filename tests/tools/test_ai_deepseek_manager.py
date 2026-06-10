"""Verify DeepSeek provider request payload handling for JSON-oriented AI calls."""

from typing import Any

import requests

from tools.ai_deepseek_manager import DeepseekManager


class _FakeResponse(requests.Response):
    def __init__(self, content: str = '{"ok": true}') -> None:
        super().__init__()
        self.status_code = 200
        self.json_content = content

    def json(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "choices": [
                {
                    "message": {
                        "content": self.json_content,
                    },
                    "finish_reason": "stop",
                }
            ]
        }


class _CapturingDeepseekManager(DeepseekManager):
    def __init__(self) -> None:
        self.api_key = "test"
        self.api_key_name = "deepseek"
        self.headers: dict[str, str] = {}
        self.captured_payload: dict[str, Any] | None = None

    def balance(self) -> dict[str, Any]:
        return {"balance_infos": [{"total_balance": "1"}]}

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> _FakeResponse:
        self.captured_payload = payload
        return _FakeResponse()


def test_request_disables_thinking_mode_by_default() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["thinking"] == {"type": "disabled"}


def test_request_allows_explicit_thinking_override() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(
        prompt="Return JSON.",
        model="deepseek-v4-flash",
        thinking={"type": "enabled", "reasoning_effort": "high"},
    )

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["thinking"] == {
        "type": "enabled",
        "reasoning_effort": "high",
    }


def test_request_uses_raised_max_tokens_default() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["max_tokens"] == 8192


def test_request_allows_explicit_max_tokens_override() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(
        prompt="Return JSON.",
        model="deepseek-v4-flash",
        max_tokens=512,
    )

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["max_tokens"] == 512
