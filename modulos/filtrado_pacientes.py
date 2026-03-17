import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización de Censo")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo (Mantenimiento de Datos)", type="primary", use_container_width=True):
    try:
        with st.spinner("Leyendo información de Google Sheets..."):
            # 1. Leer Hoja 1 y Hoja 2 asegurando que la Fila 1 son encabezados
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
            except:
                # Si la Hoja 2 no existe, creamos una estructura igual a la Hoja 1
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ No se encontraron datos en la Hoja 1 (Fila 2 en adelante).")
            st.stop()

        # --- CONFIGURACIÓN DE LIMPIEZA ---
        # Convertimos todo a texto y quitamos espacios en blanco
        df_actual = df_actual.astype(str).apply(lambda x: x.str.strip())
        df_previo = df_previo.astype(str).apply(lambda x: x.str.strip())
        
        # Eliminamos filas que estén completamente vacías
        df_actual = df_actual[df_actual.iloc[:, 0] != "nan"]

        # 2. IDENTIFICACIÓN ÚNICA (Columna D - Índice 3)
        # Verificamos que existan al menos 4 columnas
        if len(df_actual.columns) < 4:
            st.error(f"La hoja debe tener al menos 4 columnas (A, B, C, D). Detectadas: {len(df_actual.columns)}")
            st.stop()

        # Identificador: Columna D (Registro/Expediente)
        col_id_name = df_actual.columns[3]
        
        # 3. FILTRADO: Mantener lo viejo, agregar lo nuevo
        # Obtenemos los registros que ya están en el historial (Hoja 2)
        registros_viejos = df_previo[col_id_name].unique().tolist()
        
        # Filtramos la Hoja 1 para quedarnos SOLO con los que NO están en la Hoja 2
        pacientes_nuevos = df_actual[~df_actual[col_id_name].isin(registros_viejos)]

        if pacientes_nuevos.empty:
            st.info("ℹ️ Todos los pacientes del censo actual ya existen en el historial. No se hicieron cambios.")
            df_final = df_previo
        else:
            # Unimos: Historial arriba (respeta sus filas y fechas) + Nuevos abajo
            df_final = pd.concat([df_previo, pacientes_nuevos], ignore_index=True)
            st.success(f"✨ Se integraron {len(pacientes_nuevos)} pacientes nuevos al historial.")

        # 4. ORDEN CRONOLÓGICO (Columna A - Fecha)
        col_fecha = df_final.columns[0]
        df_final['temp_order'] = pd.to_datetime(df_final[col_fecha], dayfirst=True, errors='coerce')
        df_final = df_final.sort_values(by='temp_order', ascending=True).drop(columns=['temp_order'])

        # 5. LIMPIEZA FINAL DE CARACTERES
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Actualizando Hoja 2..."):
            # Actualizamos manteniendo los mismos encabezados
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa del Historial Actualizado")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")
