from id_pydantic_classes.PassportFields import PassportFields
from id_pydantic_classes.DriverLicenseFields import DriverLicenseFields
import os
from helper import *

def lambda_handler(event, context):
    print(event)
    try:
        bucket = event["bucket"]
        key = event["key"]
       
    except Exception as e:
        print("we are in dev mode", e)
        bucket = "functioncallingstack-govidextractorbucket376c0bd0-gwqac3yuvyjh"
        key = "stagging_files/dummy_passport.jpeg"
        key = "stagging_files/2024/07/08/11/01/dummy_driver_license.jpeg"

    input_jpeg_file = f"s3://{bucket}/{key}"
    file_name = key.split("/")[-1]
    jpeg_files_list = [input_jpeg_file]
    # jpeg_files_list = get_jpeg_files_uri(bucket, target_path)

    pydantic_classes = [PassportFields(), DriverLicenseFields()]

    response = invoke_bedrock_anthropic_model(jpeg_files_list, pydantic_classes)
    try:
        id_values_dict_ = parse_bedrock_response(response)
    except:
        id_values_dict_ = response.to_json()
    print(id_values_dict_)

    result_json_folder = f"processed_files/{file_name}"
    write_json_to_s3(id_values_dict_, bucket, result_json_folder)

    return{
        "statusCode": 200,
        "body": f"result has been saved in the s3::/{bucket}/{result_json_folder}"
    }

if __name__ == "__main__":
    event = None
    lambda_handler(event, None)
   