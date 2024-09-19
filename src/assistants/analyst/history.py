from geopy.distance import geodesic
import numpy as np
import pandas as pd
import requests
from src.assistants.analyst.utils import get_pin_layer, MapDisplay
import json
import pydeck as pdk

def format_apa_citation(publication):
    """
    Formats a publication dictionary into an APA style citation, handling empty entries appropriately.
    """
    authors = publication.get('Authors', '')
    year = publication.get('Published_Date_or_Year', 'n.d.')
    title = publication.get('Published_Title', '')
    journal = publication.get('Journal_Name', '')
    volume = publication.get('Volume', '')
    issue = publication.get('Issue', '')
    pages = publication.get('Pages', '')
    doi = publication.get('DOI', '')

    # Formatting the authors for APA style
    authors_list = authors.split(',')
    if len(authors_list) > 2:
        apa_authors = f"{authors_list[0]} et al."
    elif authors:
        apa_authors = ' & '.join(authors_list)
    else:
        apa_authors = ''

    # Constructing the citation
    citation_parts = [apa_authors, f"({year})", title]
    if journal:
        citation_parts.append(journal)
        if volume:
            citation_parts.append(f"{volume}({issue})" if issue else volume)
        if pages:
            citation_parts.append(pages)
    if doi:
        citation_parts.append(doi)

    citation = ', '.join(part for part in citation_parts if part)
    return citation

def extract_abstract_and_citation(publications):
    """
    Extracts publications from the given file and returns a list of dictionaries 
    containing the abstract (if available), APA style citation, and DOI (if available) for each publication.
    """
    publication_details = []

    for publication in publications:
        abstract = publication.get('Abstract', '')
        doi = publication.get('DOI', '')

        if not abstract:
            if doi:
                abstract = f"Abstract not found; but you may try DOI: {doi}."
            else:
                abstract = "Abstract not found."

        apa_citation = format_apa_citation(publication)
        publication_details.append({'Paper': apa_citation, 'Abstract': abstract})

    return publication_details


def get_publications(url):
    '''
    Downloads the file from the given URL and parses it to extract the publication details.
    Returns a list of dictionaries containing the publication details.
    
    :param url: URL of the file to download
    :return: List of dictionaries containing the publication details
    '''

    # Attempting to download and read the content of the file
    try:
        response = requests.get(url)
        # Checking if the request was successful
        if response.status_code == 200:
            data_content = response.text
        else:
            data_content = f"Failed to download the data. Status code: {response.status_code}"
    except Exception as e:
        data_content = f"An error occurred: {e}"


    try:
        file_contents = data_content

        # Splitting the file content into lines for easier processing
        lines = file_contents.split('\n')

        # Flag to indicate if we are currently reading a publication block
        in_publication_block = False

        # List to store all publication dictionaries
        publications = []

        # Temporary dictionary to hold the current publication's details
        current_publication = {}
        abstract_flag = False

        # Iterating over each line
        for line in lines:
            # Check for the start of a publication block
            if line.strip() == '# Publication':
                in_publication_block = True
                current_publication = {}
                abstract_flag = False
            elif line.strip() == '#--------------------':
                # End of a publication block
                if in_publication_block and current_publication:
                    publications.append(current_publication)
                    current_publication = {}
                in_publication_block = False
            elif in_publication_block:
                # Process the publication details
                if line.startswith('#   Abstract: '):
                    abstract_flag = True
                    current_publication['Abstract'] = line.split('#   Abstract: ', 1)[1]
                elif abstract_flag and line != '#':
                    # Continue appending to the abstract
                    current_publication['Abstract'] += line.split('# ', 1)[1]
                elif ': ' in line and not abstract_flag:
                    key, value = line.split(': ', 1)
                    key = key.replace('#', '').strip()
                    current_publication[key] = value.strip()

        # Ensuring the last publication is added if the file doesn't end with the separator
        if in_publication_block and current_publication:
            publications.append(current_publication)

    except Exception as e:
        publications = f"An error occurred: {e}"

    publications_json = [json.dumps(pub, sort_keys=True) for pub in publications]

    # Use np.unique to get unique JSON strings
    unique_publications_json = np.unique(publications_json)
    publications = [json.loads(pub) for pub in unique_publications_json]
    
    publication_details = extract_abstract_and_citation(publications)
    return publication_details


# Re-defining the functions and re-loading the data as the code execution state was reset

def long_term_fire_history_records(lat, lon, max_distance_km = 36):
    """
    Finds the 3 closest fire history records to the given latitude and longitude within 36 km.
    Returns a list of dictionaries of the fire history data, up to a maximum of max_results records.
    """
    fire_data = pd.read_csv('./data/s1-NAFSS.csv')
    distances = fire_data.apply(lambda row: geodesic((lat, lon), (row['latitude'], row['longitude'])).kilometers, axis=1)
    print(distances)
    fire_data['distance'] = distances
    nearby_records = fire_data[fire_data['distance'] <= max_distance_km].sort_values(by='distance')[:3]
    
    aggregation_functions = {
        'siteName': list,
        'latitude': list,
        'longitude': list,
        'link_to_data': list,
        'link_to_metadata': list
    }

    combined_records = nearby_records.groupby('reference').agg(aggregation_functions).reset_index().to_dict('records')
    for record in combined_records:
        url = record['link_to_metadata']
        # if url is a list, take the first one
        if isinstance(url, list):
            url = url[0]
        record['publications'] = get_publications(url)

    if not combined_records:
        return "No fire history records found within 36 km of the given location. This only means that we do not find research data from NOAA''s fire history and paleoclimate services. Please inform your client of this limitation. If you haven't analyzed the FWI data or the recent fire incident data, ask if your client would like to explore alternative sources for analysis, such as the Fire Weather Index (FWI) or recent fire incident data; otherwise, suggest your client to proceed with the plan.", None, []
    

    layer = pdk.Layer(
        'ScatterplotLayer',
        nearby_records,
        get_position='[longitude, latitude]',
        get_radius=1000,
        get_color=[255, 0, 0, 160],
        pickable=True
    )
    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=8,
        pitch=0
    )

    icon_layer = get_pin_layer(lat, lon)

    maps = pdk.Deck(
        initial_view_state=view_state,
        layers=[layer, icon_layer],
        tooltip={"text": "Latitude: {latitude}\nLongitude: {longitude}\nSite Name: {siteName}"},
        map_style = 'mapbox://styles/mapbox/light-v10'
    )

    maps = [f"The three closest fire history records found within 36 km (22 miles) of the location (lat: {lat}, lon: {lon})" , MapDisplay(maps)]

    return f"The three closest fire history records found within 36 km (22 miles) of the location (lat: {lat}, lon: {lon})\n\n" + str(combined_records), maps, []

if __name__ == '__main__':
    # Testing the function
    print(long_term_fire_history_records(35.7028, -113.1429, max_distance_km = 36))