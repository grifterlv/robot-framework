from copy import deepcopy
from dataclasses import dataclass

from sensor_msgs.msg import JointState
from robot_framework_runtime.runtime_node import validate_joint_positions

@dataclass(frozen=True)
class FeedbackFrame:
    state: JointState
    source: str
    topic: str
    sample_clock_domain: str
    received_monotonic_ns: int
    received_clock_domain: str

    def __post_init__(self):
        # 1. Check if state is a JointState message
        if not isinstance(self.state, JointState):
            raise ValueError("state must be a JointState message")
            
        # 1. Reuse existing position validation
        validate_joint_positions(self.state)

        # 2. Check velocity and effort lengths if they are not empty
        if self.state.velocity and len(self.state.velocity) != len(self.state.name):
            raise ValueError("velocity array length must match name array length")
        if self.state.effort and len(self.state.effort) != len(self.state.name):
            raise ValueError("effort array length must match name array length")

        # 3. Validate the four string fields
        string_fields = [
            ("source", self.source),
            ("topic", self.topic),
            ("sample_clock_domain", self.sample_clock_domain),
            ("received_clock_domain", self.received_clock_domain),
        ]
        for field_name, value in string_fields:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        # 3. Validate received_monotonic_ns (must be int, non-negative, and NOT a boolean)
        if isinstance(self.received_monotonic_ns, bool) or not isinstance(self.received_monotonic_ns, int) or self.received_monotonic_ns < 0:
            raise ValueError("received_monotonic_ns must be a non-negative integer")

        # 4. Validate nanosec bounds
        nanosec = self.state.header.stamp.nanosec
        if not isinstance(nanosec, int) or not (0 <= nanosec < 1_000_000_000):
            raise ValueError("state.header.stamp.nanosec must be between 0 and 999,999,999")

def make_feedback_frame(
    state: JointState,
    source: str,
    topic: str,
    sample_clock_domain: str,
    received_monotonic_ns: int,
    received_clock_domain: str,
) -> FeedbackFrame:
    # 1. Validate state type before deepcopy to fail fast
    if not isinstance(state, JointState):
        raise ValueError("state must be a JointState message")
        
    # 5. Deepcopy the state to physically isolate the original message from the factory output
    state_copy = deepcopy(state)
    
    return FeedbackFrame(
        state=state_copy,
        source=source,
        topic=topic,
        sample_clock_domain=sample_clock_domain,
        received_monotonic_ns=received_monotonic_ns,
        received_clock_domain=received_clock_domain,
    )