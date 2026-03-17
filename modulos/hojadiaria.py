import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
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
        
        # ID de tu Sheet Maestro (1yKg...)
        ss = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        
        h_maestra = ss.get_worksheet(0) # Plantilla original (pestaña 1)
        
        try:
            h_hoja2 = ss.worksheet("Hoja 2")
            h_historial = ss.worksheet("Historial")
        except:
            st.error("❌ Revisa que existan las pestañas 'Hoja 2' e 'Historial'.")
            return None, None, None, None
            
        return ss, h_maestra, h_hoja2, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN DE CELDAS ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """Actualiza datos y pone la 'X' en la columna del día correspondiente"""
    try:
        lista_celdas = [
            gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     # Especialidad
            gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), # Cama
            gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), # Nombre Paciente
            gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), # Edad
            gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), # Registro/RFC
            gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), # Fecha Ingreso
            gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  # Tachado 'X'
        ]
        h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    except Exception as e:
        st.warning(f"No se pudo actualizar el bloque en fila {fila_base}: {e}")

# --- 3. INTERFAZ ---
st.title("🏥 Generación de Vigilancia Epidemiológica")

if st.button("🔄 1. REFRESH: Cargar desde Hoja 2", use_container_width=True):
    ss, h_ma, h_h2, h_hi = conectar_google_sheets()
    if ss:
        # Forzamos leer la Hoja 2 como DF
        df = pd.DataFrame(h_h2.get_all_records())
        st.session_state['df_vig'] = df
        st.success(f"✅ Datos cargados de Hoja 2: {len(df)} pacientes.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        if st.button("🚩 INICIO (RECREAR HISTORIAL)", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                f_nueva = 1
                prog = st.progress(0)
                for i, row in df.iterrows():
                    # Copiar Plantilla
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hi.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    
                    # Lógica del día para tachar: Columna A (index 0)
                    try:
                        # Extraemos el día (ej: '17/03/2026' -> 17)
                        fecha_str = str(row.iloc[0])
                        dia_num = int(fecha_str.split('/')[0])
                        col_tachado = dia_num + 3 # Ajuste a tu formato (Día 1 es columna 4)
                        
                        actualizar_bloque_paciente(h_hi, f_nueva, row, col_tachado)
                    except: pass
                    
                    f_nueva += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(1.2)
                st.success("✅ Historial recreado.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (SEGUIMIENTO)", type="primary", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                col_b = h_hi.col_values(2) # Columna de Registros en Historial
                reg_map = {}
                
                # Mapear dónde está cada paciente (bloques de 8)
                for i in range(5, len(col_b), 8):
                    val = str(col_b[i]).strip()
                    if val and val not in ["", "Registro"]:
                        reg_map[val] = (i + 1) - 5

                f_disponible = len(col_b) + 1
                for idx, row in df.iterrows():
                    reg_id = str(row.iloc[3]).strip()
                    
                    # Obtener día para tachar
                    try:
                        dia_num = int(str(row.iloc[0]).split('/')[0])
                        col_tachado = dia_num + 3
                    except: col_tachado = 4 # Default día 1 si falla
                    
                    status.text(f"Procesando: {row.iloc[4]}")

                    if reg_id in reg_map:
                        actualizar_bloque_paciente(h_hi, reg_map[reg_id], row, col_tachado)
                    else:
                        # Paciente Nuevo
                        ss.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_hi.id, "startRowIndex": f_disponible - 1, "endRowIndex": f_disponible + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_hi, f_disponible, row, col_tachado)
                        f_disponible += 8
                    
                    time.sleep(1.2)
                st.success("✅ Sincronización completa.")
