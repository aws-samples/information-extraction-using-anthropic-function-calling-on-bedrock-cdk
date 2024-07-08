import boto3
from pydantic_utils import convert_pydantic_to_bedrock_converse_function
import json

s3_client=boto3.client("s3")
bedrock_runtime_client = boto3.client('bedrock-runtime')


# def get_jpeg_files_uri(bucket_name, target_path):
#     s3_uri_list = []
#     paginator = s3_client.get_paginator('list_objects_v2')
#     page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=target_path)

#     for page in page_iterator:
#         for obj in page.get('Contents', []):
#             if obj['Key'].endswith('.jpeg'):
#                 s3_uri = f"s3://{bucket_name}/{obj['Key']}"
#                 s3_uri_list.append(s3_uri)

#     print(s3_uri_list)
#     return s3_uri_list

def get_image_bytes(s3_path):
    s3_parts = s3_path.replace("s3://", "").split("/")
    bucket_name = s3_parts[0]
    key = "/".join(s3_parts[1:])

    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    image_bytes = response['Body'].read()
    return image_bytes
    

def invoke_bedrock_anthropic_model(jpeg_files_list, pydantic_classes):
    # model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    system_prompt =f"""Act as expert to extract and analyze information \
from various types of identity documents such as passports, driver's licenses, \
national ID cards, and other government-issued identification."""
    content_list=[]
    for jpeg_s3_uri in jpeg_files_list:
        img_bytes = get_image_bytes(jpeg_s3_uri)
        dict_ = {
                     "image":{
                        "format":"jpeg",
                         "source": {'bytes': img_bytes}
                     }
                  }
        content_list.append(dict_)

    messages=[{"role":"user",
               "content":content_list
               }]

    tools = []
    for class_ in pydantic_classes:
        tools.append(convert_pydantic_to_bedrock_converse_function(class_))
    tool_config = { "tools": tools }
    
        
    response = bedrock_runtime_client.converse(
            system=[{ "text": system_prompt}],
            modelId=model_id,
            messages=messages,
            toolConfig=tool_config
        )
    return response 


def parse_bedrock_response(response):
    udf_value_dict_ = {}
    tool_name = ""

    stop_reason = response['stopReason']
    tool_requests = response['output']['message']['content']

    if stop_reason == 'tool_use':
        for tool_request in tool_requests:
            if 'toolUse' in tool_request:
                print("Claude used a tool")
                tool_name = tool_request['toolUse']["name"]
                tool_input = tool_request['toolUse']["input"]
                udf_value_dict_[tool_name] = tool_input
        if len(tool_requests)==1:
            print("Claude didn't use any tools")
    return udf_value_dict_


## write a function to write json file into s3 bucket
def write_json_to_s3(udf_value_dict_, s3_bucket, result_json_folder):
    for key, value in udf_value_dict_.items():
        file_name = f"{key}.json"
        json_data=value
        s3_key = f"{result_json_folder}/{file_name}"
        s3_client.put_object(Body=json.dumps(json_data), Bucket=s3_bucket, Key=s3_key)
    return True
