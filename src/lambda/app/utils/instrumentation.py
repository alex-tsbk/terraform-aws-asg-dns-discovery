import os

from dataclass import dataclass


@dataclass(frozen=True)
class RuntimeContext:
    is_aws: bool


RUNTIME_CONTEXT = RuntimeContext(is_aws=os.environ.get("cloud_provider", "").lower() == "aws")
