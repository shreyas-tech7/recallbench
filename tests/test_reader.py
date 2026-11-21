from recallbench.reader import answer, replay


def L(*pairs):
    return [f"[{d}] {t}" for d, t in pairs]


def test_latest_statement_wins_in_date_order():
    lines = L(("2025-03-01", "We moved to Boise."), ("2025-01-01", "I live in Omaha."))
    assert answer("Which city do I live in?", lines) == "Boise"


def test_forget_clears_the_slot():
    lines = L(("2025-01-01", "I live in Omaha."), ("2025-02-01", "Please forget where I live."))
    assert answer("Which city do I live in?", lines) == "unknown"


def test_forget_with_trailing_please_is_not_a_value():
    """Broken case: 'Forget my hobby, please.' read as a hobby named 'please'."""
    lines = L(("2025-01-01", "My hobby is chess."), ("2025-02-01", "Forget my hobby, please."))
    assert answer("What is my hobby?", lines) == "unknown"


def test_other_people_are_ignored():
    """Broken case: 'My sister lives in Austin' taken as the user's city."""
    lines = L(
        ("2025-01-01", "My sister lives in Austin."),
        ("2025-01-02", "My brother works as a pilot."),
        ("2025-01-03", "My roommate's favorite food is pho."),
        ("2025-01-04", "My aunt's address is 11 Maple Street."),
    )
    for q in [
        "Which city do I live in?",
        "What do I do for work?",
        "What is my favorite food?",
        "What is my address?",
    ]:
        assert answer(q, lines) == "unknown"


def test_articles_and_passing_mentions():
    lines = L(
        ("2025-01-01", "user: I work as an architect."), ("2025-01-05", "The Outback needed new tires today.")
    )
    current, first = replay(lines)
    assert current["job"] == "architect" and current["car"] == "Outback"
    assert first[("job", "architect")] == "2025-01-01"


def test_temporal_and_multi_questions():
    lines = L(
        ("2025-01-01", "I live in Omaha."),
        ("2025-01-09", "My favorite food is ramen."),
        ("2025-02-01", "My address is 21 Cedar Street."),
    )
    assert answer("On what date did I first mention that my favorite food is ramen?", lines) == "2025-01-09"
    assert (
        answer("Did I first mention my city Omaha before or after my address 21 Cedar Street?", lines)
        == "before"
    )
    assert (
        answer("Did I first mention my address 21 Cedar Street before or after my city Omaha?", lines)
        == "after"
    )
    assert answer("Which city do I live in, and what is my favorite food?", lines) == "Omaha | ramen"
    assert answer("What car do I drive?", lines) == "unknown"
