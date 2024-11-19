import streamlit as st
import pandas as pd
import numpy as np

st.title('Lahore Air Quality!')
st.subheader('Particle matter, diameter < 2.5 micrometers (PM2.5)')

### Load data

import datetime
import hopsworks
from functions import util
import os
import pickle

if __name__ == "__main__":
 
    pickle_file_path = 'air_quality_df.pkl'

    with open(pickle_file_path, 'rb') as file:
        st.session_state.df = pickle.load(file)

    st.line_chart(st.session_state.df,x='date',y='pm25')
