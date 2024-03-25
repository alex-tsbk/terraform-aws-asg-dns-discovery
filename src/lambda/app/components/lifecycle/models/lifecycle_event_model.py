from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from app.utils.dataclass import DataclassBase


class LifecycleTransition(Enum):
    """Represents the possible lifecycle transitions

    Reference:
        For AWS - please see https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html#lifecycle-hooks-availability
    """

    # In the context of AWS AutoScaling Lifecycle Hooks this would represent:
    # - Instance launching in ASG and joins the fleet
    # - Instance moving from WarmPool into the fleet
    # Important: Does not apply when you attach or detach instances,
    # move instances in and out of standby mode, or delete the group with the force delete option.
    # For these actions, must enable reconciliation service to handle such transitions.
    LAUNCHING = "LAUNCHING"
    # In the context of AWS AutoScaling Lifecycle Hooks this would represent:
    # - Instance terminating from ASG and leaves the fleet
    # - Instance moving to WarmPool from the fleet
    DRAINING = "DRAINING"
    # Represents the reconciliation of the instance state. This is triggered outside of lifecycle hooks (separate service)
    RECONCILING = "RECONCILING"
    # Represents the unrelated lifecycle event, not related to the lifecycle hooks but useful for observability purposes
    UNRELATED = "UNRELATED"


class LifecycleAction(Enum):
    """Describes lifecycle action to proceed as with as result of LifecycleTransition"""

    # In the context of AWS AutoScaling Lifecycle Hooks this would represent:
    # - Continue the instance launch or draining (termination)
    CONTINUE = "CONTINUE"
    # - Abandon the instance launch. For the termination - this can't really be prevented.
    ABANDON = "ABANDON"


@dataclass
class LifecycleEventModel(DataclassBase):
    """
    Model representing the information about lifecycle event
    """

    transition: LifecycleTransition  # Transition state of the instance
    lifecycle_hook_name: str = field(default="")  # Name of the lifecycle hook
    scaling_group_name: str = field(default="")  # Name of the scaling group
    instance_id: str = field(default="")  # Instance id

    def __post_init__(self):
        if self.transition in [LifecycleTransition.LAUNCHING, LifecycleTransition.DRAINING]:
            transition_name = self.transition.value
            if not self.lifecycle_hook_name:
                raise ValueError(f"Lifecycle hook name is required for {transition_name} transition")
            if not self.scaling_group_name:
                raise ValueError(f"Scaling group name is required for {transition_name} transition")
            if not self.instance_id:
                raise ValueError(f"Instance id is required for {transition_name} transition")
