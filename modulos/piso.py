import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.title("🏥 Vigilancia Epidemiológica Activa")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
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
        st.error(f"Error de conexión a Sheets: {e}")
        return None, None, None

# --- 2. LÓGICA DE PROCESAMIENTO ---
def procesar_vigilancia(ss, h_maestra, h_historial, fila_datos, reg_map):
    # Mapeo: A=0, B=1, C=2, D=3, E=4, G=6, I=8
    fecha_str = str(fila_datos.iloc[0])
    registro = str(fila_datos.iloc[3])
    
    try:
        dia = int(fecha_str.split('/')[0])
        col_x = dia + 3
    except:
        col_x = 4

    if registro in reg_map:
        fila_base = reg_map[registro]
        accion = "Actualizado"
    else:
        vals_hist = h_historial.get_all_values()
        fila_base = len(vals_hist) + 1
        
        # Clonar Plantilla con la API de Google
        body = {
            "requests": [{
                "copyPaste": {
                    "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                    "destination": {"sheetId": h_historial.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                    "pasteType": "PASTE_NORMAL"
                }
            ]}
        }
        ss.batch_update(body)
        
        # Datos fijos para el nuevo paciente
        updates = [
            {'range': f'Historial!B{fila_base + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad B3
            {'range': f'Historial!B{fila_base + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama B4
            {'range': f'Historial!A{fila_base + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente A5
            {'range': f'Historial!B{fila_base + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad B7
            {'range': f'Historial!B{fila_base + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro B8
            {'range': f'Historial!B{fila_base + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso B9
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': updates})
        accion = "Nuevo"

    h_historial.update_cell(fila_base + 1, col_x, "X")
    return accion

# --- 3. CARGA DE ARCHIVO PARA VISUALIZACIÓN ---
archivo_excel = st.file_uploader("📂 Subir Censo para Vigilancia", type=["xlsx", "xls", "csv"])

if archivo_excel:
    try:
        # Cargar datos
        if archivo_excel.name.endswith('.csv'):
            df = pd.read_csv(archivo_excel)
        else:
            df = pd.read_excel(archivo_excel)
        
        st.metric("👥 Pacientes en Censo", len(df))
        
        # --- BOTONES DE ACCIÓN PRINCIPAL ---
        st.subheader("🚀 Acciones de Vigilancia")
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("🚩 Inicio de Vigilancia", use_container_width=True, help="Limpia el historial y crea la base desde cero"):
                ss, h_ma, h_hi = conectar_google_sheets()
                if ss:
                    h_hi.clear()
                    st.info("Iniciando vigilancia...")
                    progreso = st.progress(0)
                    for i, row in df.iterrows():
                        procesar_vigilancia(ss, h_ma, h_hi, row, {}, i)
                        progreso.progress((i+1)/len(df))
                        time.sleep(6)
                    st.success("Vigilancia iniciada correctamente.")

        with c2:
            if st.button("🔄 Vigilancia Diaria", type="primary", use_container_width=True, help="Sincroniza sin duplicar pacientes"):
                ss, h_ma, h_hi = conectar_google_sheets()
                if ss:
                    status = st.empty()
                    status.info("Escaneando registros en historial...")
                    data_hist = h_hi.get_all_values()
                    reg_map = {}
                    for r in range(5, len(data_hist), 8):
                        rv = str(data_hist[r][1]).strip()
                        if rv: reg_map[rv] = r - 5 + 1
                    
                    progreso = st.progress(0)
                    for i, row in df.iterrows():
                        status.text(f"Analizando: {row.iloc[4]}")
                        procesar_vigilancia(ss, h_ma, h_hi, row, reg_map)
                        progreso.progress((i+1)/len(df))
                        time.sleep(6)
                    status.success("Vigilancia diaria terminada.")

        st.divider()

        # --- SECCIÓN DE CONSULTA INDIVIDUAL (Tu código original) ---
        st.subheader("🔍 Consulta Individual de Paciente")
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("Especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("Cama:", lista_camas)

        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        with st.container(border=True):
            st.markdown(f"### 👤 {paciente.iloc[4]}")
            c1, c2, c3 = st.columns(3)
            with c1: st.write(f"**Registro:** {paciente.iloc[3]}")
            with c2: st.write(f"**Sexo/Edad:** {paciente.iloc[5]} / {paciente.iloc[6]}")
            with c3: st.info(f"**Ingreso:** {paciente.iloc[8]}")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.warning("⚠️ Sube el archivo Excel o CSV para habilitar las funciones de vigilancia.")
