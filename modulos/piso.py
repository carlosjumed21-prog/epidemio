import streamlit as st
import pandas as pd

st.title("🏥 Seguimiento de Piso")

# 1. CARGA DEL EXCEL DE SEGUIMIENTO (DENTRO DE LA PESTAÑA)
st.info("### 📂 Archivo de Seguimiento")
archivo_excel = st.file_uploader(
    "Subir archivo de Excel para seguimiento", 
    type=["xlsx", "xls"],
    key="excel_seguimiento_piso" # ID diferente al del main.py
)

if archivo_excel:
    try:
        df_seguimiento = pd.read_excel(archivo_excel)
        st.success("✅ Excel de seguimiento listo.")
        
        # 2. VINCULACIÓN CON EL CENSO DEL SIDEBAR
        if 'archivo_compartido' in st.session_state:
            tablas_censo = pd.read_html(st.session_state['archivo_compartido'])
            df_censo = tablas_censo[0]

            st.divider()
            st.subheader("🔍 Selección de Paciente")

            # Filtros en Cascada usando iloc (B=1, C=2)
            lista_especialidades = sorted(df_censo.iloc[:, 1].dropna().unique())
            col_esp, col_cam = st.columns(2)
            
            with col_esp:
                esp_sel = st.selectbox("Especialidad:", lista_especialidades)

            df_filtrado_esp = df_censo[df_censo.iloc[:, 1] == esp_sel]
            lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())

            with col_cam:
                cama_sel = st.selectbox("Cama:", lista_camas)

            # 3. PREVIO (D, E, F, G, I, J)
            paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

            with st.container(border=True):
                st.write(f"**Paciente:** {paciente.iloc[4]} | **Registro:** {paciente.iloc[3]}")
                st.write(f"**Sexo:** {paciente.iloc[5]} | **Edad:** {paciente.iloc[6]} | **Ingreso:** {paciente.iloc[8]} | **Días:** {paciente.iloc[9]}")

            st.divider()
            st.subheader("📝 Captura")
            st.warning("Variables pendientes de configuración...")

        else:
            st.warning("⚠️ Sube el censo HTML en el menú de la izquierda.")
            
    except Exception as e:
        st.error(f"Error: {e}")
