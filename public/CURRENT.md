# Current Status

state_revision: 31

Updated: 2026-10-09.

The runtime receives and validates joint positions. A synthetic four-message
subscription probe passed. A complete feedback snapshot and motion execution
remain to be implemented.

## Verified behavior

- The Python package has an installed `runtime` entry point.
- Recorded lifecycle checks showed node discovery, SIGINT cleanup, exit code 0,
  and disappearance from the ROS graph after shutdown.
- Position validation rejects an empty name list, empty names, duplicate names,
  mismatched name/position lengths, and NaN or infinite positions.
- Valid input produces a mapping keyed by joint name.
- The four-message probe ended with `received=4`, `accepted=2`, `rejected=2`,
  and `latest_valid={'joint_a': 0.4, 'joint_b': 0.7}`; its exit code was 0.
- The callback's rejection branch returns before updating `latest_valid`.
  Intermediate preservation is supported by source trace; the probe did not
  capture intermediate snapshots.

See [Development timeline](TIMELINE.md) for dated milestones.

## Latest source checks

On 2026-10-09, direct validation of seven inputs and Python syntax checks passed.
The existing static test selection returned one failed, one passed, and one skipped.
The flake8 test reported 39 errors in the runtime module.

Runtime source SHA256 at this check:
`4c0eddd15f7629599d8fac18545fc1b198d9c75343a4428e6b931dd841a4a11a`.

The source checks imported definitions without initializing a ROS context.
The documentation update did not change or rebuild the runtime.

## Open issues

- The log joins seconds and nanoseconds without padding the nanoseconds to nine digits.
- The existing flake8 check fails.
- Position snapshots do not retain sample/receive times, clock domains, or state sources.
- The synthetic probe used a default zero sample stamp.
- Publisher identity, feedback changes, steady update behavior, and freshness remain open.
- A recorded software demo shutdown had process failures; the synthetic probe does not
  establish a clean shutdown for that demo.
- Trajectory execution, finite planning, continuous targets, and cancellation are planned.
- Package description and license metadata still contain generator placeholders.

## Next implementation task

The author will add a complete feedback snapshot after successful validation:
positions, original sample stamp, sample clock domain, local receive time and
clock domain, configured state source, and the actual subscribed topic.

Invalid input must leave every field of the previous snapshot unchanged.
Use an explicit synthetic source for probe input. Verify a simulator's publisher
and feedback behavior separately before labeling its state as simulator feedback.

## Documentation update

Revision 30 replaces the public project documents with English descriptions of
the runtime's purpose, development sequence, current status, and dated milestones.
It records documentation work only; the implementation remains at the state above.

Revision 31 organizes maintained public documents under `public/` and adds root
navigation files. The implemented behavior and source-check results are unchanged.
