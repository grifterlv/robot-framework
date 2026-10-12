import math

def joint_order(source_names: list[str], target_names: list[str]) -> list[int]:
    if not isinstance(source_names, list) or not isinstance(target_names, list):
        raise ValueError("Arguments must be lists")

    if not source_names or not target_names:
        raise ValueError("Joint lists cannot be empty")

    for name in source_names + target_names:
        if not isinstance(name, str) or name == "":
            raise ValueError("Joint names must be non-empty strings")

    if len(source_names) != len(set(source_names)):
        raise ValueError("Duplicate names in source_names")
        
    if len(target_names) != len(set(target_names)):
        raise ValueError("Duplicate names in target_names")

    if set(source_names) != set(target_names):
        raise ValueError("Source and target names do not match")

    return [source_names.index(name) for name in target_names]

def reorder_point(
    point: list[float],
    source_names: list[str],
    target_names: list[str],
) -> list[float]:
    order = joint_order(source_names, target_names)

    if not isinstance(point, list):
        raise ValueError("Point must be a list")

    if len(point) != len(source_names):
        raise ValueError("Point length must match source_names length")

    for val in point:
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError("Point values must be numbers, not booleans or other types")
        try:
            is_finite = math.isfinite(val)
        except OverflowError as error:
            raise ValueError("Point values are too large to represent as floats") from error
        if not is_finite:
            raise ValueError("Point values must be finite (no NaN or Inf)")

    return [point[i] for i in order]

def validate_geometric_path(path: dict, model: dict) -> dict:
    validate_path_metadata(path, model)

    if "points" not in path or "times" not in path:
        raise ValueError("Path must contain 'points' and 'times'")

    if not isinstance(path["points"], list) or len(path["points"]) == 0:
        raise ValueError("Points must be a non-empty list")

    if path["times"] is not None:
        raise ValueError("Times must be exactly None")

    source_names = path["joint_names"]
    target_names = model["joint_names"]

    new_points = [
        reorder_point(pt, source_names, target_names) 
        for pt in path["points"]
    ]

    return {
        "model_id": path["model_id"],
        "model_version": path["model_version"],
        "joint_names": list(target_names),
        "units": dict(path["units"]),
        "points": new_points,
        "times": None,
        "kind": "geometric_path",
        "timing_status": "needs_time_parameterization",
    }

def validate_path_metadata(metadata: dict, model: dict) -> list[int]:
    if not isinstance(metadata, dict) or not isinstance(model, dict):
        raise ValueError("Metadata and model must be dictionaries")

    required_meta = {"model_id", "model_version", "joint_names", "units"}
    required_model = {"model_id", "model_version", "joint_names", "joint_types"}

    if not required_meta.issubset(metadata.keys()):
        raise ValueError("Metadata missing required fields")
    if not required_model.issubset(model.keys()):
        raise ValueError("Model missing required fields")

    for key in ["model_id", "model_version"]:
        if not isinstance(metadata[key], str) or not isinstance(model[key], str):
            raise ValueError(f"{key} must be strings")
        if metadata[key] == "" or model[key] == "":
            raise ValueError(f"{key} cannot be empty")
        if metadata[key] != model[key]:
            raise ValueError(f"{key} mismatch: {metadata[key]} != {model[key]}")

    order = joint_order(metadata["joint_names"], model["joint_names"])

    units = metadata["units"]
    jtypes = model["joint_types"]

    if not isinstance(units, dict) or not isinstance(jtypes, dict):
        raise ValueError("Units and joint_types must be dictionaries")

    if set(units.keys()) != set(metadata["joint_names"]):
        raise ValueError("Units keys must perfectly match input joint names")

    if not set(model["joint_names"]).issubset(jtypes.keys()):
        raise ValueError("Model joint_types missing configuration for some joints")

    for jname in metadata["joint_names"]:
        jtype = jtypes[jname]
        junit = units[jname]

        if jtype in ("revolute", "continuous"):
            if junit != "rad":
                raise ValueError(f"Joint {jname} ({jtype}) needs 'rad', got '{junit}'")
        elif jtype == "prismatic":
            if junit != "m":
                raise ValueError(f"Joint {jname} ({jtype}) needs 'm', got '{junit}'")
        else:
            raise ValueError(f"Unknown joint type '{jtype}' for {jname}")

    return order

def validate_times(times: list, point_count: int) -> list[float]:
    if isinstance(point_count, bool) or not isinstance(point_count, int):
        raise ValueError("point_count must be an integer, not a boolean or other type")
    if point_count <= 0:
        raise ValueError("point_count must be a positive integer")

    if not isinstance(times, list):
        raise ValueError("times must be a list")
    
    if len(times) != point_count:
        raise ValueError(f"times length ({len(times)}) must match point_count ({point_count})")

    new_times = []
    last_time = -1.0

    for i, t in enumerate(times):
        if isinstance(t, bool) or not isinstance(t, (int, float)):
            raise ValueError("Time values must be numbers, not booleans or other types")
        try:
            t_float = float(t)
        except OverflowError as error:
            raise ValueError("Time values are too large to represent as floats") from error
        if not math.isfinite(t_float):
            raise ValueError("Time values must be finite (no NaN or Inf)")

        if i == 0:
            if t_float < 0:
                raise ValueError("First time value must be greater than or equal to 0")
        else:
            if t_float <= last_time:
                raise ValueError("Time values must be strictly increasing")

        last_time =t_float
        new_times.append(t_float)

    return new_times

def validate_timed_path(path: dict, model: dict) -> dict:
    validate_path_metadata(path, model)

    if "points" not in path or "times" not in path:
        raise ValueError("Path must contain 'points' and 'times'")

    if not isinstance(path["points"], list) or len(path["points"]) == 0:
        raise ValueError("Points must be a non-empty list")
        
    if path["times"] is None:
        raise ValueError("Times cannot be None for a timed path")

    source_names = path["joint_names"]
    target_names = model["joint_names"]

    new_points = [
        reorder_point(pt, source_names, target_names)
        for pt in path["points"]
    ]

    new_times = validate_times(path["times"], len(new_points))

    return {
        "model_id": path["model_id"],
        "model_version": path["model_version"],
        "joint_names": list(target_names),
        "units": dict(path["units"]),
        "points": new_points,
        "times": new_times,
        "kind": "timed_path",
        "timing_status": "validated",
    }

def seconds_to_duration_parts(seconds: float) -> tuple[int, int]:
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise ValueError("Seconds must be a number (int or float), not boolean or other types")
    
    if seconds < 0:
        raise ValueError("Seconds cannot be negative")
        
    if seconds >= 2147483648:
        raise ValueError(f"Seconds value ({seconds}) exceeds ROS 2 int32 maximum (2147483647)")

    if math.isnan(seconds) or math.isinf(seconds):
        raise ValueError("Seconds must be finite (no NaN or Inf)")

    total_ns = round(float(seconds) * 1_000_000_000)
    sec, nanosec = divmod(total_ns, 1_000_000_000)
    
    if sec > 2147483647:
        raise ValueError(f"Seconds value ({sec}) exceeds ROS 2 int32 maximum (2147483647)")

    return int(sec), int(nanosec)
