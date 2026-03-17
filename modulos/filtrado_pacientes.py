import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Filtrado con Respeto de Formato")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Ejecutar Filtrado Manteniendo Columnas", type="primary", use_container_width=True):
    try:
        with st.spinner("Leyendo datos actuales..."):
            # 1. Leer datos asegurando que todo sea tratado como texto inicialmente para no perder formatos
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0).fillna("")
            df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0).fillna("")

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía.")
        else:
            # --- PRESERVAR EL ORDEN ORIGINAL ---
            # Guardamos el orden exacto de las columnas de la Hoja 1
            columnas_originales = df_actual.columns.tolist()

            # 2. Combinar
            df_total = pd.concat([df_actual, df_previo], ignore_index=True)

            # 3. Lógica de Fecha (sin corromper el formato de visualización)
            # Creamos una columna temporal para ordenar, así no dañamos la original
            df_total['temp_fecha'] = pd.to_datetime(df_total.iloc[:, 0], dayfirst=True, errors='coerce')
            
            # Ordenar por la temporal y eliminar duplicados por RFC (Columna index 3)
            df_total = df_total.sort_values(by='temp_fecha', ascending=False)
            df_limpio = df_total.drop_duplicates(subset=[df_total.columns[3]], keep='first')

            # 4. LIMPIEZA FINAL
            # Eliminamos la columna temporal y forzamos el orden original de las columnas
            df_limpio = df_limpio[columnas_originales]

            # Convertir todo a string para que Google Sheets no cambie formatos de números o fechas
            df_limpio = df_limpio.astype(str).replace("NaT", "").replace("nan", "")

            with st.spinner("Sincronizando con Hoja 2..."):
                # 5. Actualizar
                # Nota: .update() intentará mantener el formato de la hoja si ya existe
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_limpio)

            st.success("✅ ¡Filtrado finalizado! Se respetó el orden de las columnas.")
            st.dataframe(df_limpio, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")
