#!/usr/bin/env python3

"""Check parity between docs/ (English source) and docs_rus/ (Russian translation)."""

import argparse
import json
import subprocess
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    get_prep_manifest_path,
    load_prep_manifest,
)
from tools.printer import printer as pr

ROOT = Path(__file__).resolve().parents[3]
ACCEPTED_SYNC_PATH = ROOT / "kamma/upstream_sync/accepted_sync.json"
DOCS_EN = ROOT / "docs"
DOCS_RU = ROOT / "docs_rus"

# docs_rus/ files intentionally without a docs/ counterpart — not flagged as unique surprises
EXPECTED_LOCAL_ONLY: set[str] = {
    "dpd_rus.md",
    "contributing/rus_collaboration.md",
    "technical/dpd_headwords_table_ru.md",
}

# docs/ files that are mirrored via redirect — no translation needed, skip staleness checks
NO_TRANSLATE: set[str] = {
    "changelog.md",
    "newsletters.md",
}


class DocsDiffError(RuntimeError):
    """Raised when docs git-diff evidence cannot be collected."""


def load_accepted_sha() -> str:
    data: dict[str, str] = json.loads(ACCEPTED_SYNC_PATH.read_text())
    return data["last_accepted_upstream_sha"]


def load_docs_sync_range(thread_dir: Path | None) -> tuple[str, str]:
    """Return the docs parity git range from the thread manifest, falling back to HEAD."""
    if thread_dir is None:
        return load_accepted_sha(), "HEAD"

    manifest = load_prep_manifest(get_prep_manifest_path(thread_dir))
    from_ref = manifest["from_upstream_sha"]
    to_ref = manifest["to_upstream_sha"]
    if not isinstance(from_ref, str) or not isinstance(to_ref, str):
        raise ValueError("prep manifest sync range must contain string refs")
    return from_ref, to_ref


