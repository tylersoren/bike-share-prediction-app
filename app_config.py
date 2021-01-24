import os
from BikeShare.api import BikeShareApi
import logging

logger = logging.getLogger('bike-share-predict')

# Statically set configuration items
model_path = os.path.abspath(os.path.join(os.getcwd(),'models/bike_share' ))
data_filename = 'hourly_rides.csv'


def initialize():
    # Fetch Environment variables for configuration
    weather_api_key = os.getenv('WEATHER_API_KEY')
    if not weather_api_key:
        raise ValueError("Need to define WEATHER_API_KEY")

    storage_url= os.getenv('AZURE_STORAGE_ACCOUNT_URL')
    # if Storage URL var isn't set, default to local storage
    if not storage_url:
        logger.info('Env variable AZURE_STORAGE_ACCOUNT_URL not set. Using local storage')
        data_file = os.path.join(os.getcwd(), 'data/prepared', data_filename)

        api = BikeShareApi(data_file=data_file,
              model_path=model_path,
              weather_api_key=weather_api_key)

    # Get config parameters for Azure Storage
    else:
        data_container_name = os.getenv('AZURE_STORAGE_DATA_CONTAINER_NAME')
        if not data_container_name:
            raise ValueError("Need to define AZURE_STORAGE_DATA_CONTAINER_NAME")

        img_container_name = os.getenv('AZURE_STORAGE_IMAGE_CONTAINER_NAME')
        if not img_container_name:
            raise ValueError("Need to define AZURE_STORAGE_IMAGE_CONTAINER_NAME")

        api = BikeShareApi(data_file=data_filename,
              model_path=model_path,
              weather_api_key=weather_api_key, 
              storage_url=storage_url, 
              data_container_name=data_container_name,
              img_container_name=img_container_name
              )
    
    return api

