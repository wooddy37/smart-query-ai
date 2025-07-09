from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

azure_storage_emdpoint = os.getenv("AZURE_STORAGE_EMDPOINT")
azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
azure_storage_container = os.getenv("AZURE_STORAGE_CONTAINER", "query-log-data")

def upload_to_blob(file, project_code, dbms_type):
    blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))

    blob_name = f"{dbms_type.lower()}/{project_code}/{datetime.now().strftime('%Y%m%d')}_{file.name}"
    container_client = blob_service_client.get_container_client(container=azure_storage_container)
    blob_client = container_client.get_blob_client(blob_name)

    blob_client.upload_blob(file, overwrite=True)
    
    return f"{azure_storage_emdpoint}/{azure_storage_container}/{blob_name}"