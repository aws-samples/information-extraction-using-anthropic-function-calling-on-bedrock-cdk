import pypdfium2
import boto3
from datetime import datetime
from helper import *

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def lambda_handler(event, context):
    print(event)
    try:
        bucket = event["bucket"]
        key = event["key"]

    except Exception as e:
        print(e)
        print("we are in dev mode")
        bucket = "functioncallingstack-govidextractorbucket376c0bd0-gwqac3yuvyjh"
        key = "upload_files/dummy_passport_pdf.pdf"
    
    now = datetime.now()
    # Format the time as yyyy/month/day/hh/mm
    timestamp = now.strftime("%Y/%m/%d/%H/%M")

    file_name = key.split("/")[-1]
    file_extension = file_name.split(".")[-1]
    # file name without extension

    if file_extension == "pdf":
        pdf_obj = s3_resource.Object(bucket, key).get()['Body'].read()
        
        # Open the PDF file
        pdf = pypdfium2.PdfDocument(pdf_obj)
        n_pages = len(pdf)
        
        # if given pdf has more than 1 page then throw error
        if n_pages > 1:
            print("Error: This function only accepts single page PDFs. \n \
                  So we will only take first page of the pdf and process it.")
        
        page_num =0
        page = pdf[page_num]
        bitmap = page.render(scale=2, rotation=0)
        pil_image = bitmap.to_pil()

        #create the output_png_folder name with directory separated with yyyy/month/day/hh/mm time stamp
        output_png_folder= f"stagging_files/{timestamp}"
        output_image_name = f"{output_png_folder}/{file_name}.jpeg"
        save_image_to_s3(pil_image, bucket, output_image_name)
        delete_object(bucket, key)
    
    elif file_extension == "jpeg":
        output_png_folder= f"stagging_files/{timestamp}"
        output_image_name = f"{output_png_folder}/{file_name}"
        copy_and_delete_object(source_bucket_name=bucket, source_key=key, dest_bucket_name=bucket, dest_key=output_image_name)
    else:
        print(f"We can only process pdf and jpeg file formats. The uploaded file has format {file_extension} which is not supported!")

    return {
        'bucket': bucket,
        'key': output_image_name,
    }
        
if __name__ == "__main__":
    event = None
    lambda_handler(event, None)
