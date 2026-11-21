"""Run every strategy on one seed and score it. Then aggregate with 95% intervals."""

from __future__ import annotations

import math
import platform
import re
import time
from datetime import date
from pathlib import Path

from . import __version__
from .generator import generate
from .questions import TYPES, Question, build
from .reader import answer
from .strategies import NAMES, count_tokens, make

TUNE_SEED = 1  # the only seed used while tuning
BUILD_SEEDS = {1, 2, 3}  # the tuning seed plus the seeds the tests use
BUDGET = 512
SWEEP = [128, 256, 1024]  # plus BUDGET, which reuses the main run


def wilson(k: int, n: int, z: float = 1.96) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "rate": 0.0, "lo": 0.0, "hi": 0.0}
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    # Clamp so rounding never puts the rate outside its own interval (seen at k == n).
    return {"k": k, "n": n, "rate": p, "lo": max(0.0, min(p, c - h)), "hi": min(1.0, max(p, c + h))}


def _named(values: list[str], lines: list[str]) -> bool:
    text = "\n".join(lines)
    return any(re.search(rf"\b{re.escape(v)}\b", text) for v in values)


def score(q: Question, lines: list[str], got: str | None = None) -> dict:
    """Score one answer. `got` defaults to the deterministic reader's answer."""
    got = answer(q.text, lines) if got is None else got
    return {
        "qid": q.qid,
        "qtype": q.qtype,
        "answer": got,
        "correct": got == q.answer,
        "stale": q.qtype == "updated" and got in q.old_values,
        # Any returned line that names any value this persona asked to forget, whatever the question.
        "forget_violation": bool(q.forgotten) and _named(q.forgotten, lines),
        "forget_answer_leak": bool(q.deleted_values) and got in q.deleted_values,
        "tokens": count_tokens("\n".join(lines)) + count_tokens(q.text),
    }


def run_strategy(name: str, personas, questions, budget: int, embedder=None) -> list[dict]:
    by_pid: dict[str, list[Question]] = {}
    for q in questions:
        by_pid.setdefault(q.pid, []).append(q)
    rows = []
    for p in personas:
        strat = make(name, budget, embedder)
        for s in p.sessions:  # ingestion sees sessions only, never a question
            strat.ingest(s)
        for q in by_pid.get(p.pid, []):
            rows.append(score(q, strat.retrieve(q.text, q.date)))
    return rows


def aggregate(rows: list[dict]) -> dict:
    out = {"by_type": {}}
    for t in TYPES:
        sub = [r for r in rows if r["qtype"] == t]
        out["by_type"][t] = wilson(sum(r["correct"] for r in sub), len(sub))
    out["overall"] = wilson(sum(r["correct"] for r in rows), len(rows))
    upd = [r for r in rows if r["qtype"] == "updated"]
    out["stale_rate"] = wilson(sum(r["stale"] for r in upd), len(upd))
    gone = [r for r in rows if r["qtype"] == "forgotten"]
    out["forget_violations"] = wilson(sum(r["forget_violation"] for r in gone), len(gone))
    out["forget_violations_all"] = wilson(sum(r["forget_violation"] for r in rows), len(rows))
    out["forget_answer_leaks"] = wilson(sum(r["forget_answer_leak"] for r in gone), len(gone))
    toks = [r["tokens"] for r in rows]
    out["tokens_per_answer"] = {"mean": sum(toks) / len(toks), "max": max(toks)}
    return out


def cpu_name() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def run(seed: int, budget: int = BUDGET, embedder=None, sweep: bool = True, n_personas: int = 20) -> dict:
    start = time.perf_counter()
    personas = generate(seed, n_personas)
    questions = build(personas, seed)
    emb_name = embedder.name if embedder else "hash-512"
    res = {
        "meta": {
            "seed": seed,
            "tune_seed": TUNE_SEED,
            "date": date.today().isoformat(),
            "budget_tokens": budget,
            "personas": len(personas),
            "sessions": sum(len(p.sessions) for p in personas),
            "questions": len(questions),
            "questions_by_type": {t: sum(q.qtype == t for q in questions) for t in TYPES},
            "reader": "deterministic",
            "summarizer": "scripted",
            "embedder": emb_name,
            "model": "none (deterministic reader, scripted summarizer, " + emb_name + " embedder)",
            "version": __version__,
            "python": platform.python_version(),
            "cpu": cpu_name(),
        },
        "strategies": {},
        "sweep": {},
    }
    for name in NAMES:
        res["strategies"][name] = aggregate(run_strategy(name, personas, questions, budget, embedder))
    if sweep:
        for b in sorted(set(SWEEP) | {budget}):
            res["sweep"][str(b)] = {}
            for name in NAMES:
                if b == budget:
                    agg = res["strategies"][name]  # the main run, not a second copy of it
                else:
                    agg = aggregate(run_strategy(name, personas, questions, b, embedder))
                res["sweep"][str(b)][name] = {
                    "overall": agg["overall"],
                    "forget_violations": agg["forget_violations"],
                    "tokens_mean": agg["tokens_per_answer"]["mean"],
                }
    res["meta"]["seconds"] = time.perf_counter() - start
    return res


def ground_truth_check(seed: int, n_personas: int = 20) -> list[str]:
    """Replay every full transcript with the reader. Return the questions it gets wrong."""
    personas = {p.pid: p for p in generate(seed, n_personas)}
    bad = []
    for q in build(list(personas.values()), seed):
        lines = [f"[{s.date}] {t.role}: {t.text}" for s in personas[q.pid].sessions for t in s.turns]
        if answer(q.text, lines) != q.answer:
            bad.append(q.qid)
    return bad


__all__ = ["run", "ground_truth_check", "wilson", "score", "aggregate"]
