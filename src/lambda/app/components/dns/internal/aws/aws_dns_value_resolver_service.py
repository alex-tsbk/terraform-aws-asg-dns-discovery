from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from app.components.dns.internal.dns_value_resolver_base_service import DnsValueResolverService
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration
from app.infrastructure.aws.asg_service import AwsAutoScalingService
from app.infrastructure.aws.ec2_service import AwsEc2Service

if TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import Instance


class AwsDnsValueResolverService(DnsValueResolverService):
    """Service for resolving DNS values in AWS environment"""

    def __init__(
        self,
        aws_ec2_service: AwsEc2Service,
        aws_asg_service: AwsAutoScalingService,
        configuration_service: EnvironmentConfigurationService,
    ) -> None:
        self.aws_ec2_service = aws_ec2_service
        self.aws_asg_service = aws_asg_service
        self.configuration_service = configuration_service

    def handle_ip_source(
        self,
        dns_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        ip_type: Literal["public", "private"],
    ) -> list[str]:
        """Handle IP source.

        Args:
            ip_type (str): IP value to use - public or private.

        Returns:
            list[str]: The list of IPs, sorted by launch time in ascending order.
        """
        ec2_instances = self._get_ec2_instances(dns_config_item, lifecycle_event)
        ec2_instances = self._filter_by_readiness(ec2_instances)
        return [
            (ec2_instance.public_ip_address if ip_type == "public" else ec2_instance.private_ip_address)
            for ec2_instance in ec2_instances
        ]

    def handle_tag_source(
        self,
        dns_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        tag_name: str,
    ) -> list[str]:
        """Handle tag source.

        Args:
            tag_name (str): Name of the tag to resolve value from.

        Returns:
            list[str]: Values of the tag, sorted by EC2 launch time in ascending order.
        """
        ec2_instances = self._get_ec2_instances(dns_config_item, lifecycle_event)
        ec2_instances = self._filter_by_readiness(ec2_instances)
        ec2_instances_tags = [
            next(filter(lambda t: t["Key"] == tag_name, instance.tags), None) for instance in ec2_instances
        ]
        # Extract and return values from the tags
        return [tag["Value"] for tag in ec2_instances_tags if tag]

    def _filter_by_readiness(self, instances: list[Instance]) -> list[Instance]:
        """Filter out instances that don't have matching readiness tags.

        Args:
            instances (list[Instance]): The list of EC2 instances.

        Returns:
            list[Instance]: The list of EC2 instances that have matching readiness tags.
        """
        readiness_config = self.configuration_service.readiness_config
        if not readiness_config.enabled:
            return instances
        # Filter out instances that don't have matching readiness tags
        return [
            instance
            for instance in instances
            if instance.tags
            and any(
                tag["Key"] == readiness_config.tag_key and tag["Value"] == readiness_config.tag_value
                for tag in instance.tags
            )
        ]

    def _get_ec2_instances(
        self, dns_config_item: ScalingGroupConfiguration, lifecycle_event: LifecycleEventModel
    ) -> list[Instance]:
        """Resolve EC2 instances.

        Args:
            dns_config_item (ScalingGroupConfiguration): The Scaling Group DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.

        Returns:
            list[Instance]: The list of EC2 instances ids, sorted by launch time in ascending order.
        """

        if lifecycle_event.transition in [
            LifecycleTransition.LAUNCHING,
            LifecycleTransition.DRAINING,
        ]:
            instance = self.aws_ec2_service.get_instance(lifecycle_event.instance_id)
            return [instance]

        if lifecycle_event.transition == LifecycleTransition.RECONCILING:
            asg_name = dns_config_item.scaling_group_name
            instances = self.aws_asg_service.list_running_ec2_instances([asg_name])
            return instances[asg_name]

        raise ValueError(
            f"Unable to resolve EC2 instances: unsupported lifecycle transition: {lifecycle_event.transition}"
        )
