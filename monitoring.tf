resource "aws_iam_policy" "cloudwatch_custom_metrics" {
  count = var.monitoring.cloudwatch_metrics_enabled ? 1 : 0
  name  = "${local.resource_prefix}-push-custom-metrics"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "cloudwatch:PutMetricData",
      "Effect": "Allow",
      "Resource": "*",
      "Condition": {
          "StringEquals": {
            "cloudwatch:namespace": "${var.monitoring.cloudwatch_metrics_namespace}"
          }
      }
    }
  ]
}
EOF
}

# Lambda(s)
resource "aws_iam_role_policy_attachment" "cloudwatch_custom_metrics" {
  count = var.monitoring.cloudwatch_metrics_enabled ? 1 : 0

  role       = aws_iam_role.dns_discovery_lambda.id
  policy_arn = aws_iam_policy.cloudwatch_custom_metrics[count.index].arn
}
