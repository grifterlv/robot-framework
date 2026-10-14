import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
from robot_framework_runtime.joint_state_validation import validate_joint_positions
from robot_framework_runtime.feedback_frames import make_feedback_frame

def main():
    rclpy.init()
    node = rclpy.create_node('runtime')
    node.get_logger().info('runtime started')

    state_source = node.declare_parameter("state_source", "unknown").value

    stats = {
        'received': 0,
        'accepted': 0,
        'rejected': 0,
        'latest_valid': None,
    }

    def on_joint_state(msg: JointState):
        received_monotonic_ns = time.monotonic_ns()

        stats['received'] += 1

        try:
            frame = make_feedback_frame(
                state=msg,
                source=state_source,
                topic=sub.topic_name,
                sample_clock_domain='unknown',
                received_monotonic_ns=received_monotonic_ns,
                received_clock_domain='wsl_monotonic',
            )
        except ValueError as error:
            stats['rejected'] += 1
            node.get_logger().warning(
                f'Joint state rejected: {error}', throttle_duration_sec=3.0
            )
            return

        stats['accepted'] += 1
        stats['latest_valid'] = frame

        positions = validate_joint_positions(frame.state)
        state_msg = frame.state

        summary = (
            f"Received: {stats['received']} | "
            f"Names: {len(state_msg.name)} | "
            f"Pos: {len(state_msg.position)} | "
            f"Time: {state_msg.header.stamp.sec}.{state_msg.header.stamp.nanosec:09d}s | "
            f"J4: {positions.get('panda_joint4')} rad"
        )
        node.get_logger().info(summary, throttle_duration_sec=3.0)

    sub = node.create_subscription(
        JointState,
        '/joint_states',
        on_joint_state,
        qos_profile_sensor_data,
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('stop requested')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
        print('runtime stopped')
        print('final stats:', stats)


if __name__ == '__main__':
    main()
