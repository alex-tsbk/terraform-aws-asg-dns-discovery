import abc


class DistributedLockInterface(metaclass=abc.ABCMeta):
    """Defines interface for metrics service implementations"""

    @abc.abstractmethod
    def check_lock(self, lock_key: str) -> bool:
        """Checks if a lock exists.

        Args:
            lock_key (str): Lock key that uniquely identifies the lock to be checked for.

        Returns:
            bool: True if lock exists, False otherwise
        """
        pass

    @abc.abstractmethod
    def acquire_lock(self, lock_key: str) -> bool:
        """Acquires a lock.

        Args:
            lock_key (str): Lock key that uniquely identifies the lock to be acquired.

        Returns:
            bool: True if lock is acquired, False otherwise
        """
        pass

    @abc.abstractmethod
    def release_lock(self, lock_key: str) -> None:
        """Releases a lock on a resource.

        Args:
            lock_key (str): Lock key that uniquely identifies the lock to be acquired.
        """
        pass
