from app.components.lifecycle.instance_lifecycle_interface import InstanceLifecycleInterface
from app.components.lifecycle.models.aws.aws_lifecycle_event_model import AwsLifecycleEventModel
from app.components.lifecycle.models.lifecycle_event_model import LifecycleAction
from app.infrastructure.aws.asg_service import AwsAutoScalingService
from app.utils.logging import get_logger


class AwsInstanceLifecycleService(InstanceLifecycleInterface):
    """Service for managing the lifecycle of an instance."""

    def __init__(self, autoscaling_service: AwsAutoScalingService):
        self.logger = get_logger()
        self.autoscaling_service = autoscaling_service

    def complete_lifecycle_action(self, event: AwsLifecycleEventModel, action: LifecycleAction) -> bool:
        """Completes the lifecycle action for the instance with the provided result.

        Args:
            event (AwsLifecycleEventModel): Aws event object
            action (LifecycleAction): Action to proceed with

        Returns:
            bool: True if lifecycle action was completed (acknowledged) without error, False otherwise
        """
        ec2_instance_id = event.instance_id
        self.autoscaling_service.complete_lifecycle_action(
            lifecycle_hook_name=event.lifecycle_hook_name,
            autoscaling_group_name=event.scaling_group_name,
            lifecycle_action_token=event.lifecycle_action_token,
            lifecycle_action_result=action.value,
            ec2_instance_id=event.instance_id,
        )
        self.logger.info(f"Lifecycle action completed for instance: {ec2_instance_id}")
