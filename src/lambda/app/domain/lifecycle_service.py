from __future__ import annotations

from time import sleep

from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.models.dns_change_request_model import DnsChangeRequestModel
from app.components.dns.models.dns_change_response_model import DnsChangeResponseModel
from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.lifecycle.instance_lifecycle_interface import InstanceLifecycleInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleAction, LifecycleEventModel
from app.components.lifecycle.models.lifecycle_event_model_factory import LifecycleEventModelFactory
from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration, ScalingGroupConfigurations
from app.config.runtime_configuration_service import RuntimeConfigurationService
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class LifecycleService:
    """Service responsible for handling lifecycle event"""

    def __init__(
        self,
        env_configuration_service: EnvironmentConfigurationService,
        runtime_configuration_service: RuntimeConfigurationService,
        lifecycle_event_model_factory: LifecycleEventModelFactory,
        lifecycle_service: InstanceLifecycleInterface,
        health_check_service: HealthCheckInterface,
        readiness_service: InstanceReadinessInterface,
        distributed_lock_service: DistributedLockInterface,
        dns_management_service: DnsManagementInterface,
    ) -> None:
        self.logger = get_logger()
        self.env_configuration_service = env_configuration_service
        self.runtime_configuration_service = runtime_configuration_service
        self.lifecycle_event_model_factory = lifecycle_event_model_factory
        self.lifecycle_service = lifecycle_service
        self.health_check_service = health_check_service
        self.readiness_service = readiness_service
        self.distributed_lock_service = distributed_lock_service
        self.dns_management_service = dns_management_service

    def handle(self, event: LifecycleEventModel) -> bool:
        """Handles lifecycle action event."""

        # Load all Scaling Group DNS configurations
        all_scaling_groups_configs = self.runtime_configuration_service.get_scaling_groups_dns_configs()
        if not all_scaling_groups_configs:
            self.logger.error("Unable to load Scaling Group DNS configurations.")
            return False

        # Resolve Scaling Group DNS configurations for Scaling Group name from event
        scaling_group_configs = all_scaling_groups_configs.for_scaling_group(event.scaling_group_name)
        if not scaling_group_configs:
            self.logger.warning(f"Scaling Group DNS configurations not found for ASG: {event.scaling_group_name}")
            return False

        # Keep track of readiness checks that have been passed
        readiness_checks_passed: set[str] = {}

        # For each scaling group dns configuration, gather information and perform appropriate actions
        for scaling_group_config in scaling_group_configs:

            # First, ensure instance is considered ready
            ready = self._perform_readiness_check(event, scaling_group_config, readiness_checks_passed)

            if not ready:
                completion_status = self.lifecycle_service.complete_lifecycle_action(event, LifecycleAction.ABANDON)

            # Check if health check is enabled
            health_check_enabled = (
                scaling_group_config.health_check_config and scaling_group_config.health_check_config.enabled
            )
            if health_check_enabled:
                # Perform health check
                health_check_result = self.health_check_service.check(event.instance_id, scaling_group_config)
                if not health_check_result:
                    completion_status = self.lifecycle_service.complete_lifecycle_action(event, LifecycleAction.ABANDON)
                    self.logger.info(f"Lifecycle completed successfully: {completion_status}")
                    return False

        return False

    def _perform_readiness_check(
        self,
        event: LifecycleEventModel,
        scaling_group_config: ScalingGroupConfiguration,
        readiness_checks_passed: set[str],
    ) -> bool:
        """Handles instance readiness lifecycle action

        Args:
            event (LifecycleEventModel): Event object received from SNS that describes the ASG lifecycle action
            scaling_group_config (ScalingGroupConfiguration): Scaling Group DNS configuration
            readiness_checks_passed (set[str]): Set of readiness checks that have been passed

        Returns:
            bool: True if readiness check is successful, False otherwise
        """
        readiness_config = scaling_group_config.readiness_config
        if not readiness_config:
            readiness_config = self.env_configuration_service.readiness_config
        # Check if readiness check is enabled and has not been passed
        if readiness_config and readiness_config.enabled:
            self.logger.debug(f"Readiness check enabled for SG: {event.scaling_group_name}")
            # If readiness check is already passed, skip
            if readiness_config.id in readiness_checks_passed:
                self.logger.debug(f"Readiness check previously passed for SG: {event.scaling_group_name}.")
                return True
            # Perform readiness check
            self.logger.debug(f"Using readiness check configuration: {readiness_config.to_dict()}")
            instance_ready = self._wait_for_instance_to_become_ready(event, scaling_group_config, readiness_config)
            if not instance_ready:
                self.logger.warning(f"Instance readiness check failed: {event.instance_id}.")
                return False
            # Remember that configuration has passed readiness check
            readiness_checks_passed.add(readiness_config.id)
        else:
            self.logger.debug(f"Readiness check disabled for Scaling Group: {event.scaling_group_name}")
        return True

    def _wait_for_instance_to_become_ready(self, event: LifecycleEventModel, readiness_config: ReadinessConfig) -> None:
        self.logger.info(
            f"Waiting for for instance: {event.instance_id} to have readiness tag: {readiness_config.tag_key}={readiness_config.tag_value}.."
        )
        # TODO: Schedule readiness check on a separate thread in background, to handle multiple instances at once
        ec2_ready = self.readiness_service.is_ready(event.instance_id, readiness_config, wait=True)
        if not ec2_ready:
            self.logger.error(f"Instance readiness check failed: {event.instance_id}")
            return False
        # Log readiness check passed message
        self.logger.info(f"Instance readiness check passed: {event.instance_id}")
        return True
