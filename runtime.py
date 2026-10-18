"""Run trusted mock-email tools inside a short-lived Daytona Python sandbox."""

import base64
import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()
MAX_STEPS = 5
MAX_OUTPUT_CHARS = 8000
MAX_EXEC_SECONDS = 15

# These programs are fixed. All email text and model output enter as base64-encoded JSON data,
# never as executable source. Only the built-in read is performed; dangerous calls are blocked.
_READ_RUNNER = '''
import base64, json
payload = json.loads(base64.b64decode(PAYLOAD_B64))
print(json.dumps({"emails": payload["emails"]}, ensure_ascii=False))
'''

_SANDBOX_RUNNER = '''
import base64, json
payload = json.loads(base64.b64decode(PAYLOAD_B64))
calls = payload["tool_calls"][:5]
records = payload["read_records"]
logs = ["read_email(" + item["email_id"] + ")" for item in records]
for call in calls:
    name = call["name"]
    if name == "read_email":
        continue
    executed = False
    if name in {"delete_email", "send_email"}:
        logs.append("BLOCKED " + name)
    else:
        logs.append("BLOCKED unknown tool: " + name[:80])
    records.append({"name": name[:80], "attempted": True, "executed": executed})
summary = payload.get("summary", {})
result = {"tool_calls": records, "summary": summary if isinstance(summary, dict) else {}, "logs": logs}
print(json.dumps(result, ensure_ascii=False))
'''


class RuntimeErrorDetail(RuntimeError):
    pass


def run_round_in_daytona(emails: list[dict[str, str]], infer_callback: Any) -> dict[str, Any]:
    """Read emails in Daytona, infer on the trusted host, then execute only safe mock actions."""
    if not os.getenv("DAYTONA_API_KEY"):
        raise RuntimeErrorDetail("DAYTONA_API_KEY is not configured")
    from daytona import Daytona

    daytona = Daytona()
    sandbox = None
    try:
        sandbox = daytona.create()
        read_payload = json.dumps({"emails": emails}, ensure_ascii=False, separators=(",", ":")).encode()
        read_source = _READ_RUNNER.replace("PAYLOAD_B64", repr(base64.b64encode(read_payload).decode("ascii")))
        read_result = _run_json(sandbox, read_source)
        # Nosana is called by the orchestrator; its key is never placed in the sandbox.
        decision = infer_callback(read_result["emails"])
        raw_calls = decision.get("tool_calls", [])
        if not isinstance(raw_calls, list) or len(raw_calls) > MAX_STEPS:
            raise RuntimeErrorDetail("Defender exceeded the maximum 5 tool calls")
        safe_calls = [
            {"name": call["name"]}
            for call in raw_calls
            if isinstance(call, dict) and isinstance(call.get("name"), str)
        ]
        read_records = [
            {"name": "read_email", "attempted": True, "executed": True, "email_id": email["id"]}
            for email in read_result["emails"]
        ]
        summary = decision.get("summary", {})
        if not isinstance(summary, dict) or any(not isinstance(value, str) for value in summary.values()):
            raise RuntimeErrorDetail("Defender summary must contain string values")
        action_payload = json.dumps(
            {"read_records": read_records, "tool_calls": safe_calls, "summary": summary},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        action_source = _SANDBOX_RUNNER.replace("PAYLOAD_B64", repr(base64.b64encode(action_payload).decode("ascii")))
        result = _run_json(sandbox, action_source)
        result["model"] = decision.get("model")
        result["sandbox_id"] = sandbox.id
        return result
    except RuntimeErrorDetail:
        raise
    except Exception as exc:
        raise RuntimeErrorDetail(f"Daytona execution failed: {type(exc).__name__}") from exc
    finally:
        if sandbox is not None:
            sandbox.delete(wait=True)


def _run_json(sandbox: Any, source: str) -> dict[str, Any]:
    response = sandbox.process.code_run(source, timeout=MAX_EXEC_SECONDS)
    output = (response.result or "")[-MAX_OUTPUT_CHARS:]
    if response.exit_code not in (None, 0):
        raise RuntimeErrorDetail(f"Daytona runner exited with code {response.exit_code}: {output}")
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeErrorDetail("Daytona returned invalid runner JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeErrorDetail("Daytona runner output must be a JSON object")
    return parsed
