import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización Blindada")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo", type="primary", use_container_width=True):
    try:
        with st.spinner("Accediendo a Google Sheets..."):
            # 1. Leer hojas y limpiar nombres de columnas inmediatamente
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            df_actual.columns = [str(c).strip().upper() for c in df_actual.columns]
            
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
                df_previo.columns = [str(c).strip().upper() for c in df_previo.columns]
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía.")
            st.stop()

        # 2. IDENTIFICAR COLUMNA DE REGISTRO (Diferenciador)
        # Buscamos por palabras clave
        keywords = ['REGISTRO', 'RFC', 'ID', 'EXPEDIENTE', 'RFC / REGISTRO', 'RFC/ID']
        col_id = next((c for c in df_actual.columns if any(k in c for k in keywords)), None)

        # Si no lo encuentra por nombre, forzamos la columna 4 (Indice 3)
        if not col_id:
            col_id = df_actual.columns[3]

        # 3. LIMPIEZA DE DATOS (Todo a texto y sin espacios)
        df_actual = df_actual.astype(str).apply(lambda x: x.str.strip())
        df_previo = df_previo.astype(str).apply(lambda x: x.str.strip())

        # 4. FILTRADO (Lógica: Si está en el previo, no se toca)
        # Obtenemos los IDs que ya existen en la Hoja 2
        ids_viejos = df_previo[col_id].unique().tolist()
        
        # Filtramos la Hoja 1: Solo los que NO están en ids_viejos
        nuevos_pacientes = df_actual[~df_actual[col_id].isin(ids_viejos)]

        if nuevos_pacientes.empty:
            st.info("ℹ️ No hay pacientes nuevos. El historial se mantiene igual.")
            df_final = df_previo
        else:
            # Unimos: Historial arriba (mantiene su fecha) + Nuevos abajo
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se agregaron {len(nuevos_pacientes)} pacientes nuevos.")

        # 5. ORDENAR CRONOLÓGICAMENTE (Columna A - Fecha)
        # Usamos la primera columna sin importar cómo se llame
        col_fecha = df_final.columns[0]
        df_final['TEMP_ORDER'] = pd.to_datetime(df_final[col_fecha], dayfirst=True, errors='coerce')
        df_final = df_final.sort_values(by='TEMP_ORDER', ascending=True).drop(columns=['TEMP_ORDER'])

        # Limpiar etiquetas de error de pandas
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Guardando cambios en Hoja 2..."):
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error crítico: {e}")
        st.info("Asegúrate de que la Hoja 1 tenga encabezados en la primera fila.")
