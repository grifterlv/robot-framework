from dataclasses import dataclass
from enum import Enum
from robot_framework_runtime.contracts import RequestContext
from robot_framework_runtime.observation_frames import ObservationFrame


class CaptureStatus(Enum):
    """Standardized terminal statuses for sensor capture operations."""
    CAPTURED = "captured"
    FAILED = "failed"
    NOT_RECEIVED = "not_received"


@dataclass(frozen=True)
class CaptureOutcome:
    """Immutable outcome record capturing the terminal state of a 3D observation request."""
    context: RequestContext
    status: CaptureStatus
    frame: ObservationFrame | None = None
    reason: str | None = None

    def __post_init__(self):
        # 1. Type validation
        if not isinstance(self.context, RequestContext):
            raise ValueError(
                f"Expected RequestContext instance for context, got {type(self.context).__name__}"
            )
        if not isinstance(self.status, CaptureStatus):
            raise ValueError(
                f"Expected CaptureStatus instance for status, got {type(self.status).__name__}"
            )

        # 2. Status-specific contract validation
        if self.status == CaptureStatus.CAPTURED:
            if not isinstance(self.frame, ObservationFrame):
                raise ValueError(
                    f"frame must be an ObservationFrame when status is CAPTURED, "
                    f"got {type(self.frame).__name__}"
                )
            if self.frame.context != self.context:
                raise ValueError(
                    "frame.context does not match outcome context by value: "
                    f"{self.frame.context} != {self.context}"
                )
            if self.reason is not None:
                raise ValueError(
                    f"reason must be None when status is CAPTURED, got {self.reason!r}"
                )

        elif self.status == CaptureStatus.FAILED:
            if self.frame is not None:
                raise ValueError(
                    f"frame must be None when status is FAILED, got {self.frame}"
                )
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError(
                    f"reason must be a non-empty string when status is FAILED, got {self.reason!r}"
                )

        elif self.status == CaptureStatus.NOT_RECEIVED:
            if self.frame is not None:
                raise ValueError(
                    f"frame must be None when status is NOT_RECEIVED, got {self.frame}"
                )
            if self.reason is not None:
                raise ValueError(
                    f"reason must be None when status is NOT_RECEIVED, got {self.reason!r}"
                )