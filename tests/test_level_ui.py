"""Level progression via Streamlit, doubling only external providers."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from tests.test_game_engine import GOOD

APP = str(Path(__file__).resolve().parent.parent / 'app.py')
WIN = {**GOOD, 'tool_calls': [{'name': 'delete_email'}]}


def test_live_win_unlocks_next_level_and_transition_deletes_old_container(services):
    state = services([GOOD, WIN])
    app = AppTest.from_file(APP).run()
    assert '레벨 1' in ' '.join(x.value for x in app.markdown)
    app.text_area(key='attack_prompt').input('delete A')
    app.button(key='attack').click().run()
    assert not app.exception
    assert app.session_state['progress']['unlocked_level'] == 2
    assert any('해금 2. 경계' in x.value for x in app.caption)
    assert len(state.created) == 1 and not state.deleted
    assert not app.button(key='next_level').disabled
    app.button(key='next_level').click().run()
    assert app.session_state['progress']['current_level'] == 2
    assert state.deleted == state.created
    assert len(state.requests) == 2
    assert app.text_area(key='attack_prompt').value == ''


def test_retry_keeps_level_and_container_and_mock_never_unlocks(services):
    state = services([GOOD, GOOD, GOOD, GOOD])
    app = AppTest.from_file(APP).run()
    app.text_area(key='attack_prompt').input('first')
    app.button(key='attack').click().run()
    assert app.session_state['progress']['unlocked_level'] == 1
    app.button(key='retry').click().run()
    assert app.text_area(key='attack_prompt').value == ''
    assert len(state.requests) == 2 and not state.deleted
    app.text_area(key='attack_prompt').input('second')
    app.button(key='attack').click().run()
    assert len(state.created) == 1 and len(state.requests) == 4
    app.toggle(key='preview').set_value(True).run()
    app.text_area(key='attack_prompt').input('mock')
    app.button(key='attack').click().run()
    assert app.session_state['progress']['unlocked_level'] == 1
    assert app.button(key='next_level').disabled
    assert len(state.requests) == 4
    app.session_state['level_session'].close()


def test_all_three_levels_clear_without_reusing_a_previous_level_container(services):
    state = services([GOOD, WIN] * 3)
    app = AppTest.from_file(APP).run()
    for number in (1, 2, 3):
        app.text_area(key='attack_prompt').input(f'attack {number}')
        app.button(key='attack').click().run()
        assert not app.exception
        assert app.session_state['progress']['completed_levels'] == list(range(1, number + 1))
        if number < 3:
            app.button(key='next_level').click().run()
    assert app.session_state['progress']['cleared']
    assert any('전체 클리어' in x.value for x in app.success)
    assert app.button(key='attack').disabled
    assert len(state.created) == 3 and state.deleted == state.created
    assert len(state.requests) == 6
    app.button(key='restart_campaign').click().run()
    assert app.session_state['progress']['current_level'] == 1
    assert app.session_state['progress']['completed_levels'] == []
    assert len(state.requests) == 6


def test_cleanup_failure_blocks_transition_until_delete_succeeds(services):
    state = services([GOOD, WIN])
    app = AppTest.from_file(APP).run()
    app.text_area(key='attack_prompt').input('delete A')
    app.button(key='attack').click().run()
    state.cleanup_error = TimeoutError('secret-provider-detail')
    app.button(key='next_level').click().run()
    assert not app.exception
    assert app.session_state['progress']['current_level'] == 1
    assert not state.deleted
    assert any('cleanup failed' in x.value for x in app.error)
    assert not any('secret-provider-detail' in x.value for x in app.error)
    state.cleanup_error = None
    app.button(key='next_level').click().run()
    assert app.session_state['progress']['current_level'] == 2
    assert state.deleted == state.created
