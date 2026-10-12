# Current Status

state_revision: 70

Updated: 2026-10-12.

The runtime receives and validates joint positions. A synthetic four-message
subscription probe passed. The author has now implemented a complete feedback
snapshot. The author reports that a rejected message preserved the snapshot in
the two-message probe; raw final statistics and exit status have not been recorded
for that run. A subsequent runtime capture recorded 3706 accepted callbacks and
a complete final feedback snapshot. A later run recorded changing joint-position
feedback, 3180 accepted callbacks, SIGINT cleanup, and exit code 0. Current
publisher and active-state evidence remains open. Motion execution is planned.

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
- A subsequent final capture reported `received=3706`, `accepted=3706`, and
  `rejected=0`. It retained nine named positions, the original sample stamp,
  callback receive time, clock-domain labels, configured Mock source, and topic.
  Those counts do not establish zero transport loss or a stable feedback rate.
- A later run showed the named joint position changing in successive runtime
  logs and remaining in the final snapshot. It ended with `received=3180`,
  `accepted=3180`, `rejected=0`, SIGINT cleanup output, and immediate exit code 0.
  The two captures are separate runs; their counts are not combined.
- A direct source-module run returned `[1, 0]` for reversed joint-name input
  and rejected three malformed container cases with explicit `ValueError`.
- A subsequent combined run reordered a float point into a new list while
  preserving its input, accepted integer positions, and rejected 14 malformed
  name or point cases with `ValueError`. Reported wall time was 0.233 seconds.
- A metadata run accepted two valid configurations and rejected 12 malformed
  model, joint, type, or unit inputs with `ValueError`. Reported wall time was
  0.154 seconds.
- A geometric-path run reordered two valid points, retained explicit untimed
  status, and rejected 10 malformed paths with `ValueError`. Reported wall time
  was 0.217 seconds. The output-name isolation check failed: returned names
  still share the model list.
- After the output-name copy was added, a repeated run confirmed distinct
  output and model name lists, unchanged displayed input, normal reordering,
  and all 10 expected rejections. Reported wall time was 0.224 seconds.
- A relative-time run accepted two complete time lists and rejected 13 malformed
  inputs. Valid results were distinct output lists. Reported wall time was
  0.127 seconds.
- Numeric-overflow regression tests now pass all 16 cases on Python 3.12.3.
  Oversized positive and negative integers are rejected with `ValueError` by
  the point and time validators. Normal reordering, input preservation,
  nonfinite-value rejection, and time ordering remain verified.
- A timed-path run returned the expected three reordered points and relative
  times, rejected 10 malformed inputs with `ValueError`, and confirmed that
  edits to result names, units, positions, and times preserved the original
  path and model. Reported wall time was 0.129 seconds.
- An integer-duration run passed six normal conversions and six explicit
  invalid-input rejections. Extremely large finite input raised an unexpected
  `OverflowError` before the range check. Reported wall time was 0.758 seconds;
  complete duration-helper acceptance failed.
- After moving input-range checks earlier, a repeat run passed all six normal
  conversions and seven explicit rejections without an unexpected traceback.
  Reported wall time was 0.152 seconds.
- A source-module ROS conversion run verified the three-point trajectory fields,
  integer positions converted to floats, independent points, empty optional
  fields, five explicit rejections, and preservation of input and other points
  after result edits. Reported wall time was 0.257 seconds. Build/install was
  checked in the subsequent run below.
- A subsequent package build and installation check passed: the package prefix
  resolved to the configured cache installation, the conversion module imported
  from the associated build tree, and the command chain exited 0. Reported
  package build time was 2.03 seconds; the build summary reported 2.29 seconds.
- A request-identity run verified normal construction, original-value
  preservation, five explicit invalid-field rejections, blocked reassignment,
  and preservation of the session value. Reported wall time was 0.190 seconds.
