import pandas as pd
import os

class BikeData:

  def __init__(self, weather_file, summary_file):
      self.weather_df = pd.read_csv(
            filepath_or_buffer=weather_file,  
            parse_dates=[1])
      
      self.summary_df = pd.read_csv(
            filepath_or_buffer=summary_file,  
            parse_dates=[1])

  def get_weather(self, time='all'):
    if time == 'all':
        return self.weather_df

  def get_summary(self, time='all'):
    if time == 'all':
        return self.summary_df