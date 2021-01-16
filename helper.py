from sys import int_info
import pandas as pd
import numpy as np
import os, uuid, tempfile, shutil

import matplotlib
# Setting matplotlib backend to prevent conflict with Flask
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import seaborn as sns
import datetime
from flask import url_for
from azstorage import AzureStorage
from weather import Weather

import logging

logger = logging.getLogger('bike-share-predict')

temp_dir = base_path = tempfile.gettempdir()


# Fetch Environment variables for configuration
storage_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
if not storage_url:
  raise ValueError("Need to define AZURE_STORAGE_ACCOUNT_URL")

container_name = os.getenv('AZURE_STORAGE_IMAGE_CONTAINER_NAME')
if not container_name:
  raise ValueError("Need to define AZURE_STORAGE_IMAGE_CONTAINER_NAME")

weather_api_key = os.getenv('WEATHER_API_KEY')
if not weather_api_key:
  raise ValueError("Need to define WEATHER_API_KEY")


# Configure Azure Storage connection for image files
img_storage = AzureStorage(storage_url, container_name)

# Configure weather API connection
weather = Weather(weather_api_key)

# Specify column order for data model predictions
prediction_columns = ['Hour', 'TMAX', 'TMIN', 
            'Day of week', 'Month','Holiday', 
            'AWND', 'PRCP']

# Generate values for prediction based on submitted form values
def get_predict_form_values(form):
    date = datetime.datetime.strptime(form['date'], '%Y-%m-%d')
    holiday = form.get('holiday')
    # Check if box was checked and set to 0 or 1
    if holiday is None:
        holiday = float(0)
    else:
        if holiday == 'on':
            holiday = float(1)
        else:
            raise ValueError('Holiday selection value incorrect')

    lotemp = float(form['lotemp'])
    hitemp = float(form['hitemp'])
    wind = float(form['wind'])
    precip = float(form['precip'])
    month = date.month
    day = date.weekday()
    hours = np.arange(0,24,1)        


    values = pd.DataFrame()
    values['Hour'] = hours
    values['TMAX'] = hitemp
    values['TMIN'] = lotemp
    values['Day of week'] = day
    values['Month'] = month
    values['Holiday'] = holiday
    values['AWND'] = wind
    values['PRCP'] = precip

    return values

# Dynamically generate values to submit for prediction based on a # of days from the current day
# Can only generate up to a week in advance due to limited forecast availability
def get_predict_values(day = 1):
    if  0 > day > 7:
        logger.error("Day outside range")
        raise IndexError('Selected day outside range for available weather forecast')
    else:
        # Get forecasted weather values
        forecast = weather.get_daily_forecast(day)
        
        # Get date x days from today (0-7)
        date = datetime.date.today() + datetime.timedelta(days=day)
        ######################
        ## TODO
        # Add logic for Check if holiday
        holiday = 0.0

        month = date.month
        day = date.weekday()
        hours = np.arange(0,24,1)        
        values = pd.DataFrame()
        values['Hour'] = hours
        values['TMAX'] = forecast['temp_max']
        values['TMIN'] = forecast['temp_min']
        values['Day of week'] = day
        values['Month'] = month
        values['Holiday'] = holiday
        values['AWND'] = forecast['wind_speed']
        values['PRCP'] = forecast['rain']
        return values


def get_data_values(form, columns):
    rides = int(form['Ride count'])
    wind = float(form['AWND'])
    precip = float(form['PRCP'])
    hitemp = float(form['TMAX'])
    lotemp = float(form['TMIN'])
    data= [[rides, wind, precip, hitemp, lotemp]]
    
    values = pd.DataFrame(
        data, columns = columns
    )   

    return values

def create_plot(hours, predictions, destination_type = 'azure'):

    filename = str(uuid.uuid4()) + ".png"
    temp_path = os.path.join(temp_dir, filename)

    sns.set_style("whitegrid")
    sns.lineplot(x=hours, y=predictions)
    plt.title('Predicted Ride Count per Hour')
    plt.xlabel('Hour')
    plt.ylabel('Ride Count')
    plt.xticks(np.arange(0, 23, 4))
    plt.savefig(temp_path, format='png')
    plt.close()

    # Upload image to public storage bucket
    if destination_type == 'azure':
        img_storage.upload_blob(temp_path)
        img_url =  img_storage.account_url + img_storage.container_name + '/' + filename

    # Default to local path in static directory
    else:
        static_path = 'images/plots/' + filename
        local_path = os.path.join('./static', static_path)
        shutil.copyfile(temp_path, local_path)
        img_url =  url_for('static', static_path)
    
    # Cleanup temp file
    # os.remove(temp_path)
    return img_url

    