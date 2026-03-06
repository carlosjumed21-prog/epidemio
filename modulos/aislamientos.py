import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
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
    
    # Variables solicitadas
    columnas_deseadas = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "MOTIVO DE SEGUIMIENTO", "FECHA DE INICIO"]
    columnas_presentes = [c for c in columnas_deseadas if c in df.columns]
    df = df[columnas_presentes].dropna(subset=["CAMA"]) # Elimina filas extra sin cama
    
    return df.reset_index(drop=True)

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos")

try:
    df_final = cargar_censo_total()

    # --- MÉTRICAS Y CONTEO ---
    total_aislamientos = len(df_final)
    st.metric(label="Total de Aislamientos Activos", value=total_aislamientos)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Actualizar Servidor", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🚀 Enviar Datos al Censo", use_container_width=True):
            # Enviamos sin el índice de pandas para evitar la "fila/columna de más"
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
            st.success(f"¡Sincronizado! {total_aislamientos} registros enviados.")
            time.sleep(1)
            st.rerun()
    with col3:
        st.link_button("📂 Abrir Google Sheet", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()

    # --- VISTA PREVIA / EDITOR ---
    # Leemos con ttl=0 para frescura total
    df_censo = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)

    if not df_censo.empty:
        # Forzar que el conteo visual empiece en 1
        df_censo.index = range(1, len(df_censo) + 1)

        # Configuración de columnas para "Autoajuste" visual en la App
        # Esto hace que el texto se ajuste y no se corte
        st.data_editor(
            df_censo,
            use_container_width=True,
            num_rows="dynamic",
            key="main_editor",
            column_config={
                "TIPO DE AISLAMIENTO": st.column_config.TextColumn(width="medium"),
                "NOMBRE": st.column_config.TextColumn(width="large"),
            }
        )
        
        # Botón de guardado manual para cambios hechos en la tabla
        if st.button("💾 Guardar Cambios Manuales", use_container_width=True):
            # Antes de guardar quitamos el índice 1,2,3 para no ensuciar el Sheet
            df_save = df_censo.reset_index(drop=True)
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_save)
            st.toast("Cambios guardados", icon="✅")
    else:
        st.info("El censo está vacío.")

except Exception as e:
    st.error(f"Error: {e}")
