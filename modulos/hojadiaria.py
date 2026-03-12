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
        # Limpieza de la llave privada
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # ID de la hoja de salida (Plantilla)
        SHEET_ID = "116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc"
        spreadsheet = client.open_by_key(SHEET_ID)
        return spreadsheet.get_worksheet(0) # Retorna la primera pestaña
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

# --- 2. LECTURA DEL CENSO (ORIGEN) ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30) # Reducimos el tiempo de caché para ver cambios rápido
def cargar_censo_publico():
    try:
        return pd.read_csv(URL_ORIGEN)
    except Exception as e:
        st.error(f"Error al leer el censo de origen: {e}")
        return None

df_pacientes = cargar_censo_publico()

# --- 3. INTERFAZ Y LÓGICA DE VACIADO ---
if df_pacientes is not None:
    st.metric("Total de Pacientes", len(df_pacientes))
    
    with st.expander("Ver tabla de origen"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    with st.form("registro_kardex"):
        st.subheader("✍️ Vaciado a Hoja Diaria")
        
        # Selección por nombre (Columna E / Índice 4)
        nombres = df_pacientes.iloc[:, 4].dropna().unique().tolist()
        paciente_sel = st.selectbox("Selecciona al Paciente:", nombres)
        
        btn_transferir = st.form_submit_button("🚀 Iniciar Vaciado Automático")

        if btn_transferir:
            hoja = conectar_google_sheets()
            
            if hoja:
                try:
                    # Fila del paciente seleccionado
                    f = df_pacientes[df_pacientes.iloc[:, 4] == paciente_sel].iloc[0]
                    
                    # Procesar Fecha (Col A / Índice 0) -> Formato dd/mm/aaaa
                    fecha_str = str(f.iloc[0])
                    dt = datetime.strptime(fecha_str, "%d/%m/%Y")
                    dia_num = dt.day
                    
                    meses_esp = {
                        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
                    }
                    
                    # --- APLICACIÓN DEL MAPEO SOLICITADO ---
                    # 1. Datos de texto en celdas específicas
                    hoja.update_acell('B2', meses_esp[dt.month])   # Mes
                    hoja.update_acell('B3', str(f.iloc[1]))        # ESPECIALIDAD (Col B)
                    hoja.update_acell('B4', str(f.iloc[2]))        # CAMA (Col C)
                    hoja.update_acell('A5', str(f.iloc[4]))        # Paciente (Col E)
                    hoja.update_acell('B8', str(f.iloc[6]))        # EDAD (Col G)
                    hoja.update_acell('B9', str(f.iloc[3]))        # REGISTRO (Col D)
                    hoja.update_acell('B10', str(f.iloc[8]))       # Fecha de ingreso (Col I)

                    # 2. Lógica de la "X": Fila 4, Columna D (4) a AH (34)
                    # Si el día es 1, la columna es D (numéricamente es 4). 
                    # Por tanto: columna = dia + 3
                    columna_x = dia_num + 3
                    hoja.update_cell(4, columna_x, "X") # FILA 4, COLUMNA DINÁMICA
                    
                    st.success(f"✅ ¡Datos de {paciente_sel} transferidos con éxito!")
                    st.balloons()
                
                except Exception as err:
                    st.error(f"❌ Error en el mapeo: {err}")
            else:
                st.error("No se pudo conectar a la hoja de salida.")
else:
    st.warning("⚠️ No hay datos disponibles para procesar.")
