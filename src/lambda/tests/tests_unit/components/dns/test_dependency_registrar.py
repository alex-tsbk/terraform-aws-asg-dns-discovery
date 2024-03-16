from unittest.mock import MagicMock

from app.components.dns.dependency_registrar import register_services
from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.dns_value_resolver_interface import DnsValueResolverInterface
from app.components.dns.internal.aws.aws_dns_management_service import AwsDnsManagementService
from app.components.dns.internal.aws.aws_dns_value_resolver_service import AwsDnsValueResolverService


def test_register_services_when_running_on_aws(aws_runtime):
    di_container = MagicMock()

    register_services(di_container)

    di_container.register.assert_any_call(DnsManagementInterface, AwsDnsManagementService, lifetime="scoped")
    di_container.register.assert_any_call(DnsValueResolverInterface, AwsDnsValueResolverService, lifetime="scoped")
