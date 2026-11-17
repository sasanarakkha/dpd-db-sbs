"""Propose and verify Russian cognates for ledger units in off-peak AI batches, saving the ledger after every batch."""

import argparse
import copy
import json
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from kamma.translate.scripts.offpeak import require_offpeak
from scripts.ru_cognate.ru_cognate_etyma import strip_accents
from scripts.ru_cognate.ru_cognate_ledger import LEDGER_PATH, read_ledger, write_ledger
from scripts.ru_cognate.ru_cognate_sound import sound_label
from tools.ai_json_parser import JSONParser
from tools.ai_manager import AIManager
from tools.paths import ProjectPaths
from tools.printer import printer as pr

Row = dict[str, str]
Item = dict[str, object]
Members = dict[tuple[str, str], list[str]]
Ask = Callable[[str, str, bool], str | None]

MAX_WORDS = 3
MAX_MEMBERS = 5
WORD_RE = re.compile(r"^[а-яё]+(-[а-яё]+)*$")
PROPOSE_VERDICTS = {"cognate", "none", "unsure"}
VERIFY_ETYMON = {"same", "different", "loan", "uncertain"}
VERIFY_FORM = {"base", "derivative"}
VERIFY_MEANING = {"close", "drifted", "far"}
# DeepSeek-only request overrides for verify; thinking tokens count against max_tokens.
VERIFY_REQUEST_OPTIONS: dict[str, object] = {
    "thinking": {"type": "enabled"},
    "max_tokens": 32768,
}

# DeepSeek-only: verify with thinking off (provider default max_tokens applies).
VERIFY_NO_THINKING: dict[str, str] = {"type": "disabled"}

PROPOSE_SYSTEM = (
    "You are an Indo-European comparative linguist. You judge whether a Pāḷi word "
    "has an inherited Russian cognate, that is a Russian word descended from the "
    "same Proto-Indo-European (PIE) etymon. You answer with JSON only."
)
VERIFY_SYSTEM = (
    "You are a sceptical Indo-European comparative linguist checking a claim that "
    "Russian words are inherited cognates of a Pāḷi/Sanskrit etymon. You work from "
    "your own knowledge and the cited source only. You answer with JSON only."
)

PROPOSE_RULES = """\
For each unit below decide whether it has 1-3 Russian words that are INHERITED cognates
(same PIE etymon) of the Pāḷi/Sanskrit word.
Rules:
- "none" is the expected answer for most units. Use it freely.
- Inherited words only. Loan words (карма, будда, нирвана, шаман) are NOT cognates.
- Sound resemblance is not evidence. Give a PIE root and a citable source (e.g. Wiktionary,
  Mayrhofer, Vasmer). If you cannot cite one, the verdict is "unsure".
- Russian words: lower case, Cyrillic only, no stress marks, most recognisable first, at most 3.
Reply with JSON of this shape, one item per unit, `unit_key` copied exactly:
{"comparisons": [{"unit_key": "...", "pie_root": "*...", "ru_candidates": ["..."],
 "source": "...", "confidence": 1-10, "verdict": "cognate|none|unsure"}]}
For "none" use "pie_root": "", "ru_candidates": [].
"""

VERIFY_RULES = """\
For each claim below you label EVERY word in "claimed Russian cognates" separately. You do not
choose a final set; code does that from your labels.
Note: the claimed PIE root is only a hint. It often is a PIE word form rather than the bare root
(*h₁n̥gʷnis "fire" for aggi, *h₂isketi for √is) or is spelled differently. Judge against the real etymon
of the Pāḷi/Sanskrit words, never label a word "different" only because the claimed string is a word form.
Labels for each word:
- etymon: "same" if a standard etymology (Vasmer, Derksen, Wiktionary) derives this word itself from the
  same PIE root as the Pāḷi/Sanskrit side; "different" if it comes from another root; "loan" if it is
  borrowed; "uncertain" if you cannot say.
- form: "derivative" if the word is built on another Russian word with the same root (идти is "base";
  прийти and найти are "derivative"); otherwise "base".
- meaning: compare with the member headwords listed for the unit (they are the words that will show the
  cognate), not the root meaning. "close", "drifted" or "far".
Examples (decided by the dictionary editor):
- √ad "eat": еда is same, base, close. медведь ("bear") has meaning "far".
- √ādā "take": дать has meaning "far". √dā 1 "give": дать has meaning "close".
- √i 1 "go": прийти has form "derivative".
- √an "breathe": вонь has meaning "drifted".
List the words most recognisable first.
Reply with JSON of this shape, one item per unit, `unit_key` copied exactly, every claimed word exactly
once, `word` copied exactly, fields in this order:
{"comparisons": [{"unit_key": "...", "words": [{"word": "...", "note": "...",
 "etymon": "same|different|loan|uncertain", "form": "base|derivative",
 "meaning": "close|drifted|far"}]}]}
`note`: write it FIRST for each word, as one short sentence naming the word's PIE root, or saying why it is
not a cognate. Do not think aloud in it.
"""


