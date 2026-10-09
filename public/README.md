# Robot Framework

Robot Framework is an early ROS 2 project for building a standalone robot runtime.
It aims to make robot state, motion requests, execution results, and failure handling
explicit and reproducible.

The current Python node starts independently, subscribes to `/joint_states`,
validates joint positions, and retains the latest valid mapping by joint name.
Motion planning and trajectory execution are planned capabilities.

## Project documents

- [Purpose](PURPOSE.md): the problem, design goals, and engineering boundaries.
- [Development plan](PLAN.md): the sequence of capabilities and acceptance criteria.
- [Current status](CURRENT.md): verified behavior, open issues, and the next task.
- [Development timeline](TIMELINE.md): dated milestones for this project.

## Environment

The development environment is Ubuntu 24.04 with ROS 2 Jazzy, Python 3.12,
and colcon. Native Ubuntu and Ubuntu under WSL can use the commands below.
The recorded build and lifecycle checks used Ubuntu under WSL.

The package declares its ROS dependencies in
[package.xml](../src/robot_framework_runtime/package.xml).
Load the ROS environment in each terminal used for ROS commands.

## Build

Run from the repository root in an Ubuntu Bash terminal:

```bash
source /opt/ros/jazzy/setup.bash
colcon --log-base "$HOME/.cache/robot-framework/log" build \
  --build-base "$HOME/.cache/robot-framework/build" \
  --install-base "$HOME/.cache/robot-framework/install" \
  --symlink-install \
  --packages-select robot_framework_runtime
```

This keeps the generated build, install, and log directories in the user's cache.

## Run and stop

After a successful build, run:

```bash
source /opt/ros/jazzy/setup.bash
source "$HOME/.cache/robot-framework/install/setup.bash"
ros2 run robot_framework_runtime runtime
```

In another ROS environment terminal, `ros2 node list` should show `/runtime`.
The node can start while no joint-state publisher is available.
With a compatible publisher, valid messages update the position mapping;
invalid messages increase the rejection count and preserve that mapping.

Press Ctrl+C in the runtime terminal, then run `echo $?` to inspect the exit code.
The node prints its final counters during cleanup.
This check concerns software process cleanup; robot motion is not implemented yet.

## Prototype status

Recorded checks cover the installed entry point, startup and shutdown,
position validation, and a synthetic subscription probe.
Timestamp storage, clock domains, state-source verification, motion execution,
and cancellation remain open work. See [Current status](CURRENT.md).
