import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONFIGURACIÓN DE CONEXIÓN (GSPREAD) ---
def conectar_google_sheets():
    # Cargamos credenciales desde secrets.toml
    creds_dict = st.secrets["connections"]["gsheets"]
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    # Abrimos por el ID del sheet de salida
    return client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc").sheet1

# --- 2. LECTURA DE VISTA PREVIA (Censo Origen) ---
URL_VISTA_PREVIA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_censo():
    return pd.read_csv(URL_VISTA_PREVIA)

df_pacientes = cargar_censo()

if df_pacientes is not None:
    # Encabezado con totales
    st.metric("Pacientes en Censo", len(df_pacientes))
    st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    # --- 3. FORMULARIO DE SELECCIÓN Y VACIADO ---
    with st.form("vaciado_kardex"):
        st.subheader("✍️ Seleccionar Paciente para Vaciado")
        
        # Usamos la columna E (Paciente) que es el índice 4
        nombres = df_pacientes.iloc[:, 4].dropna().unique()
        paciente_sel = st.selectbox("Paciente a procesar:", nombres)
        
        submit = st.form_submit_button("🚀 Transferir a Plantilla")

        if submit:
            try:
                # Extraer datos de la fila del paciente
                datos = df_pacientes[df_pacientes.iloc[:, 4] == paciente_sel].iloc[0]
                
                # --- PROCESAMIENTO DE FECHA Y DÍA ---
                # Columna A (Índice 0) -> formato dd/mm/aaaa
                fecha_raw = str(datos.iloc[0])
                fecha_dt = datetime.strptime(fecha_raw, "%d/%m/%Y")
                dia = fecha_dt.day
                mes_num = fecha_dt.month
                
                meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
                         7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
                
                # --- CÁLCULO DE COLUMNA PARA LA "X" ---
                # Si el día 1 es columna D (4), entonces la columna es: dia + 3
                # gspread usa números: A=1, B=2, C=3, D=4...
                col_x = dia + 3 

                # --- OPERACIÓN EN GOOGLE SHEETS ---
                hoja = conectar_google_sheets()
                
                # Lista de actualizaciones (Celda, Valor)
                batch_updates = [
                    {'range': 'A4', 'values': [[str(datos.iloc[4])]]}, # Paciente (Col E)
                    {'range': 'B3', 'values': [[str(datos.iloc[2])]]}, # Cama (Col C)
                    {'range': 'B7', 'values': [[str(datos.iloc[6])]]}, # Edad (Col G)
                    {'range': 'B8', 'values': [[str(datos.iloc[3])]]}, # Registro (Col D)
                    {'range': 'B9', 'values': [[str(datos.iloc[8])]]}, # F. Ingreso (Col I)
                    {'range': 'B2', 'values': [[meses[mes_num]]]]}    # Mes
                ]
                
                # Ejecutar actualizaciones básicas
                for update in batch_updates:
                    hoja.update(range_name=update['range'], values=update['values'])
                
                # Colocar la "X" en la fila 3, columna calculada por el día
                hoja.update_cell(3, col_x, "X")
                
                st.success(f"✅ Se transfirieron los datos de {paciente_sel}. Día {dia} marcado con X.")
                st.balloons()

            except Exception as e:
                st.error(f"Error al guardar: {e}")
                st.info("Asegúrate de que el Service Account tenga permiso de EDITOR en el Sheet de destino.")

else:
    st.warning("No se pudo cargar el censo.")
