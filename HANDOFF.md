# AgentTrap handoff

## Current Goal
Connect a real Nosana Defender decision to Daytona sandbox tool execution and return one result JSON. Then run the specified pytest checks and integrate the independently owned UI.

## Current Branch
Current checkout: `feat/runtime`. `main` is the shared integration baseline; Developer B uses `feat/game` in a separate checkout.

## Last Commit
Bootstrap checkpoint containing this file. Use `git log -1 --oneline` to identify the current immutable commit.

## Completed Features
- Inspected environment: macOS ARM64; Python 3.9.6 (below requested 3.11); Git, `gh`, Codex CLI, Claude Code, and `uv` are installed.
- System Python is 3.9.6 (below project minimum). Created a project-local `.venv` using Python 3.14.8 and installed requirements there; global Python was not changed.
- Added Nosana inference adapter with dynamic model discovery, JSON parsing/validation, and key kept on orchestrator.
- Added Daytona runner that reads emails inside the sandbox, sends only returned email data to host-side Nosana inference, records blocked tool attempts, limits steps/time/output, and deletes its sandbox.
- Added deterministic Judge, fixed scenario data, game engine, UI result mock, tests, and Claude continuation script.
- README is now in Korean. Runtime preflight rejects missing credentials before creating a sandbox; oversized tool plans and malformed summary values are execution errors instead of silently truncating/coercing model output.
- Completed CLI (`python -m agenttrap check|models|hello|play`), same-model baseline comparison, baseline failure short-circuit, preserved baseline evidence on attack errors, bounded network-blocked sandboxes and cleanup diagnostics. `hello` and `play` require explicit `--live`.
- Suitable installed skills are recorded in `docs/SKILLS.md`; fixed backend acceptance criteria are in `docs/specs/runtime.md`.
- Checked current official docs: Daytona SDK uses `Daytona()`, `daytona.create()`, `sandbox.process.code_run(...)`, and `sandbox.delete()`; Nosana base URL is `https://inference.nosana.com/v1`, with `/models` for live models.

## In Progress
- Need API credentials to prove the live end-to-end path.
- Public repository: https://github.com/InryeolChoi/agenttrap . GitHub authentication works when network access is allowed.
- Write-access invitation sent to `pang0916`; invitation acceptance is pending.
- Friend's UI agent can implement `app.py` using `docs/FRIEND_AGENT_PROMPT.md` on `feat/game` in a separate clone.

## Known Issues
- `DAYTONA_API_KEY` and `NOSANA_API_KEY` are missing. No API calls or sandbox were made.
- Earlier GitHub authentication failure was caused by restricted sandbox network access, not an invalid token. Check `gh auth status` with network access before diagnosing authentication failures.
- Local system Python remains 3.9.6; project dependencies and tests use `.venv` with Python 3.14.8. Daytona still runs the untrusted tool runner remotely.
- No live model has been selected yet; the adapter discovers the first currently served model, or accepts `NOSANA_MODEL`.
- Do not claim the acceptance criteria are complete until live API execution and tests succeed.

## Test Results
`.venv/bin/python -m pytest -q` → 26 passed. Red/green regressions cover preflight, dropped tool calls, lost baseline evidence, error attribution, and CLI execution guards. External-service doubles execute the fixed Python runner locally; game outcomes and attack text remaining data are also tested. `python -m agenttrap check` reports both keys missing. No live integration checks have been performed.

## Daytona Status
SDK call pattern confirmed against current official documentation; API key missing; sandbox creation not attempted.

## Nosana Status
OpenAI-compatible endpoint confirmed against current official docs; API key missing; model list and inference not attempted.

## Next Actions
1. Fill the ignored local `.env` with `DAYTONA_API_KEY` and `NOSANA_API_KEY` (never paste them in chat); confirm before any credit-billed Nosana call or Daytona sandbox run.
2. Developer B accepts the write-access invitation to the repository.
3. Developer B clones the repository and checks out `feat/game`; Developer A works on `feat/runtime`. Dependencies and unit tests are already installed and passing in the local `.venv`.
4. Run a Daytona Hello World and clean up, then list Nosana models and test one inference.
5. Run the baseline and attack through `game_engine.run_attack`; inspect returned logs and correct API/model issues.
6. Integrate Developer B's `app.py`, perform a full UI run, and refresh this handoff.

## File Ownership
- Developer A: `runtime.py`, `nosana_client.py`.
- Developer B: `app.py`, `tests/test_app.py`; see `docs/FRIEND_AGENT_PROMPT.md`.
- Integrator: `game_engine.py`, `tests/test_runtime.py`, requirements and docs.
- Shared contract changes require coordination.

## Claude Code Handoff Prompt
Read `AGENTS.md` and this file first. Inspect current Git status and all existing files. Continue from the last saved state; do not rewrite modules, overwrite uncommitted changes, or expose/commit credentials. Honor file ownership and the shared result contract. Use `.venv` for host-side Python and Daytona for the sandboxed tool runner. First unblock API credentials and GitHub authentication with the user, then run the tests and live checks. Update this handoff after each meaningful milestone.
