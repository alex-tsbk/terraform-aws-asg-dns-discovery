from __future__ import annotations

from inspect import signature
from typing import Any, Type

from app.utils.singleton import Singleton


class DIContainer:
    """Simple DI container. Supports transient and scoped lifetimes.

    Usage example:
        ```
        class Foo:
            def __init__(self):
                pass

        class Bar:
            def __init__(self, foo: Foo):
                self.foo = foo

        container = DIContainer()
        container.register(Foo, Foo, lifetime="scoped")
        container.register(Bar, Bar, lifetime="transient")
        bar = container.build(Bar)
        ```
    """

    _instance: "DIContainer" = None

    def __init__(self) -> None:
        self._services = {}
        self._scoped_instances = {}

    def register(self, interface: Type, implementation: Type, name: str = None, lifetime: str = "transient"):
        key = (interface, name)
        self._services[key] = (implementation, lifetime)

    def build(self, interface: Type, name: str = None) -> Any:
        key = (interface, name)
        if key not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered.")
        implementation, lifetime = self._services[key]

        if lifetime == "scoped":
            if key in self._scoped_instances:
                return self._scoped_instances[key]
            instance = self._create_instance(implementation)
            self._scoped_instances[key] = instance
            return instance
        elif lifetime == "transient":
            return self._create_instance(implementation)
        else:
            raise ValueError(f"Unsupported lifetime {lifetime}.")

    def resolve(self, interface: Type, name: str = None) -> Any:
        """Resolves an instance of the given interface from the container.

        Args:
            interface (Type): _description_
            name (str, optional): _description_. Defaults to None.

        Returns:
            Any: _description_
        """
        return self.build(interface, name)

    def _create_instance(self, cls: Type) -> Any:
        """_summary_

        Args:
            cls (Type): _description_

        Returns:
            Any: _description_
        """
        constructor = signature(cls.__init__)
        kwargs = {}
        for name, param in constructor.parameters.items():
            if name == "self":
                continue
            param_type = param.annotation
            kwargs[name] = self.build(param_type)
        return cls(**kwargs)


# container = DIContainer()
# container.register(Foo, Foo, lifetime="scoped")
# container.register(Bar, Bar, lifetime="transient")

# bar = container.build(Bar)
# print(bar)
