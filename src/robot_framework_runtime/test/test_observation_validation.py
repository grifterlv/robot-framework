"""Exercise observation validation using standard ROS messages without a node."""

from copy import deepcopy

from builtin_interfaces.msg import Time
from geometry_msgs.msg import Point, Quaternion, Transform, TransformStamped, Vector3
from shape_msgs.msg import Mesh, MeshTriangle
from std_msgs.msg import Header
import pytest

from robot_framework_runtime.contracts import RequestContext
from robot_framework_runtime.observation_frames import (
    make_observation_frame,
    validate_capture_time,
    validate_capture_transform,
    validate_mesh,
    validate_observation_metadata,
)


def _header(frame='camera', sec=42, nanosec=123):
    # Disable generated-message checks so the application validator is tested.
    return Header(
        frame_id=frame,
        stamp=Time(sec=sec, nanosec=nanosec, check_fields=False),
        check_fields=False,
    )


def _transform(source='camera', target='world', sec=42, nanosec=123):
    return TransformStamped(
        header=_header(target, sec, nanosec),
        child_frame_id=source,
        transform=Transform(
            translation=Vector3(check_fields=False),
            rotation=Quaternion(w=1.0, check_fields=False),
            check_fields=False,
        ),
        check_fields=False,
    )


def _mesh():
    return Mesh(
        vertices=[Point(), Point(x=1.0), Point(y=1.0)],
        triangles=[MeshTriangle(vertex_indices=[0, 1, 2])],
    )


def _factory_inputs():
    return {
        'context': RequestContext('request', 'task', 'session', 'model', '1'),
        'mesh': _mesh(),
        'header': _header(),
        'length_unit': 'm',
        'sample_clock_domain': 'ros',
        'source': 'camera',
        'model': {'model_id': 'model', 'model_version': '1'},
        'active_session_id': 'session',
    }


@pytest.mark.parametrize('component', ['translation', 'rotation'])
@pytest.mark.parametrize('magnitude', [1.0, 1e-12], ids=['large', 'tiny'])
def test_same_frame_requires_identity(component, magnitude):
    """A coordinate frame cannot be offset or rotated relative to itself."""
    transform = _transform(source='world')
    if component == 'translation':
        transform.transform.translation.x = magnitude
    else:
        transform.transform.rotation = Quaternion(
            z=magnitude, w=0.0 if magnitude == 1.0 else 1.0, check_fields=False,
        )

    with pytest.raises(ValueError):
        validate_capture_transform(transform, 'world', 'world')

    inputs = _factory_inputs()
    inputs.update(
        header=_header('world'), capture_transform=transform,
        target_frame_id='world', transform_clock_domain='ros',
    )
    with pytest.raises(ValueError):
        make_observation_frame(**inputs)


@pytest.mark.parametrize('sign', [1.0, -1.0])
def test_same_frame_identity_accepts_both_quaternion_signs(sign):
    """Equivalent identity quaternions remain valid and are not rewritten."""
    transform = _transform(source='world')
    transform.transform.rotation.w = sign
    before = deepcopy(transform)
    assert validate_capture_transform(transform, 'world', 'world') is None
    inputs = _factory_inputs()
    inputs.update(
        header=_header('world'), capture_transform=transform,
        target_frame_id='world', transform_clock_domain='ros',
    )
    frame = make_observation_frame(**inputs)
    assert frame.capture_transform.transform.rotation.w == sign
    assert transform == before


@pytest.mark.parametrize('axis', ['x', 'y', 'z'])
@pytest.mark.parametrize('value', [10**400, -(10**400)], ids=['positive', 'negative'])
def test_mesh_unrepresentable_coordinates_raise_value_error(axis, value):
    """Oversized integer coordinates use the normal rejection exception."""
    vertex = Point(check_fields=False)
    setattr(vertex, axis, value)
    mesh = Mesh(vertices=[vertex])
    with pytest.raises(ValueError):
        validate_mesh(mesh)
    assert getattr(vertex, axis) == value


