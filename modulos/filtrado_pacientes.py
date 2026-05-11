import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import unicodedata

st.title("🔍 Máquina Virtual: Sincronización Blindada")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para limpiar acentos y que "Á" vaya con "A"
def limpiar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    texto = texto.upper().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

if st.button("🚀 Sincronizar Censo", type="primary", use_container_width=True):
    try:
        with st.spinner("Accediendo a Google Sheets..."):
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            
            if df_actual is None or df_actual.empty:
                st.warning("⚠️ La Hoja 1 está vacía.")
                st.stop()

            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
                if df_previo is None or (df_previo.empty and len(df_previo.columns) == 0):
                    df_previo = pd.DataFrame(columns=df_actual.columns)
                encabezados_hoja2 = df_previo.columns.tolist()
            except:
                encabezados_hoja2 = df_actual.columns.tolist()
                df_previo = pd.DataFrame(columns=encabezados_hoja2)

        # 1. Identificar columna de Especialidad automáticamente
        # Buscamos nombres comunes: "ESPECIALIDAD", "SERVICIO", "PISO"
        posibles_nombres = ['ESPECIALIDAD', 'SERVICIO', 'DEPARTAMENTO']
        idx_especialidad = 4 # Valor por defecto (Columna E)
        
        for i, col in enumerate(encabezados_hoja2):
            if any(nombre in col.upper() for nombre in posibles_nombres):
                idx_especialidad = i
                break

        # 2. Filtrado de nuevos (Columna D = Índice 3)
        ids_historial = df_previo.iloc[:, 3].astype(str).str.strip().unique().tolist()
        nuevos_pacientes = df_actual[~df_actual.iloc[:, 3].astype(str).str.strip().isin(ids_historial)].copy()

        if nuevos_pacientes.empty:
            st.info("ℹ️ No hay pacientes nuevos.")
            df_final = df_previo
        else:
            nuevos_pacientes.columns = encabezados_hoja2
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se integraron {len(nuevos_pacientes)} pacientes nuevos.")

        # 3. ORDENAMIENTO AVANZADO
        # Creamos columnas temporales invisibles para ordenar correctamente
        df_final['temp_fecha'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
        
        # Esta columna limpia acentos y espacios para que el orden sea real (A-Z)
        df_final['temp_esp_clean'] = df_final.iloc[:, idx_especialidad].apply(limpiar_texto)

        # Ordenar: 1° Fecha, 2° Especialidad
        df_final = df_final.sort_values(
            by=['temp_fecha', 'temp_esp_clean'], 
            ascending=[True, True]
        )

        # Borrar auxiliares
        df_final = df_final.drop(columns=['temp_fecha', 'temp_esp_clean'])

        # 4. Limpieza de valores nulos
        df_final = df_final.fillna("").replace(["nan", "None", "<NA>"], "")
        df_final.columns = encabezados_hoja2

        with st.spinner("Actualizando Hoja 2 con orden alfabético..."):
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")
