from dataclasses import dataclass

@dataclass(frozen=True)
class RequestContext:
    request_id: str
    task_id: str
    session_id: str
    model_id: str
    model_version: str

    def __post_init__(self):
        # Create a list of tuples containing field names and their actual values
        fields = [
            ("request_id", self.request_id),
            ("task_id", self.task_id),
            ("session_id", self.session_id),
            ("model_id", self.model_id),
            ("model_version", self.model_version)
        ]

        for name, value in fields:
            # Check if the value is strictly a string
            if not isinstance(value, str):
                raise ValueError(f"Field '{name}' must be a string.")
            
            # Check if the string is empty or contains only whitespace
            if not value.strip():
                raise ValueError(f"Field '{name}' cannot be empty or just whitespace.")

def validate_request_context(
    context: RequestContext,
    model: dict,
    active_session_id: str,
) -> None:
    # 1. Parameter validity checks
    if not isinstance(context, RequestContext):
        raise ValueError("context must be an instance of RequestContext")
        
    if not isinstance(model, dict):
        raise ValueError("model must be a dictionary")
        
    for key in ["model_id", "model_version"]:
        if key not in model:
            raise ValueError(f"model dictionary must contain '{key}'")
        val = model[key]
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"model['{key}'] must be a non-empty string")
            
    if not isinstance(active_session_id, str) or not active_session_id.strip():
        raise ValueError("active_session_id must be a non-empty string")

    # 2. Context matching checks
    if context.model_id != model["model_id"]:
        raise ValueError(
            f"Model ID mismatch: request expects '{context.model_id}', "
            f"but active model is '{model['model_id']}'"
        )
        
    if context.model_version != model["model_version"]:
        raise ValueError(
            f"Model version mismatch: request expects '{context.model_version}', "
            f"but active version is '{model['model_version']}'"
        )
        
    if context.session_id != active_session_id:
        raise ValueError(
            f"Session ID mismatch: request belongs to '{context.session_id}', "
            f"but active session is '{active_session_id}'"
        )