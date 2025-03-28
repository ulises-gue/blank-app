import streamlit as st
import pandas as pd
import numpy as np
import googlemaps

# Fixed cost per km
cost_oer_km = 25.5

# Title
st.title("Border Freight - Cotizador de Rutas")
st.write("---")

# Initialize Google Maps client using Streamlit secrets
gmaps = googlemaps.Client(key=st.secrets["GOOGLE_MAPS_API_KEY"])

@st.cache_data(show_spinner=False)
def get_distance_km(origin, destination):
    try:
        result = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving")
        distance_m = result['rows'][0]['elements'][0]['distance']['value']
        return round(distance_m / 1000, 2)
    except Exception as e:
        return None  # You could show a warning in Streamlit if needed

file_available = st.radio("Tienes un archivo de rutas?, ("Si", "No"))

