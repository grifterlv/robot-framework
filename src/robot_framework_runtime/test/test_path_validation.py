"""Check numeric rejection and normal behavior of the path validators."""

from copy import deepcopy

import pytest

from robot_framework_runtime.path_validation import (
    reorder_point,
    validate_geometric_path,
    validate_timed_path,
    validate_times,
)


@pytest.mark.parametrize('value', [10**400, -(10**400)])
def test_reorder_point_rejects_unrepresentable_integer(value):
    """Oversized positions must use the normal input-rejection exception."""
    with pytest.raises(ValueError):
        reorder_point([value, 0], ['b', 'a'], ['a', 'b'])


@pytest.mark.parametrize('value', [10**400, -(10**400)])
def test_validate_times_rejects_unrepresentable_integer(value):
    """Oversized times must use the normal input-rejection exception."""
    with pytest.raises(ValueError):
        validate_times([0, value], 2)


@pytest.fixture
def named_path():
    """Provide matching metadata with source names in reversed order."""
    model = {
        'model_id': 'test', 'model_version': '1',
        'joint_names': ['a', 'b'],
        'joint_types': {'a': 'revolute', 'b': 'revolute'},
    }
    path = {
        'model_id': 'test', 'model_version': '1',
        'joint_names': ['b', 'a'], 'units': {'a': 'rad', 'b': 'rad'},
        'points': [[-2, 1], [0.5, 3]], 'times': None,
    }
    return path, model


@pytest.mark.parametrize('timed', [False, True])
def test_path_entries_reject_unrepresentable_position(named_path, timed):
    """Both public path validators reject oversized point coordinates."""
    path, model = named_path
    path['points'][1][0] = 10**400
    if timed:
        path['times'] = [0, 1]
        validate = validate_timed_path
    else:
        validate = validate_geometric_path
    with pytest.raises(ValueError):
        validate(path, model)


def test_timed_path_rejects_unrepresentable_time(named_path):
    """The timed-path entry preserves the helper's rejection contract."""
    path, model = named_path
    path['times'] = [0, 10**400]
    with pytest.raises(ValueError):
        validate_timed_path(path, model)


@pytest.mark.parametrize('timed', [False, True])
def test_normal_paths_preserve_reordering_and_inputs(named_path, timed):
    """Normal integers, negative positions and time zero remain valid."""
    path, model = named_path
    if timed:
        path['times'] = [0, 1.25]
    before = deepcopy((path, model))
    validate = validate_timed_path if timed else validate_geometric_path
    result = validate(path, model)
    assert result['points'] == [[1, -2], [3, 0.5]]
    assert isinstance(result['points'][0][0], int)
    assert result['times'] == ([0.0, 1.25] if timed else None)
    assert (path, model) == before


@pytest.mark.parametrize(
    'value', [True, float('nan'), float('inf'), float('-inf')],
)
def test_invalid_numeric_values_still_rejected(value):
    """Overflow handling must not accept booleans or nonfinite floats."""
    with pytest.raises(ValueError):
        reorder_point([value], ['a'], ['a'])
    with pytest.raises(ValueError):
        validate_times([0, value], 2)


@pytest.mark.parametrize('times', [[-1, 0], [0, 0], [1, 0]])
def test_invalid_time_order_still_rejected(times):
    """Nonnegative start and strict time ordering remain required."""
    with pytest.raises(ValueError):
        validate_times(times, 2)
