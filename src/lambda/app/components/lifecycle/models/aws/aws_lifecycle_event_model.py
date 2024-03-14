from dataclasses import dataclass

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition


@dataclass
class AwsLifecycleEventModel(LifecycleEventModel):
    """
    Model representing the lifecycle event received from SNS:

        {
            "Origin": "AutoScalingGroup",
            "LifecycleHookName": "dev-asg-service-discovery-drain-lch",
            "Destination": "EC2",
            "AccountId": "123456789123",
            "RequestId": "a696378f-0ac5-68d3-d6a4-688f99ecd5b4",
            "LifecycleTransition": "autoscaling:EC2_INSTANCE_TERMINATING",
            "AutoScalingGroupName": "v2-adsbx-dev-vpc-a-vrs-global-asg",
            "Service": "AWS Auto Scaling",
            "Time": "2024-02-26T04:53:24.631Z",
            "EC2InstanceId": "i-03a2b505b266b2eaa",
            "NotificationMetadata": "{\"asg_name\":\"v2-adsbx-dev-vpc-a-vrs-global-asg\",...}",
            "LifecycleActionToken": "451ac51f-6fdc-486f-9027-745b0c254a31"
        }
    """

    origin: str  # Describes the origin state of the VM
    destination: str  # Describes the destination state of the VM
    service: str  # Service that triggered the event
    deduplication_token: str  # Token to prevent duplicate processing of lifecycle event
    lifecycle_transition: str  # In AWS:autoscaling:EC2_INSTANCE_TERMINATING
    notification_metadata: dict  # Notification metadata

    @classmethod
    def from_dict(cls, data: dict):
        origin = data.get("Origin")
        destination = data.get("Destination")

        def determine_transition(origin: str, destination: str) -> LifecycleTransition:
            if origin == "AutoScalingGroup" and destination == ["EC2", "WarmPool"]:
                return LifecycleTransition.DRAINING
            elif origin in ["EC2", "WarmPool"] and destination == "AutoScalingGroup":
                return LifecycleTransition.LAUNCHING
            # If the origin and destination are not related to the lifecycle event
            return LifecycleTransition.UNRELATED

        params = {
            # Base fields
            "transition": determine_transition(origin, destination),
            "lifecycle_hook_name": data.get("LifecycleHookName"),
            "scaling_group_name": data.get("AutoScalingGroupName"),
            "instance_id": data.get("EC2InstanceId"),
            # AWS specific fields
            "origin": origin,
            "destination": destination,
            "service": data.get("Service"),
            "deduplication_token": data.get("LifecycleActionToken"),
            "lifecycle_transition": data.get("LifecycleTransition"),
        }
        return cls(**params)
