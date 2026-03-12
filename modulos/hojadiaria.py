import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
def conectar_google_sheets():
    try:
        # Extraemos las credenciales desde los secrets de Streamlit
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        # ID del sheet de salida (el que me proporcionaste)
        return client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc").sheet1
    except Exception as e:
        st.error(f"Error de conexión a Google Sheets: {e}")
        return None

# --- 2. LECTURA DE CENSOS ---
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
    # Encabezado con total de pacientes
    st.metric("Total de Pacientes en Censo", len(df_pacientes))
    st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    with st.form("registro_kardex"):
        st.subheader("✍️ Transferencia a Plantilla")
        
        # Selección por nombre (Columna E / Índice 4)
        nombres = df_pacientes.iloc[:, 4].dropna().unique().tolist()
        paciente_sel = st.selectbox("Selecciona al Paciente para vaciar:", nombres)
        
        btn_transferir = st.form_submit_button("🚀 Transferir a Plantilla")

        if btn_transferir:
            try:
                # Extraer datos de la fila del paciente seleccionado
                fila_p = df_pacientes[df_pacientes.iloc[:, 4] == paciente_sel].iloc[0]
                
                # Procesar Fecha (Columna A / Índice 0)
                fecha_str = str(fila_p.iloc[0])
                # Convertimos a objeto datetime para extraer día y mes
                dt_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                dia_num = dt_obj.day
                mes_num = dt_obj.month
                
                dic_meses = {
                    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
                }
                
                # Conectar a la hoja
                hoja = conectar_google_sheets()
                
                if hoja:
                    # Mapeo según tus instrucciones:
                    hoja.update_acell('A4', str(fila_p.iloc[4])) # Paciente (E)
                    hoja.update_acell('B3', str(fila_p.iloc[2])) # Cama (C)
                    hoja.update_acell('B7', str(fila_p.iloc[6])) # Edad (G)
                    hoja.update_acell('B8', str(fila_p.iloc[3])) # Registro (D)
                    hoja.update_acell('B9', str(fila_p.iloc[8])) # F. Ingreso (I)
                    hoja.update_acell('B2', dic_meses[mes_num])  # Mes en texto
                    
                    # Lógica de la "X": D3 es día 1 (columna 4)
                    # La columna de la X es día + 3
                    hoja.update_cell(3, (dia_num + 3), "X")
                    
                    st.success(f"✅ ¡Datos de {paciente_sel} transferidos con éxito!")
                    st.balloons()
            
            except Exception as err:
                st.error(f"Error durante el vaciado: {err}")
else:
    st.warning("No se pudieron cargar datos del censo de origen.")
