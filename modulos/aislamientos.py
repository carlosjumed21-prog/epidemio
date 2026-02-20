import streamlit as st
import pandas as pd

# EL ENLACE DEBE VERSE PARECIDO A ESTE:
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_datos():
    # El engine='python' ayuda a evitar errores con caracteres especiales (ñ, acentos)
    return pd.read_csv(SHEET_URL, engine='python')

st.title("🦠 Control de Aislamientos")

try:
    df = cargar_datos()
    
    # Recuadro de búsqueda para filtrar la tabla
    search = st.text_input("🔍 Buscar paciente o aislamiento:", placeholder="Escribe nombre o cama...")
    
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # Mostrar la tabla de previsualización
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("⚠️ No se pudo cargar la lista.")
    st.info("Revisa que el archivo esté 'Publicado en la web' como CSV.")
