import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")

st.title("🦠 Control de Aislamientos Activos")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=10) # Bajamos a 10 segundos para máxima frescura
def cargar_aislamientos_definitivo():
    url_dinamica = f"{SHEET_URL}&nocache={time.time()}"
    
    # 1. Carga inicial
    df = pd.read_csv(url_dinamica, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de columnas B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Normalizar encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA INICIAL ---
    # Convertimos a string y quitamos espacios. 
    # IMPORTANTE: No convertimos a NaN todavía para no romper el ffill
    df = df.apply(lambda x: x.astype(str).str.strip())
    
    # Reemplazamos variantes de "vacío" por un valor nulo real de Python
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 3. LÓGICA DE UNIÓN DE FILAS (Solo si el nombre está vacío en la segunda fila)
    # Solo rellenamos la cama si realmente pertenece al mismo proceso
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    def consolidar_paciente(group):
        if len(group) == 1:
            return group.iloc[0]
        
        res = group.iloc[0].copy()
        
        # Unimos tipos de aislamiento (ej. Contacto + Gotitas)
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        
        # Para el resto, buscamos cualquier dato existente en las filas del grupo
        for col in group.columns:
            if col not in [col_tipo, col_cama, col_nombre]:
                val_real = group[col].dropna()
                res[col] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    # Agrupamos. Si esto sigue dando 7, es que dos pacientes comparten Cama y Nombre en el Excel.
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)

    # 4. FILTRO DE AISLAMIENTOS ACTIVOS (EL CORAZÓN DEL PROBLEMA)
    # Filtramos: Solo nos quedamos con los que tienen la FECHA DE TÉRMINO vacía
    if col_termino in df.columns:
        # Nos aseguramos de que sea NaN real
        df = df[df[col_termino].isna()]

    # Limpieza final
    df = df[df[col_cama].notna()]
    df = df.sort_values(by=col_cama)

    return df

# --- INTERFAZ ---
try:
    with st.container(border=True):
        if st.button("🔄 Forzar Actualización (Limpiar Caché)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_definitivo()
        
        if not df_final.empty:
            # Buscador funcional
            busqueda = st.text_input("🔍 Buscar por Cama o Nombre:", placeholder="Ej. 7305...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            st.dataframe(df_final, use_container_width=True, hide_index=True)
            
            # El conteo que te preocupa
            st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")
            st.caption(f"Última lectura del Excel: {time.strftime('%H:%M:%S')}")
        else:
            st.warning("⚠️ No se detectaron aislamientos activos.")

except Exception as e:
    st.error(f"Error: {e}")
