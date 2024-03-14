from __future__ import annotations

from enum import Enum
from time import sleep
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import Instance

from app.aws.asg import AutoScalingService
from app.aws.dynamo import DynamoDBRepository
from app.aws.ec2 import Ec2Service
from app.aws.route53 import Route53Service
from app.models.configs.asg_dns_config import AsgDnsConfig, AsgDnsConfigItem
from app.models.configs.readiness_config import ReadinessConfig
from app.models.events.lifecycle_event_model import LifecycleEventModel
from app.observability import logging
from app.services.configuration_service import ConfigurationService
from app.services.dns_management_service import DnsManagementService
from app.services.healthcheck_service import Ec2HealthCheckService
from app.services.mutex_service import MutexService


class LifecycleAction(Enum):
    """Describes lifecycle actions for AutoScalingGroup instances"""

    CONTINUE = "CONTINUE"
    ABANDON = "ABANDON"


class LifecycleService:
    """Manages handling of Service Discovery related lifecycle actions for AutoScalingGroup instances"""

    def __init__(self) -> None:
        self.logger = logging.get_logger()
        self.configuration_service = ConfigurationService()
        self.autoscaling_service = AutoScalingService()
        self.ec2_service = Ec2Service()
        self.dns_management_service = DnsManagementService(Route53Service())
        self.ec2_health_check_service = Ec2HealthCheckService()
        self.dynamodb_repository = DynamoDBRepository(self.configuration_service.get_dynamo_config().table_name)
        self.mutex_service = MutexService(self.dynamodb_repository)

    def handle(self, event_object: dict) -> bool:
        """Handles lifecycle action event from AWS SNS

        Args:
            event (dict): Event object received from SNS that describes the ASG lifecycle action

            {
                "Origin": "AutoScalingGroup",
                "LifecycleHookName": "dev-asg-service-discovery-drain-lch",
                "Destination": "EC2",
                "AccountId": "123456789123",
                "RequestId": "a696378f-0ac5-68d3-d6a4-688f99ecd5b4",
                "LifecycleTransition": "autoscaling:EC2_INSTANCE_TERMINATING",
                "AutoScalingGroupName": "v2-adsbx-dev-vpc-a-vrs-global-asg",
                "Service": "AWS Auto Scaling",
                "Time": "2024-02-26T04:53:24.631Z",
                "EC2InstanceId": "i-03a2b505b266b2eaa",
                "NotificationMetadata": "",
                "LifecycleActionToken": "451ac51f-6fdc-486f-9027-745b0c254a31"
            }

        Returns:
            bool: True if lifecycle action is handled successfully, False otherwise
        """
        try:
            event: LifecycleEventModel = LifecycleEventModel.from_dict(event_object)
        except Exception as e:
            # Might be a malformed event/event for unrelated actions, log and return False
            self.logger.warning(f"Error parsing lifecycle event: {str(e)}")
            return False

        # Extract event details
        asg_name = event.AutoScalingGroupName
        origin = event.Origin
        destination = event.Destination
        ec2_instance_id = event.EC2InstanceId

        # Launching:
        #   origin: EC2, WarmPool
        #   destination: AutoScalingGroup
        is_launching = origin in ["EC2", "WarmPool"] and destination == "AutoScalingGroup"

        # Termination:
        #   origin: AutoScalingGroup
        #   destination: EC2, WarmPool
        is_draining = origin == "AutoScalingGroup" and destination in ["EC2", "WarmPool"]

        # Ensure we're handling the lifecycle action for the correct source, don't block the lifecycle action if it's not for us
        if event.Service != "AWS Auto Scaling":
            self.logger.warning(f"Unsupported service event: {event.Service}")
            return False

        # Ensure we're handling the lifecycle action for the correct origin and destination,
        # don't block the lifecycle action if it's not for us (AWS added new hooks in the future)
        if not is_launching and not is_draining:
            self.logger.warning(f"Unsupported origin: {origin} and destination: {destination} combination. Ignoring..")
            return False

        # Obtain information about the instance
        instance = self.ec2_service.get_instance(ec2_instance_id)
        if not instance:
            self.logger.error(f"Instance not found: {ec2_instance_id}")
            return False

        # Obtain ASG DNS configuration directly from message, as we need to know exactly which
        # configuration for ASG we're dealing with (as ASG can have multiple configurations)
        asg_dns_config: AsgDnsConfig = self.configuration_service.get_asg_dns_configs()
        asg_dns_config_items: list[AsgDnsConfigItem] = asg_dns_config.for_asg_name(asg_name)
        if not asg_dns_config_items:
            self.logger.warning(f"ASG DNS configuration not found for ASG: {asg_name}")
            # Don't prevent EC2 from launching/terminating if DNS configuration is not found,
            # after all - this may be fixed by manually updating DNS record, while forcing EC2 to re-spawn is not a good idea
            self._send_lifecycle_action(event, LifecycleAction.CONTINUE)
            return False

        # Handle lifecycle action
        if is_launching:
            self.logger.info(f"Handling registering EC2 instance: {ec2_instance_id}")
            result = self._handle_launching(asg_dns_config_items, instance)
            self._send_lifecycle_action(event, LifecycleAction.CONTINUE if result else LifecycleAction.ABANDON)
            return result

        if is_draining:
            self.logger.info(f"Handle draining EC2 instance: {event.EC2InstanceId}")
            result = self._handle_draining(asg_dns_config_items, instance)
            self._send_lifecycle_action(event, LifecycleAction.CONTINUE if result else LifecycleAction.ABANDON)
            return result

        return False

    def _handle_launching(self, asg_dns_config_items: list[AsgDnsConfigItem], instance: Instance) -> bool:
        """Handles instance launch lifecycle action

        Args:
            event (LifecycleEventModel): Event object received from SNS that describes the ASG lifecycle action
            asg_dns_config_items (list[AsgDnsConfigItem]): List of ASG DNS configuration items for the same ASG
            instance (Instance): EC2 instance

        Returns:
            bool: True if lifecycle action is handled successfully, False otherwise
        """
        ec2_instance_id = instance.id
        # Inside lifecycle hook all ASG DNS configurations are for the same ASG organically
        asg_name = asg_dns_config_items[0].asg_name
        readiness_config = self.configuration_service.get_readiness_config()
        # Check if readiness check is required, if so wait for the instance to be ready
        if readiness_config.enabled:
            self.logger.info(
                f"Readiness check enabled for ASG: {asg_name}. Waiting for for EC2 instance: {ec2_instance_id} to have readiness tag: {readiness_config.tag_key}={readiness_config.tag_value}.."
            )
            ec2_ready = self._wait_ec2_to_become_ready(readiness_config, instance)
            if not ec2_ready:
                self.logger.error(f"Instance readiness check failed: {ec2_instance_id}")
                return False
            # Log readiness check passed message
            self.logger.info(f"Instance readiness check passed: {ec2_instance_id}")

        # Loop through ASG DNS configurations and ensure instance is passing health checks
        for asg_dns_config in asg_dns_config_items:
            self.logger.debug(f"Handling registering EC2 instance: {asg_dns_config} -> {ec2_instance_id}")
            # Run health check against the instance to ensure it's healthy
            if asg_dns_config.health_check_enabled:
                self.logger.debug(f"Running health check for instance: {ec2_instance_id}")
                healthy = self.ec2_health_check_service.check(
                    ip=instance.private_ip_address, asg_dns_config=asg_dns_config
                )
                # We've waited deliberately and this failed, abandon the lifecycle action
                if not healthy:
                    self.logger.error(f"Instance health check failed: {ec2_instance_id}")
                    return False
                self.logger.info(f"Instance health check passed: {ec2_instance_id}")

            # Register instance in DNS
            ip_address = instance.private_ip_address
            if asg_dns_config.use_public_ip:
                ip_address = instance.public_ip_address
            self.logger.debug(f"Registering instance in DNS: {ec2_instance_id} using IP: {ip_address}..")

            # Obtain lock to prevent concurrent processing of lifecycle actions for the same resource
            lock_key = asg_dns_config.lock_key
            lock_obtained = self._acquire_lock(lock_key)
            # We failed to obtain the lock, abandon the lifecycle action if we can't obtain the lock
            if not lock_obtained:
                self.logger.error(
                    f"Failed to obtain lock: {lock_key}. Abandoning lifecycle action for instance: {ec2_instance_id}."
                )
                return False

            # Modify DNS record
            try:
                status = self.dns_management_service.add_ip_to_record(
                    asg_dns_config.hosted_zone_id,
                    asg_dns_config.record_name,
                    asg_dns_config.record_type,
                    asg_dns_config.record_ttl,
                    asg_dns_config.dns_mock_ip,
                    ip_address,
                )
                self.logger.debug(f"Instance registered in DNS: {ec2_instance_id} with status: {status}")
            except Exception as e:
                self.logger.error(f"Error registering instance in DNS: {ec2_instance_id} with error: {str(e)}")
                return False
            finally:
                # Always release the lock
                self._release_lock(lock_key)

        return True

    def _handle_draining(self, asg_dns_config_items: list[AsgDnsConfigItem], instance: Instance) -> bool:
        """Handles instance draining lifecycle action

        Args:
            event (LifecycleEventModel): Event object received from SNS that describes the ASG lifecycle action
            asg_dns_config_items (list[AsgDnsConfigItem]): List of ASG DNS configuration items for the same ASG
            instance (Instance): EC2 instance

        Returns:
            bool: True if lifecycle action is handled successfully, False otherwise
        """
        # Loop through ASG DNS configurations and ensure instance is passing health checks
        for asg_dns_config in asg_dns_config_items:
            ec2_instance_id = instance.id
            ip_address = instance.private_ip_address
            if asg_dns_config.use_public_ip:
                ip_address = instance.public_ip_address

            # Obtain lock to prevent concurrent processing of lifecycle actions for the same resource
            lock_key = asg_dns_config.lock_key
            lock_obtained = self._acquire_lock(lock_key)

            # We failed to obtain the lock, abandon the lifecycle action if we can't obtain the lock
            if not lock_obtained:
                self.logger.error(
                    f"Failed to obtain lock: {lock_key}. Abandoning lifecycle action for instance: {ec2_instance_id}."
                )
                return False

            # Modify DNS record
            try:
                self.dns_management_service.remove_ip_from_record(
                    asg_dns_config.hosted_zone_id,
                    asg_dns_config.record_name,
                    asg_dns_config.record_type,
                    asg_dns_config.managed_dns_record,
                    asg_dns_config.dns_mock_ip,
                    ip_address,
                )
                self.logger.debug(f"Instance removed from DNS: {ec2_instance_id}")
            except Exception as e:
                self.logger.error(f"Error removing instance from DNS: {ec2_instance_id} with error: {str(e)}")
                return False
            finally:
                # Always release the lock
                self._release_lock(lock_key)

        return True

    def _send_lifecycle_action(self, event: LifecycleEventModel, result: LifecycleAction) -> None:
        """Sends lifecycle action to ASG with result provided

        Args:
            event (dict): Original event object received from SNS
            result (Literal[&quot;CONTINUE&quot;, &quot;ABANDON&quot;]): Result of lifecycle action: CONTINUE or ABANDON

        Raises:
            ValueError: When result is not CONTINUE or ABANDON
        """
        if result not in [LifecycleAction.ABANDON, LifecycleAction.CONTINUE]:
            raise ValueError(f"Invalid result: {result}")

        ec2_instance_id = event.EC2InstanceId
        try:
            self.autoscaling_service.complete_lifecycle_action(
                lifecycle_hook_name=event.LifecycleHookName,
                autoscaling_group_name=event.AutoScalingGroupName,
                lifecycle_action_token=event.LifecycleActionToken,
                lifecycle_action_result=result.value,
                ec2_instance_id=ec2_instance_id,
            )
            self.logger.debug(f"Lifecycle action completed for instance: {ec2_instance_id}")
        except ClientError as e:
            self.logger.error(f"Error completing lifecycle action for instance: {ec2_instance_id} with error: {str(e)}")
            raise e
        else:
            self.logger.info(f"Lifecycle action completed for instance: {ec2_instance_id}")

    def _wait_ec2_to_become_ready(self, readiness_config: ReadinessConfig, instance: Instance) -> bool:
        """Wait for EC2 instance to become ready for service discovery

        Args:
            readiness_config (ReadinessConfig): Readiness configuration
            instance (Instance): EC2 instance

        Returns:
            bool: True if instance is ready, False otherwise
        """
        ec2_instance_id = instance.id
        tag_key = readiness_config.tag_key
        tag_value = readiness_config.tag_value
        tag_present = None
        sleeping_for = 0
        # Wait for the instance to be ready
        while not tag_present and sleeping_for <= readiness_config.timeout:
            tag_present = next(
                filter(lambda t: t["Key"] == tag_key and t["Value"] == tag_value, instance.tags),
                None,
            )
            if tag_present:
                break
            self.logger.debug(
                f"Waiting for readiness tag: {tag_key}={tag_value} on instance: {ec2_instance_id}.. [{sleeping_for}s/{readiness_config.timeout}s]"
            )
            sleep(readiness_config.interval)
            sleeping_for += readiness_config.interval
            instance.reload()  # refresh instance tags

        # If readiness tag is not present, abandon the lifecycle action - we've waited deliberately and this failed
        if not tag_present:
            self.logger.error(f"Instance readiness check failed: {ec2_instance_id}")
            return False
        return True

    def _acquire_lock(self, lock_key: str) -> bool:
        """Acquires lock for the resource

        Args:
            lock_key (str): Lock key

        Returns:
            bool: True if lock is acquired, False otherwise
        """
        lock_obtained = False
        lock_request_count = 1
        while not lock_obtained or lock_request_count < 10:
            lock_obtained = self.mutex_service.acquire_lock(lock_key)
            if lock_obtained:
                break
            self.logger.debug(f"Waiting for lock to be obtained: {lock_key}..")
            sleep(lock_request_count)  # Incremental backoff
            lock_request_count += 1
        return lock_obtained

    def _release_lock(self, lock_key: str) -> None:
        """Releases lock for the resource

        Args:
            lock_key (str): Lock key
        """
        self.mutex_service.release_lock(lock_key)
        self.logger.debug(f"Lock released: {lock_key}")
        return