def parse_words(raw: object) -> list[str] | None:
    """Return normalised Russian words, or None when raw is not a list of 0-3 Cyrillic words."""
    if not isinstance(raw, list):
        return None
    words: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            return None
        word = strip_accents(item).strip().lower()
        if not WORD_RE.match(word):
            return None
        if word not in words:
            words.append(word)
    if len(words) > MAX_WORDS:
        return None
    return words


def parse_response(content: str) -> list[Item] | None:
    """Extract the list of items from an AI reply, or None when it cannot be parsed."""
    extracted = JSONParser().extract_json_from_response(content)
    if extracted is None:
        return None
    try:
        data = json.loads(extracted)
    except json.JSONDecodeError:
        return None
    items = data.get("comparisons") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None
    return [i for i in items if isinstance(i, dict)]


def _field(label: str, value: str) -> str:
    return f"  {label}: {value}\n" if value else ""


def build_propose_prompt(rows: list[Row], members: Members) -> str:
    """Build the propose prompt: rules plus, per unit, meaning, Sanskrit side, members, English cognate."""
    out = [PROPOSE_RULES, "Units:\n"]
    for row in rows:
        block = f"- unit_key: {row['unit_key']}\n  unit_type: {row['unit_type']}\n"
        block += _field("Pāḷi meaning", row["pali_meaning"])
        block += _field("Sanskrit", row["sanskrit"])
        block += _field("upstream English cognate", row["en_cognate"])
        listed = members.get((row["unit_type"], row["unit_key"]), [])
        if listed:
            block += "  member headwords:\n" + "".join(f"    - {m}\n" for m in listed)
        out.append(block)
    return "\n".join(out)


def build_verify_prompt(rows: list[Row], members: Members) -> str:
    """Build the verify prompt from the claim and member headwords: no confidence, no proposer reasoning."""
    out = [VERIFY_RULES, "Units:\n"]
    for row in rows:
        block = f"- unit_key: {row['unit_key']}\n  unit_type: {row['unit_type']}\n"
        block += _field("Pāḷi meaning", row["pali_meaning"])
        block += _field("Sanskrit", row["sanskrit"])
        block += _field("claimed PIE root", row["pie_root"])
        block += _field("claimed Russian cognates", row["ru_candidates"])
        block += _field("cited source", row["source"])
        listed = members.get((row["unit_type"], row["unit_key"]), [])
        if listed:
            block += "  member headwords:\n" + "".join(f"    - {m}\n" for m in listed)
        out.append(block)
    return "\n".join(out)


def _match(
    rows: list[Row], items: list[Item]
) -> tuple[list[tuple[Row, Item]], list[str]]:
    """Pair each item with its batch row by unit_key; report unknown and duplicate keys."""
    by_key = {r["unit_key"]: r for r in rows}
    seen: set[str] = set()
    pairs: list[tuple[Row, Item]] = []
    problems: list[str] = []
    for item in items:
        key = item.get("unit_key")
        if not isinstance(key, str) or key not in by_key:
            problems.append(f"unknown unit_key: {key!r}")
        elif key in seen:
            problems.append(f"duplicate unit_key: {key}")
        else:
            seen.add(key)
            pairs.append((by_key[key], item))
    for key in by_key:
        if key not in seen:
            problems.append(f"no answer for: {key}")
    return pairs, problems


def apply_propose(rows: list[Row], items: list[Item]) -> tuple[int, list[str]]:
    """Update pending rows from valid propose items in place; return (changed, problems)."""
    pairs, problems = _match(rows, items)
    changed = 0
    for row, item in pairs:
        key = row["unit_key"]
        verdict = item.get("verdict")
        words = parse_words(item.get("ru_candidates"))
        confidence = item.get("confidence")
        pie_root = item.get("pie_root", "")
        source = item.get("source", "")
        if verdict not in PROPOSE_VERDICTS:
            problems.append(f"{key}: bad verdict {verdict!r}")
        elif words is None:
            problems.append(f"{key}: bad ru_candidates {item.get('ru_candidates')!r}")
        elif (
            not isinstance(confidence, int)
            or isinstance(confidence, bool)
            or not 1 <= confidence <= 10
        ):
            problems.append(f"{key}: bad confidence {confidence!r}")
        elif not isinstance(pie_root, str) or not isinstance(source, str):
            problems.append(f"{key}: bad pie_root/source")
        elif verdict not in ("none", "unsure") and not words:
            problems.append(f"{key}: {verdict} without words")
        else:
            row["method"] = "agent"
            row["confidence"] = str(confidence)
            row["source"] = source
            row["pie_root"] = pie_root
            row["ru_candidates"] = ", ".join(words)
            row["status"] = "proposed" if verdict != "none" and words else "none"
            changed += 1
    return changed, problems


