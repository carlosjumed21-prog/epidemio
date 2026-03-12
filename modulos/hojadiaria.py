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

# --- 2. LÓGICA DE PROCESAMIENTO ---
def procesar_paciente_individual(ss, h_ma, h_hi, fila_datos, reg_map, fila_disponible):
    registro = str(fila_datos.iloc[3]).strip()
    dia = int(str(fila_datos.iloc[0]).split('/')[0])
    col_x = dia + 3
    
    es_nuevo = False
    if registro in reg_map:
        fila_base = reg_map[registro]
    else:
        fila_base = fila_disponible
        es_nuevo = True
        # Clonar Plantilla
        body = {"requests": [{"copyPaste": {
            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
            "destination": {"sheetId": h_hi.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
            "pasteType": "PASTE_NORMAL"
        }}]}
        ss.batch_update(body)

    # Preparar celdas a actualizar en el bloque
    # B3, B4, A5, B7, B8, B9 y la X
    celdas = [
        (fila_base, 2, str(fila_datos.iloc[1])),     # Especialidad
        (fila_base + 1, 2, str(fila_datos.iloc[2])), # Cama
        (fila_base + 2, 1, str(fila_datos.iloc[4])), # Paciente
        (fila_base + 4, 2, str(fila_datos.iloc[6])), # Edad
        (fila_base + 5, 2, str(fila_datos.iloc[3])), # Registro
        (fila_base + 6, 2, str(fila_datos.iloc[8])), # Ingreso
        (fila_base + 1, col_x, "X")                 # Marcado de fecha
    ]
    
    # Actualización por bloque para evitar saturar la API
    lista_celdas = []
    for r, c, val in celdas:
        cell = h_hi.cell(r, c)
        cell.value = val
        lista_celdas.append(cell)
    
    h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    
    return es_nuevo

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
            status.info("🔍 Analizando historial...")
            
            # Obtener registros actuales en Historial (Columna B / Fila 6 de cada bloque)
            data_h = h_hi.get_all_values()
            reg_map = {}
            for r in range(5, len(data_h), 8):
                rv = str(data_h[r][1]).strip()
                if rv: reg_map[rv] = r - 5 + 1
            
            fila_nueva = len(data_h) + 1
            progreso = st.progress(0)
            
            for i, row in df.iterrows():
                status.text(f"Procesando: {row.iloc[4]}")
                creado = procesar_paciente_individual(ss, h_ma, h_hi, row, reg_map, fila_nueva)
                if creado:
                    fila_nueva += 8
                
                progreso.progress((i + 1) / len(df))
                time.sleep(2) # Pausa pequeña para estabilidad

            status.success("✅ Sincronización terminada.")
            st.balloons()
