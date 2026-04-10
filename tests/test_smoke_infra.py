"""Tests for smoke-test infrastructure behavior and spec-aligned implementation details."""

from __future__ import annotations

import importlib.util
import inspect
import os
import subprocess
import sys
from pathlib import Path


def load_smoke_test_module():
    """Load the smoke test script as a module for direct testing."""
    module_name = "tests.smoke_test_sync"
    module_path = Path(__file__).with_name("smoke_test_sync.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_run_component_does_not_use_sys_path_hacks() -> None:
    """The component runner should avoid mutating sys.path."""
    smoke_test_sync = load_smoke_test_module()

    source = inspect.getsource(smoke_test_sync._run_component)

    assert "sys.path" not in source


def test_phase3_gui_uses_subprocess_launch_and_cleanup(monkeypatch) -> None:
    """The GUI smoke check should launch the real app subprocess and terminate it."""
    smoke_test_sync = load_smoke_test_module()

    class FakeProcess:
        def __init__(self) -> None:
            self.pid = 1234
            self.terminate_called = False
            self.kill_called = False
            self.communicate_calls = 0

        def communicate(self, timeout: int):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(cmd=["uv"], timeout=timeout)
            return ("", "")

        def terminate(self) -> None:
            self.terminate_called = True

        def kill(self) -> None:
            self.kill_called = True

    fake_process = FakeProcess()
    popen_calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_popen(args, **kwargs):
        popen_calls.append((args, kwargs))
        return fake_process

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(os, "killpg", lambda pid, sig: None)

    assert smoke_test_sync.phase3_gui() is True
    assert popen_calls
    assert popen_calls[0][0] == ["uv", "run", "python", "gui2/main.py"]
    assert popen_calls[0][1]["start_new_session"] is True
