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

        # 1. Estatus del Paciente (Botones segmentados)
        st.write("**Estatus de Atención:**")
        status = st.segmented_control(
            "Seleccione el estado actual:",
            options=["Ingreso", "Seguimiento", "Egreso"],
            format_func=lambda x: f"📥 {x}" if x=="Ingreso" else (f"🔄 {x}" if x=="Seguimiento" else f"📤 {x}"),
            key="status_paciente"
        )

        # 2. Datos Clínicos
        st.markdown("#### 🌡️ Datos Clínicos")
        col_clin1, col_clin2 = st.columns(2)
        with col_clin1:
            fiebre = st.toggle("¿Presenta Fiebre?", key="fiebre")
            diarrea = st.toggle("¿Presenta Diarrea?", key="diarrea")
        
        with col_clin2:
            num_evacuaciones = st.number_input("Número de evacuaciones:", min_value=0, step=1)
            bristol = st.select_slider("Escala de Bristol:", options=list(range(1, 8)))

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
            # Aquí iría la lógica para añadir estas variables como columnas al final de la fila del paciente
            st.success(f"Seguimiento guardado para la cama {cama_sel} con estatus {status}")
            
            # Tip: Podrías crear un diccionario con estos datos para exportarlos
            datos_capturados = {
                "Status": status,
                "Fiebre": fiebre,
                "Diarrea": diarrea,
                "Evacuaciones": num_evacuaciones,
                "Bristol": bristol,
                "CVC": cat_venoso,
                "CP": cat_periferico,
                "Sonda": sonda_urinaria,
                "VMI": ventilacion,
                "Leucos": leucocitos,
                "Neutros": neutrofilos,
                "Cultivos": cultivos
            }
            # st.write(datos_capturados) # Debug para ver los datos

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("⚠️ Sube el archivo Excel para habilitar la captura.")
