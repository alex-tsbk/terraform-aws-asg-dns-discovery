from app.components.metrics.metrics_interface import MetricsInterface
from app.utils.singleton import Singleton


class MetricsService(MetricsInterface, metaclass=Singleton):
    """Singleton proxy class encapsulating the metrics service implementation"""

    def __init__(self, underlying_service: MetricsInterface):
        """Initializes the metrics service proxy with a concrete implementation

        Args:
            underlying_service (MetricsInterface): concrete implementation of metrics service
        """
        self.underlying_service = underlying_service

    def reset(self):
        """Resets the metrics service to a clean state"""
        return self.underlying_service.reset()

    def record_data_point(
        self,
        metric_name: str,
        metric_value: int,
        description: str = None,
        metric_unit: str = "Count",
    ):
        """Record a metric data point for later publishing

        Args:
            metric_name (str): name of metric
            metric_value (int): value of metric
            description (str, optional): description of metric. Defaults to None.
            metric_unit (str, optional): unit of metric. Defaults to "Count".
        """
        return self.underlying_service.record_data_point(metric_name, metric_value, description, metric_unit)

    def record_dimension(self, metric_name: str, metric_value: str, description: str = None):
        """Record a metric dimension for later use in metric publishing

        Args:
            metric_name (str): name of metric dimension
            metric_value (str): value of metric dimension
            description (str, optional): description of metric. Defaults to None.
        """
        return self.underlying_service.record_dimension(metric_name, metric_value, description)

    def publish_metrics(self) -> bool:
        """Publish all recorded metrics to the metrics service

        Returns:
            bool: True if metrics were successfully published, False otherwise
        """
        return self.underlying_service.publish_metrics()
