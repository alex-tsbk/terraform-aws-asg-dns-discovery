variable "environment" {
  description = "Name of the integration environment. Example: dev, stage, prod, etc."
  type        = string
}

variable "resource_suffix" {
  description = "Value to be appended to the resource names."
  type        = string
  default     = "asg-dns-discovery"
}

variable "tags" {
  description = "Additional tags to be applied to all resources created by this module."
  type        = map(string)
  default = {
  }
}

variable "records" {
  description = "List of configuration objects describing how exactly Scaling Group instances should be translated to DNS."
  type = list(object({
    # ###
    # GENERAL SETTINGS
    # ###

    # Name of the Scaling Group that is the target of the DNS Discovery
    scaling_group_name = string

    # Value to use as the source for the DNS record. 'ip:private' is default.
    # Supported values:
    # * 'ip:public' - will use public IP of the instance
    # * 'ip:private' - will use private IP of the instance
    # * 'tag:<tag_name>' - where <tag_name> is the name of the tag to use as the source for the DNS record value.
    # IMPORTANT: If you're using private IPs, your lambda function must be in the same VPC as the ASG(s).
    value_source = optional(string, "ip:private")

    # MULTIVALUE or SINGLE. 'MULTIVALUE' is default.
    # 'MULTIVALUE' - single DNS having multiple IPs:
    #   beast.example.com -> 12.82.13.83, 12.82.13.84, 12.82.14.80
    # 'SINGLE' is DNS updated with latest IP of instance launched
    #   beast.example.com -> 12.82.13.83
    mode = optional(string, "MULTIVALUE")

    # ###
    # DNS SETTINGS
    # ###

    dns_config = object({
      # Name of DNS provider. Supported values: 'route53', 'cloudflare'. Default: 'route53'
      provider = optional(string, "route53")
      # For AWS - Hosted zone ID of the domain. 
      # You can find this in Route53 console.
      dns_zone_id = string
      # Name of the DNS record. If your domain is 'example.com', and you want to
      # create a DNS record for 'beast.example.com', then the value of this field
      # should be 'beast'
      record_name = string
      # Time to live for DNS record
      record_ttl = optional(number, 60)
      # Type of DNS record. Default is 'A'
      record_type = optional(string, "A")
      # Priority of the DNS record. Default is 0
      record_priority = optional(number, 0)
      # Weight of the DNS record. Default is 0
      record_weight = optional(number, 0)

      # If true, DNS record will be created and managed by Terraform. This has it's own pros and cons.
      # Cons:
      #   1) If you have existing Route53 record and EC2s registered in it, keep this setting set to false.
      #      Otherwise, terraform will fail to create the record because it already exists.
      #   2) This will vendor-lock your DNS records to Terraform. If you decide to move away from using this module,
      #      you will have to alter terraform state and remove managed Route53 resources.
      #   3) Because module depends on ASG resource being created first, in case when you're deploying ASG and this module together,
      #      system will not create a DNS record entry for the very first EC2 launched,
      #      because event for first instance launch 'would have been fired' before EC2 module provisioned SNS topic and ASG lifecycle hook.
      #
      # Pros:
      #   1) You manage DNS records in Terraform, therefore you have access to resources in Terraform state.
      #
      # Reconciliation (see below):
      #   To address the issue of the first EC2 not having a DNS record, you can enable reconciliation.
      #   Even if you have 'managed_dns_record' set to false, reconciliation will add EC2 on the first reconciliation run.
      managed_dns_record = optional(bool, false)

      # Default 'mock' IP address.
      # Address is used when ASG is created, but no EC2s are yet running matching readiness criteria,
      # yet we still need to have IP address in DNS record associated (record can't be created without value).
      # Once the first lifecycle is triggered, this value will be replaced with the actual IP of the EC2.
      dns_mock_ip = optional(string, "1.0.0.217")
    })

    # ###
    # HEALTHCHECK
    # ###

    # Health check to perform before adding EC2 instance to DNS record. 
    # Set to null to disable healthcheck overall.
    health_check = optional(object({
      enabled         = bool
      path            = optional(string, "")
      port            = number
      protocol        = string
      timeout_seconds = number
    }), null)
  }))

  default = []
}

# Please note, it's responsibility of your application to set the tag on the EC2 instance
# to the value specified here once EC2 is fully bootstrapped with your application.
variable "instance_readiness" {
  description = "Configuration for readiness check. DNS discovery will not proceed until tagging criteria are met."

  type = object({
    # If true, the readiness check will be enabled. Disabled by default.
    enabled = optional(bool, false)
    # Tag key to look for
    tag_key = string
    # Tag value to look for
    tag_value = string
    # Timeout in seconds. If the tag is not set within this time, the lambda will fail.
    timeout_seconds = optional(number, 300)
    # Interval in seconds to check for the tag. Default is 5 seconds.
    interval_seconds = optional(number, 5)
  })

  default = {
    enabled   = true
    tag_key   = "app:code-deploy:status"
    tag_value = "success"
  }
}

variable "reconciliation" {
  description = "Configuration for reconciliation of DNS records that are enabled for Service Discovery."

  type = object({
    # Whatif mode. If true, the reconciliation will only log what it would do, but not actually do it.
    whatif = optional(bool, false)
    # When set to false, will still create event bridge rule to run the lambda on a schedule,
    # but in 'disabled' state.
    schedule_enabled = optional(bool, false)
    # Interval in minutes between reconciliation runs. Default is 5 minutes.
    schedule_interval_minutes = optional(number, 5)
    # Maximum number of concurrent reconciliations. Default is 1.
    # Please note, depending on your ASG sizes and their count, you may want to adjust this number.
    # Math here is simple - the less EC2s you have, the more this **can** go (less resources - less boto3 throttling).
    # Setting this to more than number of ASGs being managed will not yield any boost.
    max_concurrency = optional(number, 1)
  })

  default = {
    whatif                    = false
    schedule_enabled          = false
    schedule_interval_minutes = 5
    max_concurrency           = 1
  }
}

variable "monitoring" {
  description = "Configures monitoring for the Scaling Group DNS discovery."

  type = object({
    # When set to true - enables metrics for the DNS discovery.
    metrics_enabled = optional(bool, false)
    # Metrics provider
    metrics_provider = optional(string, "cloudwatch")
    # Metrics namespace
    metrics_namespace = string
    # When set to true - enables sending alarms to specified destination. Default is false.
    alarms_enabled = optional(bool, false)
    # SNS topic ARN to send alarms to.
    alarms_notification_destination = string
  })

}

# ###
# AWS Specific settings
# ###

variable "lambda_settings" {
  description = "Lambda configuration."

  type = object({
    # Runtime version
    python_runtime = optional(string, "python3.12")
    # Timeout for the lambda function. Default is 15 minutes.
    lifecycle_timeout_seconds = optional(number, 15 * 60)
    # Subnets where the lambda will be deployed. 
    # Must be set if the lambda needs to access resources in the VPC - health checks on private IPs.
    subnets         = optional(list(string), [])
    security_groups = optional(list(string), [])
    # Log settings for the lambda runtime
    log_identifier        = optional(string, "asg-dns-discovery")
    log_level             = optional(string, "INFO")
    log_retention_in_days = optional(number, 90)
  })

  default = {
    python_runtime        = "python3.12"
    timeout_seconds       = 15 * 60
    subnets               = []
    security_groups       = []
    log_identifier        = "asg-dns-discovery"
    log_level             = "INFO"
    log_retention_in_days = 90
  }
}
