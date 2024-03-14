import time

from app.infrastructure.aws.dynamodb_repository import DynamoDBRepository
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from botocore.exceptions import ClientError


class AwsDistributedLockService:
    """Service class for acquiring and releasing shared state resource locks."""

    def __init__(self, dynamodb_repository: DynamoDBRepository) -> None:
        self.logger = get_logger()
        self.dynamodb_repository = dynamodb_repository

    def check_lock(self, resource_id: str) -> bool:
        """Checks if a lock exists on a resource.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be checked for.

        Returns:
            bool: True if lock exists, False otherwise

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        self.logger.debug(f"Checking lock for resource: {resource_id}")
        try:
            item = self.dynamodb_repository.get_item(resource_id)
            self.logger.debug(f"check_lock item: {to_json(item)}")
        except ClientError as e:
            raise CloudProviderException(f"Error checking lock for resource: {resource_id}", e)
        return bool(item)

    def acquire_lock(self, resource_id: str) -> bool:
        """Acquires a lock on a resource.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be acquired on.

        Returns:
            bool: True if lock is acquired, False otherwise

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        try:
            self.logger.debug(f"Acquiring lock for resource: {resource_id}")
            response = self.dynamodb_repository.put_item(
                item={"resource_id": resource_id, "timestamp": int(time.time())},
                condition_expression="attribute_not_exists(resource_id)",
            )
            self.logger.debug(f"acquire_lock response: {to_json(response)}")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            else:
                raise CloudProviderException(f"Error acquiring lock for resource: {resource_id}", e)

    def release_lock(self, resource_id: str) -> None:
        """Releases a lock on a resource.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be released for.

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        self.logger.debug(f"Releasing lock for resource: {resource_id}")
        try:
            self.dynamodb_repository.delete_item(resource_id)
        except ClientError as e:
            raise CloudProviderException(f"Error releasing lock for resource: {resource_id}", e)
