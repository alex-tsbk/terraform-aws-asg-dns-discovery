import base64
import json
import os
from typing import Callable

from app.aws.dynamo import DynamoDBRepository
from app.config.models.dynamo_config import DynamoConfig
from app.config.models.metrics_config import MetricsConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.reconciliation_config import ReconciliationConfig
from app.config.models.scaling_group_dns_config import ScalingGroupDnsConfig, ScalingGroupDnsConfigItem
from app.utils.dataclass import DataclassBase
from app.utils.singleton import Singleton


class ConfigurationService(metaclass=Singleton):
    """Singleton service class for resolving ASG DNS configuration"""

    _cache = {}

    def __init__(self) -> None:
        # Cache placeholders
        self._cache = {}
        # This is not DI, because concern of resolving configuration is not a concern of the caller,
        # since configuration dynamo db table name is resolved by the same class
        self.dynamodb_repository = DynamoDBRepository(self.get_dynamo_config().table_name)

    def get_asg_dns_configs(self) -> ScalingGroupDnsConfig:
        """Resolves ASG DNS configurations for all ASGs from DynamoDB

        Args:
            asg_name (str): AutoScalingGroup name

        Returns:
            dict: ASG DNS configuration
        """
        if self.cached_asg_config is not None:
            return self.cached_asg_config

        dynamodb_config: DynamoConfig = self.get_dynamo_config()
        config_table_name: str = dynamodb_config.table_name
        config_item_key_id: str = dynamodb_config.config_item_key_id
        # Retrieve configuration from DynamoDB
        config_definition: dict = self.dynamodb_repository.get_item(self.get_dynamo_config().config_item_key_id)
        if not config_definition:
            raise ValueError(
                f"DNS configuration not found in DynamoDB table: {config_table_name} -> {config_item_key_id}"
            )

        config_item_base64: str = config_definition.get("config", None)
        if not config_item_base64:
            raise ValueError(
                f"DNS configuration not found in DynamoDB table: {config_table_name} -> {config_item_key_id}"
            )

        # Decode base64
        config_items: list[dict] = json.loads(base64.b64decode(config_item_base64).decode("utf-8"))
        if not config_items:
            raise ValueError(
                f"Unable to find ASG DNS configuration not found in DynamoDB table: {config_table_name} -> {config_item_key_id}"
            )

        dns_config_items: list[ScalingGroupDnsConfigItem] = []
        for item in config_items:
            # Create AsgDnsConfigItem object
            dns_config_items.append(ScalingGroupDnsConfigItem.from_dict(item))

        # Set instance variable
        self.cached_asg_config = ScalingGroupDnsConfig(items=dns_config_items)
        return self.cached_asg_config

    @property
    def is_development(self) -> bool:
        """Returns True if the environment is development"""
        return os.environ.get("DNS_DISCOVERY_ENVIRONMENT", "development").lower() == "development"

    @property
    def readiness_config(self) -> ReadinessConfig:
        """Returns readiness settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> ReadinessConfig:
            enabled = os.environ.get("ec2_readiness_enabled", "true").lower() == "true"
            interval = int(os.environ.get("ec2_readiness_interval_seconds", 5))
            timeout = int(os.environ.get("ec2_readiness_timeout_seconds", 300))
            tag_key = os.environ.get(
                "ec2_readiness_tag_key",
                "app:code-deploy:status",
            )
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
    def dynamo_config(self) -> DynamoConfig:
        """Returns DynamoDB settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> DynamoConfig:
            table_name = os.environ.get("dynamo_db_table_name", "")
            config_item_key_id = os.environ.get("dynamo_db_config_item_key_id", "")
            return DynamoConfig(
                table_name=table_name,
                config_item_key_id=config_item_key_id,
            )

        return self._cached("dynamo_config", resolver)

    @property
    def reconciliation_config(self) -> ReconciliationConfig:
        """Returns reconciliation settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> ReconciliationConfig:
            whatif = os.environ.get("reconciliation_whatif", "false").lower() == "true"
            max_concurrency = int(os.environ.get("reconciliation_max_concurrency", 1))
            return ReconciliationConfig(whatif, max_concurrency)

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
    def _cached(
        self,
        key: str,
        resolver: Callable[[], DataclassBase],
    ) -> DataclassBase:
        """Returns a cached value or resolves it using the provided resolver function

        Args:
            key (str): Cache key
            resolver (Callable[[], any]): Resolver function

        Returns:
            any: Cached value
        """
        if key not in self._cache:
            self._cache[key] = resolver()
        return self._cache[key]
