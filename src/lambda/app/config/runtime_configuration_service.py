import base64
import json

from app.components.persistence.repository_service_interface import RepositoryInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration, ScalingGroupConfigurations
from app.utils.exceptions import BusinessException


class RuntimeConfigurationService:
    """Singleton service class for resolving ASG DNS configuration"""

    def __init__(self, repository: RepositoryInterface, environment_config: EnvironmentConfigurationService):
        # Cache placeholder
        self._cache = {}
        self.repository = repository
        self.environment_config = environment_config

    def get_asg_dns_configs(self) -> ScalingGroupConfigurations:
        """Resolves ASG DNS configurations for all ASGs from DynamoDB

        Args:
            asg_name (str): AutoScalingGroup name

        Returns:
            dict: ASG DNS configuration
        """
        if cached_item := self._cache.get("cached_asg_config", None):
            return cached_item

        config_item_key_id: str = self.environment_config.db_config.config_item_key_id
        # Retrieve configuration from DynamoDB
        config_definition: dict = self.repository.get(config_item_key_id)
        if not config_definition:
            raise BusinessException(
                f"DNS configuration not found in repository using key provided: '{config_item_key_id}'"
            )

        config_item_base64: str = config_definition.get("config", None)
        if not config_item_base64:
            raise BusinessException(
                f"Unable to find 'config' property of DNS configuration object using key provided '{config_item_key_id}'"
            )

        # Decode base64
        config_items: list[dict] = json.loads(base64.b64decode(config_item_base64).decode("utf-8"))
        if not config_items:
            raise BusinessException("Unable to resolve Scaling Groups DNS configuration")

        # Convert to ScalingGroupConfiguration objects
        sg_config_items: list[ScalingGroupConfiguration] = [
            ScalingGroupConfiguration.from_dict(item) for item in config_items
        ]

        # Set instance variable
        self._cache["cached_asg_config"] = ScalingGroupConfigurations(items=sg_config_items)
        return self._cache["cached_asg_config"]
