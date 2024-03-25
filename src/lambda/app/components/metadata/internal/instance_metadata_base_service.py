from abc import ABC, abstractmethod
from typing import Literal, Union

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration


class InstanceMetadataBaseService(InstanceMetadataInterface, ABC):
    """Base class for resolving values from instance metadata."""

    def resolve_value(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
    ) -> list[MetadataResultModel]:
        """Resolves the value(s) from instance(s) metadata.

        Args:
            sg_config_item (ScalingGroupConfiguration): The scaling group configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event for which to resolve the value.

        Returns:
            list[MetadataResultModel]: The values resolved.

        Remarks:
            There are few supported sources for the metadata value:
            - ip:public - resolves the public IP addresses of the instances.
            - ip:private - resolves the private IP addresses of the instances.
            - tag:<tag_name> - resolves the value of the specified tag for the instances.
        """
        match sg_config_item.dns_config.value_source.split(":"):
            case [source, value] if source == "ip":
                return self.handle_ip_source(sg_config_item, lifecycle_event, value)
            case [source, value] if source == "tag":
                return self.handle_tag_source(sg_config_item, lifecycle_event, value)
            case _:
                return None

    @abstractmethod
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
        pass

    @abstractmethod
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
            tag_name (str): Name of the tag to resolve value from.

        Returns:
            list[MetadataResultModel]: The list containing information about values resolved.
        """
        pass
