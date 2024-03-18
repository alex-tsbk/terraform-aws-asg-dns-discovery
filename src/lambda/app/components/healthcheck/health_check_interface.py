import abc

from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration

from .models.health_check_result_model import HealthCheckResultModel


class HealthCheckInterface(metaclass=abc.ABCMeta):
    """Interface for performing healthcheck on the specified destination."""

    @abc.abstractmethod
    def check(self, destination: str, sg_dns_config: ScalingGroupConfiguration) -> HealthCheckResultModel:
        """
        Perform a health check on a destination.

        Args:
            destination (str): The address of the resource to run health check against. Can be IP, DNS name, etc.
            sg_dns_config (ScalingGroupConfiguration): The Scaling Group DNS configuration item.


        Returns:
            HealthCheckResultModel: The model that represents the result of the health check.
        """
