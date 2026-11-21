"""Questions with exact answers, in six types, built from each persona's timeline.

Every question is asked the day after the persona's last session. The answer and
the scoring fields come from the event timeline, never from the chat text.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from .generator import SLOTS, Persona
from .reader import QUESTION, SLOT_WORD

TYPES = ["single", "updated", "multi_session", "temporal", "abstention", "forgotten"]
UNKNOWN = "unknown"


@dataclass
class Question:
    qid: str
    pid: str
    qtype: str
    text: str
    date: str
    answer: str
    old_values: list[str] = field(default_factory=list)  # superseded values, for the stale-fact rate
    deleted_values: list[str] = field(default_factory=list)  # values of a deleted slot

    def to_dict(self) -> dict:
        return asdict(self)


def timeline(p: Persona) -> dict[str, list]:
    """Per slot: the list of events in order."""
    out: dict[str, list] = {s: [] for s in SLOTS}
    for e in sorted(p.events, key=lambda e: e.session):
        out[e.slot].append(e)
    return out


def make_questions(p: Persona, rng: random.Random, per_type: int = 3) -> list[Question]:
    tl = timeline(p)
    qdate = (date.fromisoformat(p.sessions[-1].date) + timedelta(days=1)).isoformat()
    live = {s: ev for s, ev in tl.items() if ev and ev[-1].op != "delete"}
    qs: list[tuple[str, str, str, list, list]] = []

    def add(qtype, text, ans, old=(), deleted=()):
        qs.append((qtype, text, ans, list(old), list(deleted)))

    once = [s for s, ev in live.items() if len(ev) == 1]
    for s in rng.sample(once, min(per_type, len(once))):
        add("single", QUESTION[s] + "?", live[s][-1].value)
    upd = [s for s, ev in live.items() if len(ev) > 1]
    for s in rng.sample(upd, min(per_type, len(upd))):
        add("updated", QUESTION[s] + "?", live[s][-1].value, old=[e.value for e in live[s][:-1]])
    pairs = [(a, b) for a in live for b in live if a < b and live[a][-1].session != live[b][-1].session]
    for a, b in rng.sample(pairs, min(per_type, len(pairs))):
        text = f"{QUESTION[a]}, and {QUESTION[b][0].lower()}{QUESTION[b][1:]}?"
        add("multi_session", text, f"{live[a][-1].value} | {live[b][-1].value}")
    whens = list(live)
    for s in rng.sample(whens, min(2, len(whens))):
        e = live[s][-1]
        add("temporal", f"On what date did I first mention that my {SLOT_WORD[s]} is {e.value}?", e.date)
    if pairs:
        a, b = rng.choice(pairs)
        ea, eb = live[a][-1], live[b][-1]
        if ea.date != eb.date:
            text = f"Did I first mention my {SLOT_WORD[a]} {ea.value} before or after my {SLOT_WORD[b]} {eb.value}?"
            add("temporal", text, "before" if ea.date < eb.date else "after")
    never = [s for s, ev in tl.items() if not ev]
    for s in rng.sample(never, min(per_type, len(never))):
        add("abstention", QUESTION[s] + "?", UNKNOWN)
    gone = [s for s, ev in tl.items() if ev and ev[-1].op == "delete"]
    for s in gone:
        add("forgotten", QUESTION[s] + "?", UNKNOWN, deleted=[e.value for e in tl[s] if e.value])
    return [
        Question(f"{p.pid}-q{i:02d}", p.pid, t, text, qdate, ans, old, dele)
        for i, (t, text, ans, old, dele) in enumerate(qs)
    ]


def build(personas: list[Persona], seed: int) -> list[Question]:
    rng = random.Random(seed * 7919 + 1)  # noqa: S311 (seeded synthetic data, not crypto)
    out = []
    for p in personas:
        out += make_questions(p, rng)
    return out
