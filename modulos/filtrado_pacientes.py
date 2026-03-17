import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Filtrado de Pacientes (Prioridad Fecha Antigua)")

# URL de tu archivo
URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"

# Configurar conexión
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Ejecutar Filtrado (Mantener Fecha Original)", type="primary", use_container_width=True):
    try:
        with st.spinner("Conectando con las hojas..."):
            # 1. Leer Hoja 1 (Censo Diario)
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0).astype(str)
            
            # 2. Leer Hoja 2 (Histórico) con manejo de error si está vacía
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0).astype(str)
            except:
                # Si la Hoja 2 no existe o da error, creamos un DF vacío con las mismas columnas que la 1
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía. Pega los datos ahí primero.")
        else:
            # --- LÓGICA DE FILTRADO ---
            columnas_originales = df_actual.columns.tolist()

            # Combinar: Histórico primero para priorizar sus datos
            df_total = pd.concat([df_previo, df_actual], ignore_index=True)
            
            # Limpiar basura de celdas vacías
            df_total = df_total.replace(["nan", "None", "NaT", "<NA>"], "")

            # Convertir Columna A a fecha para ordenar cronológicamente
            # Usamos errors='coerce' por si hay celdas mal escritas
            df_total['temp_date'] = pd.to_datetime(df_total.iloc[:, 0], dayfirst=True, errors='coerce')
            
            # ORDENAR: El censo más antiguo primero (Ascendente)
            df_total = df_total.sort_values(by='temp_date', ascending=True)

            # ELIMINAR DUPLICADOS por RFC (Columna index 3)
            # Al estar ordenado por fecha antigua, 'keep=first' mantiene al paciente original
            df_limpio = df_total.drop_duplicates(subset=[df_total.columns[3]], keep='first')

            # Reordenar columnas a su estado original y quitar la temporal
            df_limpio = df_limpio[columnas_originales]

            with st.spinner("Actualizando Hoja 2..."):
                # 3. Sobreescribir Hoja 2
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_limpio)

            st.success("✅ ¡Filtrado completado con éxito!")
            
            # Mostrar tabla comparativa
            st.write(f"Pacientes totales únicos: **{len(df_limpio)}**")
            st.dataframe(df_limpio, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
        st.info("Revisa que en tu Google Sheets las pestañas se llamen exactamente: 'Hoja 1' y 'Hoja 2'")

st.divider()
st.caption("Recuerda: Si un paciente se repite, el sistema dejará la fecha en la que apareció por primera vez.")
