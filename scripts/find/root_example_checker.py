#!/usr/bin/env python3

"""Report dpd_roots.root_example words that are missing from the headwords or whose headwords belong to a different root."""

import re
from collections import defaultdict
from dataclasses import dataclass

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.paths import ProjectPaths
from tools.printer import printer as pr

_NUMBER_SUFFIX = re.compile(r" \d.*$")


@dataclass(frozen=True)
class Finding:
    root: str
    word: str
    kind: str  # "WRONG_ROOT" or "NOT_FOUND"
    found_roots: tuple[str, ...]


def check_root_examples(
    root_examples: dict[str, str],
    lemma_roots: dict[str, set[str]],
) -> list[Finding]:
    """Return a Finding for every example word not backed by a headword of that root."""
    findings: list[Finding] = []
    for root, example in root_examples.items():
        for word in (w.strip() for w in example.split(",")):
            if not word:
                continue
            # root_example itself sometimes carries a numbered lemma ("nissanda 1"),
            # so match the way the keys are built in main().
            roots = lemma_roots.get(_NUMBER_SUFFIX.sub("", word))
            if roots is None:
                findings.append(Finding(root, word, "NOT_FOUND", ()))
            elif root not in roots:
                findings.append(Finding(root, word, "WRONG_ROOT", tuple(sorted(roots))))
    return findings


def main() -> None:
    pr.tic()
    pr.yellow_title("root example checker")

    db_session = get_db_session(ProjectPaths().dpd_db_path)
    root_examples: dict[str, str] = {
        root: example
        for root, example in db_session.query(DpdRoot.root, DpdRoot.root_example)
        if example and example.strip()
    }
    lemma_roots: dict[str, set[str]] = defaultdict(set)
    for lemma_1, root_key in db_session.query(
        DpdHeadword.lemma_1, DpdHeadword.root_key
    ):
        lemma_roots[_NUMBER_SUFFIX.sub("", lemma_1)].add(root_key)
    db_session.close()

    findings = check_root_examples(root_examples, lemma_roots)
    total = sum(1 for ex in root_examples.values() for w in ex.split(",") if w.strip())
    wrong = [f for f in findings if f.kind == "WRONG_ROOT"]
    not_found = [f for f in findings if f.kind == "NOT_FOUND"]

    pr.summary("roots with example", len(root_examples))
    pr.summary("example words", total)
    pr.summary("OK", total - len(findings))
    pr.summary("WRONG_ROOT", len(wrong))
    pr.summary("NOT_FOUND", len(not_found))
    pr.white("")

    by_root: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_root[f.root].append(f)
    for root, items in by_root.items():
        pr.white(root)
        for f in items:
            found_keys = ", ".join(r or "<no root_key>" for r in f.found_roots)
            found = f" (found: {found_keys})" if f.found_roots else ""
            pr.white(f"    {f.word}  {f.kind}{found}")

    pr.toc()


if __name__ == "__main__":
    main()
