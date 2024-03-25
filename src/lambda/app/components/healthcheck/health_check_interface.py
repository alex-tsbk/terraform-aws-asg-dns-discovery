import abc

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration

from .models.health_check_result_model import HealthCheckResultModel


class HealthCheckInterface(metaclass=abc.ABCMeta):
    """Interface for performing healthcheck on the specified destination."""

    @abc.abstractmethod
    def check(
        self,
        sg_dns_config: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
    ) -> HealthCheckResultModel:
        """
        Perform a health check on a destination.

        Args:
            sg_dns_config (ScalingGroupConfiguration): The Scaling Group DNS configuration item.
            lifecycle_event (str): The lifecycle event for which to perform the health check.

        Returns:
            HealthCheckResultModel: The model that represents the result of the health check.
        """
