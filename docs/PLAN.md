# Plan

The brief in docs/build/BUILD_PROMPT.md is the spec. No question rounds. Assumptions are in DECISIONS.md.

## Goal
Compare five memory strategies on synthetic multi-session chats. Score six question types, stale facts, forget violations and tokens per answer under one token budget.

## Tasks, in build order
1. Initializer: init.sh, memory files, CLAUDE.md, PROJECT_CONTEXT.md, LICENSE, secret scan. Test: `./init.sh` passes.
2. Generator (`generator.py`): seeded personas, 10 to 30 sessions, set, update, delete, passing mentions, distractors. Tests: shape, valid timelines, unique values.
3. Questions (`questions.py`) and the ground truth test. Test: the reader on the full transcript answers every question exactly, seeds 1 to 3.
4. Deterministic reader (`reader.py`). Tests: date order, forget, distractors, temporal and multi questions.
5. Full context and profile store. Tests: budget, profile store never returns a deleted value, a soft delete fails the same test.
6. Vector recall with the hash embedder, then FastEmbed. Test: vector recall keeps deleted values (so violations show).
7. Rolling summary (scripted) and the hybrid. Test: the hybrid removes deleted values from its index.
8. Metrics and report (`bench.py`, `readme.py`). Tests: Wilson values, stale and forget flags, README blocks match the results.
9. Final run on seed 4049, second run on seed 90210. (Seeds 2027 and 31337 ran first and were retired after the code review changed the strategies. See DECISIONS.md.)
10. Record mode, or the README says it could not run.
11. README, decision guide, study-later kit, release check, hand-off.

## Assumptions
- Questions are asked the day after the last session.
- A deletion is permanent. No fact is stated again after its delete.
- The reader shares its patterns with the profile store extractor.
