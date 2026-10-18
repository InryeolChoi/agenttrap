"""Public contract tests for the Nosana adapter using an OpenAI SDK double."""

import json
from types import SimpleNamespace

import pytest

import nosana_client


class FakeClient:
    def __init__(self, *, models=None, response=None, inference_error=None, close_error=None):
        self.models = SimpleNamespace(list=lambda: SimpleNamespace(data=models or []))
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.response = response
        self.inference_error = inference_error
        self.close_error = close_error
        self.closed = False
        self.create_kwargs = None

    def _create(self, **kwargs):
        self.create_kwargs = kwargs
        if self.inference_error:
            raise self.inference_error
        return self.response

    def close(self):
        self.closed = True
        if self.close_error:
            raise self.close_error


def install_client(monkeypatch, client):
    captured = {}

    def make_client(**kwargs):
        captured.update(kwargs)
        return client

    monkeypatch.setenv("NOSANA_API_KEY", "secret-test-key")
    monkeypatch.delenv("NOSANA_BASE_URL", raising=False)
    monkeypatch.delenv("NOSANA_ENDPOINT_KEY", raising=False)
    monkeypatch.setattr(nosana_client, "OpenAI", make_client)
    return captured


def response_with(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_infer_uses_configured_model_parses_response_and_closes(monkeypatch):
    payload = {"action": "summarize", "tool_calls": [], "summary": {"meeting": "월요일 10시"}}
    client = FakeClient(response=response_with(json.dumps(payload, ensure_ascii=False)))
    captured = install_client(monkeypatch, client)

    result = nosana_client.infer([{"body": "mail"}], model="configured-model")

    assert result == {**payload, "model": "configured-model"}
    assert client.create_kwargs["model"] == "configured-model"
    assert captured["api_key"] == "secret-test-key"
    assert client.closed


def test_infer_discovers_first_available_model_and_closes(monkeypatch):
    payload = {"tool_calls": [], "summary": {}}
    client = FakeClient(models=[SimpleNamespace(id="first-model")], response=response_with(json.dumps(payload)))
    install_client(monkeypatch, client)
    monkeypatch.delenv("NOSANA_MODEL", raising=False)

    result = nosana_client.infer([])

    assert result["model"] == "first-model"
    assert client.create_kwargs["model"] == "first-model"
    assert client.closed


def test_infer_rejects_empty_output_without_echoing_response(monkeypatch):
    client = FakeClient(response=response_with(""))
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError, match="invalid JSON") as error:
        nosana_client.infer([], model="model")

    assert "secret-test-key" not in str(error.value)
    assert client.closed


def test_list_models_validates_discovered_ids_and_closes(monkeypatch):
    client = FakeClient(models=[SimpleNamespace(id="good"), SimpleNamespace(id=None)])
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError, match="invalid model"):
        nosana_client.list_models()

    assert client.closed


def test_inference_failure_is_preserved_when_close_fails_with_sanitized_note(monkeypatch):
    client = FakeClient(
        inference_error=RuntimeError("request failed with secret-test-key"),
        close_error=RuntimeError("cleanup exposed secret-test-key"),
    )
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError) as error:
        nosana_client.infer([], model="model")

    message = str(error.value)
    assert "Nosana inference failed: RuntimeError" in message
    assert "client cleanup also failed" in message
    assert "secret-test-key" not in message
    assert "request failed" not in message
    assert "cleanup exposed" not in message
    assert client.closed


def test_inference_failure_is_sanitized_and_client_closes(monkeypatch):
    client = FakeClient(inference_error=RuntimeError("secret-test-key and provider detail"))
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError, match="Nosana inference failed: RuntimeError") as error:
        nosana_client.infer([], model="model")

    assert "secret-test-key" not in str(error.value)
    assert "provider detail" not in str(error.value)
    assert client.closed


def test_model_discovery_failure_is_sanitized_and_client_closes(monkeypatch):
    client = FakeClient()
    client.models = SimpleNamespace(list=lambda: (_ for _ in ()).throw(RuntimeError("secret-test-key")))
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError, match="Nosana model discovery failed: RuntimeError") as error:
        nosana_client.list_models()

    assert "secret-test-key" not in str(error.value)
    assert client.closed


def test_infer_rejects_malformed_model_output_and_closes(monkeypatch):
    client = FakeClient(response=response_with('{"tool_calls": "not-an-array", "summary": {}}'))
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError, match="tool_calls array"):
        nosana_client.infer([], model="model")

    assert client.closed


def test_infer_reports_empty_model_discovery_and_closes(monkeypatch):
    client = FakeClient(models=[])
    install_client(monkeypatch, client)
    monkeypatch.delenv("NOSANA_MODEL", raising=False)

    with pytest.raises(nosana_client.NosanaError, match="no currently served models"):
        nosana_client.infer([])

    assert client.closed


def test_infer_disables_thinking_and_uses_default_endpoint(monkeypatch):
    client = FakeClient(response=response_with(json.dumps({"tool_calls": [], "summary": {}})))
    captured = install_client(monkeypatch, client)

    nosana_client.infer([], model="model")

    assert captured["base_url"] == nosana_client.BASE_URL
    assert client.create_kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert client.create_kwargs["max_tokens"] >= 1000


def test_custom_deployment_never_receives_account_key(monkeypatch):
    client = FakeClient(response=response_with(json.dumps({"tool_calls": [], "summary": {}})))
    captured = install_client(monkeypatch, client)
    monkeypatch.setenv("NOSANA_BASE_URL", "https://job.node.k8s.prd.nos.ci/v1")

    nosana_client.infer([], model="glm")
    assert captured["base_url"] == "https://job.node.k8s.prd.nos.ci/v1"
    assert captured["api_key"] != "secret-test-key"

    monkeypatch.setenv("NOSANA_ENDPOINT_KEY", "endpoint-key")
    nosana_client.infer([], model="glm")
    assert captured["api_key"] == "endpoint-key"


def test_custom_deployment_requires_https(monkeypatch):
    install_client(monkeypatch, FakeClient())
    monkeypatch.setenv("NOSANA_BASE_URL", "http://job.node.k8s.prd.nos.ci/v1")

    with pytest.raises(nosana_client.NosanaError, match="https"):
        nosana_client.infer([], model="glm")


def test_discovery_skips_embedding_models(monkeypatch):
    client = FakeClient(
        models=[SimpleNamespace(id="nvidia/nemotron-3-embed-1b"), SimpleNamespace(id="qwen/chat")],
        response=response_with(json.dumps({"tool_calls": [], "summary": {}})),
    )
    install_client(monkeypatch, client)
    monkeypatch.delenv("NOSANA_MODEL", raising=False)

    assert nosana_client.infer([])["model"] == "qwen/chat"


def test_discovery_with_only_embedding_models_is_an_error(monkeypatch):
    client = FakeClient(models=[SimpleNamespace(id="text-embed")])
    install_client(monkeypatch, client)
    monkeypatch.delenv("NOSANA_MODEL", raising=False)

    with pytest.raises(nosana_client.NosanaError, match="chat models"):
        nosana_client.infer([])
    assert client.closed


def test_truncated_empty_response_reports_token_limit(monkeypatch):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=""), finish_reason="length")])
    client = FakeClient(response=response)
    install_client(monkeypatch, client)

    with pytest.raises(nosana_client.NosanaError, match="token limit"):
        nosana_client.infer([], model="model")
    assert client.closed
