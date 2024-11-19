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
warnings.filterwarnings("ignore")


# ### IF YOU WANT TO WIPE OUT ALL OF YOUR FEATURES AND MODELS, run the cell below

# If you haven't set the env variable 'HOPSWORKS_API_KEY', then uncomment the next line and enter your API key
# os.environ["HOPSWORKS_API_KEY"] = ""
proj = hopsworks.login()
util.purge_project(proj)


csv_file="data/pakistan-lahore-cantonment.csv"
util.check_file_path(csv_file)


# In[22]:


# TODO: Change these values to point to your Sensor
country="pakistan"
city = "lahore"
street = "pakistan-lahore-cantonment"
aqicn_url="https://api.waqi.info/feed/A74005"

# This API call may fail if the IP address you run this notebook from is blocked by the Nominatim API
# If this fails, lookup the latitude, longitude using Google and enter the values here.
latitude, longitude = util.get_city_coordinates(city)
today = datetime.date.today()


aqi_api_key_file = 'data/aqi-api-key.txt'
util.check_file_path(aqi_api_key_file)

with open(aqi_api_key_file, 'r') as file:
    AQI_API_KEY = file.read().rstrip()

# ## Hopsworks API Key
# You need to have registered an account on app.hopsworks.ai.
# You will be prompted to enter your API key here, unless you set it as the environment variable HOPSWORKS_API_KEY (my preffered approach).

# with open('../../data/hopsworks-api-key.txt', 'r') as file:
#     os.environ["HOPSWORKS_API_KEY"] = file.read().rstrip()
    
project = hopsworks.login()

secrets = util.secrets_api(project.name)
try:
    secrets.create_secret("AQI_API_KEY", AQI_API_KEY)
except hopsworks.RestAPIError:
    AQI_API_KEY = secrets.get_secret("AQI_API_KEY").value


# ### Validate that the AQI_API_KEY you added earlier works
# 
# The cell below should print out something like:

try:
    aq_today_df = util.get_pm25(aqicn_url, country, city, street, today, AQI_API_KEY)
except hopsworks.RestAPIError:
    print("It looks like the AQI_API_KEY doesn't work for your sensor. Is the API key correct? Is the sensor URL correct?")

aq_today_df.head()

df = pd.read_csv(csv_file,  parse_dates=['date'], skipinitialspace=True)

# These commands will succeed if your CSV file didn't have a `median` or `timestamp` column
df = df.rename(columns={"median": "pm25"})
# df = df.rename(columns={"timestamp": "date"})
df['date'] = pd.to_datetime(df['date']).dt.date

df_aq = df[['date', 'pm25']]
df_aq['pm25'] = df_aq['pm25'].astype('float32')

# Cast the pm25 column to be a float32 data type
df_aq.info()

# It will make the model training easier if there is no missing data in the rows, so we drop any rows with missing data.

df_aq.dropna(inplace=True)

# Your sensor may have columns we won't use, so only keep the date and pm25 columns
# If the column names in your DataFrame are different, rename your columns to `date` and `pm25`
df_aq['country']=country
df_aq['city']=city
df_aq['street']=street
df_aq['url']=aqicn_url
df_aq

df_aq =df_aq.set_index("date")
df_aq['past_air_quality'] = df_aq['pm25'].rolling(3).mean()
df_aq["past_air_quality"] = df_aq["past_air_quality"].fillna(df_aq["past_air_quality"].mean())
df_aq = df_aq.reset_index()
df_aq.date.describe()

# 
# https://open-meteo.com/en/docs/historical-weather-api#hourly=&daily=temperature_2m_mean,precipitation_sum,wind_speed_10m_max,wind_direction_10m_dominant
# 
# We will download the historical weather data for your `city` by first extracting the earliest date from your DataFrame containing the historical air quality measurements.
# 
# We will download all daily historical weather data measurements for your `city` from the earliest date in your air quality measurement DataFrame. It doesn't matter if there are missing days of air quality measurements. We can store all of the daily weather measurements, and when we build our training dataset, we will join up the air quality measurements for a given day to its weather features for that day. 
# 
# The weather features we will download are:
# 
#  * `temperature (average over the day)`
#  * `precipitation (the total over the day)`
#  * `wind speed (average over the day)`
#  * `wind direction (the most dominant direction over the day)`
# 

