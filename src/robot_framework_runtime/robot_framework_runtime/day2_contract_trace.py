"""Day 2 Contract Trace: Pre-flight admission, R2 identity outputs, R4 feedback, and R5/R6 observation capture."""

import math
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Point, TransformStamped
from shape_msgs.msg import Mesh, MeshTriangle
from std_msgs.msg import Header

from robot_framework_runtime.contracts import RequestContext
from robot_framework_runtime.path_requests import prepare_path_request
from robot_framework_runtime.acceptance_config import (
    JointTolerance,
    TimingConfig,
    validate_joint_tolerances,
)
from robot_framework_runtime.result_contracts import (
    TaskResult,
    ResultStatus,
)
from robot_framework_runtime.capture_outcomes import (
    CaptureOutcome,
    CaptureStatus,
)
from robot_framework_runtime.feedback_frames import make_feedback_frame
from robot_framework_runtime.joint_state_validation import validate_joint_positions
from robot_framework_runtime.observation_frames import make_observation_frame

SOURCE = "synthetic_contract_probe"


def prepare_case(
    context: RequestContext,
    path: dict,
    model: dict,
    active_session_id: str,
    goal_tolerances: list[JointTolerance],
    stop_tolerances: list[JointTolerance],
    timing: TimingConfig,
) -> dict:
    """Pre-flight admission gate validating and canonicalizing task inputs."""
    try:
        prepared_request = prepare_path_request(
            context=context,
            path=path,
            model=model,
            active_session_id=active_session_id,
        )

        validated_goal = validate_joint_tolerances(
            tolerances=goal_tolerances,
            context=context,
            model=model,
            active_session_id=active_session_id,
        )

        validated_stop = validate_joint_tolerances(
            tolerances=stop_tolerances,
            context=context,
            model=model,
            active_session_id=active_session_id,
        )

        if not isinstance(timing, TimingConfig):
            raise ValueError(
                f"Expected TimingConfig instance for timing, got {type(timing).__name__}"
            )

        result = TaskResult(
            context=context,
            status=ResultStatus.ACCEPTED,
            source=SOURCE,
            reason=None,
        )
        return {
            "request": prepared_request,
            "goal_tolerances": validated_goal,
            "stop_tolerances": validated_stop,
            "timing": timing,
            "result": result,
        }

    except ValueError as error:
        result = TaskResult(
            context=context,
            status=ResultStatus.REJECTED,
            source=SOURCE,
            reason=str(error),
        )
        return {
            "request": None,
            "goal_tolerances": None,
            "stop_tolerances": None,
            "timing": None,
            "result": result,
        }


