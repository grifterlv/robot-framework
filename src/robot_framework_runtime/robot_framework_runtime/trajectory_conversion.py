from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from robot_framework_runtime.path_validation import (
    validate_timed_path,
    seconds_to_duration_parts,
)

def to_joint_trajectory(path: dict, model: dict) -> JointTrajectory:
    # Validate and get the strictly isolated, safe dictionary
    checked = validate_timed_path(path, model)
    
    trajectory = JointTrajectory()
    
    # 1. Copy joint names to the trajectory
    trajectory.joint_names = list(checked["joint_names"])
    
    last_total_ns = -1
    
    for i in range(len(checked["points"])):
        # 3. Create a BRAND NEW point object INSIDE the loop to avoid reference trapping
        point = JointTrajectoryPoint()
        
        # Copy positions as a list of floats
        point.positions = [float(pos) for pos in checked["points"][i]]
        
        # Get raw float seconds from the validated data
        raw_seconds = checked["times"][i]
        
        # Call the helper to safely convert to ROS time parts
        sec, nanosec = seconds_to_duration_parts(raw_seconds)
        
        # 2. Re-check strictly increasing time using nanoseconds 
        current_total_ns = sec * 1_000_000_000 + nanosec
        
        if i == 0:
            if current_total_ns < 0:
                raise ValueError("Converted first time must be >= 0")
        else:
            if current_total_ns <= last_total_ns:
                raise ValueError("Converted times must be strictly increasing")
                
        last_total_ns = current_total_ns
        
        # Assign to ROS time object
        point.time_from_start.sec = sec
        point.time_from_start.nanosec = nanosec
        
        # Append the completely independent point to the trajectory
        trajectory.points.append(point)

    return trajectory