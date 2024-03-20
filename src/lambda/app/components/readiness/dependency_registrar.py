from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RuntimeContext
from app.utils.di import DIContainer

from .readiness_interface import ReadinessInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    if RuntimeContext.is_aws:
        from .internal.aws.aws_readiness_service import AwsReadinessService

        di_container.register(ReadinessInterface, AwsReadinessService, lifetime="scoped")
