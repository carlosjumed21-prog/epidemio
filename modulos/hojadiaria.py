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

# --- 2. FUNCIÓN DE ACTUALIZACIÓN ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """Actualiza datos clínicos y marca la X acumulativa"""
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
st.title("🏥 Vigilancia Epidemiológica - Control de Duplicados")

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
        if st.button("🚩 INICIO (LIMPIEZA TOTAL)", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial borrado. Creando base desde cero...")
                prog = st.progress(0)
                f_nueva = 1
                for i, row in df.iterrows():
                    # Clonar plantilla
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_hi.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    dia = int(str(row.iloc[0]).split('/')[0])
                    actualizar_bloque_paciente(h_hi, f_nueva, row, dia + 3)
                    f_nueva += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(2)
                st.success("✅ Base inicial creada.")

    with col_diaria:
        if st.button("🔄 VIGILANCIA DIARIA (SIN DUPLICADOS)", type="primary", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                status.info("🔍 Mapeando Historial para evitar duplicados...")
                
                # 1. Obtener todos los valores de la columna B para buscar Registros
                col_b = h_hi.col_values(2) # Obtiene toda la columna B
                reg_map = {}
                
                # Buscamos el Registro en la fila 8, 16, 24... (index 7, 15, 23 en Python)
                for i in range(5, len(col_b), 8):
                    val = str(col_b[i]).strip()
                    if val and val != "" and val != "Registro":
                        # La fila base del bloque es (i+1) - 5
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
                        # PACIENTE EXISTE: Actualizar
                        actualizar_bloque_paciente(h_hi, reg_map[reg_id], row, dia + 3)
                        seguimientos += 1
                    else:
                        # PACIENTE NUEVO: Crear plantilla al final
                        ss.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_hi.id, "startRowIndex": f_disponible - 1, "endRowIndex": f_disponible + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_hi, f_disponible, row, dia + 3)
                        reg_map[reg_id] = f_disponible # Evitar duplicar si aparece 2 veces en el mismo censo
                        f_disponible += 8
                        ingresos += 1
                    
                    prog.progress((idx+1)/len(df))
                    time.sleep(2)

                status.empty()
                st.subheader("📋 Resumen Diario")
                c1, c2 = st.columns(2)
                c1.metric("🆕 Ingresos", ingresos)
                c2.metric("📋 Seguimientos", seguimientos)
                st.success("✅ Sincronización terminada correctamente.")
