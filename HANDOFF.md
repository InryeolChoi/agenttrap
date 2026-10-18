# AgentTrap handoff

## Current Goal
Connect a real Nosana Defender decision to Daytona sandbox tool execution and return one result JSON. Then run the specified pytest checks and integrate the independently owned UI.

## Current Branch
Current checkout: `feat/runtime`. `main` is the shared integration baseline; Developer B uses `feat/game` in a separate checkout.

## Last Commit
Latest integrated implementation checkpoint: `c12f14e`. Use `git log -1 --oneline` for the latest documentation/checkpoint commit.

## Completed Features
- Inspected environment: macOS ARM64; Python 3.9.6 (below requested 3.11); Git, `gh`, Codex CLI, Claude Code, and `uv` are installed.
- System Python is 3.9.6 (below project minimum). Created a project-local `.venv` using Python 3.14.8 and installed requirements there; global Python was not changed.
- Added Nosana inference adapter with dynamic model discovery, JSON parsing/validation, and key kept on orchestrator.
- Added Daytona runner that reads emails inside the sandbox, sends only returned email data to host-side Nosana inference, records blocked tool attempts, limits steps/time/output, and deletes its sandbox.
- Added deterministic Judge, fixed scenario data, game engine, UI result mock, tests, and Claude continuation script.
- README is now in Korean. Runtime preflight rejects missing credentials before creating a sandbox; oversized tool plans and malformed summary values are execution errors instead of silently truncating/coercing model output.
- Completed CLI (`python -m agenttrap check|models|hello|play`), same-model baseline comparison, baseline failure short-circuit, preserved baseline evidence on attack errors, bounded network-blocked sandboxes and cleanup diagnostics. `hello` and `play` require explicit `--live`.
- Suitable installed skills are recorded in `docs/SKILLS.md`; fixed backend acceptance criteria are in `docs/specs/runtime.md`.
- Two-axis review completed: Standards 0 findings; Spec 1 finding fixed by preserving baseline tool evidence in invalid results. See `docs/REVIEW.md`. Three-minute presentation draft is in `docs/DEMO.md`.
- Shared Korean MVP specification is published on `main` as `SPEC.md` (commit `13a6f6a`).
- Parallel work for #7 (Nosana failures) and #8 (Sandbox lifecycle) was committed in separate worktrees and merged without conflicts. Final review found no spec defects; test ownership documentation was clarified.
- Checked current official docs: Daytona SDK uses `Daytona()`, `daytona.create()`, `sandbox.process.code_run(...)`, and `sandbox.delete()`; Nosana base URL is `https://inference.nosana.com/v1`, with `/models` for live models.

## In Progress
- Need API credentials to prove the live end-to-end path.
- Public repository: https://github.com/InryeolChoi/agenttrap . GitHub authentication works when network access is allowed.
- Write access for `pang0916` has been confirmed.
- Friend's UI agent can implement `app.py` using `docs/FRIEND_AGENT_PROMPT.md` on `feat/game` in a separate clone.

## Known Issues
- `DAYTONA_API_KEY` and `NOSANA_API_KEY` are missing. No API calls or sandbox were made.
- Earlier GitHub authentication failure was caused by restricted sandbox network access, not an invalid token. Check `gh auth status` with network access before diagnosing authentication failures.
- Local system Python remains 3.9.6; project dependencies and tests use `.venv` with Python 3.14.8. Daytona still runs the untrusted tool runner remotely.
- No live model has been selected yet; the adapter discovers the first currently served model, or accepts `NOSANA_MODEL`.
- Do not claim the acceptance criteria are complete until live API execution and tests succeed.

## Test Results
`.venv/bin/python -m pytest -q` → 54 passed after merging both parallel implementations. Public SDK-boundary tests cover provider validation, primary/cleanup error preservation, sandbox creation/execution/output/deletion failures, limits and key isolation, plus full game outcomes and CLI guards. `python -m agenttrap check` reports both keys missing. No live integration checks have been performed.

## Daytona Status
SDK call pattern confirmed against current official documentation; API key missing; sandbox creation not attempted.

## Nosana Status
OpenAI-compatible endpoint confirmed against current official docs; API key missing; model list and inference not attempted.

## Next Actions
1. Fill the ignored local `.env` with `DAYTONA_API_KEY` and `NOSANA_API_KEY` (never paste them in chat); confirm before any credit-billed Nosana call or Daytona sandbox run.
2. Developer B starts UI issue #3; no API keys are required for that issue.
3. Developer B clones the repository and checks out `feat/game`; Developer A works on `feat/runtime`. Dependencies and unit tests are already installed and passing in the local `.venv`.
4. Run a Daytona Hello World and clean up, then list Nosana models and test one inference.
5. Run the baseline and attack through `game_engine.run_attack`; inspect returned logs and correct API/model issues.
6. Integrate Developer B's `app.py`, perform a full UI run, and refresh this handoff.

## GitHub Work Items
- #2: offline-verifiable backend, implemented and reviewed; awaiting the backend PR merge.
- #3: UI round with mock results, assigned to `pang0916`, can start immediately.
- #4: real Nosana/Daytona validation, blocked by #2 and missing credentials/cost approval.
- #5: live UI integration and presentation rehearsal, blocked by #3 and #4.
- #7 and #8: parallel backend failure-path validation implemented and merged into `feat/runtime`; resolved by PR #6 when merged.
- PR #6 contains the reviewed backend and closes #2, #7, #8. Live validation remains separate in #4.
- All issue and PR titles and descriptions must be understandable Korean.

## File Ownership
- Developer A: `runtime.py`, `nosana_client.py`, `tests/test_nosana_client.py`.
- Developer B: `app.py`, `tests/test_app.py`; see `docs/FRIEND_AGENT_PROMPT.md`.
- Integrator: `game_engine.py`, `agenttrap.py`, remaining core tests, requirements and docs.
- Shared contract changes require coordination.

## Claude Code Handoff Prompt
Read `AGENTS.md` and this file first. Inspect current Git status and all existing files. Continue from the last saved state; do not rewrite modules, overwrite uncommitted changes, or expose/commit credentials. Honor file ownership and the shared result contract. Use `.venv` for host-side Python and Daytona for the sandboxed tool runner. First unblock API credentials and GitHub authentication with the user, then run the tests and live checks. Update this handoff after each meaningful milestone.
