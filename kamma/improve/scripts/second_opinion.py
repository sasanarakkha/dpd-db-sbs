"""Send a file to AIManager for review. Optional --approach-only flag."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def main() -> None:
    approach_only = "--approach-only" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--approach-only"]

    if len(args) != 1:
        print(
            "Usage: second_opinion.py [--approach-only] <file_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    file_rel = args[0]
    file_path = (REPO_ROOT / file_rel).resolve()

    if not file_path.exists():
        print(f"File not found: {file_rel}", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    if approach_only:
        prompt = (
            "Review this file for a single purpose: is there a significantly "
            "simpler or more elegant approach that could achieve the same result "
            "with substantially less code? Only suggest changes that would "
            "meaningfully reduce complexity or length. Do not comment on type "
            "hints, style, naming, or minor refactors. If no substantial "
            "simplification is possible, say so explicitly.\n\n" + content
        )
    else:
        prompt = (
            "Give a thorough review of this file. Cover: (1) refactor improvements — "
            "type hints, dead code, complexity, conventions; (2) whether a significantly "
            "simpler or more elegant approach could achieve the same result with "
            "substantially less code.\n\n" + content
        )

    from tools.ai_manager import AIManager

    response = AIManager().request(prompt=prompt, grounding=True)
    print(response.content if response.content else response.status_message)


if __name__ == "__main__":
    main()
