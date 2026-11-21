"""Record mode: an LLM summarizer and an LLM reader on a free OpenAI-compatible provider.

Keys come only from environment variables. Nothing here runs in the tests except
against a fake server on localhost.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.1-8b-instant"),
    "openrouter": (
        "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY",
        "meta-llama/llama-3.2-3b-instruct:free",
    ),
}
LINE = re.compile(r"^\[(\d{4}-\d{2}-\d{2})\]\s*(.+)$")


class Client:
    def __init__(self, base_url: str, key: str, model: str, timeout: float = 60):
        if not re.match(r"^(https://|http://127\.0\.0\.1[:/])", base_url):
            raise ValueError("base_url must be https, or http on 127.0.0.1 for tests")
        self.base_url, self.key, self.model, self.timeout = base_url.rstrip("/"), key, model, timeout
        self.calls = 0

    def chat(self, prompt: str, max_tokens: int = 400) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        wait = 2.0
        for attempt in range(5):
            req = urllib.request.Request(  # noqa: S310 (scheme checked in __init__)
                self.base_url + "/chat/completions",
                data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:  # noqa: S310 (fixed https or localhost URL)
                    self.calls += 1
                    return json.loads(r.read())["choices"][0]["message"]["content"].strip()
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 4:
                    raise
                time.sleep(wait)
                wait *= 2
        raise RuntimeError("unreachable")


def from_env(provider: str) -> Client | None:
    base, var, model = PROVIDERS[provider]
    key = os.environ.get(var)
    return Client(base, key, model) if key else None


def llm_summarizer(client: Client, budget: int):
    """A rolling summarizer that asks the model to rewrite the summary after each session."""

    def summarize(summary, session, seq):
        old = "\n".join(f"[{d}] {t}" for d, _, t in summary)
        convo = "\n".join(f"{t.role}: {t.text}" for t in session.turns)
        prompt = (
            "You keep a memory of facts about the user. Rewrite the memory after today's chat.\n"
            f"Rules: one fact per line, each line starts with the date it was first said, like [2025-01-31]. "
            "Write each fact in the first person, as the user said it. Replace facts that changed. "
            "Remove every fact the user asked you to forget, and do not mention it again. "
            f"Ignore facts about other people. Stay under {budget} tokens.\n\n"
            f"Memory:\n{old or '(empty)'}\n\nToday is {session.date}. Chat:\n{convo}\n\nNew memory:"
        )
        out = []
        for line in client.chat(prompt).splitlines():
            if m := LINE.match(line.strip(" -*")):
                out.append((m.group(1), seq(), m.group(2)))
        return out

    return summarize


def llm_answer(client: Client, question: str, lines: list[str]) -> str:
    prompt = (
        "Answer the question from the memory lines only. Reply with the answer and nothing else.\n"
        "If the memory does not hold the answer, reply exactly: unknown\n"
        "For a date, reply YYYY-MM-DD. For before or after, reply before or after. "
        "For two questions joined by 'and', reply both answers separated by ' | '.\n\n"
        "Memory:\n" + "\n".join(lines) + f"\n\nQuestion: {question}\nAnswer:"
    )
    return client.chat(prompt, max_tokens=30).strip().strip(".").strip()


def normalize(a: str) -> str:
    return " | ".join(p.strip().strip(".").lower() for p in a.split("|"))
