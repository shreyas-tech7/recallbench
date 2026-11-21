# Project context: recallbench

## What it is
A benchmark for agent memory. It generates synthetic users whose facts arrive, change and get deleted over many chat sessions. It feeds the sessions to five memory strategies, asks six kinds of questions, and scores accuracy, stale facts, forget violations and tokens per answer.

## Status
v0.1.0-rc1 build. Offline numbers done. Dense embeddings and record mode are blocked on this machine (see BLOCKERS.md).

## Stack
Python 3.11+, numpy, sqlite3, pytest, ruff. FastEmbed is an optional extra (`.[dense]`).

## Commands
- `./init.sh`: venv, install, lint, link check, all tests offline.
- `recallbench truth --seed 1`: replay every transcript and check every answer.
- `recallbench run --seed N --out results/x.json`: the benchmark.
- `recallbench demo`: small run on 3 personas.
- `recallbench readme [--check]`: rewrite or check the generated number blocks.
- `recallbench record --provider groq`: record mode, needs a key.

## Layout
- `src/recallbench/generator.py`: personas, timelines, sessions.
- `src/recallbench/questions.py`: six question types with answers.
- `src/recallbench/reader.py`: deterministic reader and its patterns.
- `src/recallbench/strategies.py`: the five strategies, embedders, token counter.
- `src/recallbench/bench.py`: runner, metrics, Wilson intervals.
- `src/recallbench/readme.py`: generated blocks and `docs/index.html`.
- `src/recallbench/llm.py`, `record.py`: record mode.
- `results/`: JSON result files. `docs/`: guide, walkthrough, QA, demo page.

## Rules
- Seed 1 is the tuning seed. Tests use seeds 1 to 3. Final seed 2027, second seed 31337.
- No typed numbers in README, DECISION_GUIDE or INTERVIEW_QA. Edit prose outside the `gen` blocks only.
- Tests run offline. `tests/conftest.py` blocks network.
- No em dashes, no dash punctuation, no semicolons in prose (a test checks).

## Skills that fit
superpowers: test-driven-development, systematic-debugging, verification-before-completion, requesting-code-review.

## Do not read
`.venv/`, `logs/`, `docs/build/BUILD_PROMPT.md` unless resuming the brief.
