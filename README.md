---
title: Air Quality Forecast
emoji: 😻
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.25.0
app_file: app_streamlit.py
pinned: false
short_description: Air quality forecasting for Lahore, Pakistan!
---

# Air Quality Monitoring for Lahore, Pakistan

### [Dashboard link](https://huggingface.co/spaces/Robzy/hbg-weather)

# Architecture & pipeline

### 1. Data sourcing

* Historical air quality measurements are collected from World Air Quality Index in .csv form.
* Historical weather data collected from Open-Meteo API client, loaded as Pandas dataframe. 

Weather data features:

 * Temperature (average over the day)
 * Pecipitation (the total over the day)
 * Wind speed (average over the day)
 * Wind direction (the most dominant direction over the day)


### 2. Backfill

* Created two feature groups are created on Hopsworks: `air_quality` and  `weather`
* Data us pre-processed and uploaded to their respective feature groups.

### 3. Feature pipeline

* Daily weather and air quality data is fetched from Open Meteo and World Air Quality Index APIs respectively, then uploaded into the feature groups. 

### 4. Training & model

* A feature view `air_quality_fv` is created on Hopsworks, which is an input/output API schema for a model.
* We train a XGBoost regression model `air_quality_xgboost_model` and save it to our model registry.

### 5. Inference pipeline

* A new feature group `aq_predictions` is created on Hopsworks.
* Upon an inference request, the forecasted features and the model are retrieved from the feature view and model regsitry respectively.
* Air quality predictions are made by inputting the forecasted features into the model, and then uploaded into the `aq_predictions` feature group.

# Dashboard & scheduling

HuggingFace's Streamlit Spaces is used to display the hindcast, forecast, and real air quality using an interactive line graph. GitHub Actions is used to call the feature and inference pipeline daily by levraging schedulin.

Note that backfilling, feature group creation and model training is only performed once



### Aknowledments

* [HuggingFace restart scheduler](https://huggingface.co/spaces/davanstrien/restart/blob/main/app.py)