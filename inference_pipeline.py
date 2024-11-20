#!/usr/bin/env python
# coding: utf-8

# # <span style="font-width:bold; font-size: 3rem; color:#1EB182;"> **Air Quality** </span><span style="font-width:bold; font-size: 3rem; color:#333;">- Part 04: Batch Inference</span>
# 
# ## 🗒️ This notebook is divided into the following sections:
# 
# 1. Download model and batch inference data
# 2. Make predictions, generate PNG for forecast
# 3. Store predictions in a monitoring feature group adn generate PNG for hindcast

# ## <span style='color:#ff5f27'> 📝 Imports

# In[1]:


import datetime
import pandas as pd
from xgboost import XGBRegressor
import hopsworks
import json
from functions import util
import os


# In[2]:


today = datetime.datetime.now() - datetime.timedelta(0)
tomorrow = today + datetime.timedelta(days = 1)
today


# ## <span style="color:#ff5f27;"> 📡 Connect to Hopsworks Feature Store </span>

# In[3]:


# os.environ["HOPSWORKS_API_KEY"] = ""

api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')
project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 

secrets = util.secrets_api(project.name)
location_str = secrets.get_secret("SENSOR_LOCATION_JSON").value
location = json.loads(location_str)
country=location['country']
city=location['city']
street=location['street']


# ## <span style="color:#ff5f27;"> ⚙️ Feature View Retrieval</span>
# 

# In[4]:


feature_view = fs.get_feature_view(
    name='air_quality_fv',
    version=1,
)


# ## <span style="color:#ff5f27;">🪝 Download the model from Model Registry</span>

# In[5]:


mr = project.get_model_registry()

retrieved_model = mr.get_model(
    name="air_quality_xgboost_model",
    version=1,
)

# Download the saved model artifacts to a local directory
saved_model_dir = retrieved_model.download()


# In[6]:


# Loading the XGBoost regressor model and label encoder from the saved model directory
# retrieved_xgboost_model = joblib.load(saved_model_dir + "/xgboost_regressor.pkl")
retrieved_xgboost_model = XGBRegressor()

retrieved_xgboost_model.load_model(saved_model_dir + "/model.json")

# Displaying the retrieved XGBoost regressor model
retrieved_xgboost_model


# In[7]:


# Access the feature names of the trained XGBoost model
feature_names = retrieved_xgboost_model.get_booster().feature_names

# Print the feature names
print("Feature names:", feature_names)


# ## <span style="color:#ff5f27;">✨ Get Weather Forecast Features with Feature View   </span>
# 
# 

# In[8]:


weather_fg = fs.get_feature_group(
    name='weather',
    version=1,
)
today_timestamp = pd.to_datetime(today)
batch_data = weather_fg.filter(weather_fg.date >= today_timestamp ).read()
batch_data


# ### Get Mean air quality for past days

# In[9]:


air_quality_fg = fs.get_feature_group(
    name='air_quality',
    version=1,
)
selected_features = air_quality_fg.select_all() #(['pm25']).join(weather_fg.select_all(), on=['city'])
selected_features = selected_features.read()


# In[10]:


selected_features = selected_features.sort_values(by='date').reset_index(drop=True)


# In[11]:


past_air_q_list = selected_features[['date', 'pm25']][-3:]['pm25'].tolist()


# In[12]:


batch_data = batch_data.sort_values(by='date').reset_index(drop=True)


# In[13]:


batch_data['past_air_quality'] = None


# In[14]:


batch_data


# ### <span style="color:#ff5f27;">🤖 Making the predictions</span>

# In[15]:


# Initialize an empty list to store predictions
predictions = []

