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

# --- 2. FUNCIÓN DE ACTUALIZACIÓN DE BLOQUE ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """
    Escribe los datos en el bloque del historial.
    """
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
st.title("🏥 Sistema de Vigilancia Epidemiológica")

if st.button("🔄 1. REFRESH: Cargar Censo Actual", use_container_width=True):
    URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
    try:
        df = pd.read_csv(URL_CENSO)
        st.session_state['df_vig'] = df
        st.success(f"Censo cargado: {len(df)} pacientes.")
    except: st.error("Error al cargar censo.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    st.metric("📊 Pacientes en Censo", len(df))
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        if st.button("🚩 INICIO DE VIGILANCIA (BORRADO TOTAL)", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial reseteado. Creando base nueva...")
                prog = st.progress(0)
                fila_n = 1
                for i, row in df.iterrows():
                    # Clonar plantilla
                    body = {"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hi.id, "startRowIndex": fila_n - 1, "endRowIndex": fila_n + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]}
                    ss.batch_update(body)
                    
                    dia = int(str(row.iloc[0]).split('/')[0])
                    actualizar_bloque_paciente(h_hi, fila_n, row, dia + 3)
                    
                    fila_n += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(2)
                st.success("✅ Base inicial creada correctamente.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (ACTUALIZACIÓN)", type="primary", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                status.info("🔍 Mapeando registros para evitar duplicados...")
                
                # Obtener registros actuales en Historial para comparar
                data_h = h_hi.get_all_values()
                reg_map = {}
                registros_historial_set = set()
                
                # Buscamos en la fila donde está el "Registro" (B8, B16, B24...)
                for r_idx, fila_lista in enumerate(data_h):
                    if len(fila_lista) > 1:
                        val_reg = str(fila_lista[1]).strip() # Columna B
                        if val_reg and val_reg.isdigit():
                            # Si es un registro, el bloque inició 5 filas arriba
                            fila_base_bloque = (r_idx + 1) - 5
                            reg_map[val_reg] = fila_base_bloque
                            registros_historial_set.add(val_reg)

                ingresos = 0
                seguimientos = 0
                procesados_hoy = set()
                fila_nueva = len(data_h) + 1
                
                prog = st.progress(0)
                for i, row in df.iterrows():
                    reg_id = str(row.iloc[3]).strip()
                    dia = int(str(row.iloc[0]).split('/')[0])
                    procesados_hoy.add(reg_id)
                    
                    if reg_id in reg_map:
                        # SEGUIMIENTO: Actualizar datos existentes
                        actualizar_bloque_paciente(h_hi, reg_map[reg_id], row, dia + 3)
                        seguimientos += 1
                    else:
                        # INGRESO: Crear plantilla nueva
                        body = {"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_hi.id, "startRowIndex": fila_nueva - 1, "endRowIndex": fila_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]}
                        ss.batch_update(body)
                        actualizar_bloque_paciente(h_hi, fila_nueva, row, dia + 3)
                        fila_nueva += 8
                        ingresos += 1
                    
                    prog.progress((i+1)/len(df))
                    time.sleep(2)

                # EGRESOS
                egresos = registros_historial_set - procesados_hoy
                
                status.empty()
                st.subheader("📋 Reporte de Sincronización")
                c1, c2, c3 = st.columns(3)
                c1.metric("🆕 Ingresos", ingresos)
                c2.metric("📋 Seguimientos", seguimientos)
                c3.metric("🚪 Egresos", len(egresos))
                st.success("Sincronización finalizada.")
