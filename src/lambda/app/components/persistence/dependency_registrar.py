from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RuntimeContext
from app.utils.di import DIContainer

from .repository_service_interface import RepositoryInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers DNS services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    # Resolve the concrete implementation of the repository based on the config
    db_provider = env_config_service.db_config.provider
    if RuntimeContext.is_aws:
        if db_provider == "dynamodb":
            from .internal.aws.aws_dynamodb_repository_service import AwsDynamoDBRepository

            di_container.register(RepositoryInterface, AwsDynamoDBRepository, lifetime="scoped")
