import datetime
import requests
import pandas as pd
import hopsworks
import datetime 
from pathlib import Path
from functions import util
import json
import re
import os
import warnings
import pandas as pd

api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')

project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 
secrets = util.secrets_api(project.name)

AQI_API_KEY = secrets.get_secret("AQI_API_KEY").value
location_str = secrets.get_secret("SENSOR_LOCATION_JSON").value
location = json.loads(location_str)

country=location['country']
city=location['city']
street=location['street']
aqicn_url=location['aqicn_url']
latitude=location['latitude']
longitude=location['longitude']

today = datetime.date.today()

# Retrieve feature groups
air_quality_fg = fs.get_feature_group(
    name='air_quality',
    version=1,
)
weather_fg = fs.get_feature_group(
    name='weather',
    version=1,
)

aq_today_df = util.get_pm25(aqicn_url, country, city, street, today, AQI_API_KEY)
#aq_today_df = util.get_pm25(aqicn_url, country, city, street, "2024-11-15", AQI_API_KEY)
aq_today_df['date'] = pd.to_datetime(aq_today_df['date']).dt.date
aq_today_df

# Get weather forecast data

hourly_df = util.get_hourly_weather_forecast(city, latitude, longitude)
hourly_df = hourly_df.set_index('date')

# We will only make 1 daily prediction, so we will replace the hourly forecasts with a single daily forecast
# We only want the daily weather data, so only get weather at 12:00
daily_df = hourly_df.between_time('11:59', '12:01')
daily_df = daily_df.reset_index()
daily_df['date'] = pd.to_datetime(daily_df['date']).dt.date
daily_df['date'] = pd.to_datetime(daily_df['date'])
# daily_df['date'] = daily_df['date'].astype(str)
daily_df['city'] = city
daily_df