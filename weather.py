import requests
import logging

logger = logging.getLogger('bike-share-predict')

class Weather:

  # Set default location to Washington Dulles Internation airport
  def __init__(self, api_key, lat = "38.93", lon = "-77.45"):
      
      self.api_key = api_key
      # Set URL to onecall API that can return different weather sets
      self.api_url = "https://api.openweathermap.org/data/2.5/onecall"
      
      self.latitude = lat
      self.longitude = lon

  # Return the forecast x days from the current date (0-7)
  # Defaults to tomorrow and imperial units
  def get_daily_forecast(self, day: int = 1, units = 'imperial'):
    
    if  0 <= day <= 7:
      # Configure query parameters
      query_params = {
        'lat': self.latitude,
        'lon': self.longitude,
        # exclude all weather info but daily forecast
        'exclude': 'current,minutely,hourly,alerts',
        'appid': self.api_key,
        'units': units
      }

      # Send the API request and parse json for the requested day
      response = requests.get(self.api_url, 
            params=query_params).json()['daily'][day]

      forecast = dict()

      forecast['temp_max'] = round(response['temp']['min'], 1)
      forecast['temp_min'] = round(response['temp']['max'], 1)
      forecast['wind_speed'] = round(response['wind_speed'], 1)
      try:
        forecast['rain'] = self.__mm_to_inch(response['rain'])
      except KeyError:
        forecast['rain'] = 0.0


      return forecast

    else:
      logger.warning("Requested forecast day outside of available range (0-7 days)")
      return "Forecast not found"
  
  # mm to inch conversion rounded to two decimal places
  def __mm_to_inch(self, mm):
    return round(mm / 25.4, 2)