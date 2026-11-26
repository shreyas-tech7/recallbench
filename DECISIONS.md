# Decisions

One line per choice: what, the options weighed, and why.

- 2026-11-21 Name: `recallbench`. PyPI and npm both answered 404 for `recallbench` on 2026-11-21. The brief checked the backups `memgauge` and `forgetbench` on 2026-11-20 and found no well-known project. Kept the first free name, which matches the repo.
- 2026-11-21 Branch: `claude/project-thread-00glbp`, not `claude/build-recallbench`. The session only allows pushes to that branch (coordinator rule 11).
- 2026-11-21 Working copy: the clone the build session already had, instead of a fresh one. Same origin, less setup.
- 2026-11-21 Token budget: 512 tokens per answer for every strategy, with a sweep at 128, 256, 512 and 1024. A persona transcript runs about 1,500 to 3,900 tokens, so 512 forces a real choice while still fitting a profile.
- 2026-11-21 Token counter: words plus punctuation marks by regex. Options were tiktoken (download), a model tokenizer (blocked host) or a regex. The regex is offline and the same for every strategy, which is what the comparison needs.
- 2026-11-21 Question date: the day after a persona's last session, for every question. Mid-timeline questions would need state snapshots and add little to the six types.
- 2026-11-21 Reader: hand-written patterns on first-person statements, replayed in date order. The profile store uses the same extractor. That makes the profile store an upper bound for a store whose extractor is perfect. Said in the README limits.
- 2026-11-21 Forget violation: any value the persona asked to forget appears, as a whole word, anywhere in the lines a strategy returns, on any question. Reported on forgotten questions and on all questions. The first version checked only the slot asked about on forgotten questions, which undercounted (outside check). A second count shows when the reader also gives the deleted value as the answer. Returning the text is the leak, even when the reader is smart enough to skip it.
- 2026-11-21 Delete in the profile store removes every row of the slot, history included. A soft delete (active=0) would keep the value. A test shows the soft delete fails.
- 2026-11-21 Hybrid: profile lines first, then vector chunks in the budget that is left. A forget request also drops vector chunks that name a deleted value. Without that, the hybrid would leak like plain vector recall.
- 2026-11-21 Vector recall: one chunk per user turn, ranked by cosine, taken in that order until the budget is full. The first version capped it at the top 10, which made the budget sweep meaningless for vector recall and hybrid (code review). Changed before the new final run. Options were session chunks (too big for the budget) or turns. Assistant turns are not indexed because they hold no facts.
- 2026-11-21 Hash embedder: signed feature hashing of words and character trigrams into 512 dimensions with blake2b. Deterministic and offline.
- 2026-11-21 Scripted summarizer: keep user lines that hold a fact word, drop small talk, drop the oldest lines when over budget. It does not act on forget requests. A real LLM summarizer can, which is what record mode would test.
- 2026-11-21 Deleted slots per persona: 1 to 3 (first draft had 1 to 2) to get more forgotten questions. Changed on the tuning seed before any final run.
- 2026-11-21 Seeds: tuning seed 1, tests use seeds 1 to 3. The first final run used seed 2027 and second seed 31337. The code review then changed the strategies and questions, so those two seeds were retired, since their numbers had been seen while the fix was made. The new final seed is 4049 and the second seed 90210. Neither appears in the git history before this change, and only `truth` and `run` touched them. The review subagents fuzzed `truth` on seeds 0 to 399 only.
- 2026-11-21 Full context: keeps user turns only, without role prefixes, and returns the newest that fit with no gaps. The first version spent about 44% of its budget on assistant filler and could skip a newer turn to fit an older, shorter one (code review and outside check). Every other strategy already left assistant turns out.
- 2026-11-21 Temporal questions: name the fact, not the value ("my current city"). The first version put the value in the question, which gave vector recall a word to match on (code review).
- 2026-11-21 Budget sweep: 128, 256 and 1024, and the 512 row reuses the main run instead of running it twice.
- 2026-11-21 Build-seed guard: `recallbench run` refuses seeds 1 to 3 when the file name holds "final" or "second", in any case. The first version only refused seed 1 with a lowercase "final".
- 2026-11-21 Release check reviewers: the coordinator said nobody outside would review. So the code review and the outside check ran as fresh subagents in this session, and CI on GitHub counts as the outside check of the pushed head.
- 2026-11-21 Dependencies: numpy at run time, FastEmbed as the optional `dense` extra. The brief names both.
- 2026-11-21 Skill installs: not attempted again after the permission system denied the first `npx skills add` call. The superpowers skills were already present in the session.
