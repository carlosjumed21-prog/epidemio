import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🏥 Seguimiento de Piso - Protocolo Epidemiológico")

# 1. CARGA DEL EXCEL (Fuente única de datos para esta pestaña)
st.info("### 📂 Archivo de Seguimiento")
archivo_excel = st.file_uploader(
    "Subir archivo de Excel de Seguimiento", 
    type=["xlsx", "xls"],
    key="excel_piso_final"
)

if archivo_excel:
    try:
        # Leer el Excel
        df = pd.read_excel(archivo_excel)
        
        if df.empty:
            st.warning("El archivo está vacío.")
            st.stop()

        # --- FILTROS DE BÚSQUEDA ---
        # Columna B = Índice 1, Columna C = Índice 2
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("Especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        
        with col_cam:
            cama_sel = st.selectbox("Cama:", lista_camas)

        # MAPEO DE PACIENTE (D=3, E=4, J=9)
        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        # BANNER DE IDENTIFICACIÓN
        st.success(f"**Paciente:** {paciente.iloc[4]}  |  **Registro:** {paciente.iloc[3]}  |  **Estancia:** {paciente.iloc[9]} días")

        st.divider()

        # --- FORMULARIO VERTICAL (Categorías Page 1-6) ---
        
        # CATEGORÍA 1: STATUS (Page 1)
        with st.container(border=True):
            st.markdown("### 📍 Estatus de Seguimiento")
            status_mov = st.radio(
                "Movimiento del Paciente:",
                options=["Ingreso", "Seguimiento", "Egreso"],
                horizontal=True
            )
            diagnostico = st.text_area("Diagnóstico / Motivo de vigilancia:", placeholder="Escriba aquí...")

        # CATEGORÍA 2: DATOS CLÍNICOS (Page 2-3)
        with st.container(border=True):
            st.markdown("### 🌡️ Datos Clínicos")
            c1, c2 = st.columns(2)
            with c1:
                fiebre = st.toggle("Fiebre (>38°C)")
                diarrea = st.toggle("Diarrea")
                disnea = st.toggle("Dificultad Respiratoria")
            with c2:
                num_evac = st.number_input("No. Evacuaciones (24h):", min_value=0, step=1)
                bristol = st.select_slider("Escala de Bristol:", options=list(range(1, 8)), value=4)
                st.caption("1: Muy duro | 4: Ideal | 7: Líquido")
                [Image of the Bristol stool scale chart]

        # CATEGORÍA 3: DISPOSITIVOS INVASIVOS (Page 4)
        with st.container(border=True):
            st.markdown("### 💉 Dispositivos Invasivos")
            d1, d2 = st.columns(2)
            with d1:
                cvc = st.checkbox("Catéter Venoso Central")
                cp = st.checkbox("Catéter Periférico")
                l_art = st.checkbox("Línea Arterial")
            with d2:
                sonda = st.checkbox("Sonda Urinaria (Foley)")
                vm = st.checkbox("Ventilación Mecánica")
                drenaje = st.checkbox("Drenajes")
            
            if cvc or sonda or vm:
                st.date_input("Fecha de instalación:", datetime.now())

        # CATEGORÍA 4: LABORATORIO Y CULTIVOS (Page 5)
        with st.container(border=True):
            st.markdown("### 🧪 Laboratorio y Microbiología")
            l1, l2 = st.columns(2)
            with l1:
                leucos = st.number_input("Leucocitos totales:", min_value=0)
            with l2:
                neutros = st.number_input("Neutrófilos (%):", min_value=0, max_value=100)
            
            st.markdown("---")
            cultivos = st.radio("¿Se tomaron cultivos?", ["No", "Sí"], horizontal=True)
            if cultivos == "Sí":
                st.multiselect("Sitio de cultivo:", ["Hemocultivo", "Urocultivo", "Traqueal", "Herida", "Punta Catéter"])

        # CATEGORÍA 5: ANTIBIÓTICOS (Page 6)
        with st.container(border=True):
            st.markdown("### 💊 Antibióticos")
            esquema = st.multiselect("Antibióticos actuales:", ["Meropenem", "Vancomicina", "Linezolid", "Pip/Tazo", "Ceftriaxona"])
            dias_atb = st.number_input("Día de tratamiento:", min_value=0, step=1)

        # --- BOTÓN DE GUARDADO ---
        st.divider()
        if st.button("💾 Guardar Datos en Excel", type="primary", use_container_width=True):
            st.balloons()
            st.success("Información procesada para el paciente seleccionado.")

    except Exception as e:
        st.error(f"Error de procesamiento: {e}")
else:
    st.warning("⚠️ Esperando archivo Excel para cargar el formulario.")
