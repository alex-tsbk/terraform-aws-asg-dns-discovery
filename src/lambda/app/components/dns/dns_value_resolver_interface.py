from abc import ABCMeta, abstractmethod
from typing import Union

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration


class DnsValueResolverInterface(metaclass=ABCMeta):
    """Base interface for resolving values for DNS records.

    Args:
        metaclass (_type_, optional): _description_. Defaults to ABCMeta.
    """

    @abstractmethod
    def resolve_dns_value(
        sg_config_item: ScalingGroupConfiguration, lifecycle_event: LifecycleEventModel
    ) -> Union[list[str], None]:
        """Resolves the value of a DNS record.

        Args:
            sg_config_item (ScalingGroupConfiguration): The DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.

        Returns:
            Union[list[str], None]: The value of the DNS record, or None if can't be resolved
        """
        pass
