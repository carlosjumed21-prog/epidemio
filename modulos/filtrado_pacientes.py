import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Filtrado de Pacientes (Máquina Virtual)")

# 1. Definición del enlace directo a tu archivo
# Usamos el ID de la URL que proporcionaste
URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"

# 2. Establecer la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown("""
Esta herramienta realiza un proceso de **Upsert** (Update/Insert):
1. Lee los pacientes nuevos en la **Hoja 1**.
2. Los compara con el histórico de la **Hoja 2**.
3. Si el paciente ya existe (mismo RFC), actualiza los datos con la fecha más reciente.
4. Si es nuevo, lo agrega al final.
""")

if st.button("🚀 Iniciar Proceso de Filtrado", type="primary", use_container_width=True):
    try:
        with st.spinner("Conectando con Google Sheets..."):
            # Leer ambas hojas de forma explícita usando la URL
            # ttl=0 asegura que traiga los datos más recientes que acabas de pegar
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía. Por favor, coloca los datos del censo diario ahí.")
        else:
            # --- LÓGICA DE FILTRADO ---
            
            # Combinar ambos listados
            df_total = pd.concat([df_actual, df_previo], ignore_index=True)

            # Convertir Columna A (Fecha) a formato fecha para poder ordenar
            # iloc[:, 0] selecciona la primera columna (Fecha)
            df_total.iloc[:, 0] = pd.to_datetime(df_total.iloc[:, 0], dayfirst=True, errors='coerce')

            # Ordenar por fecha: la más actual queda arriba
            df_total = df_total.sort_values(by=df_total.columns[0], ascending=False)

            # ELIMINAR DUPLICADOS
            # Buscamos duplicados en la Columna D (index 3), que es el RFC/ID
            # 'keep=first' garantiza que nos quedamos con el registro con fecha más reciente
            df_limpio = df_total.drop_duplicates(subset=[df_total.columns[3]], keep='first')

            # --- ACTUALIZACIÓN ---
            with st.spinner("Actualizando Hoja 2 (Histórico Limpio)..."):
                # Escribimos el resultado final depurado en la Hoja 2
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_limpio)

            st.success("✅ Proceso completado exitosamente.")
            
            # Métricas de control
            c1, c2, c3 = st.columns(3)
            c1.metric("Procesados hoy", len(df_actual))
            c2.metric("Base previa", len(df_previo))
            c3.metric("Total Únicos final", len(df_limpio))

            st.write("### 📋 Vista previa de los datos filtrados")
            st.dataframe(df_limpio, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el filtrado: {e}")
        st.info("Asegúrate de que las hojas se llamen exactamente 'Hoja 1' y 'Hoja 2' en tu archivo de Sheets.")

st.divider()
st.caption("EpidemioManager v2.0 - Gestión de Datos Epidemiológicos")
