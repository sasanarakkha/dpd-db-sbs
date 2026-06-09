"""Gemini CLI provider and AIManager adapter for headless LLM requests."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, NamedTuple, cast


class GeminiCliProviderError(RuntimeError):
    """Raised when the Gemini CLI provider cannot complete a request."""


class _Response(NamedTuple):
    content: str | None
    status_message: str


class GeminiCliManager:
    def request(
        self,
        prompt: str,
        prompt_sys: str | None = None,
        model: str = "gemini-3.1-flash-lite",
        timeout: float = 120.0,
        **kwargs: Any,
    ) -> _Response:
        try:
            content = generate_content(
                contents=prompt,
                system_instruction=prompt_sys or "",
                model=model,
                timeout=int(timeout),
            )
            return _Response(content=content, status_message=f"gemini_cli/{model}")
        except GeminiCliProviderError as e:
            return _Response(content=None, status_message=str(e))


def generate_content(
    contents: str,
    system_instruction: str,
    model: str,
    max_output_tokens: int = 32768,
    temperature: float = 0.1,
    timeout: int = 120,
) -> str:
    """Generate content using Gemini CLI headless mode."""

    gemini_path = _locate_gemini()
    prompt = _build_prompt(contents, system_instruction, max_output_tokens, temperature)
    command = [
        str(gemini_path),
        "-m",
        model,
        "-p",
        prompt,
        "--output-format",
        "json",
        "--approval-mode",
        "plan",
        "-e",
        "none",
    ]

    print(f"  -> gemini-cli {model} (timeout={timeout}s)...", flush=True)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise GeminiCliProviderError(f"{model} timed out after {timeout}s") from error

    if result.returncode != 0:
        raise GeminiCliProviderError(f"{model} failed: {_brief_command_error(result)}")

    response = _extract_response(result.stdout)
    if response is None or not response.strip():
        raise GeminiCliProviderError(f"{model} returned an empty response")
    return response


def _locate_gemini() -> Path:
    executable = shutil.which("gemini")
    if executable is None:
        raise GeminiCliProviderError("gemini executable not found on PATH")
    return Path(executable)


def _build_prompt(
    contents: str, system_instruction: str, max_output_tokens: int, temperature: float
) -> str:
    return (
        "Follow the system instruction below. Treat the USER CONTENT section as the "
        "full user input. Do not inspect local files or use tools unless the user "
        "content explicitly requires it.\n\n"
        "SYSTEM INSTRUCTION:\n"
        f"{system_instruction}\n\n"
        "REQUEST SETTINGS:\n"
        f"- max_output_tokens: {max_output_tokens}\n"
        f"- temperature: {temperature}\n"
        "\nUSER CONTENT:\n"
        f"{contents}\n"
    )


def _extract_response(stdout: str) -> str | None:
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise GeminiCliProviderError(
            f"Gemini CLI returned invalid JSON: {stdout[:500]}"
        ) from error

    if isinstance(parsed, str):
        return parsed
    if not isinstance(parsed, dict):
        raise GeminiCliProviderError("Gemini CLI JSON output was not an object")

    response = cast(dict[str, Any], parsed).get("response")
    if isinstance(response, str):
        return response
    text = cast(dict[str, Any], parsed).get("text")
    if isinstance(text, str):
        return text
    return None


def _brief_command_error(result: subprocess.CompletedProcess[str]) -> str:
    message = result.stderr.strip() or result.stdout.strip() or str(result.returncode)
    if len(message) <= 500:
        return message
    return f"{message[:497]}..."
