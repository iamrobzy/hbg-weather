import streamlit as st
import pandas as pd
import numpy as np
import datetime
import hopsworks
from functions import figure, util
import os
import pickle
import plotly.express as px


st.set_page_config(
    page_title="Air Quality Prediction",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Air Quality Prediction"
    }
)

st.title('Lahore Air Quality!')
st.subheader('Particle matter, diameter < 2.5 micrometers (PM2.5)')

#pickle_file_path = 'air_quality_df.pkl'
pickle_file_path = 'outcome_df.pkl'

with open(pickle_file_path, 'rb') as file:
    st.session_state.df = pickle.load(file).sort_values(by="date")

fig = figure.plot(st.session_state.df)

# Render the chart in Streamlit
st.plotly_chart(fig)