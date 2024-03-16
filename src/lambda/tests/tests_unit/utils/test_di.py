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


def test_build_transient_instance(di_container):
    di_container.register(Foo, Foo, lifetime="transient")
    foo = di_container.build(Foo)
    assert isinstance(foo, Foo)


def test_build_scoped_instance(di_container):
    di_container.register(Foo, Foo, lifetime="scoped")
    foo1 = di_container.build(Foo)
    foo2 = di_container.build(Foo)
    assert foo1 is foo2


def test_build_with_dependency(di_container):
    di_container.register(Foo, Foo, lifetime="scoped")
    di_container.register(Bar, Bar, lifetime="transient")
    bar = di_container.build(Bar)
    assert isinstance(bar, Bar)
    assert isinstance(bar.foo, Foo)


def test_build_with_dependency_raises_error_when_service_not_registered(di_container):
    with pytest.raises(ValueError):
        di_container.build(Bar)
