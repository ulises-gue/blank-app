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

file_available = st.radio("Tienes un archivo de rutas?", ("Si", "No"))

if file_available == "Si":
    uploaded_file = st.file_uploader("Sube la contrapropuesta del cliente:", type = ["xlsx"], key = "file1")
    if uploaded_file is not None:
        route_data = pd.read_excel(uploaded_file, header = 1)
        st.write("---")
        st.write('<h2 style="color:#c4500b;">Archivo cargado:</h2>', unsafe_allow_html=True)
        st.dataframe(route_data)
        st.write("---")
        st.write('<h2 style="color:#c4500b;">Cotizacion de Rutas:</h2>', unsafe_allow_html=True)
        #We will ask the user to input price per km for different routes
        TCS_price = st.number_input("Ingresa un Precio por KM para Salidas Tramo Corto (50 - 70):")
        TCR_price = st.number_input("Ingresa un Precio por KM para Retornos Tramo Corto (40 - 56):")
        TLS_price = st.number_input("Ingresa un Precio por KM para Salidas Tramo Largo (30 - 38):")
        TLR_price = st.number_input("Ingresa un Precio por KM para Retornos Tramo Largo (38 - 46):")
        
        #We will fill any null values in the frequency column with a 1
        route_data["Frequencia (Mensual)"] = route_data["Frequencia (Mensual)"].fillna(1)
        #We will create the route column which will join the origin and destination columns 
        route_data["Ruta"] = route_data["Origen"] + " - " + route_data["Destino"]
        #We will cretae the distance column
        route_data["Distancia"] = route_data.apply(lambda row: get_distance_km(row["Origen"], row["Destino"]), axis=1)
        
        #We will create the route type column 
        route_data["Tipo de Ruta"] = np.where(route_data["Distancia"] <= 400, "Tramo Corto", "Tramo Largo")
        #We will create the dircetion column
        route_data["Sentido"] = np.where(((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Origen"] == "Reynosa")) |
                                     ((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Origen"] == "Monterrey")) |
                                     ((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Origen"] == "Saltillo")) |
                                     ((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Origen"] == "Matamoros")), "Salida",
                                     np.where((route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Origen"] == "Reynosa"), "Salida", "Retorno"))

        conditions = [
                (route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Sentido"] == "Salida"),
                (route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Sentido"] == "Retorno"),
                (route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Sentido"] == "Salida"),
                (route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Sentido"] == "Retorno"),
            ]
            
            # Define corresponding prices
        price_values = [
                route_data["Distancia"] * TCS_price,
                route_data["Distancia"] * TCR_price,
                route_data["Distancia"] * TLS_price,
                route_data["Distancia"] * TLR_price,
            ]
            
            # Assign calculated prices
        route_data["Precio MXN Quinta"] = np.select(conditions, price_values, default=0)

        price_values_cc = [
                route_data["Distancia"] * (TCS_price - 4),
                route_data["Distancia"] * (TCR_price - 4),
                route_data["Distancia"] * (TLS_price - 4),
                route_data["Distancia"] * (TLR_price - 4),
            ]
        route_data["Precio MXN Camion Corto"] = np.select(conditions, price_values_cc, default=0)
        
        price_values_pf = [
                route_data["Distancia"] * (TCS_price + 4),
                route_data["Distancia"] * (TCR_price + 4),
                route_data["Distancia"] * (TLS_price + 4),
                route_data["Distancia"] * (TLR_price + 4),
            ]
        route_data["Precio MXN Plataforma"] = np.select(conditions, price_values_pf, default=0)
        
        cotizacion = pd.DataFrame(route_data, columns["Ruta", "Precio MXN Quinta", "Precio MXN Camion Corto", "Precio MXN Plataforma")
        st.dataframe(cotizacion)







        
                

        
            
        
         

