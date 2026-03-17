import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Filtrado de Pacientes", layout="wide")

st.title("🔍 Máquina Virtual de Filtrado")
st.markdown("""
Esta herramienta compara el **Censo Actual (Hoja 1)** con el **Censo Antiguo (Hoja 2)** para actualizar la lista sin repetir pacientes, respetando siempre la fecha más reciente.
""")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🔄 Ejecutar Filtrado y Actualizar Hoja 2", type="primary"):
    try:
        # 1. Cargar datos de ambas hojas
        # Nota: Asegúrate que los nombres "Hoja 1" y "Hoja 2" coincidan exactamente en tu Sheet
        df_actual = conn.read(worksheet="Hoja 1", ttl=0)
        df_antiguo = conn.read(worksheet="Hoja 2", ttl=0)

        if df_actual.empty:
            st.warning("⚠️ La Hoja 1 está vacía. No hay nada que filtrar.")
        else:
            # 2. Combinar ambos censos
            # Concatenamos Hoja 1 y Hoja 2
            df_combinado = pd.concat([df_actual, df_antiguo], ignore_index=True)

            # 3. Limpieza y Lógica de Fecha (Columna A)
            # Convertimos la Columna A a fecha para poder ordenar correctamente
            # Usamos iloc[:, 0] para referirnos a la Columna A independientemente del nombre
            df_combinado.iloc[:, 0] = pd.to_datetime(df_combinado.iloc[:, 0], dayfirst=True, errors='coerce')

            # Ordenamos: la fecha más reciente arriba
            df_combinado = df_combinado.sort_values(by=df_combinado.columns[0], ascending=False)

            # 4. Eliminar Duplicados por RFC/ID (Columna D - index 3)
            # Mantenemos el primero (el más reciente por el ordenamiento previo)
            df_final = df_combinado.drop_duplicates(subset=[df_combinado.columns[3]], keep='first')

            # 5. Guardar resultados en Hoja 2
            conn.update(worksheet="Hoja 2", data=df_final)

            st.success(f"✅ ¡Filtrado completado! La Hoja 2 ahora tiene {len(df_final)} pacientes únicos.")
            
            # Mostrar métricas rápidas
            c1, c2 = st.columns(2)
            c1.metric("Pacientes Nuevos/Actualizados", len(df_actual))
            c2.metric("Total en Historial (Hoja 2)", len(df_final))

            st.write("### Vista previa del censo actualizado:")
            st.dataframe(df_final)

    except Exception as e:
        st.error(f"❌ Error al procesar el filtrado: {e}")

st.divider()
st.info("💡 **Consejo:** Una vez que la Hoja 2 esté actualizada, puedes ir a 'Hoja Diaria Piso' para generar tus plantillas de vigilancia.")
