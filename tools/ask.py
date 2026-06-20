#!/usr/bin/env python3
# Colored interactive prompts using the printer module.

import sys
import termios
import tty

# ANSI color codes
CYAN = "\033[36m"
RED = "\033[31m"
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
        # Check if stdin is a TTY
        if not sys.stdin.isatty():
            return _read_line_fallback()

        # Is a TTY, use raw mode for single character
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (OSError, termios.error):
        return _read_line_fallback()


def ask_question(question: str) -> str:
    """Ask a question with color. Return the first char of the response."""
    # Print to stderr so it displays even when stdout is captured
    sys.stderr.write(f"{CYAN}{question}{RESET}")
    sys.stderr.flush()

    response = read_single_char()
    sys.stderr.write("\n")
    sys.stderr.flush()

    if response == "q":
        sys.stderr.write(f"{RED}Aborted by user.{RESET}\n")
        sys.stderr.flush()
        sys.exit(1)

    # Return the character
    return response


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(f"{RED}Usage: ask.py '<question>'{RESET}\n")
        sys.exit(1)

    answer = ask_question(sys.argv[1])
    # Output the answer so bash can check it
    print(answer, end="")
