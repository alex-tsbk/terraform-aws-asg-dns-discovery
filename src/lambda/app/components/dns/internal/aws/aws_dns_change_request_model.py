from __future__ import annotations

from dataclasses import field
from typing import override

from app.components.dns.models.dns_change_request_model import DnsChangeRequestAction, DnsChangeRequestModel


class AwsDnsChangeRequestModel(DnsChangeRequestModel):
    """Model for AWS Route53 change request."""

    # Private attributes
    _change: dict = field(init=False, repr=False, default_factory=dict)

    @override
    def get_change(self) -> dict:
        """Returns a fully-constructed change batch to update the IPs in the DNS record set for Route53.

        Args:
            hosted_zone_id [str]: The ID of the hosted zone that contains the resource record sets that you want to change.

        Returns:
            dict: The change batch to update the IPs.
                Example of A record change batch:
                {
                    'Changes': [{
                        'Action': 'UPSERT' | 'CREATE' | 'DELETE',
                        'ResourceRecordSet': {
                            'Name': record_name,
                            'Type': record_type,
                            'TTL': record_ttl,
                            'ResourceRecords': [{'Value': ip} for ip in ips]
                        }
                    }]
                }
        """
        return {"Changes": [self._change]}

    @override
    def build_change(self) -> "AwsDnsChangeRequestModel":
        """Generate a change request for a record based on record type.

        Returns:
            AwsDnsChangeRequestModel: The change request.
        """
        match self.record_type:
            case "A":
                self._change = self._build_A_record_change()
            case _:
                raise NotImplementedError(
                    f"No change implementation found in 'AwsDnsChangeRequestModel' for record type: {self.record_type}"
                )
        return self

    def _build_A_record_change(self) -> dict:
        """Build an A record change.

        Returns:
            dict: The A record change.
        """
        return {
            "Action": self._get_route53_change_action_name(self.action),
            "ResourceRecordSet": {
                "Name": self.record_name,
                "Type": self.record_type,
                "TTL": self.record_ttl,
                "ResourceRecords": [{"Value": value} for value in sorted(list(set(self.record_values)))],
            },
        }

    @staticmethod
    def _get_route53_change_action_name(action: DnsChangeRequestAction) -> str:
        """Get Route53 change action.

        Args:
            action [DnsChangeRequestAction]: The action to perform.

        Returns:
            str: The Route53 change action.
        """
        if action in [DnsChangeRequestAction.CREATE, DnsChangeRequestAction.UPDATE]:
            return "UPSERT"
        elif action == DnsChangeRequestAction.DELETE:
            return "DELETE"

        raise ValueError(f"Unsupported action in 'AwsDnsChangeRequestModel': {action}")
