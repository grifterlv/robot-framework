# Project Purpose

Robot Framework is a project for building a standalone ROS 2 robot runtime.
Its purpose is to make state validation, motion requests, execution results,
and failure handling explicit and reproducible.

## Design goals

- Run from this repository with documented dependencies and commands.
- Keep robot state separate from motion targets.
- Define joint identity, units, frames, timestamps, and state sources explicitly.
- Let external application clients use documented, explicit data contracts.
- Keep planning, execution, and feedback responsibilities understandable.
- Record failures and cancellation results alongside successful operations.

## Current implementation

The Python runtime subscribes to `/joint_states`.
It validates nonempty and unique joint names, matching position dimensions,
and finite position values before creating a joint-name-to-position mapping.

Each callback increments the received count.
Valid messages update the latest valid mapping and the accepted count.
Invalid messages increment the rejected count and preserve that mapping.

The runtime prints final counters during shutdown.
It currently stores positions only; timestamp storage, clock domains,
state-source labeling, and freshness checks remain to be implemented.

Motion planning and robot command execution are not yet implemented here.

## Planned capabilities

Development will proceed through bounded, separately verified steps:
state snapshots, finite motion requests, planning, execution, independent
feedback, cancellation, and fault recovery.

Each capability needs its own reproducible inputs, commands, and results.
Software simulation, virtual-controller tests, and physical-hardware tests
will be documented separately.
