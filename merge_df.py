import datetime
import pandas as pd
import hopsworks
import os

os.environ["HOPSWORKS_API_KEY"] = "Q1hpGzlHnrKrf4g1.kxP3EPqrvulBl7XQ8oRJE3tFaxhg2PexXjhUN8Wcgvu78uN74Sw8FtH4lZODqe3D"

project = hopsworks.login()
fs = project.get_feature_store() 


def get_merged_dataframe():

    # Get data
    monitor_fg = fs.get_or_create_feature_group(
        name='aq_predictions',
        description='Air Quality prediction monitoring',
        version=1,
        primary_key=['city','street','date','days_before_forecast_day'],
        event_time="date"
    )

    air_quality_fg = fs.get_feature_group(
        name='air_quality',
        version=1,
    )
    selected_features = air_quality_fg.select_all(['pm25', 'past_air_quality']).join(weather_fg.select(['temperature_2m_mean', 'precipitation_sum', 'wind_speed_10m_max', 'wind_direction_10m_dominant']), on=['city'])
    selected_features = selected_features.read()
    selected_features['date'] = pd.to_datetime(selected_features['date'], utc=True).dt.tz_convert(None).astype('datetime64[ns]')
    
    predicted_data = monitor_fg.read()
    predicted_data = predicted_data[['date','predicted_pm25']]
    predicted_data['date'] = predicted_data['date'].dt.tz_convert(None).astype('datetime64[ns]')
    predicted_data = predicted_data.sort_values(by=['date'], ascending=True).reset_index(drop=True)


    #get historical predicted pm25
    selected_features['predicted_pm25'] = retrieved_xgboost_model.predict(selected_features[['past_air_quality','temperature_2m_mean', 'precipitation_sum', 'wind_speed_10m_max', 'wind_direction_10m_dominant']])

    #merge data
    selected_features = selected_features[['date', 'pm25', 'predicted_pm25']]
    combined_df = pd.merge(selected_features, predicted_data,on='date', how='outer')
    combined_df['date'] =  pd.to_datetime(combined_df['date'], utc=True).dt.tz_convert(None).astype('datetime64[ns]')

    # Combine the predicted_pm25_x and predicted_pm25_y columns into one
    combined_df['predicted_pm25'] = combined_df['predicted_pm25_x'].combine_first(combined_df['predicted_pm25_y'])

    # Drop the individual columns after merging
    combined_df = combined_df.drop(columns=['predicted_pm25_x', 'predicted_pm25_y'])

    return combined_df

print(get_merged_dataframe())