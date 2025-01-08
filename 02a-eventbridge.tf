module "eventbridge-cron" {
  source = "terraform-aws-modules/eventbridge/aws"

  create_bus     = false
  create_targets = true

  rules = {
    crons = {
      description         = "Trigger for a Lambda"
      schedule_expression = var.schedule-expression
    }
  }

  targets = {
    crons = [
      {
        name  = "lambda-cron"
        arn   = module.lambda-function-service-limits.lambda_function_arn
        input = jsonencode({ "job" : "crons" })
      }
    ]
  }

  tags = {
    Name = "eventbridge-rule-cron-${var.project}"
  }
}