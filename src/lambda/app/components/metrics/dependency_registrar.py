from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RuntimeContext
from app.utils.di import DIContainer

from .internal.development_metrics_service import DevelopmentMetricsService
from .metrics_interface import MetricsInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    if RuntimeContext.is_localhost_development:
        di_container.register(MetricsInterface, DevelopmentMetricsService, lifetime="scoped")

    metrics_provider = env_config_service.metrics_config.metrics_provider
    if RuntimeContext.is_aws and metrics_provider == "cloudwatch":
        from app.components.metrics.aws.aws_cloudwatch_metrics_service import AwsCloudwatchMetricsService

        di_container.register(MetricsInterface, AwsCloudwatchMetricsService, lifetime="scoped")
