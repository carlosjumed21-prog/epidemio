import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.header("🏥 Hoja Diaria Piso")

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
def conectar_google_sheets():
    try:
        # Extraemos las credenciales desde los secrets
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        
        # Limpieza crucial de la llave privada para evitar errores de formato
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrimos el archivo por su ID y seleccionamos la primera pestaña
        # ID: 116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc
        spreadsheet = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        return spreadsheet.get_worksheet(0) # Retorna la primera pestaña
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        st.info("Asegúrate de haber compartido el Sheet con el correo de la cuenta de servicio como 'Editor'.")
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

# --- 3. INTERFAZ Y LÓGICA DE VACIADO ---
if df_pacientes is not None:
    # Encabezado con métricas
    st.metric("Total de Pacientes en Censo", len(df_pacientes))
    
    with st.expander("Ver tabla completa de pacientes"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    with st.form("registro_kardex"):
        st.subheader("✍️ Transferencia a Plantilla Estándar")
        
        # Selección por nombre (Columna E / Índice 4)
        nombres = df_pacientes.iloc[:, 4].dropna().unique().tolist()
        paciente_sel = st.selectbox("Selecciona al Paciente para vaciar datos:", nombres)
        
        btn_transferir = st.form_submit_button("🚀 Iniciar Vaciado Automático")

        if btn_transferir:
            hoja = conectar_google_sheets()
            
            if hoja:
                try:
                    # Extraer datos de la fila del paciente seleccionado
                    fila_p = df_pacientes[df_pacientes.iloc[:, 4] == paciente_sel].iloc[0]
                    
                    # Procesar Fecha (Columna A / Índice 0) -> Formato dd/mm/aaaa
                    fecha_str = str(fila_p.iloc[0])
                    dt_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                    dia_num = dt_obj.day
                    mes_num = dt_obj.month
                    
                    dic_meses = {
                        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
                    }
                    
                    # --- OPERACIONES DE ACTUALIZACIÓN EN EL SHEET ---
                    # Usamos update_acell para celdas fijas
                    hoja.update_acell('A4', str(fila_p.iloc[4])) # Paciente (E)
                    hoja.update_acell('B3', str(fila_p.iloc[2])) # Cama (C)
                    hoja.update_acell('B7', str(fila_p.iloc[6])) # Edad (G)
                    hoja.update_acell('B8', str(fila_p.iloc[3])) # Registro (D)
                    hoja.update_acell('B9', str(fila_p.iloc[8])) # F. Ingreso (I)
                    hoja.update_acell('B2', dic_meses[mes_num])  # Mes en texto

                    # Lógica de la "X": Fila 3, Columna calculada
                    # Día 1 -> Col D (4), por tanto: dia + 3
                    hoja.update_cell(3, (dia_num + 3), "X")
                    
                    st.success(f"✅ ¡Datos de {paciente_sel} transferidos con éxito!")
                    st.balloons()
                
                except Exception as err:
                    st.error(f"❌ Error durante el mapeo de datos: {err}")
            else:
                st.error("No se pudo establecer la conexión con la plantilla de salida.")
else:
    st.warning("⚠️ No se pudieron cargar datos del censo de origen. Revisa el link de publicación.")
