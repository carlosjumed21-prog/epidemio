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

# --- 2. PREPARACIÓN DE DATOS ---
def preparar_datos_paciente(h_maestra, h_historial, fila_datos, reg_map, fila_disponible_nueva):
    registro = str(fila_datos.iloc[3]).strip()
    fecha_str = str(fila_datos.iloc[0])
    dia = int(fecha_str.split('/')[0])
    col_x = dia + 3 

    requests_formato = []
    batch_values = []
    es_nuevo = False
    fila_actual_bloque = 0

    if registro in reg_map:
        fila_actual_bloque = reg_map[registro]
    else:
        fila_actual_bloque = fila_disponible_nueva
        es_nuevo = True
        requests_formato.append({
            "copyPaste": {
                "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                "destination": {"sheetId": h_historial.id, "startRowIndex": fila_actual_bloque - 1, "endRowIndex": fila_actual_bloque + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                "pasteType": "PASTE_NORMAL"
            }
        })

    # Datos a escribir (Mapeo estricto Carlos)
    val_map = [
        (fila_actual_bloque, 2, str(fila_datos.iloc[1])),     # B3: Especialidad
        (fila_actual_bloque + 1, 2, str(fila_datos.iloc[2])), # B4: Cama
        (fila_actual_bloque + 2, 1, str(fila_datos.iloc[4])), # A5: Paciente
        (fila_actual_bloque + 4, 2, str(fila_datos.iloc[6])), # B7: Edad
        (fila_actual_bloque + 5, 2, str(fila_datos.iloc[3])), # B8: Registro
        (fila_actual_bloque + 6, 2, str(fila_datos.iloc[8])), # B9: Ingreso
        (fila_actual_bloque + 1, col_x, "X")                 # Marcado de X
    ]
    
    for r, c, val in val_map:
        range_a1 = f"Historial!{gspread.utils.rowcol_to_a1(r, c)}"
        batch_values.append({'range': range_a1, 'values': [[val]]})

    return requests_formato, batch_values, es_nuevo

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
    st.metric("📊 Total Pacientes", len(df))
    
    if st.button("🚀 VIGILANCIA DIARIA (Sincronización)", type="primary", use_container_width=True):
        ss, h_ma, h_hi = conectar_google_sheets()
        if ss:
            status = st.empty()
            status.info("🔍 Mapeando historial...")
            
            data_h = h_hi.get_all_values()
            reg_map = {}
            for r in range(5, len(data_h), 8):
                rv = str(data_h[r][1]).strip()
                if rv: reg_map[rv] = r - 5 + 1
            
            fila_nueva = len(data_h) + 1
            all_format_reqs = []
            all_batch_values = []

            for i, row in df.iterrows():
                f_reqs, b_vals, es_nuevo = preparar_datos_paciente(h_ma, h_hi, row, reg_map, fila_nueva)
                all_format_reqs.extend(f_reqs)
                all_batch_values.extend(b_vals)
                if es_nuevo: fila_nueva += 8
            
            try:
                # A. Primero aplicamos formatos (Estructura)
                if all_format_reqs:
                    status.text("🎨 Generando plantillas nuevas...")
                    ss.batch_update({"requests": all_format_reqs})
                
                # B. Luego aplicamos los valores (Datos)
                if all_batch_values:
                    status.text("✍️ Actualizando datos clínicos...")
                    # USAMOS values_batch_update PARA LOS DATOS
                    h_hi.spreadsheet.values_batch_update({
                        'valueInputOption': 'USER_ENTERED', 
                        'data': all_batch_values
                    })
                
                status.success("✅ Sincronización terminada con éxito.")
                st.balloons()
            except Exception as e:
                st.error(f"Error técnico en la subida: {e}")
