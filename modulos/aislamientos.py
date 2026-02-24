import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de tu Google Sheets (Asegúrate de que sea la versión CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=1) # Cache de 1 segundo para pruebas
def cargar_censo_extremo():
    # Truco para saltar la cache de Google
    url_final = f"{SHEET_URL}&nocache={time.time()}"
    
    # 1. Leemos TODO el archivo sin saltar nada (header=None para no perder la primera fila por error)
    df = pd.read_csv(url_final, header=None, engine='python', encoding='utf-8')
    
    # 2. Buscamos en qué fila están realmente los encabezados
    # Buscamos la palabra "CAMA" en cualquier parte del archivo
    mask = df.apply(lambda x: x.astype(str).str.contains('CAMA', case=False)).any(axis=1)
    if not mask.any():
        return pd.DataFrame() # Si no encuentra la palabra CAMA, algo anda mal
    
    header_idx = df[mask].index[0]
    
    # 3. Recortamos y asignamos nombres
    df_datos = df.iloc[header_idx + 1:].copy() # Datos reales
    df_cols = df.iloc[header_idx].astype(str).str.strip().str.upper().tolist() # Encabezados
    
    # Asignar nombres y recortar a las columnas B-J (índices 1 a 9)
    df_datos.columns = df_cols
    df_final = df_datos.iloc[:, 1:10].copy()
    
    # Limpiar nombres de columnas para evitar errores de espacios
    df_final.columns = [str(c).strip().replace('\n', ' ') for c in df_final.columns]
    
    c_cama = "CAMA"
    c_nombre = "NOMBRE"
    c_termino = "FECHA DE TÉRMINO"

    # 4. Limpieza absoluta
    df_final = df_final.astype(str).apply(lambda x: x.str.strip())
    df_final = df_final.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 5. Rellenar para no perder pacientes en filas dobles
    df_final[c_cama] = df_final[c_cama].ffill()
    df_final[c_nombre] = df_final[c_nombre].ffill()

    # 6. FILTRO DE ORO: Si NO hay fecha de término, está activo
    # Eliminamos a los que tienen CUALQUIER dato en la columna de término
    if c_termino in df_final.columns:
        df_final = df_final[df_final[c_termino].isna()]

    # Eliminar basura (filas que no tienen ni cama ni nombre real)
    df_final = df_final[df_final[c_cama].notna()]
    
    return df_final

try:
    if st.button("🚨 Sincronización Forzada Total"):
        st.cache_data.clear()
        st.rerun()

    df = cargar_censo_extremo()

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.success(f"📋 **{len(df)}** Aislamientos Activos detectados.")
        
        # PRUEBA DE DIAGNÓSTICO:
        st.write("---")
        st.write("### 🔍 Diagnóstico de la fila 50:")
        st.write(f"Última cama en memoria: `{df.iloc[-1][0]}`")
        st.write(f"Último nombre en memoria: `{df.iloc[-1][1]}`")
    else:
        st.warning("No se detectan datos. Revisa la publicación de tu Google Sheets.")

except Exception as e:
    st.error(f"Error crítico: {e}")
