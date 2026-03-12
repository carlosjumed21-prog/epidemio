import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # ID de la hoja de salida
        SHEET_ID = "116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc"
        spreadsheet = client.open_by_key(SHEET_ID)
        return spreadsheet.get_worksheet(0) 
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

# --- 2. LECTURA DEL CENSO (ORIGEN) ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_censo_publico():
    try:
        return pd.read_csv(URL_ORIGEN)
    except Exception as e:
        st.error(f"Error al leer el censo de origen: {e}")
        return None

df_pacientes = cargar_censo_publico()

# --- 3. INTERFAZ Y LÓGICA ---
if df_pacientes is not None:
    st.metric("Pacientes en Censo", len(df_pacientes))
    
    with st.expander("Ver tabla de origen"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    with st.form("registro_kardex"):
        st.subheader("✍️ Vaciado a Hoja Diaria")
        
        # Selección por nombre (Columna E / Índice 4)
        nombres = df_pacientes.iloc[:, 4].dropna().unique().tolist()
        paciente_sel = st.selectbox("Selecciona al Paciente:", nombres)
        
        btn_transferir = st.form_submit_button("🚀 Iniciar Vaciado")

        if btn_transferir:
            hoja = conectar_google_sheets()
            
            if hoja:
                try:
                    # Fila del paciente seleccionado
                    f = df_pacientes[df_pacientes.iloc[:, 4] == paciente_sel].iloc[0]
                    
                    # Procesar Fecha (Col A / Índice 0)
                    dt = datetime.strptime(str(f.iloc[0]), "%d/%m/%Y")
                    dia_num = dt.day
                    
                    dic_meses = {
                        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
                    }
                    
                    # --- ACTUALIZACIÓN DE CELDAS SEGÚN NUEVO MAPEO ---
                    hoja.update_acell('B2', dic_meses[dt.month])   # Mes
                    hoja.update_acell('B3', str(f.iloc[1]))        # Especialidad (Col B)
                    hoja.update_acell('B4', str(f.iloc[2]))        # Cama (Col C)
                    hoja.update_acell('A5', str(f.iloc[4]))        # Paciente (Col E)
                    hoja.update_acell('B8', str(f.iloc[6]))        # Edad (Col G)
                    hoja.update_acell('B9', str(f.iloc[3]))        # Registro (Col D)
                    hoja.update_acell('B10', str(f.iloc[8]))       # Fecha Ingreso (Col I)

                    # Lógica de la "X": Fila 4, Columna D (4) a AH (34)
                    # Día 1 + 3 = Columna 4 (D)
                    columna_x = dia_num + 3
                    hoja.update_cell(4, columna_x, "X")
                    
                    st.success(f"✅ ¡Datos de {paciente_sel} transferidos a la plantilla!")
                    st.balloons()
                
                except Exception as err:
                    st.error(f"❌ Error en el proceso de mapeo: {err}")
else:
    st.warning("No se pudo cargar el censo de origen.")