- A context-matching run returned `None` for matching configuration, explicitly
  rejected three configuration mismatches and eight invalid arguments, and
  preserved request and model values. Reported wall time was 0.170 seconds.
- A path-request preparation run verified geometric and timed branches, seven
  preparation failures, four carrier-structure failures, context retention, and
  input isolation. Reported wall time was 0.285 seconds.
- A normal typed-feedback probe verified named positions, preserved unavailable
  effort and metadata, and isolation after input position and stamp edits. It
  recorded exit code 0 and 0.589 seconds reported wall time.
- A feedback boundary run accepted a valid boundary frame, rejected 16 factory
  inputs and one invalid carrier, blocked outer-field assignment, and preserved
  the input after output edits. Exit code was 0; reported wall time was 0.711 seconds.

See [Development timeline](TIMELINE.md) for dated milestones.

## Latest source checks

The latest source review on 2026-10-09 confirmed that valid messages store
positions, the original sample stamp, clock-domain labels, callback-entry
monotonic time, the configured source, and the actual subscribed topic.
Rejected messages return before replacing any snapshot fields. Nanosecond
display now uses nine digits.

The author has added a named joint position to the throttled log. It reads the
validated mapping with `dict.get`, so missing joint data displays as `None` and
remains distinct from a zero position. A separator between time and position
still needs a small readability adjustment.

Runtime source SHA256 at this review:
`a00ef728b6ff9939de46a8cbef24cea9615ec63e6b97330b883b44a0beb3348c`.

The earlier `git diff --check` reported one trailing-whitespace issue in the runtime module.
No build, syntax check, static test, or ROS probe was run for this revision.

An earlier check on the same date passed direct validation of seven inputs and
Python syntax checks. Its static test selection returned one failed, one passed,
and one skipped; the flake8 test reported 39 errors in that earlier source.

Runtime source SHA256 at the earlier check:
`4c0eddd15f7629599d8fac18545fc1b198d9c75343a4428e6b931dd841a4a11a`.

Those earlier checks imported definitions without initializing a ROS context.
Their results do not verify the latest source revision.

The author has implemented `joint_order` in `path_validation.py` and repaired
the outer-container check. The saved source rejects non-list containers before
concatenating the lists. A direct run returned `[1, 0]` for valid reversed input
and rejected two strings and both mixed string/list cases with `ValueError`.
A subsequent combined point run also covers empty, duplicate, missing, extra,
and malformed joint-name cases.

The author has now added `reorder_point`. Source review confirms list and
dimension checks, rejection of booleans and non-numeric values, finite-value
checks, and construction of a new list in the requested joint order. A combined
direct run verifies two valid point cases and 14 malformed name or point
cases for that recorded revision. The normal float case also records unchanged input and
a distinct output list.

Path-validation source SHA256 for the recorded combined point run:
`4e468e8f06127347760e54a479ae7cbab79535c05e22a07bf7b934dd940d8177`.

The author has added `validate_path_metadata`. Source review confirms required
dictionary fields, non-empty model identity and version checks, joint-name
validation, exact unit-name coverage, target joint-type coverage, and units by
joint type. It returns the ordering only after all metadata checks pass. A direct
run now records two valid configurations and 12 explicit validation failures
for this source revision. Matching declarations do not establish kinematic
equivalence, collision validity, or executable timing.

Path-validation source SHA256 for the recorded metadata run:
`a9454b6b73f678e11e2a322a9dc3852b5957c89e09d3480616c462abb44bccfb`.

The author has saved `validate_geometric_path`. It validates metadata and every
point, accepts only explicit untimed input, and reports pending time
parameterization. The original run exposed a shared-reference issue. The author
has now copied the returned names; a repeated run confirms distinct name lists,
the normal two-point path, and 10 explicit validation failures. A separate
output-mutation capture was not supplied.

Path-validation source SHA256 for the recorded geometric-path run:
`cd2b7b4f61e8d44300b125d201eb3a2708130aab63fd55fa39794eeb71bf73ab`.

