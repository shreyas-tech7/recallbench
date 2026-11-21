"""Five memory strategies. Each one ingests sessions in order, then returns memory lines
for a question. Every strategy gets the same token budget for what it returns.

A memory line is `[YYYY-MM-DD] text`. Strategies return lines in date order.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from collections.abc import Callable

import numpy as np

from .generator import Session
from .reader import PATTERNS

TOKEN = re.compile(r"\w+|[^\w\s]")
STOP = set(
    "a an the i my me is are was to of in on for and or do what which where when did you your it at".split()
)


def count_tokens(text: str) -> int:
    """Approximate tokens: words and punctuation marks. Close to a BPE count for plain English."""
    return len(TOKEN.findall(text))


def pick(items: list[tuple[str, int, str]], budget: int) -> list[tuple[str, int, str]]:
    """Take items in the given priority order while they fit the budget."""
    out, used = [], 0
    for item in items:
        n = count_tokens(f"[{item[0]}] {item[2]}")
        if used + n <= budget:
            out.append(item)
            used += n
    return out


def fit(items: list[tuple[str, int, str]], budget: int) -> list[str]:
    """Pick items that fit the budget. Return them as lines in date order."""
    return [f"[{d}] {t}" for d, _, t in sorted(pick(items, budget))]


def extract(text: str) -> tuple[str, str, str | None] | None:
    """The rule extractor shared with the reader: (slot, op, value) or None."""
    for slot, pats in PATTERNS.items():
        for op, pat in pats:
            if m := pat.search(text):
                return slot, op, (None if op == "delete" else m.group(1))
    return None


class Strategy:
    name = "base"

    def __init__(self, budget: int):
        self.budget = budget
        self.seq = 0

    def ingest(self, session: Session) -> None:
        raise NotImplementedError

    def retrieve(self, question: str, qdate: str) -> list[str]:
        raise NotImplementedError

    def dump(self) -> str:
        """Everything the strategy stores, as text. Used by the leak test."""
        raise NotImplementedError

    def _next(self) -> int:
        self.seq += 1
        return self.seq


class FullContext(Strategy):
    """Keep the whole transcript. Return the newest turns that fit the budget."""

    name = "full_context"

    def __init__(self, budget: int):
        super().__init__(budget)
        self.items: list[tuple[str, int, str]] = []

    def ingest(self, session):
        for t in session.turns:
            self.items.append((session.date, self._next(), f"{t.role}: {t.text}"))

    def retrieve(self, question, qdate):
        return fit(list(reversed(self.items)), self.budget)

    def dump(self):
        return "\n".join(t for _, _, t in self.items)


FACT_WORDS = re.compile(
    r"\b(work|job|live|moved|dog|cat|pet|favorite|hobby|trip|address|car|drive|bought|forget|delete)\b", re.I
)


def scripted_summarizer(
    summary: list[tuple[str, int, str]], session: Session, seq
) -> list[tuple[str, int, str]]:
    """Keep user lines that contain a fact word. Drop small talk. No rewriting, no merging."""
    keep = [
        (session.date, seq(), t.text) for t in session.turns if t.role == "user" and FACT_WORDS.search(t.text)
    ]
    return summary + keep


class RollingSummary(Strategy):
    """After each session, fold it into a summary. When the summary passes the budget,
    drop its oldest lines."""

    name = "rolling_summary"

    def __init__(self, budget: int, summarizer: Callable = scripted_summarizer):
        super().__init__(budget)
        self.summary: list[tuple[str, int, str]] = []
        self.summarizer = summarizer

    def ingest(self, session):
        self.summary = self.summarizer(self.summary, session, self._next)
        while sum(count_tokens(f"[{d}] {t}") for d, _, t in self.summary) > self.budget:
            self.summary.pop(0)

    def retrieve(self, question, qdate):
        return fit(self.summary, self.budget)

    def dump(self):
        return "\n".join(t for _, _, t in self.summary)


class HashEmbedder:
    """Offline embedder for tests and the default run: signed feature hashing of words
    and character trigrams. Deterministic, no download."""

    name = "hash-512"

    def __init__(self, dim: int = 512):
        self.dim = dim

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim)
        words = [w for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in STOP]
        feats = words + [w[i : i + 3] for w in words for i in range(max(1, len(w) - 2))]
        for f in feats:
            h = int.from_bytes(hashlib.blake2b(f.encode(), digest_size=8).digest(), "little")
            v[h % self.dim] += 1 if (h >> 32) & 1 else -1
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array([self._vec(t) for t in texts]) if texts else np.zeros((0, self.dim))


class FastEmbedder:
    """Small dense model through FastEmbed. Needs the model download to work."""

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding  # optional dependency

        self.name = model
        self.model = TextEmbedding(model)

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array(list(self.model.embed(texts))) if texts else np.zeros((0, 384))


class VectorRecall(Strategy):
    """Index each user turn as a chunk. Return the top k chunks by cosine similarity."""

    name = "vector_recall"

    def __init__(self, budget: int, embedder=None, k: int = 10):
        super().__init__(budget)
        self.embedder = embedder or HashEmbedder()
        self.k = k
        self.chunks: list[tuple[str, int, str]] = []
        self.vecs: list[np.ndarray] = []

    def ingest(self, session):
        new = [(session.date, self._next(), t.text) for t in session.turns if t.role == "user"]
        if new:
            self.chunks += new
            self.vecs += list(self.embedder.embed([t for _, _, t in new]))

    def search(self, question: str) -> list[tuple[str, int, str]]:
        if not self.chunks:
            return []
        q = self.embedder.embed([question])[0]
        scores = np.array(self.vecs) @ q
        order = np.argsort(-scores, kind="stable")[: self.k]
        return [self.chunks[i] for i in order]

    def retrieve(self, question, qdate):
        return fit(self.search(question), self.budget)

    def drop(self, values: list[str]) -> None:
        """Remove every chunk that names one of the values."""
        pats = [re.compile(rf"\b{re.escape(v)}\b") for v in values]
        keep = [i for i, (_, _, t) in enumerate(self.chunks) if not any(p.search(t) for p in pats)]
        self.chunks = [self.chunks[i] for i in keep]
        self.vecs = [self.vecs[i] for i in keep]

    def dump(self):
        return "\n".join(t for _, _, t in self.chunks)


CANON = {
    "job": "I work as {a} {v}.",
    "city": "I live in {v}.",
    "pet": "I have a dog named {v}.",
    "food": "My favorite food is {v}.",
    "hobby": "My hobby is {v}.",
    "trip": "I'm planning a trip to {v}.",
    "address": "My address is {v}.",
    "car": "I drive {a} {v}.",
}


class ProfileStore(Strategy):
    """Key-value facts in SQLite. A new value supersedes the old one. A forget request
    deletes every row for that slot, history included."""

    name = "profile_store"

    def __init__(self, budget: int):
        super().__init__(budget)
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE facts (slot TEXT, value TEXT, since TEXT, seq INT, active INT)")

    def ingest(self, session):
        for t in session.turns:
            if t.role == "user" and (f := extract(t.text)):
                self.apply(session.date, *f)

    def apply(self, day: str, slot: str, op: str, value: str | None) -> list[str]:
        """Apply one fact. Return the values removed by a delete."""
        if op == "delete":
            gone = [r[0] for r in self.db.execute("SELECT value FROM facts WHERE slot=?", (slot,))]
            self.db.execute("DELETE FROM facts WHERE slot=?", (slot,))
            return gone
        row = self.db.execute("SELECT value FROM facts WHERE slot=? AND active=1", (slot,)).fetchone()
        if row and row[0] == value:
            return []  # a passing mention of the current value
        self.db.execute("UPDATE facts SET active=0 WHERE slot=?", (slot,))
        self.db.execute("INSERT INTO facts VALUES (?,?,?,?,1)", (slot, value, day, self._next()))
        return []

    def lines(self) -> list[tuple[str, int, str]]:
        rows = self.db.execute(
            "SELECT slot, value, since, seq FROM facts WHERE active=1 ORDER BY since DESC, seq DESC"
        )
        art = lambda v: "an" if v[0].lower() in "aeiou" else "a"  # noqa: E731
        return [(d, s, CANON[slot].format(v=v, a=art(v))) for slot, v, d, s in rows]

    def retrieve(self, question, qdate):
        return fit(self.lines(), self.budget)

    def dump(self):
        return "\n".join(" ".join(map(str, r)) for r in self.db.execute("SELECT * FROM facts"))


class Hybrid(Strategy):
    """The profile store first, then vector chunks in the budget that is left. A forget
    request also removes the matching chunks from the vector index."""

    name = "hybrid"

    def __init__(self, budget: int, embedder=None, k: int = 10):
        super().__init__(budget)
        self.profile = ProfileStore(budget)
        self.vector = VectorRecall(budget, embedder, k)

    def ingest(self, session):
        self.vector.ingest(session)
        for t in session.turns:
            if t.role == "user" and (f := extract(t.text)):
                if gone := self.profile.apply(session.date, *f):
                    self.vector.drop(gone)

    def retrieve(self, question, qdate):
        prof = pick(self.profile.lines(), self.budget)
        used = sum(count_tokens(f"[{d}] {t}") for d, _, t in prof)
        vec = pick(self.vector.search(question), self.budget - used)
        # On the same date, the store's line goes after the raw chunks, because it is the latest word.
        both = [(d, 0, s, t) for d, s, t in vec] + [(d, 1, s, t) for d, s, t in prof]
        return [f"[{d}] {t}" for d, _, _, t in sorted(both)]

    def dump(self):
        return self.profile.dump() + "\n" + self.vector.dump()


NAMES = ["full_context", "rolling_summary", "vector_recall", "profile_store", "hybrid"]


def make(name: str, budget: int, embedder=None) -> Strategy:
    return {
        "full_context": lambda: FullContext(budget),
        "rolling_summary": lambda: RollingSummary(budget),
        "vector_recall": lambda: VectorRecall(budget, embedder),
        "profile_store": lambda: ProfileStore(budget),
        "hybrid": lambda: Hybrid(budget, embedder),
    }[name]()
