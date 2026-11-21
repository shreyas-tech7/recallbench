import json

from recallbench.cli import main


def test_truth_command(capsys):
    assert main(["truth", "--seed", "2", "--personas", "5"]) == 0
    assert "answered exactly" in capsys.readouterr().out


def test_run_refuses_tune_seed_for_final(tmp_path):
    """Broken case: final numbers produced from the seed used while building."""
    assert main(["run", "--seed", "1", "--out", str(tmp_path / "final-seed1.json")]) == 2
    assert main(["run", "--seed", "1", "--out", str(tmp_path / "FINAL.json")]) == 2
    assert main(["run", "--seed", "2", "--out", str(tmp_path / "second-seed2.json")]) == 2


def test_run_writes_results(tmp_path):
    out = tmp_path / "r.json"
    assert main(["run", "--seed", "3", "--personas", "3", "--no-sweep", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["meta"]["seed"] == 3


def test_generate_writes_jsonl(tmp_path):
    assert main(["generate", "--seed", "2", "--personas", "2", "--out", str(tmp_path)]) == 0
    assert len((tmp_path / "personas.jsonl").read_text().splitlines()) == 2


def test_record_without_key_is_blocked(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    assert main(["record"]) == 3
    assert json.loads((tmp_path / "results" / "record-status.json").read_text())["status"] == "blocked"


def test_demo(capsys):
    assert main(["demo", "--seed", "2"]) == 0
    out = capsys.readouterr().out
    assert "profile_store" in out and "name a deleted value" in out
