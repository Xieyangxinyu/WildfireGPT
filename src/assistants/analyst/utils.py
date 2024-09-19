import geopandas as gpd
import pydeck as pdk
from shapely.geometry import Point, mapping
from shapely.ops import transform
from geopandas import GeoDataFrame
import pandas as pd
from functools import partial
import pyproj
import streamlit as st

def create_geographic_circle(lat, lon, radius_in_km):
    local_azimuthal_projection = f"+proj=aeqd +R=6371000 +units=m +lat_0={lat} +lon_0={lon}"
    wgs84_to_aeqd = partial(
        pyproj.transform,
        pyproj.Proj('+proj=longlat +datum=WGS84 +no_defs'),
        pyproj.Proj(local_azimuthal_projection),
    )
    aeqd_to_wgs84 = partial(
        pyproj.transform,
        pyproj.Proj(local_azimuthal_projection),
        pyproj.Proj('+proj=longlat +datum=WGS84 +no_defs'),
    )
    point_transformed = transform(wgs84_to_aeqd, Point(lon, lat))
    circle = point_transformed.buffer(radius_in_km * 1000)  # radius in meters
    circle_wgs84 = transform(aeqd_to_wgs84, circle)
    return circle_wgs84

def get_pinned_map(lat, lon, radius_in_km=36):

    circle = create_geographic_circle(lat, lon, radius_in_km)  # Circle radius 36 km

    # Convert the circle into a GeoDataFrame
    gdf = GeoDataFrame(gpd.GeoSeries(circle), columns=['geometry'])

    # Define the pin data
    pins = [{
        "position": [lon, lat],
        "icon_data": {
            "url": "https://cdn-icons-png.flaticon.com/512/684/684908.png",  # Replace with your icon URL
            "width": 128,
            "height": 128,
            "anchorY": 128
        }
    }]

    # Convert pin data to DataFrame
    df_pins = pd.DataFrame(pins)

    # Set up Pydeck layers
    circle_layer = pdk.Layer(
        "GeoJsonLayer",
        gdf,
        get_fill_color=[255, 0, 0, 140],  # RGBA color: Red with some transparency
        get_line_color=[255, 0, 0],  # Red outline
        line_width_min_pixels=1,
    )

    icon_layer = pdk.Layer(
        "IconLayer",
        df_pins,
        get_icon='icon_data',
        get_position="position",
        size_scale=15,
        get_size=1,
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=8,
        pitch=0
    )

    maps = pdk.Deck(layers=[circle_layer, icon_layer], initial_view_state=view_state, map_style = 'mapbox://styles/mapbox/light-v10')
    
    return maps

def get_pin_layer(lat, lon):
    pins = [{
        "position": [lon, lat],
        "icon_data": {
            "url": "https://cdn-icons-png.flaticon.com/512/684/684908.png",  # Replace with your icon URL
            "width": 128,
            "height": 128,
            "anchorY": 128
        }
    }]
    df_pins = pd.DataFrame(pins)
    icon_layer = pdk.Layer(
        "IconLayer",
        df_pins,
        get_icon='icon_data',
        get_position="position",
        size_scale=30,
        get_size=1,
    )
    return icon_layer

class MapDisplay:
    def __init__(self, map):
        self.map = map

    def display(self):
        st.pydeck_chart(self.map)


def display_maps(maps):
    if maps is None:
        return
    caption, this_map = maps
    st.write(caption)
    # if map is a MapDisplay object, call its display method
    this_map.display()

def display_plots(figs):
    if figs is None or len(figs) == 0:
        return
    for fig in figs:
        st.plotly_chart(fig, use_container_width=True)