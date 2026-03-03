import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")
st.title("🦠 Control de Aislamientos y Censo General")

# URLs de publicación
URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
URL_CENSO_NUEVO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSD2cPIZRxh-b5NyaVARl3Ioa5B0KeIqdLhtDkQ1nldthyu6TIT4KrWG5NWSNiUeY0XWiL1icDafU0P/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2)
def cargar_datos(url, es_aislamiento=True):
    url_final = f"{url}&cachebust={time.time()}"
    
    try:
        if es_aislamiento:
            # Lógica original para Aislamientos (saltando título)
            df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
            df = df.iloc[:, 1:10] # Columnas B a J
        else:
            # Lógica para la nueva hoja de Censo
            df = pd.read_csv(url_final, engine='python', encoding='utf-8')

        # Normalizar encabezados
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpieza básica
        df = df.astype(str).apply(lambda x: x.str.strip())
        df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)
        
        if es_aislamiento:
            c_cama, c_nombre, c_tipo, c_termino = "CAMA", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"
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
            if c_termino in df.columns:
                df = df[df[c_termino].isna()]
            df = df[df[c_cama].notna()]
            
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🔄 Actualizar Todo", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

tab1, tab2 = st.tabs(["📑 Censo Nuevo", "🦠 Aislamientos Activos"])

with tab1:
    st.subheader("Censo de Pacientes (Nueva Hoja)")
    df_censo = cargar_datos(URL_CENSO_NUEVO, es_aislamiento=False)
    if not df_censo.empty:
        busqueda_c = st.text_input("🔍 Buscar en censo:", key="bus_censo")
        if busqueda_c:
            mask = df_censo.apply(lambda r: r.astype(str).str.contains(busqueda_c, case=False).any(), axis=1)
            df_censo = df_censo[mask]
        
        # El dataframe de Streamlit autoajusta columnas por defecto al contenido
        st.dataframe(df_censo, use_container_width=True, hide_index=True)
        st.caption(f"Total de registros en censo: {len(df_censo)}")
    else:
        st.warning("No hay datos disponibles en la nueva hoja.")

with tab2:
    st.subheader("Pacientes en Aislamiento")
    df_aisla = cargar_datos(URL_AISLAMIENTOS, es_aislamiento=True)
    if not df_aisla.empty:
        busqueda_a = st.text_input("🔍 Buscar en aislamientos:", key="bus_aisla")
        if busqueda_a:
            mask = df_aisla.apply(lambda r: r.astype(str).str.contains(busqueda_a, case=False).any(), axis=1)
            df_aisla = df_aisla[mask]
            
        st.dataframe(df_aisla, use_container_width=True, hide_index=True)
        st.success(f"📋 **{len(df_aisla)}** Aislamientos Activos.")
    else:
        st.info("No se detectaron aislamientos activos.")
