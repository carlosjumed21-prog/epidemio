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
        
        # ID de tu Spreadsheet Maestro
        ss = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        
        # Localización de pestañas por nombre para obtener el sheetId correcto
        h_maestra = ss.get_worksheet(0) # Asumimos que la plantilla es la primera pestaña
        
        try:
            h_hoja2 = ss.worksheet("Hoja 2")     # Fuente de datos limpia
            h_historial = ss.worksheet("Historial") # Destino
        except Exception as e:
            st.error(f"❌ Error: No se encontró la pestaña 'Hoja 2' o 'Historial'. {e}")
            return None, None, None, None
            
        return ss, h_maestra, h_hoja2, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """Escribe los datos en el bloque y marca la X en el día"""
    try:
        lista_celdas = [
            gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     # Especialidad
            gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), # Cama
            gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), # Nombre Paciente
            gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), # Edad
            gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), # Registro/RFC
            gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), # Fecha Ingreso
            gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  # Tachado día
        ]
        h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    except Exception as e:
        st.error(f"Error al escribir datos: {e}")

# --- 3. INTERFAZ ---
st.title("🏥 Vigilancia Epidemiológica - Automatización")

if st.button("🔄 1. REFRESH: Cargar desde Hoja 2", use_container_width=True):
    ss, h_ma, h_h2, h_hi = conectar_google_sheets()
    if ss:
        datos = h_h2.get_all_records()
        df = pd.DataFrame(datos)
        st.session_state['df_vig'] = df
        st.success(f"✅ Se cargaron {len(df)} pacientes desde la Hoja 2.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        if st.button("🚩 INICIO (RECREAR TODO EL HISTORIAL)", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear() # Borra todo el historial
                f_nueva = 1
                prog = st.progress(0)
                for i, row in df.iterrows():
                    # EXPLICACIÓN: Copiamos de h_maestra a h_historial usando sus IDs reales
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hi.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    
                    # Tachado de fecha (Columna A -> Índice 0)
                    try:
                        dia = int(str(row.iloc[0]).split('/')[0])
                        actualizar_bloque_paciente(h_hi, f_nueva, row, dia + 3)
                    except: pass
                    
                    f_nueva += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(1.5) # Pausa para evitar error de API
                st.success("✅ Plantillas creadas desde cero.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (SIN DUPLICADOS)", type="primary", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                col_b = h_hi.col_values(2) # Columna B del Historial (Registros)
                reg_map = {}
                
                # Mapear dónde está cada registro ya creado
                for i in range(5, len(col_b), 8):
                    val = str(col_b[i]).strip()
                    if val and val not in ["", "Registro"]:
                        reg_map[val] = (i + 1) - 5

                f_disponible = len(col_b) + 1
                for idx, row in df.iterrows():
                    reg_id = str(row.iloc[3]).strip()
                    try:
                        dia = int(str(row.iloc[0]).split('/')[0])
                        col_tachado = dia + 3
                    except: col_tachado = 4
                    
                    if reg_id in reg_map:
                        # Si ya existe, solo tachamos el nuevo día
                        actualizar_bloque_paciente(h_hi, reg_map[reg_id], row, col_tachado)
                    else:
                        # Si es nuevo, CREAMOS LA PLANTILLA
                        ss.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_hi.id, "startRowIndex": f_disponible - 1, "endRowIndex": f_disponible + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_hi, f_disponible, row, col_tachado)
                        f_disponible += 8
                    
                    time.sleep(1.5)
                st.success("✅ Vigilancia diaria actualizada.")
