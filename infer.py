import datetime
import pandas as pd
from xgboost import XGBRegressor
import hopsworks
import json
from functions import util
import os

# Set up

api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')

project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 
secrets = util.secrets_api(project.name)

AQI_API_KEY = secrets.get_secret("AQI_API_KEY").value
location_str = secrets.get_secret("SENSOR_LOCATION_JSON").value
location = json.loads(location_str)

today = datetime.datetime.now() - datetime.timedelta(0)

feature_view = fs.get_feature_view(
    name='air_quality_fv',
    version=1,
)

# Retreive model

mr = project.get_model_registry()

retrieved_model = mr.get_model(
    name="air_quality_xgboost_model",
    version=1,
)

saved_model_dir = retrieved_model.download()
retrieved_xgboost_model = XGBRegressor()
retrieved_xgboost_model.load_model(saved_model_dir + "/model.json")

# Retrieve features 

weather_fg = fs.get_feature_group(
    name='weather',
    version=1,
)

today_timestamp = pd.to_datetime(today)
batch_data = weather_fg.filter(weather_fg.date >= today_timestamp ).read()
batch_data['predicted_pm25'] = retrieved_xgboost_model.predict(
    batch_data[['temperature_2m_mean', 'precipitation_sum', 'wind_speed_10m_max', 'wind_direction_10m_dominant']])