def main():
    model = {
        "model_id": "day2_fixture",
        "model_version": "1",
        "joint_names": ["turn", "slide"],
        "joint_types": {"turn": "revolute", "slide": "prismatic"},
    }

    path = {
        "model_id": "day2_fixture",
        "model_version": "1",
        "joint_names": ["slide", "turn"],
        "units": {"slide": "m", "turn": "rad"},
        "points": [[0.2, 0.1], [0.4, 0.3]],
        "times": [0.0, 0.5],
    }

    goal_tolerances = [
        JointTolerance("turn", "rad", 0.01),
        JointTolerance("slide", "m", 0.001),
    ]
    stop_tolerances = [
        JointTolerance("turn", "rad", 0.001),
        JointTolerance("slide", "m", 0.0001),
    ]

    timing = TimingConfig(
        clock_domain="test_monotonic",
        feedback_receive_timeout_ns=500_000_000,
        request_accept_timeout_ns=2_000_000_000,
        execution_timeout_ns=30_000_000_000,
        cancel_confirmation_timeout_ns=5_000_000_000,
        reached_window_ns=300_000_000,
        stop_window_ns=500_000_000,
    )

    active_session_id = "session-1"

    # --- Valid Case (session-1) ---
    valid_context = RequestContext(
        request_id="req-trace-valid",
        task_id="contract-preparation",
        session_id="session-1",
        model_id="day2_fixture",
        model_version="1",
    )
    res_valid = prepare_case(
        context=valid_context,
        path=path,
        model=model,
        active_session_id=active_session_id,
        goal_tolerances=goal_tolerances,
        stop_tolerances=stop_tolerances,
        timing=timing,
    )

    assert res_valid["result"].status == ResultStatus.ACCEPTED
    assert res_valid["result"].reason is None
    assert res_valid["request"] is not None
    assert res_valid["request"].kind == "timed_path"
    assert res_valid["request"].payload.joint_names == ["turn", "slide"]
    assert res_valid["goal_tolerances"] == {"turn": 0.01, "slide": 0.001}
    assert res_valid["stop_tolerances"] == {"turn": 0.001, "slide": 0.0001}

    points_positions = [list(pt.positions) for pt in res_valid["request"].payload.points]
    points_times = [
        (pt.time_from_start.sec, pt.time_from_start.nanosec)
        for pt in res_valid["request"].payload.points
    ]

    print("--- Valid Case Output (R2 Complete) ---")
    print("Result context:", res_valid["result"].context)
    print("Result source:", res_valid["result"].source)
    print("Status:", res_valid["result"].status.value)
    print("Path kind:", res_valid["request"].kind)
    print("Canonical joint names:", res_valid["request"].payload.joint_names)
    print("Canonical points:", points_positions)
    print("Points times (sec, nanosec):", points_times)
    print("Goal tolerances (canonical order):", res_valid["goal_tolerances"])
    print("Stop tolerances (canonical order):", res_valid["stop_tolerances"])
    print("Timing config:", res_valid["timing"])

    # --- R4 Feedback Frame Trace ---
    state = JointState()
    state.name = ["slide", "extra_joint", "turn"]
    state.position = [0.4, 0.02, 0.3]
    state.velocity = []
    state.effort = [float("nan")] * 3
    state.header.stamp.sec = 10
    state.header.stamp.nanosec = 20

    feedback = make_feedback_frame(
        state=state,
        source="synthetic_probe",
        topic="/day2_joint_states_probe",
        sample_clock_domain="unknown",
        received_monotonic_ns=1_000_000_000,
        received_clock_domain=timing.clock_domain,
    )

    assert feedback.state is not state
    assert len(feedback.state.effort) == 3
    assert all(math.isnan(val) for val in feedback.state.effort)

    all_positions = validate_joint_positions(feedback.state)
    assert len(all_positions) == 3
    assert "extra_joint" in all_positions

    canonical_names = res_valid["request"].payload.joint_names
    controlled_view = {name: all_positions[name] for name in canonical_names}
    assert controlled_view == {"turn": 0.3, "slide": 0.4}

    print("\n--- Feedback Frame Trace (R4) ---")
    print("Controlled view:", controlled_view)
    print("Full frame joints count:", len(all_positions))
    print("Sample stamp (sec, nanosec):", (feedback.state.header.stamp.sec, feedback.state.header.stamp.nanosec))
    print("Received monotonic ns:", feedback.received_monotonic_ns)
    print("Sample clock domain:", feedback.sample_clock_domain)
    print("Received clock domain:", feedback.received_clock_domain)
    print("Feedback source:", feedback.source)
    print("Feedback topic:", feedback.topic)

    # --- R5 + R6: Observation Frame & Capture Outcomes Trace ---
    mesh = Mesh()
    mesh.vertices = [
        Point(x=0.0, y=0.0, z=1.0),
        Point(x=1.0, y=0.0, z=1.0),
        Point(x=0.0, y=1.0, z=1.0),
    ]
    triangle = MeshTriangle()
    triangle.vertex_indices = [0, 1, 2]
    mesh.triangles = [triangle]

    obs_header = Header()
    obs_header.frame_id = "camera_optical_frame"
    obs_header.stamp.sec = 10
    obs_header.stamp.nanosec = 20

    tf_stamped = TransformStamped()
    tf_stamped.header.frame_id = "world"
    tf_stamped.header.stamp.sec = 10
    tf_stamped.header.stamp.nanosec = 20
    tf_stamped.child_frame_id = "camera_optical_frame"
    tf_stamped.transform.translation.x = 1.0
    tf_stamped.transform.translation.y = 0.0
    tf_stamped.transform.translation.z = 0.0
    tf_stamped.transform.rotation.x = 0.0
    tf_stamped.transform.rotation.y = 0.0
    tf_stamped.transform.rotation.z = 0.0
    tf_stamped.transform.rotation.w = 1.0

    clock_domain_synthetic = "synthetic_clock:session-1"

    # Invoke observation frame factory with canonical parameter names
    obs_frame = make_observation_frame(
        context=valid_context,
        mesh=mesh,
        header=obs_header,
        length_unit="m",
        sample_clock_domain=clock_domain_synthetic,
        source="synthetic_probe",
        model=model,
        active_session_id=active_session_id,
        capture_transform=tf_stamped,
        target_frame_id="world",
        transform_clock_domain=clock_domain_synthetic,
    )

    # 1. Identity & two-way isolation assertions
    assert obs_frame.mesh is not mesh
    assert obs_frame.header is not obs_header
    assert obs_frame.capture_transform is not tf_stamped

    # Mutate original inputs to verify that the snapshot stays isolated
    mesh.vertices[0].x = 999.0
    obs_header.stamp.sec = 999
    tf_stamped.transform.translation.x = 999.0
    assert obs_frame.mesh.vertices[0].x == 0.0
    assert obs_frame.header.stamp.sec == 10
    assert obs_frame.capture_transform.transform.translation.x == 1.0

    # Mutate instance fields to assert original inputs remain isolated
    obs_frame.mesh.vertices[0].x = 888.0
    obs_frame.header.stamp.sec = 888
    obs_frame.capture_transform.transform.translation.x = 888.0
    assert mesh.vertices[0].x == 999.0
    assert obs_header.stamp.sec == 999
    assert tf_stamped.transform.translation.x == 999.0

    # Reset all mutated fields back to original values to avoid fixture pollution
    mesh.vertices[0].x = 0.0
    obs_header.stamp.sec = 10
    tf_stamped.transform.translation.x = 1.0

    obs_frame.mesh.vertices[0].x = 0.0
    obs_frame.header.stamp.sec = 10
    obs_frame.capture_transform.transform.translation.x = 1.0

    # 2. Camera frame retention assertion
    assert obs_frame.header.frame_id == "camera_optical_frame"
    assert obs_frame.capture_transform.header.frame_id == "world"
    assert obs_frame.capture_transform.child_frame_id == "camera_optical_frame"
    assert obs_frame.mesh.vertices[0].z == 1.0

    # 3. Timestamp mismatch rejection assertion
    bad_tf = TransformStamped()
    bad_tf.header.frame_id = "world"
    bad_tf.header.stamp.sec = 10
    bad_tf.header.stamp.nanosec = 21
    bad_tf.child_frame_id = "camera_optical_frame"
    bad_tf.transform.rotation.w = 1.0
    try:
        make_observation_frame(
            context=valid_context,
            mesh=mesh,
            header=obs_header,
            length_unit="m",
            sample_clock_domain=clock_domain_synthetic,
            source="synthetic_probe",
            model=model,
            active_session_id=active_session_id,
            capture_transform=bad_tf,
            target_frame_id="world",
            transform_clock_domain=clock_domain_synthetic,
        )
    except ValueError as err:
        print("\nMismatched transform stamp REJECT:", err)
    else:
        raise AssertionError("Mismatched transform stamp should have been rejected with ValueError")

    # 4. Four Capture Outcomes
    captured_normal = CaptureOutcome(
        context=valid_context,
        status=CaptureStatus.CAPTURED,
        frame=obs_frame,
    )
    assert captured_normal.frame.context == captured_normal.context
    assert len(captured_normal.frame.mesh.vertices) == 3
    assert len(captured_normal.frame.mesh.triangles) == 1

    empty_mesh = Mesh()
    empty_mesh.vertices = []
    empty_mesh.triangles = []
    empty_frame = make_observation_frame(
        context=valid_context,
        mesh=empty_mesh,
        header=obs_header,
        length_unit="m",
        sample_clock_domain=clock_domain_synthetic,
        source="synthetic_probe",
        model=model,
        active_session_id=active_session_id,
        capture_transform=obs_frame.capture_transform,
        target_frame_id="world",
        transform_clock_domain=clock_domain_synthetic,
    )
    captured_empty = CaptureOutcome(
        context=valid_context,
        status=CaptureStatus.CAPTURED,
        frame=empty_frame,
    )
    assert len(captured_empty.frame.mesh.vertices) == 0
    assert len(captured_empty.frame.mesh.triangles) == 0

    fault_context = RequestContext(
        request_id="req-trace-capture-fault",
        task_id="contract-preparation",
        session_id="session-1",
        model_id="day2_fixture",
        model_version="1",
    )
    res_fault = prepare_case(
        context=fault_context,
        path=path,
        model=model,
        active_session_id=active_session_id,
        goal_tolerances=goal_tolerances,
        stop_tolerances=stop_tolerances,
        timing=timing,
    )
    assert res_fault["result"].status == ResultStatus.ACCEPTED
    assert res_fault["result"].context == fault_context
    assert res_fault["request"].context == fault_context

    captured_failed = CaptureOutcome(
        context=fault_context,
        status=CaptureStatus.FAILED,
        frame=None,
        reason="synthetic_sensor_read_timeout",
    )
    assert captured_failed.frame is None
    assert captured_failed.reason == "synthetic_sensor_read_timeout"

    fault_result = TaskResult(
        context=fault_context,
        status=ResultStatus.FAULT,
        source="synthetic_probe",
        reason=captured_failed.reason,
    )
    assert fault_result.status == ResultStatus.FAULT
    assert fault_result.reason == "synthetic_sensor_read_timeout"
    assert fault_result.source == "synthetic_probe"
    assert captured_failed.context == fault_result.context == fault_context
    assert fault_result.context == res_fault["result"].context

    captured_not_received = CaptureOutcome(
        context=valid_context,
        status=CaptureStatus.NOT_RECEIVED,
        frame=None,
        reason=None,
    )
    assert captured_not_received.frame is None
    assert captured_not_received.reason is None

    print("\n--- Observation & Capture Outcomes (R5 + R6) ---")
    print("Observation context:", obs_frame.context)
    print("Observation source:", obs_frame.source)
    print("Observation length_unit:", obs_frame.length_unit)
    print("Sensor frame id:", obs_frame.header.frame_id)
    print(
        "Transform parent/child:",
        f"{obs_frame.capture_transform.header.frame_id} -> {obs_frame.capture_transform.child_frame_id}",
    )
    print("Sample stamp (sec, nanosec):", (obs_frame.header.stamp.sec, obs_frame.header.stamp.nanosec))
    print(
        "Transform stamp (sec, nanosec):",
        (obs_frame.capture_transform.header.stamp.sec, obs_frame.capture_transform.header.stamp.nanosec),
    )
    print("Sample clock domain:", obs_frame.sample_clock_domain)
    print("Transform clock domain:", obs_frame.transform_clock_domain)
    print("Capture outcomes verified:", [
        captured_normal.status.value,
        captured_empty.status.value,
        captured_failed.status.value,
        captured_not_received.status.value,
    ])
    print("Fault request admission:", res_fault["result"].status.value)
    print("Failed capture context:", captured_failed.context)
    print("Fault result context:", fault_result.context)
    print("Synthetic task fault recorded:", fault_result.status.value, fault_result.reason)

    # --- Stale Session Case (old-session) ---
    stale_context = RequestContext(
        request_id="req-trace-stale",
        task_id="contract-preparation",
        session_id="old-session",
        model_id="day2_fixture",
        model_version="1",
    )
    res_stale = prepare_case(
        context=stale_context,
        path=path,
        model=model,
        active_session_id=active_session_id,
        goal_tolerances=goal_tolerances,
        stop_tolerances=stop_tolerances,
        timing=timing,
    )

    assert res_stale["result"].status == ResultStatus.REJECTED
    assert res_stale["request"] is None
    assert res_stale["goal_tolerances"] is None
    assert res_stale["stop_tolerances"] is None
    assert res_stale["timing"] is None
    assert res_stale["result"].reason is not None

    print("\n--- Stale Session Rejection Output ---")
    print("Status:", res_stale["result"].status.value)
    print("Source:", res_stale["result"].source)
    print("Rejection reason:", res_stale["result"].reason)


if __name__ == "__main__":
    main()
