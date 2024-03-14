locals {
  asg_hooks_with_managed_ip_dns = {
    for record in var.records :
    "${record.scaling_group_name}-${record.dns_config.dns_zone_id}-${record.dns_config.record_name}-${record.dns_config.record_type}" =>
    record if record.dns_config.managed_dns_record && startswith(record.dns_config.value_source, "ip:")
  }
}

data "aws_instances" "asg_ec2_instances" {
  for_each = local.asg_hooks_with_managed_ip_dns

  instance_state_names = ["running"]

  filter {
    name   = "tag:${local.aws_partition}:autoscaling:groupName"
    values = [each.value.scaling_group_name]
  }

  dynamic "filter" {
    for_each = var.ec2_readiness.enabled ? [1] : []
    content {
      name   = "tag:${var.ec2_readiness.tag_key}"
      values = [var.ec2_readiness.tag_value]
    }
  }
}

resource "aws_route53_record" "asg_dns_discovery_ips" {
  for_each = local.asg_hooks_with_managed_ip_dns

  zone_id = each.value.dns_config.dns_zone_id
  name    = each.value.dns_config.record_name
  type    = each.value.dns_config.record_type
  ttl     = each.value.dns_config.record_ttl

  records = length(each.value.dns_config.value_source == "ip:public" ? data.aws_instances.asg_ec2_instances[each.key].public_ips : data.aws_instances.asg_ec2_instances[each.key].private_ips) > 0 ? each.value.dns_config.value_source == "ip:public" ? data.aws_instances.asg_ec2_instances[each.key].public_ips : data.aws_instances.asg_ec2_instances[each.key].private_ips : [each.value.dns_mock_ip]
}
