from abc import ABCMeta, abstractmethod

from .models.lifecycle_event_model import LifecycleAction, LifecycleEventModel


class InstanceLifecycleInterface(metaclass=ABCMeta):
    """Interface for instance lifecycle service"""

    @abstractmethod
    def complete_lifecycle_action(self, event: LifecycleEventModel, action: LifecycleAction) -> bool:
        """Completes the lifecycle action for the instance with the provided result.

        Args:
            event (LifecycleEventModel): Event object
            action (LifecycleAction): Action to proceed with

        Returns:
            bool: True if lifecycle action was completed (acknowledged) without error, False otherwise
        """
        pass
