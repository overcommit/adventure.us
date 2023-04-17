import streamlit as st
import pydeck as pdk
import numpy as np
import pandas as pd
import requests

mbtk = st.secrets["mbtk"]
fstk = st.secrets["fstk"]

pd.set_option('display.max_rows', None)

FOURSQUARE_API_BASE_URL = "https://api.foursquare.com/v3/places/search"
MAPBOX_GEOCODING_API_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"

@st.cache_data
def get_venues(near):
    params = {
        "query": "food",
        "near": near,
        "open_now": "true",
        "sort": "DISTANCE",
        "fields": "fsq_id,name,geocodes,location,categories,distance,website,tel,menu",
        "limit": 50,
    }

    headers = {
        "Accept": "application/json",
        "Authorization": fstk
    }
    response = requests.get(FOURSQUARE_API_BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        venues = data["results"]
        df_venues = pd.DataFrame.from_records(venues)

        required_columns = ["fsq_id", "name", "geocodes", "location", "categories", "distance", "website", "tel", "menu"]
        if not set(required_columns).issubset(set(df_venues.columns)):
            st.error(f"Location not found. Please try another location or add the state abbreviation.")
            return pd.DataFrame()

        # Select and rename columns
        df_venues = df_venues[["fsq_id", "name", "geocodes", "location", "categories", "distance", "website", "tel","menu",]]
        df_venues.columns = ["id", "name", "geocodes", "location", "categories", "distance", "website", "tel","menu",]
        df_venues = df_venues.where(pd.notnull(df_venues), None)
        df_venues = df_venues.drop_duplicates(subset=["name"])

        # Extract latitude and longitude
        df_venues["latitude"] = df_venues["geocodes"].apply(lambda x: x["main"]["latitude"])
        df_venues["longitude"] = df_venues["geocodes"].apply(lambda x: x["main"]["longitude"])

        # Extract formatted address
        df_venues["address"] = df_venues["location"].apply(lambda x: x.get("address", ""))

        # Convert categories to comma-separated string
        df_venues["categories"] = df_venues["categories"].apply(lambda x: ", ".join([category["name"] for category in x]))

        # Drop unnecessary columns
        df_venues.drop(columns=["geocodes", "location"], inplace=True)
        df_venues['icon_data'] = [icon_data] * len(df_venues)
        return df_venues
    else:
        st.error("Error fetching data from the API.")
        return pd.DataFrame()

st.title("What Am I Eating?")
location_name = f'"{st.text_input("Enter a town or city name:")}"'

ICON_URL = "https://raw.githubusercontent.com/overcommit/adventure.us/main/reshot-icon-restaurant.png"

icon_data = {
    "url": ICON_URL,
    "width": 256,
    "height": 256,
    "anchorY": 256,
}

category_label = (
"",
"Bagel Shop",
"Bakery",
"Breakfast Spot",
"Cafes, Coffee, and Tea Houses",
"Donut Shop",
"Frozen Yogurt Shop",
"Ice Cream Parlor",
"Asian Restaurant",
"BBQ Joint",
"Bistro",
"Buffet",
"Burger Joint",
"Chinese Restaurant",
"Comfort Food Restaurant",
"Deli",
"Diner",
"Eastern European Restaurant",
"Fast Food Restaurant",
"Filipino Restaurant",
"French Restaurant",
"Fried Chicken Joint",
"Halal Restaurant",
"Hawaiian Restaurant",
"Hot Dog Joint",
"Indian Restaurant",
"Italian Restaurant",
"Japanese Restaurant",
"Sushi Restaurant",
"Kebab Restaurant",
"Korean Restaurant",
"Latin American Restaurant",
"Mediterranean Restaurant",
"Mexican Restaurant",
"Middle Eastern Restaurant",
"Pizzeria",
"Seafood Restaurant",
"Shawarma Restaurant",
"Steakhouse",
"Thai Restaurant",
"Theme Restaurant",
)

category = st.selectbox("Select a category filter(Default searches all categories):", category_label)

if st.button("Find Random Venue"):
    if location_name:
        venues = get_venues(location_name)
        if len(venues) == 0:
            st.error("No venues found. Please try another location")
        else:
            venues_filtered = venues[venues['categories'].str.contains(category, case=False)]
            if len(venues_filtered) == 0:
                st.error(f"No {category} venues found. Please try another category.")
            else:
                random_venue = np.random.choice(venues_filtered['name'].values)
                selected_venue = venues.loc[venues['name'] == random_venue].squeeze()
                st.write(f"{selected_venue['name']}")
                st.write(f"Address: {selected_venue['address']}")
                st.write(f"Website: {selected_venue['website'] if selected_venue['website'] else 'Unavailable'}")
                st.write(f"Phone number: {selected_venue['tel']}")
                st.write(f"Menu: {selected_venue['menu'] if selected_venue['menu'] else 'Unavailable'}")
                st.pydeck_chart(pdk.Deck(
                    map_style="mapbox://styles/mapbox/navigation-night-v1",
                    initial_view_state={
                        "latitude": selected_venue['latitude'],
                        "longitude": selected_venue['longitude'],
                        "zoom": 16,
                        "pitch": 25,
                    },
                    layers=[
                        pdk.Layer(
                            "IconLayer",
                            data=pd.DataFrame([selected_venue]),
                            get_position=["longitude", "latitude"],
                            get_icon="icon_data",
                            get_size=4,
                            size_scale=15,
                            pickable=True,
                        ),
                    ],
                    tooltip={"text": "{name}\nAddress: {address}"},
                ))
    else:
        st.error("Invalid location. Please enter a valid town or city name.")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

hide_streamlit_style = """
    <style>
        #MainMenu {display: none;}
        footer {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)