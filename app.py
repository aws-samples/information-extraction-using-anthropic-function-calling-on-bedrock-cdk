#!/usr/bin/env python3
import json
import cdk_nag
from aws_cdk import Aspects
import aws_cdk as cdk
import os
from information_extraction_using_anthropic_function_calling_on_bedrock_cdk.information_extraction_using_anthropic_function_calling_on_bedrock_cdk_stack import InformationExtractionUsingAnthropicFunctionCallingOnBedrockCdkStack

with open('project_config.json', 'r') as file:
    variables = json.load(file)

app = cdk.App()
InformationExtractionUsingAnthropicFunctionCallingOnBedrockCdkStack(app, variables["MainStackName"],)

Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(reports=True, verbose=True))

app.synth()