The author has corrected the relative-time helper's control flow. Source review
confirms point-count, container, numeric-type, and finite-value checks, a
nonnegative first time, and strictly increasing later times. Every valid time is
appended to a new float list, which returns only after the loop completes. A direct
run now records two accepted time lists and 13 explicit validation failures for
this revision. These checks do not establish motion feasibility.

Path-validation source SHA256 for the recorded relative-time run:
`f42dbc99f9630754d389ca9a1717aa15d5e677bad74f1a198f691b19f615f59e`.

The author has corrected the timed-path name keys and added the result return.
Source review confirms metadata, every point, and relative-time checks, followed
by construction of a new result dictionary. The time-count argument uses the
number of reordered points. Names and units are copied; points and times come
from validators that create new lists. A direct run now verifies normal output,
10 invalid-input cases, and preservation of the original path and model after
result edits for this revision. ROS message conversion remains unimplemented.

Path-validation source SHA256 for the recorded timed-path run:
`c7512044d0f4581b56c273023eff0b3879fe3f1ec25dc3ca77363fc2ae94e25a`.

The author has repaired `seconds_to_duration_parts`. Input-range checks now
precede finite-value checks and floating-point operations; NaN and final
integer-seconds checks remain. The original run exposed an overflow for
extremely large finite input. A repeat run now verifies all six normal
conversions and seven explicit rejections without an unexpected traceback.

Path-validation source SHA256 for the recorded duration-helper run:
`7dd86b57627e70934ee6a54a3053a904eb9fb853e072e8a86adaceb7a6436ec3`.

The point and time validators now translate integer-to-float overflow into
`ValueError`, preserving their input-rejection contract. Time conversion is
checked before finite-value and ordering checks; normal point integers are
retained. The new `test_path_validation.py` reproduced seven overflow failures
before the fix and passed all 16 cases afterward on Python 3.12.3 under WSL.
Three direct `prepare_path_request` checks also rejected oversized geometric
positions, timed positions, and timed times without changing path or model
inputs. These checks use pure data and do not initialize ROS or submit motion.

Path-validation source SHA256 for the numeric-overflow regression run:
`317d0d47c2d44cf0610e412e9c25d2aab63e308be5c2f84d80679cae447a79eb`.

The author has implemented `to_joint_trajectory` in a separate ROS conversion
module and declared the `trajectory_msgs` runtime dependency. Source review
confirms validation before conversion, copied names and float positions,
independent point messages, normalized relative times, and strictly increasing
integer nanoseconds after rounding. The function returns a data object without
controller submission. A source-module run now verifies normal and integer
input, five explicit failures, independent points, and result isolation for
this revision. A subsequent build and installation check passed for the same
source revision, including package discovery and conversion-module import.
A correct single-point example output is user-reported; its raw output was
not supplied.

Trajectory-conversion source SHA256 at this review:
`430da8ce55623be51c172ce355244a33848a0d681e141d886662fce30154d1cc`.

Package manifest SHA256 at this review:
`210d767a7230bdc4fedad114b0e51c2d3d66bb70535575d1e1ca84fefbd3f415`.

The author has added a frozen `RequestContext` dataclass with five required
identity fields. Source review confirms explicit string and nonblank checks
for each field during post-initialization, errors identifying the field, and
preservation of the original values. A direct run now verifies normal
construction, five representative invalid fields, original-value preservation,
and blocked field reassignment. This type validates identity format only;
comparison with the current model and session remains a separate pending
ingress check. Frozen fields do not make future nested payloads deeply immutable.

Contracts source SHA256 for the recorded identity-format run:
`79ee862a4484d1d00a2536c92186d16a75190567a71a344a07b12ccf57ba58b9`.

The author has added `validate_request_context`. Source review confirms explicit
argument checks and comparison of model identity, version, and active session,
with descriptive `ValueError` on mismatch. A normal call returns `None` by
reaching the end of the function. A direct run now verifies normal matching,
three mismatches, eight invalid arguments, and value preservation. This helper
does not validate a path or implement a ROS ingress.

