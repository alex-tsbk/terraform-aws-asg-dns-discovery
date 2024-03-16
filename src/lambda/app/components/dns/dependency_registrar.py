from app.config.instrumentation import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .dns_management_interface import DnsManagementInterface
from .dns_management_service import DnsManagementService
from .dns_value_resolver_interface import DnsValueResolverInterface
from .dns_value_resolver_base_service import DnsValueResolverService


def register_services(di_container: DIContainer):
    """Registers DNS services in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_dns_management_service import AwsDnsManagementService
        from .internal.aws.aws_dns_value_resolver_service import AwsDnsValueResolverService

        di_container.register(DnsManagementInterface, AwsDnsManagementService, lifetime="scoped")
        di_container.register(DnsValueResolverInterface, AwsDnsValueResolverService, lifetime="scoped")
