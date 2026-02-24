import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de publicación
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=5)
def cargar_aislamientos_total():
    # Forzar a Google a no usar caché vieja
    url_final = f"{SHEET_URL}&t={time.time()}"
    
    # 1. Cargamos TODO el archivo sin recortes previos para ver dónde termina
    # Usamos on_bad_lines para evitar errores si la última fila está incompleta
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8', on_bad_lines='skip')
    
    # 2. Recorte manual de columnas B a J (Índices 1 al 9)
    # Verificamos que el DF tenga suficientes columnas antes de recortar
    if df.shape[1] > 1:
        df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA DE DATOS ---
    # Convertimos todo a string y limpiamos espacios para que la última fila no falle
    df = df.astype(str).apply(lambda x: x.str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 3. Lógica para no perder al paciente de la última fila
    # Rellenamos Cama y Nombre hacia abajo SOLO si la fila es parte de una continuación
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    # Definimos la función de consolidación para filas dobles
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        for c in group.columns:
            if c not in [col_tipo, col_cama, col_nombre]:
                val = group[c].dropna()
                res[c] = val.iloc[0] if not val.empty else np.nan
        return res

    # Agrupamos por Cama y Nombre para mantener la integridad
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # 4. EL FILTRO DETERMINANTE
    # Mantener solo los que NO tienen fecha de término
    if col_termino in df.columns:
        # Filtramos estrictamente por valores nulos (vacíos)
        df = df[df[col_termino].isna()]

    # Eliminar filas donde la cama sea nula (final del archivo o basura)
    df = df[df[col_cama].notna()]
    
    return df

# --- INTERFAZ ---
try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_total()
        
        if not df_final.empty:
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success(f"📋 Se detectaron **{len(df_final)}** pacientes aislados actualmente.")
            st.caption(f"Actualizado: {time.strftime('%H:%M:%S')}")
        else:
            st.warning("⚠️ No hay aislamientos activos detectados en la última fila ni en el resto del documento.")

except Exception as e:
    st.error(f"Error al leer la última fila: {e}")
