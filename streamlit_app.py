import streamlit as st

# Fixed cost per km
costo_por_km = 25.3  

# Title
st.title("Border Freight - Cotizador de Rutas")
st.write("Reglas a recordar:")
st.write("Nuestra utilidad objetivo es 35%. Se cumple este objetivo a cotizar al menos $39 por km")
st.write("Nunca cotizar abajo de $25 por km. Nos generaria una perdida")
st.write("---")

# User inputs
kilometraje = st.number_input("Ingresa el kilometraje de la ruta:", min_value=1, step=1)
dolares = st.radio("¿Deseas cotizar en dólares?", ["no", "si"])

sugerir_precio = st.radio("¿Tienes algún precio en mente?", ["no", "si"])

if sugerir_precio == "no":
    precio_por_km = st.number_input("Ingresa el precio por kilómetro deseado:", min_value=0.0, step=0.1)
    precio_mxn = precio_por_km * kilometraje
    
    if dolares == "si":
        tipo_de_cambio = st.number_input("Ingresa el tipo de cambio:", min_value=0.0, step=0.01)
        precio_usd = precio_mxn / tipo_de_cambio
        precio_final = precio_usd
        moneda = "USD"
    else:
        precio_final = precio_mxn
        moneda = "MXN"
    
else:
    precio_final = st.number_input("Ingresa el precio deseado:")
    precio_por_km = precio_final / kilometraje
    
    if dolares == "si":
        tipo_de_cambio = st.number_input("Ingresa el tipo de cambio:", min_value=0.0, step=0.01)
        precio_mxn = precio_final * tipo_de_cambio
    else:
        precio_mxn = precio_final

# Calculate margin
margen_utilidad = (precio_mxn - (kilometraje * COSTO_POR_KM)) / precio_mxn

# Function to determine color
def get_color(margen):
    if margen < 0:
        return "#FF4C4C"  # Red
    elif 0 <= margen < 0.35:
        return "#D4A017"  # Darker Yellow
    else:
        return "#28A745"  # Green

# Display results
st.markdown(f"### El precio total es: **${precio_final:,.2f} {moneda}**")
st.markdown(
    f"<p style='color:{get_color(margen_utilidad)}; font-size:24px; font-weight:bold;'>"
    f"La utilidad es: {margen_utilidad:.2%}</p>",
    unsafe_allow_html=True
)
st.write("---")
