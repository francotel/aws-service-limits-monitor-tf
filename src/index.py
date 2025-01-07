import boto3
import json
import os
import urllib.request

# Lambda handler function
def lambda_handler(event, context):
    try:
        print("Init lambda process...")

        # Read the parameter name from environment variables
        parameter_name = os.environ['SLACK_WEBHOOK_PARAM_NAME']
        sns_topic_arn = os.environ['SNS_TOPIC_ARN']

        # Get the parameter value from AWS SSM Parameter Store
        ssm_client = boto3.client('ssm')
        parameter = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        slack_webhook_url = parameter['Parameter']['Value']

        print("Retrieving Trusted Advisor Checks...")
        support_client = boto3.client('support', region_name='us-east-1')
        response = support_client.describe_trusted_advisor_checks(language='en')

        checks = []
        ta_checks_dict = {}
        # Store each Trusted Advisor check ID and its associated metadata
        for check in response["checks"]:
            checks.append(check["id"])
            ta_checks_dict[check["id"]] = {
                "name": check["name"],
                "category": check["category"]
            }

        # Get the summary of the Trusted Advisor Checks
        result = support_client.describe_trusted_advisor_check_summaries(checkIds=checks)

        # Initialize counters for different check statuses
        count_ok = 0
        count_warn = 0
        count_critical = 0
        message = ""
        summary = ""

        # Iterate through the check summaries to categorize them by status
        for check_summary in result['summaries']:
            check_status = check_summary['status']
            check_id = check_summary['checkId']

            if check_status == 'ok':
                count_ok += 1
            elif check_status == 'warning':
                count_warn += 1
            elif check_status == 'error':
                count_critical += 1
                # Add high-risk checks to the detailed message
                message += f"❗ *HIGH RISK* - [{ta_checks_dict[check_id]['category']}] {ta_checks_dict[check_id]['name']}\n"
            else:
                continue

        # Create the summary in Markdown format for Slack
        summary += "\n*========= Summary of Trusted Advisor Findings =========*\n"
        summary += f"🟢 *GREEN - OK:* {count_ok}\n"
        summary += f"🟡 *YELLOW (Investigate):* {count_warn}\n"
        summary += f"🔴 *RED (High Risk):* {count_critical}\n\n"

        # Combine the summary and detailed messages
        slack_message = summary + message
        slack_message += "\nFor more details, visit the [Trusted Advisor Console](https://console.aws.amazon.com/trustedadvisor/home)."

        # Send the message to Slack
        print("Sending message to Slack...")
        headers = {
            'Content-Type': 'application/json'
        }
        data = json.dumps({"text": slack_message}).encode('utf-8')

        request = urllib.request.Request(slack_webhook_url, data=data, headers=headers)
        response = urllib.request.urlopen(request)

        # Publish the message to SNS
        sns_client = boto3.client('sns')
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject='Trusted Advisor Summary',
            Message=slack_message
        )

        print("Message sent successfully to Slack.")
        return {
            'statusCode': 200,
            'body': json.dumps('Message sent to Slack')
        }

    except Exception as e:
        # Handle any errors that occur during execution
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }