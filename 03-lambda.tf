data "archive_file" "zip-python-code" {
  type        = "zip"
  source_dir  = "./src/"
  output_path = "./src/python.zip"
}

module "lambda-function-service-limits" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "lambda-${var.project}"
  description   = "Lambda function code is deployed separately"
  handler       = "index.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 128
  timeout       = 15

  environment_variables = {
    SLACK_WEBHOOK_PARAM_NAME = module.secret.ssm_parameter_name
    SNS_TOPIC_ARN            = module.sns-topic.topic_arn
  }

  create_package         = false
  local_existing_package = "./src/python.zip"

  ignore_source_code_hash                 = false
  create_current_version_allowed_triggers = false

  cloudwatch_logs_retention_in_days = 30
  cloudwatch_logs_log_group_class   = "INFREQUENT_ACCESS"
  cloudwatch_logs_skip_destroy      = false

  allowed_triggers = {
    cron = {
      principal  = "events.amazonaws.com"
      source_arn = module.eventbridge-cron.eventbridge_rules.crons.arn
    }
  }

  attach_policy_statements = true
  policy_statements = {
    trustedadvisor = {
      effect = "Allow",
      actions = [
        "support:DescribeTrustedAdvisorCheckRefreshStatuses",
        "support:DescribeTrustedAdvisorCheckResult",
        "support:DescribeTrustedAdvisorCheckSummaries",
        "support:DescribeTrustedAdvisorChecks"
      ],
      resources = ["*"]
    },
    parameterstore = {
      effect = "Allow",
      actions = [
        "ssm:GetParameter"
      ],
      resources = [module.secret.ssm_parameter_arn]
    },
    snspublish = {
      effect = "Allow",
      actions = [
        "sns:Publish"
      ],
      resources = [module.sns-topic.topic_arn]
    }
  }
}