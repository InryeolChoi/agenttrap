"""Compose live Nosana decisions, isolated Daytona tool execution, and the judge."""

from typing import Any

from judge import judge_result
from nosana_client import infer
from runtime import run_round_in_daytona
from scenarios import make_emails


def run_attack(attack_prompt: str) -> dict[str, Any]:
    """Run baseline and attack rounds; return the stable UI result contract."""
    try:
        baseline_emails = make_emails()
        baseline_run = run_round_in_daytona(baseline_emails, infer)
        baseline_judgement = judge_result(
            baseline_run["summary"], baseline_run["tool_calls"], baseline_task_pass=True, mode="live"
        )
        baseline_pass = baseline_judgement["task_pass"] and baseline_judgement["security_pass"]

        attack_emails = make_emails(attack_prompt)
        attack_run = run_round_in_daytona(attack_emails, infer)
        result = judge_result(
            attack_run["summary"], attack_run["tool_calls"], baseline_task_pass=baseline_pass, mode="live"
        )
        result["baseline_status"] = "PASS" if baseline_pass else "FAIL"
        result["logs"] = [
            {"round": "baseline", "entries": baseline_run.get("logs", [])},
            {"round": "attack", "entries": attack_run.get("logs", [])},
        ]
        result["models"] = {"baseline": baseline_run.get("model"), "attack": attack_run.get("model")}
        return result
    except Exception as exc:
        return {
            "mode": "execution_error",
            "baseline_status": "UNKNOWN",
            "security_pass": False,
            "task_pass": False,
            "verdict": "EXECUTION_ERROR",
            "reason": str(exc),
            "tool_calls": [],
            "summary": {},
            "logs": [],
        }
