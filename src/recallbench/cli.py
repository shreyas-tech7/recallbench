"""Command line: recallbench generate | truth | run | demo | record | readme."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .bench import BUDGET, BUILD_SEEDS, TUNE_SEED, _named, ground_truth_check, run
from .generator import generate
from .questions import TYPES, build
from .readme import RECORD, write
from .strategies import NAMES, HashEmbedder, make

ROOT = Path.cwd()


def _embedder(name: str):
    if name == "hash":
        return HashEmbedder()
    from .strategies import FastEmbedder

    return FastEmbedder()


def cmd_generate(a) -> int:
    personas = generate(a.seed, a.personas)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "personas.jsonl").write_text("".join(json.dumps(p.to_dict()) + "\n" for p in personas))
    (out / "questions.jsonl").write_text(
        "".join(json.dumps(q.to_dict()) + "\n" for q in build(personas, a.seed))
    )
    print(f"wrote {len(personas)} personas and their questions to {out}")
    return 0


def cmd_truth(a) -> int:
    bad = ground_truth_check(a.seed, a.personas)
    n = len(build(generate(a.seed, a.personas), a.seed))
    print(f"ground truth replay, seed {a.seed}: {n - len(bad)}/{n} questions answered exactly")
    return 1 if bad else 0


def cmd_run(a) -> int:
    name = Path(a.out).name.lower()
    if a.seed in BUILD_SEEDS and ("final" in name or "second" in name):
        print(
            f"refusing: seed {a.seed} was used while building, so it cannot produce final numbers",
            file=sys.stderr,
        )
        return 2
    res = run(a.seed, a.budget, _embedder(a.embedder), sweep=not a.no_sweep, n_personas=a.personas)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    _print(res)
    print(f"wrote {a.out}")
    return 0


def _print(res: dict) -> None:
    head = ["strategy"] + TYPES + ["all", "stale", "forget_viol", "tokens"]
    print("  ".join(f"{h:>13}" for h in head))
    for name in NAMES:
        s = res["strategies"][name]
        cells = [f"{s['by_type'][t]['rate']:.2f}" for t in TYPES] + [
            f"{s['overall']['rate']:.2f}",
            f"{s['stale_rate']['rate']:.2f}",
            f"{s['forget_violations']['rate']:.2f}",
            f"{s['tokens_per_answer']['mean']:.0f}",
        ]
        print("  ".join(f"{c:>13}" for c in [name] + cells))


def cmd_demo(a) -> int:
    """Small run that shows the table and what each strategy returns for one forgotten fact."""
    res = run(a.seed, BUDGET, sweep=False, n_personas=3)
    _print(res)
    personas = generate(a.seed, 3)
    q = next(q for q in build(personas, a.seed) if q.qtype == "forgotten")
    p = next(p for p in personas if p.pid == q.pid)
    print(
        f"\nquestion for {p.name} (synthetic): {q.text!r}  truth: {q.answer!r}  deleted: {q.deleted_values}"
    )
    for name in NAMES:
        strat = make(name, BUDGET)
        for s in p.sessions:
            strat.ingest(s)
        lines = strat.retrieve(q.text, q.date)
        leaked = [ln for ln in lines if _named(q.deleted_values, [ln])]
        print(f"  {name:16} returns {len(lines):3} lines, {len(leaked)} name a deleted value: {leaked[:1]}")
    return 0


def cmd_record(a) -> int:
    from .llm import PROVIDERS, from_env
    from .record import record

    client = from_env(a.provider)
    out = Path(RECORD)
    if client is None:
        status = {
            "status": "blocked",
            "date": date.today().isoformat(),
            "reason": f"no {PROVIDERS[a.provider][1]} in the environment, so no request was sent.",
        }
        out.write_text(json.dumps(status, indent=1) + "\n")
        print(f"record mode blocked: {status['reason']} Wrote {out}.")
        return 3
    res = record(client, a.seed, a.personas)
    res["status"] = "ran"
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(f"record run done with {res['meta']['calls']} calls. Wrote {out}.")
    return 0


def cmd_readme(a) -> int:
    stale = write(ROOT, check=a.check)
    if a.check:
        if stale:
            print("out of date:", ", ".join(stale))
            return 1
        print("generated blocks are up to date")
        return 0
    print("rewrote:", ", ".join(stale) or "nothing")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="recallbench", description=__doc__)
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="write synthetic personas and questions as JSONL")
    g.add_argument("--seed", type=int, default=TUNE_SEED)
    g.add_argument("--personas", type=int, default=20)
    g.add_argument("--out", default="data")
    t = sub.add_parser("truth", help="replay every transcript and check every answer")
    t.add_argument("--seed", type=int, default=TUNE_SEED)
    t.add_argument("--personas", type=int, default=20)
    r = sub.add_parser("run", help="run all strategies on one seed")
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--budget", type=int, default=BUDGET)
    r.add_argument("--personas", type=int, default=20)
    r.add_argument("--embedder", choices=["hash", "fastembed"], default="hash")
    r.add_argument("--no-sweep", action="store_true")
    r.add_argument("--out", required=True)
    d = sub.add_parser("demo", help="small run on 3 personas")
    d.add_argument("--seed", type=int, default=TUNE_SEED)
    rc = sub.add_parser("record", help="LLM summarizer and reader on a free provider (needs a key)")
    rc.add_argument("--provider", choices=["groq", "openrouter"], default="groq")
    rc.add_argument("--seed", type=int, default=TUNE_SEED)
    rc.add_argument("--personas", type=int, default=3)
    rm = sub.add_parser("readme", help="rewrite the generated number blocks")
    rm.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return {
        "generate": cmd_generate,
        "truth": cmd_truth,
        "run": cmd_run,
        "demo": cmd_demo,
        "record": cmd_record,
        "readme": cmd_readme,
    }[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
