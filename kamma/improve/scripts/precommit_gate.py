"""Run ruff/pyright/pyrefly on exact source files and pytest on explicit test files."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _run(cmd: list[str], desc: str) -> tuple[int, str, list[str]]:
    """Run a command and return (exit_code, stdout+stderr, list of fixed paths)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (1, f"{desc} timed out after 300s", [])
    except FileNotFoundError:
        return (1, f"{desc}: command not found ({cmd[0]})", [])

    output = result.stdout.strip() + "\n" + result.stderr.strip()
    output = output.strip()

    fixed: list[str] = []
    if "ruff check --fix" in " ".join(cmd) and result.returncode == 0:
        for line in result.stdout.split("\n"):
            if line.startswith("Fixed ") or line.endswith(" (fixed)"):
                line = line.strip()
                if line.startswith("Fixed "):
                    fixed.append(line.removeprefix("Fixed ").strip())
    return (result.returncode, output, fixed)


def main() -> None:
    args = sys.argv[1:]
    test_files: list[str] = []
    source_files: list[str] = []

    i = 0
    while i < len(args):
        if args[i] == "--test":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                test_files.append(args[i])
                i += 1
        else:
            source_files.append(args[i])
            i += 1

    if not source_files:
        print("FAIL: No source files provided.", file=sys.stderr)
        sys.exit(1)

    if not test_files:
        print(
            "FAIL: --test is required. Supply at least one pytest file with --test <path>.",
            file=sys.stderr,
        )
        sys.exit(1)

    for f in source_files + test_files:
        fp = (REPO_ROOT / f).resolve()
        if not fp.exists():
            print(f"FAIL: File not found: {f}", file=sys.stderr)
            sys.exit(1)

    # ruff check --fix
    rc, out, fixed = _run(
        ["uv", "run", "ruff", "check", "--fix"] + source_files,
        "ruff check --fix",
    )
    for fp in fixed:
        print(f"fixed: {fp}")

    # ruff format
    rc2, out2, _ = _run(
        ["uv", "run", "ruff", "format"] + source_files,
        "ruff format",
    )

    # pyright
    rc3, out3, _ = _run(
        ["uv", "run", "pyright"] + source_files,
        "pyright",
    )

    # pyrefly
    rc4, out4, _ = _run(
        [
            "uv",
            "run",
            "--with",
            "pyrefly",
            "pyrefly",
            "check",
            "--min-severity",
            "warn",
        ]
        + source_files,
        "pyrefly",
    )

    # Collect failures in order (first failure wins)
    if rc != 0:
        first_error = out.split("\n")[0] if out else "unknown ruff error"
        print(f"FAIL: ruff check --fix: {first_error}")
        sys.exit(1)
    if rc2 != 0:
        first_error = out2.split("\n")[0] if out2 else "unknown ruff format error"
        print(f"FAIL: ruff format: {first_error}")
        sys.exit(1)
    if rc3 != 0:
        first_error = out3.split("\n")[0] if out3 else "unknown pyright error"
        print(f"FAIL: pyright: {first_error}")
        sys.exit(1)
    if rc4 != 0:
        first_error = out4.split("\n")[0] if out4 else "unknown pyrefly error"
        print(f"FAIL: pyrefly: {first_error}")
        sys.exit(1)

    # pytests
    rc5, out5, _ = _run(
        ["uv", "run", "pytest", "-v"] + test_files,
        "pytest",
    )
    if rc5 != 0:
        first_error = out5.split("\n")[-2] if out5 else "unknown pytest error"
        print(f"FAIL: pytest: {first_error}")
        sys.exit(1)

    print("PASS")


if __name__ == "__main__":
    main()
