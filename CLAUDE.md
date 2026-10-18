# Claude Code continuation instructions

Before changing anything, read `AGENTS.md` and `HANDOFF.md`. Then inspect `git status --short --branch`, the latest commit, and the existing implementation. Continue from the current state; do not rewrite working modules or discard another developer's changes.

Honor file ownership and the public `run_attack(attack_prompt: str) -> dict` contract in `AGENTS.md`. Keep tests and API-key protections intact. Keep `NOSANA_API_KEY` out of Daytona, never execute attack text as code, and never commit `.env`. Run tests in the isolated Python environment. Do not force push, automatically commit, or push without an explicit user request.

The handoff prompt is at the end of `HANDOFF.md`.
