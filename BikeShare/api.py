from BikeShare.data import BikeData
from BikeShare.predict import BikeShareModel
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
import datetime
from flask import url_for


import logging

logger = logging.getLogger('bike-share-predict')



class BikeShareApi:

    def __init__(self, data_file, model_path, weather_api_key, img_url, img_container_name):
        logger.info('Initializing the BikeShare data. Purging old graph images...')
        # Configure Azure Storage connection for image files
        self.img_storage = AzureStorage(img_url, img_container_name)
        self.img_storage.clear_storage()

        # Configure weather API connection
        self.weather = Weather(weather_api_key)

        # Specify column order for data model predictions
        self.prediction_columns = ['Hour', 'Hi temp', 'Lo temp', 
                    'Day of week', 'Month','Holiday', 
                    'Wind', 'Rain']
        
        # Create ML data model object for predictions
        self.model = BikeShareModel(model_path)

        # Create historical data object
        self.data = BikeData(summary_file=data_file)

    # Generate values for prediction based on submitted form values
    def get_predict_form_values(self, form):
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
    def get_predict_values(self, day = 1):
        if  0 > day > 7:
            logger.error("Day outside range")
            raise IndexError('Selected day outside range for available weather forecast')
        else:
            # Get forecasted weather values
            forecast = self.weather.get_daily_forecast(day)
            
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
    
    def update_data_values(self, form, timestamp):
        rides = int(form['Ride count'])
        wind = float(form['Wind'])
        precip = float(form['Rain'])
        hitemp = float(form['Hi temp'])
        lotemp = float(form['Lo temp'])
        data= [[rides, wind, precip, hitemp, lotemp]]
        
        updated_values = pd.DataFrame(
            data, columns = self.data.data_columns
        )   

        self.data.update(timestamp, updated_values)

    def get_data(self, page):
        return self.data.get(page)

    def get_predictions(self, values):
        # run predictions and round to nearest integer and clip any negative numbers to 0
        predictions = np.rint(self.model.predict(values).clip(min=0)).astype(int).flatten()
        results = []
        for index, hour in enumerate(values['Hour']):
            results.append(dict(hour=f" {hour} : 00", count=predictions[index]))
        
        return results, predictions

    def create_prediction_plot(self, hours, predictions, destination_type = 'azure'):
        title = 'Predicted Ride Count per Hour'
        xlabel = 'Hour'
        ylabel = 'Ride Count'
        xticks =  np.arange(0, 23, 4)

        return self.__create_plot(hours, predictions, title, xlabel, ylabel, xticks, destination_type)

    def create_data_plot(self, request, destination_type = 'azure'):
        data_type = request.args.get('type')
        if data_type is None or data_type not in ['year', 'week', 'temp', 'wind']:
            data_type = 'week'

        plot_type = "line"
        data_type = data_type.lower()
        if data_type in ['year', 'week']:
            plot_data = self.data.get_time(data_type)
            x = plot_data['Timestamp']
            y = plot_data['Ride count']
            xlabel = 'Date'
            ylabel = 'Ride Count'
            xticks = None
            if data_type == 'year':
                title = 'Ride Count per Day for Past Year'
            else:
                title = 'Ride Count per Hour for Past Week'
        else:
            plot_data = self.data.get_weather(data_type)
            ylabel = 'Hourly Ride Count'
            if data_type == 'temp':
                x = plot_data['Average temp']
                y = plot_data['Ride count']
                title = 'Average Hourly Ride Count by Daily Average Temp'
                xlabel = 'Temp (F)'
                xticks = np.arange(plot_data['Average temp'].min(), plot_data['Average temp'].max(), 3.0)

            else:
                x = plot_data['Wind']
                y = plot_data['Ride count']
                title = 'Average Hourly Ride Count by Daily Average Wind Speed'
                xlabel = 'Wind Speed (MPH)'
                xticks = np.arange(round(plot_data['Wind'].min()), round(plot_data['Wind'].max())+1, 2.0)

        return data_type, self.__create_plot(x, y, title, xlabel, ylabel, xticks, plot_type, destination_type)

    def __create_plot(self, x, y, title, xlabel, ylabel, xticks, plot_type = 'line', destination_type = 'azure'):

        filename = str(uuid.uuid4()) + ".png"
        temp_path = os.path.join(tempfile.gettempdir(), filename)

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
            # Use date formatting to conform to the timescale of the given data
            locator = mdates.AutoDateLocator(minticks=4, maxticks=14)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        else:
            plt.xticks(xticks)

        plt.xticks(rotation=45)
        plt.savefig(temp_path, format='png')
        plt.close()

        # Upload image to public storage bucket
        if destination_type == 'azure':
            img_url = self.img_storage.upload_blob(temp_path)

        # Default to local path in static directory
        else:
            static_path = 'images/plots/' + filename
            local_path = os.path.join('./static', static_path)
            shutil.copyfile(temp_path, local_path)
            img_url =  url_for('static', static_path)
        
        # Cleanup temp file
        os.remove(temp_path)
        return img_url

