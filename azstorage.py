import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError
from werkzeug.utils import secure_filename
import time
import logging

logger = logging.getLogger('bike-share-predict')


# Class for storing a connection to an Azure storage account and container
# Provides methods for uploading, downloading, and deleting blobs
class AzureStorage:

    # Initialize the Azure Storage client
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
                    return None
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
            return None

        blob_url = self.account_url + self.container_name + '/' + target_blob

        return blob_url
        
    # Download blob from Azure Storage
    def download_blob(self, destination_file, source_file, destination_folder = '', source_folder = ''):
        # Check if file was included in the Post, if not return warning
        filename = secure_filename(source_file)
        if not filename:
            logger.warning("Must select a file to download first!")
            return None

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
                logger.error(f"Download file failed. {target_blob} not found")
                return None
            
            logger.info(f"Downloaded {target_blob} to {out_file}")

        except Exception as e:
            logger.error(e)
            return None

        return out_file

    # Delete specified blob
    def delete_blob(self, blob_name):
        if blob_name is None:
            logger.warning("Sent delete request without specified blob name")
        else:
            try:
                blob_client = self.blob_service_client.get_blob_client(container=self.container_name,
                                                                        blob=blob_name)
                logger.info(f"Deleting blob: {blob_name}")
                blob_client.delete_blob(delete_snapshots=False)
            except ResourceNotFoundError:
                logger.warning(f"Sent delete request for: { blob_name } but blob was not found")

    # Return list of blobs in the container
    def list_blobs(self):
        try:
            blob_list = self.container_client.list_blobs()
        except Exception:
            logger.error(f"Failed to list Blobs in container {self.container_name}")
            return None

        return blob_list
    
    # Delete all blobs in the storage container
    def clear_storage(self):
        blob_list = self.list_blobs()
        for blob in blob_list:
            self.delete_blob(blob['name'])