import pytest
from app.utils.di import DIContainer


class Foo:
    def __init__(self):
        pass


class Bar:
    def __init__(self, foo: Foo):
        self.foo = foo


@pytest.fixture
def di_container():
    container = DIContainer()
    yield container
    container._scoped_instances.clear()


def test_resolve_transient_instance(di_container):
    di_container.register(Foo, Foo, lifetime="transient")
    foo = di_container.resolve(Foo)
    assert isinstance(foo, Foo)


def test_resolve_transient_instance_with_name(di_container):
    di_container.register(Foo, Foo, lifetime="transient", name="foo1")
    foo = di_container.resolve(Foo, name="foo1")
    assert isinstance(foo, Foo)


def test_resolve_transient_instance_with_names(di_container):
    di_container.register(Foo, Foo, lifetime="transient", name="foo1")
    di_container.register(Foo, Foo, lifetime="transient", name="foo2")
    foo1 = di_container.resolve(Foo, name="foo1")
    foo2 = di_container.resolve(Foo, name="foo2")
    assert foo1 is not foo2


def test_resolve_scoped_instance(di_container):
    di_container.register(Foo, Foo, lifetime="scoped")
    foo1 = di_container.resolve(Foo)
    foo2 = di_container.resolve(Foo)
    assert foo1 is foo2


def test_resolve_with_dependency(di_container):
    di_container.register(Foo, Foo, lifetime="scoped")
    di_container.register(Bar, Bar, lifetime="transient")
    bar = di_container.resolve(Bar)
    assert isinstance(bar, Bar)
    assert isinstance(bar.foo, Foo)


def test_resolve_with_dependency_raises_error_when_service_not_registered(di_container):
    with pytest.raises(ValueError):
        di_container.resolve(Bar)


def test_register_instance(di_container):
    foo_instance = Foo()
    di_container.register_instance(foo_instance)
    resolved_instance = di_container.resolve(Foo)
    assert resolved_instance is foo_instance


def test_register_instance_with_name(di_container):
    foo_instance = Foo()
    di_container.register_instance(foo_instance, name="foo_instance")
    resolved_instance = di_container.resolve(Foo, name="foo_instance")
    assert resolved_instance is foo_instance


def test_register_instance_with_same_name_raises_error_when_allow_override_is_false(di_container):
    foo_instance1 = Foo()
    foo_instance2 = Foo()
    di_container.register_instance(foo_instance1, name="foo_instance")
    with pytest.raises(ValueError):
        di_container.register_instance(foo_instance2, name="foo_instance", allow_override=False)


def test_register_instance_with_same_name_allows_override_when_allow_override_is_true(di_container):
    foo_instance1 = Foo()
    foo_instance2 = Foo()
    di_container.register_instance(foo_instance1, name="foo_instance")
    di_container.register_instance(foo_instance2, name="foo_instance", allow_override=True)
    resolved_instance = di_container.resolve(Foo, name="foo_instance")
    assert resolved_instance is foo_instance2
