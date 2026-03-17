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
        
        # ID de tu Sheet Maestro
        ss = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        
        h_maestra = ss.get_worksheet(0) # Tu plantilla de 8 filas
        
        # Intentar conectar a Hoja 2 (Base de datos limpia)
        try:
            h_hoja2 = ss.worksheet("Hoja 2")
        except:
            st.error("❌ No se encontró la 'Hoja 2'. Asegúrate de que el proceso de filtrado se haya ejecutado.")
            return None, None, None, None

        # Intentar conectar a Historial (Donde se pegan las plantillas)
        try:
            h_historial = ss.worksheet("Historial")
        except:
            # Si no existe, la creamos para evitar el error
            h_historial = ss.add_worksheet(title="Historial", rows="5000", cols="35")
            
        return ss, h_maestra, h_hoja2, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN DE CELDAS ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
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

# --- 3. INTERFAZ ---
st.title("🏥 Vigilancia Epidemiológica (Base: Hoja 2)")

# BOTÓN REFRESH: Ahora lee directamente de tu Hoja 2
if st.button("🔄 1. REFRESH: Cargar Censo desde Hoja 2", use_container_width=True):
    try:
        ss, h_ma, h_h2, h_hi = conectar_google_sheets()
        if ss:
            datos = h_h2.get_all_records()
            df = pd.DataFrame(datos)
            st.session_state['df_vig'] = df
            st.success(f"✅ Censo cargado desde Hoja 2: {len(df)} pacientes.")
    except Exception as e: 
        st.error(f"Error al cargar datos de Hoja 2: {e}")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    st.metric("📊 Pacientes Listos para Procesar", len(df))
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        if st.button("🚩 INICIO (LIMPIEZA TOTAL HISTORIAL)", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial borrado. Creando bloques desde cero...")
                prog = st.progress(0)
                f_nueva = 1
                for i, row in df.iterrows():
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hi.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    # Obtener día de la fecha (Columna A)
                    dia = int(str(row.iloc[0]).split('/')[0])
                    actualizar_bloque_paciente(h_hi, f_nueva, row, dia + 3)
                    f_nueva += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(1.5)
                st.success("✅ Historial inicializado correctamente.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (SEGUIMIENTO)", type="primary", use_container_width=True):
            ss, h_ma, h_h2, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                status.info("🔍 Buscando pacientes en Historial...")
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
                    status.text(f"Actualizando: {row.iloc[4]}")

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
                st.success(f"✅ Proceso terminado. Nuevos: {ingresos}, Actualizados: {seguimientos}")
