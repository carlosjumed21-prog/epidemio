import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
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

# --- 2. MOTOR DE VIGILANCIA (LÓGICA DE DUPLICADOS) ---
def procesar_registro(ss, h_maestra, h_historial, fila_datos, reg_map):
    # Mapeo: A=0, B=1, C=2, D=3, E=4, G=6, I=8
    registro = str(fila_datos.iloc[3]).strip()
    fecha_str = str(fila_datos.iloc[0])
    dia = int(fecha_str.split('/')[0])
    col_x = dia + 3 

    if registro in reg_map:
        fila_base = reg_map[registro]
        accion = "Actualizado"
    else:
        vals = h_historial.get_all_values()
        fila_base = len(vals) + 1
        # Clonar Plantilla (A3:AI10)
        body = {"requests": [{"copyPaste": {
            "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
            "destination": {"sheetId": h_historial.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
            "pasteType": "PASTE_NORMAL"
        }}]}
        ss.batch_update(body)
        accion = "Nuevo"

    # Actualizar datos en el bloque
    batch_updates = [
        {'range': f'Historial!B{fila_base}',     'values': [[str(fila_datos.iloc[1])]]}, # Especialidad (B3)
        {'range': f'Historial!B{fila_base + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama (B4)
        {'range': f'Historial!A{fila_base + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente (A5)
        {'range': f'Historial!B{fila_base + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad (B7)
        {'range': f'Historial!B{fila_base + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro (B8)
        {'range': f'Historial!B{fila_base + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso (B9)
    ]
    ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': batch_updates})
    h_historial.update_cell(fila_base + 1, col_x, "X")
    return accion

# --- 3. INTERFAZ Y ENCABEZADOS RESTAURADOS ---
st.title("🏥 Vigilancia Epidemiológica")

# Botón de Refresh
if st.button("🔄 1. REFRESH: Cargar Censo Actual", use_container_width=True):
    URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
    try:
        df_cloud = pd.read_csv(URL_CENSO)
        st.session_state['df_vig'] = df_cloud
        st.success("Censo sincronizado desde la nube.")
    except:
        st.error("Error al conectar con el Censo.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    
    # --- ENCABEZADOS RESTAURADOS ---
    st.metric("📊 Total de Pacientes en Censo", len(df))
    
    with st.expander("🔍 Ver listado de pacientes para procesar"):
        st.dataframe(df.iloc[:, [3,4,2,1]], use_container_width=True, hide_index=True)

    st.divider()

    # --- BOTONES DE ACCIÓN ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚩 INICIO DE VIGILANCIA (BORRAR TODO)", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial reseteado. Creando base...")
                prog = st.progress(0)
                for i, row in df.iterrows():
                    procesar_registro(ss, h_ma, h_hi, row, {})
                    prog.progress((i+1)/len(df))
                    time.sleep(5)
                st.success("Base de vigilancia creada.")

    with col2:
        if st.button("🔄 VIGILANCIA DIARIA (ACTUALIZAR)", type="primary", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                status_msg = st.empty()
                status_msg.info("⏳ Buscando pacientes existentes en el historial...")
                
                # Corregido: Obtener columna B directamente de h_hi después de conectar
                col_b = h_hi.col_values(2) 
                reg_map = {}
                for idx, val in enumerate(col_b):
                    clean_val = str(val).strip()
                    if clean_val and clean_val.isdigit():
                        # El registro está en B8, el bloque inicia 5 filas arriba
                        fila_inicio_bloque = (idx + 1) - 5
                        reg_map[clean_val] = fila_inicio_bloque
                
                prog = st.progress(0)
                for i, row in df.iterrows():
                    nombre_p = row.iloc[4]
                    status_msg.text(f"Analizando: {nombre_p}")
                    procesar_registro(ss, h_ma, h_hi, row, reg_map)
                    prog.progress((i+1)/len(df))
                    time.sleep(5)
                status_msg.success("✅ Sincronización completa.")
                st.balloons()
