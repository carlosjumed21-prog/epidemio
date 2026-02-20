import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
# Reemplaza con tu link de publicación en CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

# Definimos los encabezados exactos que solicitaste
COLUMNAS_DESEADAS = [
    "CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", 
    "MOTIVO DE SEGUIMIENTO", "FECHA DE INICIO", "DÍAS DE SEGUIMIENTO", 
    "FECHA DE TÉRMINO", "GUARDIA", "INGRESO/EGRESO"
]

def cargar_y_filtrar_aislamientos():
    # 1. Cargar los datos
    df = pd.read_csv(SHEET_URL, engine='python')
    
    # Limpiar espacios en los nombres de las columnas por si acaso
    df.columns = [c.strip() for c in df.columns]
    
    # 2. Seleccionar solo los encabezados solicitados
    # Usamos intersection para evitar errores si un nombre varía por un acento
    df = df[COLUMNAS_DESEADAS]
    
    # 3. Lógica de "Sombreado Verde" -> Filtrar donde la columna INGRESO/EGRESO esté vacía
    # Asumiendo que cuando se sombrea en verde, se llena el dato de egreso.
    # Si prefieres basarte estrictamente en que la columna A esté en blanco:
    df = df[df["INGRESO/EGRESO"].isna() | (df["INGRESO/EGRESO"].astype(str).str.strip() == "")]
    
    return df

try:
    with st.container(border=True):
        st.markdown("### 📋 Pacientes en Aislamiento")
        st.caption("Mostrando solo aislamientos activos (sin registro de egreso/sombreado).")
        
        df_activos = cargar_y_filtrar_aislamientos()
        
        if df_activos.empty:
            st.info("No hay aislamientos activos registrados actualmente.")
        else:
            # Buscador rápido
            busqueda = st.text_input("🔍 Filtrar por cama, registro o nombre:", placeholder="Ej: 4210...")
            
            if busqueda:
                mask = df_activos.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_activos = df_activos[mask]

            # Visualización profesional
            st.dataframe(
                df_activos,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "CAMA": st.column_config.TextColumn("Cama"),
                    "DÍAS DE SEGUIMIENTO": st.column_config.NumberColumn("Días", format="%d"),
                    "TIPO DE AISLAMIENTO": st.column_config.TextColumn("Tipo")
                }
            )
            
            st.success(f"Se detectaron {len(df_activos)} aislamientos activos.")

except Exception as e:
    st.error(f"Error al procesar la lista: {e}")
    st.info("Verifica que los nombres de las columnas en Google Sheets coincidan exactamente con los solicitados.")

if st.button("🔄 Actualizar desde Google Sheets"):
    st.cache_data.clear()
    st.rerun()
