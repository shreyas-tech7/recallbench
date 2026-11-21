"""Write the number blocks in the README and docs, and docs/index.html, from the results files.

Nobody types a number into the README. Each block sits between `<!-- gen:NAME -->` and
`<!-- /gen:NAME -->`, and this module rewrites it.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .questions import TYPES
from .strategies import NAMES

FINAL = "results/final-seed2027.json"
SECOND = "results/second-seed31337.json"
TUNE = "results/tune-seed1.json"
RECORD = "results/record-status.json"
FILES = ["README.md", "docs/DECISION_GUIDE.md", "docs/INTERVIEW_QA.md"]
BLOCK = re.compile(r"(<!-- gen:(\w+) -->\n)(.*?)(<!-- /gen:\2 -->)", re.S)
TYPE_LABEL = {
    "single": "Single fact",
    "updated": "Updated fact",
    "multi_session": "Multi-session",
    "temporal": "Temporal",
    "abstention": "Abstention",
    "forgotten": "Forgotten",
}


def pct(r: dict) -> str:
    return f"{r['k']}/{r['n']} = {100 * r['rate']:.1f}% ({100 * r['lo']:.1f} to {100 * r['hi']:.1f})"


def short(r: dict) -> str:
    return f"{100 * r['rate']:.0f}% ({100 * r['lo']:.0f} to {100 * r['hi']:.0f})"


def load(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text())


def _table(head: list[str], rows: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(head) + " |", "| " + " | ".join(["---"] * len(head)) + " |"] + [
        "| " + " | ".join(r) + " |" for r in rows
    ]


def meta_line(res: dict, rel: str) -> str:
    m = res["meta"]
    return (
        f"Run of {m['date']}, model: {m['model']}, seed {m['seed']} (never used while building, "
        f"tuning used seed {m['tune_seed']}), budget {m['budget_tokens']} tokens per answer, "
        f"{m['personas']} personas, {m['sessions']} sessions, {m['questions']} questions. File `{rel}`."
    )


def accuracy_table(res: dict) -> list[str]:
    head = ["Strategy"] + [TYPE_LABEL[t] for t in TYPES] + ["All"]
    rows = []
    for name in NAMES:
        s = res["strategies"][name]
        rows.append([f"`{name}`"] + [short(s["by_type"][t]) for t in TYPES] + [short(s["overall"])])
    return _table(head, rows)


def risk_table(res: dict) -> list[str]:
    head = [
        "Strategy",
        "Stale-fact rate",
        "Forget violations (deleted value returned)",
        "Deleted value given as answer",
        "Tokens per answer (mean)",
    ]
    rows = []
    for name in NAMES:
        s = res["strategies"][name]
        rows.append(
            [
                f"`{name}`",
                pct(s["stale_rate"]),
                pct(s["forget_violations"]),
                pct(s["forget_answer_leaks"]),
                f"{s['tokens_per_answer']['mean']:.0f}",
            ]
        )
    return _table(head, rows)


def sweep_table(res: dict) -> list[str]:
    budgets = list(res["sweep"])
    head = (
        ["Strategy"]
        + [f"All, budget {b}" for b in budgets]
        + [f"Forget violations, budget {b}" for b in budgets]
    )
    rows = []
    for name in NAMES:
        rows.append(
            [f"`{name}`"]
            + [short(res["sweep"][b][name]["overall"]) for b in budgets]
            + [short(res["sweep"][b][name]["forget_violations"]) for b in budgets]
        )
    return _table(head, rows)


def compare_table(final: dict, second: dict) -> list[str]:
    head = ["Strategy", f"All, seed {final['meta']['seed']}", f"All, seed {second['meta']['seed']}"]
    head += [
        f"Forget violations, seed {final['meta']['seed']}",
        f"Forget violations, seed {second['meta']['seed']}",
    ]
    rows = []
    for n in NAMES:
        a, b = final["strategies"][n], second["strategies"][n]
        rows.append(
            [
                f"`{n}`",
                short(a["overall"]),
                short(b["overall"]),
                short(a["forget_violations"]),
                short(b["forget_violations"]),
            ]
        )
    return _table(head, rows)


def record_text(rec: dict) -> str:
    if rec.get("status") != "ran":
        return (
            f"Record mode did not run. Checked on {rec['date']}: {rec['reason']} "
            "So every number on this page comes from the deterministic reader and the scripted summarizer. "
            "The LLM summarizer and the LLM reader exist in `src/recallbench/llm.py` and pass their tests against a fake local server."
        )
    m = rec["meta"]
    lines = [
        f"Record run of {m['date']}, model `{m['model']}`, seed {m['seed']}, {m['personas']} personas, file `{RECORD}`.",
        "",
    ]
    lines += _table(
        ["Setup", "All", "Forget violations"],
        [[f"`{n}`", pct(s["overall"]), pct(s["forget_violations"])] for n, s in rec["strategies"].items()],
    )
    return "\n".join(lines)


def blocks(root: Path) -> dict[str, str]:
    final, second, rec = load(root, FINAL), load(root, SECOND), load(root, RECORD)
    s = final["strategies"]
    m = final["meta"]
    best_tokens = min(NAMES, key=lambda n: s[n]["tokens_per_answer"]["mean"])
    worst_tokens = max(NAMES, key=lambda n: s[n]["tokens_per_answer"]["mean"])
    out = {
        "results": "\n".join(
            [
                meta_line(final, FINAL),
                "",
                "Accuracy by question type, with 95% Wilson intervals:",
                "",
                *accuracy_table(final),
            ]
        ),
        "risks": "\n".join([*risk_table(final)]),
        "second": "\n".join(
            [
                f"Some rows reach {100 * max(s[n]['overall']['rate'] for n in NAMES):.0f}%, which looks too good. "
                f"So the same run went again on seed {second['meta']['seed']} (file `{SECOND}`).",
                "",
                *compare_table(final, second),
            ]
        ),
        "sweep": "\n".join(
            [
                f"Same seed {m['seed']}, budgets from {min(map(int, final['sweep']))} to {max(map(int, final['sweep']))} tokens:",
                "",
                *sweep_table(final),
            ]
        ),
        "cost": "\n".join(
            [
                f"Tokens per answer counts the memory lines a strategy returns plus the question (seed {m['seed']}, budget {m['budget_tokens']}).",
                f"The cheapest strategy is `{best_tokens}` at {s[best_tokens]['tokens_per_answer']['mean']:.0f} tokens. "
                f"The most expensive is `{worst_tokens}` at {s[worst_tokens]['tokens_per_answer']['mean']:.0f} tokens.",
                f"For 1,000 answers that is {s[best_tokens]['tokens_per_answer']['mean']:.0f}k against "
                f"{s[worst_tokens]['tokens_per_answer']['mean']:.0f}k input tokens for an LLM reader.",
                f"The deterministic reader costs no tokens. The full benchmark (5 strategies, 5 budgets) took "
                f"{m['seconds']:.1f} seconds on one core of `{m['cpu']}` on {m['date']}.",
            ]
        ),
        "record": record_text(rec),
        "qa_numbers": "\n".join(
            [
                f"From `{FINAL}` (seed {m['seed']}, budget {m['budget_tokens']}):",
                f"`vector_recall` forget violations: {pct(s['vector_recall']['forget_violations'])}.",
                f"`rolling_summary` forget violations: {pct(s['rolling_summary']['forget_violations'])}.",
                f"`vector_recall` stale-fact rate: {pct(s['vector_recall']['stale_rate'])}.",
                f"`full_context` multi-session accuracy: {pct(s['full_context']['by_type']['multi_session'])}.",
                f"Tokens per answer: `profile_store` {s['profile_store']['tokens_per_answer']['mean']:.0f}, "
                f"`full_context` {s['full_context']['tokens_per_answer']['mean']:.0f}.",
            ]
        ),
    }
    out["guide"] = "\n".join([*risk_table(final), "", *sweep_table(final)])
    return out


def page(root: Path) -> str:
    final = load(root, FINAL)

    def md_table(lines: list[str]) -> str:
        rows = [
            [c.strip().strip("`") for c in ln.strip("|").split("|")]
            for ln in lines
            if not ln.startswith("| ---")
        ]
        head = "".join(f"<th>{html.escape(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>recallbench results</title>
<style>
:root {{ --bg:#ffffff; --fg:#1b1f24; --muted:#57606a; --line:#d0d7de; --head:#f6f8fa; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0d1117; --fg:#e6edf3; --muted:#9aa4ae; --line:#30363d; --head:#161b22; }} }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; margin:0 auto; max-width:1100px; padding:24px 16px; }}
table {{ border-collapse:collapse; width:100%; margin:12px 0 28px; font-size:13px; display:block; overflow-x:auto; }}
th, td {{ border:1px solid var(--line); padding:6px 8px; text-align:left; white-space:nowrap; }}
th {{ background:var(--head); }}
p.meta {{ color:var(--muted); }}
</style>
</head>
<body>
<h1 id="top">recallbench results</h1>
<p class="meta">{html.escape(meta_line(final, FINAL))}</p>
<p>Every number on this page comes from the results file. The deterministic reader and the scripted summarizer produced them. Synthetic personas only.</p>
<h2 id="accuracy">Accuracy by question type</h2>
{md_table(accuracy_table(final))}
<h2 id="forgetting">Stale facts, forgetting and cost</h2>
{md_table(risk_table(final))}
<h2 id="budget">Accuracy by token budget</h2>
{md_table(sweep_table(final))}
<p><a href="../README.md">Back to the README</a></p>
</body>
</html>
"""


def write(root: Path, check: bool = False) -> list[str]:
    """Rewrite every block. With check, change nothing and return the files that are out of date."""
    b, stale = blocks(root), []
    for rel in FILES:
        path = root / rel
        text = path.read_text()
        new = BLOCK.sub(lambda m: m.group(1) + b[m.group(2)] + "\n" + m.group(4), text)
        if new != text:
            stale.append(rel)
            if not check:
                path.write_text(new)
    html_path = root / "docs" / "index.html"
    new_page = page(root)
    if not html_path.exists() or html_path.read_text() != new_page:
        stale.append("docs/index.html")
        if not check:
            html_path.write_text(new_page)
    return stale
