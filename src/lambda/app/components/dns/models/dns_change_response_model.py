from dataclasses import field

from app.utils.dataclass import DataclassBase


class DnsChangeResponseModel(DataclassBase):
    """Represents the response of a DNS change request"""

    successful: bool
    message: str = field(default="")

    @classmethod
    def SUCCESS(cls):
        return cls(successful=True)

    @classmethod
    def FAILURE(cls):
        return cls(successful=False)
