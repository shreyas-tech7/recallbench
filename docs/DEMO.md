# Demo

A real terminal transcript, captured on 2026-11-21 on the build machine (Intel Xeon @ 2.30GHz, Python 3.11). The demo uses the tuning seed 1 and 3 personas, so its numbers differ from the README. All personas are synthetic.

```text
$ .venv/bin/recallbench truth --seed 1
ground truth replay, seed 1: 266/266 questions answered exactly

$ .venv/bin/recallbench demo
     strategy         single        updated  multi_session       temporal     abstention      forgotten            all          stale    forget_viol         tokens
 full_context           0.60           0.75           0.44           0.78           1.00           1.00           0.72           0.00           0.50            517
rolling_summary           1.00           1.00           1.00           1.00           1.00           1.00           1.00           0.00           1.00            350
vector_recall           0.80           0.62           0.44           0.78           1.00           1.00           0.72           0.38           1.00            516
profile_store           1.00           1.00           1.00           1.00           1.00           1.00           1.00           0.00           0.00             75
       hybrid           1.00           1.00           1.00           1.00           1.00           1.00           1.00           0.00           0.00            517

question for Oakley Okafor (synthetic): 'What is my favorite food?'  truth: 'unknown'  deleted: ['pierogi', 'shakshuka']
  full_context     returns  35 lines, 0 name a deleted value: []
  rolling_summary  returns  27 lines, 2 name a deleted value: ['[2025-02-22] My favorite food is pierogi.']
  vector_recall    returns  34 lines, 2 name a deleted value: ['[2025-02-22] My favorite food is pierogi.']
  profile_store    returns   6 lines, 0 name a deleted value: []
  hybrid           returns  35 lines, 0 name a deleted value: []

$ .venv/bin/recallbench record
record mode blocked: no GROQ_API_KEY in the environment, so no request was sent. Wrote results/record-status.json.
(exit code 3)
```

For the results as a page, open [index.html](index.html) from disk.