# Iterate through each row of the DataFrame
for index, row in batch_data.iterrows():
    past_air_quality_mean = sum(past_air_q_list)/3
    # Extract the feature values for prediction as a 1D array
    features = row[['past_air_quality', 'temperature_2m_mean', 'precipitation_sum', 
                    'wind_speed_10m_max', 'wind_direction_10m_dominant']].values
    
    # Reshape features to a 2D array (required by XGBoost's predict method)
    features = features.reshape(1, -1)
    
    # Make a prediction for the row
    prediction = retrieved_xgboost_model.predict(features)
    
    # Append the prediction to the list
    predictions.append(prediction[0])
    past_air_q_list.append(prediction[0])
    past_air_q_list = past_air_q_list[1:]

    # print(past_air_q_list)
    batch_data.loc[index,'past_air_quality'] = past_air_quality_mean

# Add the predictions as a new column in the DataFrame
batch_data['predicted_pm25'] = predictions

# Display the updated DataFrame
batch_data


# In[16]:


# batch_data['predicted_pm25'] = retrieved_xgboost_model.predict(
#     batch_data[['temperature_2m_mean', 'precipitation_sum', 'wind_speed_10m_max', 'wind_direction_10m_dominant']])
# batch_data


# In[17]:


batch_data.info()


# ### <span style="color:#ff5f27;">🤖 Saving the predictions (for monitoring) to a Feature Group</span>

# In[18]:


batch_data['street'] = street
batch_data['city'] = city
batch_data['country'] = country
# Fill in the number of days before the date on which you made the forecast (base_date)
batch_data['days_before_forecast_day'] = range(1, len(batch_data)+1)
batch_data = batch_data.sort_values(by=['date'])
batch_data['date'] = batch_data['date'].dt.tz_convert(None).astype('datetime64[ns]')
batch_data


# In[19]:


batch_data.info()


# ### Create Forecast Graph
# Draw a graph of the predictions with dates as a PNG and save it to the github repo
# Show it on github pages

# In[20]:


file_path = "img/pm25_forecast.png"
plt = util.plot_air_quality_forecast(city, street, batch_data, file_path)
plt.show()


# In[21]:


# Get or create feature group
monitor_fg = fs.get_or_create_feature_group(
    name='aq_predictions',
    description='Air Quality prediction monitoring',
    version=1,
    primary_key=['city','street','date','days_before_forecast_day'],
    event_time="date"
)


# In[22]:


monitor_fg.insert(batch_data, write_options={"wait_for_job": True})


# In[23]:


# We will create a hindcast chart for  only the forecasts made 1 day beforehand
monitoring_df = monitor_fg.filter(monitor_fg.days_before_forecast_day == 1).read()
monitoring_df


# In[24]:


air_quality_fg = fs.get_feature_group(
    name='air_quality',
    version=1,
)
air_quality_df = air_quality_fg.read()
air_quality_df


# In[25]:


air_quality_df['date']


# In[26]:


monitoring_df['date']


# In[27]:


air_quality_df['date'] = pd.to_datetime(air_quality_df['date'])
monitoring_df['date'] = monitoring_df['date'].dt.tz_convert(None).astype('datetime64[ns]')


# In[28]:


weather_fg.read()


# In[29]:


air_quality_df


# In[30]:


monitor_fg.read()


# In[31]:


outcome_df = air_quality_df[['date', 'pm25']]
preds_df =  monitoring_df[['date', 'predicted_pm25']]

hindcast_df = pd.merge(preds_df, outcome_df, on="date")
hindcast_df = hindcast_df.sort_values(by=['date'])

# If there are no outcomes for predictions yet, generate some predictions/outcomes from existing data
if len(hindcast_df) == 0:
    hindcast_df = util.backfill_predictions_for_monitoring(weather_fg, air_quality_df, monitor_fg, retrieved_xgboost_model)
hindcast_df


# ### Plot the Hindcast comparing predicted with forecasted values (1-day prior forecast)
# 
# __This graph will be empty to begin with - this is normal.__
# 
# After a few days of predictions and observations, you will get data points in this graph.

# In[32]:


file_path = "img/pm25_hindcast_1day.png"
plt = util.plot_air_quality_forecast(city, street, hindcast_df, file_path, hindcast=True)
plt.show()
# %%