@pytest.mark.parametrize('component,axis', [
    ('translation', 'x'), ('translation', 'y'), ('translation', 'z'),
    ('rotation', 'x'), ('rotation', 'y'), ('rotation', 'z'), ('rotation', 'w'),
])
@pytest.mark.parametrize('value', [10**400, -(10**400)], ids=['positive', 'negative'])
def test_transform_unrepresentable_components_raise_value_error(component, axis, value):
    """Every transform component rejects overflow without changing the input."""
    transform = _transform()
    part = getattr(transform.transform, component)
    setattr(part, axis, value)
    with pytest.raises(ValueError):
        validate_capture_transform(transform, 'camera', 'world')
    assert getattr(part, axis) == value


@pytest.mark.parametrize('payload', ['mesh', 'translation', 'rotation'])
def test_factory_preserves_value_error_for_unrepresentable_payload(payload):
    """Copying a payload does not bypass the validators or leak OverflowError."""
    inputs = _factory_inputs()
    if payload == 'mesh':
        inputs['mesh'] = Mesh(vertices=[Point(x=10**400, check_fields=False)])
    else:
        transform = _transform()
        setattr(getattr(transform.transform, payload), 'x', 10**400)
        inputs.update(
            capture_transform=transform, target_frame_id='world',
            transform_clock_domain='ros',
        )
    with pytest.raises(ValueError):
        make_observation_frame(**inputs)


@pytest.mark.parametrize('stamp', [None, 'invalid', {'sec': 42, 'nanosec': 123}])
def test_metadata_requires_a_time_message(stamp):
    """Malformed nested stamps are rejected before accessing their fields."""
    header = Header(frame_id='camera', stamp=stamp, check_fields=False)
    with pytest.raises(ValueError):
        validate_observation_metadata(header, 'm', 'ros')


@pytest.mark.parametrize('sec', [
    True, False, 1.5, '42', None, -(2**31) - 1, 2**31, 10**400, -(10**400),
], ids=['true', 'false', 'float', 'string', 'none', 'below', 'above', 'huge', 'negative-huge'])
def test_metadata_requires_non_boolean_int32_seconds(sec):
    """Equal-looking values cannot replace the ROS Time signed integer field."""
    header = _header(sec=sec)
    with pytest.raises(ValueError):
        validate_observation_metadata(header, 'm', 'ros')
    assert header.stamp.sec == sec


@pytest.mark.parametrize('sec', [-(2**31), -1, 0, 2**31 - 1])
def test_metadata_and_capture_time_accept_signed_seconds_boundaries(sec):
    """Valid negative ROS timestamps and both int32 boundaries remain usable."""
    header = _header(sec=sec)
    transform = _transform(sec=sec)
    before = deepcopy((header, transform))
    assert validate_observation_metadata(header, 'm', 'ros') is None
    assert validate_capture_time(header, transform, 'ros', 'ros') is None
    assert (header, transform) == before


@pytest.mark.parametrize('sec', ['bad', 2**31])
def test_equal_invalid_seconds_cannot_bind_capture_time(sec):
    """Matching timestamps must be valid, rather than merely equal objects."""
    header = _header(sec=sec)
    transform = _transform(sec=sec)
    with pytest.raises(ValueError):
        validate_capture_time(header, transform, 'ros', 'ros')
    inputs = _factory_inputs()
    inputs.update(
        header=header, capture_transform=transform, target_frame_id='world',
        transform_clock_domain='ros',
    )
    with pytest.raises(ValueError):
        make_observation_frame(**inputs)


@pytest.mark.parametrize('nanosec', [True, 1.5, -1, 1_000_000_000])
def test_metadata_still_rejects_invalid_nanoseconds(nanosec):
    """Adding seconds checks retains the existing nanosecond rejection rules."""
    with pytest.raises(ValueError):
        validate_observation_metadata(_header(nanosec=nanosec), 'm', 'ros')


@pytest.mark.parametrize('localized', [False, True])
@pytest.mark.parametrize('empty', [False, True])
def test_factory_accepts_raw_localized_and_empty_observations(localized, empty):
    """Empty geometry remains a valid observation, with or without localization."""
    inputs = _factory_inputs()
    if empty:
        inputs['mesh'] = Mesh()
    if localized:
        inputs.update(
            capture_transform=_transform(), target_frame_id='world',
            transform_clock_domain='ros',
        )
    before = deepcopy(inputs)
    frame = make_observation_frame(**inputs)
    assert frame.context is inputs['context']
    assert frame.mesh == inputs['mesh'] and frame.mesh is not inputs['mesh']
    assert frame.header == inputs['header'] and frame.header is not inputs['header']
    if localized:
        assert frame.capture_transform == inputs['capture_transform']
        assert frame.capture_transform is not inputs['capture_transform']
    else:
        assert frame.capture_transform is None
    assert inputs == before


