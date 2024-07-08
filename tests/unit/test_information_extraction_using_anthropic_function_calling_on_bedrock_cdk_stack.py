import aws_cdk as core
import aws_cdk.assertions as assertions

from information_extraction_using_anthropic_function_calling_on_bedrock_cdk.information_extraction_using_anthropic_function_calling_on_bedrock_cdk_stack import InformationExtractionUsingAnthropicFunctionCallingOnBedrockCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in information_extraction_using_anthropic_function_calling_on_bedrock_cdk/information_extraction_using_anthropic_function_calling_on_bedrock_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = InformationExtractionUsingAnthropicFunctionCallingOnBedrockCdkStack(app, "information-extraction-using-anthropic-function-calling-on-bedrock-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
