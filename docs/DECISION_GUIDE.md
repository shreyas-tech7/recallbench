# Decision guide: which memory strategy?

This guide is for a team that adds memory to an assistant. Every number in it comes from the generated block below. The prose around it describes patterns, and you should check each one against the block.

## The numbers

<!-- gen:guide -->
| Strategy | Stale-fact rate | Forget violations (deleted value returned) | Deleted value given as answer | Tokens per answer (mean) |
| --- | --- | --- | --- | --- |
| `full_context` | 0/47 = 0.0% (0.0 to 7.6) | 5/41 = 12.2% (5.3 to 25.5) | 0/41 = 0.0% (0.0 to 8.6) | 517 |
| `rolling_summary` | 0/47 = 0.0% (0.0 to 7.6) | 41/41 = 100.0% (91.4 to 100.0) | 0/41 = 0.0% (0.0 to 8.6) | 389 |
| `vector_recall` | 4/47 = 8.5% (3.4 to 19.9) | 41/41 = 100.0% (91.4 to 100.0) | 2/41 = 4.9% (1.3 to 16.1) | 160 |
| `profile_store` | 0/47 = 0.0% (0.0 to 7.6) | 0/41 = 0.0% (0.0 to 8.6) | 0/41 = 0.0% (0.0 to 8.6) | 64 |
| `hybrid` | 0/47 = 0.0% (0.0 to 7.6) | 0/41 = 0.0% (0.0 to 8.6) | 0/41 = 0.0% (0.0 to 8.6) | 214 |

| Strategy | All, budget 128 | All, budget 256 | All, budget 512 | All, budget 1024 | Forget violations, budget 128 | Forget violations, budget 256 | Forget violations, budget 512 | Forget violations, budget 1024 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `full_context` | 36% (31 to 42) | 42% (37 to 48) | 52% (46 to 58) | 73% (67 to 78) | 0% (0 to 9) | 5% (1 to 16) | 12% (5 to 26) | 37% (24 to 52) |
| `rolling_summary` | 58% (52 to 63) | 86% (81 to 89) | 100% (99 to 100) | 100% (99 to 100) | 10% (4 to 23) | 59% (43 to 72) | 100% (91 to 100) | 100% (91 to 100) |
| `vector_recall` | 86% (82 to 90) | 88% (83 to 91) | 88% (83 to 91) | 88% (83 to 91) | 100% (91 to 100) | 100% (91 to 100) | 100% (91 to 100) | 100% (91 to 100) |
| `profile_store` | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 0% (0 to 9) | 0% (0 to 9) | 0% (0 to 9) | 0% (0 to 9) |
| `hybrid` | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 100% (99 to 100) | 0% (0 to 9) | 0% (0 to 9) | 0% (0 to 9) | 0% (0 to 9) |
<!-- /gen:guide -->

## How to read them

1. **Start with forgetting.** If users can ask you to forget things, look at the forget violation column first. A strategy that keeps raw text (full context, a rolling summary that never rewrites, plain vector recall) keeps deleted values. A store that deletes by key does not. Your reader may skip a deleted value, but the value is still in the prompt, in the logs and in any cache.
2. **Then updates.** Look at the stale-fact rate. Vector recall ranks by similarity, not by date. When the newest statement uses different words from the question ("We moved to Boise" against "Which city do I live in?"), it can lose to an older line.
3. **Then cost.** Tokens per answer is what an LLM reader pays on every question. A profile store sends a few short lines. Full context sends the whole budget every time.
4. **Then the budget sweep.** Full context and the rolling summary depend on the budget. A profile store barely does. If your budget is tight, that row matters most.

## A short rule set

- Facts about the user that change or must be deleted: use a structured store with explicit supersede and delete rules.
- Open questions about past chats ("what did we say about the trip?"): add vector recall, and make a delete reach the vector index too. The `hybrid` strategy does that by dropping chunks that name a deleted value.
- Never rely on a rolling summary to forget. It only forgets when the summarizer drops a line, and that happens by age, not by request. An LLM summarizer told to drop forgotten facts might do better. Record mode would measure that, and it has not run yet.

## What this guide cannot tell you

The profile store rows are an upper bound. Its extractor knows the generator's phrasing. A real extractor is an LLM call that can miss a fact or store a fact about the user's sister. Measure your own extractor before you trust that row.
