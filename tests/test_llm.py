import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from recallbench.generator import generate
from recallbench.llm import Client, from_env, llm_answer, llm_summarizer, normalize
from recallbench.record import record


class Fake(BaseHTTPRequestHandler):
    replies: list = []
    seen: list = []

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Fake.seen.append((self.headers.get("Authorization"), body))
        code, text = Fake.replies.pop(0) if Fake.replies else (200, "unknown")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"choices": [{"message": {"content": text}}]}).encode())

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    Fake.replies, Fake.seen = [], []
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1"
    srv.shutdown()
    srv.server_close()


def test_client_sends_key_and_reads_reply(server):
    Fake.replies = [(200, " Boise. ")]
    c = Client(server, "k-test", "m")
    assert llm_answer(c, "Which city do I live in?", ["[2025-01-01] We moved to Boise."]) == "Boise"
    auth, body = Fake.seen[0]
    assert auth == "Bearer k-test" and body["model"] == "m" and body["temperature"] == 0


def test_client_retries_on_429(server, monkeypatch):
    monkeypatch.setattr("recallbench.llm.time.sleep", lambda s: None)
    Fake.replies = [(429, ""), (200, "ok")]
    assert Client(server, "k", "m").chat("hi") == "ok"


def test_llm_summarizer_keeps_only_dated_lines(server):
    Fake.replies = [(200, "Here is the memory:\n- [2025-01-02] I live in Omaha.\nnot a line")]
    s = generate(1, 1)[0].sessions[0]
    n = iter(range(100))
    out = llm_summarizer(Client(server, "k", "m"), 512)([], s, lambda: next(n))
    assert out == [("2025-01-02", 0, "I live in Omaha.")]


def test_record_runs_end_to_end_on_a_fake_server(server):
    c = Client(server, "k", "fake-model")
    res = record(c, seed=1, n_personas=1)
    assert res["meta"]["model"] == "fake-model" and res["meta"]["calls"] > 0
    assert set(res["strategies"]) == {"rolling_summary_llm", "profile_store_llm_reader"}


def test_no_key_means_no_client(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert from_env("groq") is None


def test_normalize():
    assert normalize("Boise | Ramen.") == "boise | ramen"


def test_client_refuses_other_schemes():
    """Broken case: a file: or plain http URL to a remote host would be opened."""
    for bad in ("file:///etc/passwd", "http://api.groq.com/openai/v1", "ftp://x"):
        with pytest.raises(ValueError):
            Client(bad, "k", "m")
