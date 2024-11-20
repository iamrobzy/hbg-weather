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
    selected_features = air_quality_fg.select_all(['pm25'])
    selected_features = selected_features.read()
    predicted_data = monitor_fg.read()

    #filter columns
    selected_features = selected_features[['date', 'pm25']]
    predicted_data = predicted_data[['date','predicted_pm25']]
    predicted_data = predicted_data.rename(columns={"predicted_pm25" : "pm25"})
    predicted_data = predicted_data.sort_values(by=['date'], ascending=True)

    #merge the dataframes
    selected_features = selected_features.reset_index(drop=True)
    predicted_data = predicted_data.reset_index(drop=True)
    combined_df = pd.concat([selected_features, predicted_data], axis=0, ignore_index=True)
    combined_df['date'] =  pd.to_datetime(combined_df['date'], utc=True).dt.tz_convert(None).astype('datetime64[ns]')

    return combined_df

print(get_merged_dataframe())