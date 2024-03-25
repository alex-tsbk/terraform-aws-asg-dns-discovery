from abc import ABCMeta, abstractmethod

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration

from .models.metadata_result_model import MetadataResultModel


class InstanceMetadataInterface(metaclass=ABCMeta):
    """Interface for resolving value from instance metadata."""

    @abstractmethod
    def resolve_value(
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
        pass
