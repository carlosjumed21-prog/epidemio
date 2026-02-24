import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")
st.title("🦠 Control de Aislamientos Activos")

# URL de publicación
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2)
def cargar_censo_total():
    # 1. Forzar lectura fresca
    url_final = f"{SHEET_URL}&cachebust={time.time()}"
    
    # 2. Leemos TODO el archivo sin saltar filas inicialmente
    # Esto asegura que no nos "comamos" la última fila por un error de conteo
    df_raw = pd.read_csv(url_final, engine='python', encoding='utf-8')
    
    # 3. Localizar la fila de encabezados real
    # Buscamos la fila donde aparezca la palabra "CAMA" (usualmente la fila 1 o 2)
    # y recortamos desde ahí hacia abajo
    header_row = 0
    for i, row in df_raw.iterrows():
        if "CAMA" in [str(val).upper() for val in row.values]:
            header_row = i
            break
            
    # Re-leemos o recortamos desde esa fila
    df = df_raw.iloc[header_row:].copy()
    df.columns = df.iloc[0] # La primera fila encontrada son los nombres
    df = df[1:] # El resto son los datos
    
    # 4. Recorte de columnas (B a J)
    # Seleccionamos por posición para evitar errores si los nombres cambian un poco
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA TOTAL ---
    # Convertimos a string y quitamos espacios
    df = df.astype(str).apply(lambda x: x.str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 5. LÓGICA DE FILAS DOBLES (Consolidación)
    # Rellenamos para no perder contexto en la última fila
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    def consolidar_evento(group):
        res = group.iloc[0].copy()
        # Unir tipos de aislamiento
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        # Rescatar cualquier otro dato perdido en la fila de abajo
        for c in group.columns:
            if c not in [col_tipo, col_cama, col_nombre]:
                val = group[c].dropna()
                res[c] = val.iloc[0] if not val.empty else np.nan
        return res

    # Agrupamos por cama y nombre para consolidar
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_evento)

    # 6. FILTRO DE ACTIVOS (Celdas vacías en Término)
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # Filtro final: que la cama no sea nula
    df = df[df[col_cama].notna()]
    
    return df

# --- INTERFAZ ---
try:
    if st.button("🔄 Actualización Forzada (Escanear hasta fila final)"):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_censo_total()

    if not df_final.empty:
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")
        
        # Verificación visual para ti
        st.info(f"Última cama detectada en el sistema: {df_final.iloc[-1][col_cama]}")
    else:
        st.warning("⚠️ No se encontraron pacientes activos.")

except Exception as e:
    st.error(f"Hubo un error al leer el archivo: {e}")
