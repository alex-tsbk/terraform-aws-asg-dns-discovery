from abc import ABCMeta, abstractmethod

from app.config.models.readiness_config import ReadinessConfig


class ReadinessInterface(metaclass=ABCMeta):
    """Interface for readiness service implementations"""

    @abstractmethod
    def is_ready(instance_id: str, readiness_config: ReadinessConfig, wait: bool) -> bool:
        """Checks if the instance is ready.

        Args:
            instance_id (str): Instance ID
            readiness_config (ReadinessConfig): Readiness configuration
            wait (bool): Whether to wait for the instance to become ready

        Returns:
            bool: True if service is ready, False otherwise
        """
        pass
