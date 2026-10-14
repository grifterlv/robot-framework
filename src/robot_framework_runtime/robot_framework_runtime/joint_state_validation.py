import math
from sensor_msgs.msg import JointState

def validate_joint_positions(msg: JointState) -> dict[str, float]:
    if len(msg.name) == 0:
        raise ValueError('Joint names list cannot be empty')

    if '' in msg.name:
        raise ValueError('Joint name cannot be empty')

    if len(msg.name) != len(set(msg.name)):
        raise ValueError('Duplicate joint names found')

    if len(msg.name) != len(msg.position):
        raise ValueError('Names and positions length mismatch')

    for pos in msg.position:
        if not math.isfinite(pos):
            raise ValueError('Position contains invalid number (NaN or Inf)')

    return dict(zip(msg.name, msg.position))
