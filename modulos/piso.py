import streamlit as st
import pandas as pd

st.title("🏥 Seguimiento de Piso")

# --- ESTILO CSS PARA INTERRUPTORES POSITIVOS EN VERDE ---
st.markdown("""
    <style>
    /* Cambia el color del toggle cuando está activado (clase nativa de Streamlit) */
    .st-at {
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
        
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("Especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("Cama:", lista_camas)

        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        with st.container(border=True):
            st.markdown(f"### 👤 {paciente.iloc[4]}")
            c1, c2, c3 = st.columns(3)
            with c1: st.write(f"**Registro:** {paciente.iloc[3]}")
            with c2: st.write(f"**Sexo/Edad:** {paciente.iloc[5]} / {paciente.iloc[6]}")
            with c3: st.info(f"**Días Estancia:** {paciente.iloc[9]}")

        st.divider()
        st.subheader("📝 Captura de Seguimiento")

        status = st.segmented_control(
            "Seleccione el estatus de atención:",
            options=["Ingreso", "Seguimiento", "Egreso"],
            format_func=lambda x: f"📥 {x}" if x=="Ingreso" else (f"🔄 {x}" if x=="Seguimiento" else f"📤 {x}"),
            key="status_paciente"
        )

        st.markdown("#### 🌡️ Datos Clínicos")
        col_v1, col_v2, col_v3 = st.columns(3)
        
        with col_v1:
            temperatura = st.number_input("temperatura (°C):", min_value=30.0, max_value=45.0, value=36.5, step=0.1)
            
            # --- LÓGICA DE TENSIÓN ARTERIAL AUTOMÁTICA ---
            ta_raw = st.text_input("tensión arterial (mmHg):", placeholder="Ej: 12080")
            ta_final = ta_raw
            
            # Si el usuario escribe solo números (ej. 12080), insertamos la diagonal
            if ta_raw.isdigit():
                if len(ta_raw) == 5: # Caso 120/80
                    ta_final = f"{ta_raw[:3]}/{ta_raw[3:]}"
                elif len(ta_raw) == 6: # Caso 120/100
                    ta_final = f"{ta_raw[:3]}/{ta_raw[3:]}"
            
            if ta_final != ta_raw:
                st.caption(f"Registrado como: **{ta_final}**")

        with col_v2:
            frecuencia_cardiaca = st.number_input("frecuencia cardiaca (lpm):", min_value=0, step=1)
            glucosa = st.number_input("glucosa (mg/dL):", min_value=0, step=1)
        with col_v3:
            frecuencia_respiratoria = st.number_input("frecuencia respiratoria (rpm):", min_value=0, step=1)
            sat_o2 = st.number_input("sat o2 (%):", min_value=0, max_value=100, step=1)

        st.markdown("---")
        
        col_evac, col_bristol = st.columns([1, 2])
        with col_evac:
            num_evacuaciones = st.number_input("número de evacuaciones:", min_value=0, step=1)
            
            # LÓGICA AUTOMÁTICA: FIEBRE >= 38
            es_fiebre = temperatura >= 38.0
            st.write("**Estatus Clínico:**")
            st.toggle("FIEBRE DETECTADA" if es_fiebre else "fiebre", value=es_fiebre, disabled=True)
            placeholder_diarrea = st.empty()

        with col_bristol:
            st.write("**Referencia y Selección: Escala de Bristol**")
            st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRM9aDaAOLH7m9GQmTitcpcGGoTOdO7-WbotA&s", use_container_width=True)
            bristol = st.select_slider("Seleccione el tipo de acuerdo a la imagen superior:", options=list(range(1, 8)), value=4)
        
        # LÓGICA AUTOMÁTICA: DIARREA
        es_diarrea = (num_evacuaciones >= 3 and bristol >= 6)
        placeholder_diarrea.toggle("DIARREA DETECTADA" if es_diarrea else "diarrea", value=es_diarrea, disabled=True)

        st.markdown("#### 💉 Dispositivos Invasivos")
        col_disp1, col_disp2 = st.columns(2)
        with col_disp1:
            cat_venoso = st.checkbox("Catéter Venoso Central")
            cat_periferico = st.checkbox("Catéter Periférico")
        with col_disp2:
            sonda_urinaria = st.checkbox("Sonda Urinaria")
            ventilacion = st.checkbox("Ventilación Mecánica")

        st.markdown("#### 🧪 Datos de Laboratorio")
        col_lab1, col_lab2, col_lab3 = st.columns(3)
        with col_lab1:
            leucocitos = st.number_input("Leucocitos (cel/uL):", min_value=0)
        with col_lab2:
            neutrofilos = st.number_input("Neutrófilos (%):", min_value=0, max_value=100)
        with col_lab3:
            cultivos = st.radio("¿Cultivos?", ["No", "Sí"], horizontal=True)

        st.divider()
        if st.button("💾 Guardar Seguimiento", type="primary", use_container_width=True):
            st.success(f"Captura completa para la cama {cama_sel}. TA: {ta_final}")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("⚠️ Sube el archivo Excel para habilitar la captura.")
