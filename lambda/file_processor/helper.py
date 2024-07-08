import boto3
from io import BytesIO

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def save_image_to_s3(image, bucket, key):
    with BytesIO() as image_buffer:
        image.save(image_buffer, 'JPEG')
        image_buffer.seek(0)
        s3_client.upload_fileobj(image_buffer, bucket, key)

def delete_object(bucket, key):
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def copy_and_delete_object(source_bucket_name, source_key, dest_bucket_name, dest_key=None):
    if dest_key is None:
        dest_key = source_key
    try:
        copy_source = {
            'Bucket': source_bucket_name,
            'Key': source_key
        }
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket_name, Key=dest_key)

        # Delete the original object
        s3_client.delete_object(Bucket=source_bucket_name, Key=source_key)

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
