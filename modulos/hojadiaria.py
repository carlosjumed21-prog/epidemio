import streamlit as st
import pandas as pd
import gspread
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
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        return ss.get_worksheet(0)
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_datos():
    return pd.read_csv(URL_ORIGEN)

df_pacientes = cargar_datos()

# --- 3. FUNCIÓN DE VACIADO (RESISTENTE A ERRORES DE CUOTA) ---
def vaciar_paciente_robusto(hoja, fila_datos):
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
            dia_num = dt.day
            columna_x = dia_num + 3

            # PASO A: Clonar plantilla con TODO el formato (Copiado interno de Google)
            hoja.insert_rows([[''] * 35] * 8, row=11)
            hoja.copy_range("A3:AI10", "A11:AI18", copy_format=True, strategy="DEFAULT")

            # PASO B: Actualización por lotes (Batch Update) para ahorrar peticiones
            batch_updates = [
                {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
                {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
                {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
                {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
                {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
                {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
                {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X previas
            ]
            hoja.batch_update(batch_updates)

            # PASO C: Nueva X
            hoja.update_cell(4, columna_x, "X")
            
            return True # Éxito

        except Exception as e:
            if "429" in str(e):
                intentos += 1
                st.warning(f"⏳ Límite de Google alcanzado. Reintentando en 15 segundos... (Intento {intentos})")
                time.sleep(15)
            else:
                st.error(f"❌ Error crítico con {fila_datos.iloc[4]}: {e}")
                return False
    return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    col1, col2 = st.columns([1, 4])
    with col1:
        st.link_button("📂 Abrir Sheet", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes por Procesar", len(df_pacientes))
    st.divider()

    if st.button("📥 Iniciar Vaciado Masivo (Con Formato)", type="primary"):
        hoja = conectar_google_sheets()
        if hoja:
            bar_progreso = st.progress(0)
            txt_status = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre_p = row.iloc[4]
                txt_status.text(f"📝 Procesando ({i+1}/{total}): {nombre_p}")
                
                exito = vaciar_paciente_robusto(hoja, row)
                
                if exito:
                    bar_progreso.progress((i + 1) / total)
                    # PAUSA DE SEGURIDAD PARA MANTENER EL FORMATO
                    time.sleep(6) 
                else:
                    st.error(f"No se pudo procesar a {nombre_p}. Se detuvo el proceso.")
                    break
            
            if exito:
                txt_status.success(f"✅ ¡Censo completado! {total} plantillas generadas con éxito.")
                st.balloons()
else:
    st.error("No se pudo cargar el censo.")
