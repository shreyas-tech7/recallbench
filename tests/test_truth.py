import pytest

from recallbench.bench import ground_truth_check
from recallbench.generator import generate
from recallbench.questions import build


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_replay_answers_every_question_exactly(seed):
    """Broken case: a question whose answer the chat text does not support. Done-means item 2."""
    n = len(build(generate(seed), seed))
    assert n > 200
    assert ground_truth_check(seed) == []
