"""Public level session lifecycle, doubled only at provider boundaries."""
from game_engine import run_attack
from tests.test_game_engine import GOOD


def test_level_retries_reuse_one_container_and_close_deletes_it(services):
    from runtime import LevelSession
    state = services([GOOD, GOOD, GOOD, GOOD])
    session = LevelSession(1)
    first = run_attack('first', level_id=1, session=session)
    second = run_attack('second', level_id=1, session=session)
    assert first['verdict'] == second['verdict'] == 'DEFENDER_WINS'
    assert first['level_id'] == second['level_id'] == 1
    assert len(state.created) == 1
    assert state.deleted == []
    assert {row['sandbox_id'] for result in [first, second] for row in result['logs']} == {state.created[0]}
    assert len(state.requests) == 4
    assert state.requests[1]['messages'][1]['content'].endswith('first"}]')
    assert 'first' not in state.requests[3]['messages'][1]['content']
    session.close()
    session.close()
    assert state.deleted == state.created


def test_each_level_uses_same_defense_for_baseline_and_attack(services):
    state = services([GOOD, GOOD] * 3)
    for level_id in (1, 2, 3):
        assert run_attack('attack', level_id=level_id)['level_id'] == level_id
    prompts = [request['messages'][0]['content'] for request in state.requests]
    assert prompts[0] == prompts[1]
    assert prompts[2] == prompts[3]
    assert prompts[4] == prompts[5]
    assert len(set(prompts)) == 3
    assert 'untrusted' not in prompts[0]
    assert 'untrusted' in prompts[2]
    assert 'Never perform delete_email or send_email' in prompts[4]
    assert state.created == state.deleted


def test_invalid_level_or_session_mismatch_never_calls_services(services):
    from runtime import LevelSession
    state = services([])
    for level_id in (0, 4, True, '1'):
        assert run_attack('attack', level_id=level_id)['verdict'] == 'EXECUTION_ERROR'
    session = LevelSession(1)
    assert run_attack('attack', level_id=2, session=session)['verdict'] == 'EXECUTION_ERROR'
    assert not state.created and not state.requests
    session.close()


def test_expired_session_closes_without_another_inference(services, monkeypatch):
    from runtime import LevelSession
    import runtime
    clock = [0]
    monkeypatch.setattr(runtime.time, 'monotonic', lambda: clock[0])
    state = services([GOOD, GOOD])
    session = LevelSession(1)
    assert run_attack('one', level_id=1, session=session)['verdict'] == 'DEFENDER_WINS'
    clock[0] = 241
    result = run_attack('two', level_id=1, session=session)
    assert result['verdict'] == 'EXECUTION_ERROR'
    assert 'expired' in result['reason']
    assert len(state.requests) == 2 and state.deleted == state.created


def test_provider_error_closes_level_container_and_preserves_error(services):
    from runtime import LevelSession
    state = services([GOOD, RuntimeError('provider secret')])
    session = LevelSession(1)
    result = run_attack('one', level_id=1, session=session)
    assert result['verdict'] == 'EXECUTION_ERROR'
    assert result['baseline_status'] == 'PASS'
    assert 'provider secret' not in result['reason']
    assert state.deleted == state.created and session.closed


def test_failed_cleanup_is_visible_and_can_be_retried_without_losing_sandbox(services):
    import pytest
    from runtime import LevelSession, RuntimeErrorDetail
    state = services([GOOD, GOOD])
    session = LevelSession(1)
    run_attack('one', level_id=1, session=session)
    state.cleanup_error = TimeoutError('secret')
    with pytest.raises(RuntimeErrorDetail, match='cleanup failed: TimeoutError'):
        session.close()
    assert session.failed and not session.closed
    assert not state.deleted
    state.cleanup_error = None
    session.close()
    assert session.closed and state.deleted == state.created


def test_intro_defender_knows_tool_protocol_without_security_guard(services):
    state = services([GOOD, GOOD])
    run_attack('attack', level_id=1)
    prompt = state.requests[0]['messages'][0]['content']
    assert 'Do not invent tool names' in prompt
    assert 'put the complete summary directly in summary' in prompt
    assert 'Never perform' not in prompt


def test_already_deleted_container_can_close_after_server_ttl(services):
    from daytona import DaytonaNotFoundError
    from runtime import LevelSession
    state = services([GOOD, GOOD])
    session = LevelSession(1)
    run_attack('one', level_id=1, session=session)
    state.cleanup_error = DaytonaNotFoundError('Sandbox no longer exists')
    session.close()
    assert session.closed
