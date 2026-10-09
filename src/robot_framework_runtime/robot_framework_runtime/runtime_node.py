import math

import rclpy
from rclpy.qos import qos_profile_sensor_data
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


def main():
    rclpy.init()
    node = rclpy.create_node('runtime')
    node.get_logger().info('runtime started')

    stats = {
        'received': 0,
        'accepted': 0,
        'rejected': 0,
        'latest_valid': None,
    }

    def on_joint_state(msg: JointState):
        stats['received'] += 1

        try:
            positions = validate_joint_positions(msg)
        except ValueError as error:
            stats['rejected'] += 1
            node.get_logger().warning(
                f'Joint state rejected: {error}', throttle_duration_sec=3.0
            )
            return

        stats['accepted'] += 1
        stats['latest_valid'] = positions

        summary = (
            f"Received: {stats['received']} | Names: {len(msg.name)} | "
            f'Pos: {len(msg.position)} | '
            f'Time: {msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}s'
        )
        node.get_logger().info(summary, throttle_duration_sec=3.0)

    node.create_subscription(
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
