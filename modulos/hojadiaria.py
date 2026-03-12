import streamlit as st
import pandas as pd
import gspread
from gspread_formatting import * # Librería para asegurar formatos si fuera necesario
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONEXIÓN ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        # Necesitamos el objeto spreadsheet para operaciones de copiado
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        return ss.get_worksheet(0)
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

# --- 2. LECTURA ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_datos():
    return pd.read_csv(URL_ORIGEN)

df_pacientes = cargar_datos()

# --- 3. FUNCIÓN DE VACIADO CON FORMATO ---
def vaciar_paciente_con_formato(hoja, fila_datos):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        dia_num = dt.day
        columna_x = dia_num + 3

        # 1. CLONACIÓN CON FORMATO
        # Insertamos las 8 filas vacías
        hoja.insert_rows([[''] * 35] * 8, row=11)
        
        # Copiamos el rango A3:AI10 al A11:AI18 manteniendo TODO el formato
        # Esta función de gspread es la que permite duplicar colores, bordes, etc.
        hoja.copy_range("A3:AI10", "A11:AI18", copy_format=True, strategy="DEFAULT")

        # 2. VACIADO DE DATOS (Batch)
        batch_data = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X
        ]
        hoja.batch_update(batch_data)

        # 3. Colocar la nueva X
        hoja.update_cell(4, columna_x, "X")
        
        return True
    except Exception as e:
        if "429" in str(e):
            time.sleep(10)
            return False
        st.error(f"Error con {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    col1, col2 = st.columns([1, 4])
    with col1:
        st.link_button("📂 Abrir Sheet", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes en Censo", len(df_pacientes))
    st.divider()

    # Opción Masiva
    if st.button("📥 Capturar TODO el Censo con Formato", type="primary"):
        hoja = conectar_google_sheets()
        if hoja:
            progreso = st.progress(0)
            status = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre_p = row.iloc[4]
                status.text(f"Procesando {i+1}/{total}: {nombre_p}")
                
                exito = vaciar_paciente_con_formato(hoja, row)
                if not exito: # Reintento por cuota
                    time.sleep(5)
                    vaciar_paciente_con_formato(hoja, row)
                
                progreso.progress((i + 1) / total)
                time.sleep(3) # Pausa más larga para proteger la cuota de formato
            
            status.success(f"✅ ¡Vaciado masivo completado con éxito!")
            st.balloons()
else:
    st.error("No se pudo cargar el censo.")
