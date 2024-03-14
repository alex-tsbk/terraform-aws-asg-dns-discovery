import abc
from typing import Union

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupDnsConfigItem


class DnsValueResolverInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def resolve_dns_value(
        self, dns_config_item: ScalingGroupDnsConfigItem, lifecycle_event: LifecycleEventModel
    ) -> Union[list[str], None]:
        """Resolves the value of a DNS record.

        Args:
            dns_config_item (ScalingGroupDnsConfigItem): The DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.

        Returns:
            Union[list[str], None]: The value of the DNS record, or None if can't be resolved
        """
        pass
