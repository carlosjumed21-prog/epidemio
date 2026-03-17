import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Máquina Virtual: Sincronización Blindada")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 Sincronizar Censo", type="primary", use_container_width=True):
    try:
        with st.spinner("Conectando con Google Sheets..."):
            # 1. Leer Hoja 1
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0)
            
            # 2. Leer Hoja 2 con manejo de error total
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0)
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ No hay datos en la Hoja 1 (Fila 2 en adelante).")
            st.stop()

        # --- PROTECCIÓN ANTI-ERRORES DE COLUMNA ---
        # Forzamos que los nombres de las columnas sean IGUALES en ambos DataFrames
        # Tomamos los nombres de la Hoja 1 como la verdad absoluta
        df_previo.columns = df_actual.columns 

        # 3. NORMALIZACIÓN
        df_actual = df_actual.astype(str).apply(lambda x: x.str.strip())
        df_previo = df_previo.astype(str).apply(lambda x: x.str.strip())

        # 4. IDENTIFICADOR POR POSICIÓN (Columna D = Índice 3)
        # Usamos .iloc para extraer los valores sin importar el nombre de la columna
        ids_historial = df_previo.iloc[:, 3].unique().tolist()
        
        # Filtramos: Solo filas de Hoja 1 cuyo valor en Columna D NO esté en el historial
        # Usamos .iloc[:, 3] para que no busque la palabra 'REGISTRO' y no falle
        nuevos_pacientes = df_actual[~df_actual.iloc[:, 3].isin(ids_historial)]

        if nuevos_pacientes.empty:
            st.info("ℹ️ Todos los pacientes ya están en la Hoja 2. No hay cambios que hacer.")
            df_final = df_previo
        else:
            # Unimos: Historial arriba + Nuevos abajo
            df_final = pd.concat([df_previo, nuevos_pacientes], ignore_index=True)
            st.success(f"✨ Se integraron {len(nuevos_pacientes)} pacientes nuevos.")

        # 5. ORDEN CRONOLÓGICO (Columna A = Índice 0)
        # Convertimos a fecha para ordenar, luego regresamos a string
        df_final['temp_order'] = pd.to_datetime(df_final.iloc[:, 0], dayfirst=True, errors='coerce')
        df_final = df_final.sort_values(by='temp_order', ascending=True).drop(columns=['temp_order'])

        # Limpieza de nulos de Pandas
        df_final = df_final.replace(["nan", "None", "<NA>", "nan.1"], "")

        with st.spinner("Actualizando Hoja 2..."):
            # Sobreescribir con los datos limpios
            conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_final)

        st.write("### 📋 Vista Previa: Historial Actualizado")
        st.dataframe(df_final, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error detectado: {e}")
        st.info("Sugerencia: Revisa que la Hoja 2 no tenga columnas extra o nombres distintos en la Fila 1.")
