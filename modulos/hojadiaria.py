import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONEXIÓN SEGURA ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # ID de tu hoja de salida
        SHEET_ID = "116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc"
        spreadsheet = client.open_by_key(SHEET_ID)
        return spreadsheet.get_worksheet(0) 
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

# --- 2. LECTURA DEL CENSO (VISTA PREVIA) ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

# Forzamos la recarga de datos para recuperar la vista previa
def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except Exception as e:
        return None

df_pacientes = cargar_censo()

# --- 3. LÓGICA DE VACIADO ROBUSTA ---
def vaciar_con_reintento(hoja, fila_datos):
    max_reintentos = 2
    for intento in range(max_reintentos):
        try:
            # Procesar datos
            dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
            columna_x = dt.day + 3

            # PASO 1: Insertar filas y copiar rango (Sintaxis corregida para gspread)
            hoja.insert_rows([[''] * 35] * 8, row=11)
            # copy_range en versiones actuales solo requiere origen y destino
            hoja.copy_range("A3:AI10", "A11:AI18") 

            # PASO 2: Actualización por lotes
            batch = [
                {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
                {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
                {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
                {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
                {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
                {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
                {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X
            ]
            hoja.batch_update(batch)

            # PASO 3: Nueva X
            hoja.update_cell(4, columna_x, "X")
            return True

        except Exception as e:
            if "429" in str(e):
                st.warning(f"⏳ Pausa por límite de Google (Paciente: {fila_datos.iloc[4]}). Esperando 20s...")
                time.sleep(20)
            else:
                st.error(f"❌ Error técnico: {e}")
                return False
    return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    # Botón para abrir el archivo
    st.link_button("📂 Abrir Hoja de Salida", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes detectados", len(df_pacientes))
    
    # Vista previa restaurada
    with st.expander("🔍 Ver listado de pacientes para capturar"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    if st.button("📥 INICIAR VACIADO MASIVO", type="primary"):
        hoja = conectar_google_sheets()
        if hoja:
            progreso = st.progress(0)
            status = st.empty()
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Procesando {i+1}/{len(df_pacientes)}: {nombre}")
                
                if vaciar_con_reintento(hoja, row):
                    progreso.progress((i + 1) / len(df_pacientes))
                    # Pausa obligatoria de 8 segundos para que Google no nos bloquee el formato
                    time.sleep(8)
                else:
                    st.error("Se detuvo el proceso por un error persistente.")
                    break
            
            status.success("✅ ¡Censo completado exitosamente!")
            st.balloons()
else:
    st.error("❌ No se pudo cargar la vista previa del censo. Verifica la conexión.")
