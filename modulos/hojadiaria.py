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

# --- 2. MOTOR DE PROCESAMIENTO ---
def procesar_paciente_individual(ss, h_ma, h_hi, fila_datos, reg_map, fila_disponible):
    registro = str(fila_datos.iloc[3]).strip()
    fecha_str = str(fila_datos.iloc[0])
    dia = int(fecha_str.split('/')[0])
    col_x = dia + 3
    
    es_nuevo = False
    if registro in reg_map:
        fila_base = reg_map[registro]
    else:
        fila_base = fila_disponible
        es_nuevo = True
        # Clonar Plantilla Base
        body = {"requests": [{"copyPaste": {
            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
            "destination": {"sheetId": h_hi.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
            "pasteType": "PASTE_NORMAL"
        }}]}
        ss.batch_update(body)

    # Crear objetos Cell localmente
    lista_celdas = [
        gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     # B3
        gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), # B4
        gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), # A5
        gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), # B7
        gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), # B8
        gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), # B9
        gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  # Marcado día
    ]
    
    h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    return es_nuevo

# --- 3. INTERFAZ ---
st.title("🏥 Gestión de Vigilancia Epidemiológica")

# Botón de Refresh
if st.button("🔄 REFRESH: Cargar Censo Actual", use_container_width=True):
    URL_CENSO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
    try:
        df_cloud = pd.read_csv(URL_CENSO)
        st.session_state['df_vig'] = df_cloud
        st.success(f"✅ Censo obtenido: {len(df_cloud)} pacientes.")
    except:
        st.error("❌ No se pudo conectar con el Censo en la nube.")

# Mostrar botones solo si hay datos cargados
if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    st.metric("👥 Pacientes en Censo", len(df))
    
    st.divider()
    st.subheader("🛠️ Acciones de Sincronización")
    
    col_inic, col_diaria = st.columns(2)

    with col_inic:
        # Botón de Inicio (Generación de base)
        if st.button("🚩 INICIO DE VIGILANCIA", use_container_width=True, help="Borra historial y crea plantillas desde cero"):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("🧹 Limpiando historial... Generando cuadros nuevos.")
                prog = st.progress(0)
                fila_n = 1
                for i, row in df.iterrows():
                    procesar_paciente_individual(ss, h_ma, h_hi, row, {}, fila_n)
                    fila_n += 8
                    prog.progress((i+1)/len(df))
                    time.sleep(3)
                st.success("✅ Vigilancia inicial completada.")

    with col_diaria:
        # Botón de Vigilancia Diaria (Sincronización con reporte)
        if st.button("🔄 VIGILANCIA DIARIA", type="primary", use_container_width=True):
            ss, h_ma, h_hi = conectar_google_sheets()
            if ss:
                status = st.empty()
                status.info("🔍 Analizando historial...")
                
                # Mapear registros en el historial
                data_h = h_hi.get_all_values()
                reg_map = {}
                registros_en_historial = set()
                
                for r in range(5, len(data_h), 8):
                    if r < len(data_h):
                        rv = str(data_h[r][1]).strip()
                        if rv != "":
                            reg_map[rv] = r - 5 + 1
                            registros_en_historial.add(rv)
                
                ingresos = 0
                seguimientos = 0
                registros_procesados = set()
                fila_nueva = len(data_h) + 1
                
                prog = st.progress(0)
                for i, row in df.iterrows():
                    reg_id = str(row.iloc[3]).strip()
                    status.text(f"Procesando: {row.iloc[4]}")
                    
                    es_nuevo = procesar_paciente_individual(ss, h_ma, h_hi, row, reg_map, fila_nueva)
                    
                    if es_nuevo:
                        ingresos += 1
                        fila_nueva += 8
                    else:
                        seguimientos += 1
                    
                    registros_procesados.add(reg_id)
                    prog.progress((i+1)/len(df))
                    time.sleep(3)

                # Calcular Egresos (Altas)
                egresos_lista = registros_en_historial - registros_procesados
                num_egresos = len(egresos_lista)

                status.empty()
                st.divider()
                st.subheader("📋 Reporte Epidemiológico")
                r1, r2, r3 = st.columns(3)
                r1.metric("🆕 Ingresos", ingresos)
                r2.metric("📋 Seguimientos", seguimientos)
                r3.metric("🚪 Egresos", num_egresos)
                
                if num_egresos > 0:
                    with st.expander("📝 Ver Registros de Egresos"):
                        st.write(list(egresos_lista))
                
                st.success("✅ Sincronización exitosa.")
                st.balloons()
