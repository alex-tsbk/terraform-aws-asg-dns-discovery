from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition
from app.components.metadata.internal.instance_metadata_base_service import InstanceMetadataBaseService
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration
from app.infrastructure.aws.ec2_asg_service import AwsEc2AutoScalingService
from app.infrastructure.aws.ec2_service import AwsEc2Service

if TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import Instance


class AwsEc2MetadataService(InstanceMetadataBaseService):
    """Service for resolving EC2 metadata values"""

    def __init__(
        self,
        aws_ec2_service: AwsEc2Service,
        aws_asg_service: AwsEc2AutoScalingService,
        configuration_service: EnvironmentConfigurationService,
    ) -> None:
        self.aws_ec2_service = aws_ec2_service
        self.aws_asg_service = aws_asg_service
        self.configuration_service = configuration_service

    def handle_ip_source(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        ip_type: Literal["public", "private"],
    ) -> list[MetadataResultModel]:
        """Handle IP source.

        Args:
            sg_config_item (ScalingGroupConfiguration): Scaling Group DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.
            ip_type (str): IP value to use - public or private.

        Returns:
            list[MetadataResultModel]: The list containing information about values resolved.
        """
        ec2_instances: list[Instance] = self._get_ec2_instances(sg_config_item, lifecycle_event)
        results: list[MetadataResultModel] = []
        for ec2_instance in ec2_instances:
            ec2_instance.load()
            value = ec2_instance.public_ip_address if ip_type == "public" else ec2_instance.private_ip_address
            results.append(
                MetadataResultModel(
                    instance_id=ec2_instance.id,
                    instance_launch_timestamp=int(ec2_instance.launch_time.timestamp()),
                    value=value,
                    source=f"ip:{ip_type}",
                )
            )

        return results

    def handle_tag_source(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        tag_name: str,
    ) -> list[MetadataResultModel]:
        """Handle tag source.

        Args:
            sg_config_item (ScalingGroupConfiguration): Scaling Group DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.
            tag_name (str): The name of the tag to extract the value from.

        Returns:
            list[MetadataResultModel]: The list containing information about values resolved.
        """
        ec2_instances: list[Instance] = self._get_ec2_instances(sg_config_item, lifecycle_event)
        results: list[MetadataResultModel] = []
        for ec2_instance in ec2_instances:
            ec2_instance.load()
            value = next(filter(lambda t: t["Key"] == tag_name, ec2_instance.tags), {"Value": None})["Value"]
            results.append(
                MetadataResultModel(
                    instance_id=ec2_instance.id,
                    instance_launch_timestamp=int(ec2_instance.launch_time.timestamp()),
                    value=value,
                    source=f"tag:{tag_name}",
                )
            )

        return results

    def _get_ec2_instances(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
    ) -> list[Instance]:
        """Resolve EC2 instances.

        Args:
            sg_config_item (ScalingGroupConfiguration): The Scaling Group DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.

        Returns:
            list[Instance]: The list of EC2 instances ids, sorted by launch time in ascending order.
        """

        supported_transitions = [
            LifecycleTransition.LAUNCHING,
            LifecycleTransition.DRAINING,
            LifecycleTransition.RECONCILING,
        ]

        # Don't resolve instances for unsupported transitions
        if lifecycle_event.transition not in supported_transitions:
            return []

        if lifecycle_event.transition in [
            LifecycleTransition.LAUNCHING,
            LifecycleTransition.DRAINING,
        ]:
            instance = self.aws_ec2_service.get_instance(lifecycle_event.instance_id)
            return [instance]

        if lifecycle_event.transition == LifecycleTransition.RECONCILING:
            asg_name = sg_config_item.scaling_group_name
            valid_states = sg_config_item.scaling_group_valid_states
            instances = self.aws_asg_service.list_running_ec2_instances([asg_name], lifecycle_states=valid_states)
            return instances[asg_name]
