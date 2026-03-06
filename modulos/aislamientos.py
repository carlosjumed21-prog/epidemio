import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def cargar_censo_total():
    url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10]
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # Rellenar datos para evitar celdas vacías
    df["CAMA"] = df["CAMA"].ffill()
    df["NOMBRE"] = df["NOMBRE"].ffill()
    
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group["TIPO DE AISLAMIENTO"].dropna().unique()
        res["TIPO DE AISLAMIENTO"] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        return res

    df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar)
    
    if "FECHA DE TÉRMINO" in df.columns:
        df = df[df["FECHA DE TÉRMINO"].isna()]
    
    # Selección de variables requeridas
    columnas_deseadas = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "MOTIVO DE SEGUIMIENTO", "FECHA DE INICIO"]
    columnas_presentes = [c for c in columnas_deseadas if c in df.columns]
    df = df[columnas_presentes]
    
    # --- ELIMINACIÓN DE FILAS FANTASMA (LIMPIEZA ESTRICTA) ---
    df = df.replace(['nan', 'None', '', ' '], np.nan)
    # Solo conservamos filas que tengan CAMA y NOMBRE (evita sesgos en el conteo)
    df = df.dropna(subset=["CAMA", "NOMBRE"], how='any')
    
    return df.reset_index(drop=True)

# --- INTERFAZ ---
st.title("🦠 Gestión de Aislamientos")

try:
    df_final = cargar_censo_total()

    # Métrica de conteo real sin encabezados ni filas vacías
    st.metric(label="Total Pacientes en Censo", value=len(df_final))

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🚀 Enviar a Google Sheets", use_container_width=True):
            # Se envía sin el índice de pandas para que Google lo reconozca como tabla pura
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
            st.success("¡Datos enviados!")
            time.sleep(1)
            st.rerun()
    with col3:
        st.link_button("📂 Ir al Google Sheet (Filtros)", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()

    # Visualización en la App
    df_censo = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)

    if not df_censo.empty:
        # Iniciamos conteo visual en 1 para la App
        df_censo.index = range(1, len(df_censo) + 1)
        
        st.data_editor(
            df_censo,
            use_container_width=True,
            num_rows="dynamic",
            key="main_editor",
            column_config={
                "NOMBRE": st.column_config.TextColumn(width="large"),
                "TIPO DE AISLAMIENTO": st.column_config.TextColumn(width="medium")
            }
        )
        
        if st.button("💾 Guardar Cambios Manuales", use_container_width=True):
            df_save = df_censo.reset_index(drop=True)
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_save)
            st.toast("Censo actualizado en la nube")
    else:
        st.info("Sincroniza los datos para ver la tabla.")

except Exception as e:
    st.error(f"Error: {e}")