def get_docs_changed_since(
    from_ref: str, to_ref: str = "HEAD", fail_on_error: bool = False
) -> set[str]:
    """Return relative paths (under docs/) changed in an explicit git range."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", from_ref, to_ref, "--", "docs/"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError as exc:
        message = f"git diff failed: {exc}"
        if fail_on_error:
            raise DocsDiffError(message) from exc
        pr.amber(f"{message} — staleness check skipped")
        return set()

    changed: set[str] = set()
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("docs/"):
            changed.add(stripped[len("docs/") :])
    return changed


def get_docs_diff(from_ref: str, docs_relative_path: str, to_ref: str = "HEAD") -> str:
    """Return exact git diff evidence for one docs/ file in an explicit git range."""
    try:
        result = subprocess.run(
            ["git", "diff", from_ref, to_ref, "--", f"docs/{docs_relative_path}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        return f"Unable to collect diff evidence for docs/{docs_relative_path}: {exc}"
    return result.stdout


def collect_md_files(directory: Path) -> set[str]:
    return {str(p.relative_to(directory)) for p in directory.rglob("*.md")}


def find_unexpected_local_files(unique_local: list[str]) -> list[str]:
    """Return docs_rus files without docs counterparts that are not expected local files."""
    return sorted(f for f in unique_local if f not in EXPECTED_LOCAL_ONLY)


def display_report_path(report_path: Path) -> Path:
    """Return a concise display path for report output."""
    resolved = report_path.resolve()
    try:
        return resolved.relative_to(ROOT)
    except ValueError:
        return resolved


def write_report(
    thread_dir: Path,
    sha: str,
    missing: list[str],
    stale: list[str],
    no_translate: list[str],
    unique_local: list[str],
    unexpected_local: list[str],
    to_ref: str = "HEAD",
) -> None:
    lines: list[str] = [
        "# Docs Translation Parity Report",
        "",
        f"Sync range: `{sha}` → `{to_ref}`",
        "",
        "---",
        "",
        "## Missing Translations",
        "",
    ]

    if missing:
        lines.append(
            "Files present in `docs/` with no `docs_rus/` counterpart — full translation needed:"
        )
        lines.append("")
        for f in missing:
            lines.append(f"- `docs/{f}` → create `docs_rus/{f}`")
    else:
        lines.append("None.")

    lines += [
        "",
        "## Stale Translations",
        "",
    ]

    if stale:
        lines.append(
            "Files in `docs/` changed since baseline SHA — corresponding Russian translation needs review:"
        )
        lines.append("")
        for f in stale:
            lines.append(f"- `docs/{f}` → review/update `docs_rus/{f}`")
        lines += [
            "",
            "## Stale Translation Diff Evidence",
            "",
        ]
        for f in stale:
            diff = get_docs_diff(sha, f, to_ref)
            lines += [
                f"### `docs/{f}`",
                "",
                "```diff",
                diff.rstrip(),
                "```",
                "",
            ]
    else:
        lines.append("None.")

    if no_translate:
        lines += [
            "",
            "## No-translate Files (HTML Redirect)",
            "",
            "Files mirrored via HTML redirect — no translation needed:",
            "",
        ]
        for f in no_translate:
            lines.append(f"- `docs_rus/{f}` (redirect)")

    lines += [
        "",
        "## Unique Local Files",
        "",
        "Files in `docs_rus/` with no `docs/` counterpart (no action needed):",
        "",
    ]
    for f in unique_local:
        marker = " ← expected" if f in EXPECTED_LOCAL_ONLY else ""
        lines.append(f"- `docs_rus/{f}`{marker}")

    if unexpected_local:
        lines += [
            "",
            "## Unexpected Local Files",
            "",
            "These `docs_rus/` files have no `docs/` counterpart and are not listed as expected local-only files:",
            "",
        ]
        for f in unexpected_local:
            lines.append(f"- `docs_rus/{f}`")

    report_path = thread_dir / "docs_parity_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    pr.green(f"Report written → {display_report_path(report_path)}")


def run_parity_check(thread_dir: Path | None, strict: bool = False) -> int:
    try:
        sha, to_ref = load_docs_sync_range(thread_dir)
    except FileNotFoundError as exc:
        pr.red(f"Manifest not found: {exc}")
        return 1
    except ValueError as exc:
        pr.red(f"Manifest invalid: {exc}")
        return 1

    pr.green_title(f"Docs parity check ({sha} -> {to_ref})")

    en_files = collect_md_files(DOCS_EN)
    ru_files = collect_md_files(DOCS_RU)
    try:
        if strict:
            changed = get_docs_changed_since(sha, to_ref, fail_on_error=True)
        else:
            changed = get_docs_changed_since(sha, to_ref)
    except DocsDiffError as exc:
        pr.red(str(exc))
        return 1

    missing: list[str] = sorted(f for f in en_files if f not in ru_files)
    stale: list[str] = sorted(
        f for f in en_files if f in changed and f in ru_files and f not in NO_TRANSLATE
    )
    unique_local: list[str] = sorted(f for f in ru_files if f not in en_files)
    unexpected_local = find_unexpected_local_files(unique_local)

    no_translate_list: list[str] = sorted(f for f in ru_files if f in NO_TRANSLATE)

    if missing:
        pr.no(f"{len(missing)} missing translations")
        for f in missing:
            pr.amber(f"  MISSING  docs_rus/{f}")
    else:
        pr.yes("no missing translations")

    if stale:
        pr.no(f"{len(stale)} stale translations")
        for f in stale:
            pr.amber(f"  STALE    docs_rus/{f}")
    else:
        pr.yes("no stale translations")

    if no_translate_list:
        pr.green(f"{len(no_translate_list)} no-translate files (informational)")
        for f in no_translate_list:
            pr.green(f"  REDIRECT  docs_rus/{f}")

    if unique_local:
        pr.green(f"{len(unique_local)} unique local files (informational)")
        for f in unique_local:
            pr.green(f"  LOCAL    docs_rus/{f}")

    if unexpected_local:
        pr.no(f"{len(unexpected_local)} unexpected local-only docs_rus files")
        for f in unexpected_local:
            pr.red(f"  UNEXPECTED docs_rus/{f}")

    if thread_dir:
        write_report(
            thread_dir,
            sha,
            missing,
            stale,
            no_translate_list,
            unique_local,
            unexpected_local,
            to_ref=to_ref,
        )

    if unexpected_local or (strict and (missing or stale)):
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check docs/ vs docs_rus/ translation parity."
    )
    parser.add_argument(
        "thread_dir", nargs="?", help="Thread folder to write report into"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when translations are missing or stale.",
    )
    args = parser.parse_args()

    thread_dir = Path(args.thread_dir) if args.thread_dir else None
    return run_parity_check(thread_dir, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
