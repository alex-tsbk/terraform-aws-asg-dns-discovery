import os

from app.utils.singleton import Singleton


class RuntimeContext(metaclass=Singleton):
    @property
    def is_aws(self) -> bool:
        return os.environ.get("cloud_provider", "").lower() == "aws"
