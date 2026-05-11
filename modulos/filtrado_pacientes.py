import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización Blindada")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo", type="primary", use_container_width=True):
    try:
        with st.spinner("Accediendo a Google Sheets..."):
            # 1. Leer Hoja 1 (Censo Actual)
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            
            if df_actual is None or df_actual.empty:
                st.warning("⚠️ La Hoja 1 está vacía.")
                st.stop()

            # 2. Intentar leer Hoja 2 (Historial)
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
                if df_previo is None or df_previo.empty:
                    df_previo = pd.DataFrame(columns=df_actual.columns)
                else:
                    # Alineamos columnas por si acaso
                    df_previo.columns = df_actual.columns
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        # 3. FILTRADO (Columna D = Índice 3)
        # Limpieza rápida para comparación
        ids_historial = df_previo.iloc[:, 3].astype(str).str.strip().unique().tolist()
        nuevos_pacientes = df_actual[~df_actual.iloc[:, 3].astype(str).str.strip().isin(ids_historial)]

        if nuevos_pacientes.empty:
            st.info("ℹ️ No hay pacientes nuevos. El historial está al día.")
            df_final = df_previo
        else:
            # Unimos: Historial + Nuevos
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se integraron {len(nuevos_pacientes)} pacientes nuevos.")

        # 4. ORDEN CRONOLÓGICO ESTRICTO (Columna A = Índice 0)
        # Convertimos a datetime para ordenar, pero mantenemos el formato original después
        df_final['temp_date'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
        
        # Ordenamos y eliminamos la columna temporal
        df_final = df_final.sort_values(by='temp_date', ascending=True).drop(columns=['temp_date'])

        # 5. LIMPIEZA FINAL Y FORMATEO
        # Reemplazamos valores nulos para que Sheets no reciba errores de formato
        df_final = df_final.fillna("")
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Actualizando Hoja 2 (Fila 1: Encabezados | Fila 2+: Datos)..."):
            # 'conn.update' con un DataFrame escribe los nombres de las columnas en la Fila 1 
            # y los datos inmediatamente debajo.
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa del Historial Sincronizado")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
