from threading import Lock


class Singleton(type):
    """Thread-safe metaclass for creating singleton classes"""

    _instances = {}
    _lock = Lock()  # Class-level lock

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:  # Acquire lock
                if cls not in cls._instances:  # Double-checked locking
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
