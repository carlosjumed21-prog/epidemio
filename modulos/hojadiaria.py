import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

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
        
        h_maestra = ss.get_worksheet(0)
        try:
            h_historial = ss.worksheet("Historial")
        except:
            h_historial = ss.add_worksheet(title="Historial", rows="5000", cols="35")
        return ss, h_maestra, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. MOTOR DE PROCESAMIENTO OPTIMIZADO ---
def preparar_datos_paciente(h_maestra, h_historial, fila_datos, reg_map, fila_disponible_nueva):
    registro = str(fila_datos.iloc[3]).strip()
    fecha_str = str(fila_datos.iloc[0])
    dia = int(fecha_str.split('/')[0])
    col_x = dia + 3 

    requests_formato = []
    batch_data = []
    es_nuevo = False
    fila_actual_bloque = 0

    if registro in reg_map:
        fila_actual_bloque = reg_map[registro]
    else:
        fila_actual_bloque = fila_disponible_nueva
        es_nuevo = True
        # Request para clonar plantilla
        requests_formato.append({
            "copyPaste": {
                "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                "destination": {"sheetId": h_historial.id, "startRowIndex": fila_actual_bloque - 1, "endRowIndex": fila_actual_bloque + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                "pasteType": "PASTE_NORMAL"
            }
        })

    # Datos a escribir
    celdas_y_valores = [
        (f'B{fila_actual_bloque}', str(fila_datos.iloc[1])),     # Especialidad
        (f'B{fila_actual_bloque + 1}', str(fila_datos.iloc[2])), # Cama
        (f'A{fila_actual_bloque + 2}', str(fila_datos.iloc[4])), # Paciente
        (f'B{fila_actual_bloque + 4}', str(fila_datos.iloc[6])), # Edad
        (f'B{fila_actual_bloque + 5}', str(fila_datos.iloc[3])), # Registro
        (f'B{fila_actual_bloque + 6}', str(fila_datos.iloc[8]))  # Ingreso
    ]
    
    for celda, valor in celdas_y_valores:
        batch_data.append({'range': f'Historial!{celda}', 'values': [[valor]]})
    
    # Marcado de X (Columna dinámica)
    letra_col = gspread.utils.rowcol_to_a1(fila_actual_bloque + 1, col_x)
    batch_data.append({'range': f'Historial!{letra_col}', 'values': [['X']]})

    return requests_formato, batch_data, es_nuevo

# --- 3. INTERFAZ ---
st.title("🏥 Vigilancia Epidemiológica")

if st.button("🔄 REFRESH: Cargar Censo", use_container_width=True):
    URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
    try:
        df = pd.read_csv(URL_CENSO)
        st.session_state['df_vig'] = df
        st.success("Censo cargado.")
    except: st.error("Error al cargar.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    st.metric("📊 Pacientes en Censo", len(df))
    
    if st.button("🚀 VIGILANCIA DIARIA (Sincronización Total)", type="primary", use_container_width=True):
        ss, h_ma, h_hi = conectar_google_sheets()
        if ss:
            status = st.empty()
            status.info("🔍 Mapeando historial y preparando datos...")
            
            # 1. Mapeo inicial
            data_h = h_hi.get_all_values()
            reg_map = {}
            for r in range(5, len(data_h), 8):
                rv = str(data_h[r][1]).strip()
                if rv: reg_map[rv] = r - 5 + 1
            
            fila_nueva = len(data_h) + 1
            all_format_reqs = []
            all_batch_data = []

            # 2. Procesar pacientes localmente (Rápido)
            for i, row in df.iterrows():
                f_reqs, b_data, es_nuevo = preparar_datos_paciente(h_ma, h_hi, row, reg_map, fila_nueva)
                all_format_reqs.extend(f_reqs)
                all_batch_data.extend(b_data)
                if es_nuevo: fila_nueva += 8
            
            # 3. EJECUCIÓN MASIVA (Pocas peticiones a la API)
            try:
                if all_format_reqs:
                    status.text("🎨 Clonando plantillas nuevas...")
                    ss.batch_update({"requests": all_format_reqs})
                
                status.text("✍️ Escribiendo datos clínicos...")
                ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': all_batch_data})
                
                status.success("✅ ¡Sincronización terminada con éxito!")
                st.balloons()
            except Exception as e:
                st.error(f"Error en la subida masiva: {e}")
