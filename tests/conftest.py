"""External-service doubles; execute the trusted runner locally, never contact APIs."""
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def services(monkeypatch):
    def configure(decisions):
        state = SimpleNamespace(created=[], deleted=[], requests=[], decisions=iter(decisions))

        class Process:
            def code_run(self, source, timeout):
                process = subprocess.run(
                    [sys.executable, "-I", "-c", source],
                    capture_output=True, text=True, timeout=timeout,
                )
                return SimpleNamespace(result=process.stdout, exit_code=process.returncode)

        class Sandbox:
            def __init__(self):
                self.id = f"test-sandbox-{len(state.created)}"
                self.process = Process()
                state.created.append(self.id)

            def delete(self, wait=False, timeout=None):
                state.deleted.append(self.id)

        import daytona
        import nosana_client
        monkeypatch.setattr(daytona, "Daytona", lambda: SimpleNamespace(create=lambda **kwargs: Sandbox()))

        def completion(**kwargs):
            state.requests.append(kwargs)
            decision = next(state.decisions)
            if isinstance(decision, Exception):
                raise decision
            content = decision if isinstance(decision, str) else json.dumps(decision, ensure_ascii=False)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

        monkeypatch.setattr(nosana_client, "OpenAI", lambda **kwargs: SimpleNamespace(
            close=lambda: None,
            models=SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id="test-model")])),
            chat=SimpleNamespace(completions=SimpleNamespace(create=completion)),
        ))
        monkeypatch.setenv("DAYTONA_API_KEY", "test-only")
        monkeypatch.setenv("NOSANA_API_KEY", "test-only")
        monkeypatch.delenv("NOSANA_MODEL", raising=False)
        monkeypatch.delenv("NOSANA_BASE_URL", raising=False)
        monkeypatch.delenv("NOSANA_ENDPOINT_KEY", raising=False)
        return state
    return configure
