from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .dns_management_interface import DnsManagementInterface
from .dns_value_resolver_interface import DnsValueResolverInterface
from .internal.cloudflare.cloudflare_dns_management_service import CloudflareDnsManagementService


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    di_container.register(DnsManagementInterface, CloudflareDnsManagementService, name="cloudflare", lifetime="scoped")

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_dns_management_service import AwsDnsManagementService
        from .internal.aws.aws_dns_value_resolver_service import AwsDnsValueResolverService

        di_container.register(DnsManagementInterface, AwsDnsManagementService, name="route53", lifetime="scoped")
        di_container.register(DnsValueResolverInterface, AwsDnsValueResolverService, lifetime="scoped")
