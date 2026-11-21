# Environment

Probes run on 2026-11-21 with `curl -sS -o /dev/null -w '%{http_code}' -m 10 <url>`.

| Host | Result |
| --- | --- |
| https://huggingface.co | blocked (CONNECT tunnel failed, 403) |
| https://storage.googleapis.com | reachable (400 on the root), but the FastEmbed object answers AccessDenied |
| https://api.groq.com | blocked (CONNECT tunnel failed, 403) |
| https://openrouter.ai | blocked (CONNECT tunnel failed, 403) |
| https://api.osv.dev | blocked (CONNECT tunnel failed, 403) |
| https://semgrep.dev | blocked (CONNECT tunnel failed, 403) |
| https://pypi.org | reachable |
| https://raw.githubusercontent.com | reachable (301) |

No provider key variable was set. Python in the venv: 3.11. CPU: see `meta.cpu` in the results files.
