from dataclasses import dataclass, field
from enum import Enum

from app.utils.dataclass import DataclassBase


class DnsRecordProvider(Enum):
    """DNS record provider"""

    ROUTE53 = "route53"
    CLOUDFLARE = "cloudflare"
    MOCK = "mock"


@dataclass
class DnsRecordConfig(DataclassBase):
    """Model representing the DNS record configuration"""

    # DNS configuration
    provider: DnsRecordProvider = field(default=DnsRecordProvider.ROUTE53)
    dns_zone_id: str = field(default="")
    record_name: str = field(default="")
    record_ttl: int = field(default=60)
    record_type: str = field(default="A")
    # DNS record priority and weight for SRV records
    record_priority: int = field(default=0)
    record_weight: int = field(default=0)
    # Whether the DNS record is managed by the terraform
    managed_dns_record: bool = field(default=False)
    # Default mock IP address to use when DNS record is managed
    dns_mock_ip: str = field(default="1.0.0.217")

    def __post_init__(self):
        """Validate the DNS record configuration"""
        self.record_type = self.record_type.upper()

        if self.record_ttl < 1 or self.record_ttl > 604800:
            raise ValueError(f"Invalid record TTL: {self.record_ttl}")

    @staticmethod
    def from_dict(item: dict) -> "DnsRecordConfig":
        """Create a DNS record configuration from a dictionary"""
        return DnsRecordConfig(
            provider=DnsRecordProvider(str(item.get("provider", "route53")).upper()),
            dns_zone_id=item.get("dns_zone_id", ""),
            record_name=item.get("record_name", ""),
            record_ttl=item.get("record_ttl", 60),
            record_type=item.get("record_type", "A"),
            record_priority=item.get("record_priority", 0),
            record_weight=item.get("record_weight", 0),
            managed_dns_record=str(item.get("managed_dns_record", False)).lower() == "true",
            dns_mock_ip=item.get("dns_mock_ip", "1.0.0.217"),
        )
