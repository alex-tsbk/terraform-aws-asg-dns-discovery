import base64
import json
import os
from typing import Callable

from app.config.env_configuration_service import EnvironmentConfigurationService

# from app.aws.dynamo import DynamoDBRepository
from app.config.models.db_config import DbConfig
from app.config.models.metrics_config import MetricsConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.reconciliation_config import ReconciliationConfig
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration, ScalingGroupConfigurations
from app.utils.dataclass import DataclassBase
from app.utils.singleton import Singleton


class RuntimeConfigurationService:
    """Singleton service class for resolving ASG DNS configuration"""

    _cache = {}

    def __init__(self, env_configuration_service: EnvironmentConfigurationService) -> None:
        # Cache placeholders
        self._cache = {}
        self.env_configuration_service = env_configuration_service
        # This is not DI, because concern of resolving configuration is not a concern of the caller,
        # since configuration dynamo db table name is resolved by the same class
        self.dynamodb_repository = DynamoDBRepository(self.get_dynamo_config().table_name)

    def get_asg_dns_configs(self) -> ScalingGroupConfigurations:
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

        sg_config_items: list[ScalingGroupConfiguration] = []
        for item in config_items:
            # Create AsgDnsConfigItem object
            sg_config_items.append(ScalingGroupConfiguration.from_dict(item))

        # Set instance variable
        self.cached_asg_config = ScalingGroupConfigurations(items=sg_config_items)
        return self.cached_asg_config

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
