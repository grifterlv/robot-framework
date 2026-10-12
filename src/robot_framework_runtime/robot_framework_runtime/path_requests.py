from dataclasses import dataclass
from trajectory_msgs.msg import JointTrajectory
from robot_framework_runtime.contracts import (
    RequestContext,
    validate_request_context,
)
from robot_framework_runtime.path_validation import validate_geometric_path
from robot_framework_runtime.trajectory_conversion import to_joint_trajectory

@dataclass(frozen=True)
class PathRequest:
    context: RequestContext
    kind: str
    payload: dict | JointTrajectory

    def __post_init__(self):
        if not isinstance(self.context, RequestContext):
            raise ValueError("context must be a RequestContext object")
        if self.kind == "geometric_path":
            if not isinstance(self.payload, dict):
                raise ValueError("Payload must be a dictionary for geometric_path")
        elif self.kind == "timed_path":
            if not isinstance(self.payload, JointTrajectory):
                raise ValueError("Payload must be a JointTrajectory for timed_path")
        else:
            raise ValueError("kind must be either 'geometric_path' or 'timed_path'")

def prepare_path_request(
    context: RequestContext,
    path: dict,
    model: dict,
    active_session_id: str,
) -> PathRequest:
    # 1. Check identity and session match first
    validate_request_context(context, model, active_session_id)
    
    # 2. Check if the path is a dictionary
    if not isinstance(path, dict):
        raise ValueError("path must be a dictionary")
        
    # 3. Strictly check if the "times" key actually exists (answering the tutor's question)
    if "times" not in path:
        raise ValueError("The path dictionary must explicitly contain a 'times' key")
        
    # 4. Route the data based on what is inside the "times" field
    if path["times"] is None:
        payload = validate_geometric_path(path, model)
        kind = "geometric_path"
    else:
        payload = to_joint_trajectory(path, model)
        kind = "timed_path"
        
    return PathRequest(context=context, kind=kind, payload=payload)