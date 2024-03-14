
# data.aws_caller_identity.current.account_id (123456789012)
data "aws_caller_identity" "current" {}

# data.aws_region.current.name (us-west-2)
data "aws_region" "current" {}

# data.aws_partition.current.dns_suffix (amazonaws.com vs amazonaws.com.cn)
# data.aws_partition.current.partition (aws vs aws-cn)
data "aws_partition" "current" {}
