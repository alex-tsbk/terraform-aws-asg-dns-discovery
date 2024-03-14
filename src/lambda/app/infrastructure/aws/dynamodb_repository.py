from __future__ import annotations

from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

from app.infrastructure.aws import boto_config
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class DynamoDBRepository:
    """Repository for accessing items in DynamoDB table."""

    dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb", config=boto_config.CONFIG)

    def __init__(self, table_name: str):
        self.logger = get_logger()
        self.table: Table = self.dynamodb.Table(table_name)

    def get_item(self, resource_id: str) -> dict:
        """Get item from DynamoDB table.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource.

        Returns:
            dict: Item from DynamoDB table
        """
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/get_item.html
        response: dict = self.table.get_item(Key={"resource_id": resource_id}, ConsistentRead=True)
        self.logger.debug(f"get_item response: {to_json(response)}")
        return response.get("Item", {})

    def put_item(self, item: dict, condition_expression: str = None) -> None:
        """Put item in DynamoDB table.

        Args:
            item (dict): Item to be put in DynamoDB table
            condition_expression (str): Condition expression for conditional writes
        """
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/put_item.html
        kwargs = {"Item": item}
        if condition_expression:
            kwargs["ConditionExpression"] = condition_expression
        response = self.table.put_item(**kwargs)
        self.logger.debug(f"put_item response: {to_json(response)}")
        return response

    def delete_item(self, resource_id: str) -> None:
        """Delete item from DynamoDB table.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource.
        """
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/delete_item.html
        response = self.table.delete_item(Key={"resource_id": resource_id})
        self.logger.debug(f"delete_item response: {to_json(response)}")
        return response
