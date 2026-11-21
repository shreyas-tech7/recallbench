# Interview questions and answers

Each answer points to the code or the results file it rests on. The numbers sit in the generated block at the end. They come from the results file, not from a person.

**1. What does recallbench measure?**

How well a memory strategy keeps, updates and forgets facts about a user across many sessions. It reports accuracy for six question types, the stale-fact rate, forget violations and tokens per answer. The scoring is in `src/recallbench/bench.py`, function `score`.

**2. Why is an update harder than an append?**

An append only needs the new fact to be found. An update needs the new fact found and the old one ignored. Raw memory holds both lines, and both match the question. The strategy must return the newer one, and the reader must know which is newer. That is why every memory line carries a date and why `reader.replay` sorts by date before it applies anything. Vector recall shows the failure: it ranks lines by similarity, so an old "I live in Omaha" can beat a newer "We moved to Boise" for "Which city do I live in?". The stale-fact rate counts exactly that case.

**3. Why is forgetting hard for vector memory?**

A vector index stores chunks of text, not facts. "Forget my address" is one more chunk. It does not remove the chunk that holds the address. To forget, you must find every chunk that holds the value and delete it, and you must know the value to search for it. `VectorRecall` in `src/recallbench/strategies.py` never does that, so its forget violations stay high. `Hybrid` does it: when the profile store deletes a slot, it passes the old values to `VectorRecall.drop`.

**4. Why put tokens per answer next to accuracy?**

Because an LLM reader pays for every token on every question. Two strategies with the same accuracy can differ several times over in cost. Full context always fills the budget. A profile store sends a handful of short lines. `score` counts the returned lines plus the question with `count_tokens`.

**5. What are the five LongMemEval abilities?**

Information extraction, multi-session reasoning, temporal reasoning, knowledge updates and abstention. recallbench maps them to its question types: single fact, multi-session, temporal, updated fact and abstention. It adds a sixth type, forgotten, for deleted facts.

**6. How do you know the answer keys are right?**

`tests/test_truth.py` replays every full transcript with the reader and checks that it answers every question exactly. `recallbench truth` runs the same check from the command line. The answer keys come from the event timeline in `questions.py`, and the replay reads only the chat text. If the two disagree, the test fails.

**7. How does the deterministic reader work, and is it fair?**

It runs hand-written patterns over dated lines and replays them in date order (`src/recallbench/reader.py`). It is fair across strategies because every strategy gets the same reader. It is generous because its patterns know the generator's phrasing. So the benchmark tests what each strategy returns, not how well a model reads.

**8. Why is the profile store so strong here?**

It uses the same rule extractor as the reader. In this benchmark, extraction never misses. That makes its row an upper bound. In a real product the extractor is an LLM call that can miss facts or store a fact about someone else.

**9. What does a forget violation count?**

A question about a deleted fact where any returned line names a deleted value as a whole word (`_named` in `bench.py`). A second count, deleted value given as answer, shows when the reader also used it.

**10. How do you stop a strategy from cheating?**

Three guards. Strategies only get sessions during ingestion, and `test_strategies_never_see_questions_during_ingestion` checks both the argument type and that no question text sits in the stored memory. The final numbers use seed 2027, which no run touched while building. And the CLI refuses to write a final file from the tuning seed.

**11. Why Wilson intervals?**

Many rates sit at or near 0 or 1, where the plain normal interval breaks. Wilson stays inside 0 and 1 and keeps sensible width with tens of questions. `wilson` in `bench.py`.

**12. What did you learn from the budget sweep?**

Strategies that keep raw text depend on the budget. Full context climbs as the budget grows. The rolling summary only drops lines by age, so a small budget hides deleted values by accident and a large one keeps them. The profile store barely changes. See the sweep table in the README.

**13. Why does the rolling summary leak deleted facts?**

The scripted summarizer keeps fact lines and drops the oldest when the summary is too long. It never acts on a forget request. A real LLM summarizer can be told to drop forgotten facts, and record mode would test that. Record mode has not run yet, so that claim is untested here.

**14. What would you change for production?**

Replace the rule extractor with an LLM extractor and measure its misses. Make every delete reach every store: profile, vectors, summaries, caches and logs. Keep a date on every memory line. Track tokens per answer as a first-class metric.

**15. What is blocked and why?**

Dense embeddings and record mode. The build machine could not reach Hugging Face or the free LLM providers, and no key was set. The vector rows use a hash embedder. `BLOCKERS.md` lists the exact errors.

## Numbers used above

<!-- gen:qa_numbers -->
From `results/final-seed2027.json` (seed 2027, budget 512):
`vector_recall` forget violations: 41/41 = 100.0% (91.4 to 100.0).
`rolling_summary` forget violations: 41/41 = 100.0% (91.4 to 100.0).
`vector_recall` stale-fact rate: 4/47 = 8.5% (3.4 to 19.9).
`full_context` multi-session accuracy: 10/51 = 19.6% (11.0 to 32.5).
Tokens per answer: `profile_store` 64, `full_context` 517.
<!-- /gen:qa_numbers -->
