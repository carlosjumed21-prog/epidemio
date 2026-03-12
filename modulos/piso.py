import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN Y CONSTANTES ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Seguimiento de Piso", layout="wide")
st.title("🏥 Sistema de Vigilancia Epidemiológica")

# Usamos tabs para separar las funciones claramente
tab_inicial, tab_seguimiento = st.tabs(["🆕 Inicio de Vigilancia", "🔄 Seguimiento"])

# --- FUNCIÓN AUXILIAR PARA RENDERIZAR FORMULARIO ---
def formulario_captura(datos_paciente):
    """Renderiza el formulario clínico común para ambos procesos"""
    st.markdown(f"### 👤 {datos_paciente.iloc[4]}")
    c1, c2, c3 = st.columns(3)
    with c1: st.write(f"**registro:** {datos_paciente.iloc[3]}")
    with c2: st.write(f"**sexo/edad:** {datos_paciente.iloc[5]} / {datos_paciente.iloc[6]}")
    with c3: st.info(f"**días estancia:** {datos_paciente.iloc[9]}")

    st.divider()
    st.subheader("📝 captura de datos")
    
    # ... (Aquí va todo tu bloque de datos clínicos, dispositivos, etc.)
    # Por brevedad, mantengo la estructura de los inputs que ya tienes
    status = st.segmented_control(
        "estatus:", ["Ingreso", "Seguimiento", "Egreso"], key=f"status_{datos_paciente.iloc[3]}"
    )
    
    # Datos clínicos simplificados para el ejemplo
    temp = st.number_input("temperatura (°C):", 30.0, 45.0, 36.5, step=0.1, key=f"t_{datos_paciente.iloc[3]}")
    
    if st.button("💾 Guardar y Actualizar Plantilla", type="primary", use_container_width=True):
        # Aquí es donde conectarías con tu Service Account de Google para escribir
        st.success(f"Plantilla actualizada para Registro {datos_paciente.iloc[3]} en el Sheet de Epidemio")

# --- TAB 1: INICIO DE VIGILANCIA (ARCHIVO LOCAL) ---
with tab_inicial:
    st.info("### 📂 Carga de Censo Nuevo")
    archivo_excel = st.file_uploader(
        "Subir archivo excel para iniciar vigilancia", 
        type=["xlsx", "xls"],
        key="uploader_inicial"
    )

    if archivo_excel:
        df_inicial = pd.read_excel(archivo_excel)
        # Lógica de filtrado que ya tenías
        esp_list = sorted(df_inicial.iloc[:, 1].dropna().unique())
        esp_sel = st.selectbox("Especialidad:", esp_list, key="esp_init")
        
        df_filtrado = df_inicial[df_inicial.iloc[:, 1] == esp_sel]
        cama_list = sorted(df_filtrado.iloc[:, 2].dropna().unique())
        cama_sel = st.selectbox("Cama:", cama_list, key="cama_init")
        
        paciente = df_filtrado[df_filtrado.iloc[:, 2] == cama_sel].iloc[0]
        formulario_captura(paciente)

# --- TAB 2: SEGUIMIENTO (GOOGLE SHEETS) ---
with tab_seguimiento:
    st.info("### 🔄 Seguimiento de Pacientes Activos")
    
    if st.button("🔌 Sincronizar con Sheet Base"):
        try:
            # Leemos directamente de la URL de publicación del Google Sheet
            st.session_state.df_seguimiento = pd.read_csv(SHEET_URL)
            st.toast("Datos sincronizados correctamente", icon="✅")
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {e}")

    if 'df_seguimiento' in st.session_state:
        df_seg = st.session_state.df_seguimiento
        
        # Filtros para seguimiento
        col1, col2 = st.columns(2)
        with col1:
            esp_seg = st.selectbox("Filtrar Especialidad:", sorted(df_seg.iloc[:, 1].unique()))
        
        df_seg_filtrado = df_seg[df_seg.iloc[:, 1] == esp_seg]
        
        with col2:
            # Aquí evitamos duplicados en el selector mostrando ID + Nombre
            opciones_pacientes = df_seg_filtrado.apply(lambda x: f"{x.iloc[3]} - {x.iloc[4]}", axis=1).tolist()
            paciente_sel = st.selectbox("Seleccionar Paciente en Vigilancia:", opciones_pacientes)
        
        if paciente_sel:
            id_registro = paciente_sel.split(" - ")[0]
            # Buscamos por el ID único (Registro) para asegurar que no hay duplicados
            datos_paciente = df_seg[df_seg.iloc[:, 3].astype(str) == str(id_registro)].iloc[0]
            
            # Al llamar a la misma función, la "Plantilla" es consistente
            formulario_captura(datos_paciente)
    else:
        st.write("Haz clic en el botón superior para cargar los datos del servidor.")
