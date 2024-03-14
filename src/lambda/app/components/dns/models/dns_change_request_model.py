from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from app.utils.dataclass import DataclassBase


class DnsChangeRequestAction(Enum):
    """Enum representing the DNS change request actions"""

    # CREATE: Create a new record.
    CREATE = "CREATE"
    # DELETE: Delete an existing record.
    DELETE = "DELETE"
    # UPDATE: Update an existing record.
    UPDATE = "UPDATE"
    # IGNORE: Do nothing.
    IGNORE = "IGNORE"

    @staticmethod
    def from_str(label: str):
        """Returns the DNS change request action from the label"""
        if not hasattr(DnsChangeRequestAction, label.upper()):
            raise NotImplementedError(f"Unsupported action: {label}")
        return DnsChangeRequestAction[label.upper()]


@dataclass
class DnsChangeRequestModel(DataclassBase):
    """Model representing a DNS change request to reach desired DNS record state."""

    # The action to perform. Example: UPDATE, CREATE, DELETE.
    action: DnsChangeRequestAction
    # Name of the record to change. Example: myapp.example.com or myapp.
    record_name: str
    # Type of the record. Example: A, CNAME, TXT, etc.
    record_type: str
    # Time to live for the record.
    record_ttl: int = field(default=300)
    # Weight for weighted records. Used only for records with a type of SRV or TXT.
    record_weight: int = field(default=0)
    # Priority for records. Used only for records with a type of SRV or MX.
    record_priority: int = field(default=0)
    # List of record values. Depending on the record type, it can be a list of IPs, CNAMEs, etc.
    record_values: list = field(default_factory=list)

    def __post_init__(self):
        self.record_type = self.record_type.upper()

    def __str__(self) -> str:
        return f"{self.record_name}/{self.record_type}/{self.action}/{', '.join(self.record_values)}"

    @abstractmethod
    def build_change(self) -> "DnsChangeRequestModel":
        """Builds a change for the underlying DNS provider."""
        pass

    @abstractmethod
    def get_change(self) -> dict:
        """Get the dict representation of the change request."""
        pass
