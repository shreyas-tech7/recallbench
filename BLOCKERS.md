# Blockers

## Skill installs (2026-11-21)
- What: `npx -y skills add DietrichGebert/ponytail -g -a claude-code -y` (and the other toolkit installs).
- Error: the permission system denied the call ("Permission for this action was denied by the Claude Code auto mode classifier").
- Instead: used the superpowers skills already in the session. Followed Ponytail's idea (least code, no extra layers) by hand. No caveman. Logged in docs/TOOLING.md.

## FastEmbed model download (2026-11-21)
- What: `TextEmbedding("BAAI/bge-small-en-v1.5")` with a 3-document embed.
- Error: `Could not download model from HuggingFace: 403 Forbidden (agent proxy: no rule or network setting allows this host)`. The storage.googleapis.com copy answered `AccessDenied: Anonymous caller does not have storage.objects.get access` for `qdrant-fastembed/fast-bge-small-en-v1.5.tar.gz`.
- Instead: the hash embedder runs every vector number. Dense recall is marked blocked in the README. `FastEmbedder` and `--embedder fastembed` exist for a machine that can download the model.
- Manual step: docs/HUMAN_STEPS.md, "Run dense recall".

## Record mode (2026-11-21)
- What: an LLM summarizer and reader on a free provider for 3 personas.
- Error: no `GROQ_API_KEY` or `OPENROUTER_API_KEY` in the environment. `api.groq.com` and `openrouter.ai` both failed with `CONNECT tunnel failed, response 403`.
- Instead: the scripted summarizer and the deterministic reader give every number. `recallbench record` writes `results/record-status.json` with the reason, and the README says record mode did not run. The LLM client passes its tests against a fake local server.
- Manual step: docs/HUMAN_STEPS.md, "Record mode".

## Bugs found
- Wilson interval at k == n put the upper bound a hair under the rate (float rounding). Frequency 2 times severity 3 = 6. Fixed by clamping. Live bug.
- Reader read "Forget my hobby, please." as a hobby named "please". Frequency 3 times severity 4 = 12. Fixed by trying forget patterns first. Live bug, found by the ground truth replay.
- Full context spent about 44% of its budget on assistant filler and could skip a newer turn to fit an older one. Frequency 5 times severity 4 = 20. Fixed: user turns only, no gaps. Found by the code review subagent.
- Vector recall and hybrid were capped at 10 chunks, so the budget sweep did nothing for them. Frequency 5 times severity 3 = 15. Fixed: fill the budget by score. Found by the code review subagent.
- Temporal questions held the value, a free word for vector recall to match. Frequency 4 times severity 3 = 12. Fixed: questions name the fact only. Found by the code review subagent.
- Forget violations checked only the slot asked about. Frequency 5 times severity 4 = 20. Fixed: every forgotten value of the persona, on every question, with a new "any question" column. Found by the outside check subagent.
- The build-seed guard only caught seed 1 with a lowercase "final" in the path. Frequency 2 times severity 3 = 6. Fixed: seeds 1 to 3, "final" or "second", any case.
- CI skipped `readme --check` when only docs/DECISION_GUIDE.md or docs/INTERVIEW_QA.md changed. Frequency 2 times severity 2 = 4. Fixed in the path filter.

## Not fixed (logged)
- The extractor and the reader only know the generator's exact phrasing. A capitalized "Delete my address" would not register. Said in the README limits. Fixing it means a less exact reader, which would blur what the benchmark isolates.
- Wilson intervals assume independent questions. About 13 questions share one persona. Said in the README limits. A cluster bootstrap would be the fix.
- No test sets a slot again after a forget. The generator never does it, so the benchmark does not measure it.