earliest_aq_date = pd.Series.min(df_aq['date'])
earliest_aq_date = earliest_aq_date.strftime('%Y-%m-%d')
earliest_aq_date

weather_df = util.get_historical_weather(city, earliest_aq_date, str(today), latitude, longitude)
# weather_df = util.get_historical_weather(city, earliest_aq_date, "2024-11-05", latitude, longitude)
weather_df.info()


# ## <span style='color:#ff5f27'> 🌍 STEP 10: Define Data Validation Rules </span>
# 
# We will validate the air quality measurements (`pm25` values) before we write them to Hopsworks.
# 
# We define a data validation rule (an expectation in Great Expectations) that ensures that `pm25` values are not negative or above the max value available by the sensor.
# 
# We will attach this expectation to the air quality feature group, so that we validate the `pm25` data every time we write a DataFrame to the feature group. We want to prevent garbage-in, garbage-out.



import great_expectations as ge
aq_expectation_suite = ge.core.ExpectationSuite(
    expectation_suite_name="aq_expectation_suite"
)

aq_expectation_suite.add_expectation(
    ge.core.ExpectationConfiguration(
        expectation_type="expect_column_min_to_be_between",
        kwargs={
            "column":"pm25",
            "min_value":-0.1,
            "max_value":500.0,
            "strict_min":True
        }
    )
)


# ## Expectations for Weather Data
# Here, we define an expectation for 2 columns in our weather DataFrame - `precipitation_sum` and `wind_speed_10m_max`, where we expect both values to be greater than zero, but less than 1000.

# In[56]:


import great_expectations as ge
weather_expectation_suite = ge.core.ExpectationSuite(
    expectation_suite_name="weather_expectation_suite"
)

def expect_greater_than_zero(col):
    weather_expectation_suite.add_expectation(
        ge.core.ExpectationConfiguration(
            expectation_type="expect_column_min_to_be_between",
            kwargs={
                "column":col,
                "min_value":-0.1,
                "max_value":1000.0,
                "strict_min":True
            }
        )
    )
expect_greater_than_zero("precipitation_sum")
expect_greater_than_zero("wind_speed_10m_max")
# In[57]:


fs = project.get_feature_store() 


# #### Save country, city, street names as a secret
# 
# These will be downloaded from Hopsworks later in the (1) daily feature pipeline and (2) the daily batch inference pipeline

# In[58]:


dict_obj = {
    "country": country,
    "city": city,
    "street": street,
    "aqicn_url": aqicn_url,
    "latitude": latitude,
    "longitude": longitude
}

# Convert the dictionary to a JSON string
str_dict = json.dumps(dict_obj)

try:
    secrets.create_secret("SENSOR_LOCATION_JSON", str_dict)
except hopsworks.RestAPIError:
    print("SENSOR_LOCATION_JSON already exists. To update, delete the secret in the UI (https://c.app.hopsworks.ai/account/secrets) and re-run this cell.")
    existing_key = secrets.get_secret("SENSOR_LOCATION_JSON").value
    print(f"{existing_key}")


# ### <span style="color:#ff5f27;"> 🔮 STEP 12: Create the Feature Groups and insert the DataFrames in them </span>

# ### <span style='color:#ff5f27'> 🌫 Air Quality Data
#     
#  1. Provide a name, description, and version for the feature group.
#  2. Define the `primary_key`: we have to select which columns uniquely identify each row in the DataFrame - by providing them as the `primary_key`. Here, each air quality sensor measurement is uniquely identified by `country`, `street`, and  `date`.
#  3. Define the `event_time`: We also define which column stores the timestamp or date for the row - `date`.
#  4. Attach any `expectation_suite` containing data validation rules

