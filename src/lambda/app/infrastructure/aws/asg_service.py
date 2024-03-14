from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_autoscaling.client import AutoScalingClient
    from mypy_boto3_autoscaling.type_defs import FilterTypeDef

from app.infrastructure.aws import boto_config
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class AutoScalingService:
    """Service class for interacting with Auto-Scaling Groups."""

    autoscaling_client: AutoScalingClient = boto3.client("autoscaling", config=boto_config.CONFIG)

    def __init__(self):
        self.logger = get_logger()

    def list_running_ec2_instances(
        self,
        autoscaling_group_names: list[str],
        tag_filters: Sequence[FilterTypeDef] = None,
        lifecycle_states: list[str] = ["InService"],
    ) -> dict[str, list[str]]:
        """Lists the running EC2 instances in the Auto-Scaling Groups.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_auto_scaling_groups

        Args:
            autoscaling_group_names [list[str]]: The names of the Auto Scaling groups.
            tag_filters [list[dict]]: A list of tag filters to apply to the query.
            lifecycle_states [list[str]]: A list of lifecycle states to filter the results. ['InService'] is the default.
                Example: ['InService', 'Pending', 'Terminating', 'Terminated', 'Detaching', 'Detached']

        Returns:
            dict[str, list[str]]: A dictionary with the ASG name as the key and a list of EC2 instance IDs as the value.
        """
        kwargs = {"AutoScalingGroupNames": autoscaling_group_names}
        if tag_filters:
            kwargs["Filters"] = list(tag_filters)

        asg_ec2_instances: dict[str, list[str]] = {}

        # Get paginator and iterate through the results
        try:
            paginator = self.autoscaling_client.get_paginator("describe_auto_scaling_groups")
            iterable = paginator.paginate(**kwargs)
            for page in iterable:
                self.logger.debug(f"list_running_ec2_instances page: {to_json(page)}")
                if not page.get("AutoScalingGroups", None):
                    break
                for asg in page["AutoScalingGroups"]:
                    asg_ec2_instances[asg["AutoScalingGroupName"]] = [
                        instance["InstanceId"]
                        for instance in asg["Instances"]
                        if instance["LifecycleState"] in lifecycle_states
                    ]
        except ClientError as e:
            message = f"Error listing ASG running EC2 instances: {str(e)}"
            self.logger.error(message)
            raise e

        return asg_ec2_instances

    def complete_lifecycle_action(
        self,
        lifecycle_hook_name: str,
        autoscaling_group_name: str,
        lifecycle_action_token: str,
        lifecycle_action_result: str,
        ec2_instance_id: str,
    ) -> None:
        """Completes the lifecycle action for the ASG.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.complete_lifecycle_action

        Args:
            lifecycle_hook_name [str]: The name of the lifecycle hook.

            autoscaling_group_name [str]: The name of the Auto Scaling group.

            lifecycle_action_token [str]: UUID identifying a specific lifecycle action associated with an instance.
                ASG sends this token to the SNS specified when LCH is created.

            lifecycle_action_result [str]: The action for the group to take. This parameter can be either CONTINUE or ABANDON .

            ec2_instance_id [str]: EC2 instance ID.

        Raises:
            ClientError: When call fails to underlying boto3 function
        """
        try:
            response = self.autoscaling_client.complete_lifecycle_action(
                LifecycleHookName=lifecycle_hook_name,
                AutoScalingGroupName=autoscaling_group_name,
                LifecycleActionToken=lifecycle_action_token,
                LifecycleActionResult=lifecycle_action_result,
                InstanceId=ec2_instance_id,
            )
            self.logger.debug(f"complete_lifecycle_action response: {to_json(response)}")
        except ClientError as e:
            message = f"Error completing lifecycle action: {str(e)}"
            self.logger.error(message)
            raise e
