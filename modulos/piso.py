import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.title("🏥 Centro de Mando: Vigilancia Activa")

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
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
        st.error(f"Error de conexión: {e}")
        return None, None, None

# --- 2. MOTOR DE PROCESAMIENTO ---
def motor_vigilancia(ss, h_maestra, h_historial, fila_datos, reg_map):
    # Mapeo estricto Carlos: A=0, B=1, C=2, D=3, E=4, G=6, I=8
    fecha_str = str(fila_datos.iloc[0])
    registro = str(fila_datos.iloc[3]).strip()
    
    try:
        dia = int(fecha_str.split('/')[0])
        col_x = dia + 3
    except:
        col_x = 4

    if registro in reg_map:
        fila_base = reg_map[registro]
        accion = "Actualizado"
    else:
        vals = h_historial.get_all_values()
        fila_base = len(vals) + 1
        
        # Clonar Plantilla (CopyPaste Request)
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
        
        # Datos fijos (B3, B4, A5, B7, B8, B9)
        datos = [
            {'range': f'Historial!B{fila_base + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': f'Historial!B{fila_base + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': f'Historial!A{fila_base + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': f'Historial!B{fila_base + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': f'Historial!B{fila_base + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': f'Historial!B{fila_base + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': datos})
        accion = "Nuevo"

    # Siempre marcar la X
    h_historial.update_cell(fila_base + 1, col_x, "X")
    return accion

# --- 3. INTERFAZ DE CONTROL ---

# Botón de Refresh principal
if st.button("🔄 REFRESH: Sincronizar Censo desde la Nube", use_container_width=True):
    URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
    try:
        df = pd.read_csv(URL_CENSO)
        st.session_state['df_censo'] = df
        st.success(f"Censo actualizado: {len(df)} pacientes encontrados.")
    except:
        st.error("No se pudo conectar con el Censo. Verifica que el archivo esté publicado como CSV.")

# Solo si hay datos cargados, mostramos las opciones de decisión
if 'df_censo' in st.session_state:
    df = st.session_state['df_censo']
    
    with st.expander("👁️ Ver pacientes detectados para procesar"):
        st.dataframe(df.iloc[:, [3,4,2,1]], use_container_width=True, hide_index=True)

    st.subheader("🛠️ ¿Qué acción realizar con este censo?")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚩 INICIO DE VIGILANCIA", help="Borra historial y crea todo de nuevo", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial reseteado. Generando nuevas plantillas...")
                prog = st.progress(0)
                for i, row in df.iterrows():
                    motor_vigilancia(ss, h_ma, h_hi, row, {})
                    prog.progress((i+1)/len(df))
                    time.sleep(4) # Pausa para evitar error 429
                st.success("¡Vigilancia inicial completa!")

    with col2:
        if st.button("🔄 VIGILANCIA DIARIA", type="primary", help="Actualiza existentes y añade nuevos", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                msg = st.empty()
                msg.info("Buscando duplicados en el historial...")
                # Mapeo de registros en B8 (filas 6, 14, 22...)
                data_h = h_hi.get_all_values()
                reg_map = {}
                for r in range(5, len(data_h), 8):
                    reg_id = str(data_h[r][1]).strip()
                    if reg_id: reg_map[reg_id] = r - 5 + 1
                
                prog = st.progress(0)
                for i, row in df.iterrows():
                    msg.text(f"Sincronizando: {row.iloc[4]}")
                    motor_vigilancia(ss, h_ma, h_hi, row, reg_map)
                    prog.progress((i+1)/len(df))
                    time.sleep(4)
                msg.success("Sincronización de seguimiento terminada.")
