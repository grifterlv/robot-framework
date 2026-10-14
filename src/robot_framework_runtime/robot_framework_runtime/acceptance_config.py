import math
from dataclasses import dataclass
from robot_framework_runtime.contracts import (
    RequestContext,
    validate_request_context,
)
from robot_framework_runtime.path_validation import validate_path_metadata

@dataclass(frozen=True)
class JointTolerance:
    """Specification defining position acceptance tolerance for a single robot joint."""
    joint_name: str
    unit: str
    position_tolerance: float

    def __post_init__(self):
        # 1. Validate joint name is a non-empty string
        if not isinstance(self.joint_name, str) or not self.joint_name.strip():
            raise ValueError(f"joint_name must be a non-empty string, got {self.joint_name!r}")

        # 2. Validate measurement unit strictly restricted to 'rad' or 'm'
        if not isinstance(self.unit, str) or self.unit not in ("rad", "m"):
            raise ValueError(f"unit must be either 'rad' or 'm', got {self.unit!r}")

        # 3. Validate numeric type and explicitly reject boolean values
        if isinstance(self.position_tolerance, bool) or not isinstance(
            self.position_tolerance, (int, float)
        ):
            raise ValueError(
                f"position_tolerance must be a real number, got {type(self.position_tolerance).__name__}"
            )

        # 4. Check finiteness and strict positivity (convert OverflowError to ValueError)
        try:
            is_finite = math.isfinite(self.position_tolerance)
        except OverflowError as err:
            raise ValueError(f"position_tolerance exceeds numerical range: {err}") from err

        if not is_finite or self.position_tolerance <= 0.0:
            raise ValueError(
                f"position_tolerance must be finite and strictly greater than 0, got {self.position_tolerance}"
            )

def validate_joint_tolerances(
tolerances: list[JointTolerance],
context: RequestContext,
model: dict,
active_session_id: str,
) -> dict[str, float]:
    """Validate joint tolerance list against robot model and return reordered tolerance mapping."""

    # Step 1: Validate context against model and active session ID
    validate_request_context(
        context=context,
        model=model,
        active_session_id=active_session_id,
    )

    # Step 2: Ensure tolerances is a non-empty list of JointTolerance objects
    if not isinstance(tolerances, list) or len(tolerances) == 0:
        raise ValueError(f"tolerances must be a non-empty list, got {type(tolerances).__name__}")

    for item in tolerances:
        if not isinstance(item, JointTolerance):
            raise ValueError(f"Expected JointTolerance instance in tolerances, got {type(item).__name__}")

    # Step 3: Construct metadata with raw lists to preserve duplicate names for validation
    metadata = {
        "model_id": context.model_id,
        "model_version": context.model_version,
        "joint_names": [t.joint_name for t in tolerances],
        "units": {t.joint_name: t.unit for t in tolerances},
    }

    # Step 4: Delegate structural, duplicate, and type validation to get canonical order indices
    indices = validate_path_metadata(metadata, model)

    # Step 5: Construct and return reordered dictionary matching model["joint_names"]
    return {
        tolerances[idx].joint_name: tolerances[idx].position_tolerance
        for idx in indices
    }

@dataclass(frozen=True)
class TimingConfig:
    """Immutable timing configuration defining deadlines and observation windows in nanoseconds."""
    clock_domain: str
    feedback_receive_timeout_ns: int
    request_accept_timeout_ns: int
    execution_timeout_ns: int
    cancel_confirmation_timeout_ns: int
    reached_window_ns: int
    stop_window_ns: int

    def __post_init__(self):
        # 1. Validate clock_domain is non-empty and not 'unknown'
        if not isinstance(self.clock_domain, str) or not self.clock_domain.strip():
            raise ValueError(f"clock_domain must be a non-empty string, got {self.clock_domain!r}")
        if self.clock_domain.strip() == "unknown":
            raise ValueError("clock_domain cannot be 'unknown'")

        # 2. Validate all 6 timing fields are strictly positive integers (reject bool/float)
        timing_fields = (
            ("feedback_receive_timeout_ns", self.feedback_receive_timeout_ns),
            ("request_accept_timeout_ns", self.request_accept_timeout_ns),
            ("execution_timeout_ns", self.execution_timeout_ns),
            ("cancel_confirmation_timeout_ns", self.cancel_confirmation_timeout_ns),
            ("reached_window_ns", self.reached_window_ns),
            ("stop_window_ns", self.stop_window_ns),
        )

        for name, value in timing_fields:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(
                    f"{name} must be an integer, got {type(value).__name__}"
                )
            if value <= 0:
                raise ValueError(
                    f"{name} must be strictly greater than 0, got {value}"
                )