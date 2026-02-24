import streamlit as st
import pandas as pd
import numpy as np
import time
import random

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de publicación
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2) # Reducimos el tiempo de espera al mínimo (2 segundos)
def cargar_censo_actualizado():
    # Generamos un número aleatorio para obligar a Google a refrescar el archivo
    seed = random.randint(1, 100000)
    url_forzada = f"{SHEET_URL}&recheck={seed}&t={time.time()}"
    
    # 1. Carga de datos (Columnas B a J)
    df = pd.read_csv(url_forzada, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10]
    
    # 2. Limpiar encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # 3. Limpieza profunda de vacíos
    # Convertimos todo a string para uniformar y luego detectamos nulos
    df = df.apply(lambda x: x.astype(str).str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 4. Agrupación por CAMA para manejar filas dobles
    # Usamos la Cama como ancla para no perder pacientes nuevos
    df['GRUPO'] = (df[col_cama].notna()).cumsum()

    def consolidar(group):
        res = group.iloc[0].copy()
        # Unir aislamientos si hay más de uno
        aislamientos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(aislamientos) if len(aislamientos) > 0 else "SIN ESPECIFICAR"
        
        # Recuperar datos de otras columnas si están en la segunda fila
        for c in group.columns:
            if c not in [col_tipo, 'GRUPO']:
                val = group[c].dropna()
                res[c] = val.iloc[0] if not val.empty else np.nan
        return res

    df = df.groupby('GRUPO', as_index=False).apply(consolidar)

    # 5. FILTRO DE ACTIVOS: Si la Fecha de Término NO tiene dato, está ACTIVO
    if col_termino in df.columns:
        # Mantenemos solo los que tienen NaN en la columna de término
        df = df[df[col_termino].isna()]

    # Quitar filas que no tienen número de cama (basura del Excel)
    df = df[df[col_cama].notna()]
    
    return df.sort_values(by=col_cama)

# --- INTERFAZ ---
try:
    # Botón con limpieza manual de caché
    if st.button("🔄 Forzar Sincronización Inmediata"):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_censo_actualizado()

    if not df_final.empty:
        st.dataframe(df_final.drop(columns=['GRUPO'], errors='ignore'), use_container_width=True, hide_index=True)
        st.success(f"✅ **{len(df_final)}** Aislamientos Activos detectados.")
        st.caption(f"Última actualización intentada: {time.strftime('%H:%M:%S')}")
    else:
        st.warning("No se detectan pacientes activos sin fecha de término.")

except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
