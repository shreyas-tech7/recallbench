# Tooling

| Tool | Source | Version | Why | Check |
| --- | --- | --- | --- | --- |
| superpowers skills | obra/superpowers, already in the session | session copy | plans, TDD, debugging, verification, review | used, nothing installed |
| ponytail, caveman, find-skills, humanizer | toolkit list | none | least code, terse chat, skill search, docs polish | install denied by the permission system, not retried. Ponytail rules and the writing rules applied by hand |
| graphify | PyPI graphifyy | not installed | resume runs on big repos | skipped, the repo has under 30 source files |
| gitleaks | github.com/zricethezav/gitleaks | go install latest | secret scan before commits and on history | installed |
| actionlint | github.com/rhysd/actionlint | go install latest | workflow lint | installed |
| pip-audit | PyPI | uv tool latest | dependency audit | installed |
| ruff | PyPI | dev extra | lint, format, `--select S` security rules | installed |
| skill-scanner | PyPI cisco-ai-skill-scanner | not installed | scan new skills | not needed, no skill was installed |
| osv-scanner, semgrep | GitHub | not used | dependency and code scan | api.osv.dev and semgrep.dev are blocked |
| LlamaFirewall, Prompt Guard, garak, mcp-scanner | GITHUB_REPOS.md | not used | prompt injection and MCP checks | do not fit: no LLM in the default run, no MCP server, and the models need huggingface.co |
| OmniRoute, litellm | GITHUB_REPOS.md | not used | free model routing | need a key, listed in HUMAN_STEPS.md |
| crawl4ai, playwright-mcp | GITHUB_REPOS.md | not used | crawling, UI tests | no crawl and no UI in this project |
