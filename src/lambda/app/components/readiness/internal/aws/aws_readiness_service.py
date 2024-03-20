from time import sleep
from typing import TYPE_CHECKING

from app.components.readiness.readiness_interface import ReadinessInterface
from app.config.models.readiness_config import ReadinessConfig
from app.infrastructure.aws.ec2_service import Ec2Service
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import Instance


class AwsReadinessService(ReadinessInterface):
    """Implementation of ReadinessInterface for checking readiness of AWS EC2 instance.

    Args:
        ReadinessInterface (_type_): _description_
    """

    def __init__(self, ec2_service: Ec2Service) -> None:
        self.logger = get_logger()
        self.ec2_service = ec2_service

    def is_ready(self, instance_id: str, readiness_config: ReadinessConfig, wait: bool) -> bool:
        """Checks if the instance is ready.

        Args:
            instance_id (str): Instance ID
            readiness_config (ReadinessConfig): Readiness configuration
            wait (bool): Whether to wait for the instance to become ready

        Returns:
            bool: True if service is ready, False otherwise
        """
        if not readiness_config.enabled:
            return True

        instance: Instance = self.ec2_service.get_instance(instance_id)
        if not instance:
            return False

        tag_key = readiness_config.tag_key
        tag_value = readiness_config.tag_value
        tag_match = self._match_tag(tag_key, tag_value, instance.tags)

        if tag_match:
            return True

        if not wait:
            return False

        sleeping_for = 0
        tag_match_timeout = readiness_config.timeout_seconds
        tag_match_interval = readiness_config.interval_seconds

        # Wait for instance to become ready
        while not tag_match and sleeping_for <= tag_match_timeout:
            instance.reload()  # Refreshes instance tags
            tag_match = self._match_tag(tag_key, tag_value, instance.tags)
            if tag_match:
                return True
            self.logger.info(
                f"Waiting for readiness tag: {tag_key}={tag_value} on instance: {instance_id}.. [{sleeping_for}s/{tag_match_timeout}s]"
            )
            sleep(tag_match_interval)
            sleeping_for += tag_match_interval

        self.logger.error(
            f"Instance readiness check failed: {instance_id}. Not tag pair found: {tag_key}={tag_value} after {tag_match_timeout}s."
        )
        return False

    @staticmethod
    def _match_tag(tag_key: str, tag_value: str, tags: list[dict]) -> dict | None:
        """Finds tag by key and ensures value match in list of tags.

        Args:
            tag_key (str): Tag key
            tag_value (str): Tag value
            tags (list[dict]): List of tags
                [
                    {
                        "Key": "Name",
                        "Value": "my-instance"
                    },
                    ...
                ]

        Returns:
            dict: Tag object if found, None otherwise
        """
        return next(
            filter(lambda t: t["Key"] == tag_key and t["Value"] == tag_value, tags),
            None,
        )
