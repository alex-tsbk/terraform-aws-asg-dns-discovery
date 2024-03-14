from dataclasses import dataclass, field
from enum import Enum

from app.utils.dataclass import DataclassBase


class LifecycleTransition(Enum):
    """Represents the possible lifecycle transitions"""

    LAUNCHING = "LAUNCHING"
    DRAINING = "DRAINING"
    RECONCILING = "RECONCILING"
    UNRELATED = "UNRELATED"


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
