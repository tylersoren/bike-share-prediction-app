import pandas as pd

import math

# Set static number of rows to return for queries
count = 50

# Class representing Bike Share data object
class BikeData:

  # Initialize the data object
  def __init__(self, summary_file):

      self.data_df = pd.read_csv(
            filepath_or_buffer=summary_file,  
            parse_dates=[0])
      
      #Ensure that Ride count column is integer
      self.data_df['Ride count'] = self.data_df['Ride count'].astype(str).astype(int)
      # Get number of pages
      self.max_page=math.ceil(len(self.data_df.index)/count)
      # Set data and display columns for updates and output
      self.data_columns = [
                  'Ride count',
                  'Wind',
                  'Rain',
                  'Snow',
                  'Hi temp',
                  'Lo temp'
              ]
      self.display_columns = self.data_columns.copy()
      self.display_columns.insert(0, 'Timestamp')

  # return paginated data
  def get(self, page=1):
      start = count*(page-1)
      end = count*page
      return self.data_df[self.display_columns].loc[start:end]

  def get_time(self, type):
      # Return 7-day rolling average of ride count over previous year or all time
      if type == 'year' or type == 'alltime':
        # Copy data and extract the date portion of the time as a new field
        year_df = self.data_df.copy()
        year_df['Date'] = year_df['Timestamp'].dt.date
        
        # Create grouping by Date and total # of rides
        year_df = year_df.groupby(['Date'], as_index = False)['Ride count'].sum()
        # Calculate 7-day rolling average
        year_df['Rolling avg'] = year_df.iloc[:,1].rolling(window=7).mean()
        if type == 'year':  
            # Return last 365 days worth of data
            return year_df.tail(365)
        else:
            return year_df

      # Return year's worth of data for monthly reporting
      elif type == 'monthly':
        # Return previous year's data
        year = self.data_df['Year'].max()
        return self.data_df.loc[self.data_df['Year'] == year]
      # Default to week
      else:
        # Return 7 days worth of hourly data
        return self.data_df.tail(7*24)

  # Return dataframe in different formats for weather queries
  def get_weather(self, type):
      # Return total fo all ride counts by Average temp
      if type == 'temp':
        return self.data_df.groupby(['Average temp'], as_index = False)['Ride count'].sum()
      # Return average ride count by wind speed  
      elif type == 'wind':
        return self.data_df.groupby(['Wind'], as_index = False)['Ride count'].mean()
      # return 7-day rolling average of temperature by date
      elif type == 'rolling_temp':
        temp_df = self.data_df.copy()
        temp_df['Date'] = temp_df['Timestamp'].dt.date
        # Create grouping by date and average temp
        temp_df = temp_df.groupby(['Date', 'Average temp'], as_index = False).count()
        # Calculate 7-day rolling average
        temp_df['Rolling avg'] = temp_df.iloc[:,1].rolling(window=7).mean()
        return temp_df.tail(365)
      # Return 3-day rolling average of wind speed by date
      elif type == 'rolling_wind':
        wind_df = self.data_df.copy()
        wind_df['Date'] = wind_df['Timestamp'].dt.date
        # Create grouping by date and wind speed
        wind_df = wind_df.groupby(['Date', 'Wind'], as_index = False).count()
        # Calculate 3-day rolling average
        wind_df['Rolling avg'] = wind_df.iloc[:,1].rolling(window=3).mean()
        return wind_df.tail(365)
      # Return total rainfall by month
      elif type == 'rain':
        # previous year's data and group by Date
        year = self.data_df['Year'].max()
        rain_df = self.data_df.loc[self.data_df['Year'] == year]
        rain_df['Date'] = rain_df['Timestamp'].dt.date
        rain_df = rain_df.groupby(['Date', 'Rain', 'Month'], as_index = False).count()
        # Get Sum of rainfall by month
        rain_df = rain_df.groupby(['Month'], as_index = False)['Rain'].sum()
        return rain_df

  # Update dataframe row matching the selected timestamp
  def update(self, timestamp, updated_values):
      self.data_df.loc[self.data_df['Timestamp'] == timestamp, self.data_columns] = updated_values.values

  # Write dataframe to csv file  
  def to_csv(self, path):
    self.data_df.to_csv(path)

