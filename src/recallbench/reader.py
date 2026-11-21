"""The deterministic reader: answer a question from the memory lines a strategy returns.

How it finds an answer:

1. Each memory line looks like `[2025-03-04] some text`. The reader sorts the lines
   by date. Lines from the same date keep the order the strategy gave.
2. It runs hand-written patterns over each line. A pattern matches a first-person
   statement about one slot ("I live in Denver", "We moved to Boise") or a request
   to forget it ("Please forget where I live"). Statements about other people
   ("My sister lives in Austin") match nothing.
3. It replays the matches in date order. A statement makes that value current. A
   later statement replaces it. A forget request clears the slot.
4. It parses the question text with patterns of its own and reads the answer off
   the replayed state. No current value means "unknown".

The reader never sees the ground truth. It sees only the question text and the lines.
Because the patterns were written against the generator's phrasing, the reader is
exact on any line it gets. So a wrong answer means the strategy returned the wrong
lines, not that the reader misread them.
"""

from __future__ import annotations

import re

V = r"([A-Z][\w-]*|[a-z]+)"  # one word value
ADDR = r"(\d+ [A-Z]\w+ Street)"
PATTERNS: dict[str, list[tuple[str, re.Pattern]]] = {
    "job": [
        ("set", rf"\bI (?:work as an?|just started a job as an?) {V}"),
        ("set", rf"\b[Ff]or work I'm an? {V}"),
        ("set", rf"\bbeing an? {V} is tiring"),
        ("delete", r"\b[Ff]orget (?:what my job is|my job)\b"),
    ],
    "city": [
        ("set", rf"\bI live in {V}"),
        ("set", rf"\b(?:We|I) moved to {V}"),
        ("set", rf"\bThe weather in {V} was lovely"),
        ("delete", r"\b[Ff]orget (?:where I live|my city)\b"),
    ],
    "pet": [
        ("set", rf"\b(?:I have a dog named|[Mm]y cat is called|We adopted a new dog named) {V}"),
        ("set", rf"^{V} chewed my shoe"),
        ("delete", r"\b[Ff]orget my pet's name\b"),
    ],
    "food": [
        ("set", rf"(?:^|[^'\w])[Mm]y favorite food is {V}"),
        ("set", rf"\bMade {V} for dinner, still the best"),
        ("delete", r"\b[Ff]orget my favorite food\b"),
    ],
    "hobby": [
        ("set", rf"(?:^|[^'\w])[Mm]y hobby(?: is|,) {V}"),
        ("set", rf"\bNew hobby: {V}"),
        ("set", rf"\bSpent the evening on {V}, very relaxing"),
        ("delete", r"\b[Ff]orget my hobby\b"),
    ],
    "trip": [
        ("set", rf"\bI'm planning a trip to {V}"),
        ("set", rf"\bBought a guidebook for {V}"),
        ("delete", r"\b[Ff]orget my trip plans\b"),
    ],
    "address": [
        ("set", rf"(?:^|[^'\w])[Mm]y address(?: is|,) {ADDR}"),
        ("set", rf"\bI have a new address, {ADDR}"),
        ("set", rf"\bA package came to {ADDR}"),
        ("delete", r"\b(?:[Ff]orget|delete) my address\b"),
    ],
    "car": [
        ("set", rf"\b(?:I drive an?|[Mm]y car is an?|bought an?) {V}"),
        ("set", rf"\bThe {V} needed new tires"),
        ("delete", r"\b[Ff]orget what car I drive\b"),
    ],
}
# Forget requests are tried first: "Forget my hobby, please" must not read as a hobby named "please".
PATTERNS = {
    k: [(op, re.compile(p)) for op, p in sorted(v, key=lambda x: x[0] != "delete")]
    for k, v in PATTERNS.items()
}

QUESTION = {
    "job": "What do I do for work",
    "city": "Which city do I live in",
    "pet": "What is my pet's name",
    "food": "What is my favorite food",
    "hobby": "What is my hobby",
    "trip": "Where am I planning a trip to",
    "address": "What is my address",
    "car": "What car do I drive",
}
SLOT_WORD = {
    "job": "job",
    "city": "city",
    "pet": "pet",
    "food": "favorite food",
    "hobby": "hobby",
    "trip": "trip",
    "address": "address",
    "car": "car",
}
WORD_SLOT = {w: s for s, w in SLOT_WORD.items()}
LINE = re.compile(r"^\[(\d{4}-\d{2}-\d{2})\]\s*(?:user:\s*|assistant:\s*)?(.*)$")
WHEN = re.compile(r"^On what date did I first mention that my (.+?) is (.+)\?$")
ORDER = re.compile(
    r"^Did I first mention my (.+?) (\S+(?: \S+ Street)?) before or after my (.+?) (\S+(?: \S+ Street)?)\?$"
)


def replay(lines: list[str]) -> tuple[dict[str, str | None], dict[tuple[str, str], str]]:
    """Replay the lines in date order. Return the current value of each slot and the
    first date each (slot, value) pair was stated."""
    parsed = []
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if m:
            parsed.append((m.group(1), i, m.group(2)))
    parsed.sort()
    current: dict[str, str | None] = {}
    first: dict[tuple[str, str], str] = {}
    for day, _, text in parsed:
        for slot, pats in PATTERNS.items():
            for op, pat in pats:
                m = pat.search(text)
                if not m:
                    continue
                if op == "delete":
                    current[slot] = None
                else:
                    current[slot] = m.group(1)
                    first.setdefault((slot, m.group(1)), day)
                break
    return current, first


def answer(question: str, lines: list[str]) -> str:
    current, first = replay(lines)
    q = question.strip()
    if m := WHEN.match(q):
        slot = WORD_SLOT.get(m.group(1))
        return first.get((slot, m.group(2)), "unknown") if current.get(slot) == m.group(2) else "unknown"
    if m := ORDER.match(q):
        a = first.get((WORD_SLOT.get(m.group(1)), m.group(2)))
        b = first.get((WORD_SLOT.get(m.group(3)), m.group(4)))
        if not a or not b or a == b:
            return "unknown"
        return "before" if a < b else "after"
    parts = [p.strip().rstrip("?") for p in q.split(", and ")]
    out = []
    for part in parts:
        slot = next((s for s, t in QUESTION.items() if part.lower() == t.lower()), None)
        out.append((current.get(slot) if slot else None) or "unknown")
    return " | ".join(out)
