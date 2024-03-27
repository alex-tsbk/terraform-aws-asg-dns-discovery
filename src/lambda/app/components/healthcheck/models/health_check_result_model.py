from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class EndpointHealthCheckResultModel(DataclassBase):
    """Model representing the result of a health check for an endpoint.

    Remarks:
        Most of the properties are optional, these are used primarily for telemetry and observability purposes.
        When something is not healthy, it's important to know why. It's then up to consumer to decide what to do with this information.
        One way is to proceed only with healthy endpoints, ignoring unhealthy.
    """

    # Whether the endpoint is healthy
    healthy: bool
    # Endpoint that was checked
    endpoint: str = field(default="")
    # Instance id
    instance_id: str = field(default="")
    # Protocol used for the health check
    protocol: str = field(default="")
    # Status of the health check. Optional.
    status: str = field(default="")
    # Message from the health check. Optional.
    message: str = field(default="")
    # Time taken for instance to become ready. In seconds. Optional.
    time_taken_s: int = field(default=0)

    def __str__(self) -> str:
        return f"{self.protocol}:{self.endpoint}:{self.healthy} (instance_id:{self.instance_id};status:{self.status};msg:{self.message};time_s:{self.time_taken_s})"


@dataclass
class HealthCheckResultModel(DataclassBase):
    """Model representing the result of a health check"""

    endpoints: list[EndpointHealthCheckResultModel] = field(default_factory=list)

    @property
    def healthy(self):
        return bool(self)

    def __str__(self) -> str:
        return f"Healthy: {self.healthy}, Endpoints: {', '.join([str(endpoint) for endpoint in self.endpoints])}"

    def __bool__(self) -> bool:
        return len(self.endpoints) > 0 and all([endpoint.healthy for endpoint in self.endpoints])

    def __eq__(self, other: "HealthCheckResultModel") -> bool:
        if not isinstance(other, HealthCheckResultModel):
            return False
        return self.healthy == other.healthy

    @classmethod
    def UNHEALTHY(cls, endpoints: list[EndpointHealthCheckResultModel] = None):
        """Create an unhealthy health check result.

        Args:
            endpoints (list[EndpointHealthCheckResultModel]], optional): The endpoints tested and their health status. Defaults to None.
        """
        return cls(endpoints=endpoints or [])