Latest contracts source SHA256 at this review:
`9d5d954249429d7c3d22c3b4d16c0a2508caecfb5bcd528d3122e1864f1e5827`.

The author has implemented a typed `PathRequest` carrier and
`prepare_path_request`. Source review confirms identity matching before path
processing, explicit presence of the timing field, geometric/timed routing
through the existing validators, matching kind/payload types, and retention
of the request context. A combined run now verifies both normal branches, seven
preparation failures, four carrier-structure failures, context retention, and
input isolation. A stale session is rejected before invalid point data is
processed. Direct carrier construction checks structure only; the preparation
function performs full data validation for this scope.

Path-request source SHA256 at this review:
`3b4ac867ec13b40348b07f1dfb69cb9129d10c5c2ac48f203790b74a12711679`.

The author has saved `FeedbackFrame` and its copy-producing factory, and repaired
the position-validator call to pass one `JointState` message. Source review now
passes for this scope. A normal probe now verifies named positions, preserved
NaN effort, sample and receive metadata, a distinct message object, and isolation
after input edits. A boundary run now verifies a valid boundary frame, 16 factory
input rejections, one invalid carrier, blocked outer-field assignment, and input
preservation after output edits. Callback integration remains pending. The
checks use synthetic metadata, not publisher evidence.

Feedback source SHA256 at this review:
`bfe2ff96fe5d143230dd9ab4952d99e80f71320530cc7a293270ab69bf34d703`.

## Open issues

- The earlier two-message preservation report still lacks raw final statistics
  and exit status. The subsequent runtime capture records full snapshot fields,
  and a later run adds feedback-change and exit evidence.
- A trailing-whitespace issue remains; the earlier flake8 failures have not been rechecked.
- The recorded four-message probe used a default zero sample stamp.
- Current publisher identity, active-state output, steady update behavior, and freshness remain open.
- Typed feedback has passing normal/rejection/boundary checks; callback integration is pending.
- ROS ingress, observation, and result contracts remain planned.
- The new contracts module needs installation verification as the contracts are completed.
- A recorded software demo shutdown had process failures; the synthetic probe does not
  establish a clean shutdown for that demo.
- Trajectory execution, finite planning, continuous targets, and cancellation are planned.
- Package description and license metadata still contain generator placeholders.

## Next verification task

Verify the current simulator publisher, active state broadcaster, and Mock
hardware backend, then capture one complete joint-state message. The author has
identified the two Mock hardware components and reports unavailable effort
values; raw publisher and active-state output is still unrecorded.

Archive the current publisher and active-state output to close the source
verification gap. The recorded position changes do not define a complete
reached-state criterion.

Joint-name, single-point, model, and unit validation have normal and failure-case
evidence. The geometric-path run also covers a normal path, 10 invalid paths,
and distinct output names after the copy correction. The relative-time helper
also has normal and failure-case evidence. The timed-path entry point now has
normal three-point output, 10 rejected inputs, and result-isolation evidence.
The repaired integer duration helper now has six normal conversions and seven
explicit rejection cases. ROS trajectory conversion and the message dependency
now have direct runtime evidence for the normal three-point message, integer
input, five failures, independent points, and result isolation. The updated
build and installation check also passed. The minimal request identity type is
verified by normal construction, five invalid-field cases, value preservation,
and blocked reassignment. The model/session comparison helper also has normal
matching, three configuration mismatch cases, eight invalid arguments, and value
preservation evidence. Typed path-request preparation now has runtime evidence
for geometric and timed normal branches, seven preparation failures, four
carrier-structure failures, context retention, and input isolation. Explicit
untimed input retains its geometric path and pending timing status; timed input
uses the existing ROS conversion. A typed feedback frame and factory are now
saved and source-reviewed after the call correction, with a passing normal
snapshot probe and passing rejection/boundary checks. The next task moves
position validation into a shared module and updates both callers before
callback integration, keeping dependencies free of a runtime/feedback import
cycle. The frame reuses `JointState` and checks source, clock, and receive metadata while
preserving unavailable optional effort. Observation and result contracts
follow incrementally. Model identity
belongs to the application request; `header.frame_id` identifies a coordinate
frame. Untimed input remains explicitly pending time parameterization. This
stage constructs data objects only; controller submission remains a later task.

