import streamlit as st
import pydeck as pdk
import numpy as np
import pandas as pd
import requests
from FS import fstk
from MB import mbtk
import os
from django.core.wsgi import get_wsgi_application
from django.contrib.auth import authenticate
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()


# Foursquare API v3 base URL
FOURSQUARE_API_BASE_URL = "https://api.foursquare.com/v3/places/search"

MAPBOX_GEOCODING_API_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"

def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        user = authenticate(
            username=st.session_state['username'], 
            password=st.session_state['password']
            )
        
        if (user is not None):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True
    
if check_password():

    @st.cache_data
    def get_location_coordinates(location_name):
        params = {
            "access_token": mbtk,
            "limit": 1,
        }

        response = requests.get(f"{MAPBOX_GEOCODING_API_BASE_URL}/{location_name}.json", params=params)
        data = response.json()

        if response.status_code == 200 and data["features"]:
            return f"{data['features'][0]['center'][1]},{data['features'][0]['center'][0]}"

        else:
            return None


    @st.cache_data
    def get_venues(location, radius):
        params = {
            "query": "food",
            "ll": location,
            "radius": radius,
            "open_now": "true",
            "sort": "DISTANCE",
        }

        headers = {
            "Accept": "application/json",
            "Authorization": fstk
        }

        response = requests.get(FOURSQUARE_API_BASE_URL, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if "results" in data["results"]:
                venues = data["results"]
                df_venues = pd.DataFrame.from_records(venues)

                # Select and rename columns
                df_venues = df_venues[["fsq_id", "name", "geocodes", "location", "categories", "distance"]]
                df_venues.columns = ["id", "name", "geocodes", "location", "categories", "distance"]

                # Extract latitude and longitude
                df_venues["latitude"] = df_venues["geocodes"].apply(lambda x: x["main"]["latitude"])
                df_venues["longitude"] = df_venues["geocodes"].apply(lambda x: x["main"]["longitude"])

                # Extract formatted address
                df_venues["address"] = df_venues["location"].apply(lambda x: x["formatted_address"])

                # Convert categories to comma-separated string
                df_venues["categories"] = df_venues["categories"].apply(lambda x: ", ".join([category["name"] for category in x]))

                # Drop unnecessary columns
                df_venues.drop(columns=["geocodes", "location"], inplace=True)

                return df_venues
        else:
            st.error("Error fetching data from the API.")
            return pd.DataFrame()

    st.title("Random Food Venue Finder")
    location_name = st.text_input("Enter a town or city name:", value="")
    radius = st.number_input("Radius (meters):", min_value=100, max_value=50000, value=1000, step=100)

    if st.button("Find Random Venue"):
        location_coordinates = get_location_coordinates(location_name)
        if location_coordinates:
            venues = get_venues(location_coordinates, radius)
            if venues:
                selected_venue = np.random.choice(venues)
                st.write(f"Selected venue: {selected_venue['name']}")
                st.write(f"Address: {', '.join(selected_venue['address'])}")
                st.write(f"Contact: {selected_venue['contact']}")

                st.pydeck_chart(pdk.Deck(
                    map_style="mapbox://styles/mapbox/light-v9",
                    initial_view_state={
                        "latitude": selected_venue['location'][0],
                        "longitude": selected_venue['location'][1],
                        "zoom": 14,
                        "pitch": 50,
                    },
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=pd.DataFrame([selected_venue]),
                            get_position="location",
                            get_radius=100,
                            get_fill_color=[255, 0, 0, 160],
                            pickable=True,
                            auto_highlight=True,
                        ),
                    ],
                    mapbox_key = mbtk,
                    tooltip={"text": "{name}\nAddress: {address}\nContact: {contact}"}
                ))
            else:
                st.error("No venues found. Please try another location or radius.")
        else:
            st.error("Invalid location. Please enter a valid town or city name.")