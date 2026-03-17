import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Filtrado de Pacientes (Consolidación de Censo)")

URL_SABANA = "https://docs.google.com/spreadsheets/d/1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURACIÓN DE COLUMNAS ---
# Columna A = Fecha (Indice 0)
# Columna D = Registro/Expediente (Indice 3)
# Columna E = Nombre (Indice 4)

id_filtro = st.radio(
    "Selecciona el criterio para evitar duplicados:",
    ["RFC / Registro", "Nombre del Paciente"],
    horizontal=True
)

# Mapeo de columna según elección
col_index = 3 if id_filtro == "RFC / Registro" else 4

if st.button("🚀 Actualizar Historial (Sin Duplicados)", type="primary", use_container_width=True):
    try:
        with st.spinner("Procesando datos..."):
            # 1. Leer hojas (TTL=0 para datos frescos)
            df_actual = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 1", ttl=0).astype(str)
            
            try:
                df_previo = conn.read(spreadsheet=URL_SABANA, worksheet="Hoja 2", ttl=0).astype(str)
            except:
                df_previo = pd.DataFrame(columns=df_actual.columns)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía.")
        else:
            # 2. LÓGICA DE FILTRADO PURO
            # Ponemos el Censo PREVIO arriba y el ACTUAL abajo
            df_consolidado = pd.concat([df_previo, df_actual], ignore_index=True)
            
            # Limpieza de nulos para que no afecten el filtro
            df_consolidado = df_consolidado.replace(["nan", "None", "NaT", "<NA>"], "")

            # 3. EVITAR DUPLICADOS
            # Al usar 'keep=first', pandas mantiene la PRIMERA aparición que encuentra.
            # Como pusimos el previo arriba, mantendrá la fila antigua (con su fecha original).
            # El identificador es la columna seleccionada (Registro o Nombre)
            col_id_name = df_consolidado.columns[col_index]
            df_limpio = df_consolidado.drop_duplicates(subset=[col_id_name], keep='first')

            # 4. ORDENAR POR FECHA (Columna A)
            # Para que el censo final siempre esté en orden cronológico ascendente
            df_limpio['temp_fecha'] = pd.to_datetime(df_limpio.iloc[:, 0], dayfirst=True, errors='coerce')
            df_limpio = df_limpio.sort_values(by='temp_fecha', ascending=True)
            
            # Quitar columna temporal y asegurar que el orden de columnas es idéntico al original
            df_limpio = df_limpio[df_actual.columns.tolist()]

            with st.spinner("Guardando en Hoja 2..."):
                # 5. Sobreescribir Hoja 2
                conn.update(spreadsheet=URL_SABANA, worksheet="Hoja 2", data=df_limpio)

            st.success(f"✅ ¡Filtrado exitoso! Se mantienen los datos originales de {len(df_limpio)} pacientes.")
            st.dataframe(df_limpio, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")

st.divider()
st.info("💡 **Lógica aplicada:** Si el paciente ya existe en la Hoja 2, se ignora la nueva fila de la Hoja 1 para no duplicar ni cambiar la fecha original.")
