import os


class RuntimeContext:
    """Provides runtime context information - execution environment, cloud provider, etc."""

    @property
    @staticmethod
    def is_aws() -> bool:
        return os.environ.get("cloud_provider", "").lower() == "aws"

    @property
    @staticmethod
    def is_localhost_development() -> bool:
        """Returns True if the environment is local development, False otherwise."""
        return os.environ.get("SG_DNS_DISCOVERY__ENVIRONMENT", "").lower() == "development"
