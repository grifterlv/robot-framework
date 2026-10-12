# Development Plan

Updated: 2026-10-09.

Build a standalone runtime incrementally. The initial development target is a
seven-to-ten-development-day software prototype. Progress follows acceptance
evidence rather than elapsed calendar days.

## Capability sequence

| Stage | Work | Acceptance evidence |
| --- | --- | --- |
| D1 | Environment, ROS package, build, and lifecycle | Reproducible build, installed entry point, node discovery, and clean exit |
| D2 | State snapshots, named paths, and application contracts | Valid and invalid input cases; explicit joint identity, units, frames, times, and state sources |
| D3 | Finite trajectory execution in software simulation | A request reaches an executor; independent feedback, result, timeout, and cancellation are observable |
| D4 | Client requests and execution ownership | A client submits explicit data; overlapping requests and stale sessions are handled |
| D5 | Observations and replay | Typed observations carry frames, timestamps, and calibration; failed capture remains distinct from an empty observation |
| D6 | Freshness and fault handling | Disconnect, expired input, invalid frames, stop, and recovery each have recorded outcomes |
| D7 | Reproducible prototype demonstration | Fresh startup, finite request, feedback, cancellation, and exported results are repeatable |
| D8 | Finite planning and continuous target mode | Planning and Servo each pass their own model, input, feedback, and stop checks |
| D9 | Repeated verification | Fixed configurations and repeated normal and fault cases support measured conclusions |
| D10 | Startup reproduction and capability review | Documented setup reproduces verified capabilities and records remaining work |

These stages describe planned capabilities. They do not imply that the runtime
already executes robot motion. Model, controller, or clock gaps can change the
development estimate.

## Current task

The D2 state snapshot stores positions, the original sample stamp, its clock
domain, callback receive time, configured state source, and actual topic.
Recorded runs include position changes and clean shutdown. Current publisher
and active-state evidence still needs to be archived.
Invalid input must preserve the previous snapshot in full.

State-source configuration needs verification against the actual publisher.
Unknown clock relationships must remain explicit until an age calculation is valid.

Now validate and reorder named paths, distinguish geometric paths from timed
trajectories, and define request, feedback, observation, and result contracts.
Robot model selection and limits need their own checks.

## Engineering boundaries

- Use ROS software simulation for the initial stages.
- Treat finite planning, continuous targets, and trajectory execution as separate modes.
- Assign one execution owner to a robot session and reject stale session input.
- Keep commanded targets separate from observed state.
- Confirm cancellation and stopping through executor results and valid feedback.
- Verify model identity, joint types, limits, base frames, and tool transforms.
- Use a defined clock domain for each timestamp and local steady time for timeouts.

Virtual-controller and physical-hardware work belong to later stages with their
own setup, feedback, execution, and stopping criteria.
