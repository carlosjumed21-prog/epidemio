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
                st.warning("⚠️ La Hoja 1 está vacía. Pega los datos con encabezados en la Fila 1.")
                st.stop()

            # 2. Leer Hoja 2 (Historial) y PROTEGER SUS ENCABEZADOS
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
                
                # Si está totalmente vacía, le damos las columnas de la Hoja 1 por defecto
                if df_previo is None or (df_previo.empty and len(df_previo.columns) == 0):
                    encabezados_hoja2 = df_actual.columns.tolist()
                    df_previo = pd.DataFrame(columns=encabezados_hoja2)
                else:
                    # RESPALDAMOS EL ENCABEZADO ORIGINAL DE LA HOJA 2 (Fila 1)
                    encabezados_hoja2 = df_previo.columns.tolist()
            except:
                encabezados_hoja2 = df_actual.columns.tolist()
                df_previo = pd.DataFrame(columns=encabezados_hoja2)

        # 3. FILTRADO (Columna D = Índice 3)
        if not df_previo.empty:
            ids_historial = df_previo.iloc[:, 3].astype(str).str.strip().unique().tolist()
        else:
            ids_historial = []

        # Encontramos los pacientes de Hoja 1 que NO están en Hoja 2
        nuevos_pacientes = df_actual[~df_actual.iloc[:, 3].astype(str).str.strip().isin(ids_historial)].copy()

        if nuevos_pacientes.empty:
            st.info("ℹ️ No hay pacientes nuevos. El historial se mantiene intacto.")
            df_final = df_previo
        else:
            # CLAVE: Hacemos que los nuevos pacientes adopten el nombre de columnas de la Hoja 2
            # Esto evita que al unir se creen columnas raras o se mueva el encabezado
            nuevos_pacientes.columns = encabezados_hoja2
            
            # Unimos: Historial (Hoja 2) + Nuevos pacientes (Hoja 1)
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se integraron {len(nuevos_pacientes)} pacientes nuevos.")

        # 4. ORDEN CRONOLÓGICO ESTRICTO (Columna A = Índice 0)
        # Convertimos la columna A en fechas para ordenar (desde la Fila 2 hacia abajo)
        df_final['temp_date'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
        
        # Ordenamos usando la fecha y luego borramos esa columna temporal
        df_final = df_final.sort_values(by='temp_date', ascending=True).drop(columns=['temp_date'])

        # 5. LIMPIEZA FINAL DE NULOS
        df_final = df_final.fillna("")
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        # 6. RESTAURAR EL ENCABEZADO BLINDADO
        # Aseguramos de manera definitiva que la Fila 1 sea tu encabezado original
        df_final.columns = encabezados_hoja2

        with st.spinner("Guardando cambios y orden cronológico en Hoja 2..."):
            # Al mandar df_final, streamlit-gsheets pega los 'encabezados_hoja2' en la Fila 1
            # y todos los pacientes ya ordenados por fecha a partir de la Fila 2.
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa: Hoja 2 Actualizada")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
