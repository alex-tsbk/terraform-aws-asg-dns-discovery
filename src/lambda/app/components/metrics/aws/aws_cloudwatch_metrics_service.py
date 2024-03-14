from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch import CloudWatchClient

from app.components.metrics.metrics_interface import MetricsInterface
from app.config.configuration_service import ConfigurationService
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class AwsCloudwatchMetricsService(MetricsInterface):
    """Concrete implementation of metrics service using AWS Cloudwatch as backend"""

    # Store CloudWatch client as class variable
    cloudwatch_client: ClassVar[CloudWatchClient] = boto3.client("cloudwatch")

    def __init__(self, configuration_service: ConfigurationService):
        self.logger = get_logger()
        # Specify processing date time
        self.processing_date_time = datetime.utcnow()
        self.cloudwatch_metrics_namespace = configuration_service.metrics_config.metrics_namespace
        # Metric data - records individual metrics for later publishing
        self.metric_data_points = []
        # Metric dimensions - shared across all metrics pushed
        self.metric_dimensions = []

    def reset(self):
        """Resets the metrics service to a clean state"""
        self.metric_data_points = []
        self.metric_dimensions = []
        self.processing_date_time = datetime.utcnow()
        return

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
            metric_unit (str, optional): unit of metric. Defaults to "Count".
        """
        existing_metric = next((x for x in self.metric_data_points if x["MetricName"] == metric_name), None)
        if existing_metric:
            existing_metric["Value"] += metric_value
        else:
            self.metric_data_points.append(
                {
                    "MetricName": metric_name,
                    "Timestamp": self.processing_date_time,
                    "Unit": metric_unit,
                    "Value": metric_value,
                }
            )
        if description:
            self.logger.debug(f"{description}: {metric_value}")

    def record_dimension(self, metric_name: str, metric_value: str, description: str = None):
        """Record a metric dimension for later use in metric publishing

        Args:
            metric_name (str): name of metric dimension
            metric_value (str): value of metric dimension
        """
        # Only add dimension if it doesn't exist
        if not next((x for x in self.metric_dimensions if x["Name"] == metric_name), None):
            self.metric_dimensions.append({"Name": metric_name, "Value": str(metric_value)})
        if description:
            self.logger.info(f"{description}: {metric_value}")

    def publish_metrics(self) -> bool:
        """Publish all recorded metrics to the metrics service

        Returns:
            bool: True if metrics were successfully published, False otherwise
        """

        # Merge shared dimensions into metric data points
        for metric in self.metric_data_points:
            metric["Dimensions"] = self.metric_dimensions

        try:
            # Put metric data
            response = self.cloudwatch_client.put_metric_data(
                Namespace=self.cloudwatch_metrics_namespace, MetricData=self.metric_data_points
            )
            self.logger.debug(f"Pushing metrics to cloudwatch: {self.metric_data_points}")
            self.logger.info(
                f"Metric pushed successfully: {self.cloudwatch_metrics_namespace} / {len(self.metric_data_points)} data points."
            )
        except ClientError as e:
            message = f"Error pushing metrics to cloudwatch: {str(e)}"
            self.logger.error()
            self.logger.error(to_json(self.metric_data_points))
            raise CloudProviderException(message, e)
