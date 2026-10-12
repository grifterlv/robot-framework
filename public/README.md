# Robot Framework

Robot Framework is an early ROS 2 project for building a standalone robot runtime.
It aims to make robot state, motion requests, execution results, and failure handling
explicit and reproducible.

The current Python node starts independently, subscribes to `/joint_states`,
validates joint positions, and retains the latest valid feedback snapshot.
The snapshot includes positions keyed by joint name, the original sample stamp,
clock-domain labels, callback-entry monotonic time, configured source, and topic.
Recorded final captures contain all snapshot fields. A later run records
position feedback changes, SIGINT cleanup, and exit code 0; current publisher
and active-state evidence remains open.
The throttled log now includes one simulator joint selected by name; missing
joint data displays as `None`. This field has shown position changes in a
recorded simulator session.
Motion planning and trajectory execution are planned capabilities.

A separate `joint_order` helper computes source indices in a requested joint-name
order. Direct checks cover valid reversed input and malformed containers;
the path-validation and ROS conversion evidence is described below.
The author has added `reorder_point` to validate a single position list and
reorder it by joint name. A direct run covers valid float and integer positions,
unchanged input, a distinct output list, and 14 rejected name or point cases.
A model and per-joint unit metadata validator has direct evidence for two valid
configurations and 12 rejected inputs. A geometric-path run verifies normal
reordering and 10 rejected inputs, retaining explicit untimed status. After an
output-name copy correction, a repeated run confirms distinct result and model
name lists. A relative-time run accepts two valid lists and rejects 13 malformed
inputs, returning a distinct list for valid data. A timed-path run verifies three
reordered points, 10 rejected inputs, and unchanged input and model after edits
to the result. After an earlier overflow was repaired, a repeated integer
duration run verifies six normal conversions and seven rejected inputs.
A source-module ROS trajectory run verifies three reordered points, relative
times, integer positions converted to floats, independent points, empty optional
fields, five explicit rejections, and result isolation. The message dependency
is declared; a subsequent build and installation check confirms the package
prefix, conversion-module import, and exit code 0. A request-identity run verifies
normal construction, five rejected fields, preserved values, and blocked field
reassignment. A model/session matching run verifies normal matching, three
configuration mismatches, eight invalid arguments, and preserved values.
Typed path-request preparation has combined evidence for geometric and timed
branches, seven preparation failures, four carrier-structure failures, retained
context, and isolated inputs. A normal typed-feedback probe verifies named
positions, preserved unavailable effort and metadata, copy isolation, and exit
code 0. A boundary run verifies a valid frame, 17 rejected inputs, frozen outer
fields, and input preservation after output edits. Moving validation into a
shared module and integrating typed feedback into the callback are next.
Observation and result contracts follow incrementally.

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

After a successful build, inspect the conversion-module installation in the
same Ubuntu terminal:

```bash
source "$HOME/.cache/robot-framework/install/setup.bash"
ros2 pkg prefix robot_framework_runtime
python3 - <<'PY'
import robot_framework_runtime.trajectory_conversion as conversion
print("module_file", conversion.__file__)
print("entry", conversion.to_joint_trajectory.__name__)
PY
```

With symlink installation, the module path may point to the source checkout or
the associated build tree. The recorded installation check imported the module
from the configured cache build tree and resolved the expected package prefix.

## Run and stop

After a successful build, run:

```bash
source /opt/ros/jazzy/setup.bash
source "$HOME/.cache/robot-framework/install/setup.bash"
ros2 run robot_framework_runtime runtime
```

In another ROS environment terminal, `ros2 node list` should show `/runtime`.
The node can start while no joint-state publisher is available.
With a compatible publisher, valid messages update the feedback snapshot;
invalid messages increase the rejection count and preserve the previous snapshot.

Press Ctrl+C in the runtime terminal, then run `echo $?` to inspect the exit code.
The node prints its final counters during cleanup.
This check concerns software process cleanup; robot motion is not implemented yet.

## Prototype status

Recorded checks cover the installed entry point, startup and shutdown,
position validation, a synthetic subscription probe, and a subsequent full
feedback snapshot from 3706 accepted callbacks. A separate 3180-callback run
records changing position feedback and exit code 0.
The saved sample-clock domain remains unknown; configured source labels still
need publisher evidence.
Publisher identity, sample-clock identification, freshness, motion execution,
and cancellation remain open work. See [Current status](CURRENT.md).
