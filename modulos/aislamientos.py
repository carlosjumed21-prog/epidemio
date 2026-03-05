import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

# --- URLs DE LOS SHEETS ---
# 1. Origen (Solo lectura - CSV publicado)
SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

# 2. Destino (Editable - Sheet de Carlos)
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit?usp=sharing"

# --- CONEXIÓN A GSHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def cargar_censo_total():
    # Forzar lectura fresca del origen
    url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
    
    # 1. Leemos el archivo original
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

# --- INTERFAZ DE USUARIO ---
st.title("🦠 Sistema de Control de Aislamientos")

# Pestañas para organizar la vista
tab1, tab2 = st.tabs(["🔍 Monitor en Tiempo Real", "📝 Censo Editable (Carlos)"])

with tab1:
    st.header("Aislamientos Detectados")
    if st.button("🔄 Actualizar Datos del Servidor", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    try:
        df_final = cargar_censo_total()

        if not df_final.empty:
            busqueda = st.text_input("🔍 Buscar en tiempo real (cama, nombre, etc):")
            if busqueda:
                mask = df_final.apply(lambda r: r.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_mostrar = df_final[mask]
            else:
                df_mostrar = df_final

            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")
            
            # BOTÓN PARA ENVIAR AL SEGUNDO SHEET
            st.divider()
            if st.button("🚀 ENVIAR ESTA TABLA AL CENSO EDITABLE", use_container_width=True):
                conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
                st.balloons()
                st.success("✅ Datos sincronizados con el Sheet de Carlos.")
        
        else:
            st.warning("⚠️ No se encontraron pacientes activos.")

    except Exception as e:
        st.error(f"Error al procesar el origen: {e}")

with tab2:
    st.header("Censo Aislamientos 26 (Carlos)")
    st.info("Aquí puedes editar la información, agregar filas o modificar notas manualmente.")

    try:
        # Leer la data actual del segundo sheet
        df_editable = conn.read(spreadsheet=SHEET_URL_EDITABLE)

        # Editor interactivo
        df_actualizado = st.data_editor(
            df_editable,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="editor_carlos"
        )

        # Botón para guardar los cambios hechos en esta tabla
        if st.button("💾 Guardar Cambios Manuales", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_actualizado)
            st.toast("Cambios guardados exitosamente", icon="✅")
            
    except Exception as e:
        st.error(f"Error al conectar con el Censo Editable: {e}")
        st.info("Asegúrate de que el Sheet tenga permisos de 'Editor' para cualquier persona con el enlace.")
