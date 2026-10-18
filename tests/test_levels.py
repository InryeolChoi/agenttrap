"""Campaign progression through the public policy interface."""
from levels import new_progress, apply_result


def test_live_attacker_win_unlocks_next_level_without_skipping_current():
    original = new_progress()
    updated = apply_result(original, {
        'level_id': 1, 'mode': 'live', 'baseline_status': 'PASS', 'verdict': 'ATTACKER_WINS',
    })
    assert updated == {'current_level': 1, 'unlocked_level': 2, 'completed_levels': [1], 'cleared': False}
    assert original == {'current_level': 1, 'unlocked_level': 1, 'completed_levels': [], 'cleared': False}


import pytest


@pytest.mark.parametrize('change', [
    {'mode': 'mock'}, {'mode': 'partial'}, {'verdict': 'DEFENDER_WINS'},
    {'verdict': 'INVALID_TEST'}, {'verdict': 'EXECUTION_ERROR'},
    {'baseline_status': 'FAIL'}, {'level_id': 2},
])
def test_unqualified_results_do_not_unlock(change):
    state = new_progress()
    result = {'level_id': 1, 'mode': 'live', 'baseline_status': 'PASS', 'verdict': 'ATTACKER_WINS', **change}
    assert apply_result(state, result) == state


def test_next_level_requires_completion_and_final_win_clears_campaign():
    from levels import advance_level
    state = new_progress()
    with pytest.raises(ValueError, match='complete'):
        advance_level(state)
    for level in (1, 2, 3):
        result = {'level_id': level, 'mode': 'live', 'baseline_status': 'PASS', 'verdict': 'ATTACKER_WINS'}
        state = apply_result(state, result)
        assert apply_result(state, result) == state
        if level < 3:
            state = advance_level(state)
            assert state['current_level'] == level + 1
    assert state['cleared'] is True
    assert state['completed_levels'] == [1, 2, 3]
    with pytest.raises(ValueError):
        advance_level(state)
