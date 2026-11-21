"""Record mode run: LLM summarizer and LLM reader on a few personas."""

from __future__ import annotations

import re
from datetime import date

from .bench import aggregate
from .generator import generate
from .llm import Client, llm_answer, llm_summarizer, normalize
from .questions import build
from .strategies import ProfileStore, RollingSummary, count_tokens


def record(client: Client, seed: int, n_personas: int = 3, budget: int = 512) -> dict:
    personas = generate(seed, n_personas)
    questions = build(personas, seed)
    out = {
        "meta": {
            "seed": seed,
            "date": date.today().isoformat(),
            "model": client.model,
            "provider_url": client.base_url,
            "personas": n_personas,
            "questions": len(questions),
            "budget_tokens": budget,
        },
        "strategies": {},
    }
    configs = {
        "rolling_summary_llm": lambda: RollingSummary(budget, llm_summarizer(client, budget)),
        "profile_store_llm_reader": lambda: ProfileStore(budget),
    }
    for name, factory in configs.items():
        rows = []
        for p in personas:
            strat = factory()
            for s in p.sessions:
                strat.ingest(s)
            for q in (q for q in questions if q.pid == p.pid):
                lines = strat.retrieve(q.text, q.date)
                got = normalize(llm_answer(client, q.text, lines))
                text = "\n".join(lines)
                rows.append(
                    {
                        "qtype": q.qtype,
                        "correct": got == normalize(q.answer),
                        "stale": q.qtype == "updated" and got in {normalize(v) for v in q.old_values},
                        "forget_violation": any(
                            re.search(rf"\b{re.escape(v)}\b", text) for v in q.deleted_values
                        ),
                        "forget_answer_leak": got in {normalize(v) for v in q.deleted_values},
                        "tokens": count_tokens(text) + count_tokens(q.text),
                    }
                )
        out["strategies"][name] = aggregate(rows)
    out["meta"]["calls"] = client.calls
    return out
