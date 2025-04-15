import streamlit as st
import pandas as pd
import numpy as np
import googlemaps

# Fixed cost per km
cost_per_km = 25.8
avg_monthly_km = 1100000
monthly_kpi = 1380189.67

# Title
st.title("Border Freight - Cotizador de Rutas")
st.write("Esta aplicacion esta diseñada para la generacion de precios.")
st.write("Puedes subir un archivo en el template diseñado o cotizar una ruta individual.")
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
        LOCAL_price = st.number_input("Ingresa un Precio por KM para Rutas Locales (65 - 70):")
        
        #We will fill any null values in the frequency column with a 1
        route_data["Frequencia (Mensual)"] = route_data["Frequencia (Mensual)"].fillna(1)
        #We will create the route column which will join the origin and destination columns 
        route_data["Ruta"] = route_data["Origen"] + " - " + route_data["Destino"]
        #We will cretae the distance column
        route_data["Distancia"] = route_data.apply(lambda row: get_distance_km(row["Origen"], row["Destino"]), axis=1)
        
        #We will create the route type column 
        route_data["Tipo de Ruta"] = np.where(
            route_data["Origen"] == route_data["Destino"],
            "Local",
            np.where(route_data["Distancia"] <= 400, "Tramo Corto", "Tramo Largo")
        )
        route_data.loc[route_data["Tipo de Ruta"] == "Local", "Distancia"] = 40
        #We will create the dircetion column
        route_data["Sentido"] = np.where(
            (
                ((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Origen"].isin([
                    "Reynosa", "Monterrey", "Saltillo", "Matamoros",
                    "Reynosa, TAM", "Monterrey, NLE", "Saltillo, COA", "Matamoros, TAM",
                    "Ramos Arizpe, COA", "Monclova, COA", "Apodaca, NLE",
                    "Santa Catarina, NLE", "Guadalupe, NLE", "Cienega de Flores, NLE",
                    "Nuevo Laredo, TAM", "Ciudad Juarez, CHH"
                ])))
            ),
            "Salida",
            np.where(
                (route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Origen"] == "Reynosa"),
                "Salida",
                "Retorno"
            )
        )

        conditions = [
                (route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Sentido"] == "Salida"),
                (route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Sentido"] == "Retorno"),
                (route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Sentido"] == "Salida"),
                (route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Sentido"] == "Retorno"),
                (route_data["Tipo de Ruta"] == "Local")
            
            ]
            
            # Define corresponding prices
        price_values = [
                route_data["Distancia"] * TCS_price,
                route_data["Distancia"] * TCR_price,
                route_data["Distancia"] * TLS_price,
                route_data["Distancia"] * TLR_price,
                route_data["Distancia"] * LOCAL_price
            ]

     
            # Assign calculated prices
        route_data["Precio MXN Quinta"] = np.select(conditions, price_values, default=0)
        
        price_values_cc = [
                route_data["Distancia"] * (TCS_price - 4),
                route_data["Distancia"] * (TCR_price - 4),
                route_data["Distancia"] * (TLS_price - 4),
                route_data["Distancia"] * (TLR_price - 4),
                route_data["Distancia"] * (LOCAL_price - 4),
            ]
        route_data["Precio MXN Camion Corto"] = np.select(conditions, price_values_cc, default=0)
        
        price_values_pf = [
                route_data["Distancia"] * (TCS_price + 4),
                route_data["Distancia"] * (TCR_price + 4),
                route_data["Distancia"] * (TLS_price + 4),
                route_data["Distancia"] * (TLR_price + 4),
                route_data["Distancia"] * (LOCAL_price + 4),
            ]
        route_data["Precio MXN Plataforma"] = np.select(conditions, price_values_pf, default=0)
        # Apply round-trip (Redondo) logic
        if "Tipo" in route_data.columns:
            route_data.loc[route_data["Tipo"] == "Redondo", "Distancia"] *= 2
            route_data.loc[route_data["Tipo"] == "Redondo", "Precio MXN Quinta"] *= 0.85
            route_data.loc[route_data["Tipo"] == "Redondo", "Precio MXN Camion Corto"] *= 0.85
            route_data.loc[route_data["Tipo"] == "Redondo", "Precio MXN Plataforma"] *= 0.85
        else:
            st.warning("La columna 'Tipo' no está en el archivo. Asegúrate de incluir una columna con valores 'Sencillo' o 'Redondo'.")

        cotizacion = pd.DataFrame(route_data, columns = ["Ruta", "Precio MXN Quinta", "Precio MXN Camion Corto", "Precio MXN Plataforma"])
        cotizacion["Precio MXN Quinta"] = cotizacion["Precio MXN Quinta"].apply(lambda x: f"{x:,.2f}")
        cotizacion["Precio MXN Camion Corto"] = cotizacion["Precio MXN Camion Corto"].apply(lambda x: f"{x:,.2f}")
        cotizacion["Precio MXN Plataforma"] = cotizacion["Precio MXN Plataforma"].apply(lambda x: f"{x:,.2f}")
        st.dataframe(cotizacion)

        st.write("---")
        st.write('<h2 style="color:#c4500b;">Evaluacion de Rutas:</h2>', unsafe_allow_html=True)
        route_data["Utilidad (%)"] = ((route_data["Precio MXN Quinta"] - (route_data["Distancia"] * cost_per_km))/route_data["Precio MXN Quinta"])*100
        route_data["Utilidad (%)"] = route_data["Utilidad (%)"]. round(2)

        route_data["Evaluacion"] = np.where(((route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Sentido"]  == "Retorno") & (route_data["Utilidad (%)"] >= 36)), "Si",
                                        np.where(((route_data["Tipo de Ruta"] == "Tramo Corto") & (route_data["Sentido"] == "Salida") & (route_data["Utilidad (%)"] >= 49)), "Si",
                                                 np.where(((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Sentido"] == "Salida") & (route_data["Utilidad (%)"] >= 15)), "Si",
                                                          np.where(((route_data["Tipo de Ruta"] == "Tramo Largo") & (route_data["Sentido"] == "Retorno") & (route_data["Utilidad (%)"] >= 33)), "Si", "No"))))
        precio_km_values = [
                TCS_price,
                TCR_price,
                TLS_price,
                TLR_price,
                LOCAL_price,
            ]
        route_data["Precio por KM"] = np.select(conditions, precio_km_values, default=0)
        evaluation = pd.DataFrame(route_data, columns = ["Ruta", "Tipo de Ruta", "Sentido","Frequencia (Mensual)", "Tipo", "Distancia", "Precio MXN Quinta", "Precio por KM", "Utilidad (%)", "Evaluacion"])
        evaluation["Distancia"] = evaluation["Distancia"].apply(lambda x: f"{x:,.2f}")
        evaluation["Precio MXN Quinta"] = evaluation["Precio MXN Quinta"].apply(lambda x: f"{x:,.2f}")
        evaluation["Precio por KM"] = evaluation["Precio por KM"].apply(lambda x: f"{x:,.2f}")
        st.dataframe(evaluation)

        route_data["Distancia Mensual"] = route_data["Frequencia (Mensual)"] * route_data["Distancia"]
        route_data["Facturacion Mensual"] = route_data["Frequencia (Mensual)"] * route_data["Precio MXN Quinta"]
        route_data["Costo Mensual"] = route_data["Distancia Mensual"] * cost_per_km

        total_distance = route_data["Distancia Mensual"].sum()
        revenue = route_data["Facturacion Mensual"].sum()
        costs = route_data["Costo Mensual"].sum()
        total_profit = (revenue - costs) / revenue

        st.write('<b>Kilometros Mensuales de Operacion Cotizada:</b>', f"{total_distance:,.2f}", unsafe_allow_html=True)
        st.write('<b>Facturacion Mensual de Operacion Cotizada:</b>', f"{revenue:,.2f}", unsafe_allow_html=True)
        st.write('<b>Utlidad de Operacion Cotizada:</b>', f"{total_profit:.2%}", unsafe_allow_html=True)
        st.write('<b>Promedio de Kilometros Mensuales:</b>', f"{avg_monthly_km:,.2f}", unsafe_allow_html=True)
          
        km_mensual_new = total_distance + avg_monthly_km
        st.write('<b>Kilometros Mensuales + Nueva Operacion:</b>', f"{km_mensual_new:,.2f}", unsafe_allow_html=True)
        per_increase = ((total_distance + avg_monthly_km) - avg_monthly_km) / avg_monthly_km
        st.write('<b>Porcentaje de Incremento:</b>', f"{per_increase:.2%}", unsafe_allow_html=True)
          
        st.write('<b>KPI Mensual:</b>', f"{monthly_kpi:,.2f}", unsafe_allow_html=True)
          
        difference = km_mensual_new - monthly_kpi
        st.write('<b>Diferencia:</b>', f"{difference:,.2f}", unsafe_allow_html=True)
        
        

        







        
                

        
            
        
         

