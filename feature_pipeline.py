#!/usr/bin/env python
# coding: utf-8

# <span style="font-width:bold; font-size: 3rem; color:#333;">- Part 02: Daily Feature Pipeline for Air Quality (aqicn.org) and weather (openmeteo)</span>
# 
# ## 🗒️ This notebook is divided into the following sections:
# 1. Download and Parse Data
# 2. Feature Group Insertion
# 
# 
# __This notebook should be scheduled to run daily__
# 
# In the book, we use a GitHub Action stored here:
# [.github/workflows/air-quality-daily.yml](https://github.com/featurestorebook/mlfs-book/blob/main/.github/workflows/air-quality-daily.yml)
# 
# However, you are free to use any Python Orchestration tool to schedule this program to run daily.

# ### <span style='color:#ff5f27'> 📝 Imports

# In[1]:


import datetime
import time
import requests
import pandas as pd
import hopsworks
from functions import util
import json
import os
import warnings
warnings.filterwarnings("ignore")


# ## <span style='color:#ff5f27'> 🌍 Get the Sensor URL, Country, City, Street names from Hopsworks </span>
# 
# __Update the values in the cell below.__
# 
# __These should be the same values as in notebook 1 - the feature backfill notebook__
# 

# In[2]:


# If you haven't set the env variable 'HOPSWORKS_API_KEY', then uncomment the next line and enter your API key
# os.environ["HOPSWORKS_API_KEY"] = ""

project = hopsworks.login()
api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')
project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 
secrets = util.secrets_api(project.name)

# This line will fail if you have not registered the AQI_API_KEY as a secret in Hopsworks
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

location_str


# ### <span style="color:#ff5f27;"> 🔮 Get references to the Feature Groups </span>

# In[3]:


# Retrieve feature groups
air_quality_fg = fs.get_feature_group(
    name='air_quality',
    version=1,
)
weather_fg = fs.get_feature_group(
    name='weather',
    version=1,
)


# ---

# ## <span style='color:#ff5f27'> 🌫 Retrieve Today's Air Quality data (PM2.5) from the AQI API</span>
# 

# In[4]:


import requests
import pandas as pd

aq_today_df = util.get_pm25(aqicn_url, country, city, street, today, AQI_API_KEY)
# aq_today_df = util.get_pm25(aqicn_url, country, city, street, "2024-11-05", AQI_API_KEY)
aq_today_df['date'] = pd.to_datetime(aq_today_df['date']).dt.date
aq_today_df


# In[5]:


aq_today_df.info()


# In[24]:


from datetime import timedelta
# Generate a list of dates for the past three days (including today)
dates_list = [pd.to_datetime(today - timedelta(days=i)).tz_localize('UTC') for i in range(1,4)]  # [0, 1, 2, 3]

print("Dates to filter:", dates_list)


# In[9]:


selected_features = air_quality_fg.select(['pm25']).join(weather_fg.select_all(), on=['city'])
selected_features = selected_features.read()
# filtered_df = selected_features[selected_features['date'].isin(dates_list)]

selected_features[selected_features['date'] <= dates_list[0]][selected_features['date'] >= dates_list[2]]

# In[17]:


past_3_day_mean = selected_features[selected_features['date'] <= dates_list[0]][selected_features['date'] >= dates_list[2]]['pm25'].mean()


# In[18]:


import numpy as np
past_3_day_mean = np.float64(past_3_day_mean)


# In[19]:


aq_today_df['past_air_quality'] = past_3_day_mean


# ## <span style='color:#ff5f27'> 🌦 Get Weather Forecast data</span>

# In[20]:


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


# In[21]:


daily_df.info()


# ## <span style="color:#ff5f27;">⬆️ Uploading new data to the Feature Store</span>

# In[22]:


# Insert new data
air_quality_fg.insert(aq_today_df)


# In[23]:


# Insert new data
weather_fg.insert(daily_df)


# ## <span style="color:#ff5f27;">⏭️ **Next:** Part 03: Training Pipeline
#  </span> 
# 
# In the following notebook you will read from a feature group and create training dataset within the feature store
# 

# In[ ]:



