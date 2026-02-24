import streamlit as st
import pandas as pd
import numpy as np
import time

# Configuración de la página
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de publicación del CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=5) # Caché de solo 5 segundos para máxima precisión
def cargar_datos_reales():
    # Forzar actualización de Google Sheets con timestamp
    url_final = f"{SHEET_URL}&cachebust={time.time()}"
    
    # 1. Carga de datos (Columnas B a J)
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10]
    
    # 2. Normalización de encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # 3. Limpieza de valores vacíos
    df = df.apply(lambda x: x.astype(str).str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 4. Lógica de consolidación por FILA INDEPENDIENTE
    # En lugar de ffill general, solo unimos filas si el nombre está vacío 
    # y pertenecen al mismo bloque de ingreso
    df['REGISTRO_ID'] = (df[col_cama].notna()).cumsum()

    def fusionar_filas_dobles(group):
        res = group.iloc[0].copy()
        # Combinar aislamientos (ej: Contacto + Gotitas)
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        
        # Para el resto, tomar el primer valor no nulo
        for col in group.columns:
            if col not in [col_tipo, 'REGISTRO_ID']:
                val = group[col].dropna()
                res[col] = val.iloc[0] if not val.empty else np.nan
        return res

    df = df.groupby('REGISTRO_ID', as_index=False).apply(fusionar_filas_dobles)

    # 5. Filtro estricto: Pacientes sin Fecha de Término
    # Solo mostramos los registros donde la celda de término sea nula
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # Limpieza final
    df = df[df[col_cama].notna()]
    return df.sort_values(by=col_cama)

try:
    if st.button("🔄 Sincronizar Censo Ahora"):
        st.cache_data.clear()
        st.rerun()

    df_activos = cargar_datos_reales()

    if not df_activos.empty:
        # Buscador por cualquier campo
        query = st.text_input("🔍 Buscar paciente o microorganismo:")
        if query:
            mask = df_activos.apply(lambda r: r.astype(str).str.contains(query, case=False).any(), axis=1)
            df_activos = df_activos[mask]

        st.dataframe(df_activos, use_container_width=True, hide_index=True)
        st.success(f"📋 **{len(df_activos)}** Aislamientos Activos detectados.")
    else:
        st.warning("No hay aislamientos activos registrados.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
