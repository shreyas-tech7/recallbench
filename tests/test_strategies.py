import re

import pytest

from recallbench.bench import run_strategy
from recallbench.generator import Session, generate
from recallbench.questions import build
from recallbench.strategies import NAMES, ProfileStore, VectorRecall, count_tokens, make


def _named(values, lines):
    text = "\n".join(lines)
    return any(re.search(rf"\b{re.escape(v)}\b", text) for v in values)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_profile_store_never_returns_a_deleted_fact(seed):
    """Done-means item 4. Broken case: a delete that only marks the row inactive keeps the old value."""
    personas = generate(seed)
    qs = build(personas, seed)
    deleted = {}
    for p in personas:
        deleted[p.pid] = [
            e.value
            for s in {e.slot for e in p.events if e.op == "delete"}
            for e in p.events
            if e.slot == s and e.value
        ]
    for p in personas:
        store = ProfileStore(512)
        for s in p.sessions:
            store.ingest(s)
        assert deleted[p.pid]
        assert not _named(deleted[p.pid], [store.dump()])  # not even in the stored history
        for q in (q for q in qs if q.pid == p.pid):
            assert not _named(deleted[p.pid], store.retrieve(q.text, q.date))


def test_vector_recall_keeps_deleted_facts():
    """The benchmark must be able to see a violation: plain vector memory never forgets."""
    p = generate(1, 3)[0]
    gone = [
        e.value
        for e in p.events
        if e.op != "delete" and any(d.slot == e.slot and d.op == "delete" for d in p.events)
    ]
    v = VectorRecall(512)
    for s in p.sessions:
        v.ingest(s)
    assert _named(gone, [v.dump()])


def test_broken_profile_store_is_caught():
    """Shows the forget test fails on the broken case: soft delete leaves the value in the store."""

    class SoftDelete(ProfileStore):
        def apply(self, day, slot, op, value):
            if op == "delete":
                self.db.execute("UPDATE facts SET active=0 WHERE slot=?", (slot,))
                return []
            return super().apply(day, slot, op, value)

    p = generate(1, 1)[0]
    s = SoftDelete(512)
    for sess in p.sessions:
        s.ingest(sess)
    gone = [
        e.value for e in p.events if e.value and any(d.slot == e.slot and d.op == "delete" for d in p.events)
    ]
    assert _named(gone, [s.dump()])


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("budget", [64, 256])
def test_every_strategy_keeps_to_the_budget(name, budget):
    p = generate(2, 2)[1]
    strat = make(name, budget)
    for s in p.sessions:
        strat.ingest(s)
    for q in build([p], 2):
        assert count_tokens("\n".join(strat.retrieve(q.text, q.date))) <= budget


@pytest.mark.parametrize("name", NAMES)
def test_strategies_never_see_questions_during_ingestion(name):
    """Broken case: question text leaks into memory before the question is asked."""
    personas = generate(1, 4)
    qs = build(personas, 1)
    for p in personas:
        strat = make(name, 512)
        seen = []
        real = strat.ingest

        def spy(session, real=real, seen=seen):
            seen.append(type(session))
            return real(session)

        strat.ingest = spy
        for s in p.sessions:
            strat.ingest(s)
        assert set(seen) == {Session}
        stored = strat.dump()
        for q in qs:
            assert q.text not in stored
            assert q.text.rstrip("?") not in stored


def test_hybrid_drops_deleted_values_from_its_index():
    p = generate(1, 2)[0]
    h = make("hybrid", 512)
    for s in p.sessions:
        h.ingest(s)
    gone = [
        e.value for e in p.events if e.value and any(d.slot == e.slot and d.op == "delete" for d in p.events)
    ]
    assert not _named(gone, [h.vector.dump(), h.profile.dump()])


def test_runner_scores_every_question():
    personas = generate(1, 3)
    qs = build(personas, 1)
    rows = run_strategy("full_context", personas, qs, 512)
    assert len(rows) == len(qs)
