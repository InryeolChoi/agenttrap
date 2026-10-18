import json


def test_daytona_hello_uses_no_nosana_and_cleans_up(services):
    from runtime import hello_world
    state = services([])
    result = hello_world()
    assert result["message"] == "Hello World"
    assert result["python"]
    assert state.requests == []
    assert len(state.created) == 1
    assert state.created == state.deleted


def test_cli_will_not_start_paid_execution_without_live_flag(services, capsys):
    from agenttrap import main
    state = services([])
    assert main(["hello"]) == 1
    assert json.loads(capsys.readouterr().out)["verdict"] == "EXECUTION_ERROR"
    assert state.created == []


def test_cli_check_never_discloses_credentials(services, capsys):
    from agenttrap import main
    state = services([])
    assert main(["check"]) == 0
    output = capsys.readouterr().out
    assert "test-only" not in output
    assert json.loads(output)["ready"] is True
    assert state.created == []
    assert state.requests == []
