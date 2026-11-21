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
