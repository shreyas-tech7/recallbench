# Decision guide: which memory strategy?

This guide is for a team that adds memory to an assistant. Every number in it comes from the generated block below. The prose around it describes patterns, and you should check each one against the block.

## The numbers

<!-- gen:guide -->
| Strategy | Stale-fact rate | Forget violations, forgotten questions | Forget violations, any question | Deleted value given as answer | Tokens per answer (mean) |
| --- | --- | --- | --- | --- | --- |
| `full_context` | 0/52 = 0.0% (0.0 to 6.9) | 14/42 = 33.3% (21.0 to 48.4) | 61/265 = 23.0% (18.4 to 28.5) | 0/42 = 0.0% (0.0 to 8.4) | 514 |
| `rolling_summary` | 0/52 = 0.0% (0.0 to 6.9) | 42/42 = 100.0% (91.6 to 100.0) | 265/265 = 100.0% (98.6 to 100.0) | 0/42 = 0.0% (0.0 to 8.4) | 437 |
| `vector_recall` | 6/52 = 11.5% (5.4 to 23.0) | 41/42 = 97.6% (87.7 to 99.6) | 202/265 = 76.2% (70.7 to 81.0) | 3/42 = 7.1% (2.5 to 19.0) | 516 |
| `profile_store` | 0/52 = 0.0% (0.0 to 6.9) | 0/42 = 0.0% (0.0 to 8.4) | 0/265 = 0.0% (0.0 to 1.4) | 0/42 = 0.0% (0.0 to 8.4) | 61 |
| `hybrid` | 0/52 = 0.0% (0.0 to 6.9) | 0/42 = 0.0% (0.0 to 8.4) | 0/265 = 0.0% (0.0 to 1.4) | 0/42 = 0.0% (0.0 to 8.4) | 516 |

| Strategy | All, budget 128 | All, budget 256 | All, budget 512 | All, budget 1024 | Forget violations, budget 128 | Forget violations, budget 256 | Forget violations, budget 512 | Forget violations, budget 1024 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `full_context` | 43% (37 to 49) | 55% (49 to 61) | 75% (69 to 80) | 87% (83 to 91) | 0% (0 to 8) | 29% (17 to 44) | 33% (21 to 48) | 95% (84 to 99) |
| `rolling_summary` | 57% (51 to 62) | 79% (74 to 83) | 100% (99 to 100) | 100% (99 to 100) | 12% (5 to 25) | 86% (72 to 93) | 100% (92 to 100) | 100% (92 to 100) |
| `vector_recall` | 74% (68 to 79) | 82% (76 to 86) | 87% (82 to 90) | 94% (90 to 96) | 90% (78 to 96) | 93% (81 to 98) | 98% (88 to 100) | 100% (92 to 100) |
| `profile_store` | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 0% (0 to 8) | 0% (0 to 8) | 0% (0 to 8) | 0% (0 to 8) |
| `hybrid` | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 0% (0 to 8) | 0% (0 to 8) | 0% (0 to 8) | 0% (0 to 8) |
<!-- /gen:guide -->

## How to read them

1. **Start with forgetting.** If users can ask you to forget things, look at the forget violation column first. A strategy that keeps raw text (full context, a rolling summary that never rewrites, plain vector recall) keeps deleted values. A store that deletes by key does not. Your reader may skip a deleted value, but the value is still in the prompt, in the logs and in any cache.
2. **Then updates.** Look at the stale-fact rate. Vector recall ranks by similarity, not by date. When the newest statement uses different words from the question ("We moved to Boise" against "Which city do I live in?"), it can lose to an older line.
3. **Then cost.** Tokens per answer is what an LLM reader pays on every question. A profile store sends a few short lines. Full context sends the whole budget every time.
4. **Then the budget sweep.** Full context, the rolling summary and vector recall depend on the budget. A profile store barely does. If your budget is tight, that row matters most.

## A short rule set

- Facts about the user that change or must be deleted: use a structured store with explicit supersede and delete rules.
- Open questions about past chats ("what did we say about the trip?"): add vector recall, and make a delete reach the vector index too. The `hybrid` strategy does that by dropping chunks that name a deleted value.
- Never rely on a rolling summary to forget. It only forgets when the summarizer drops a line, and that happens by age, not by request. An LLM summarizer told to drop forgotten facts might do better. Record mode would measure that, and it has not run yet.

## What this guide cannot tell you

The profile store rows are an upper bound. Its extractor knows the generator's phrasing. A real extractor is an LLM call that can miss a fact or store a fact about the user's sister. Measure your own extractor before you trust that row.
