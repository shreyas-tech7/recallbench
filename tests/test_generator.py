import re
from collections import Counter

from recallbench.generator import DISTRACT, SLOTS, generate
from recallbench.questions import TYPES, build, timeline


def test_same_seed_same_data():
    assert [p.to_dict() for p in generate(3, 4)] == [p.to_dict() for p in generate(3, 4)]
    assert generate(3, 2)[0].to_dict() != generate(4, 2)[0].to_dict()


def test_shape_matches_the_brief():
    ps = generate(1)
    assert len(ps) == 20
    for p in ps:
        assert 10 <= len(p.sessions) <= 30
        dates = [s.date for s in p.sessions]
        assert dates == sorted(dates) and len(set(dates)) == len(dates)
        ops = Counter(e.op for e in p.events)
        assert ops["set"] >= 5 and ops["update"] >= 2 and ops["delete"] >= 1


def test_every_slot_timeline_is_valid():
    """Broken case: an update or delete before the first set, or a fact after a delete."""
    for p in generate(2):
        for slot, events in timeline(p).items():
            if not events:
                continue
            assert events[0].op == "set"
            assert all(e.op != "set" for e in events[1:])
            assert all(e.op != "delete" for e in events[:-1])
            assert slot in SLOTS


def test_values_are_unique_within_a_persona():
    """Broken case: a deleted city that also shows up as the sister's city would count as a leak."""
    for p in generate(1):
        values = [e.value for e in p.events if e.value]
        assert len(values) == len(set(values))
        text = " ".join(t.text for s in p.sessions for t in s.turns)
        distract_vals = [w for w in text.split() if w.strip(".,") in values]
        assert distract_vals  # facts are in the text


def test_distractors_and_small_talk_are_present():
    ps = generate(1)
    text = " ".join(t.text for p in ps for s in p.sessions for t in s.turns)
    assert "My sister lives in" in text or "My cousin moved to" in text
    assert sum(text.count(t.split("{")[0]) for v in DISTRACT.values() for t in v) > 20


def test_all_six_question_types():
    qs = build(generate(1), 1)
    counts = Counter(q.qtype for q in qs)
    assert set(counts) == set(TYPES)
    assert all(n >= 20 for n in counts.values()), counts


def test_temporal_questions_name_no_value():
    """Broken case: a temporal question that holds the value gives retrieval a word to match on."""
    from recallbench.questions import build

    personas = generate(1, 5)
    values = {e.value for p in personas for e in p.events if e.value}
    temporal = [q for q in build(personas, 1) if q.qtype == "temporal"]
    assert temporal
    for q in temporal:
        assert not any(re.search(rf"\b{re.escape(v)}\b", q.text) for v in values), q.text
