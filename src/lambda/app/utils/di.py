from __future__ import annotations

from inspect import signature
from typing import Annotated, Any, Type, TypeVar

T = TypeVar("T")
# Use this annotation to inject named dependency registered in the container.
# Example:
# class Foo:
#     def __init__(self):
#         pass
#
# class Bar:
#     def __init__(self, foo: NamedDependency[Foo, "foo"]):
#         self.foo = foo
#
# container = DIContainer()
# container.register(Foo, Foo, lifetime="scoped", name="foo")
# container.register(Bar, Bar, lifetime="transient")
# bar = container.resolve(Bar)
# assert isinstance(bar.foo, Foo)
NamedDependency = Annotated


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
        container.register(Foo, Foo, lifetime="scoped")  # will create a single instance of Foo and reuse it
        container.register(Bar, Bar, lifetime="transient")  # will create a new instance of Bar every time it's resolved
        foo1 = container.resolve(Foo)
        foo2 = container.resolve(Foo)
        # foo1 and foo2 are the same instance
        bar1 = container.resolve(Bar)
        bar2 = container.resolve(Bar)
        # bar1 and bar2 are different instances
        ```
    """

    def __init__(self) -> None:
        self._services = {}
        self._scoped_instances = {}

    def register(self, interface: Type, implementation: Type, name: str = None, lifetime: str = "transient"):
        key = (interface, name)
        self._services[key] = (implementation, lifetime)

    def register_instance(self, instance: Any, name: str = None, allow_override: bool = False):
        """Registers an instance in the container.

        Args:
            instance (Any): Instance to register.
            name (str, optional): When provided, will be a named instance. Defaults to None.
            allow_override (bool, optional): When set to True, allows overriding existing instance. Defaults to False.

        Raises:
            ValueError: If instance with the same name is already registered and allow_override is False.
        """
        key = (type(instance), name)
        if key in self._services and not allow_override:
            raise ValueError(f"Service {key} is already registered. Please set allow_override to True to override.")
        self._services[key] = (instance, "instance")

    def resolve(self, interface: Type, name: str = None) -> Any:
        """Resolves an instance of the given interface from the container.

        Args:
            interface (Type): Type of the interface to resolve.
            name (str, optional): If named instance is required, provide name. Defaults to None.

        Returns:
            Any: Instance of the given interface.
        """
        return self._build(interface, name)

    def _build(self, interface: Type, name: str = None) -> Any:
        key = (interface, name)
        if key not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered.")
        implementation, lifetime = self._services[key]

        if lifetime == "instance":
            return implementation
        elif lifetime == "scoped":
            if key in self._scoped_instances:
                return self._scoped_instances[key]
            instance = self._create_instance(implementation)
            self._scoped_instances[key] = instance
            return instance
        elif lifetime == "transient":
            return self._create_instance(implementation)
        else:
            raise ValueError(f"Unsupported lifetime {lifetime}.")

    def _create_instance(self, cls: Type) -> Any:
        """Creates an instance of the given class by resolving its dependencies.

        Args:
            cls (Type): Type of the class to create.

        Returns:
            Any: Instance of the given class.
        """
        constructor = signature(cls.__init__)
        kwargs = {}
        for name, param in constructor.parameters.items():
            if name == "self":
                continue
            param_type = param.annotation

            # Check if param_type is NamedDependency
            if param_type.__name__ == NamedDependency.__name__:
                dependency_type = param_type.__origin__
                dependency_name = param_type.__metadata__[0]
                kwargs[name] = self._build(dependency_type, dependency_name)
            else:
                kwargs[name] = self._build(param_type)
        return cls(**kwargs)
