import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- ELIMINA TODO LO QUE SEA SIDEBAR O NAVIGATION AQUÍ ---
# El sidebar ya lo dibujó main.py automáticamente

st.header("🏥 Censo Diario Piso")
st.markdown("---")

# Link de lectura pública (Vista previa)
URL_VISTA_PREVIA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def cargar_vista_previa():
    try:
        return pd.read_csv(URL_VISTA_PREVIA)
    except Exception as e:
        st.error(f"Error al cargar la vista previa: {e}")
        return None

# Recuperar el archivo subido desde el estado de la sesión si lo necesitas
if 'archivo_compartido' in st.session_state:
    archivo = st.session_state['archivo_compartido']
    # Aquí puedes procesar el HTML si es necesario para esta pestaña
else:
    st.info("ℹ️ Puedes subir un censo en la barra lateral para procesar más datos.")

df_pacientes = cargar_vista_previa()

if df_pacientes is not None:
    st.subheader("📋 Vista Previa de Pacientes")
    st.dataframe(df_pacientes, use_container_width=True, hide_index=True)
    
    st.divider()
    
    with st.form("form_vaciado"):
        st.subheader("✍️ Registro de Seguimiento")
        paciente = st.selectbox("Seleccionar Paciente", df_pacientes.iloc[:, 1].unique())
        comentarios = st.text_area("Notas")
        
        if st.form_submit_button("Guardar en Plantilla"):
            st.success(f"Registrando datos para {paciente}...")
            # Aquí irá tu lógica de vaciado con el JSON
