# Decisions

One line per choice: what, the options weighed, and why.

- 2026-11-21 Name: `recallbench`. PyPI and npm both answered 404 for `recallbench` on 2026-11-21. The brief checked the backups `memgauge` and `forgetbench` on 2026-11-20 and found no well-known project. Kept the first free name, which matches the repo.
- 2026-11-21 Branch: `claude/project-thread-00glbp`, not `claude/build-recallbench`. The session only allows pushes to that branch (coordinator rule 11).
- 2026-11-21 Working copy: `/home/user/recallbench`, the clone the session already had, instead of `~/work/recallbench`. Same origin, less setup.
- 2026-11-21 Token budget: 512 tokens per answer for every strategy, with a sweep at 128, 256, 512 and 1024. A persona transcript runs about 1,500 to 3,900 tokens, so 512 forces a real choice while still fitting a profile.
- 2026-11-21 Token counter: words plus punctuation marks by regex. Options were tiktoken (download), a model tokenizer (blocked host) or a regex. The regex is offline and the same for every strategy, which is what the comparison needs.
- 2026-11-21 Question date: the day after a persona's last session, for every question. Mid-timeline questions would need state snapshots and add little to the six types.
- 2026-11-21 Reader: hand-written patterns on first-person statements, replayed in date order. The profile store uses the same extractor. That makes the profile store an upper bound for a store whose extractor is perfect. Said in the README limits.
- 2026-11-21 Forget violation: a deleted value appears, as a whole word, anywhere in the lines a strategy returns. A second count shows when the reader also gives the deleted value as the answer. Returning the text is the leak, even when the reader is smart enough to skip it.
- 2026-11-21 Delete in the profile store removes every row of the slot, history included. A soft delete (active=0) would keep the value. A test shows the soft delete fails.
- 2026-11-21 Hybrid: profile lines first, then vector chunks in the budget that is left. A forget request also drops vector chunks that name a deleted value. Without that, the hybrid would leak like plain vector recall.
- 2026-11-21 Vector recall: one chunk per user turn, top 10 by cosine, then the budget. Options were session chunks (too big for the budget) or turns. Assistant turns are not indexed because they hold no facts.
- 2026-11-21 Hash embedder: signed feature hashing of words and character trigrams into 512 dimensions with blake2b. Deterministic and offline.
- 2026-11-21 Scripted summarizer: keep user lines that hold a fact word, drop small talk, drop the oldest lines when over budget. It does not act on forget requests. A real LLM summarizer can, which is what record mode would test.
- 2026-11-21 Deleted slots per persona: 1 to 3 (first draft had 1 to 2) to get more forgotten questions. Changed on the tuning seed before any final run.
- 2026-11-21 Seeds: tuning seed 1, tests use seeds 1 to 3, final seed 2027, second seed 31337. Seeds 2027 and 31337 ran only for the final numbers.
- 2026-11-21 Dependencies: numpy at run time, FastEmbed as the optional `dense` extra. The brief names both.
- 2026-11-21 Skill installs: not attempted again after the permission system denied the first `npx skills add` call. The superpowers skills were already present in the session.
