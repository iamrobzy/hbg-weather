import streamlit as st
import pandas as pd
import numpy as np

st.title('Lahore Air Quality!')
st.subheader('Particle matter, diameter < 2.5 micrometers (PM2.5)')

### Load data

import datetime
import pandas as pd
import hopsworks
import datetime 
from functions import util
import os
import pandas as pd
import modal

app = modal.App('scheduler')
volume = modal.Volume.from_name("my-volume")

@app.function(schedule=modal.Period(seconds=10))
def update():
    print('Updating...')
    



if __name__ == "__main__":
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame(np.random.randn(20, 2), columns=["x", "y"])
    else:
        st.session_state.df = pd.DataFrame(
            np.random.randn(20, 3),
            columns=['a', 'b', 'c'])

    st.line_chart(st.session_state.df)