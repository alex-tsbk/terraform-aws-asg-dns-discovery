from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class MetadataResultModel(DataclassBase):
    """Model representing the result of a metadata request"""

    # Instance id
    instance_id: str
    # Instance launch timestamp (epoch)
    instance_launch_timestamp: int
    # Value resolved
    value: str
    # Source of the value
    source: str = field(default="")
