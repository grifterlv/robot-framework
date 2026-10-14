import math
from copy import deepcopy
from dataclasses import dataclass
from builtin_interfaces.msg import Time
from geometry_msgs.msg import Point
from geometry_msgs.msg import TransformStamped
from std_msgs.msg import Header
from shape_msgs.msg import Mesh, MeshTriangle
from robot_framework_runtime.contracts import RequestContext
from robot_framework_runtime.contracts import validate_request_context


def _finite_float(value: int | float, field_name: str) -> float:
    """Check numeric fields without leaking integer-to-float overflow."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number")
    try:
        converted = float(value)
    except OverflowError as error:
        raise ValueError(f"{field_name} exceeds the floating-point range") from error
    if not math.isfinite(converted):
        raise ValueError(f"{field_name} must be a finite number")
    return converted


@dataclass(frozen=True)
class ObservationFrame:
    """Immutable data container holding validated 3D observation payload and optional localization."""
    context: RequestContext
    mesh: Mesh
    header: Header
    length_unit: str
    sample_clock_domain: str
    source: str
    capture_transform: TransformStamped | None = None
    target_frame_id: str | None = None
    transform_clock_domain: str | None = None

    def __post_init__(self):
        # 1. Verify context is an instance of RequestContext
        if not isinstance(self.context, RequestContext):
            raise ValueError(
                f"Expected RequestContext instance for context, got {type(self.context).__name__}"
            )

        # 2. Validate geometric mesh integrity
        validate_mesh(self.mesh)

        # 3. Validate observation metadata
        validate_observation_metadata(
            header=self.header,
            length_unit=self.length_unit,
            sample_clock_domain=self.sample_clock_domain,
        )

        # 4. Ensure data source is a non-empty string
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError(f"source must be a non-empty string, got {self.source!r}")

        # 5. Localization all-or-nothing validation
        loc_parts = (
            self.capture_transform,
            self.target_frame_id,
            self.transform_clock_domain,
        )

        # Case 1: All None is valid (raw unlocalized observation)
        if all(v is None for v in loc_parts):
            return

        # Case 2: Partial None is invalid (incomplete localization)
        if any(v is None for v in loc_parts):
            raise ValueError(
                "capture_transform, target_frame_id, and transform_clock_domain "
                "must either all be None or all be provided"
            )

        # Case 3: Fully localized - validate spatial consistency and temporal alignment
        validate_capture_transform(
            transform=self.capture_transform,
            source_frame_id=self.header.frame_id,
            target_frame_id=self.target_frame_id,
        )
        validate_capture_time(
            observation_header=self.header,
            transform=self.capture_transform,
            observation_clock_domain=self.sample_clock_domain,
            transform_clock_domain=self.transform_clock_domain,
        )

def validate_mesh(mesh: Mesh) -> None:
    """Validate data integrity and structural validity of a 3D geometric mesh.

    Rules:
    1. Input must be a Mesh instance.
    2. Empty mesh (0 vertices and 0 triangles) is permitted.
    3. Each vertex must be a Point instance, and x, y, z must all be finite numbers (no NaN or Inf).
    4. Each triangle must be a MeshTriangle instance containing exactly 3 indices.
    5. Each vertex index must satisfy: 0 <= index < number of vertices.

    Returns None if valid; raises ValueError if invalid.
    """
    # Rule 1: Check outer container type
    if not isinstance(mesh, Mesh):
        raise ValueError(f"Expected Mesh instance, got {type(mesh).__name__}")

    # Rule 2: Allow empty mesh (zero vertices and zero triangles)
    num_vertices = len(mesh.vertices)
    num_triangles = len(mesh.triangles)
    if num_vertices == 0 and num_triangles == 0:
        return None

    # Invalid state: Triangles exist without any vertices to reference
    if num_vertices == 0 and num_triangles > 0:
        raise ValueError("Mesh has triangles but 0 vertices")

    # Rule 3: Validate each vertex
    for i, vertex in enumerate(mesh.vertices):
        if not isinstance(vertex, Point):
            raise ValueError(f"Vertex at index {i} is not a Point instance")

        # Verify coordinates are finite numbers (not NaN or Inf)
        for axis_name, coord in (('x', vertex.x), ('y', vertex.y), ('z', vertex.z)):
            _finite_float(coord, f"Vertex {i} {axis_name}-coordinate")

    # Rules 4 & 5: Validate each triangle and check index bounds
    for tri_idx, triangle in enumerate(mesh.triangles):
        if not isinstance(triangle, MeshTriangle):
            raise ValueError(f"Triangle at index {tri_idx} is not a MeshTriangle instance")

        indices = triangle.vertex_indices
        if len(indices) != 3:
            raise ValueError(
                f"Triangle {tri_idx} must have exactly 3 vertex indices, got {len(indices)}"
            )

        for corner_idx, v_idx in enumerate(indices):
            # Convert numpy.int32 or int to Python int for bounds checking
            try:
                v_idx_int = int(v_idx)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Triangle {tri_idx} index {corner_idx} is not an integer: {v_idx}"
                )

            if not (0 <= v_idx_int < num_vertices):
                raise ValueError(
                    f"Triangle {tri_idx} references invalid vertex index {v_idx_int} "
                    f"(valid range: 0 to {num_vertices - 1})"
                )

    return None

def validate_observation_metadata(
    header: Header,
    length_unit: str,
    sample_clock_domain: str,
) -> None:
    """Validate 3D observation metadata (frame, timestamp, length unit, clock domain).

    Rules:
    1. header must be a Header instance.
    2. header.frame_id must be a non-empty string.
    3. stamp must be a Time message with non-boolean int32 sec and integer
       nanosec in the range 0 <= nanosec < 1_000_000_000.
    4. length_unit must be strictly "m".
    5. sample_clock_domain must be a non-empty string (allows "unknown").

    Returns None if valid; raises ValueError if invalid.
    """
    # Rule 1: Validate header type
    if not isinstance(header, Header):
        raise ValueError(f"Expected Header instance, got {type(header).__name__}")

    # Rule 2: Validate frame_id is a non-empty string
    if not isinstance(header.frame_id, str) or not header.frame_id.strip():
        raise ValueError(f"header.frame_id must be a non-empty string, got {header.frame_id!r}")

    # Rule 3: Validate the complete ROS Time message before reading its fields.
    stamp = header.stamp
    if not isinstance(stamp, Time):
        raise ValueError("header.stamp must be a Time message")
    sec = stamp.sec
    if isinstance(sec, bool) or not isinstance(sec, int):
        raise ValueError("header.stamp.sec must be a non-boolean integer")
    if not (-2**31 <= sec < 2**31):
        raise ValueError("header.stamp.sec must be in the ROS int32 range")

    nanosec = stamp.nanosec
    if isinstance(nanosec, bool) or not isinstance(nanosec, int):
        raise ValueError(f"header.stamp.nanosec must be an integer, got {type(nanosec).__name__}")
    if not (0 <= nanosec < 1_000_000_000):
        raise ValueError(
            f"header.stamp.nanosec must be in range [0, 1000000000), got {nanosec}"
        )

    # Rule 4: Validate length unit strictly equals "m"
    if length_unit != "m":
        raise ValueError(f'length_unit must be strictly "m", got {length_unit!r}')

    # Rule 5: Validate sample clock domain is a non-empty string
    if not isinstance(sample_clock_domain, str) or not sample_clock_domain.strip():
        raise ValueError(
            f"sample_clock_domain must be a non-empty string, got {sample_clock_domain!r}"
        )

    return None

def make_observation_frame(
    context: RequestContext,
    mesh: Mesh,
    header: Header,
    length_unit: str,
    sample_clock_domain: str,
    source: str,
    model: dict,
    active_session_id: str,
    capture_transform: TransformStamped | None = None,
    target_frame_id: str | None = None,
    transform_clock_domain: str | None = None,
) -> ObservationFrame:
    """Factory function creating an ObservationFrame with deep-copied isolation."""

    # Step 1: Validate context against current model and active session ID
    validate_request_context(
        context=context,
        model=model,
        active_session_id=active_session_id,
    )

    # Step 2: Validate input object types before cloning
    if not isinstance(mesh, Mesh):
        raise ValueError(f"Expected Mesh instance, got {type(mesh).__name__}")
    if not isinstance(header, Header):
        raise ValueError(f"Expected Header instance, got {type(header).__name__}")
    if capture_transform is not None and not isinstance(capture_transform, TransformStamped):
        raise ValueError(
            f"Expected TransformStamped instance for capture_transform, "
            f"got {type(capture_transform).__name__}"
        )

    # Step 3: Perform deep copy to isolate payloads and transform envelope
    isolated_mesh = deepcopy(mesh)
    isolated_header = deepcopy(header)
    isolated_transform = deepcopy(capture_transform)

    # Step 4: Construct and return the frozen ObservationFrame
    return ObservationFrame(
        context=context,
        mesh=isolated_mesh,
        header=isolated_header,
        length_unit=length_unit,
        sample_clock_domain=sample_clock_domain,
        source=source,
        capture_transform=isolated_transform,
        target_frame_id=target_frame_id,
        transform_clock_domain=transform_clock_domain,
    )

def validate_capture_transform(
    transform: TransformStamped,
    source_frame_id: str,
    target_frame_id: str,
) -> None:
    """Validate spatial transform metadata, frame directions, and numerical validity.

    Rules:
    1. transform must be a TransformStamped instance.
    2. source_frame_id and target_frame_id must be non-empty strings.
    3. header.frame_id must match target_frame_id.
    4. child_frame_id must match source_frame_id.
    5. Translation (x, y, z) and rotation (x, y, z, w) must all be finite numbers.
    6. Quaternion norm must approximate 1.0 with abs_tol=1e-6. No in-place normalization.
    7. A same-frame transform must have zero translation and zero quaternion
       x, y, z. Both quaternion signs are permitted under the norm check above.

    Returns None if valid; raises ValueError if invalid.
    """
    # Rule 1: Type check
    if not isinstance(transform, TransformStamped):
        raise ValueError(f"Expected TransformStamped instance, got {type(transform).__name__}")

    # Rule 2: Coordinate frame parameter checks
    if not isinstance(source_frame_id, str) or not source_frame_id.strip():
        raise ValueError(f"source_frame_id must be a non-empty string, got {source_frame_id!r}")
    if not isinstance(target_frame_id, str) or not target_frame_id.strip():
        raise ValueError(f"target_frame_id must be a non-empty string, got {target_frame_id!r}")

    # Rules 3 & 4: Frame directional alignment
    if transform.header.frame_id != target_frame_id:
        raise ValueError(
            f"header.frame_id mismatch: expected {target_frame_id!r}, "
            f"got {transform.header.frame_id!r}"
        )
    if transform.child_frame_id != source_frame_id:
        raise ValueError(
            f"child_frame_id mismatch: expected {source_frame_id!r}, "
            f"got {transform.child_frame_id!r}"
        )

    # Rule 5: Translation components check
    trans = transform.transform.translation
    translation_values = []
    for axis, val in (('x', trans.x), ('y', trans.y), ('z', trans.z)):
        translation_values.append(_finite_float(val, f"Translation {axis}"))

    # Rules 5 & 6: Rotation components and unit quaternion length check
    rot = transform.transform.rotation
    q_vals = []
    for axis, val in (('x', rot.x), ('y', rot.y), ('z', rot.z), ('w', rot.w)):
        q_vals.append(_finite_float(val, f"Rotation {axis}"))

    norm = math.hypot(*q_vals)
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError(
            f"Quaternion rotation is not normalized: norm={norm:.8f} (expected 1.0 +/- 1e-6)"
        )

    if source_frame_id == target_frame_id and (
        any(value != 0.0 for value in translation_values)
        or any(value != 0.0 for value in q_vals[:3])
    ):
        raise ValueError("A transform from a frame to itself must be identity")

    return None


def validate_capture_time(
    observation_header: Header,
    transform: TransformStamped,
    observation_clock_domain: str,
    transform_clock_domain: str,
) -> None:
    """Validate temporal alignment and clock domain consistency between observation and transform.

    Rules:
    1. transform must be a TransformStamped instance.
    2. Reuse validate_observation_metadata for both headers with length_unit="m".
    3. Reject if either clock domain is "unknown" (after strip).
    4. Exact equality of clock domain strings required before timestamp comparison.
    5. Integer pair (sec, nanosec) must be strictly identical.

    Returns None if valid; raises ValueError if invalid.
    """
    # Step 1: Type check on transform
    if not isinstance(transform, TransformStamped):
        raise ValueError(f"Expected TransformStamped instance, got {type(transform).__name__}")

    # Step 2: Validate both headers via existing metadata validator
    validate_observation_metadata(
        header=observation_header,
        length_unit="m",
        sample_clock_domain=observation_clock_domain,
    )
    validate_observation_metadata(
        header=transform.header,
        length_unit="m",
        sample_clock_domain=transform_clock_domain,
    )

    # Step 3: Reject "unknown" clock domains
    if observation_clock_domain.strip() == "unknown":
        raise ValueError("Cannot bind capture time with unknown observation clock domain")
    if transform_clock_domain.strip() == "unknown":
        raise ValueError("Cannot bind capture time with unknown transform clock domain")

    # Step 4: Clock domain strings must match exactly
    if observation_clock_domain != transform_clock_domain:
        raise ValueError(
            f"Clock domain mismatch: observation has {observation_clock_domain!r}, "
            f"transform has {transform_clock_domain!r}"
        )

    # Step 5: Compare integer timestamp tuples strictly
    obs_stamp = (observation_header.stamp.sec, observation_header.stamp.nanosec)
    tf_stamp = (transform.header.stamp.sec, transform.header.stamp.nanosec)
    if obs_stamp != tf_stamp:
        raise ValueError(
            f"Capture timestamp mismatch: observation stamp {obs_stamp} != transform stamp {tf_stamp}"
        )

    return None
