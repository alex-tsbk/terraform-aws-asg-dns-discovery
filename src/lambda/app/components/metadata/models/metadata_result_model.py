from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class MetadataResultModel(DataclassBase):
    """Model representing the result of a metadata request"""

    # Instance id
    instance_id: str
    # Value resolved
    value: str
    # Instance launch timestamp (epoch)
    instance_launch_timestamp: int = field(default=0)
    # Source of the value
    source: str = field(default="")
