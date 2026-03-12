import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        SHEET_ID = "116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc"
        spreadsheet = client.open_by_key(SHEET_ID)
        return spreadsheet.get_worksheet(0) 
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_censo_publico():
    try:
        return pd.read_csv(URL_ORIGEN)
    except Exception as e:
        st.error(f"Error al leer el censo de origen: {e}")
        return None

df_pacientes = cargar_censo_publico()

# --- 3. FUNCIÓN CORE DE VACIADO ---
def vaciar_paciente(hoja, fila_datos):
    """Lógica para clonar plantilla y llenar datos de un solo paciente"""
    try:
        # Extraer info
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        dia_num = dt.day
        
        # A. Clonación: Insertar espacio y desplazar (A3:AI10 -> A11:AI18)
        hoja.insert_rows([[''] * 35] * 8, row=11)
        rango_plantilla = hoja.get('A3:AI10')
        hoja.update(range_name='A11:AI18', values=rango_plantilla)

        # B. Limpieza de X en fila 4 original
        limpieza_x = [[''] * 31]
        hoja.update(range_name='D4:AH4', values=limpieza_x)

        # C. Llenado de datos en plantilla superior
        hoja.update_acell('B3', str(fila_datos.iloc[1]))  # Especialidad
        hoja.update_acell('B4', str(fila_datos.iloc[2]))  # Cama
        hoja.update_acell('A5', str(fila_datos.iloc[4]))  # Paciente
        hoja.update_acell('B8', str(fila_datos.iloc[6]))  # Edad
        hoja.update_acell('B9', str(fila_datos.iloc[3]))  # Registro
        hoja.update_acell('B10', str(fila_datos.iloc[8])) # Ingreso

        # D. Nueva X
        columna_x = dia_num + 3
        hoja.update_cell(4, columna_x, "X")
        return True
    except Exception as e:
        st.error(f"Error procesando a {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    # Fila de botones superiores
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        st.link_button("📂 Ver Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes listos para capturar", len(df_pacientes))

    st.divider()

    # Opción 1: Captura Individual
    with st.expander("🎯 Captura Individual"):
        with st.form("individual"):
            nombres = df_pacientes.iloc[:, 4].dropna().unique().tolist()
            p_sel = st.selectbox("Selecciona Paciente:", nombres)
            if st.form_submit_button("Registrar Solo Este"):
                hoja = conectar_google_sheets()
                if hoja:
                    f_datos = df_pacientes[df_pacientes.iloc[:, 4] == p_sel].iloc[0]
                    if vaciar_paciente(hoja, f_datos):
                        st.success(f"Registrado: {p_sel}")
                        st.balloons()

    # Opción 2: Captura Masiva
    st.subheader("🚀 Acciones Masivas")
    if st.button("📥 Capturar TODOS los pacientes del censo", type="primary"):
        hoja = conectar_google_sheets()
        if hoja:
            progreso = st.progress(0)
            status_text = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre_p = row.iloc[4]
                status_text.text(f"Procesando {i+1}/{total}: {nombre_p}")
                vaciar_paciente(hoja, row)
                progreso.progress((i + 1) / total)
                time.sleep(1) # Pausa breve para evitar bloqueos de API de Google
            
            status_text.success(f"✅ ¡Se han capturado {total} pacientes exitosamente!")
            st.balloons()

else:
    st.warning("No se detectó el censo de origen.")
