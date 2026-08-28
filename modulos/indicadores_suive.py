import streamlit as st
import pandas as pd
from pygwalker.api.streamlit import StreamlitRenderer

st.title("📈 Indicadores SUIVE (Constructor Visual)")
st.markdown("Arrastra las variables a los ejes de Columnas y Filas para construir tu tabla dinámica.")

# 1. Carga de datos (Simulando la estructura de tu imagen)
@st.cache_data
def cargar_datos_prueba():
    return pd.DataFrame({
        'Delegacion ISSSTE': ['CDMX Sur', 'CDMX Sur', 'Puebla', 'CDMX Sur', 'Puebla', 'CDMX Sur'],
        'Año': [2026, 2026, 2026, 2026, 2026, 2026],
        'Semana': [30, 31, 30, 31, 31, 30],
        'Unidad médica': ['CMN 20 de Noviembre', 'CMN 20 de Noviembre', 'H.R. Puebla', 'CMN 20 de Noviembre', 'H.R. Puebla', 'C.M.F. Balbuena'],
        'Datos indicadores': ['Casos Nuevos', 'Casos Nuevos', 'Seguimiento', 'Alta', 'Casos Nuevos', 'Seguimiento'],
        'Datos': [12, 15, 8, 5, 10, 3]
    })

df = cargar_datos_prueba()

# 2. Inicializar el renderizador de PyGWalker
# Se usa @st.cache_resource para evitar que la interfaz parpadee o se reinicie con cada clic
@st.cache_resource
def obtener_renderizador(dataframe):
    # El archivo JSON guarda automáticamente la estructura de la tabla dinámica que armes
    return StreamlitRenderer(dataframe, spec="configuracion_suive.json", spec_io_mode="rw")

renderizador = obtener_renderizador(df)

# 3. Mostrar la interfaz interactiva de arrastrar y soltar
# Desplegará un panel completo donde puedes mover 'Semana' a Columnas y 'Unidad médica' a Filas
renderizador.explorer()
