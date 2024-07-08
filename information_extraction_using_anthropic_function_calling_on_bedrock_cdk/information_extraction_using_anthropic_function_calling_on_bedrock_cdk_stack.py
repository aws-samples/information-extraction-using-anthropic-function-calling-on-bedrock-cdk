from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    Duration,
    aws_lambda as _lambda,
    aws_s3_deployment as s3_deployment,
    aws_stepfunctions as stepfunctions,
    aws_stepfunctions_tasks as stepfunctions_tasks,
    aws_lambda_event_sources,
    aws_s3 as s3,
    aws_logs as logs,
    RemovalPolicy,
    aws_s3_notifications,
    aws_lambda_python_alpha as _alambda,
)
from cdk_nag import NagSuppressions
from constructs import Construct

class InformationExtractionUsingAnthropicFunctionCallingOnBedrockCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## S3 bucket for access logs
        access_logs_bucket = s3.Bucket(
            self,
            "AccessLogsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            auto_delete_objects=True,
        )

        gov_id_extractor_bucket_s3  = s3.Bucket(
            self,
            "GovIdExtractorBucket",
            removal_policy= RemovalPolicy.DESTROY,
            block_public_access= s3.BlockPublicAccess.BLOCK_ALL,
            encryption= s3.BucketEncryption.S3_MANAGED,
            server_access_logs_bucket=access_logs_bucket,
            enforce_ssl=True,
            auto_delete_objects=True,
        )

        ## copy the files from dataset folder into input_bucket_s3 bucket
        s3_deployment.BucketDeployment(
            self,
            "DeployFiles",
            sources=[s3_deployment.Source.asset("./sample_dataset/")],
            destination_bucket=gov_id_extractor_bucket_s3,
            destination_key_prefix="upload_files/",  # Prefix for the files in the bucket
        )

        ############### Lambda Layers ###############
        boto3_layer = _alambda.PythonLayerVersion(self, 'boto3-layer',
            entry = './lambda/lambda_layer/boto3_layer/',
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
        )

        pypdfium2_layer = _alambda.PythonLayerVersion(self, 'pypdfium2-layer',
            entry = './lambda/lambda_layer/pypdfium2_layer/',
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
        )

        pydantic_layer = _alambda.PythonLayerVersion(self, 'pydantic-layer',
            entry = './lambda/lambda_layer/pydantic_layer/',
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
        )

        ########################### Lambdas ###########################
        ############### file_processor ###############
        file_processor_lambda = _lambda.Function(self,
                                "file_processor_lambda",
                                code=_lambda.Code.from_asset("./lambda/file_processor"),
                                runtime=_lambda.Runtime.PYTHON_3_12,
                                architecture=_lambda.Architecture.ARM_64,
                                memory_size=256,
                                timeout=Duration.minutes(2),
                                handler="index.lambda_handler",
                                layers=[pypdfium2_layer],
                            )
        gov_id_extractor_bucket_s3.grant_read_write(file_processor_lambda)

        ############### Field EXTRACTOR ###############
        field_extractor_lambda = _lambda.Function(self, 
                                "field_extractor_lambda",
                                code=_lambda.Code.from_asset("./lambda/field_extractor"),
                                runtime=_lambda.Runtime.PYTHON_3_12,
                                architecture=_lambda.Architecture.ARM_64,
                                memory_size=256,
                                timeout=Duration.minutes(2),
                                handler="index.lambda_handler",
                                layers=[boto3_layer, pydantic_layer],
                            )
        gov_id_extractor_bucket_s3.grant_read_write(field_extractor_lambda)
        haiku_sonnet_bedrock_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel"],
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-haiku*:0",
                       f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet*:0"]
        )
        field_extractor_lambda.add_to_role_policy(haiku_sonnet_bedrock_policy_statement)

        ########################### CloudWatch Log Group ###########################
        log_group = logs.LogGroup(self, "StateMachineLogGroup",
                                  removal_policy= RemovalPolicy.DESTROY,  # Adjust this according to your needs
                                  retention=logs.RetentionDays.ONE_DAY)
        
        ########################### Step Function ###########################
        file_processing_step = stepfunctions_tasks.LambdaInvoke(self, "InvokeFileProcessorLambda",
                                                   lambda_function=file_processor_lambda,
                                                   payload_response_only=True)
        field_extraction_step = stepfunctions_tasks.LambdaInvoke(self, "InvokeFieldExtractorLambda",
                                                    lambda_function=field_extractor_lambda,
                                                    payload_response_only=True)

        # definition = stepfunctions_tasks.Chain.start(file_processing_step).next(field_extraction_step)
        definition = file_processing_step.next(field_extraction_step)

        state_machine = stepfunctions.StateMachine(self, "StateMachine",
                                                    definition= definition,
                                                    timeout=Duration.minutes(5),
                                                    logs=stepfunctions.LogOptions(
                                                        destination=log_group,
                                                        level=stepfunctions.LogLevel.ALL  # Log all events
                                                    ),
                                                    tracing_enabled=True  # Enable X-Ray tracing
                                                    )

        # Grant Step Function permissions to invoke Lambda functions
        file_processor_lambda.grant_invoke(state_machine.role)
        field_extractor_lambda.grant_invoke(state_machine.role)

        ############### state_machine_trigger Lambda ##########
        state_machine_trigger_lambda = _lambda.Function(self, 
                                "state_machine_trigger_lambda",
                                code=_lambda.Code.from_asset("./lambda/state_machine_trigger"),
                                runtime=_lambda.Runtime.PYTHON_3_12,
                                architecture=_lambda.Architecture.ARM_64,
                                memory_size=256,
                                timeout=Duration.minutes(2),
                                handler="index.lambda_handler",
                                environment={
                                    "STATE_MACHINE_ARN": state_machine.state_machine_arn
                                }
                            )
        state_machine.grant_start_execution(state_machine_trigger_lambda)
        gov_id_extractor_bucket_s3.grant_read(state_machine_trigger_lambda)

        # Link S3 bucket notification with Step Function
        gov_id_extractor_bucket_s3.add_event_notification(
                s3.EventType.OBJECT_CREATED,
                aws_s3_notifications.LambdaDestination(state_machine_trigger_lambda),
                s3.NotificationKeyFilter(
                    prefix="upload_files/",
                    suffix=".jpeg",
                ),
            )

        gov_id_extractor_bucket_s3.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.LambdaDestination(state_machine_trigger_lambda),
            s3.NotificationKeyFilter(
                prefix="upload_files/",
                suffix=".pdf",
            ),
        )

        ## CDK NAG suppression
        NagSuppressions.add_stack_suppressions(self, [
                                            {
                                                "id": 'AwsSolutions-IAM4',
                                                "reason": 'Lambda execution policy for custom resources created by higher level CDK constructs',
                                                "appliesTo": [
                                                        'Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                                                    ],
                                            }])

         ## CDK NAG suppression
        NagSuppressions.add_resource_suppressions_by_path(            
            self,
            path="/FunctionCallingStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/Resource",
            suppressions = [
                            { "id": 'AwsSolutions-L1', "reason": 'CDK BucketDeployment L1 Construct' },
                            { "id": 'AwsSolutions-IAM5', "reason": 'CDK BucketDeployment L1 Construct' },
                        ],
            apply_to_children=True
        )

        # CDK Nag Suppression
        NagSuppressions.add_resource_suppressions([state_machine.role, state_machine_trigger_lambda.role, file_processor_lambda.role, field_extractor_lambda.role],
                            suppressions=[{
                                                "id": "AwsSolutions-IAM4",
                                                "reason": "This code is for demo purposes. So granted full access to AWS service.",
                                            },
                                            {
                                                "id": "AwsSolutions-IAM5",
                                                "reason": "This code is for demo purposes. So granted access to all indices of S3 bucket.",
                                            }
                                        ],
                            apply_to_children=True)
        
        # CDK Nag Suppression
        NagSuppressions.add_resource_suppressions_by_path(            
            self,
            path="/FunctionCallingStack/BucketNotificationsHandler050a0587b7544547bf325f094a3db834/Role/DefaultPolicy/Resource",
            suppressions = [
                            { "id": 'AwsSolutions-IAM5', "reason": 'CDK BucketNotificationsHandler L1 Construct' },
                        ],
            apply_to_children=True
        )