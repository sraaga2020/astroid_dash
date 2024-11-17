import plotly.graph_objs as go
import streamlit as st
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import os

# Define NASA API endpoint and API key
API_ENDPOINT = "https://api.nasa.gov/neo/rest/v1/feed"
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")  # Use an environment variable for API key

@st.cache_data
def fetch_asteroid_data(start_date, end_date):
    params = {
        'start_date': start_date,
        'end_date': end_date,
        'api_key': API_KEY
    }
    try:
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from NASA API: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

    asteroids = []
    for date in data.get('near_earth_objects', {}):
        for asteroid in data['near_earth_objects'][date]:
            try:
                asteroids.append({
                    'name': asteroid['name'],
                    'diameter_m': asteroid['estimated_diameter']['meters']['estimated_diameter_max'],
                    'speed_kmh': float(asteroid['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']),
                    'distance_km': float(asteroid['close_approach_data'][0]['miss_distance']['kilometers']),
                    'orbiting_body': asteroid['close_approach_data'][0]['orbiting_body'],
                    'hazardous': asteroid['is_potentially_hazardous_asteroid']
                })
            except (KeyError, IndexError, ValueError):
                continue

    return pd.DataFrame(asteroids)

def run_dashboard():
    # Fetch data for the next 7 days
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    asteroid_df = fetch_asteroid_data(start_date, end_date)

    # Layout for the app
    st.markdown(
        "<h1 style='text-align: center; color: #CFCFCF;'>Asteroid Impact Simulator 🚀</h1>",
        unsafe_allow_html=True
    )

    if asteroid_df.empty:
        st.warning("No asteroid data available. Check your API key or internet connection.")
        return  # Stop execution if no data is available

    # Display Data Metrics
    st.markdown("---")
    st.subheader("Asteroid Metrics Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Asteroids", len(asteroid_df))
    col2.metric("Average Diameter (m)", f"{asteroid_df['diameter_m'].mean():.2f}")
    col3.metric("Average Speed (km/h)", f"{asteroid_df['speed_kmh'].mean():.2f}")

    # Select an Asteroid for Detailed Analysis
    st.subheader("Select an Asteroid for Detailed Analysis")
    selected_asteroid = st.selectbox("Choose an Asteroid", asteroid_df['name'].unique())
    selected_data = asteroid_df[asteroid_df['name'] == selected_asteroid]

    # Display Selected Asteroid Details
    st.markdown(f"### Asteroid Details: {selected_asteroid}")
    st.write(f"**Diameter:** {selected_data['diameter_m'].values[0]} meters")
    st.write(f"**Speed:** {selected_data['speed_kmh'].values[0]} km/h")
    st.write(f"**Distance from Earth:** {selected_data['distance_km'].values[0]} km")
    st.write(f"**Orbiting Body:** {selected_data['orbiting_body'].values[0]}")
    st.write(f"**Potentially Hazardous:** {selected_data['hazardous'].values[0]}")

    diameter = selected_data['diameter_m'].values[0]
    speed = selected_data['speed_kmh'].values[0]
    distance = selected_data['distance_km'].values[0]

    # Impact simulation logic
    impact_radius = np.log(diameter) * 10 if diameter > 0 else 0
    impact_location = [20 + np.random.uniform(-5, 5), 0 + np.random.uniform(-5, 5)]

    trace = go.Scattergeo(
        lon=[impact_location[1]],
        lat=[impact_location[0]],
        text=[f"Impact!\nDiameter: {diameter} m\nSpeed: {speed} km/h\nImpact Radius: {impact_radius:.2f} km"],
        mode="markers+text",
        marker=dict(
            size=impact_radius,
            color='red',
            opacity=0.7,
            line=dict(width=1, color='black')
        ),
        textposition="bottom center"
    )

    layout = go.Layout(
        geo=dict(
            scope='world',
            projection_type='equirectangular',
            showland=True,
            landcolor='white',
            coastlinewidth=1
        ),
        title="Asteroid Impact Simulation",
        showlegend=False
    )

    fig = go.Figure(data=[trace], layout=layout)
    st.plotly_chart(fig, use_container_width=True)

    # Add a caption about the impact
    st.markdown(
        """
        ### Impact Simulation
        Based on the asteroid's size, speed, and distance from Earth, the above simulation shows the impact location and potential damage.
        Larger asteroids with greater speeds will have more significant impacts and wider radii.
        """
    )
