import gradio as gr
import pandas as pd
import numpy as np
import random
import os 
import hopsworks

from datetime import datetime, timedelta
now = datetime.now()

api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')

project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 

air_quality_fg = fs.get_feature_group(
    name='air_quality',
    version=1,
)
air_quality_df = air_quality_fg.read()
air_quality_df

print(air_quality_df.info())
print(air_quality_df)

with gr.Blocks() as demo:
    gr.Markdown("Helsingborg Air Quality Forecast")
    start_date = gr.Date(label="Start Date", value=(now - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = gr.Date(label="End Date", value=now.strftime('%Y-%m-%d'))
    
    def filter_data(start, end):
        mask = (air_quality_df['date'] >= start) & (air_quality_df['date'] <= end)
        return air_quality_df.loc[mask]
    
    filtered_data = gr.DataFrame(filter_data, inputs=[start_date, end_date], outputs="dataframe")
    gr.LinePlot(filtered_data, x="date", y="pm25")

demo.launch()