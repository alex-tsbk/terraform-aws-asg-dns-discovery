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

    # List of valid states for the scaling group. Default is ['InService']
    # More on states here: https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-lifecycle.html
    scaling_group_valid_states = optional(list(string), ["InService"])

    # MULTIVALUE or SINGLE. 'MULTIVALUE' is default.
    # 'MULTIVALUE' - single DNS having multiple IPs:
    #   subdomain.example.com -> 12.82.13.83, 12.82.13.84, 12.82.14.80
    # 'SINGLE' is DNS updated with latest IP of instance launched
    #   subdomain.example.com -> 12.82.13.83
    mode = optional(string, "MULTIVALUE")

    # ###
    # DNS SETTINGS
    # ###

    dns_config = object({
      # Name of DNS provider. Supported values: 'route53', 'cloudflare'. Default: 'route53'
      provider = optional(string, "route53")
      # Value to use as the source for the DNS record. 'ip:private' is default.
      # Supported values:
      # * 'ip:public' - will use public IP of the instance
      # * 'ip:private' - will use private IP of the instance
      # * 'tag:<tag_name>' - where <tag_name> is the name of the tag to use as the source for the DNS record value.
      # IMPORTANT:
      # * If you're using private IPs, resolver function must be on the same network as VM.
      #   For AWS this means lambda being deployed to the same VPC as the ASG(s) it's runnign check against.
      value_source = optional(string, "ip:private")
      # For AWS - Hosted zone ID of the domain.
      # You can find this in Route53 console.
      dns_zone_id = string
      # Name of the DNS record. If your domain is 'example.com', and you want to
      # create a DNS record for 'subdomain.example.com', then the value of this field
      # should be 'subdomain'
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
      #
      # It is strongly recommended to keep this setting set to 'false', unless you really understand the implications.
      #
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
      #   1) You manage DNS records in Terraform, therefore - you have access to resources via Terraform state.
      #
      # Reconciliation (see below):
      #   When deploying this alongside ASG, to address the limitation of the first EC2s not having a DNS record,
      #   it is suggested to enable reconciliation. Even if you have 'managed_dns_record' set to false,
      #   reconciliation will add EC2s on the first reconciliation run. This should satisfy vast majority of use-cases.
      managed_dns_record = optional(bool, false)

      # Default 'mock' value.
      # Address is used when ASG is created, but no EC2s are yet running matching readiness criteria,
      # yet we still need to have IP address in DNS record associated (record can't be created without value).
      # Once the first lifecycle is triggered, this value will be replaced with the actual value resolved from the EC2 (IP typically).
      dns_mock_value = optional(string, "1.0.0.217")
    })

    # ###
    # READINESS
    # ###

    # Scaling Group specific readiness check. If set, will override global readiness check.
    # This is handy when you have different readiness criteria for different ASGs,
    # or you want to disable readiness check for specific ASG, while having it enabled globally.
    readiness = optional(object({
      # If true, the readiness check will be enabled. Enabled by default.
      enabled = optional(bool, true)
      # Tag key to look for
      tag_key = string
      # Tag value to look for
      tag_value = string
      # Timeout in seconds. If the tag is not set within this time, the lambda will fail.
      timeout_seconds = optional(number, 300)
      # Interval in seconds to check for the tag. Default is 5 seconds.
      interval_seconds = optional(number, 5)
    }), null)

    # ###
    # HEALTHCHECK
    # ###

    # Health check to perform before adding instance to DNS record.
    # Set to null to disable healthcheck overall.
    health_check = optional(object({
      enabled = optional(bool, true)
      # Value to use as the source for the health check. If not provided, then the value from `dns_config.value_source` will be used.
      # Supported values:
      # * 'ip:public' - will use public IP of the instance
      # * 'ip:private' - will use private IP of the instance
      # * 'tag:<tag_name>' - where <tag_name> is the name of the tag to use as the source for the DNS record value.
      # IMPORTANT:
      # * Ensure that the health check source is accessible from the resolver function (for AWS - from Lambda).
      endpoint_source = optional(string, "ip:private")
      path            = optional(string, "")
      port            = number
      protocol        = string
      timeout_seconds = number
    }), null)
  }))

  default = []
}

# Please note, it's responsibility of your application to set the tag on the instance
# to the value specified here once instance is fully bootstrapped with your application/custom scripts.
variable "instance_readiness" {
  description = "Default global configuration for readiness check. DNS discovery will not proceed until tagging criteria are met."

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
    tag_key   = "app:readiness:status"
    tag_value = "ready"
  }
}

variable "reconciliation" {
  description = "Configuration for reconciliation of DNS records that are enabled for Service Discovery."

  type = object({
    # ###
    # RUNTIME BEHAVIOR
    # ###

    # "What If" mode. When `true`, the reconciliation will only log what it would do, but not actually do it.
    # It is recommended that you run application in this mode first to see what would happen,
    # and ensure changes created are as what expected.
    what_if = optional(bool, false)
    # Maximum number of concurrent reconciliations. Default is 1.
    # Please note, depending on your ASG sizes and their count, you may want to adjust this number.
    # Math here is simple - the less EC2s you have, the more this **can** go (less resources - less boto3 throttling).
    # Setting this to more than number of ASGs being managed will not yield any boost.
    max_concurrency = optional(number, 1)

    # ###
    # INFRASTRUCTURE SETTINGS
    # ###

    # When set to `true` will enable running reconciliation on schedule.
    # When set to `false`, will still create event bridge rule to run the lambda on a schedule,
    # but in 'disabled' state. Default is `false`.
    schedule_enabled = optional(bool, false)
    # Interval in minutes between reconciliation runs. Default is 5 minutes.
    schedule_interval_minutes = optional(number, 5)
  })

  default = {
    what_if                   = false
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
