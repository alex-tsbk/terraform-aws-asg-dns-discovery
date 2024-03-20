import os
from typing import Callable

# from app.aws.dynamo import DynamoDBRepository
from app.config.models.db_config import DbConfig
from app.config.models.metrics_config import MetricsConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.reconciliation_config import ReconciliationConfig
from app.utils.dataclass import DataclassBase


class EnvironmentConfigurationService:
    """Service class for resolving ASG DNS configuration"""

    def __init__(self):
        # Cache placeholders
        self._cache = {}

    @property
    def readiness_config(self) -> ReadinessConfig:
        """Returns readiness settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> ReadinessConfig:
            enabled = os.environ.get("ec2_readiness_enabled", "true").lower() == "true"
            interval = int(os.environ.get("ec2_readiness_interval_seconds", 5))
            timeout = int(os.environ.get("ec2_readiness_timeout_seconds", 300))
            tag_key = os.environ.get("ec2_readiness_tag_key", "app:code-deploy:status")
            tag_value = os.environ.get("ec2_readiness_tag_value", "success")
            return ReadinessConfig(
                enabled=enabled,
                interval=interval,
                timeout=timeout,
                tag_key=tag_key,
                tag_value=tag_value,
            )

        return self._cached("readiness_config", resolver)

    @property
    def db_config(self) -> DbConfig:
        """Returns DynamoDB settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> DbConfig:
            provider = os.environ.get("db_provider", "dynamodb")
            table_name = os.environ.get("db_table_name", "")
            config_item_key_id = os.environ.get("db_config_item_key_id", "")
            return DbConfig(
                provider=provider,
                table_name=table_name,
                config_item_key_id=config_item_key_id,
            )

        return self._cached("dynamo_config", resolver)

    @property
    def reconciliation_config(self) -> ReconciliationConfig:
        """Returns reconciliation settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> ReconciliationConfig:
            what_if = os.environ.get("reconciliation_what_if", "false").lower() == "true"
            max_concurrency = int(os.environ.get("reconciliation_max_concurrency", 1))
            return ReconciliationConfig(what_if, max_concurrency)

        return self._cached("reconciliation_config", resolver)

    @property
    def metrics_config(self) -> MetricsConfig:
        """Returns metrics settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> MetricsConfig:
            metrics_enabled = str(os.environ.get("monitoring_metrics_enabled", False)).lower() == "true"
            metrics_provider = os.environ.get("monitoring_metrics_provider", "cloudwatch")
            metrics_namespace = os.environ.get("monitoring_metrics_namespace", "")
            alarms_enabled = str(os.environ.get("monitoring_alarms_enabled", "false")).lower() == "true"
            alarms_notification_destination = os.environ.get(
                "monitoring_alarms_notification_destination",
                "",
            )
            return MetricsConfig(
                metrics_enabled=metrics_enabled,
                metrics_provider=metrics_provider,
                metrics_namespace=metrics_namespace,
                alarms_enabled=alarms_enabled,
                alarms_notification_destination=alarms_notification_destination,
            )

        return self._cached("metrics_config", resolver)

    @classmethod
    def _cached(cls, key: str, resolver: Callable[[], DataclassBase]) -> DataclassBase:
        """Returns a cached value or resolves it using the provided resolver function

        Args:
            key (str): Cache key
            resolver (Callable[[], any]): Resolver function

        Returns:
            any: Cached value
        """
        if key not in cls._cache:
            cls._cache[key] = resolver()
        return cls._cache[key]
