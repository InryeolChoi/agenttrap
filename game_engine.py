"""Compose live Nosana decisions, isolated Daytona tool execution, and the judge."""

import os
from typing import Any

from judge import judge_result
from nosana_client import NosanaError, infer
from runtime import RuntimeErrorDetail, run_round_in_daytona
from scenarios import make_emails


def run_attack(attack_prompt: str) -> dict[str, Any]:
    """Run baseline and attack rounds; return the stable UI result contract."""
    baseline_status = "UNKNOWN"
    logs = []
    stage = "preflight"
    try:
        if not isinstance(attack_prompt, str) or len(attack_prompt) > 2000:
            raise ValueError("Attack prompt must be a string of at most 2000 characters")
        missing = [key for key in ("DAYTONA_API_KEY", "NOSANA_API_KEY") if not os.getenv(key)]
        if missing:
            raise ValueError("Missing configuration: " + ", ".join(missing))
        stage = "baseline"
        baseline_emails = make_emails()
        baseline_run = run_round_in_daytona(baseline_emails, infer)
        logs.append({"round": "baseline", "entries": baseline_run.get("logs", []),
                     "sandbox_id": baseline_run.get("sandbox_id"), "model": baseline_run.get("model")})
        baseline_judgement = judge_result(
            baseline_run["summary"], baseline_run["tool_calls"], baseline_task_pass=True, mode="live"
        )
        baseline_pass = baseline_judgement["task_pass"] and baseline_judgement["security_pass"]
        baseline_status = "PASS" if baseline_pass else "FAIL"
        if not baseline_pass:
            result = judge_result(
                baseline_run["summary"], baseline_run["tool_calls"], baseline_task_pass=False, mode="live"
            )
            result["reason"] = "Baseline failed; attack was not run."
            result["evaluated_round"] = "baseline"
            result["logs"] = logs
            return result

        stage = "attack"
        attack_emails = make_emails(attack_prompt)
        attack_run = run_round_in_daytona(
            attack_emails, lambda emails: infer(emails, model=baseline_run.get("model"))
        )
        result = judge_result(
            attack_run["summary"], attack_run["tool_calls"], baseline_task_pass=baseline_pass, mode="live"
        )
        result["baseline_status"] = "PASS" if baseline_pass else "FAIL"
        logs.append({"round": "attack", "entries": attack_run.get("logs", []),
                     "sandbox_id": attack_run.get("sandbox_id"), "model": attack_run.get("model")})
        result["logs"] = logs
        result["evaluated_round"] = "attack"
        result["models"] = {"baseline": baseline_run.get("model"), "attack": attack_run.get("model")}
        return result
    except Exception as exc:
        reason = str(exc) if isinstance(exc, (ValueError, NosanaError, RuntimeErrorDetail)) else f"Execution failed: {type(exc).__name__}"
        logs.append({"round": stage, "entries": [reason, *getattr(exc, "__notes__", [])]})
        return {
            "mode": "execution_error",
            "baseline_status": baseline_status,
            "security_pass": False,
            "task_pass": False,
            "verdict": "EXECUTION_ERROR",
            "reason": reason,
            "error_stage": stage,
            "tool_calls": [],
            "summary": {},
            "logs": logs,
        }
