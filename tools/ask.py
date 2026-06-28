#!/usr/bin/env python3
# Colored interactive prompts and print statements for bash scripts.

import argparse
import sys
import termios
import tty

COLORS: dict[str, str] = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}
RESET = "\033[0m"


def _read_line_fallback() -> str:
    """Read one line of input and return its first lowercase char, or '' on EOF/empty."""
    try:
        line = sys.stdin.readline().strip().lower()
        return line[0] if line else ""
    except EOFError:
        return ""


def read_single_char() -> str:
    """Read a single character without requiring Enter (if TTY). Falls back to line input for pipes."""
    try:
        fd = sys.stdin.fileno()
        if not sys.stdin.isatty():
            return _read_line_fallback()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (OSError, termios.error):
        return _read_line_fallback()


def ask_question(question: str, color: str = "cyan") -> str:
    """Ask a question with color. Return the first char of the response."""
    ansi = COLORS.get(color, COLORS["cyan"])
    sys.stderr.write(f"{ansi}{question}{RESET}")
    sys.stderr.flush()

    response = read_single_char()
    sys.stderr.write("\n")
    sys.stderr.flush()

    if response == "q":
        sys.stderr.write(f"{COLORS['red']}Aborted by user.{RESET}\n")
        sys.stderr.flush()
        sys.exit(1)

    return response


def print_message(message: str, color: str = "cyan") -> None:
    """Print a colored message to stderr without waiting for input."""
    ansi = COLORS.get(color, COLORS["cyan"])
    sys.stderr.write(f"{ansi}{message}{RESET}\n")
    sys.stderr.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Colored interactive prompts and print statements for bash scripts."
    )
    parser.add_argument("message", help="The question or message to display.")
    parser.add_argument(
        "--print",
        "-p",
        action="store_true",
        dest="print_only",
        help="Print message without waiting for input.",
    )
    parser.add_argument(
        "--color",
        "-c",
        default="cyan",
        choices=list(COLORS.keys()),
        help="Color name (default: cyan).",
    )
    args = parser.parse_args()

    if args.print_only:
        print_message(args.message, args.color)
    else:
        answer = ask_question(args.message, args.color)
        print(answer, end="")
