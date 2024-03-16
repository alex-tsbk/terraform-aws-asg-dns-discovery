from typing import List

from app.components.dns.internal.dns_value_resolver_base_service import DnsValueResolverService
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition
from app.config.models.dns_record_config import DnsRecordConfig
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration


class MockDnsValueResolverService(DnsValueResolverService):
    def handle_ip_source(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        ip_type: str,
    ) -> List[str]:
        return ["192.168.0.1", "192.168.0.2"]

    def handle_tag_source(
        self,
        sg_config_item: ScalingGroupConfiguration,
        lifecycle_event: LifecycleEventModel,
        tag_name: str,
    ) -> List[str]:
        return ["example.com"]


def test_resolve_dns_value_with_ip_source():
    resolver = MockDnsValueResolverService()
    sg_config_item = ScalingGroupConfiguration(
        value_source="ip:public",
        scaling_group_name="test-sg",
        dns_config=DnsRecordConfig(record_type="A", record_ttl=60),
    )
    lifecycle_event = LifecycleEventModel(
        transition=LifecycleTransition.LAUNCHING,
        lifecycle_hook_name="test-hook",
        scaling_group_name="test-sg",
        instance_id="i-12345",
    )
    result = resolver.resolve_dns_value(sg_config_item, lifecycle_event)
    assert result == ["192.168.0.1", "192.168.0.2"]


def test_resolve_dns_value_with_tag_source():
    resolver = MockDnsValueResolverService()
    sg_config_item = ScalingGroupConfiguration(
        value_source="tag:example_tag",
        scaling_group_name="test-sg",
        dns_config=DnsRecordConfig(record_type="A", record_ttl=60),
    )
    lifecycle_event = LifecycleEventModel(
        transition=LifecycleTransition.LAUNCHING,
        lifecycle_hook_name="test-hook",
        scaling_group_name="test-sg",
        instance_id="i-12345",
    )
    result = resolver.resolve_dns_value(sg_config_item, lifecycle_event)
    assert result == ["example.com"]


def test_resolve_dns_value_with_unknown_source():
    resolver = MockDnsValueResolverService()
    sg_config_item = ScalingGroupConfiguration(
        value_source="unknown_source",
        scaling_group_name="test-sg",
        dns_config=DnsRecordConfig(record_type="A", record_ttl=60),
    )
    lifecycle_event = LifecycleEventModel(
        transition=LifecycleTransition.LAUNCHING,
        lifecycle_hook_name="test-hook",
        scaling_group_name="test-sg",
        instance_id="i-12345",
    )
    result = resolver.resolve_dns_value(sg_config_item, lifecycle_event)
    assert result is None
