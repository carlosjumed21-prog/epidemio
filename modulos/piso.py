import streamlit as st
import pandas as pd

st.title("🏥 Seguimiento de Piso")

# 1. CARGA DEL EXCEL
st.info("### 📂 Archivo de Seguimiento")
archivo_excel = st.file_uploader(
    "Subir archivo de Excel para seguimiento", 
    type=["xlsx", "xls"],
    key="excel_unico_piso"
)

if archivo_excel:
    try:
        df = pd.read_excel(archivo_excel)
        
        # Filtros de búsqueda (B=1, C=2)
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("Especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("Cama:", lista_camas)

        # Mapeo de Paciente (D, E, F, G, I, J)
        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        # --- PANEL DE VISTA PREVIA ---
        with st.container(border=True):
            st.markdown(f"### 👤 {paciente.iloc[4]}")
            c1, c2, c3 = st.columns(3)
            with c1: st.write(f"**Registro:** {paciente.iloc[3]}")
            with c2: st.write(f"**Sexo/Edad:** {paciente.iloc[5]} / {paciente.iloc[6]}")
            with c3: st.info(f"**Días Estancia:** {paciente.iloc[9]}")

        st.divider()

        # --- FORMULARIO DE CAPTURA ---
        st.subheader("📝 Captura de Seguimiento")

        # 1. Estatus del Paciente
        status = st.segmented_control(
            "Seleccione el estatus de atención:",
            options=["Ingreso", "Seguimiento", "Egreso"],
            format_func=lambda x: f"📥 {x}" if x=="Ingreso" else (f"🔄 {x}" if x=="Seguimiento" else f"📤 {x}"),
            key="status_paciente"
        )

        # 2. Datos Clínicos
        st.markdown("#### 🌡️ Datos Clínicos")
        
        # --- Signos Vitales (Minúsculas conforme a solicitud) ---
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            temperatura = st.number_input("temperatura (°C):", min_value=30.0, max_value=45.0, value=36.5, step=0.1)
            tension_arterial = st.text_input("tensión arterial (mmHg):", placeholder="120/80")
        with col_v2:
            frecuencia_cardiaca = st.number_input("frecuencia cardiaca (lpm):", min_value=0, step=1)
            glucosa = st.number_input("glucosa (mg/dL):", min_value=0, step=1)
        with col_v3:
            frecuencia_respiratoria = st.number_input("frecuencia respiratoria (rpm):", min_value=0, step=1)
            sat_o2 = st.number_input("sat o2 (%):", min_value=0, max_value=100, step=1)

        st.markdown("---")
        
        # --- Evacuaciones y Bristol con Lógica Médica ---
        col_clin1, col_clin2 = st.columns([1, 1.2]) 
        
        with col_clin1:
            num_evacuaciones = st.number_input("número de evacuaciones:", min_value=0, step=1)
            bristol = st.select_slider("escala de bristol:", options=list(range(1, 8)), value=4)
            
            # LÓGICA AUTOMÁTICA
            # Fiebre: > 38 se activa
            es_fiebre = temperatura > 38.0
            # Diarrea: >= 3 evacuaciones Y bristol >= 6 se activa
            es_diarrea = (num_evacuaciones >= 3 and bristol >= 6)
            
            st.write("**Estatus Clínico Automático:**")
            st.toggle("fiebre", value=es_fiebre, disabled=True, help="Se activa automáticamente si temperatura > 38°C")
            st.toggle("diarrea", value=es_diarrea, disabled=True, help="Se activa si evacuaciones ≥ 3 y Bristol ≥ 6")

        with col_clin2:
            # Inserción de imagen por LINK
            st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRM9aDaAOLH7m9GQmTitcpcGGoTOdO7-WbotA&s", 
                     caption="Referencia: Escala de Bristol", 
                     use_container_width=True)

        # 3. Dispositivos Invasivos
        st.markdown("#### 💉 Dispositivos Invasivos")
        col_disp1, col_disp2 = st.columns(2)
        with col_disp1:
            cat_venoso = st.checkbox("Catéter Venoso Central")
            cat_periferico = st.checkbox("Catéter Periférico")
        with col_disp2:
            sonda_urinaria = st.checkbox("Sonda Urinaria")
            ventilacion = st.checkbox("Ventilación Mecánica")

        # 4. Datos de Laboratorio
        st.markdown("#### 🧪 Datos de Laboratorio")
        col_lab1, col_lab2, col_lab3 = st.columns(3)
        with col_lab1:
            leucocitos = st.number_input("Leucocitos (cel/uL):", min_value=0)
        with col_lab2:
            neutrofilos = st.number_input("Neutrófilos (%):", min_value=0, max_value=100)
        with col_lab3:
            cultivos = st.radio("¿Cultivos?", ["No", "Sí"], horizontal=True)

        # --- BOTÓN DE GUARDADO ---
        st.divider()
        if st.button("💾 Guardar Seguimiento", type="primary", use_container_width=True):
            st.success(f"Información procesada para el paciente en la cama {cama_sel}.")
            # Los datos ya están listos en variables para ser exportados al Excel

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("⚠️ Sube el archivo Excel para habilitar la captura.")
