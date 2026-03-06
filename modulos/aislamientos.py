import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

# --- URLs ---
SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def cargar_censo_total():
    url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10]
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # Lógica de limpieza y ffill
    df["CAMA"] = df["CAMA"].ffill()
    df["NOMBRE"] = df["NOMBRE"].ffill()
    df = df.astype(str).replace(['nan', 'None', ''], np.nan)

    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group["TIPO DE AISLAMIENTO"].dropna().unique()
        res["TIPO DE AISLAMIENTO"] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        return res

    df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar)
    
    if "FECHA DE TÉRMINO" in df.columns:
        df = df[df["FECHA DE TÉRMINO"].isna()]
    
    return df[df["CAMA"].notna()]

# --- INTERFAZ ÚNICA ---
st.title("🦠 Control de Aislamientos Activos")

try:
    # 1. CARGA DE DATOS
    df_final = cargar_censo_total()

    # 2. SECCIÓN DE ACCIONES (Botones principales)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 Actualizar Servidor", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    with col2:
        # BOTÓN DE ENVÍO DIRECTO
        if st.button("🚀 Enviar Datos al Censo", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
            st.success("¡Sincronizado!")
            st.rerun()

    with col3:
        # BOTÓN PARA ABRIR EL SHEET EN OTRA PESTAÑA
        st.link_button("📂 Abrir Google Sheet", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()

    # 3. BUSCADOR Y TABLA EDITABLE
    busqueda = st.text_input("🔍 Buscar paciente o cama:")
    
    # Leemos el censo de Carlos para que la edición sea persistente
    df_censo = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)

    if not df_censo.empty:
        if busqueda:
            mask = df_censo.apply(lambda r: r.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_censo = df_censo[mask]

        # EDITOR DE DATOS
        df_editado = st.data_editor(
            df_censo,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="main_editor"
        )

        if st.button("💾 Guardar Cambios en el Censo", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_editado)
            st.toast("Cambios guardados", icon="✅")
    else:
        st.info("El censo está vacío. Presiona 'Enviar Datos' para comenzar.")

except Exception as e:
    st.error(f"Error en el sistema: {e}")
