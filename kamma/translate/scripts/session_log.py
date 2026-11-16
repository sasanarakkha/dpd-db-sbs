"""Append one-line session records to kamma/translate/log.md and merge keys into kamma/translate/state.json."""

import json
from pathlib import Path
from typing import Any


def format_session_line(
    start: str, end: str, fields: dict[str, str | int], exit_code: int
) -> str:
    """Render `- <start> → <end> | k=v k=v ... exit=<code>`."""
    body = " ".join(f"{key}={value}" for key, value in fields.items())
    return f"- {start} → {end} | {body} exit={exit_code}"


def append_log_line(log_path: Path, line: str) -> None:
    """Append one line to the log, creating the file if needed."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    needs_newline = log_path.exists() and not log_path.read_text(
        encoding="utf-8"
    ).endswith("\n")
    with log_path.open("a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        f.write(line + "\n")


def update_state(state_path: Path, updates: dict[str, Any]) -> None:
    """Merge top-level keys into state.json, preserving every other key."""
    state: dict[str, Any] = {}
    if state_path.exists():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state = loaded
        except json.JSONDecodeError:
            state = {}
    state.update(updates)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
