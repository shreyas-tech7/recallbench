# Human steps

Steps that only Shreyas can do, in order. The release commit is named below.

Release commit: `ee194409745836a1727b38af72a64aca28ff41d0`.
Branch: `claude/project-thread-00glbp`.

1. **Open a pull request** from `claude/project-thread-00glbp` into `main` on GitHub. Read the diff. Merge with a merge commit, so the release commit stays in the history of `main`.
2. **Create the tag** on the release commit:
   ```bash
   git fetch origin
   git tag -a v0.1.0-rc1 ee194409745836a1727b38af72a64aca28ff41d0 -m "Release candidate 1"
   git push origin v0.1.0-rc1
   ```
   Or create a pre-release with that tag on the GitHub Releases page.
3. **Run the secret scan once more:** `gitleaks git -v .` in a fresh clone.
4. **Make the repo public.** Done 2026-11-26: the repo is public.
5. **Pages:** not needed. `docs/index.html` opens from disk. Turn on Pages from `/docs` on `main` only if you want a hosted copy.
6. **Social preview:** upload `docs/social-preview.png` in Settings, General, Social preview.
7. **About box and topics:** paste the description from `docs/GITHUB_ABOUT.md` and the topics from `docs/topics.txt`, if they are not set yet.
8. **Pin the repo** on your profile or list it in your profile README.
9. **Publish to PyPI** with trusted publishing, if you want `pip install recallbench`. Add a publish workflow first. The name was free on 2026-11-21.
10. **Record mode:** create a free key at a provider that offers a free tier (Groq or OpenRouter). Add it as `GROQ_API_KEY` or `OPENROUTER_API_KEY` in the environment or as a network secret. Then run:
    ```bash
    .venv/bin/recallbench record --provider groq --personas 3
    .venv/bin/recallbench readme
    ./init.sh
    ```
    Check the provider's free limits first. Only synthetic text is sent.
11. **Dense recall:** on a machine that reaches huggingface.co, run:
    ```bash
    uv pip install --python .venv/bin/python -e ".[dense]"
    .venv/bin/recallbench run --seed 4049 --embedder fastembed --out results/dense-seed4049.json
    ```
    The README does not show this file yet. Add a block for it if the numbers matter.
12. **Decide whether `docs/build/BUILD_PROMPT.md` stays public.** It is the full build brief.
13. **Skills that could not install here:** ponytail, caveman, find-skills and humanizer. The permission system denied the install. Install them on your machine if you want later sessions to use them. OmniRoute and litellm need a key, so they stay manual.
