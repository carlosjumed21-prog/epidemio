import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización Blindada")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo", type="primary", use_container_width=True):
    try:
        with st.spinner("Accediendo a Google Sheets..."):
            # 1. Leer hojas. Usamos header=0 para asegurar que lea los títulos
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        # Verificación de seguridad: ¿Hay datos?
        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 parece estar vacía o no tiene encabezados.")
            st.stop()

        # 2. ASEGURAR NOMBRES DE COLUMNAS
        # Limpiamos los nombres de las columnas (quitar espacios y saltos de línea)
        df_actual.columns = [str(c).strip() for c in df_actual.columns]
        df_previo.columns = [str(c).strip() for c in df_previo.columns]

        # Buscamos la columna de identificación (Registro o RFC)
        # La buscamos por nombre para evitar el error de "out-of-bounds"
        posibles_nombres = ['RFC/ID', 'REGISTRO', 'RFC', 'EXPEDIENTE', 'RFC / Registro']
        col_id = next((c for c in df_actual.columns if c.upper() in posibles_nombres), None)

        # Si no la encuentra por nombre, usamos la cuarta columna (índice 3) con validación
        if col_id is None:
            if len(df_actual.columns) >= 4:
                col_id = df_actual.columns[3]
            else:
                st.error(f"La hoja solo tiene {len(df_actual.columns)} columnas. Se necesitan al menos 4.")
                st.write("Columnas detectadas:", list(df_actual.columns))
                st.stop()

        # 3. LIMPIEZA DE DATOS
        df_actual = df_actual.astype(str).apply(lambda x: x.str.strip())
        df_previo = df_previo.astype(str).apply(lambda x: x.str.strip())

        # 4. FILTRADO (Mantener lo viejo, añadir lo nuevo)
        ids_historial = df_previo[col_id].unique()
        # Solo tomamos filas de la Hoja 1 que NO estén en la Hoja 2
        nuevos = df_actual[~df_actual[col_id].isin(ids_historial)]

        if nuevos.empty:
            st.info("ℹ️ No hay pacientes nuevos. El historial está intacto.")
            df_final = df_previo
        else:
            # Unimos: Historial arriba, Nuevos abajo
            df_final = pd.concat([df_previo, nuevos], ignore_index=True)
            st.success(f"✨ Se agregaron {len(nuevos)} pacientes nuevos.")

        # 5. ORDENAR POR FECHA (Columna A)
        col_fecha = df_actual.columns[0]
        df_final['temp_order'] = pd.to_datetime(df_final[col_fecha], dayfirst=True, errors='coerce')
        df_final = df_final.sort_values(by='temp_order', ascending=True).drop(columns=['temp_order'])

        # Limpiar valores basura
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Guardando en Hoja 2..."):
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error crítico: {e}")
