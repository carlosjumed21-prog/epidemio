import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Sincronizador de Vigilancia (Mapeo por Registro)")

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
        st.error(f"Error de conexión: {e}")
        return None, None, None

# --- 2. LECTURA DEL CENSO ---
URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo_nube():
    try:
        return pd.read_csv(URL_CENSO)
    except:
        return None

# --- 3. MOTOR DE VIGILANCIA (NUEVO vs EXISTENTE) ---
def procesar_registro(ss, h_maestra, h_historial, fila_datos, reg_map):
    # Extraemos datos del censo (A=0, B=1, C=2, D=3, E=4, G=6, I=8)
    registro = str(fila_datos.iloc[3]).strip()
    fecha_str = str(fila_datos.iloc[0])
    dia = int(fecha_str.split('/')[0])
    col_x = dia + 3 # Día 1 = Col D (4)

    if registro in reg_map:
        # --- PACIENTE EXISTENTE ---
        fila_base = reg_map[registro]
        accion = "Actualizado"
    else:
        # --- PACIENTE NUEVO ---
        vals = h_historial.get_all_values()
        fila_base = len(vals) + 1
        # Clonar Plantilla (CopyPaste Request)
        body = {"requests": [{"copyPaste": {
            "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
            "destination": {"sheetId": h_historial.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
            "pasteType": "PASTE_NORMAL"
        }}]}
        ss.batch_update(body)
        accion = "Nuevo"

    # ESCRIBIR/ACTUALIZAR DATOS EN EL BLOQUE (B3, B4, A5, B7, B8, B9)
    # B3 es fila_base, B4 es fila_base+1, A5 es fila_base+2, B7 es fila_base+4, B8 es fila_base+5, B9 es fila_base+6
    batch_updates = [
        {'range': f'Historial!B{fila_base}',     'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
        {'range': f'Historial!B{fila_base + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
        {'range': f'Historial!A{fila_base + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
        {'range': f'Historial!B{fila_base + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
        {'range': f'Historial!B{fila_base + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
        {'range': f'Historial!B{fila_base + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso
    ]
    ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': batch_updates})
    
    # Marcar X en la fila 4 del bloque (fila_base + 1)
    h_historial.update_cell(fila_base + 1, col_x, "X")
    return accion

# --- 4. INTERFAZ ---
if st.button("🔄 1. REFRESH: Cargar Censo Actual"):
    df = cargar_censo_nube()
    if df is not None:
        st.session_state['df_vig'] = df
        st.success(f"Censo listo con {len(df)} pacientes.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    st.dataframe(df.iloc[:, [3,4,2]], use_container_width=True) # Vista rápida: Registro, Nombre, Cama

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚩 INICIO DE VIGILANCIA (BORRAR TODO)"):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial reseteado. Creando base...")
                for i, row in df.iterrows():
                    procesar_registro(ss, h_ma, h_hi, row, {})
                    time.sleep(4)
                st.success("Base de vigilancia creada.")

    with col2:
        if st.button("🔄 VIGILANCIA DIARIA (ACTUALIZAR)", type="primary"):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                msg = st.empty()
                msg.info("Buscando registros existentes en el Historial...")
                
                # Leemos la columna B del historial para buscar registros (donde cae el B8)
                # Obtenemos todos los valores de la columna B
                col_b = h_historial.col_values(2) # Columna B es la 2
                reg_map = {}
                # Buscamos el registro en las posiciones 8, 16, 24... (índices 7, 15, 23...)
                for idx, val in enumerate(col_b):
                    clean_val = str(val).strip()
                    if clean_val and clean_val.isdigit(): # Si parece un número de registro
                        # El bloque empieza 5 filas arriba de donde está el registro (B8)
                        fila_inicio_bloque = (idx + 1) - 5
                        reg_map[clean_val] = fila_inicio_bloque
                
                prog = st.progress(0)
                for i, row in df.iterrows():
                    nombre = row.iloc[4]
                    msg.text(f"Analizando: {nombre}")
                    procesar_registro(ss, h_ma, h_hi, row, reg_map)
                    prog.progress((i+1)/len(df))
                    time.sleep(4)
                msg.success("Sincronización completa: Se actualizaron existentes y se añadieron nuevos.")
