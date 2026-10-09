# Development Timeline

This timeline records the development of the ROS runtime in this repository.
It was assembled on 2026-10-09 from dated local development notes and recorded
outputs. It summarizes milestones; it is not a record of historical Git commits.

## Recorded milestones

| Date | Milestone | Evidence and scope |
| --- | --- | --- |
| 2026-10-04 | Local project established | The project directory and local Git boundary were established. Package creation, implementation, and runtime verification were separate development steps. |
| 2026-10-05 | Minimal runtime lifecycle verified | The installed `runtime` entry point started, appeared as `/runtime`, handled SIGINT, exited with code 0, and disappeared from the queried ROS graph. |
| 2026-10-05 | Development simulation environment checked | The official Panda Mock example planned and executed a goal, and joint positions changed. This was an environment example check; this runtime did not issue motion requests. |
| 2026-10-08 | Joint-state reception and validation checked | Author-run checks recorded reception summaries and a clean exit. Six validation cases covered valid mapping, duplicate names, dimension mismatch, NaN, infinity, and an empty name list. |
| 2026-10-09, record date | Synthetic callback probe passed | An author-run four-message check through the installed entry point produced 4 received, 2 accepted, 2 rejected, the final valid mapping, and exit code 0. |
| 2026-10-09 | Source checks and public documentation prepared | Seven direct validation inputs and Python syntax checks passed. Static tests found one failure, one pass, and one skip. The English project documents were prepared with the runtime source unchanged. |

The early entries describe local records rather than commits created on those dates.
At the time this timeline was prepared, the repository had no commits or configured remote.

## Callback milestone

The recorded probe inputs were:

| Input | Result |
| --- | --- |
| `joint_b=0.2`, `joint_a=0.1` | Accepted |
| Two entries named `joint_a` | Rejected |
| One empty joint name | Rejected |
| `joint_a=0.4`, `joint_b=0.7` | Accepted |

The final recorded output was:

```text
final stats: {'received': 4, 'accepted': 2, 'rejected': 2, 'latest_valid': {'joint_a': 0.4, 'joint_b': 0.7}}
exit code: 0
```

This establishes input classification and the final mapping for that probe.
Its sample stamps were zero, and it did not measure freshness or a stable feedback
frequency. The current rejection branch preserves the previous mapping by returning
before the update; intermediate probe snapshots were not captured.

## Next milestones

Complete timestamped state snapshots and publisher verification, then add named
path validation and request/result contracts. Execution in software simulation,
independent feedback, cancellation, finite planning, and continuous targets follow
as separately verified capabilities. See [Development plan](PLAN.md).
