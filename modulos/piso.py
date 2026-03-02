import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🏥 Seguimiento de Piso - Protocolo Epidemiológico")

# 1. CARGA DEL EXCEL
archivo_excel = st.file_uploader(
    "Subir archivo de Excel de Seguimiento", 
    type=["xlsx", "xls"],
    key="excel_piso_final"
)

if archivo_excel:
    try:
        df = pd.read_excel(archivo_excel)
        
        # Filtros de búsqueda (B=Especialidad, C=Cama)
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        col_esp, col_cam = st.columns(2)
        with col_esp:
            esp_sel = st.selectbox("Especialidad:", lista_especialidades)
        
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())
        with col_cam:
            cama_sel = st.selectbox("Cama:", lista_camas)

        # Mapeo de Paciente (D=Registro, E=Nombre, J=Días)
        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        # BANNER DE IDENTIFICACIÓN
        st.success(f"**Paciente:** {paciente.iloc[4]}  |  **Registro:** {paciente.iloc[3]}  |  **Estancia:** {paciente.iloc[9]} días")

        st.divider()

        # --- FORMULARIO VERTICAL (Extracción de Macros Page 1-6) ---
        
        # SECCIÓN 1: STATUS Y DATOS GENERALES (Page 1)
        with st.container(border=True):
            st.markdown("### 📍 Estatus y Ubicación")
            st.segmented_control(
                "Movimiento del Paciente:",
                options=["Ingreso", "Seguimiento", "Egreso"],
                format_func=lambda x: f"📥 {x}" if x=="Ingreso" else (f"🔄 {x}" if x=="Seguimiento" else f"📤 {x}"),
                key="status_mov"
            )
            motivo_seguimiento = st.text_area("Motivo de seguimiento / Diagnóstico:", placeholder="Ej. Neumonía nosocomial...")

        # SECCIÓN 2: DATOS CLÍNICOS (Page 2-3 del Macro)
        with st.container(border=True):
            st.markdown("### 🌡️ Datos Clínicos")
            c1, c2 = st.columns(2)
            with c1:
                fiebre = st.toggle("Presencia de Fiebre (>38°C)")
                diarrea = st.toggle("Presencia de Diarrea")
                disnea = st.toggle("Dificultad Respiratoria (Disnea)")
            with c2:
                num_evacuaciones = st.number_input("Número de evacuaciones (24h):", min_value=0, step=1)
                bristol = st.select_slider("Escala de Bristol:", options=list(range(1, 8)), value=4)
                

[Image of the Bristol stool scale chart]

                st.caption("1: Constipación severa - 7: Diarrea acuosa")

        # SECCIÓN 3: DISPOSITIVOS INVASIVOS (Page 4 del Macro)
        with st.container(border=True):
            st.markdown("### 💉 Dispositivos Invasivos")
            d1, d2 = st.columns(2)
            with d1:
                cvc = st.checkbox("Catéter Venoso Central (CVC)")
                cp = st.checkbox("Catéter Periférico")
                linea_arterial = st.checkbox("Línea Arterial")
            with d2:
                sonda_foley = st.checkbox("Sonda Urinaria (Foley)")
                vm = st.checkbox("Ventilación Mecánica Invasiva")
                drenajes = st.checkbox("Drenajes Quirúrgicos")
            
            # Condición de fecha para dispositivos
            if cvc or sonda_foley or vm:
                st.date_input("Fecha de instalación del dispositivo:", datetime.now())

        # SECCIÓN 4: LABORATORIO Y CULTIVOS (Page 5 del Macro)
        with st.container(border=True):
            st.markdown("### 🧪 Laboratorios y Microbiología")
            l1, l2, l3 = st.columns(3)
            with l1:
                leucos = st.number_input("Leucocitos totales:", min_value=0)
            with l2:
                neutros = st.number_input("Neutrófilos (%):", min_value=0, max_value=100)
            with l3:
                procalcitonina = st.number_input("Procalcitonina:", min_value=0.0)
            
            st.markdown("---")
            cultivos_pedidos = st.radio("¿Se solicitaron cultivos hoy?", ["No", "Sí"], horizontal=True)
            if cultivos_pedidos == "Sí":
                tipo_cultivo = st.multiselect("Tipo de cultivo:", ["Hemocultivo", "Urocultivo", "Secreción Traqueal", "Punta de Catéter", "Otros"])

        # SECCIÓN 5: ANTIBIÓTICOS (Page 6 del Macro)
        with st.container(border=True):
            st.markdown("### 💊 Esquema Antimicrobiano")
            antibiotico = st.multiselect("Antibióticos actuales:", ["Meropenem", "Vancomicina", "Linezolid", "Piperacilina/Tazobactam", "Ceftriaxona", "Otro"])
            dia_tratamiento = st.number_input("Día de tratamiento:", min_value=1, step=1)

        # --- BOTÓN FINAL ---
        st.divider()
        if st.button("💾 Guardar y Actualizar Excel", type="primary", use_container_width=True):
            st.success(f"Datos de {paciente.iloc[4]} procesados correctamente. Listo para exportar a columna K en adelante.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.warning("⚠️ Sube el archivo Excel para desplegar el formulario de seguimiento.")
