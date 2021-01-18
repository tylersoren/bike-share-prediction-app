import pandas as pd

import math

# Set static number of rows to return for queries
count = 50
class BikeData:

  def __init__(self, summary_file):

      self.summary_df = pd.read_csv(
            filepath_or_buffer=summary_file,  
            parse_dates=[0])
      
      #Ensure that Ride count column is integer
      self.summary_df['Ride count'] = self.summary_df['Ride count'].astype(str).astype(int)
      # Get number of pages
      self.max_page=math.ceil(len(self.summary_df.index)/count)
      # Set data and display columns for updates and output
      self.data_columns = [
                  'Ride count',
                  'Wind',
                  'Rain',
                  'Hi temp',
                  'Lo temp'
              ]
      self.display_columns = self.data_columns.copy()
      self.display_columns.insert(0, 'Timestamp')


  def get_summary(self, page=1):
      start = count*(page-1)
      end = count*page
      return self.summary_df[self.display_columns].loc[start:end]

  def get_summary_time(self, type):
      if type == 'week':
        return self.summary_df.tail(7*24)
      if type == 'year':
        # Copy data and extract the date portion of the time as a new field
        year_df = self.summary_df.copy()
        year_df['Date'] = year_df['Timestamp'].dt.date
        
        # Create grouping by Date and total # of rides
        year_df = year_df.groupby(['Date'], as_index = False)['Ride count'].sum()
        year_df.rename(columns={'Date': 'Timestamp'}, inplace=True)
        # Return last 365 days worth of data
        return year_df.tail(365)
      return 1

  def get_summary_weather(self, type):
      if type == 'temp':
        return self.summary_df.groupby(['Average temp'], as_index = False)['Ride count'].mean()
      if type == 'wind':
        return self.summary_df.groupby(['Wind'], as_index = False)['Ride count'].mean()

  def update_summary(self, timestamp, updated_values):
      self.summary_df.loc[self.summary_df['Timestamp'] == timestamp, self.data_columns] = updated_values.values

