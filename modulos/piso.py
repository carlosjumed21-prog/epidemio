import streamlit as st
import pandas as pd

st.title("🏥 Seguimiento de Piso")

# 1. CARGA DEL EXCEL (Única fuente de datos para esta pestaña)
st.info("### 📂 Archivo de Seguimiento")
archivo_excel = st.file_uploader(
    "Subir archivo de Excel para seguimiento", 
    type=["xlsx", "xls"],
    key="excel_unico_piso"
)

if archivo_excel:
    try:
        # Leer el Excel (usamos keep_default_na=False para evitar problemas con celdas vacías)
        df = pd.read_excel(archivo_excel)
        
        if df.empty:
            st.warning("El archivo Excel está vacío.")
            st.stop()

        st.divider()
        st.subheader("🔍 Selección de Paciente")

        # --- FILTROS EN CASCADA (Basados en el Excel subido) ---
        
        # Especialidad: Columna B (Índice 1)
        lista_especialidades = sorted(df.iloc[:, 1].dropna().unique())
        
        col_esp, col_cam = st.columns(2)
        
        with col_esp:
            esp_sel = st.selectbox("Especialidad (Columna B):", lista_especialidades)

        # Filtrar el DataFrame por la especialidad seleccionada
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]
        
        # Cama: Columna C (Índice 2)
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].dropna().unique())

        with col_cam:
            cama_sel = st.selectbox("Cama (Columna C):", lista_camas)

        # --- MOSTRAR DATOS DEL PACIENTE (Basados en el Excel subido) ---
        # Buscamos la fila que corresponde a la cama seleccionada
        paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        with st.container(border=True):
            st.markdown(f"### 👤 {paciente.iloc[4]}") # Nombre (Columna E)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**Registro:** {paciente.iloc[3]}") # Columna D
                st.write(f"**Sexo:** {paciente.iloc[5]}")      # Columna F
            with c2:
                st.write(f"**Edad:** {paciente.iloc[6]}")      # Columna G
                st.write(f"**Ingreso:** {paciente.iloc[8]}")   # Columna I
            with c3:
                st.info(f"**Estancia:** {paciente.iloc[9]} días") # Columna J

        st.divider()
        
        # --- SECCIÓN DE CAPTURA ---
        st.subheader("📝 Captura de Seguimiento")
        # Aquí es donde agregaremos las variables que me proporciones
        st.warning("Listo para configurar las variables de captura.")

    except Exception as e:
        st.error(f"Error al procesar el Excel: {e}")
        st.info("Asegúrate de que el archivo tenga datos en las columnas B, C, D, E, F, G, I y J.")
else:
    st.warning("⚠️ Por favor, sube el archivo de Excel para comenzar el seguimiento.")
