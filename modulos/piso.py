import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🏥 Seguimiento de Piso")

# 1. carga del excel
st.info("### 📂 archivo de seguimiento")
archivo_excel = st.file_uploader(
    "subir archivo de excel para seguimiento", 
    type=["xlsx", "xls"],
    key="excel_unico_piso"
)

if archivo_excel:
    try:
        df = pd.read_excel(archivo_excel)
        
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("cama:", lista_camas)

        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        with st.container(border=True):
            st.markdown(f"### 👤 {paciente.iloc[4]}")
            c1, c2, c3 = st.columns(3)
            with c1: st.write(f"**registro:** {paciente.iloc[3]}")
            with c2: st.write(f"**sexo/edad:** {paciente.iloc[5]} / {paciente.iloc[6]}")
            with c3: st.info(f"**días estancia:** {paciente.iloc[9]}")

        st.divider()

        # --- formulario de captura ---
        st.subheader("📝 captura de seguimiento")

        status = st.segmented_control(
            "seleccione el estatus de atención:",
            options=["Ingreso", "Seguimiento", "Egreso"],
            format_func=lambda x: f"📥 {x}" if x=="Ingreso" else (f"🔄 {x}" if x=="Seguimiento" else f"📤 {x}"),
            key="status_paciente"
        )

        # 2. datos clínicos
        st.markdown("#### 🌡️ datos clínicos")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            temperatura = st.number_input("temperatura (°C):", min_value=30.0, max_value=45.0, value=36.5, step=0.1)
            ta_raw = st.text_input("tensión arterial (mmHg):", placeholder="ej: 12080")
            ta_final = f"{ta_raw[:3]}/{ta_raw[3:]}" if ta_raw.isdigit() and len(ta_raw) >= 5 else ta_raw
            if ta_final != ta_raw: st.caption(f"registrado: **{ta_final}**")
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
            es_fiebre = temperatura >= 38.0
            st.write("**estatus clínico:**")
            st.toggle("fiebre detectada" if es_fiebre else "fiebre", value=es_fiebre, disabled=True)
            placeholder_diarrea = st.empty()

        with col_bristol:
            st.write("**referencia: escala de bristol**")
            st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRM9aDaAOLH7m9GQmTitcpcGGoTOdO7-WbotA&s", use_container_width=True)
            bristol = st.select_slider("seleccione el tipo acorde a la imagen superior:", options=list(range(1, 8)), value=4)
        
        es_diarrea = (num_evacuaciones >= 3 and bristol >= 6)
        placeholder_diarrea.toggle("diarrea detectada" if es_diarrea else "diarrea", value=es_diarrea, disabled=True)

        # 3. dispositivos invasivos
        st.markdown("#### 💉 dispositivos invasivos")
        tiene_dispositivos = st.checkbox("¿el paciente cuenta con dispositivos invasivos?")
        
        if tiene_dispositivos:
            def campos_fecha(key_prefix):
                f1, f2 = st.columns(2)
                with f1: st.date_input("fecha de instalación", value=datetime.now(), key=f"inst_{key_prefix}")
                with f2: st.date_input("fecha de retiro", value=None, key=f"ret_{key_prefix}")

            st.write("---")
            cp = st.checkbox("catéter periférico")
            if cp: campos_fecha("cp")
            cvc = st.checkbox("catéter venoso central")
            if cvc: campos_fecha("cvc")
            su = st.checkbox("sonda urinaria")
            if su: campos_fecha("su")
            sng = st.checkbox("sonda nasogástrica")
            if sng: campos_fecha("sng")
            vm = st.checkbox("ventilación mecánica")
            if vm: campos_fecha("vm")

        # 4. procedimientos quirúrgicos
        st.markdown("#### 🔪 procedimientos quirúrgicos")
        cirugia = st.checkbox("¿se realizó cirugía?")
        if cirugia:
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.date_input("fecha de cirugía", value=datetime.now(), key="f_cirugia")
                st.radio("elección:", ["electiva", "urgencia"], horizontal=True, key="elec_cirugia")
            with c_col2:
                st.text_area("tipo de procedimiento", placeholder="describa la cirugía...", key="tipo_cirugia")

        # 5. antibióticos
        st.markdown("#### 💊 antibióticos")
        atb_activo = st.checkbox("¿paciente con antibióticos?")
        if atb_activo:
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                st.text_input("nombre del antibiótico:", key="nombre_atb")
                st.date_input("fecha de inicio:", value=datetime.now(), key="inicio_atb")
            with a_col2:
                st.date_input("fecha de término:", value=None, key="fin_atb")

        # 6. datos de laboratorio
        st.markdown("#### 🧪 datos de laboratorio")
        
        # laboratorios de rutina
        rutina = st.checkbox("¿cuenta con laboratorios de rutina?")
        if rutina:
            l_col1, l_col2 = st.columns(2)
            with l_col1:
                leucocitos = st.number_input("leucocitos (cel/uL):", min_value=0, key="lab_leucos")
            with l_col2:
                neutrofilos = st.number_input("neutrófilos (%):", min_value=0, max_value=100, key="lab_neutros")
        
        # cultivos
        tiene_cultivos = st.checkbox("¿cuenta con cultivos?")
        if tiene_cultivos:
            cul_col1, cul_col2 = st.columns(2)
            with cul_col1:
                st.date_input("fecha de toma:", value=datetime.now(), key="f_cultivo")
            with cul_col2:
                st.text_input("tipo de cultivo:", placeholder="ej: urocultivo, hemocultivo...", key="tipo_cultivo")

        st.divider()
        if st.button("💾 guardar seguimiento", type="primary", use_container_width=True):
            st.success(f"captura completa para la cama {cama_sel}. ta: {ta_final}")

    except Exception as e:
        st.error(f"error: {e}")
else:
    st.warning("⚠️ sube el archivo excel para habilitar la captura.")
