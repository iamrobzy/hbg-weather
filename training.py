#!/usr/bin/env python
# coding: utf-8

# # <span style="font-width:bold; font-size: 3rem; color:#333;">Training Pipeline</span>
# 
# ## 🗒️ This notebook is divided into the following sections:
# 
# 1. Select features for the model and create a Feature View with the selected features
# 2. Create training data using the feature view
# 3. Train model
# 4. Evaluate model performance
# 5. Save model to model registry

# ### <span style='color:#ff5f27'> 📝 Imports

# In[1]:


import os
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from xgboost import plot_importance
from sklearn.metrics import mean_squared_error, r2_score
import hopsworks
from functions import util

import warnings
warnings.filterwarnings("ignore")


# ## <span style="color:#ff5f27;"> 📡 Connect to Hopsworks Feature Store </span>

# In[2]:


project = hopsworks.login()
api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')
project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 
secrets = util.secrets_api(project.name)

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
# 
# ## <span style="color:#ff5f27;"> 🖍 Feature View Creation and Retrieving </span>

# In[4]:


# Select features for training data.
selected_features = air_quality_fg.select(['pm25', 'past_air_quality']).join(weather_fg.select_all(), on=['city'])
selected_features.show(10)


# In[9]:


feature_view = fs.get_or_create_feature_view(
    name='air_quality_fv',
    description="weather features with air quality as the target",
    version=1,
    labels=['pm25'],
    query=selected_features,
)

# In[10]:


start_date_test_data = "2024-03-01"
# Convert string to datetime object
test_start = datetime.strptime(start_date_test_data, "%Y-%m-%d")


# In[11]:


X_train, X_test, y_train, y_test = feature_view.train_test_split(
    test_start=test_start
)


# In[12]:


X_train


# In[13]:


# Drop the index columns - 'date' (event_time) and 'city' (primary key)

train_features = X_train.drop(['date', 'city'], axis=1)
test_features = X_test.drop(['date', 'city'], axis=1)


# In[14]:


y_train


# The `Feature View` is now saved in Hopsworks and you can retrieve it using `FeatureStore.get_feature_view(name='...', version=1)`.

# ---

# ## <span style="color:#ff5f27;">🧬 Modeling</span>
# 
# We will train a regression model to predict pm25 using our 4 features (wind_speed, wind_dir, temp, precipitation)

# In[16]:


# Creating an instance of the XGBoost Regressor
xgb_regressor = XGBRegressor()

# Fitting the XGBoost Regressor to the training data
xgb_regressor.fit(train_features, y_train)


# In[17]:


# Predicting target values on the test set
y_pred = xgb_regressor.predict(test_features)

# Calculating Mean Squared Error (MSE) using sklearn
mse = mean_squared_error(y_test.iloc[:,0], y_pred)
print("MSE:", mse)

# Calculating R squared using sklearn
r2 = r2_score(y_test.iloc[:,0], y_pred)
print("R squared:", r2)


# In[18]:


df = y_test
df['predicted_pm25'] = y_pred


# In[19]:


df['date'] = X_test['date']
df = df.sort_values(by=['date'])
df.head(5)


# In[20]:


# Creating a directory for the model artifacts if it doesn't exist
model_dir = "air_quality_model"
if not os.path.exists(model_dir):
    os.mkdir(model_dir)
images_dir = model_dir + "/images"
if not os.path.exists(images_dir):
    os.mkdir(images_dir)


# In[21]:


file_path = images_dir + "/pm25_hindcast.png"
plt = util.plot_air_quality_forecast("lahore", "pakistan-lahore-cantonment", df, file_path, hindcast=True) 
plt.show()


# In[22]:


# Plotting feature importances using the plot_importance function from XGBoost
plot_importance(xgb_regressor, max_num_features=5)
feature_importance_path = images_dir + "/feature_importance.png"
plt.savefig(feature_importance_path)
plt.show()


# ---

# ## <span style='color:#ff5f27'>🗄 Model Registry</span>
# 
# One of the features in Hopsworks is the model registry. This is where you can store different versions of models and compare their performance. Models from the registry can then be served as API endpoints.

# ### <span style="color:#ff5f27;">⚙️ Model Schema</span>

# The model needs to be set up with a [Model Schema](https://docs.hopsworks.ai/machine-learning-api/latest/generated/model_schema/), which describes the inputs and outputs for a model.
# 
# A Model Schema can be automatically generated from training examples, as shown below.

# In[23]:


from hsml.schema import Schema
from hsml.model_schema import ModelSchema

# Creating input and output schemas using the 'Schema' class for features (X) and target variable (y)
input_schema = Schema(X_train)
output_schema = Schema(y_train)

# Creating a model schema using 'ModelSchema' with the input and output schemas
model_schema = ModelSchema(input_schema=input_schema, output_schema=output_schema)

# Converting the model schema to a dictionary representation
schema_dict = model_schema.to_dict()


# In[24]:


# Saving the XGBoost regressor object as a json file in the model directory
xgb_regressor.save_model(model_dir + "/model.json")


# In[25]:


res_dict = { 
        "MSE": str(mse),
        "R squared": str(r2),
    }


# In[26]:


mr = project.get_model_registry()

# Creating a Python model in the model registry named 'air_quality_xgboost_model'

aq_model = mr.python.create_model(
    name="air_quality_xgboost_model", 
    metrics= res_dict,
    model_schema=model_schema,
    input_example=X_test.sample().values, 
    description="Air Quality (PM2.5) predictor",
)

# Saving the model artifacts to the 'air_quality_model' directory in the model registry
aq_model.save(model_dir)


# ---
# ## <span style="color:#ff5f27;">⏭️ **Next:** Part 04: Batch Inference</span>
# 
# In the following notebook you will use your model for Batch Inference.
# 

# In[ ]:



