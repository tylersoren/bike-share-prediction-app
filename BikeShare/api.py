from BikeShare.data import BikeData
from BikeShare.predict import BikeShareModel
from BikeShare.calendar import is_holiday
from azstorage import AzureStorage
from weather import Weather
import pandas as pd
import numpy as np
import os, uuid, tempfile, shutil

import matplotlib
# Setting matplotlib backend to prevent conflict with Flask
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import seaborn as sns
import datetime as dt
from flask import url_for

import logging

logger = logging.getLogger('bike-share-predict')

temp_dir = tempfile.gettempdir()

class BikeShareApi():
       
    # Initialize API
    def __init__(self, data_file, model_path, weather_api_key, 
            storage_url=None, data_container_name=None, img_container_name=None):
        # Configure weather API connection
        self.weather = Weather(weather_api_key)

        # Create ML data model object for predictions
        self.model = BikeShareModel(model_path)

        # If no Azure storage information provided default to local storage
        if storage_url is None:
            self.storage_type = 'local'
        # Else configure Azure storage
        else:
            self.storage_type = 'azure'
            logger.info('Initializing the BikeShare data. Purging old graph images from Azure Storage...')
            # Configure Azure Storage connection for image files
            self.img_storage = AzureStorage(storage_url, img_container_name)
            # Purge all old messages
            self.img_storage.clear_storage()
            
            # Configure Azure Storage connection and download data file
            self.data_storage = AzureStorage(storage_url, data_container_name)
            self.data_storage.download_blob(source_file=data_file, 
                        destination_file=data_file, 
                        destination_folder=temp_dir)
            data_file = os.path.join(temp_dir, data_file)
        
        # Create historical data object
        self.data = BikeData(summary_file=data_file)

    # Generate values for prediction based on submitted form values
    def get_predict_form_values(self, form):
        date = (dt.datetime.strptime(form['date'], '%Y-%m-%d')).date()
        
        # check if date is a holiday
        holiday = float(is_holiday(date))


        lotemp = float(form['lotemp'])
        hitemp = float(form['hitemp'])
        wind = float(form['wind'])
        precip = float(form['precip'])
        # Set boolean flag for snow
        if float(form['snow']) > 0:
            snow = 1
        else:
            snow = 0
        month = date.month
        day = date.weekday()
        hours = np.arange(0,24,1)        


        values = pd.DataFrame()
        values['Hour'] = hours
        values['Hi temp'] = hitemp
        values['Lo temp'] = lotemp
        values['Day of week'] = day
        values['Month'] = month

        # Set season one-hot variables
        seasons = ['Fall','Spring','Summer','Winter']
        for col in seasons:
            values[col] = 0
        if month in [1,2,12]:
            values['Winter'] = 1
        elif month in[3,4,5]:
            values['Spring'] = 1
        elif month in [6,7,8]:
            values['Summer'] = 1
        elif month in[9,10,11]:
            values['Fall'] = 1

        values['Holiday'] = holiday
        values['Wind'] = wind
        values['Rain'] = precip
        values['Snow'] = snow

        return values

    # Dynamically generate values to submit for prediction based on a # of days from the current day
    # Can only generate up to a week in advance due to limited forecast availability
    def get_predict_values(self, day = 1):
        if  0 > day > 7:
            logger.error("Day outside range")
            raise IndexError('Selected day outside range for available weather forecast')
        else:
            # Get forecasted weather values
            forecast = self.weather.get_daily_forecast(day)
            
            # Get date x days from today (0-7)
            date = dt.date.today() + dt.timedelta(days=day)
            
            # check if date is a holiday
            holiday = float(is_holiday(date))

            month = date.month
            day = date.weekday()
            hours = np.arange(0,24,1)        
            values = pd.DataFrame()
            values['Hour'] = hours
            values['Hi temp'] = forecast['temp_max']
            values['Lo temp'] = forecast['temp_min']
            values['Day of week'] = day
            values['Month'] = month
            # Set season one-hot variables
            seasons = ['Fall','Spring','Summer','Winter']
            for col in seasons:
                values[col] = 0
            if month in [1,2,12]:
                values['Winter'] = 1
            elif month in[3,4,5]:
                values['Spring'] = 1
            elif month in [6,7,8]:
                values['Summer'] = 1
            elif month in[9,10,11]:
                values['Fall'] = 1

            values['Holiday'] = holiday
            values['Wind'] = forecast['wind_speed']
            values['Rain'] = forecast['rain']
            # Set boolean flag for snow
            if forecast['snow'] > 0:
                values['Snow'] = 1
            else:
                values['Snow'] = 0
            

            return values
    
    # Update dataframe with submitted values
    def update_data_values(self, form, timestamp):
        rides = int(form['Ride count'])
        wind = float(form['Wind'])
        precip = float(form['Rain'])
        snow = float(form['Snow'])
        hitemp = float(form['Hi temp'])
        lotemp = float(form['Lo temp'])
        data= [[rides, wind, precip, snow, hitemp, lotemp]]
        
        updated_values = pd.DataFrame(
            data, columns = self.data.data_columns
        )   

        self.data.update(timestamp, updated_values)
    
    # Save dataframe object to a CSV file in the configured storage location
    def save_data_values(self):
        # Export data to temp csv and save to temp file
        time_format='%Y-%m-%dT%H.%M.%S'
        timestamp = dt.datetime.now().strftime(time_format)
        temp_file = f"updated-ride-data-{timestamp}.csv"
        temp_path = os.path.join(temp_dir, temp_file)

        logger.info(f"Saving updated data as file {temp_file}")
        self.data.to_csv(temp_path)
        if self.storage_type == 'azure':
            file_loc = self.data_storage.upload_blob(temp_path)
            # Cleanup temp file
            os.remove(temp_path)
        else:
            file_loc = temp_path 

        return file_loc
    
    # Return dataframe for selected page
    def get_data(self, page):
        return self.data.get(page)

    # Get predictions from ML model
    def get_predictions(self, values):
        # run predictions and round to nearest integer and clip any negative numbers to 0
        predictions = np.rint(self.model.predict(values).clip(min=0)).astype(int).flatten()
        results = []
        for index, hour in enumerate(values['Hour']):
            results.append(dict(hour=f" {hour} : 00", count=predictions[index]))
        
        return results, predictions

    # Generate plot image for ride count predictions
    def create_prediction_plot(self, hours, predictions):
        title = 'Predicted Ride Count per Hour'
        xlabel = 'Hour'
        ylabel = 'Ride Count'
        xticks =  np.arange(0, 23, 4)

        return self.__create_plot(hours, predictions, title, xlabel, ylabel, xticks)

    # Generate plot image for data visualizations
    def create_data_plot(self, request):
        # Retrieve selected plot subtype and type 
        data_type = request.args.get('type')
        data_subtype = request.args.get('subtype')
        # error handling if incorrect input was entered
        if data_type is None or data_type not in ['rides', 'weather']:
            data_type = 'rides'
        
        plot_type = "line"
        xticks = None
        # Handling for the Ride count type plots
        if data_type == 'rides':
            # error handling, set to default of week
            if data_subtype is None or data_subtype not in ['year', 'week', 'monthly', 'temp', 'wind']:
                data_subtype = 'week'
            # Get time based parameters
            if data_subtype in ['year', 'week', 'monthly']:
                plot_data = self.data.get_time(data_subtype)
                y = plot_data['Ride count']
                xlabel = 'Date'
                ylabel = 'Ride Count'
                if data_subtype == 'year':
                    title = 'Ride Count 7-day rolling average for Past Year'
                    x = plot_data['Date']
                    y = plot_data['Rolling avg']
                elif data_subtype == "monthly":
                    title = 'Distribution of hourly rides by month'
                    x = plot_data['Month']
                    xlabel = 'Month'
                    xticks = plot_data['Month'].unique()
                    xticks.sort()
                    plot_type = 'box'
                else:
                    title = 'Ride Count per Hour for Past Week'
                    x = plot_data['Timestamp']
        
            else:
                # Get weather based parameters
                plot_data = self.data.get_weather(data_subtype)
                ylabel = 'Ride Count'
                if data_subtype == 'temp':
                    plot_type = 'area'
                    x = plot_data['Average temp']
                    y = plot_data['Ride count']
                    title = 'Distribution of total rides over daily average temperatures'
                    xlabel = 'Temp (F)'
                    xticks = np.arange(plot_data['Average temp'].min(), plot_data['Average temp'].max(), 3.0)
                else:
                    x = plot_data['Wind']
                    y = plot_data['Ride count']
                    title = 'Average Hourly Ride Count by Daily Average Wind Speed'
                    xlabel = 'Wind Speed (MPH)'
                    xticks = np.arange(round(plot_data['Wind'].min()), round(plot_data['Wind'].max())+1, 2.0)
        # Data type is weather
        elif data_type == 'weather':
            # error handling, set to default of temp
            if data_subtype is None or data_subtype not in ['temp', 'wind', 'rain']:
                data_subtype = 'temp'
            if data_subtype == 'wind':
                subtype = 'rolling_wind'
                ylabel = 'Average Wind Speed (MPH)'
                title = 'Wind Speed 3-day rolling average for Past Year'
            elif data_subtype == 'rain':
                plot_type = 'bar'
                subtype = 'rain'
                ylabel = 'Rain (inches)'
                title = 'Total Rainfall by Month'
            else:
                subtype = 'rolling_temp'
                ylabel = 'Average Temp (F)'
                title = 'Temperature 7-day rolling average for Past Year'
                
            plot_data = self.data.get_weather(subtype)
            if subtype == 'rain':
                y = plot_data['Rain']
                x = plot_data['Month']
                xlabel = 'Month'
            else:
                y = plot_data['Rolling avg']
                x = plot_data['Date']
                xlabel = 'Date'

        logger.info(f"Creating plot for type: {data_type} and subtype: {data_subtype}")

        return data_type, data_subtype, self.__create_plot(x, y, title, xlabel, ylabel, xticks, plot_type)

    # Handle image generation for plot creation
    def __create_plot(self, x, y, title, xlabel, ylabel, xticks, plot_type = 'line'):

        filename = str(uuid.uuid4()) + ".png"
        temp_path = os.path.join(temp_dir, filename)

        fig, ax = plt.subplots(figsize = ( 8 , 5 )) 

        # Create plot of selected type
        sns.set_style("whitegrid")
        if plot_type == 'box':
            sns.boxplot(x=x, y=y)
        elif plot_type == 'area':
            sns.lineplot(x=x, y=y)
            plt.fill_between(x.values, y.values)
        elif plot_type == 'bar':
            sns.barplot(x=x, y=y)
        else:
            sns.lineplot(x=x, y=y)

        # Set plot display parameters
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        if xlabel == 'Date':
            # Use date formatting to conform to the timescale of the given data
            locator = mdates.AutoDateLocator(minticks=4, maxticks=14)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
            plt.xlim(min(x), max(x))
        elif plot_type == 'area':
            plt.xlim(0, 90)
        elif plot_type == 'line':
            plt.xticks(xticks)
            plt.xlim(min(x) - 1, max(x) + 1)
        
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=45)
        plt.savefig(temp_path, format='png')
        plt.close()

        # Upload image to public storage bucket
        if self.storage_type == 'azure':
            img_url = self.img_storage.upload_blob(temp_path)

        # Default to local path in static directory
        else:
            static_path = 'images/plots/' + filename
            local_path = os.path.normpath(os.path.join(os.getcwd(), 'static', static_path))
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            # Copy the temp file to the static images folder
            shutil.copyfile(temp_path, local_path)
            # Generate flask url for the image
            img_url =  url_for('static', filename=static_path)
        
        # Cleanup temp file
        os.remove(temp_path)
        return img_url