# In[59]:


air_quality_fg = fs.get_or_create_feature_group(
    name='air_quality',
    description='Air Quality characteristics of each day',
    version=1,
    primary_key=['city', 'street', 'date'],
    event_time="date",
    expectation_suite=aq_expectation_suite
)


# #### Insert the DataFrame into the Feature Group

# In[60]:


air_quality_fg.insert(df_aq)


# #### Enter a description for each feature in the Feature Group

# In[61]:


air_quality_fg.update_feature_description("date", "Date of measurement of air quality")
air_quality_fg.update_feature_description("country", "Country where the air quality was measured (sometimes a city in acqcn.org)")
air_quality_fg.update_feature_description("city", "City where the air quality was measured")
air_quality_fg.update_feature_description("street", "Street in the city where the air quality was measured")
air_quality_fg.update_feature_description("pm25", "Particles less than 2.5 micrometers in diameter (fine particles) pose health risk")
air_quality_fg.update_feature_description("past_air_quality", "mean air quality of the past 3 days")


# ### <span style='color:#ff5f27'> 🌦 Weather Data
#     
#  1. Provide a name, description, and version for the feature group.
#  2. Define the `primary_key`: we have to select which columns uniquely identify each row in the DataFrame - by providing them as the `primary_key`. Here, each weather measurement is uniquely identified by `city` and  `date`.
#  3. Define the `event_time`: We also define which column stores the timestamp or date for the row - `date`.
#  4. Attach any `expectation_suite` containing data validation rules

# In[62]:


# Get or create feature group 
weather_fg = fs.get_or_create_feature_group(
    name='weather',
    description='Weather characteristics of each day',
    version=1,
    primary_key=['city', 'date'],
    event_time="date",
    expectation_suite=weather_expectation_suite
) 


# #### Insert the DataFrame into the Feature Group

# In[63]:


# Insert data
weather_fg.insert(weather_df)


# #### Enter a description for each feature in the Feature Group

# In[64]:


weather_fg.update_feature_description("date", "Date of measurement of weather")
weather_fg.update_feature_description("city", "City where weather is measured/forecast for")
weather_fg.update_feature_description("temperature_2m_mean", "Temperature in Celsius")
weather_fg.update_feature_description("precipitation_sum", "Precipitation (rain/snow) in mm")
weather_fg.update_feature_description("wind_speed_10m_max", "Wind speed at 10m abouve ground")
weather_fg.update_feature_description("wind_direction_10m_dominant", "Dominant Wind direction over the dayd")


# ## <span style="color:#ff5f27;">⏭️ **Next:** Part 02: Daily Feature Pipeline 
#  </span> 
# 

# ## <span style="color:#ff5f27;">⏭️ **Exercises:** 
#  </span> 
# 
# Extra Homework:
# 
#   * Try adding a new feature based on a rolling window of 3 days for 'pm25'
#       * This is not easy, as forecasting more than 1 day in the future, you won't have the previous 3 days of pm25 measurements.
#       * df.set_index("date").rolling(3).mean() is only the start....
#   * Parameterize the notebook, so that you can provide the `country`/`street`/`city`/`url`/`csv_file` as parameters. 
#       * Hint: this will also require making the secret name (`SENSOR_LOCATION_JSON`), e.g., add the street name as part of the secret name. Then you have to pass that secret name as a parameter when running the operational feature pipeline and batch inference pipelines.
#       * After you have done this, collect the street/city/url/csv files for all the sensors in your city or region and you make dashboards for all of the air quality sensors in your city/region. You could even then add a dashboard for your city/region, as done [here for Poland](https://github.com/erno98/ID2223).
# 
# Improve this AI System
#   * As of mid 2024, there is no API call available to download historical data from the AQIN website. You could improve this system by writing a PR to download the CSV file using Python Selenium and the URL for the sensor.
# 

# ---
