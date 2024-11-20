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
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from huggingface_hub import restart_space
import os


# Real data
#df = get_merged_dataframe()

# Dummmy data
size = 400
data = {
    'date': pd.date_range(start='2023-01-01', periods=size, freq='D'),
    'pm25': np.random.randint(50, 150, size=size),
    'predicted_pm25': np.random.randint(50, 150, size=size)
}
df = pd.DataFrame(data)


# Page configuration

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

# Plotting
fig = figure.plot(df)
st.plotly_chart(fig, use_container_width=True)