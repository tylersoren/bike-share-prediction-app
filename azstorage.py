import os
from azure.storage.blob import BlobServiceClient
# from azure.storage.blob._models import BlobPrefix
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
        # Get a token credential for authentication
        # token_credential = ClientSecretCredential(
        #     self.app_config['TENANT_ID'],
        #     self.app_config['CLIENT_ID'],
        #     self.app_config['CLIENT_SECRET']
        # )
        
        # Create the BlobServiceClient and connect to the storage container
        try:
            self.blob_service_client = BlobServiceClient(account_url=self.account_url, credential=credential)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
        except Exception as e:
            logger.error(e)


    # # Function to walk an Azure Storage path and get all blobs and subdirectories
    # def walk_blobs(self, user_session: UserStorageSession, sub_folder=""):
    #     # Initiate blob iterator on the search path
    #     search_path = user_session.path + sub_folder
    #     try:
    #         blob_list = self.container_client.walk_blobs(name_starts_with=search_path, include='metadata',
    #                                                      delimiter='/')
    #     except Exception as e:
    #         logger.error(e)
    #         return Response(message="Failed to get Blob List", status_code=400)

    #     new_folders = []
    #     for blob in blob_list:
    #         # Check if item is a directory and add to list of additional folders to walk
    #         if isinstance(blob, BlobPrefix):
    #             new_folders.append(remove_prefix(blob.name, user_session.path).rstrip("/"))
    #         else:
    #             # Try to get metadata for blob if it exists and check if user matches the
    #             # original upload user
    #             try:
    #                 uploaded_by = getattr(blob, 'metadata')['uploaded_by'].lower()
    #             except AttributeError:
    #                 logger.warning("Metadata missing from blob: " + blob.name + " Setting user to null")
    #                 uploaded_by = ""

    #             # If blob uploaded by current user, enable deleteion
    #             if uploaded_by == user_session.user:
    #                 delete_enabled = True
    #             else:
    #                 delete_enabled = False

    #             # Convert size to KB
    #             size = int(blob.size / 1024)
    #             if size == 0:
    #                 size = "<1"

    #             # Add blob info to blob_table
    #             user_session.blob_table.append(dict(filename=blob.name.split("/")[-1],
    #                                                         path=blob.name.rsplit("/", 1)[0],
    #                                                         name=blob.name,
    #                                                         size=size,
    #                                                         uploaded_by=uploaded_by,
    #                                                         delete_enabled=delete_enabled))

    #     # Append discovered subfolders to folder list and recursively walk any new directories
    #     user_session.folder_list += new_folders
    #     for folder in new_folders:
    #         self.walk_blobs(user_session, folder + "/")

    #     return Response()

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
            return Response(message="Must select a file to upload first!",status_code=400)

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
    def delete_blob(self, user_session: UserStorageSession, blob_name):
        if blob_name is None:
            logger.warning(user_session.user + " sent delete request without specified blob name")
            return Response(message="No file specified for deletion",status_code=400)
        else:
            delete_count = 0
            for blob in user_session.blob_table:
                if blob['name'] == blob_name and blob['uploaded_by'] == user_session.user:
                    delete_count += 1
                    blob_client = self.blob_service_client.get_blob_client(container=self.container_name,
                                                                           blob=blob_name)
                    logger.info(user_session.user + " deleting blob: " + blob_name)
                    blob_client.delete_blob(delete_snapshots=False)
                    user_session.blob_table.remove(blob)

            if delete_count < 1:
                logger.warning(user_session.user + " sent delete request for: " + blob_name + " but blob was not found")
                return Response(message="File to delete was not found in the specified location",status_code=400)

        return Response(message="File deleted successfully",status_code=200)


# function to get unique values
def unique(list1):
    # insert the list to the set 
    list_set = set(list1)
    # convert the set to the list and return
    return (list(list_set))


# Remove prefix from string
def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
