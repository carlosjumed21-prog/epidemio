import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización Blindada")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo (Mantenimiento de Historial)", type="primary", use_container_width=True):
    try:
        with st.spinner("Accediendo a Google Sheets..."):
            # 1. Leer hojas y forzar que todo sea texto (String)
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0).astype(str)
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0).astype(str)
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía.")
        else:
            # --- LÓGICA POR POSICIÓN (BLINDADA) ---
            
            # Limpiamos espacios en blanco de los datos
            df_actual = df_actual.apply(lambda x: x.str.strip())
            df_previo = df_previo.apply(lambda x: x.str.strip())

            # Definimos que el ID está en la cuarta columna (Columna D = Índice 3)
            # Usamos .iloc para no depender del nombre del encabezado
            ids_en_historial = df_previo.iloc[:, 3].unique()
            
            # Filtramos: Solo filas de Hoja 1 cuyo ID NO esté en el historial
            # Esto garantiza que lo viejo NO se toque y NO se borre
            pacientes_nuevos = df_actual[~df_actual.iloc[:, 3].isin(ids_en_historial)]

            if pacientes_nuevos.empty:
                st.info("ℹ️ No hay pacientes nuevos. El historial está al día.")
                df_final = df_previo
            else:
                # Unimos el historial con los nuevos
                df_final = pd.concat([df_previo, pacientes_nuevos], ignore_index=True)
                st.success(f"✨ Se agregaron {len(pacientes_nuevos)} pacientes nuevos al historial.")

            # --- ORDEN CRONOLÓGICO (Columna A = Índice 0) ---
            # Creamos una serie de tiempo temporal para ordenar
            df_final['temp_order'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
            df_final = df_final.sort_values(by='temp_order', ascending=True).drop(columns=['temp_order'])

            # Limpiar textos de error de Pandas
            df_final = df_final.replace(["nan", "None", "<NA>"], "")

            with st.spinner("Guardando cambios..."):
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

            st.write("### 📋 Vista Previa: Historial Protegido (Hoja 2)")
            st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
        st.info("Asegúrate de que la columna de Registro/RFC sea la cuarta columna (Columna D).")

st.divider()
st.caption("Esta herramienta detecta pacientes nuevos por RFC y los añade al final, manteniendo el orden de fechas.")
