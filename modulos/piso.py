import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
# URL del Google Sheet base (fuente de la verdad para seguimiento)
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Seguimiento de Piso", layout="wide")

# --- MENÚ PRINCIPAL ---
opcion = st.sidebar.radio(
    "Seleccione Proceso:",
    ["🆕 Inicio de Vigilancia (Excel)", "🔄 Seguimiento (Sheet Base)"],
    help="Inicio: Carga un Excel nuevo. Seguimiento: Actualiza datos del Sheet de Google."
)

st.title("🏥 Seguimiento de Piso")

# ---------------------------------------------------------
# CASO 1: INICIO DE VIGILANCIA (Tu código original)
# ---------------------------------------------------------
if opcion == "🆕 Inicio de Vigilancia (Excel)":
    st.info("### 📂 Carga de Censo para Inicio")
    archivo_excel = st.file_uploader(
        "Subir archivo excel para registro inicial", 
        type=["xlsx", "xls"],
        key="excel_inicial"
    )

    if archivo_excel:
        df = pd.read_excel(archivo_excel)
        # ... (Tu lógica de filtrado de especialidad y cama)
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("Especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("Cama:", lista_camas)
            
        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]
        # Aquí se mostraría el formulario... (Formulario simplificado para el ejemplo)
        st.success(f"Registrando nuevo ingreso: {paciente.iloc[4]}")

# ---------------------------------------------------------
# CASO 2: SEGUIMIENTO (Lectura del Sheet Base)
# ---------------------------------------------------------
elif opcion == "🔄 Seguimiento (Sheet Base)":
    st.info("### 🔄 Sincronización con Base de Datos (Google Sheets)")
    
    # Botón para forzar la actualización del Sheet
    if st.button("🔄 Actualizar Datos del Servidor"):
        st.cache_data.clear() # Limpia caché para leer datos frescos
    
    try:
        # Cargamos el CSV desde la URL pública
        df_base = pd.read_csv(SHEET_BASE_URL)
        
        # Filtros para buscar pacientes que YA ESTÁN en el sistema
        col1, col2 = st.columns(2)
        with col1:
            esp_lista = sorted(df_base.iloc[:, 1].dropna().unique())
            esp_seg = st.selectbox("Filtrar por Especialidad:", esp_lista)
            
        df_filtrado_seg = df_base[df_base.iloc[:, 1] == esp_seg]
        
        with col2:
            # Mostramos Registro + Nombre para evitar confusiones
            nombres_pacientes = df_filtrado_seg.apply(lambda x: f"{x.iloc[3]} | {x.iloc[4]}", axis=1).tolist()
            seleccion = st.selectbox("Seleccione Paciente para Seguimiento:", nombres_pacientes)
            
        if seleccion:
            reg_id = seleccion.split(" | ")[0]
            # Extraemos la fila del paciente seleccionado usando su Registro (ID único)
            paciente = df_base[df_base.iloc[:, 3].astype(str) == str(reg_id)].iloc[0]
            
            # --- Aquí empieza tu formulario de captura (el que ya tienes) ---
            with st.container(border=True):
                st.markdown(f"### 👤 {paciente.iloc[4]}")
                # (Demás datos clínicos...)
                st.write(f"**Cama:** {paciente.iloc[2]} | **Días Estancia:** {paciente.iloc[9]}")
            
            st.divider()
            st.subheader("📝 Actualización de Plantilla")
            # Tus inputs: Temperatura, TA, Frecuencias, etc.
            
            if st.button("💾 Actualizar Seguimiento", type="primary"):
                # Aquí enviarías los datos al email epidemio@... via API
                st.success(f"Datos actualizados en la plantilla de {paciente.iloc[4]}")
                
    except Exception as e:
        st.error(f"No se pudo conectar con el Sheet base: {e}")
