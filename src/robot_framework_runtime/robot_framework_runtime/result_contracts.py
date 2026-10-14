from dataclasses import dataclass
from enum import Enum
from robot_framework_runtime.contracts import RequestContext


class ResultStatus(Enum):
    """Standardized execution statuses for runtime tasks."""
    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    FAULT = "fault"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class TaskResult:
    """Immutable record capturing generic task execution state and diagnostic reasons."""
    context: RequestContext
    status: ResultStatus
    source: str
    reason: str | None = None

    def __post_init__(self):
        # 1. Base type validations
        if not isinstance(self.context, RequestContext):
            raise ValueError(
                f"Expected RequestContext instance for context, got {type(self.context).__name__}"
            )
        if not isinstance(self.status, ResultStatus):
            raise ValueError(
                f"Expected ResultStatus instance for status, got {type(self.status).__name__}"
            )
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError(f"source must be a non-empty string, got {self.source!r}")

        # 2. Reason consistency validation based on state category
        if self.status in (ResultStatus.ACCEPTED, ResultStatus.RUNNING, ResultStatus.SUCCEEDED):
            if self.reason is not None:
                raise ValueError(
                    f"reason must be None when status is {self.status.name}, got {self.reason!r}"
                )
        else:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError(
                    f"reason must be a non-empty string when status is {self.status.name}, "
                    f"got {self.reason!r}"
                )