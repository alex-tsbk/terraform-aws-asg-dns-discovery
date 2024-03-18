from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class HealthCheckResultModel(DataclassBase):
    """Model representing the result of a health check"""

    # The health check result. Example: True, False.
    healthy: bool
    # The status of the health check. Example: UP, DOWN, ..
    status: str = field(default="")
    # The message of the health check.
    message: str = field(default="")

    def __str__(self) -> str:
        return f"{self.status}/{self.message}"

    def __bool__(self) -> bool:
        return self.healthy

    def __eq__(self, other: "HealthCheckResultModel") -> bool:
        if not isinstance(other, HealthCheckResultModel):
            return False
        return self.healthy == other.healthy

    @classmethod
    def UNHEALTHY(cls):
        return cls(healthy=False)
