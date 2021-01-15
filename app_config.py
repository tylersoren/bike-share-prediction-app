import os, tempfile
from predict import BikeShareModel
from tables import BikeData
from azstorage import AzureStorage

# Statically set configuration items
model_path = os.path.abspath(os.path.join(os.getcwd(),'models/bike_share_v1.0' ))
temp_dir = base_path = tempfile.gettempdir()
weather_filename = 'weather.csv'
summary_filename = 'hourly_rides.csv'

# Fetch Environment variables for configuration
storage_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
if not storage_url:
  raise ValueError("Need to define AZURE_STORAGE_ACCOUNT_URL")

container_name = os.getenv('AZURE_STORAGE_DATA_CONTAINER_NAME')
if not container_name:
  raise ValueError("Need to define AZURE_STORAGE_DATA_CONTAINER_NAME")



def startup():
  model = BikeShareModel(model_path)

  # Configure Azure Storage connection and download data files
  azure_storage = AzureStorage(storage_url, container_name)
  azure_storage.download_blob(source_file=weather_filename, 
              destination_file=weather_filename, 
              destination_folder=temp_dir)
  azure_storage.download_blob(source_file=summary_filename, 
              destination_file=summary_filename, 
              destination_folder=temp_dir)


  data = BikeData(weather_file=os.path.join(temp_dir, weather_filename),
                summary_file=os.path.join(temp_dir, summary_filename))
  
  return model, data, azure_storage

