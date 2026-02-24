import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

# Agregamos caché de 60 segundos para no saturar la red, pero mantener frescura
@st.cache_data(ttl=60)
def cargar_aislamientos_definitivo():
    # Truco: Agregamos un timestamp a la URL para saltar la caché de Google
    url_con_timestamp = f"{SHEET_URL}&cachebust={time.time()}"
    
    # 1. Carga inicial saltando el título
    df = pd.read_csv(url_con_timestamp, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte estricto de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA CRÍTICA DE "NONE" Y ESPACIOS ---
    df = df.apply(lambda x: x.astype(str).str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 3. LÓGICA DE UNIÓN DE FILAS DOBLES
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    def consolidar_paciente(group):
        res = group.iloc[0].copy()
        # Combinamos los Tipos de Aislamiento únicos
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        
        # Para el resto de columnas, buscamos el valor que sí tenga datos
        for col in group.columns:
            if col not in [col_tipo, col_cama, col_nombre]:
                val_real = group[col].dropna()
                res[col] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    # Aplicamos consolidación
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)

    # 4. FILTRO DE FECHA DE TÉRMINO
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # Limpieza final y ordenamiento
    df = df[df[col_cama].notna()]
    df = df.sort_values(by=col_cama)

    return df

# --- INTERFAZ DE USUARIO ---
try:
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("💡 Los datos se actualizan automáticamente cada 60s o al presionar el botón.")
        with col2:
            if st.button("🔄 Sincronizar Ahora", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        df_final = cargar_aislamientos_definitivo()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Buscar por Cama o Nombre:", placeholder="Ej. 7305...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Mostramos la tabla
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success(f"📋 {len(df_final)} Aislamientos Activos detectados.")
            
            # Timestamp de la última actualización local
            st.caption(f"Última consulta al servidor: {time.strftime('%H:%M:%S')}")
        else:
            st.warning("⚠️ No se detectaron aislamientos activos (Todos tienen Fecha de Término).")

except Exception as e:
    st.error(f"Error en la sincronización: {e}")
