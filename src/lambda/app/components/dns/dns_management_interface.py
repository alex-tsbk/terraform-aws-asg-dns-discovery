import abc

from app.components.dns.models.dns_change_request_model import DnsChangeRequestModel
from app.components.dns.models.dns_change_response_model import DnsChangeResponseModel
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupDnsConfigItem


class DnsManagementInterface(metaclass=abc.ABCMeta):
    """Interface for managing DNS records."""

    @abc.abstractmethod
    def generate_change_request(
        self, dns_config_item: ScalingGroupDnsConfigItem, lifecycle_event: LifecycleEventModel
    ) -> DnsChangeRequestModel:
        """For a given set of input parameters, generate a change set to update the values for DNS record.

        Args:
            dns_config_item [str]: The Scaling Group DNS configuration item.
            lifecycle_event [LifecycleEventModel]: The lifecycle event.

        Returns:
            DnsChangeRequestModel: The model that represents the change set to update the value of the DNS record.
        """
        pass

    @abc.abstractmethod
    def apply_change_request(
        self, dns_config_item: ScalingGroupDnsConfigItem, change_request: DnsChangeRequestModel
    ) -> DnsChangeResponseModel:
        """Apply the change request to the DNS record.

        Args:
            dns_config_item [ScalingGroupDnsConfigItem]: The Scaling Group DNS configuration item.
            change_request [DnsChangeRequestModel]: The change request model.

        Returns:
            DnsChangeResponseModel: The model that represents the response of the change request.
        """
        pass
