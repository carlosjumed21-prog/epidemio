import streamlit as st
import pandas as pd

st.title("🏥 Seguimiento de Piso")

# Verificamos si hay archivo en el estado de la sesión
if 'archivo_compartido' in st.session_state and st.session_state['archivo_compartido'] is not None:
    try:
        # 1. Lectura del archivo (Normalmente los censos HTML tienen la tabla en el índice 0)
        # Forzamos que todo se lea como texto para evitar errores con números de registro
        tablas = pd.read_html(st.session_state['archivo_compartido'], keep_default_na=False)
        df = tablas[0]

        # 2. Selección de Especialidad (Columna B -> Índice 1)
        # Usamos .iloc para referenciar por posición de columna
        lista_especialidades = sorted(df.iloc[:, 1].unique())
        
        col1, col2 = st.columns(2)
        
        with col1:
            esp_sel = st.selectbox("Seleccione Especialidad (Columna B):", lista_especialidades)

        # Filtrar por especialidad para obtener las camas disponibles
        df_filtrado_esp = df[df.iloc[:, 1] == esp_sel]

        # 3. Selección de Cama (Columna C -> Índice 2)
        lista_camas = sorted(df_filtrado_esp.iloc[:, 2].unique())
        
        with col2:
            cama_sel = st.selectbox("Seleccione Cama (Columna C):", lista_camas)

        # 4. Obtener datos del paciente seleccionado
        # Buscamos la fila donde la cama coincida
        datos_paciente = df_filtrado_esp[df_filtrado_esp.iloc[:, 2] == cama_sel].iloc[0]

        # 5. Visualización del Previo (Mapeo solicitado)
        st.markdown("---")
        st.subheader(f"🔍 Datos del Paciente Seleccionado - Cama {cama_sel}")
        
        # Layout de 3 columnas para el previo
        p_col1, p_col2, p_col3 = st.columns(3)
        
        with p_col1:
            st.write(f"**Nombre:** {datos_paciente.iloc[4]}")    # Columna E
            st.write(f"**Registro:** {datos_paciente.iloc[3]}")  # Columna D
            
        with p_col2:
            st.write(f"**Sexo:** {datos_paciente.iloc[5]}")      # Columna F
            st.write(f"**Edad:** {datos_paciente.iloc[6]}")      # Columna G
            
        with p_col3:
            st.write(f"**Fecha Ingreso:** {datos_paciente.iloc[8]}") # Columna I
            st.write(f"**Días Estancia:** {datos_paciente.iloc[9]}") # Columna J

        st.markdown("---")

        # 6. SECCIÓN DE CAPTURA (Aquí irán tus variables)
        st.info("### 📝 Captura de Seguimiento")
        st.write("Ingresa los datos correspondientes a este paciente a continuación:")
        
        # --- AQUÍ AGREGAREMOS LAS VARIABLES QUE ME PASES ---
        st.warning("Pendiente: Definición de variables de captura.")

    except Exception as e:
        st.error(f"Error al procesar el censo: {e}")
else:
    st.warning("⚠️ No se ha detectado ningún censo. Por favor, sube el archivo HTML en la barra lateral.")
