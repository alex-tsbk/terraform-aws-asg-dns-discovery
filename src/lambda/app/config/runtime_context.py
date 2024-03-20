import os

from app.utils.singleton import Singleton


class RuntimeContext(metaclass=Singleton):
    @property
    def is_aws(self) -> bool:
        return os.environ.get("cloud_provider", "").lower() == "aws"

    @property
    def is_development(self) -> bool:
        """Returns True if the environment is local development, False otherwise."""
        return os.environ.get("SG_DNS_DISCOVERY__ENVIRONMENT", "").lower() == "development"