Invalid input must leave every field of the previous snapshot unchanged.
Use an explicit synthetic source for probe input. Verify a simulator's publisher
and feedback behavior separately before labeling its state as simulator feedback.

## Documentation update

Revision 30 replaces the public project documents with English descriptions of
the runtime's purpose, development sequence, current status, and dated milestones.
It records documentation work only; the implementation remains at the state above.

Revision 31 organizes maintained public documents under `public/` and adds root
navigation files. The implemented behavior and source-check results are unchanged.

Revision 32 records the author's feedback-snapshot implementation and source
review. Its two-message runtime probe remains pending.

Revision 33 records the author's report that the rejected message preserved the
snapshot. The run's raw statistics and exit status remain unrecorded; the next
task is current simulator-source verification.

Revision 34 records the author's identification of Mock hardware components.
Publisher and active-state evidence remains open; the next source task is a
named-joint log field for the runtime pose-change check.

Revision 35 records the saved named-joint log field and source review. Build and
runtime pose-change verification remain pending.

Revision 36 records a complete final snapshot from 3706 accepted callbacks.
Before/after pose, publisher, and exit evidence remain open for that run.

Revision 37 records feedback changes and clean exit from a later 3180-callback
run. Source evidence remains open; independent named-path validation is next.

Revision 38 records the saved joint-order helper and its source-review findings.
The outer-container check and direct runtime cases remain pending.

Revision 39 records the repaired outer-container check and four passing direct
cases. Name-validation failures and complete path validation remain pending.

Revision 40 records the next point-validation task. No new implementation or
runtime result is recorded; name-failure verification remains pending.

Revision 41 records the saved point validator and source review. Normal and
failure-case runs remain pending; no execution result is inferred from review.

Revision 42 records the combined point and name-validation run: two normal
cases, 14 explicit rejections, and 0.233 seconds reported wall time. Metadata
validation is the next implementation task.

Revision 43 records the saved model and unit metadata validator and source
review. Runtime verification remains pending; model declarations alone do not
establish kinematic equivalence or motion validity.

Revision 44 records the metadata run: two accepted configurations, 12 explicit
rejections, and 0.154 seconds reported wall time. The geometric-path entry point
is the next implementation task; timing and ROS conversion remain pending.

Revision 45 records the saved geometric-path entry point and source review.
Returned names still share the model list; isolation and runtime verification
remain pending.

Revision 46 records the geometric-path run: normal reordering, 10 explicit
rejections, and 0.217 seconds reported wall time. The output-name isolation
check failed; copying the names and focused verification remain pending.

Revision 47 records the copied output names and repeated path verification:
distinct name lists, expected normal data, 10 explicit rejections, and 0.224
seconds reported wall time. Relative-time validation is the next task.

Revision 48 records the saved relative-time helper and source-review findings.
Control-flow indentation needs correction; direct time-case verification remains
pending. No new runtime acceptance result is recorded.

Revision 49 records the corrected relative-time control flow and source review.
Normal and invalid time cases remain pending; no execution result is inferred
from the saved source.

Revision 50 records the relative-time run: two accepted lists, 13 explicit
rejections, and 0.127 seconds reported wall time. Timed-path integration is the
next implementation task; ROS conversion remains pending.

Revision 51 records the saved timed-path entry and source review. Name-key
corrections and a result return are required before direct verification; no new
execution result is recorded.

Revision 52 records the corrected timed-path entry and source review. Direct
normal, invalid-input, and result isolation checks remain pending; no runtime
acceptance result is inferred from review.