def test_factory_isolates_nested_payloads_in_both_directions():
    """Edits to source messages and returned messages cannot cross the factory."""
    inputs = _factory_inputs()
    inputs.update(
        capture_transform=_transform(), target_frame_id='world',
        transform_clock_domain='ros',
    )
    frame = make_observation_frame(**inputs)
    inputs['mesh'].vertices[0].x = 2.0
    inputs['mesh'].triangles[0].vertex_indices[0] = 1
    inputs['header'].stamp.nanosec = 456
    inputs['capture_transform'].transform.translation.x = 3.0
    inputs['capture_transform'].header.stamp.nanosec = 456
    assert frame.mesh.vertices[0].x == 0.0
    assert frame.mesh.triangles[0].vertex_indices[0] == 0
    assert frame.header.stamp.nanosec == 123
    assert frame.capture_transform.transform.translation.x == 0.0
    assert frame.capture_transform.header.stamp.nanosec == 123
    before = deepcopy(inputs)
    frame.mesh.vertices[1].y = 5.0
    frame.mesh.triangles[0].vertex_indices[1] = 0
    frame.header.stamp.sec = 43
    frame.capture_transform.transform.translation.y = 6.0
    frame.capture_transform.header.stamp.sec = 43
    assert inputs == before


def test_factory_preserves_valid_integer_payload_values():
    """Numeric checking does not rewrite valid caller-owned numeric fields."""
    inputs = _factory_inputs()
    inputs['mesh'] = Mesh(vertices=[Point(x=1, check_fields=False)])
    transform = _transform()
    transform.transform.translation.x = 2
    transform.transform.rotation.w = 1
    inputs.update(
        capture_transform=transform, target_frame_id='world',
        transform_clock_domain='ros',
    )
    before = deepcopy(inputs)
    frame = make_observation_frame(**inputs)
    assert inputs == before
    assert frame.mesh.vertices[0].x == 1
    assert type(frame.mesh.vertices[0].x) is int
    assert frame.capture_transform.transform.translation.x == 2
    assert type(frame.capture_transform.transform.translation.x) is int
    assert frame.capture_transform.transform.rotation.w == 1
    assert type(frame.capture_transform.transform.rotation.w) is int


def test_rejected_factory_input_is_not_modified():
    """Rejecting a same-frame offset leaves all caller-owned inputs intact."""
    inputs = _factory_inputs()
    transform = _transform(source='world')
    transform.transform.translation.x = 1.0
    inputs.update(
        header=_header('world'), capture_transform=transform,
        target_frame_id='world', transform_clock_domain='ros',
    )
    before = deepcopy(inputs)
    with pytest.raises(ValueError):
        make_observation_frame(**inputs)
    assert inputs == before


@pytest.mark.parametrize('observation_clock,transform_clock', [
    ('unknown', 'unknown'), ('ros', 'unknown'), ('ros', 'steady'),
])
def test_capture_time_requires_known_matching_clocks(observation_clock, transform_clock):
    """A matching numeric timestamp cannot bridge unknown or distinct clocks."""
    with pytest.raises(ValueError):
        validate_capture_time(_header(), _transform(), observation_clock, transform_clock)


def test_capture_time_rejects_a_one_nanosecond_difference():
    """Exact integer timestamp comparison must survive float-second rounding."""
    header = _header(sec=1_700_000_000, nanosec=100)
    transform = _transform(sec=1_700_000_000, nanosec=101)
    with pytest.raises(ValueError):
        validate_capture_time(header, transform, 'ros', 'ros')


@pytest.mark.parametrize('missing', [
    'capture_transform', 'target_frame_id', 'transform_clock_domain',
])
def test_factory_rejects_partial_localization(missing):
    """Localization keeps its transform, target frame, and clock as one envelope."""
    inputs = _factory_inputs()
    inputs.update(
        capture_transform=_transform(), target_frame_id='world',
        transform_clock_domain='ros',
    )
    inputs[missing] = None
    with pytest.raises(ValueError):
        make_observation_frame(**inputs)
