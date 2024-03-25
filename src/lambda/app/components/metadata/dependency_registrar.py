from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .instance_metadata_interface import InstanceMetadataInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_ec2_metadata_service import AwsEc2MetadataService

        di_container.register(InstanceMetadataInterface, AwsEc2MetadataService, lifetime="scoped")
