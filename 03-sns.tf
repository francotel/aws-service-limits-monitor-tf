module "sns-topic" {
  source  = "terraform-aws-modules/sns/aws"
  version = "6.1.2"

  name = "monitoring-sns-email-${var.project}"

  subscriptions = {
    for email in var.email-alert : email => {
      protocol = "email"
      endpoint = email
    }
  }
}
