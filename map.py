import streamlit as st
import pydeck as pdk
import numpy as np
import pandas as pd
from FS import fstk
from MB import mbtk

@st.cache_data
def from_data_file(filename):
    url = (
        "http://raw.githubusercontent.com/streamlit/"
        "example-data/master/hello/v1/%s" % filename
    )
    return pd.read_json(url)

try:
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state={
                "latitude": 37.76,
                "longitude": -122.4,
                "zoom": 11,
            }
            )
    )
except OSError as e:
    st.error(
        """
        **This app requires internet access.**
        Connection error: %s
    """
        % e.reason
    )