import streamlit as st
import pandas as pd
import numpy as np
import datetime
import hopsworks
from functions import util
import os
import pickle
import plotly.express as px


st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

st.title('Lahore Air Quality!')
st.subheader('Particle matter, diameter < 2.5 micrometers (PM2.5)')

pickle_file_path = 'air_quality_df.pkl'

with open(pickle_file_path, 'rb') as file:
    st.session_state.df = pickle.load(file).sort_values(by="date")

# st.line_chart(st.session_state.df,x='date',y='pm25',width=2000,height=800,use_container_width=False)

# Define the number of last elements to show
n = 10

# Extract the x-axis values (dates) from the dataframe
x_values = st.session_state.df["date"]

# Define your colors, labels, and ranges
colors = ['green', 'yellow', 'orange', 'red', 'purple', 'darkred']
labels = ['Good', 'Moderate', 'Unhealthy for Some', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
ranges = [(1, 49), (50, 99), (100, 149), (150, 199), (200, 299), (300, 500)]  # Avoid 0 for log scale

# Create the Plotly Express line chart
fig = px.line(
    st.session_state.df, 
    x="date", 
    y="pm25", 
    markers=True
)

# Add background color rectangles using `shapes`
shapes = []
for i, (start, end) in enumerate(ranges):
    shapes.append(
        dict(
            type="rect",  # Add a rectangle
            xref="paper",  # Extend the rectangle across the entire x-axis
            yref="y",      # Anchor the rectangle to the y-axis
            x0=0,          # Start from the left (x0 in paper coordinates)
            x1=1,          # End at the right (x1 in paper coordinates)
            y0=start,      # Start of the y-range
            y1=end,        # End of the y-range
            fillcolor=colors[i],  # Background color
            opacity=0.2,          # Transparency level
            layer="below",        # Place behind the data
            line_width=0          # No border
        )
    )

# Update the layout and traces for customization
fig.update_traces(
    marker=dict(size=10),  # Increase marker size
    line=dict(width=3)     # Make the line thicker
)

fig.update_layout(
    shapes=shapes,  # Add the background rectangles
    xaxis=dict(
        range=[x_values.iloc[-n], x_values.iloc[-1]],  # Dynamically set the range
        title=dict(
            text="Date",  # Set x-axis label
            font=dict(size=20)  # Increase font size for the x-axis label
        ),
    ),
    yaxis=dict(
        title=dict(
            text="PM2.5 Concentration",  # Set y-axis label
            font=dict(size=20)  # Increase font size for the y-axis label
        ),
        type="log",  # Set y-axis to logarithmic scale
        fixedrange=True  # Disable vertical panning/zooming
    ),
    autosize=True,
    width=2100,
    height=900,
)

# Render the chart in Streamlit
st.plotly_chart(fig)
