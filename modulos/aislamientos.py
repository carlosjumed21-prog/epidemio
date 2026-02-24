import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de publicación
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2) # TTL mínimo para detectar cambios rápidos
def cargar_censo_definitivo():
    # El truco del tiempo para que Google no nos engañe con datos viejos
    url_final = f"{SHEET_URL}&nocache={time.time()}"
    
    # 1. Cargar datos
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Seleccionar columnas B a J
    df = df.iloc[:, 1:10]
    
    # 3. Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA CRÍTICA ---
    # Convertimos todo a texto y limpiamos espacios. 
    # Esto es vital para que la última fila no se ignore si tiene espacios.
    df = df.astype(str).apply(lambda x: x.str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # --- LÓGICA DE FILAS DOBLES (SIN PERDER LA ÚLTIMA) ---
    # Rellenamos solo los datos del paciente hacia abajo para que la fila de abajo
    # tenga el contexto de quién es, pero SIN agrupar todavía.
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    # Ahora agrupamos, pero usamos un ID de fila para no mezclar pacientes distintos
    # que por error tengan el mismo nombre o cama.
    df['AUX_ID'] = (df[col_cama].astype(str) + df[col_nombre].astype(str))
    
    # Esta función une los aislamientos si el paciente tiene 2 filas
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        # Para el resto de columnas, si la primera fila es nula, busca en la segunda
        for c in group.columns:
            if c not in [col_tipo, 'AUX_ID']:
                val_real = group[c].dropna()
                res[c] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    # Agrupamos respetando el orden original para no perder la última fila
    df = df.groupby(['AUX_ID'], as_index=False, sort=False).apply(consolidar)

    # --- EL FILTRO DE "TERMINADO" ---
    # Si la FECHA DE TÉRMINO es nula (NaN), el paciente está activo.
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # Eliminar cualquier fila que no tenga cama (final del archivo)
    df = df[df[col_cama].notna()]
    
    # Limpieza de columnas auxiliares
    if 'AUX_ID' in df.columns:
        df = df.drop(columns=['AUX_ID'])
        
    return df

# --- INTERFAZ ---
try:
    if st.button("🔄 Sincronizar Censo (Forzar lectura de última fila)"):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_censo_definitivo()

    if not df_final.empty:
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")
        st.info(f"Último paciente en lista: {df_final.iloc[-1][0]} - {df_final.iloc[-1][1]}")
    else:
        st.warning("⚠️ No se detectan aislamientos activos.")

except Exception as e:
    st.error(f"Error en la lectura: {e}")
