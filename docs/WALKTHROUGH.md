# Walkthrough

A tour of every file, in plain words. One idea per sentence.

## The big picture

The generator invents users and their chats. Each memory strategy reads the chats. Then it answers questions through the same reader. The scorer checks each answer against the truth. A script writes the tables.

## Source code (`src/recallbench/`)

- `generator.py` makes the fake users. Each user gets 10 to 30 chat sessions. Facts arrive, change and get deleted. Small talk and lines about other people fill the gaps. The seed makes it repeatable.
- `questions.py` turns each user's fact history into questions. There are six kinds. Each question has one exact answer. The answer comes from the fact history, not from the chat text.
- `reader.py` is the deterministic reader. It reads dated memory lines. It finds first-person facts with patterns. It replays them in date order. A forget request clears a fact. Then it answers.
- `strategies.py` holds the five memory strategies. All share one token budget. It also holds the token counter, the hash embedder and the FastEmbed wrapper.
- `bench.py` runs every strategy on every user. It scores each answer. It adds up the scores with 95% intervals. It also runs the budget sweep.
- `readme.py` writes the number blocks in the README and docs. It also writes `docs/index.html`. With `--check`, it only reports stale blocks.
- `llm.py` talks to a free LLM provider for record mode. It reads the key from the environment. It retries on rate limits.
- `record.py` runs the LLM summarizer and the LLM reader on three users.
- `cli.py` is the `recallbench` command. It has six subcommands: generate, truth, run, demo, record and readme.

## Tests (`tests/`)

- `conftest.py` blocks every network call that leaves the machine.
- `test_network_guard.py` proves that block works.
- `test_generator.py` checks the shape of the fake data.
- `test_truth.py` replays every chat and checks every answer. This proves the answer keys.
- `test_reader.py` checks the reader on small hand-made cases.
- `test_strategies.py` checks the budget, the forget rule and the leak rule.
- `test_metrics.py` checks the intervals and the stale and forget flags.
- `test_llm.py` runs record mode against a fake server on this machine.
- `test_cli.py` runs each command.
- `test_repo.py` checks the README order, the generated numbers, the writing rules and the shipped files.

## Results and docs

- `results/final-seed4049.json` holds the headline numbers.
- `results/second-seed90210.json` is the rerun on a second fresh seed.
- `results/tune-seed1.json` is the seed used while building.
- `results/record-status.json` says why record mode did not run.
- `docs/DECISION_GUIDE.md` helps a team pick a strategy.
- `docs/INTERVIEW_QA.md` answers likely questions about the design.
- `docs/index.html` shows the tables as a page.
- `docs/DEMO.md` is a real terminal run.
- `docs/HUMAN_STEPS.md` lists what only Shreyas can do.
- `docs/handoff/COWORK_PROMPT.md` is a prompt for the browser steps.
- `docs/build/BUILD_PROMPT.md` is the brief this repo was built from.
- `examples/` holds two users and their questions as JSONL.

## Project files

- `init.sh` sets up and checks everything in one command.
- `feature_list.json` lists each feature and whether it passes.
- `PROGRESS.md`, `BLOCKERS.md` and `DECISIONS.md` are the build's memory.
- `scripts/check_links.py` checks every link in the docs.
- `scripts/make_social_preview.py` draws the social preview image.
- `.github/workflows/ci.yml` runs the checks on every push.
- `.github/workflows/bench.yml` runs the benchmark by hand.