def _normalise_word(raw: str) -> str:
    return strip_accents(raw).strip().lower()


def _parse_labels(
    item: Item, candidates: list[str]
) -> tuple[list[dict[str, str]], str | None]:
    """Validate one verify item's per-word labels; return (labels, problem)."""
    raw_words = item.get("words")
    if not isinstance(raw_words, list):
        return [], "words is not a list"
    labels: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in raw_words:
        if not isinstance(raw, dict):
            return [], "word entry is not an object"
        word = raw.get("word")
        note = raw.get("note")
        if not isinstance(word, str):
            return [], f"bad word {word!r}"
        word = _normalise_word(word)
        if word not in candidates:
            return [], f"word not in candidates: {word}"
        if word in seen:
            return [], f"duplicate word: {word}"
        if not isinstance(note, str) or not note.strip():
            return [], f"empty note for {word}"
        entry = {"word": word, "note": note.strip()}
        for name, allowed in (
            ("etymon", VERIFY_ETYMON),
            ("form", VERIFY_FORM),
            ("meaning", VERIFY_MEANING),
        ):
            value = raw.get(name)
            if not isinstance(value, str) or value not in allowed:
                return [], f"bad {name} for {word}: {value!r}"
            entry[name] = value
        seen.add(word)
        labels.append(entry)
    missing = [w for w in candidates if w not in seen]
    if missing:
        return [], f"missing words: {', '.join(missing)}"
    return labels, None


def _add_sound(row: Row, labels: list[dict[str, str]]) -> None:
    """Set each word's `sound` from the code-side label (the model no longer labels sound)."""
    for entry in labels:
        entry["sound"] = sound_label(row["unit_key"], row["sanskrit"], entry["word"])


def _outcome(entry: dict[str, str]) -> str:
    """Return "keep", "flag" or "drop" for one word's labels.

    keep = same etymon, base form, sound close, meaning close; flag = same + base +
    sound not none + meaning not far + (sound close or meaning close); the rest is dropped.
    """
    if entry["etymon"] != "same" or entry["form"] != "base":
        return "drop"
    if entry["sound"] == "close" and entry["meaning"] == "close":
        return "keep"
    if (
        entry["sound"] != "none"
        and entry["meaning"] != "far"
        and "close" in (entry["sound"], entry["meaning"])
    ):
        return "flag"
    return "drop"


def _candidates(row: Row) -> list[str]:
    return [_normalise_word(w) for w in row["ru_candidates"].split(", ") if w.strip()]


def _note(labels: list[dict[str, str]]) -> str:
    return "; ".join(
        f"{e['word']} [{e['etymon']}/{e['form']}/sound {e['sound']} (code)"
        f"/meaning {e['meaning']}]: {e['note']}"
        for e in labels
    )


def _set_result(
    row: Row, labels: list[dict[str, str]], outcomes: list[str], note: str
) -> None:
    """Write ru_final / ru_flagged / verdict / note / status from per-word outcomes."""
    kept = [e["word"] for e, o in zip(labels, outcomes) if o == "keep"]
    flagged = [e["word"] for e, o in zip(labels, outcomes) if o == "flag"]
    overflow = kept[MAX_WORDS:]
    kept = kept[:MAX_WORDS]
    extra = set(flagged) | set(overflow)
    row["ru_final"] = ", ".join(kept)
    row["ru_flagged"] = ", ".join(e["word"] for e in labels if e["word"] in extra)
    row["verifier_verdict"] = "confirmed" if kept else "rejected"
    row["verifier_note"] = note
    row["status"] = "verified" if kept else "disputed"


def apply_verify(rows: list[Row], items: list[Item]) -> tuple[int, list[str]]:
    """Update proposed rows from per-word verify labels in place; return (changed, problems).

    Code derives each word's outcome with `_outcome`.
    """
    pairs, problems = _match(rows, items)
    changed = 0
    for row, item in pairs:
        key = row["unit_key"]
        labels, problem = _parse_labels(item, _candidates(row))
        if problem:
            problems.append(f"{key}: {problem}")
            continue
        _add_sound(row, labels)
        _set_result(row, labels, [_outcome(e) for e in labels], _note(labels))
        changed += 1
    return changed, problems


