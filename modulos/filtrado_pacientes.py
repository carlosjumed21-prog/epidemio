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
                
                if df_previo is None or (df_previo.empty and len(df_previo.columns) == 0):
                    encabezados_hoja2 = df_actual.columns.tolist()
                    df_previo = pd.DataFrame(columns=encabezados_hoja2)
                else:
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
            nuevos_pacientes.columns = encabezados_hoja2
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se integraron {len(nuevos_pacientes)} pacientes nuevos.")

        # =====================================================================
        # 4. ORDEN MÚLTIPLE: 1º Fecha (Cronológico) -> 2º Especialidad (Alfabético)
        # =====================================================================
        
        # ⚠️ IMPORTANTE: Cambia este número por el índice de tu columna de Especialidad.
        # Ejemplo: Si Especialidad es la columna E, el índice es 4 (A=0, B=1, C=2, D=3, E=4)
        COL_ESPECIALIDAD = 4 

        # A) Preparamos la Fecha para el orden (Columna A = Índice 0)
        df_final['temp_date'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
        
        # B) Preparamos la Especialidad para el orden exacto (Limpiar espacios y pasar a mayúsculas)
        df_final['temp_especialidad'] = df_final.iloc[:, COL_ESPECIALIDAD].astype(str).str.strip().str.upper()

        # C) Ejecutamos el ordenamiento múltiple (ambos ascendentes)
        df_final = df_final.sort_values(
            by=['temp_date', 'temp_especialidad'], 
            ascending=[True, True]
        )
        
        # D) Borramos las columnas temporales para no ensuciar el Excel
        df_final = df_final.drop(columns=['temp_date', 'temp_especialidad'])

        # =====================================================================

        # 5. LIMPIEZA FINAL DE NULOS
        df_final = df_final.fillna("")
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        # 6. RESTAURAR EL ENCABEZADO BLINDADO
        df_final.columns = encabezados_hoja2

        with st.spinner("Guardando cambios y aplicando ordenamiento múltiple..."):
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa: Hoja 2 Actualizada y Ordenada")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
