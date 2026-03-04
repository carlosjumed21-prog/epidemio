import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de publicación original
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

@st.cache_data(ttl=2)
def cargar_censo_total():
    # Forzar lectura fresca
    url_final = f"{SHEET_URL}&cachebust={time.time()}"
    
    # 1. Leemos el archivo. Skiprows=1 para saltar el título "AISLAMIENTOS"
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte manual de columnas B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # 3. Normalizar encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    c_cama = "CAMA"
    c_nombre = "NOMBRE"
    c_tipo = "TIPO DE AISLAMIENTO"
    c_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA DE DATOS ---
    df = df.astype(str).apply(lambda x: x.str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 4. LÓGICA DE FILAS DOBLES
    df[c_cama] = df[c_cama].ffill()
    df[c_nombre] = df[c_nombre].ffill()

    def consolidar_evento(group):
        res = group.iloc[0].copy()
        tipos = group[c_tipo].dropna().unique()
        res[c_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        for col in group.columns:
            if col not in [c_tipo, c_cama, c_nombre]:
                val_real = group[col].dropna()
                res[col] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    df = df.groupby([c_cama, c_nombre], as_index=False, sort=False).apply(consolidar_evento)

    # 5. FILTRO DE ACTIVOS
    if c_termino in df.columns:
        df = df[df[c_termino].isna()]

    df = df[df[c_cama].notna()]
    
    return df

# --- INTERFAZ ---
try:
    if st.button("🔄 Actualizar Censo", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_censo_total()

    if not df_final.empty:
        # Buscador
        busqueda = st.text_input("🔍 Buscar por cama, nombre o microorganismo:")
        if busqueda:
            mask = df_final.apply(lambda r: r.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_final = df_final[mask]

        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")
        
    else:
        st.warning("⚠️ No se encontraron pacientes activos sin fecha de término.")

except Exception as e:
    st.error(f"Error al procesar el archivo: {e}")
