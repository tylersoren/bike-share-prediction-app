import pandas as pd

import math

# Set static number of rows to return for queries
count = 50
class BikeData:

  def __init__(self, summary_file):

      self.summary_df = pd.read_csv(
            filepath_or_buffer=summary_file,  
            parse_dates=[1])
      
      # Get number of pages
      self.max_page=math.ceil(len(self.summary_df.index)/count)
      # Set data and display columns for updates and output
      self.data_columns = [
                  'Ride count',
                  'AWND',
                  'PRCP',
                  'TMAX',
                  'TMIN'
              ]
      self.display_columns = self.data_columns.copy()
      self.display_columns.insert(0, 'Timestamp')


  def get_summary(self, page=1):
      start = count*(page-1)
      end = count*page
      return self.summary_df[self.display_columns].loc[start:end]

  def update_summary(self, timestamp, updated_values):
      self.summary_df.loc[self.summary_df['Timestamp'] == timestamp, self.data_columns] = updated_values.values

