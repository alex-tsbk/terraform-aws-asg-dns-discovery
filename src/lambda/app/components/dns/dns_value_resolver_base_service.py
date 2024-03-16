from abc import ABC, abstractmethod
from typing import Literal, Union

from app.components.dns.dns_value_resolver_interface import DnsValueResolverInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration


class DnsValueResolverService(DnsValueResolverInterface, ABC):
    """Base class for resolving values for DNS records."""

    def resolve_dns_value(
        self, sg_config_item: ScalingGroupConfiguration, lifecycle_event: LifecycleEventModel
    ) -> Union[list[str], None]:
        """Resolves the value of a DNS record.

        Args:
            sg_config_item (ScalingGroupConfiguration): The DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.

        Returns:
            Union[list[str], None]: The value of the DNS record.
        """
        match sg_config_item.value_source.split(":"):
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
    ) -> list[str]:
        """Handle IP source.

        Args:
            sg_config_item (ScalingGroupConfiguration): Scaling Group DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.
            ip_type (str): IP value to use - public or private.

        Returns:
            list[str]: The list of IPs.
        """
        pass

    @abstractmethod
    def handle_tag_source(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        tag_name: str,
    ) -> list[str]:
        """Handle tag source.

        Args:
            sg_config_item (ScalingGroupConfiguration): Scaling Group DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.
            tag_name (str): Name of the tag to resolve value from.

        Returns:
            list[str]: Single value wrapped in a list.
        """
        pass
