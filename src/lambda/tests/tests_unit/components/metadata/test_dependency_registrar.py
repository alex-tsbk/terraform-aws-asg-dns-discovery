from unittest.mock import MagicMock

from app.components.metadata.dependency_registrar import register_services
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.internal.aws.aws_ec2_metadata_service import AwsEc2MetadataService


def test_register_services_when_running_on_aws(aws_runtime):
    di_container = MagicMock()

    register_services(di_container, MagicMock())

    di_container.register.assert_any_call(InstanceMetadataInterface, AwsEc2MetadataService, lifetime="scoped")
