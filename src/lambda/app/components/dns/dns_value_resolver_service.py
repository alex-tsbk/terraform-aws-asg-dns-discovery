from abc import ABC, abstractmethod
from typing import Literal, Union

from app.components.dns.dns_value_resolver_interface import DnsValueResolverInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupDnsConfigItem


class DnsValueResolverService(DnsValueResolverInterface, ABC):
    """Base class for resolving values for DNS records."""

    def __init__(self, underlying_service: "DnsValueResolverService") -> None:
        super().__init__()
        self.underlying_service = underlying_service

    def resolve_dns_value(
        self, dns_config_item: ScalingGroupDnsConfigItem, lifecycle_event: LifecycleEventModel
    ) -> Union[list[str], None]:
        """Resolves the value of a DNS record.

        Args:
            dns_config_item (ScalingGroupDnsConfigItem): The DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.

        Returns:
            Union[list[str], None]: The value of the DNS record.
        """
        match dns_config_item.value_source.split(":"):
            case [source, value] if source == "ip":
                return self.underlying_service.handle_ip_source(dns_config_item, lifecycle_event, value)
            case [source, value] if source == "tag":
                return self.underlying_service.handle_tag_source(dns_config_item, lifecycle_event, value)
            case _:
                return None

    @abstractmethod
    def handle_ip_source(
        self,
        dns_config_item: ScalingGroupDnsConfigItem,
        lifecycle_event: LifecycleEventModel,
        ip_type: Literal["public", "private"],
    ) -> list[str]:
        """Handle IP source.

        Args:
            dns_config_item (ScalingGroupDnsConfigItem): The DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.
            ip_type (str): IP value to use - public or private.

        Returns:
            list[str]: The list of IPs.
        """
        pass

    @abstractmethod
    def handle_tag_source(
        self,
        dns_config_item: ScalingGroupDnsConfigItem,
        lifecycle_event: LifecycleEventModel,
        tag_name: str,
    ) -> list[str]:
        """Handle tag source.

        Args:
            dns_config_item (ScalingGroupDnsConfigItem): The DNS configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event.
            tag_name (str): Name of the tag to resolve value from.

        Returns:
            list[str]: Single value wrapped in a list.
        """
        pass
