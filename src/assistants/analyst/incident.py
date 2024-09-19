import pandas as pd
import plotly.subplots as sp
import plotly.graph_objects as go
import pydeck as pdk
from src.assistants.analyst.utils import get_pin_layer, MapDisplay


def prune_data(source_file = "./data/Wildland_Fire_Incident_Locations.csv"):
    data = pd.read_csv(source_file)
    data = data[["X", "Y", "IncidentTypeCategory", "FireDiscoveryDateTime"]]
    # change DateTime to year, month
    data["FireDiscoveryDateTime"] = pd.to_datetime(data["FireDiscoveryDateTime"])
    data["year"] = data["FireDiscoveryDateTime"].dt.year
    data["month"] = data["FireDiscoveryDateTime"].dt.month
    data = data[data["IncidentTypeCategory"] == "WF"]
    # change X to lon, Y to lat
    data = data[["X", "Y", "year", "month"]]
    data.columns = ["lon", "lat", "year", "month"]
    data.to_csv("./data/Wildland_Fire_Incident_Locations_pruned.csv", index=False)


import pandas as pd
from geopy.distance import geodesic

def extract_historical_fire_data(lat, lon, start_year=2015, end_year=2023, source_file="./data/Wildland_Fire_Incident_Locations_pruned.csv"):
    '''
    Finds all fire incidents within 36 km of the given latitude and longitude, and within the given time range.
    input:
        lat: latitude of the location
        lon: longitude of the location
        start_year: the start year of the historical data, must be later than 2015; 
        end_year: the end year of the historical data, must be earlier than 2023;
        source_file: the source file of the historical data
    '''

    # check if the input is valid
    assert start_year >= 2015, "start_year must be later than 2015"
    assert end_year <= 2023, "end_year must be earlier than 2023"
    assert start_year <= end_year, "start_year must be earlier than end_year"

    # Load data
    data = pd.read_csv(source_file)
    
    # Filter data by year
    data = data[(data["year"] >= start_year) & (data["year"] <= end_year)]

    max_distance_km = 36

    # Calculate distances
    distances = data.apply(lambda row: geodesic((lat, lon), (row['lat'], row['lon'])).kilometers, axis=1)
    
    # Filter data based on distance
    data = data[distances <= max_distance_km]

    return data

import streamlit as st

def recent_fire_incident_data(lat, lon, start_year=2015, end_year=2023):
    data = extract_historical_fire_data(lat, lon, start_year, end_year)
    if type(data) == str:
        return data  + " Please try again."
    
    # Count of incidents per year, sorted by year
    incidents_per_year = data['year'].value_counts().sort_index()

    # Count of incidents per month, sorted by month
    incidents_per_month = data['month'].value_counts().sort_index()
    # Assuming you have two DataFrames incidents_per_year and incidents_per_month

    # Create subplots with two rows and one column
    fig = sp.make_subplots(rows=2, cols=1, shared_xaxes=False, subplot_titles=("Wildfire Incidents per Year", "Wildfire Incidents per Month, Aggregated Across Years"))

    # Add the first line chart to the first subplot
    fig.add_trace(go.Scatter(x=incidents_per_year.index, y=incidents_per_year, mode='lines', name='Yearly Incidents'), row=1, col=1)

    # Add the second line chart to the second subplot
    fig.add_trace(go.Scatter(x=incidents_per_month.index, y=incidents_per_month, mode='lines', name='Monthly Incidents'), row=2, col=1)

    # Update subplot titles and labels
    fig.update_layout(title_text=f"Wildfire Incidents within 36 km (22 miles) of the Location (lat: {lat}, lon: {lon}) ")
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=2, col=1)

    # Summary of incidents
    summary = f"The number of wildfire incidents within 36 km (22 miles) of the location (lat: {lat}, lon: {lon}) from {start_year} to {end_year} are as follows:\n\nIncidents per Year:\n{incidents_per_year}\n\nIncidents per Month:\n{incidents_per_month}\n"

    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=8,
        pitch=0
    )

    icon_layer = get_pin_layer(lat, lon)

    layer = pdk.Layer(
        'ScatterplotLayer',
        data,
        get_position='[lon, lat]',
        get_radius=500,
        get_color=[255, 0, 0, 160],
        pickable=True
    )

    # Render the map
    maps = pdk.Deck(
        initial_view_state=view_state,
        layers=[layer, icon_layer],
        tooltip={"text": "{year}-{month}"},
        map_style = 'mapbox://styles/mapbox/light-v10'
    )

    maps = [f"The Fire Incident Records (shown in red dots) within 36 km (22 miles) of the location (lat: {lat}, lon: {lon})" , MapDisplay(maps)]

    return summary, maps, [fig]
    
if __name__ == "__main__":
    #prune_data()
    summary, maps, [fig] = recent_fire_incident_data(33.9534, -117.3962, 2016, 2022)