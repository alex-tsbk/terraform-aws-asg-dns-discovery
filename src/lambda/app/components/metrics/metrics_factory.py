from app.components.metrics.internal.development_metrics_service import DevelopmentMetricsService
from app.components.metrics.metrics_interface import MetricsInterface
from app.config.configuration_service import ConfigurationService
from app.config.runtime_context import RuntimeContext


class MetricsServiceFactory:
    """Factory for creating metrics service implementation based on config"""

    def __init__(self, configuration_service: ConfigurationService) -> None:
        self.config_service = configuration_service

    def create(self) -> MetricsInterface:
        """Creates a concrete implementation of metrics service based on config

        Returns:
            MetricsInterface: Concrete implementation of metrics service
        """

        is_development = self.config_service.is_development
        if is_development:
            return DevelopmentMetricsService()

        metrics_provider = self.config_service.metrics_config.metrics_provider
        if RuntimeContext.is_aws and metrics_provider == "cloudwatch":
            from app.components.metrics.aws.aws_cloudwatch_metrics_service import AwsCloudwatchMetricsService

            return AwsCloudwatchMetricsService(self.config_service)

        raise NotImplementedError(f"Metrics provider '{metrics_provider}' not implemented")
