# Handover

## Done
Every feature except the two blocked ones (F09 dense recall, F15 record mode). The release check found fairness bugs, which are fixed with tests. Seeds 2027 and 31337 were retired after the fixes. Final numbers on seed 4049, second seed 90210.

## Next
Release SHA ee19440 is recorded. Bundle and final report are outside the repo. Next is the pull request into main and the v0.1.0-rc1 pre-release on ee19440.

## Open decisions
None. Blockers need a key (record mode) or a machine that reaches huggingface.co (dense recall).

## Commands
```bash
./init.sh
.venv/bin/recallbench readme --check
.venv/bin/recallbench truth --seed 4049
git push -u origin HEAD && git push backup HEAD
```
