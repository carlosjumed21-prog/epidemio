import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE GOOGLE SHEETS ---
# Usamos las credenciales que ya tienes configuradas
def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Extraemos directamente del diccionario de secrets de Streamlit
    creds_dict = st.secrets["connections"]["gsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    # Reemplaza con el ID o Nombre exacto de tu Sheet de salida
    return client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc").sheet1

SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

# --- LÓGICA DE NAVEGACIÓN ---
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "menu"

def cambiar_pantalla(nombre):
    st.session_state.pantalla = nombre

# --- 1. MENÚ PRINCIPAL (BOTONES DE DIFERENCIACIÓN) ---
if st.session_state.pantalla == "menu":
    st.title("🏥 Sistema de Vigilancia Epidemiológica")
    st.subheader("¿Qué acción desea realizar hoy?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 🆕 Inicio de Vigilancia")
            st.write("Cargar un **nuevo Excel** para registrar pacientes que ingresan al censo por primera vez.")
            if st.button("Comenzar Inicio", use_container_width=True, type="primary"):
                cambiar_pantalla("inicio")
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 🔄 Seguimiento")
            st.write("Actualizar datos de pacientes que **ya están en el sistema** (usando el Google Sheet base).")
            if st.button("Ir a Seguimiento", use_container_width=True):
                cambiar_pantalla("seguimiento")
                st.rerun()

# --- 2. PANTALLA: INICIO DE VIGILANCIA ---
elif st.session_state.pantalla == "inicio":
    if st.button("⬅️ Volver al Menú"): cambiar_pantalla("menu"); st.rerun()
    
    st.header("🆕 Registro de Inicio de Vigilancia")
    archivo_excel = st.file_uploader("Subir archivo de excel", type=["xlsx", "xls"])
    
    if archivo_excel:
        df = pd.read_excel(archivo_excel)
        # Aquí va tu lógica original de selectbox para especialidad y cama
        st.info("Formulario de ingreso inicial cargado...")
        # Al guardar, usaríamos conectar_google().append_row(...)

# --- 3. PANTALLA: SEGUIMIENTO ---
elif st.session_state.pantalla == "seguimiento":
    if st.button("⬅️ Volver al Menú"): cambiar_pantalla("menu"); st.rerun()
    
    st.header("🔄 Seguimiento de Pacientes Activos")
    
    try:
        df_base = pd.read_csv(SHEET_BASE_URL)
        
        # Filtros
        esp_lista = sorted(df_base.iloc[:, 1].dropna().unique())
        esp_sel = st.selectbox("Seleccione Especialidad:", esp_lista)
        
        df_filtrado = df_base[df_base.iloc[:, 1] == esp_sel]
        pacientes = df_filtrado.apply(lambda x: f"{x.iloc[3]} | {x.iloc[4]}", axis=1).tolist()
        seleccion = st.selectbox("Seleccione Paciente:", pacientes)
        
        if seleccion:
            reg_id = seleccion.split(" | ")[0]
            paciente = df_base[df_base.iloc[:, 3].astype(str) == str(reg_id)].iloc[0]
            
            # Formulario clínico (Tu código de Temperatura, TA, etc.)
            with st.container(border=True):
                st.markdown(f"#### Editando: {paciente.iloc[4]}")
                nueva_temp = st.number_input("Temperatura actual:", value=36.5)
            
            if st.button("💾 Actualizar Seguimiento en la Nube", type="primary"):
                # CONEXIÓN Y ACTUALIZACIÓN SIN DUPLICADOS
                hoja = conectar_google()
                try:
                    celda = hoja.find(str(reg_id))
                    # Ejemplo: Actualizar columna A (fecha) y columna J (temperatura)
                    hoja.update_cell(celda.row, 1, datetime.now().strftime("%d/%m/%Y"))
                    hoja.update_cell(celda.row, 10, nueva_temp)
                    st.success(f"✅ Seguimiento actualizado para el registro {reg_id}")
                except:
                    # Si no lo encuentra, lo agrega como nuevo para no perder el dato
                    hoja.append_row([datetime.now().strftime("%d/%m/%Y"), esp_sel, paciente.iloc[2], reg_id, paciente.iloc[4]])
                    st.warning("Paciente no encontrado en la hoja de salida, se creó un registro nuevo.")

    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
