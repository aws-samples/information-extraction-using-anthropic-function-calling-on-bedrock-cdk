import os
import json
import boto3

stepfunctions_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    print(event)
    state_machine_arn = os.environ['STATE_MACHINE_ARN']

    for record in event['Records']:
        s3_event = record['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']

        # Start the state machine execution
        stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps({
                "bucket": bucket_name,
                "key": object_key
            })
        )

    return {
        'statusCode': 200,
        'body': json.dumps('State Machine triggered successfully.')
    }