import streamlit as st
import pandas as pd
import numpy as np
import datetime
import hopsworks
from functions import figure, util
import os
import pickle
import plotly.express as px
import json

# Set up
api_key = os.getenv('HOPSWORKS_API_KEY')
project_name = os.getenv('HOPSWORKS_PROJECT')
project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 
secrets = util.secrets_api(project.name)

feature_view = fs.get_feature_view(
    name='air_quality_fv',
    version=1,
)
df = feature_view.get_batch_data(start_time=None, end_time=None, read_options=None).sort_values(by='date')
today = datetime.datetime.now() - datetime.timedelta(0)


st.set_page_config(
    page_title="Air Quality Prediction",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Air Quality Prediction"
    }
)

st.title('Lahore Air Quality')
st.subheader('Forecast and hindcast')
st.subheader('Unit: PM25 - particle matter of diameter < 2.5 micrometers')

#pickle_file_path = 'air_quality_df.pkl'
# pickle_file_path = 'outcome_df.pkl'

# with open(pickle_file_path, 'rb') as file:
#     st.session_state.df = pickle.load(file).sort_values(by="date")

fig = figure.plot(df)

# Render the chart in Streamlit
st.plotly_chart(fig)