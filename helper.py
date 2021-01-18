from seaborn.categorical import barplot
from tables import BikeData
import pandas as pd
import numpy as np
import os, uuid, tempfile, shutil

import matplotlib
# Setting matplotlib backend to prevent conflict with Flask
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
prediction_columns = ['Hour', 'Hi temp', 'Lo temp', 
            'Day of week', 'Month','Holiday', 
            'Wind', 'Rain']

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
    values['Hi temp'] = hitemp
    values['Lo temp'] = lotemp
    values['Day of week'] = day
    values['Month'] = month
    values['Holiday'] = holiday
    values['Wind'] = wind
    values['Rain'] = precip

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
        values['Hi temp'] = forecast['temp_max']
        values['Lo temp'] = forecast['temp_min']
        values['Day of week'] = day
        values['Month'] = month
        values['Holiday'] = holiday
        values['Wind'] = forecast['wind_speed']
        values['Rain'] = forecast['rain']
        return values


def get_data_values(form, columns):
    rides = int(form['Ride count'])
    wind = float(form['Wind'])
    precip = float(form['Rain'])
    hitemp = float(form['Hi temp'])
    lotemp = float(form['Lo temp'])
    data= [[rides, wind, precip, hitemp, lotemp]]
    
    values = pd.DataFrame(
        data, columns = columns
    )   

    return values

def create_prediction_plot(hours, predictions, destination_type = 'azure'):

    title = 'Predicted Ride Count per Hour'
    xlabel = 'Hour'
    ylabel = 'Ride Count'
    xticks = np.arange(0, 23, 4)

    return create_plot(hours, predictions, title, xlabel, ylabel, xticks, destination_type)

def create_data_plot(data: BikeData, request, destination_type = 'azure'):
    data_type = request.args.get('type')
    if data_type is None or data_type not in ['year', 'week', 'temp', 'wind']:
        data_type = 'week'

    plot_type = "line"
    data_type = data_type.lower()
    if data_type in ['year', 'week']:
        plot_data = data.get_summary_time(data_type)
        x = plot_data['Timestamp']
        y = plot_data['Ride count']
        if data_type == 'year':
            title = 'Ride Count per Day for Past Year'
            xlabel = 'Date'
            ylabel = 'Ride Count'
            xticks = np.arange(plot_data['Timestamp'].min(), plot_data['Timestamp'].max(),datetime.timedelta(days=30))
        else:
            title = 'Ride Count per Hour for Past Week'
            xlabel = 'Date'
            ylabel = 'Ride Count'
            xticks = np.arange(plot_data['Timestamp'].min(), plot_data['Timestamp'].max(),datetime.timedelta(hours=6))
    else:
        plot_data = data.get_summary_weather(data_type)
        if data_type == 'temp':
            x = plot_data['Average temp']
            y = plot_data['Ride count']
            title = 'Average Hourly Ride Count by Daily Average Temp'
            xlabel = 'Temp (F)'
            ylabel = 'Hourly Ride Count'
            xticks = np.arange(plot_data['Average temp'].min(), plot_data['Average temp'].max(), 3.0)

        else:
            x = plot_data['Wind']
            y = plot_data['Ride count']
            title = 'Average Hourly Ride Count by Daily Average Wind Speed'
            xlabel = 'Wind Speed (MPH)'
            ylabel = 'Hourly Ride Count'
            xticks = np.arange(round(plot_data['Wind'].min()), round(plot_data['Wind'].max())+1, 2.0)

    return data_type, create_plot(x, y, title, xlabel, ylabel, xticks, plot_type, destination_type)

def create_plot(x, y, title, xlabel, ylabel, xticks, plot_type = 'line', destination_type = 'azure'):

    filename = str(uuid.uuid4()) + ".png"
    temp_path = os.path.join(temp_dir, filename)

    fig, ax = plt.subplots(figsize = ( 8 , 5 )) 
    sns.set_style("whitegrid")
    if plot_type == 'bar':
       sns.barplot(x, y)
    else:
       sns.lineplot(x, y)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xlim(min(x), max(x))

    if xlabel == 'Date':
        locator = mdates.AutoDateLocator(minticks=4, maxticks=14)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        plt.xticks(rotation=60)
    else:
        plt.xticks(xticks)
        plt.xticks(rotation=45)
    
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
    os.remove(temp_path)
    return img_url
