import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURACIÓN DE APIS ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"
NOMBRE_SHEET_DESTINO = "NOMBRE_DE_TU_HOJA_AQUI" # Cambia esto por el nombre del archivo en Drive

def conectar_google_sheets():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", SCOPE)
        client = gspread.authorize(creds)
        return client.open(NOMBRE_SHEET_DESTINO).sheet1
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return None

# --- INTERFAZ ---
st.set_page_config(page_title="Seguimiento de Piso", layout="wide")

with st.sidebar:
    st.header("Navegación")
    opcion = st.radio("Acción:", ["🆕 Inicio de Vigilancia", "🔄 Seguimiento Activo"])

# --- LÓGICA DE INICIO DE VIGILANCIA (EXCEL LOCAL) ---
if opcion == "🆕 Inicio de Vigilancia":
    st.header("🆕 Registro Inicial")
    archivo = st.file_uploader("Subir Censo Excel", type=["xlsx"])
    
    if archivo:
        df = pd.read_excel(archivo)
        # ... [Aquí va todo tu bloque de código original de selección de cama/paciente] ...
        # Al final, el botón de guardado enviaría los datos como una fila nueva.
        if st.button("💾 Crear Nueva Plantilla"):
            hoja = conectar_google_sheets()
            if hoja:
                # Ejemplo de envío de datos (ajusta las columnas según tu necesidad)
                nueva_fila = [datetime.now().strftime("%Y-%m-%d"), "Ingreso", "Cama X", "Paciente Y"]
                hoja.append_row(nueva_fila)
                st.success("✅ Paciente registrado en el sistema.")

# --- LÓGICA DE SEGUIMIENTO (GOOGLE SHEETS) ---
elif opcion == "🔄 Seguimiento Activo":
    st.header("🔄 Seguimiento y Actualización")
    
    # 1. Leer del Sheet Base (URL Pública)
    try:
        df_base = pd.read_csv(SHEET_BASE_URL)
        
        col1, col2 = st.columns(2)
        with col1:
            esp_lista = sorted(df_base.iloc[:, 1].dropna().unique())
            esp_sel = st.selectbox("Especialidad:", esp_lista)
        
        df_filtrado = df_base[df_base.iloc[:, 1] == esp_sel]
        
        with col2:
            pacientes = df_filtrado.apply(lambda x: f"{x.iloc[3]} | {x.iloc[4]}", axis=1).tolist()
            seleccion = st.selectbox("Paciente:", pacientes)

        if seleccion:
            reg_id = seleccion.split(" | ")[0]
            paciente = df_base[df_base.iloc[:, 3].astype(str) == str(reg_id)].iloc[0]

            # --- FORMULARIO CLÍNICO (Tu bloque de datos original) ---
            with st.container(border=True):
                st.markdown(f"### 📋 {paciente.iloc[4]}")
                # [Tus inputs de Temperatura, TA, Bristol, etc.]
                temp = st.number_input("Temperatura:", 35.0, 42.0, 36.5)
                comentarios = st.text_area("Evolución:")

            if st.button("🔄 Actualizar Plantilla Existente", type="primary"):
                hoja = conectar_google_sheets()
                if hoja:
                    # Buscamos la fila del paciente por su Registro (ID)
                    try:
                        celda = hoja.find(str(reg_id))
                        # Actualizamos columnas específicas (ejemplo: columna 10 para temp)
                        hoja.update_cell(celda.row, 10, temp) 
                        hoja.update_cell(celda.row, 11, comentarios)
                        st.success("✅ Datos actualizados sin duplicar registro.")
                    except gspread.exceptions.CellNotFound:
                        # Si no existe en el de salida, lo agregamos como nuevo
                        hoja.append_row([str(reg_id), paciente.iloc[4], temp, comentarios])
                        st.info("ℹ️ Paciente no estaba en hoja de salida. Se ha creado el registro.")

    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
