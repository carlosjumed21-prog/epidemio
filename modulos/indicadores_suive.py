import streamlit as st
import pandas as pd
import numpy as np

st.title("📈 Indicadores SUIVE")

# 1. Simulación de los datos basados en tu imagen
# (Cuando te conectes al servidor, reemplazarás esto con los datos reales)
@st.cache_data
def cargar_datos_prueba():
    return pd.DataFrame({
        'Delegacion ISSSTE': ['CDMX Sur', 'CDMX Sur', 'Puebla', 'CDMX Sur'],
        'Año': [2026, 2026, 2026, 2026],
        'Semana': [30, 31, 30, 31],
        'Unidad médica': ['CMN 20 de Noviembre', 'CMN 20 de Noviembre', 'H.R. Puebla', 'CMN 20 de Noviembre'],
        'Datos indicadores': ['Casos Nuevos', 'Casos Nuevos', 'Seguimiento', 'Alta'],
        'Datos': [12, 15, 8, 5]
    })

df = cargar_datos_prueba()

# 2. Interfaz del Constructor (Los 4 Cuadrantes de Excel)
st.subheader("Campos de tabla dinámica")
st.markdown("Selecciona los campos para las áreas siguientes:")

# Cuadrantes Superiores
col_filtros, col_columnas = st.columns(2)

with col_filtros:
    st.markdown("#### 🔍 Filtros")
    # En Excel, el filtro aplica a toda la hoja antes de armar la tabla
    filtro_delegacion = st.multiselect("Delegacion ISSSTE", df['Delegacion ISSSTE'].unique())
    filtro_ano = st.multiselect("Año", df['Año'].unique())

with col_columnas:
    st.markdown("#### ⏸️ Columnas")
    # Dejamos 'Semana' por defecto como en tu foto
    columnas_sel = st.multiselect("Seleccionar Columnas", df.columns.tolist(), default=['Semana'])

# Cuadrantes Inferiores
col_filas, col_valores = st.columns(2)

with col_filas:
    st.markdown("#### 📋 Filas")
    # Dejamos 'Unidad médica' y 'Datos indicadores' por defecto
    filas_sel = st.multiselect("Seleccionar Filas", df.columns.tolist(), default=['Unidad médica', 'Datos indicadores'])

with col_valores:
    st.markdown("#### Σ Valores")
    # Seleccionamos qué medir y cómo medirlo
    valor_sel = st.selectbox("Campo de Valores", df.columns.tolist(), index=df.columns.tolist().index('Datos'))
    operacion = st.selectbox("Operación", ["Suma", "Recuento", "Promedio"])

st.divider()

# 3. Procesamiento en el Backend (Pandas)

# Aplicar los filtros globales primero
df_filtrado = df.copy()
if filtro_delegacion:
    df_filtrado = df_filtrado[df_filtrado['Delegacion ISSSTE'].isin(filtro_delegacion)]
if filtro_ano:
    df_filtrado = df_filtrado[df_filtrado['Año'].isin(filtro_ano)]

# Diccionario para traducir la operación seleccionada a Numpy
diccionario_operaciones = {
    "Suma": np.sum,
    "Recuento": len,
    "Promedio": np.mean
}

# 4. Generar y Mostrar la Tabla Dinámica
st.subheader("Informe Dinámico")

# Validar que el usuario haya seleccionado al menos una fila o columna para evitar errores
if filas_sel or columnas_sel:
    try:
        tabla_dinamica = pd.pivot_table(
            df_filtrado,
            index=filas_sel if filas_sel else None,
            columns=columnas_sel if columnas_sel else None,
            values=valor_sel,
            aggfunc=diccionario_operaciones[operacion],
            fill_value=0
        )
        st.dataframe(tabla_dinamica, use_container_width=True)
    except Exception as e:
        st.error(f"Configuración de tabla no válida. Error: {e}")
else:
    st.info("👈 Por favor, selecciona al menos un campo para 'Filas' o 'Columnas' para generar la tabla.")