Revision 53 records the timed-path run: expected three-point output, 10 explicit
rejections, preserved input and model after result edits, and 0.129 seconds
reported wall time. Integer duration representation is the next task; ROS
trajectory objects and execution remain unimplemented.

Revision 54 records the saved integer duration helper and source review. Normal
and boundary runs remain pending; extremely large finite inputs need explicit
rejection before floating-point overflow. No runtime result is inferred from
source inspection.

Revision 55 records six normal duration conversions, six expected rejections,
and a confirmed overflow for extremely large finite input. Reported wall time
was 0.758 seconds. Earlier input-range validation and a repeat run are pending;
complete duration-helper acceptance has not passed.

Revision 56 records the repaired input-range checks and repeated duration
verification: six normal conversions, seven explicit rejections, and 0.152
seconds reported wall time. ROS trajectory object conversion is the next task;
no controller submission is implemented.

Revision 57 records the saved ROS conversion module, message dependency, and
passing source review. Full conversion runtime acceptance and updated
build/install verification remain pending; no execution result is inferred
from source inspection or the reported single-point example.

Revision 58 records the full source-module ROS conversion run: normal and integer
positions, five explicit rejections, independent output points, result isolation,
and 0.257 seconds reported wall time. Updated build/install verification and
typed application contracts remain pending.

Revision 59 records the successful package build and installation check:
configured package prefix, conversion-module import and entry point, and
command-chain exit code 0. Reported build times were 2.03 seconds for the package
and 2.29 seconds in the summary. Minimal typed request identity is the next task.

Revision 60 records the saved request identity dataclass and passing source
review. Construction, invalid-field, and reassignment checks remain pending;
current-model/session matching is not inferred from identity-format validation.

Revision 61 records the request-identity run: normal construction, five explicit
invalid-field rejections, original-value preservation, blocked reassignment,
and 0.190 seconds reported wall time. Model/session comparison is the next task;
complete request acceptance is not inferred from format checks.

Revision 62 records the saved model/session matching helper and passing source
review. Normal matching, configuration mismatches, and invalid-argument runs
remain pending; path acceptance and a ROS ingress are not inferred from review.

Revision 63 records the context-matching run: normal `None`, three configuration
mismatches, eight invalid arguments, preserved values, and 0.170 seconds reported
wall time. Typed path-request composition is the next task; no ROS ingress or
controller submission is implemented.

Revision 64 records the saved typed path request and preparation function,
with passing source review. Combined normal, failure, and isolation runs remain
pending; no execution behavior is inferred from carrier construction.

Revision 65 records the path-request preparation run: two normal branches,
seven preparation rejections, four carrier-structure rejections, retained
context, preserved inputs, and 0.285 seconds reported wall time. Typed feedback
is the next implementation task; controller submission remains unimplemented.

Revision 66 records the saved feedback type and factory, with a blocking
position-validator call mismatch found during source review. Correction and
normal/failure runtime verification remain pending; no new acceptance is inferred.

Revision 67 records the corrected position-validator call and passing feedback
source review. Normal/failure runtime verification, callback integration, and
the remaining observation/result contracts and acceptance configuration are pending.

Revision 68 records the passing normal feedback probe: named position values,
preserved unavailable effort and metadata, message-copy isolation, exit code 0,
and 0.589 seconds reported wall time. Rejection and boundary cases are next;
callback integration and the remaining contracts are still pending.

Revision 69 records the feedback rejection/boundary run: a valid boundary frame,
17 explicit invalid-input rejections, frozen outer fields, preserved input after
output edits, exit code 0, and 0.711 seconds reported wall time. Shared validation
and callback integration are next; no new runtime subscription behavior is inferred.

Revision 70 records the point/time numeric-overflow correction: seven regression
failures before the fix, all 16 cases passing afterward, and three successful
outer request-rejection checks. No build, ROS node, or motion request was run.
