import streamlit as st

# --- 1. CONFIGURACIÓN GLOBAL ---
st.set_page_config(
    page_title="EpidemioManager - CMN 20 de Noviembre", 
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("⚙️ Configuración")

archivo_subido = st.sidebar.file_uploader(
    "Subir Censo HTML", 
    type=["html", "htm"],
    help="Arrastra aquí el archivo generado por el sistema del hospital."
)

if archivo_subido:
    st.session_state['archivo_compartido'] = archivo_subido
    st.sidebar.success("✅ Censo cargado")
else:
    st.sidebar.info("👋 Por favor, sube un censo.")

st.sidebar.divider()

# --- 3. NAVEGACIÓN ---
# Aquí vinculamos el nombre visible con el nombre del archivo físico
pg = st.navigation([
    st.Page("modulos/censo_diario.py", title="Censo Epidemiológico", icon="📋"),
    st.Page("modulos/insumos.py", title="Censo de Insumos", icon="📦"),
    st.Page("modulos/aislamientos.py", title="Aislamientos", icon="🦠"),
    st.Page("modulos/hojadiaria.py", title="Censo Diario Piso", icon="🏥"), # <--- Cambiado a hojadiaria.py
])

# --- 4. EJECUCIÓN ---
pg.run()
