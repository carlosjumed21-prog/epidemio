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
    
    # Rellenar datos
    df["CAMA"] = df["CAMA"].ffill()
    df["NOMBRE"] = df["NOMBRE"].ffill()
    
    # Consolidar tipos de aislamiento
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group["TIPO DE AISLAMIENTO"].dropna().unique()
        res["TIPO DE AISLAMIENTO"] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        return res

    df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar)
    
    # Filtrar solo activos (sin fecha de término)
    if "FECHA DE TÉRMINO" in df.columns:
        df = df[df["FECHA DE TÉRMINO"].isna()]
    
    # --- SELECCIÓN DE VARIABLES Y LIMPIEZA DE FILAS VACÍAS ---
    columnas_deseadas = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "MOTIVO DE SEGUIMIENTO", "FECHA DE INICIO"]
    columnas_presentes = [c for c in columnas_deseadas if c in df.columns]
    df = df[columnas_presentes]
    
    # ELIMINAR FILAS FANTASMA: Solo mantener si tienen CAMA y NOMBRE real
    df = df.replace(['nan', 'None', '', ' '], np.nan)
    df = df.dropna(subset=["CAMA", "NOMBRE"], how='any')
    
    return df.reset_index(drop=True)

# --- INTERFAZ ---
st.title("🦠 Gestión de Aislamientos")

try:
    df_final = cargar_censo_total()

    # Métrica exacta de pacientes
    total_pacientes = len(df_final)
    st.metric(label="Pacientes con Aislamiento Activo", value=total_pacientes)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refrescar Monitor", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🚀 Sincronizar con Google Sheets", use_container_width=True):
            # Enviamos datos limpios sin índice
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
            st.success(f"Se enviaron {total_pacientes} registros correctamente.")
            time.sleep(1)
            st.rerun()
    with col3:
        st.link_button("📂 Abrir Excel en Drive", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()

    # Lectura del Censo Editable
    df_censo = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)

    if not df_censo.empty:
        # Numeración visual empezando en 1
        df_censo.index = range(1, len(df_censo) + 1)

        # Editor con ajuste de texto visual en la App
        df_editado = st.data_editor(
            df_censo,
            use_container_width=True,
            num_rows="dynamic",
            key="main_editor",
            column_config={
                "NOMBRE": st.column_config.TextColumn("NOMBRE", width="large"),
                "TIPO DE AISLAMIENTO": st.column_config.TextColumn("AISLAMIENTO", width="medium"),
            }
        )

        if st.button("💾 Guardar Cambios Manuales", use_container_width=True):
            df_save = df_editado.reset_index(drop=True)
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_save)
            st.toast("Archivo actualizado", icon="✅")
    else:
        st.info("No hay datos en el censo. Usa el botón de sincronizar.")

except Exception as e:
    st.error(f"Error técnico: {e}")
