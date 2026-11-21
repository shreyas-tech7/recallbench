# Changelog

## v0.1.0-rc1 (2026-11-21)

Release commit: recorded in the next commit, see the line below once it is filled in.

- Seeded generator of 20 synthetic personas with 10 to 30 sessions each. Facts are set, updated, deleted and mentioned in passing, with near-miss lines about other people.
- Six question types with exact answers and a test that replays every transcript and answers every question.
- Deterministic reader with documented patterns.
- Five memory strategies under one token budget: full context, rolling summary (scripted), vector recall (hash embedder), profile store (SQLite) and a hybrid that deletes from both stores.
- Metrics: accuracy per type with Wilson intervals, stale-fact rate, forget violations, deleted value given as answer, tokens per answer, and a budget sweep.
- Final numbers on seed 2027 and a second run on seed 31337. Tuning used seed 1 only.
- Record mode client for free OpenAI-compatible providers. Not run: no key on the build machine.
- FastEmbed support as the `dense` extra. Not run: the model could not download.
- README, decision guide, results page, demo transcript, walkthrough, interview QA, CI.
