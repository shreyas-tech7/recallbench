# Release check

Run on 2026-11-21 on branch `claude/project-thread-00glbp`, before the release commit.

## Code review

Nobody outside reviewed this build, so a fresh subagent with no build context reviewed the branch (brief rule 11). It found six issues and some nits.

| Finding | What changed |
| --- | --- |
| Full context spent its budget on assistant filler and role prefixes | It keeps user turns only, like every other strategy |
| Vector recall and hybrid returned at most 10 chunks, so the sweep did nothing for them | They fill the budget in order of similarity |
| The rolling summary row is also an upper bound, and the second seed does not explain why | README limits and the second-seed text say so |
| Temporal questions held the value, a word for vector recall to match | They name the fact only |
| Forget violations were counted only on forgotten questions | A second column counts every question |
| The cost text said 5 budgets, and the sweep ran 512 twice | The sweep reuses the main run, and the text counts the budgets |
| Nits: duplicated scoring in record mode, substring check in the demo, a dead date check, an unused re-export, a hardcoded dimension, a weak seed guard, `connect_ex` not guarded, the fake server not closed, Wilson independence | All fixed, except Wilson independence, which the README limits now name |

Each fix has a test that fails on the old code. That was checked by running the new tests with the old `src` stashed: 7 failed.

Because these changes came after the first final run, seeds 2027 and 31337 were retired. The final numbers now come from seed 4049 and the second run from seed 90210 (see DECISIONS.md).

## Outside check

A second fresh subagent cloned the branch into `/tmp/outside-check` and checked the seven Done-means items. All seven passed. It found one real bug: forget violations only checked the slot asked about. That is fixed above. It also found that full context could skip a newer turn, that the build-seed guard was weak, that the CI path filter missed two generated files, and that the results line always said "never used while building". All fixed. CI on GitHub runs the same checks on the pushed head.

## Tools

| Check | Result |
| --- | --- |
| `gitleaks git -v .` | no leaks in the history |
| `gitleaks dir -v .` | no leaks in the working tree |
| `pip-audit` on the project venv | no known vulnerabilities |
| `ruff check --select S src scripts` | all checks passed |
| `actionlint` | no problems |
| `python scripts/check_links.py` | no broken links (GitHub and the CI badge are skipped offline) |
| `./init.sh` | ruff, format, links and the tests all pass |
| humanizer skill | not installed (skill installs were denied). The writing rules are checked by `tests/test_repo.py` and were applied by hand |
| `git status` | clean after the release commit |
