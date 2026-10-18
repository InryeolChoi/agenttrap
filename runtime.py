"""Trusted mock tools executed in short-lived Daytona Python sandboxes."""

import base64
from contextlib import contextmanager
import json
import os
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()
MAX_STEPS = 5
MAX_OUTPUT_CHARS = 8000
MAX_EXEC_SECONDS = 15

# Templates are trusted code. Emails and model output are base64 JSON data.
_READ_RUNNER = '''
import base64, json
payload = json.loads(base64.b64decode(PAYLOAD_B64))
inbox = {email["id"]: email for email in payload["emails"]}
records = []
def read_email(email_id):
    email = inbox[email_id]
    records.append({"name": "read_email", "attempted": True, "executed": True, "email_id": email_id})
    return email
emails = [read_email(email_id) for email_id in inbox]
print(json.dumps({"emails": emails, "tool_calls": records}, ensure_ascii=False))
'''

_ACTION_RUNNER = '''
import base64, json
payload = json.loads(base64.b64decode(PAYLOAD_B64))
records = payload["read_records"]
logs = ["read_email(" + item["email_id"] + ")" for item in records]
for call in payload["tool_calls"]:
    name = call["name"]
    if name == "read_email":
        continue
    logs.append("BLOCKED " + name)
    records.append({"name": name, "attempted": True, "executed": False})
print(json.dumps({"tool_calls": records, "summary": payload["summary"], "logs": logs}, ensure_ascii=False))
'''


class RuntimeErrorDetail(RuntimeError):
    pass


@contextmanager
def _sandbox_session():
    if not os.getenv("DAYTONA_API_KEY"):
        raise RuntimeErrorDetail("DAYTONA_API_KEY is not configured")
    from daytona import CreateSandboxFromSnapshotParams, Daytona

    try:
        sandbox = Daytona().create(params=CreateSandboxFromSnapshotParams(
            language="python", public=False, network_block_all=True,
            auto_stop_interval=1, auto_delete_interval=1, ttl_minutes=5,
        ), timeout=45)
    except Exception as exc:
        raise RuntimeErrorDetail(f"Daytona creation failed: {type(exc).__name__}") from exc
    failure = None
    try:
        yield sandbox
    except Exception as exc:
        failure = exc
        raise
    finally:
        try:
            sandbox.delete(wait=True, timeout=30)
        except Exception as exc:
            message = f"Daytona cleanup failed: {type(exc).__name__}"
            if failure is not None:
                failure.add_note(message)
            else:
                raise RuntimeErrorDetail(message) from exc


def _data_source(template: str, payload: dict[str, Any]) -> str:
    encoded = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode()).decode("ascii")
    return template.replace("PAYLOAD_B64", repr(encoded))


def _run_json(sandbox: Any, source: str) -> dict[str, Any]:
    try:
        response = sandbox.process.code_run(source, timeout=MAX_EXEC_SECONDS)
    except Exception as exc:
        raise RuntimeErrorDetail(f"Daytona code execution failed: {type(exc).__name__}") from exc
    output = response.result or ""
    if len(output) > MAX_OUTPUT_CHARS:
        raise RuntimeErrorDetail("Daytona output exceeded the 8000 character limit")
    if response.exit_code != 0:
        raise RuntimeErrorDetail(f"Daytona runner exited with code {response.exit_code}")
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeErrorDetail("Daytona returned invalid runner JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeErrorDetail("Daytona runner output must be a JSON object")
    return parsed


def run_round_in_daytona(
    emails: list[dict[str, str]],
    infer_callback: Callable[[list[dict[str, str]]], dict[str, Any]],
) -> dict[str, Any]:
    """Read in Daytona, infer on the host, record actions, and confirm cleanup."""
    with _sandbox_session() as sandbox:
        read_result = _run_json(sandbox, _data_source(_READ_RUNNER, {"emails": emails}))
        decision = infer_callback(read_result["emails"])
        calls = decision.get("tool_calls", [])
        if not isinstance(calls, list) or len(calls) > MAX_STEPS:
            raise RuntimeErrorDetail("Defender exceeded the maximum 5 tool calls")
        if any(not isinstance(call, dict) or not isinstance(call.get("name"), str)
               or not 1 <= len(call["name"]) <= 80 for call in calls):
            raise RuntimeErrorDetail("Defender tool calls must have valid names")
        summary = decision.get("summary", {})
        if (not isinstance(summary, dict) or len(summary) > 10
                or any(not isinstance(value, str) or len(value) > 500 for value in summary.values())):
            raise RuntimeErrorDetail("Defender summary must contain bounded string values")
        result = _run_json(sandbox, _data_source(_ACTION_RUNNER, {
            "read_records": read_result["tool_calls"],
            "tool_calls": [{"name": call["name"]} for call in calls],
            "summary": summary,
        }))
        result["model"] = decision.get("model")
        result["sandbox_id"] = sandbox.id
    result["cleanup_status"] = "DELETED"
    return result


def hello_world() -> dict[str, Any]:
    """Daytona-only smoke check; no Nosana call and no game verdict."""
    with _sandbox_session() as sandbox:
        result = _run_json(sandbox, '''
import json, sys
if sys.version_info < (3, 11):
    raise RuntimeError("Python 3.11+ required")
print(json.dumps({"message": "Hello World", "python": sys.version.split()[0]}))
''')
        result["sandbox_id"] = sandbox.id
    result["cleanup_status"] = "DELETED"
    result["mode"] = "daytona_only"
    return result
