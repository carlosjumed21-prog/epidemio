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
        with st.spinner("Comparando censos..."):
            # 1. Leer Hoja 1 (Censo Diario) y Hoja 2 (Histórico)
            # Todo se lee como string para preservar formatos de RFC y fechas
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0).astype(str)
            df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0).astype(str)

        if df_actual.empty and df_previo.empty:
            st.warning("⚠️ No hay datos en ninguna de las hojas.")
        else:
            # Guardamos el orden original de las columnas de la Hoja 1
            columnas_originales = df_actual.columns.tolist()

            # 2. Lógica inversa de combinación:
            # Ponemos el HISTÓRICO (Hoja 2) primero y el ACTUAL (Hoja 1) después
            df_total = pd.concat([df_previo, df_actual], ignore_index=True)
            
            # Limpiamos valores "nan" que genera pandas al leer celdas vacías
            df_total = df_total.replace(["nan", "None", "NaT"], "")

            # 3. Lógica de Fecha Antigua y No Duplicados:
            # Convertimos temporalmente la Columna A a fecha para ordenar
            df_total['temp_date'] = pd.to_datetime(df_total.iloc[:, 0], dayfirst=True, errors='coerce')
            
            # ORDENAMOS: La fecha más ANTIGUA primero (Ascending=True)
            df_total = df_total.sort_values(by='temp_date', ascending=True)

            # ELIMINAR DUPLICADOS por RFC (Columna index 3):
            # Al estar ordenado por fecha antigua, 'keep=first' mantendrá el registro 
            # de la primera vez que el paciente apareció en el sistema.
            df_limpio = df_total.drop_duplicates(subset=[df_total.columns[3]], keep='first')

            # 4. Limpieza final de columnas
            # Quitamos la columna temporal y forzamos el orden A -> J
            df_limpio = df_limpio[columnas_originales]

            with st.spinner("Actualizando Hoja 2..."):
                # 5. Sobreescribir Hoja 2 con el listado depurado
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_limpio)

            st.success("✅ ¡Filtrado completado!")
            st.info("Se han mantenido las fechas de la primera aparición de cada paciente.")
            
            # Mostrar tabla de resultados
            st.dataframe(df_limpio, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")

st.divider()
st.caption("Esta herramienta asegura que si un paciente ya estaba registrado, su fecha de censo original no se modifique.")
