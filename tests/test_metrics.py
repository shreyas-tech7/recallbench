import pytest

from recallbench.bench import aggregate, run, score, wilson
from recallbench.questions import Question


def test_wilson_matches_known_values():
    r = wilson(5, 10)
    assert r["rate"] == 0.5
    assert r["lo"] == pytest.approx(0.2366, abs=1e-4) and r["hi"] == pytest.approx(0.7634, abs=1e-4)
    assert wilson(0, 0)["n"] == 0
    assert wilson(10, 10)["hi"] == 1.0


def test_score_flags_stale_and_forget():
    """Broken case: an old value returned after an update must count as stale, not just wrong."""
    q = Question("q", "p", "updated", "Which city do I live in?", "2025-09-01", "Boise", old_values=["Omaha"])
    r = score(q, ["[2025-01-01] I live in Omaha."])
    assert not r["correct"] and r["stale"]
    f = Question(
        "f", "p", "forgotten", "What is my hobby?", "2025-09-01", "unknown", deleted_values=["chess"]
    )
    r = score(f, ["[2025-01-01] My hobby is chess.", "[2025-02-01] Forget my hobby, please."])
    assert r["correct"] and r["forget_violation"] and not r["forget_answer_leak"]


def test_aggregate_and_run_shape():
    res = run(2, sweep=False, n_personas=3)
    for s in res["strategies"].values():
        assert set(s["by_type"]) == {
            "single",
            "updated",
            "multi_session",
            "temporal",
            "abstention",
            "forgotten",
        }
        for key in ("stale_rate", "forget_violations", "forget_answer_leaks", "overall"):
            assert s[key]["lo"] <= s[key]["rate"] <= s[key]["hi"]
        assert s["tokens_per_answer"]["mean"] > 0
    assert res["strategies"]["profile_store"]["forget_violations"]["k"] == 0
    assert (
        aggregate(
            [
                {
                    "qtype": "single",
                    "correct": True,
                    "stale": False,
                    "forget_violation": False,
                    "forget_answer_leak": False,
                    "tokens": 3,
                }
            ]
        )["overall"]["k"]
        == 1
    )
