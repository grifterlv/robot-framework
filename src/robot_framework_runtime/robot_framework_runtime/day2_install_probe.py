"""Day 2 Install Probe: Verify colcon build artifact, standard entrypoint, and contract boundaries."""

import robot_framework_runtime
from robot_framework_runtime.contracts import RequestContext
from robot_framework_runtime.result_contracts import TaskResult, ResultStatus
from robot_framework_runtime.acceptance_config import (
    JointTolerance,
    validate_joint_tolerances,
)
from robot_framework_runtime.runtime_node import main as node_main
from robot_framework_runtime.day2_contract_trace import main as trace_main


def main():
    # 1. Print installation location and assert node entrypoint is callable
    print("robot_framework_runtime __file__:", robot_framework_runtime.__file__)
    assert callable(node_main), "runtime_node.main entrypoint must be callable"
    print("Verified runtime_node.main is callable.")

    context = RequestContext(
        request_id="req-probe-valid",
        task_id="install-probe-task",
        session_id="session-1",
        model_id="day2_fixture",
        model_version="1",
    )
    model = {
        "model_id": "day2_fixture",
        "model_version": "1",
        "joint_names": ["turn", "slide"],
        "joint_types": {"turn": "revolute", "slide": "prismatic"},
    }
    active_session_id = "session-1"

    # 2. Iterate all 7 ResultStatus: first 3 use reason=None, remaining 4 require non-empty reason
    statuses = list(ResultStatus)
    assert len(statuses) == 7, f"Expected 7 ResultStatus members, got {len(statuses)}: {statuses}"

    for idx, status in enumerate(statuses):
        reason = None if idx < 3 else f"probe_reason_for_{status.value}"
        res = TaskResult(
            context=context,
            status=status,
            source="install_probe",
            reason=reason,
        )
        assert res.context == context
        assert res.status == status
        if idx < 3:
            assert res.reason is None
        else:
            assert res.reason == f"probe_reason_for_{status.value}"

    print(f"Verified all 7 ResultStatus contracts: {[s.value for s in statuses]}")

    # 3. Canonical order verification with inverted slide/turn input
    inverted_tolerances = [
        JointTolerance(joint_name="slide", unit="m", position_tolerance=0.001),
        JointTolerance(joint_name="turn", unit="rad", position_tolerance=0.01),
    ]
    canonical_tolerances = validate_joint_tolerances(
        tolerances=inverted_tolerances,
        context=context,
        model=model,
        active_session_id=active_session_id,
    )
    assert list(canonical_tolerances.keys()) == ["turn", "slide"], (
        f"Expected canonical order ['turn', 'slide'], got {list(canonical_tolerances.keys())}"
    )
    assert canonical_tolerances == {"turn": 0.01, "slide": 0.001}
    print("Verified tolerance canonical reordering:", canonical_tolerances)

    # 4. Check four rejection boundary conditions
    # 4.1 ACCEPTED with reason
    try:
        TaskResult(
            context=context,
            status=ResultStatus.ACCEPTED,
            source="install_probe",
            reason="accepted_should_not_have_reason",
        )
    except ValueError as error:
        print("REJECT (ACCEPTED with reason):", error)
    else:
        raise AssertionError("ACCEPTED with reason should have been rejected")

    # 4.2 FAULT without reason
    try:
        TaskResult(
            context=context,
            status=ResultStatus.FAULT,
            source="install_probe",
            reason=None,
        )
    except ValueError as error:
        print("REJECT (FAULT without reason):", error)
    else:
        raise AssertionError("FAULT without reason should have been rejected")

    # 4.3 Prismatic joint using rad unit
    try:
        bad_unit_tolerances = [
            JointTolerance(joint_name="turn", unit="rad", position_tolerance=0.01),
            JointTolerance(joint_name="slide", unit="rad", position_tolerance=0.001),
        ]
        validate_joint_tolerances(
            tolerances=bad_unit_tolerances,
            context=context,
            model=model,
            active_session_id=active_session_id,
        )
    except ValueError as error:
        print("REJECT (Prismatic joint using rad):", error)
    else:
        raise AssertionError("Prismatic joint using rad should have been rejected")

    # 4.4 Stale session with bad unit: assert session mismatch is reported first
    stale_context = RequestContext(
        request_id="req-probe-stale",
        task_id="install-probe-task",
        session_id="old-session",
        model_id="day2_fixture",
        model_version="1",
    )
    try:
        validate_joint_tolerances(
            tolerances=bad_unit_tolerances,
            context=stale_context,
            model=model,
            active_session_id=active_session_id,
        )
    except ValueError as error:
        err_msg = str(error)
        print("REJECT (Old session + bad unit):", err_msg)
        assert "session" in err_msg.lower() or "old-session" in err_msg, (
            f"Session mismatch must be reported first, got: {err_msg}"
        )
        assert "unit" not in err_msg.lower() and "rad" not in err_msg.lower(), (
            f"Unit validation must not precede session validation, got: {err_msg}"
        )
    else:
        raise AssertionError("Stale session with bad unit should have been rejected")

    # 5. Invoke existing day2_contract_trace.main() and report pass
    print("\n--- Invoking day2_contract_trace.main() in installed environment ---")
    trace_main()

    print("\ninstall_probe PASS")


if __name__ == "__main__":
    main()