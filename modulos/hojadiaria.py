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
        
        # --- ARCHIVOS ---
        # SS_DATOS: Donde filtraste los pacientes (Hoja 2)
        ss_datos = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        # SS_SALIDA: Donde está la Plantilla (Hoja 1) e Historial (Hoja 2)
        ss_salida = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        h_origen_datos = ss_datos.worksheet("Hoja 2") # Censo limpio
        h_plantilla = ss_salida.get_worksheet(0)       # Hoja 1 de salida
        h_historial = ss_salida.worksheet("Hoja 2")   # Hoja 2 de salida (Tu Historial)
        
        return ss_salida, h_plantilla, h_origen_datos, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """Mantiene tu configuración original de mapeo"""
    try:
        lista_celdas = [
            gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     # B3: Especialidad
            gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), # B4: Cama
            gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), # A5: Paciente
            gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), # B7: Edad
            gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), # B8: Registro
            gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), # B9: F. Ingreso
            gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  # Marcado X
        ]
        h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    except Exception as e:
        st.error(f"Error al actualizar celdas: {e}")

# --- 3. INTERFAZ ---
st.title("🏥 Vigilancia Epidemiológica - Salida Final")

if st.button("🔄 1. REFRESH: Cargar Datos Filtrados", use_container_width=True):
    ss_sal, h_pla, h_datos, h_hist = conectar_google_sheets()
    if ss_sal:
        df = pd.DataFrame(h_datos.get_all_records())
        st.session_state['df_vig'] = df
        st.success(f"✅ {len(df)} pacientes cargados para procesar.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        if st.button("🚩 INICIO (LIMPIEZA TOTAL HISTORIAL)", use_container_width=True):
            ss_sal, h_pla, h_datos, h_hist = conectar_google_sheets()
            if ss_sal:
                h_hist.clear()
                f_nueva = 1
                prog = st.progress(0)
                for i, row in df.iterrows():
                    # Copiamos de Hoja 1 a Hoja 2 del archivo de salida
                    ss_sal.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_pla.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hist.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    
                    dia = int(str(row.iloc[0]).split('/')[0])
                    actualizar_bloque_paciente(h_hist, f_nueva, row, dia + 3)
                    
                    f_nueva += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(1.5)
                st.success("✅ Historial recreado en Hoja 2.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (SEGUIMIENTO)", type="primary", use_container_width=True):
            ss_sal, h_pla, h_datos, h_hist = conectar_google_sheets()
            if ss_sal:
                status = st.empty()
                col_b = h_hist.col_values(2) 
                reg_map = {}
                
                for i in range(5, len(col_b), 8):
                    val = str(col_b[i]).strip()
                    if val and val not in ["", "Registro"]:
                        reg_map[val] = (i + 1) - 5

                f_disponible = len(col_b) + 1
                for idx, row in df.iterrows():
                    reg_id = str(row.iloc[3]).strip()
                    dia = int(str(row.iloc[0]).split('/')[0])
                    status.text(f"Analizando: {row.iloc[4]}")

                    if reg_id in reg_map:
                        actualizar_bloque_paciente(h_hist, reg_map[reg_id], row, dia + 3)
                    else:
                        # Nuevo: Copiar plantilla de Hoja 1 a Hoja 2
                        ss_sal.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_pla.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_hist.id, "startRowIndex": f_disponible - 1, "endRowIndex": f_disponible + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_hist, f_disponible, row, dia + 3)
                        f_disponible += 8
                    
                    time.sleep(1.5)
                st.success("✅ Vigilancia diaria terminada.")