def apply_verify_pair(
    rows: list[Row], items_a: list[Item], items_b: list[Item]
) -> tuple[int, list[str]]:
    """Combine two independent verify passes: keep if both keep, drop if either drops, else flag."""
    pairs_a, problems_a = _match(rows, items_a)
    pairs_b, problems_b = _match(rows, items_b)
    problems = [f"pass 1: {p}" for p in problems_a]
    problems += [f"pass 2: {p}" for p in problems_b]
    item_b = {r["unit_key"]: i for r, i in pairs_b}
    changed = 0
    for row, item in pairs_a:
        key = row["unit_key"]
        other = item_b.get(key)
        if other is None:
            continue
        candidates = _candidates(row)
        labels_a, problem_a = _parse_labels(item, candidates)
        labels_b, problem_b = _parse_labels(other, candidates)
        if problem_a:
            problems.append(f"pass 1: {key}: {problem_a}")
        if problem_b:
            problems.append(f"pass 2: {key}: {problem_b}")
        if problem_a or problem_b:
            continue
        _add_sound(row, labels_a)
        _add_sound(row, labels_b)
        out_b = {e["word"]: _outcome(e) for e in labels_b}
        outcomes: list[str] = []
        differs: list[str] = []
        for entry in labels_a:
            first, second = _outcome(entry), out_b[entry["word"]]
            if first == second:
                outcomes.append(first)
            else:
                outcomes.append("drop" if "drop" in (first, second) else "flag")
                differs.append(f"{entry['word']} {first}/{second}")
        note = _note(labels_a)
        if differs:
            note += " || pass 2 differs: " + ", ".join(differs)
        _set_result(row, labels_a, outcomes, note)
        changed += 1
    return changed, problems


def load_members() -> Members:
    """Read up to 5 member headwords per root/family unit, read-only from dpd.db."""
    session = get_db_session(ProjectPaths().dpd_db_path)
    grouped: dict[tuple[str, str], list[tuple[str, str]]] = {}
    try:
        query = session.query(
            DpdHeadword.lemma_1,
            DpdHeadword.pos,
            DpdHeadword.meaning_1,
            DpdHeadword.root_key,
            DpdHeadword.family_word,
        )
        for r in query:
            if not r.meaning_1:
                continue
            if r.root_key:
                key = ("root", r.root_key)
            elif r.family_word:
                key = ("family", r.family_word)
            else:
                continue
            grouped.setdefault(key, []).append(
                (r.lemma_1 or "", f"{r.lemma_1} ({r.pos}) {r.meaning_1}")
            )
    finally:
        session.close()
    return {
        key: [text for _, text in sorted(items, key=lambda t: (len(t[0]), t[0]))][
            :MAX_MEMBERS
        ]
        for key, items in grouped.items()
    }


def read_units(path: Path) -> set[str]:
    """Read unit keys, one per line, stripped; empty lines are ignored."""
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line}


def _peak_gate(batches_run: int, allow_peak: bool) -> bool:
    """Return True to run the next batch; the first batch may exit 1, a later one stops cleanly."""
    if batches_run == 0:
        require_offpeak(allow_peak)
        return True
    try:
        require_offpeak(allow_peak)
    except SystemExit:
        pr.amber("peak hours started — stopping")
        return False
    return True


