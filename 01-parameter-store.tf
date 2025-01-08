module "secret" {
  source  = "terraform-aws-modules/ssm-parameter/aws"
  version = "1.1.2"

  name                 = var.parameter-name
  value                = var.slack-webhook-url
  secure_type          = true
  ignore_value_changes = true
}