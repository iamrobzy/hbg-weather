import streamlit as st
import datetime

today = datetime.date.today()


def plot(df, n=10):
    import plotly.express as px

    # Order: prev pred, future pred, real
    line_colors = ['tomato', 'steelblue', 'limegreen']

    # Extract the x-axis values (dates) from the dataframe
    x_values = df["date"]

    # Define your colors, labels, and ranges
    colors = ['green', 'yellow', 'orange', 'red', 'purple', 'darkred']
    labels = ['Good', 'Moderate', 'Unhealthy for Some', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    ranges = [(1, 49), (50, 99), (100, 149), (150, 199), (200, 299), (300, 500)]  # Avoid 0 for log scale

    # Create the Plotly Express line chart for actual pm25
    fig = px.line(
        df.iloc[:-n],  # Exclude the last n points
        x="date", 
        y="pm25", 
        markers=True,
        line_shape='linear'
    )
    fig.update_traces(line=dict(color=line_colors[2]), name='Actual', showlegend=True)

    # Add the predicted pm25 line in two segments
    fig.add_scatter(
        x=df["date"][:-n], 
        y=df["predicted_pm25"][:-n], 
        mode='lines+markers', 
        name='Past prediction', 
        line=dict(color=line_colors[0], width=3), 
        marker=dict(size=10)
    )

    fig.add_scatter(
        x=df["date"][-n:], 
        y=df["predicted_pm25"][-n:], 
        mode='lines+markers', 
        name='Future prediction', 
        line=dict(color=line_colors[1], width=3, dash='dot'), 
        marker=dict(size=10)
    )
    # Add a dotted line connecting past predicted pm25 to future predicted pm25
    fig.add_scatter(
        x=[df["date"].iloc[-n-1], df["date"].iloc[-n]], 
        y=[df["predicted_pm25"].iloc[-n-1], df["predicted_pm25"].iloc[-n]], 
        mode='lines', 
        name='Connecting Line', 
        line=dict(color=line_colors[1], width=3, dash='dot'),
        showlegend=False  # Remove from legend
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

    label_font_size = 26
    ticks_font_size = 20

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
                font=dict(size=label_font_size)  # Increase font size for the x-axis label
            ),
            tickfont=dict(size=ticks_font_size)  # Increase font size for x-axis numbers
        ),
        yaxis=dict(
            title=dict(
                text="log PM2.5",  # Set y-axis label
                font=dict(size=label_font_size)  # Increase font size for the y-axis label
            ),
            type="log",  # Set y-axis to logarithmic scale
            fixedrange=True,  # Disable vertical panning/zooming
            tickfont=dict(size=ticks_font_size)  # Increase font size for y-axis numbers
        ),
        autosize=True,
        width=2100,
        height=900,
        hoverlabel=dict(
            font_size=20  # Increase hover label font size
        )
    )

    return fig