def run_batches(
    mode: str,
    ledger: Path,
    ask: Ask,
    members: Members,
    batch_size: int,
    max_batches: int,
    allow_peak: bool,
    passes: int = 1,
    units: set[str] | None = None,
) -> int:
    """Run propose or verify batches until done or capped; return the exit code."""
    wanted = "pending" if mode == "propose" else "proposed"
    rows = read_ledger(ledger)
    if units is not None:
        unknown = units - {r["unit_key"] for r in rows}
        if unknown:
            pr.red(f"unknown units: {', '.join(sorted(unknown))}")
            return 1
        skipped = {
            r["unit_key"]
            for r in rows
            if r["unit_key"] in units and r["status"] != wanted
        }
        if skipped:
            pr.amber(f"not {wanted}, skipped: {', '.join(sorted(skipped))}")
        if not any(r["unit_key"] in units and r["status"] == wanted for r in rows):
            pr.amber("nothing to do")
            return 0
    attempted: set[str] = set()
    batches = 0
    total_changed = 0
    total_problems = 0
    exit_code = 0
    while max_batches <= 0 or batches < max_batches:
        batch = [
            r
            for r in rows
            if r["status"] == wanted
            and r["unit_key"] not in attempted
            and (units is None or r["unit_key"] in units)
        ][:batch_size]
        if not batch:
            break
        if not _peak_gate(batches, allow_peak):
            break
        attempted.update(r["unit_key"] for r in batch)
        if mode == "propose":
            prompt, system = build_propose_prompt(batch, members), PROPOSE_SYSTEM
        else:
            prompt, system = build_verify_prompt(batch, members), VERIFY_SYSTEM
        pr.green(f"{mode} batch {batches + 1}: {len(batch)} units")
        two_pass = mode == "verify" and passes == 2
        contents = [ask(prompt, system, mode == "verify")]
        if two_pass and contents[0] is not None:
            contents.append(ask(prompt, system, True))
        if any(c is None for c in contents):
            pr.red("no content from the AI — stopping")
            exit_code = 2
            break
        batches += 1
        parsed = [parse_response(c) for c in contents if c is not None]
        bad = [n for n, items in enumerate(parsed, 1) if items is None]
        if bad:
            where = f" (pass {bad[0]})" if two_pass else ""
            pr.red(f"unparseable response{where}, {len(batch)} rows unchanged")
            total_problems += len(batch)
            continue
        if two_pass:
            changed, problems = apply_verify_pair(
                batch, parsed[0] or [], parsed[1] or []
            )
        else:
            apply = apply_propose if mode == "propose" else apply_verify
            changed, problems = apply(batch, parsed[0] or [])
        for problem in problems:
            pr.amber(problem)
        total_changed += changed
        total_problems += len(problems)
        write_ledger(ledger, rows)
    pr.summary("batches", batches)
    pr.summary("rows changed", total_changed)
    pr.summary("problems", total_problems)
    pr.summary(f"still {wanted}", sum(r["status"] == wanted for r in rows))
    return exit_code


def check_grounded_chain(models: Sequence[tuple[object, ...]]) -> None:
    """Exit with a red message unless the grounded chain is non-empty and all DeepSeek."""
    if not models:
        pr.red("grounded model chain is empty — verify needs DeepSeek")
        raise SystemExit(1)
    for model in models:
        if model[0] != "deepseek":
            pr.red(
                f"grounded chain has non-deepseek provider {model[0]!r} — "
                "verify thinking options are DeepSeek-specific"
            )
            raise SystemExit(1)


def make_ask(manager: AIManager | None = None, thinking: bool = True) -> Ask:
    """Build the AI caller: default chain for propose; for verify the grounded
    (DeepSeek) chain with thinking enabled and a raised max_tokens, or with
    thinking disabled and the provider's default max_tokens."""
    manager = manager or AIManager()

    def ask(prompt: str, system: str, grounding: bool) -> str | None:
        if grounding:
            check_grounded_chain(manager.GROUNDED_MODELS)
            if not thinking:
                return manager.request(
                    prompt=prompt,
                    prompt_sys=system,
                    grounding=True,
                    thinking=copy.deepcopy(VERIFY_NO_THINKING),
                ).content
            return manager.request(
                prompt=prompt,
                prompt_sys=system,
                grounding=True,
                thinking=copy.deepcopy(VERIFY_REQUEST_OPTIONS["thinking"]),
                max_tokens=VERIFY_REQUEST_OPTIONS["max_tokens"],
            ).content
        return manager.request(
            prompt=prompt, prompt_sys=system, grounding=False
        ).content

    return ask


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["propose", "verify"])
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument(
        "--max-batches", type=int, default=0, help="0 = run until none are left"
    )
    parser.add_argument(
        "--allow-peak", action="store_true", help="run during DeepSeek peak hours"
    )
    parser.add_argument(
        "--no-thinking", action="store_true", help="verify with thinking disabled"
    )
    parser.add_argument(
        "--passes",
        type=int,
        choices=[1, 2],
        default=1,
        help="verify passes; 2 keeps only words both passes keep",
    )
    parser.add_argument(
        "--units-file",
        type=Path,
        default=None,
        help="only these unit_keys, one per line",
    )
    args = parser.parse_args()
    if args.mode == "propose" and (args.no_thinking or args.passes == 2):
        parser.error("--no-thinking and --passes 2 apply to verify only")
    require_offpeak(args.allow_peak)
    members = load_members()
    sys.exit(
        run_batches(
            args.mode,
            LEDGER_PATH,
            make_ask(thinking=not args.no_thinking),
            members,
            args.batch_size,
            args.max_batches,
            args.allow_peak,
            args.passes,
            read_units(args.units_file) if args.units_file else None,
        )
    )


if __name__ == "__main__":
    main()
