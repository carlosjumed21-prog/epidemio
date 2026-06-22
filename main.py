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

# Selector de archivos para el Censo HTML
archivo_subido = st.sidebar.file_uploader(
    "Subir Censo HTML", 
    type=["html", "htm"],
    help="Arrastra aquí el archivo generado por el sistema del hospital."
)

if archivo_subido:
    st.session_state['archivo_compartido'] = archivo_subido
    st.sidebar.success("✅ Censo cargado")
else:
    st.sidebar.info("👋 Por favor, sube un censo para comenzar.")

st.sidebar.divider()

# --- 3. NAVEGACIÓN Y ESTRUCTURA DE PÁGINAS ---
pg = st.navigation([
    st.Page(
        "modulos/censo_diario.py", 
        title="Censo Epidemiológico", 
        icon="📋", 
        default=True
    ),
    st.Page(
        "modulos/filtrado_pacientes.py", 
        title="Filtrado de Pacientes", 
        icon="🔍"
    ),
    st.Page(
        "modulos/hojadiaria.py", 
        title="Hoja Diaria Piso", 
        icon="📝" 
    ),
    st.Page(
        "modulos/insumos.py", 
        title="Censo de Insumos", 
        icon="📦"
    ),
    st.Page(
        "modulos/aislamientos.py", 
        title="Aislamientos", 
        icon="🦠"
    ),
    st.Page(
        "modulos/piso.py", 
        title="Seguimiento de Piso", 
        icon="🏥"
    ),
    st.Page(
        "modulos/vigilancia_piso.py", 
        title="Vigilancia Activa de Piso", 
        icon="🛡️" 
    ),
    st.Page(
        "modulos/estadisticas_iaas.py", 
        title="Estadísticas IAAS", 
        icon="📊"
    ),
    st.Page(
        "modulos/Formulario_VIH.py", 
        title="Formulario VIH", 
        icon="📝"
    ),
    st.Page(
        "modulos/analisis_datos.py", 
        title="Análisis Estadístico", 
        icon="📉"
    ),
    st.Page(
        "modulos/linea.py", 
        title="Línea Cronológica", 
        icon="⏳" 
    ),
])

# --- 4. EJECUCIÓN ---
pg.run()
