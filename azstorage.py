import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError
from werkzeug.utils import secure_filename
import time
import logging

logger = logging.getLogger('bike-share-predict')

class Response:

    # Default response object is success with blank message
    # error flag 0 = use base.html
    # error flag 1 = use error.html
    # error flag 2 = return message only
    def __init__(self, message="", status_code=200, error_flag=0):
        self.message=message
        self.status_code=status_code
        self.error_flag=error_flag


class UserStorageSession:

    def __init__(self, path, user):
        self.path = path
        self.user = user
        self.blob_table = []
        self.folder_list = []


# Class for storing a connection to an Azure storage account and container
# Provides methods for listing blobs and folders, uploading and deleting blobs
# All methods return a Response object which contains a message, response code, and a flag 
# to indicates if the error template page should be used instead of the base template
class AzureStorage:

    def __init__(self, storage_url, container_name):
        
        self.account_url = storage_url
        self.container_name = container_name
        
        # Acquire a credential object for the app identity. When running in the cloud,
        # DefaultAzureCredential uses the app's managed identity or user-assigned service principal.
        # When run locally, DefaultAzureCredential relies on environment variables named
        # AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID.
        credential = DefaultAzureCredential()

        # Create the BlobServiceClient and connect to the storage container
        try:
            self.blob_service_client = BlobServiceClient(account_url=self.account_url, credential=credential)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
        except Exception as e:
            logger.error(e)

    # Upload blob to Azure Storage
    def upload_blob(self, file, subfolder=''):
        if subfolder == '':
            target_blob = os.path.basename(file)
        else:
            target_blob =  subfolder + "/" + os.path.basename(file)

        try:
            # Create a blob client using the local file name as the name for the blob
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name,
                                                                   blob=(target_blob))
            try:
                # Check if blob already exists
                if blob_client.get_blob_properties()['size'] > 0:
                    logger.warning(f"{target_blob} already exists in the selected path. Skipping upload.")
                    return Response(message=f"{target_blob} already exists in the selected path",status_code=409,error_flag=2)
            except ResourceNotFoundError as e:
                # catch exception that indicates that the blob does not exist and we are good to upload file
                pass
            logger.info(f"Uploading {target_blob} to Azure Storage")

            # Upload the file and measure upload time
            elapsed_time = time.time()
            with open(file, "rb") as data:
                blob_client.upload_blob(data)
            elapsed_time = round(time.time() - elapsed_time, 2)
            logger.info(f"Upload succeeded after {str(elapsed_time)} seconds for: {target_blob}")

        except Exception as e:
            logger.error(e)
            return Response(message="Failed to upload file",status_code=400,error_flag=1)


        return Response(message="Uploaded File Successfully",status_code=200)
        
    # Download blob from Azure Storage
    def download_blob(self, destination_file, source_file, destination_folder = '', source_folder = ''):
        # Check if file was included in the Post, if not return warning
        filename = secure_filename(source_file)
        if not filename:
            return Response(message="Must select a file to download first!",status_code=400)

        if source_folder == '':
            target_blob = filename 
        else:
            target_blob = source_folder + '/' + filename 
        
        if destination_folder == '':
            out_file = os.path.join(os.getcwd(), destination_file)
        else:
            out_file = os.path.join(destination_folder, destination_file)

        try:
            # Create a blob client to 
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name,
                                                                   blob=target_blob)
            try:
                # Attempt download of blob to local storage
                with open(out_file, "wb") as my_blob:
                    blob_data = blob_client.download_blob()
                    blob_data.readinto(my_blob)
            except ResourceNotFoundError as e:
                message = f"Download file failed. {target_blob} not found"
                logger.warning(message)
                return Response(message=message,status_code=400,error_flag=1)
            
            logger.info(f"Downloaded {target_blob} to {out_file}")

        except Exception as e:
            logger.error(e)
            return Response(message="Failed to download file",status_code=400,error_flag=1)


        return Response(message="Downloaded File Successfully",status_code=200)

    # Delete specified blob
    def delete_blob(self, blob_name):
        if blob_name is None:
            logger.warning("Sent delete request without specified blob name")
            return Response(message="No file specified for deletion",status_code=400)
        else:
            try:
                blob_client = self.blob_service_client.get_blob_client(container=self.container_name,
                                                                        blob=blob_name)
                logger.info(f"Deleting blob: {blob_name}")
                blob_client.delete_blob(delete_snapshots=False)
            except ResourceNotFoundError:
                logger.warning(f"Sent delete request for: { blob_name } but blob was not found")
                return Response(message="File to delete was not found in the specified location",status_code=400)

        return Response(message="File deleted successfully",status_code=200)
