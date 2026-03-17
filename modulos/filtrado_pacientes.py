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
            
            # Verificación de seguridad: ¿Hay datos en Hoja 1?
            if df_actual is None or df_actual.empty:
                st.warning("⚠️ La Hoja 1 está vacía. Pega los datos con encabezados en la Fila 1.")
                st.stop()

            # 2. Intentar leer Hoja 2 (Historial)
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
                
                # SI LA HOJA 2 EXISTE PERO NO TIENE COLUMNAS (Error 0 vs 10)
                if df_previo is None or len(df_previo.columns) == 0:
                    df_previo = pd.DataFrame(columns=df_actual.columns)
                else:
                    # Forzamos que los nombres de columnas sean iguales para evitar el Error de "REGISTRO"
                    df_previo.columns = df_actual.columns
            except:
                # Si la Hoja 2 ni siquiera existe o falla la lectura
                df_previo = pd.DataFrame(columns=df_actual.columns)

        # 3. NORMALIZACIÓN (Limpieza de espacios y formatos)
        df_actual = df_actual.astype(str).apply(lambda x: x.str.strip())
        df_previo = df_previo.astype(str).apply(lambda x: x.str.strip())

        # 4. FILTRADO POR POSICIÓN (Columna D = Índice 3)
        # Usamos .iloc para no depender de nombres de columnas
        ids_historial = df_previo.iloc[:, 3].unique().tolist()
        
        # Pacientes de Hoja 1 que NO están en Hoja 2
        nuevos_pacientes = df_actual[~df_actual.iloc[:, 3].isin(ids_historial)]

        if nuevos_pacientes.empty:
            st.info("ℹ️ No hay pacientes nuevos. El historial se mantiene intacto.")
            df_final = df_previo
        else:
            # Unimos: Historial arriba (respeta su fecha original) + Nuevos abajo
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se integraron {len(nuevos_pacientes)} pacientes nuevos.")

        # 5. ORDEN CRONOLÓGICO (Columna A = Índice 0)
        df_final['temp_order'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
        df_final = df_final.sort_values(by='temp_order', ascending=True).drop(columns=['temp_order'])

        # Limpieza de valores nulos de visualización
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Guardando cambios en Hoja 2..."):
            # Actualizamos Hoja 2
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa: Hoja 2 Actualizada")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
