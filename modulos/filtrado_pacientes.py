import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización de Censo")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo (Proteger Datos Previos)", type="primary", use_container_width=True):
    try:
        with st.spinner("Leyendo información de Google Sheets..."):
            # 1. Leer Hoja 1 y Hoja 2
            # Pandas toma automáticamente la Fila 1 como encabezados
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ No se encontraron datos en la Hoja 1.")
            st.stop()

        # --- NORMALIZACIÓN DE DATOS ---
        # Convertimos todo a texto y quitamos espacios para evitar errores de comparación
        df_actual = df_actual.astype(str).apply(lambda x: x.str.strip())
        df_previo = df_previo.astype(str).apply(lambda x: x.str.strip())

        # 2. IDENTIFICACIÓN POR POSICIÓN (Columna D = Índice 3)
        # Usamos el nombre real que tenga la columna en la posición 3 para evitar el error 'REGISTRO'
        col_id_nombre = df_actual.columns[3] 
        
        # 3. LÓGICA DE FILTRADO (MÁSCARA)
        # Obtenemos los IDs que ya existen en la Hoja 2 para NO tocarlos
        registros_en_historial = df_previo[col_id_nombre].unique().tolist()
        
        # Filtramos Hoja 1: Solo filas cuyo ID NO esté en el historial
        # Esto garantiza que si el paciente ya existe, se mantiene la fila vieja de la Hoja 2
        nuevos_pacientes = df_actual[~df_actual[col_id_nombre].isin(registros_en_historial)]

        if nuevos_pacientes.empty:
            st.info("ℹ️ Todos los pacientes ya están registrados. El historial no requiere cambios.")
            df_final = df_previo
        else:
            # Unimos: Historial (Viejos) arriba + Nuevos abajo
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se agregaron {len(nuevos_pacientes)} pacientes nuevos.")

        # 4. ORDENAR POR FECHA (Columna A - Índice 0)
        col_fecha = df_final.columns[0]
        df_final['temp_order'] = pd.to_datetime(df_final[col_fecha], dayfirst=True, errors='coerce')
        df_final = df_final.sort_values(by='temp_order', ascending=True).drop(columns=['temp_order'])

        # 5. LIMPIEZA FINAL
        # Reemplazamos los valores nulos de Pandas por celdas vacías para el Sheet
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Actualizando Hoja 2..."):
            # Sobreescribimos la Hoja 2 con la lista consolidada
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa del Historial (Orden Ascendente)")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        # Si el error es específicamente por la columna, damos un mensaje más claro
        st.error(f"❌ Error en el proceso: {e}")
        st.info("Verifica que la Hoja 1 tenga al menos 4 columnas y que los encabezados estén en la fila 1.")
