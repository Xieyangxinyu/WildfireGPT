from pygris.geocode import geolookup
from census import Census
import geopandas as gpd
import pydeck as pdk
import plotly.graph_objects as go
import pandas as pd
from shapely.geometry import Point
from src.assistants.analyst.utils import get_pin_layer, MapDisplay
c = Census("93c3297165ad8b5b6c81e0ed9e2e44a38e56224f")

def get_census_info(lon: float, lat: float) -> str:
    
    geocode = geolookup(longitude = lon, latitude= lat)['GEOID'][0]
    state_code = geocode[0:2]
    radius_meters = 36 * 1000  # radius in meters

    point = Point(lon, lat)
    # Create a GeoSeries in geographic coordinates
    point_gseries = gpd.GeoSeries([point], crs="EPSG:4326")

    # Transform to a projected CRS that uses meters (e.g., World Mercator)
    point_transformed = point_gseries.to_crs(epsg=3857)

    # Create a buffer around the point in the correct CRS
    buffer = point_transformed.buffer(radius_meters)

    # Optionally transform back to geographic coordinates to check the result in EPSG:4326
    buffer = buffer.to_crs(epsg=4326)

    # C17002_001E: count of ratio of income to poverty in the past 12 months (total)
    # C17002_002E: count of ratio of income to poverty in the past 12 months (< 0.50)
    # C17002_003E: count of ratio of income to poverty in the past 12 months (0.50 - 0.99)
    # B01003_001E: total population
    # B25001_001E: Housing units
    # B19013_001E: Median household income
    # Sources: https://api.census.gov/data/2019/acs/acs5/variables.html

    state_tract = gpd.read_file(f"https://www2.census.gov/geo/tiger/TIGER2022/BG/tl_2022_{state_code}_bg.zip")
    state_tract = state_tract.to_crs(epsg=4326)
    state_tract["GEOID"] = state_tract["GEOID"].astype(str)
    state_tract = state_tract[state_tract.intersects(buffer.geometry[0])]
    
    block_groups = c.acs5.state_county_blockgroup(fields = ('C17002_001E', 'C17002_002E', 'C17002_003E', 'B01003_001E', 'B25001_001E', 'B19013_001E'),
        state_fips = state_code,
        county_fips = '*',
        tract = '*',
        blockgroup = "*",
        year = 2022)
    bg_df = pd.DataFrame(block_groups)

    
    bg_df["GEOID"] = bg_df["state"] + bg_df["county"] + bg_df["tract"] + bg_df["block group"]
    bg_df["GEOID"] = bg_df["GEOID"].astype(str)
    bg_df = state_tract.merge(bg_df, on = "GEOID")

    bg_df['poverty_count'] = bg_df['C17002_002E'] + bg_df['C17002_003E'] 

    # sum each column to a new dataframe
    bg_df_sum = pd.DataFrame(bg_df[['poverty_count', 'C17002_002E', 'B01003_001E', 'B25001_001E']].sum()).T

    output = f"In 2022, the total population within roughly 36km (22 miles) of location (lat: {lat}, lon: {lon}) is {bg_df_sum['B01003_001E'][0]}. The number of individual under the poverty line is {bg_df_sum['poverty_count'][0]}. In particular, {bg_df_sum['C17002_002E'][0]} individuals hold income less than half of what is considered the minimum required to meet basic living expenses. There are {bg_df_sum['B25001_001E'][0]} housing units in the area."


    bg_df = bg_df[['GEOID', 'poverty_count', 'C17002_002E', 'B01003_001E', 'B25001_001E', 'geometry']]
    bg_df = bg_df.to_crs(epsg=4326)
    layer = pdk.Layer(
        'GeoJsonLayer',
        bg_df,
        opacity=0.8,
        get_fill_color=[255, 0, 0, 140],  # RGBA color: Red with some transparency
        get_line_color=[255, 0, 0],  # Red outline
        line_width_min_pixels=1,
        pickable=True
    )

    icon_layer = get_pin_layer(lat, lon)

    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=8,
        pitch=50
        )
    
    maps = pdk.Deck(layers=[layer, icon_layer], 
                    initial_view_state=view_state, 
                    tooltip={"text": "GEOID: {GEOID} \n Population: {B01003_001E} \n Below Poverty: {poverty_count} \n Below Half Poverty: {C17002_002E} \n Housing Units: {B25001_001E}"},
                    map_style = 'mapbox://styles/mapbox/light-v10')

    maps = [f"The census block groups overlapping with the area within 36 km (22 miles) of the location (lat: {lat}, lon: {lon})" , MapDisplay(maps)]
    # draw a table with the data

    fig = go.Figure(data=[go.Table(
        header=dict(values=['Population', 'Below Poverty', 'Below Half Poverty', 'Housing Units'],
                        fill_color='royalblue',  # Header background color
                        align='left',
                        font=dict(color='white', size=14)),
        cells=dict(values=[bg_df_sum['B01003_001E'][0], bg_df_sum['poverty_count'][0], bg_df_sum['C17002_002E'][0], bg_df_sum['B25001_001E'][0]],
                        fill_color=['paleturquoise', 'lavender'],  # Cell background colors
                        align='left',
                        font=dict(color='black', size=14)))
        ])
    
    fig.update_layout(title=f'Census Data within 36km (22 miles) surrounding location (lat: {lat}, lon: {lon})')

    return output, maps, [fig]