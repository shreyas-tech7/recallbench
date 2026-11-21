"""Record mode run: LLM summarizer and LLM reader on a few personas."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from .bench import aggregate, score
from .generator import generate
from .llm import Client, llm_answer, llm_summarizer, normalize
from .questions import build
from .strategies import ProfileStore, RollingSummary


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
                # Same scoring as the main run, with the model's answer and lowercased keys.
                key = replace(
                    q,
                    answer=normalize(q.answer),
                    old_values=[normalize(v) for v in q.old_values],
                    deleted_values=[normalize(v) for v in q.deleted_values],
                )
                rows.append(score(key, lines, got))
        out["strategies"][name] = aggregate(rows)
    out["meta"]["calls"] = client.calls
    return out
