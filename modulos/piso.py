import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🕵️ Vigilancia Epidemiológica de Piso")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        hoja_maestra = ss.get_worksheet(0)
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="5000", cols="35")
            
        return ss, hoja_maestra, hoja_historial
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None, None

# --- 2. LÓGICA DE PROCESAMIENTO ---
def procesar_vigilancia(ss, h_maestra, h_historial, fila_datos, reg_map, index_nuevo):
    # Mapeo de origen: A=0, B=1, C=2, D=3, E=4, G=6, I=8
    fecha_str = str(fila_datos.iloc[0])
    registro = str(fila_datos.iloc[3])
    
    # Calcular Columna X según el día del mes
    try:
        dia = int(fecha_str.split('/')[0])
        col_x = dia + 3
    except:
        col_x = 4

    # DETERMINAR SI ES NUEVO O EXISTENTE
    if registro in reg_map:
        fila_base = reg_map[registro]
        accion = "Actualizado"
    else:
        # Si es nuevo, se coloca al final del historial actual
        vals_hist = h_historial.get_all_values()
        fila_base = len(vals_hist) + 1
        
        # Clonar Plantilla (A3:AI10 de Hoja 1)
        body = {
            "requests": [{
                "copyPaste": {
                    "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                    "destination": {"sheetId": h_historial.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                    "pasteType": "PASTE_NORMAL"
                }
            ]}
        }
        ss.batch_update(body)
        
        # Llenar datos fijos por ser nuevo
        updates_fijos = [
            {'range': f'Historial!B{fila_base + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': f'Historial!B{fila_base + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': f'Historial!A{fila_base + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': f'Historial!B{fila_base + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': f'Historial!B{fila_base + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': f'Historial!B{fila_base + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': updates_fijos})
        accion = "Nuevo"

    # Marcar la "X" en la fecha (esto se hace siempre)
    h_historial.update_cell(fila_base + 1, col_x, "X")
    return accion

# --- 3. INTERFAZ ---
URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

df_censo = pd.read_csv(URL_CENSO)

if df_censo is not None:
    st.metric("Pacientes en Censo Actual", len(df_censo))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚩 Inicio de Vigilancia", help="Borra el historial y empieza de cero con este censo"):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear() # Limpiar todo
                st.info("Iniciando vigilancia desde cero...")
                # Aquí procesaría a todos como nuevos
                reg_map = {} 
                for i, row in df_censo.iterrows():
                    procesar_vigilancia(ss, h_ma, h_hi, row, reg_map, i)
                    time.sleep(5)
                st.success("Vigilancia iniciada.")

    with col2:
        if st.button("🔄 Vigilancia Diaria", type="primary", help="Compara y actualiza sin duplicar"):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                status.info("Escaneando pacientes existentes en historial...")
                
                # Obtener registros existentes (Celda B8 de cada bloque)
                data_hist = h_hi.get_all_values()
                reg_map = {}
                for r in range(5, len(data_hist), 8):
                    reg_val = str(data_hist[r][1]).strip()
                    if reg_val: reg_map[reg_val] = r - 5 + 1
                
                progreso = st.progress(0)
                for i, row in df_censo.iterrows():
                    status.text(f"Analizando: {row.iloc[4]}")
                    procesar_vigilancia(ss, h_ma, h_hi, row, reg_map, i)
                    progreso.progress((i+1)/len(df_censo))
                    time.sleep(5)
                
                status.success("Vigilancia diaria completada.")
