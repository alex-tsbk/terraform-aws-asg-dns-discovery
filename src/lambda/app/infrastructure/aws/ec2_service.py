from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
from app.infrastructure.aws import boto_config
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import EC2ServiceResource, Instance


class Ec2Service:
    """Service class for interacting with EC2."""

    ec2_resource: EC2ServiceResource = boto3.resource("ec2", config=boto_config.CONFIG)

    def __init__(self):
        self.logger = get_logger()

    def get_instance(self, instance_id: str) -> Instance:
        """Returns EC2 instance object by instance ID

        Args:
            instance_id [str]: EC2 instance ID

        Returns:
            EC2Instance: EC2 instance object
        """
        return self.ec2_resource.Instance(instance_id)

    def get_instances(self, instance_ids: list[str]) -> list[Instance]:
        """Returns EC2 instance objects by instance IDs

        Args:
            instance_ids [list[str]]: EC2 instance IDs

        Returns:
            list[EC2Instance]: List of EC2 instance objects
        """
        return [self.ec2_resource.Instance(instance_id) for instance_id in instance_ids]
