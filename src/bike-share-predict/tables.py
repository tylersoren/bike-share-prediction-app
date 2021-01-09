import pandas as pd
import os

data_subdir = 'data\\prepared'
weather_file = 'weather.csv'
transaction_file = 'bike_transactions.csv'
hourly_ride_file = 'hourly_rides.csv'

data_dir = os.path.abspath(os.path.join(os.getcwd(), '../..', data_subdir))
class BikeData:

  def __init__(self):
      self.weather_df = pd.read_csv(
            filepath_or_buffer=os.path.join(data_dir, weather_file),  
            parse_dates=[1])
      
      self.summary_df = pd.read_csv(
            filepath_or_buffer=os.path.join(data_dir, hourly_ride_file),  
            parse_dates=[1])

  def get_weather(self, time='all'):
    if time == 'all':
        return self.weather_df

  def get_summary(self, time='all'):
    if time == 'all':
        return self.summary_df