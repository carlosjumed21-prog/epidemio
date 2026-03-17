import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Protección de Historial")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Usaremos la Columna D (index 3) como el Registro/Expediente único
COL_ID_INDEX = 3 

if st.button("🚀 Sincronizar Censo (Sin tocar datos previos)", type="primary", use_container_width=True):
    try:
        with st.spinner("Leyendo bases de datos..."):
            # 1. Leer Hoja 1 (Actual) y Hoja 2 (Historial)
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0).astype(str)
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0).astype(str)
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía. No hay nada que procesar.")
        else:
            # 2. LIMPIEZA CRÍTICA: Quitar espacios en blanco que arruinan el filtro
            # Esto asegura que "123 " sea igual a "123"
            col_name = df_actual.columns[COL_ID_INDEX]
            df_actual[col_name] = df_actual[col_name].str.strip()
            df_previo[col_name] = df_previo[col_name].str.strip()

            # 3. FILTRADO: ¿Quiénes de la Hoja 1 NO están en la Hoja 2?
            # Solo vamos a "invitar" al historial a los pacientes nuevos
            registros_en_historial = df_previo[col_name].unique()
            pacientes_nuevos = df_actual[~df_actual[col_id_name].isin(registros_en_historial)]

            if pacientes_nuevos.empty:
                st.info("ℹ️ No hay pacientes nuevos en el censo de hoy. Todos ya están en el historial.")
                df_final = df_previo
            else:
                # 4. CONSOLIDACIÓN: Historial + Solo los nuevos
                df_final = pd.concat([df_previo, pacientes_nuevos], ignore_index=True)
                st.success(f"✨ Se detectaron e integraron {len(pacientes_nuevos)} pacientes nuevos.")

            # 5. ORDENAR Y LIMPIAR
            # Ordenar por fecha (Columna A) ascendente para mantener el orden cronológico
            df_final['temp_f'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
            df_final = df_final.sort_values(by='temp_f', ascending=True).drop(columns=['temp_f'])
            
            # Asegurar orden original de columnas
            df_final = df_final[df_actual.columns.tolist()]
            df_final = df_final.replace(["nan", "None", "<NA>"], "")

            with st.spinner("Guardando en Hoja 2..."):
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

            st.write("### 📋 Historial Actualizado (Hoja 2)")
            st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")

st.divider()
st.caption("Esta versión garantiza que la información que ya está en la Hoja 2 sea inamovible.")
