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
        
        # ID de tu Spreadsheet (donde están Hoja 2, Plantilla e Historial)
        ss = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        
        h_maestra = ss.get_worksheet(0) # Pestaña de Plantilla (Hoja 1 original)
        
        try:
            h_hoja2 = ss.worksheet("Hoja 2") # Origen de datos filtrados
            h_historial = ss.worksheet("Historial") # Destino de plantillas
        except:
            st.error("⚠️ No se encontró la 'Hoja 2' o 'Historial'. Ejecuta el filtrado primero.")
            return None, None, None, None
            
        return ss, h_maestra, h_hoja2, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """Actualiza datos clínicos y marca la X acorde al día del mes"""
    lista_celdas = [
        gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     # B: Especialidad
        gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), # B: Cama
        gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), # A: Paciente
        gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), # B: Edad
        gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), # B: Registro
        gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), # B: F. Ingreso
        gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  # Marcado X
    ]
    h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')

# --- 3. INTERFAZ ---
st.title("🏥 Vigilancia Epidemiológica - Control de Duplicados")
st.info("Fuente de datos activa: **Hoja 2** (Censo Filtrado)")

# Botón REFRESH: Ahora lee internamente de la Hoja 2
if st.button("🔄 1. REFRESH: Cargar Censo desde Hoja 2", use_container_width=True):
    try:
        ss, h_ma, h_h2, h_hi = conectar_google_sheets()
        if ss:
            # Obtener todos los registros de la Hoja 2
            datos = h_h2.get_all_records()
            df = pd.DataFrame(datos)
            st.session_state['df_vig'] = df
            st.success(f"Censo cargado desde Hoja 2: {len(df)} pacientes.")
    except Exception as e:
        st.error(f"Error al cargar datos internos: {e}")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    st.metric("📊 Pacientes en Censo", len(df))
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        if st.button("🚩 INICIO (LIMPIEZA TOTAL)", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial borrado. Recreando desde Hoja 2...")
                prog = st.progress(0)
                f_nueva = 1
                for i, row in df.iterrows():
                    # Clonar plantilla
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hi.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    # Calcular día para la X (Columna A)
                    dia = int(str(row.iloc[0]).split('/')[0])
                    actualizar_bloque_paciente(h_hi, f_nueva, row, dia + 3)
                    f_nueva += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(1.5)
                st.success("✅ Historial recreado con éxito.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (SIN DUPLICADOS)", type="primary", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                status.info("🔍 Mapeando Historial...")
                
                col_b = h_hi.col_values(2) 
                reg_map = {}
                
                for i in range(5, len(col_b), 8):
                    val = str(col_b[i]).strip()
                    if val and val not in ["", "Registro"]:
                        reg_map[val] = (i + 1) - 5

                ingresos = 0
                seguimientos = 0
                f_disponible = len(col_b) + 1
                prog = st.progress(0)
                
                for idx, row in df.iterrows():
                    reg_id = str(row.iloc[3]).strip()
                    dia = int(str(row.iloc[0]).split('/')[0])
                    status.text(f"Analizando: {row.iloc[4]}")

                    if reg_id in reg_map:
                        actualizar_bloque_paciente(h_hi, reg_map[reg_id], row, dia + 3)
                        seguimientos += 1
                    else:
                        ss.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_hi.id, "startRowIndex": f_disponible - 1, "endRowIndex": f_disponible + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_hi, f_disponible, row, dia + 3)
                        reg_map[reg_id] = f_disponible
                        f_disponible += 8
                        ingresos += 1
                    
                    prog.progress((idx+1)/len(df))
                    time.sleep(1.5)

                status.empty()
                st.success(f"✅ Sincronización terminada. Nuevos: {ingresos}, Seguimientos: {seguimientos}")
