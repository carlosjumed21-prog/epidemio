import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")

st.title("🦠 Control de Aislamientos Activos")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=10)
def cargar_aislamientos_definitivo():
    url_dinamica = f"{SHEET_URL}&nocache={time.time()}"
    
    # 1. Carga inicial (B a J)
    df = pd.read_csv(url_dinamica, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10]
    
    # Limpiar encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA DE VACÍOS ---
    df = df.apply(lambda x: x.astype(str).str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 2. IDENTIFICADOR ÚNICO POR EVENTO (No por nombre)
    # Creamos un ID que cambia cada vez que aparece una nueva CAMA o un nuevo NOMBRE
    # Esto evita que si un paciente aparece dos veces en la lista (aislamientos diferentes), se junten.
    df['EVENTO_ID'] = (df[col_cama].notna() | df[col_nombre].notna()).cumsum()

    def consolidar_evento(group):
        res = group.iloc[0].copy()
        # Si el tipo de aislamiento está repartido en dos filas, los une
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        
        # Para el resto, toma el dato que exista
        for col in group.columns:
            if col not in [col_tipo, 'EVENTO_ID']:
                val_real = group[col].dropna()
                res[col] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    # Agrupamos por el ID de evento único
    df = df.groupby('EVENTO_ID', as_index=False).apply(consolidar_evento)

    # 3. FILTRO ESTRICTO DE FECHA DE TÉRMINO
    # Si tiene cualquier dato en "FECHA DE TÉRMINO", el aislamiento terminó.
    # Solo mostramos los que son NaN (Vacíos).
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # Limpieza de filas basura (sin cama) y ordenamiento
    df = df[df[col_cama].notna()]
    df = df.sort_values(by=col_cama)
    
    # Quitamos la columna auxiliar antes de mostrar
    if 'EVENTO_ID' in df.columns:
        df = df.drop(columns=['EVENTO_ID'])

    return df

# --- INTERFAZ ---
try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar Censo", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_definitivo()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Buscar:", placeholder="Cama, Nombre, Microorganismo...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")
        else:
            st.warning("⚠️ No se detectaron aislamientos activos.")

except Exception as e:
    st.error(f"Error: {e}")
