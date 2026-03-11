import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Control de Aislamientos", layout="wide")
st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

def cargar_aislamientos():
    # 1. Carga cruda
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte B a J (Esto nos deja con 9 columnas)
    # Columna B=0, C=1, D=2, E=3, F=4, G=5, H=6, I=7, J=8
    df = df.iloc[:, 1:10]
    
    # 3. Limpieza de nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Identificamos las columnas por su POSICIÓN para evitar errores de nombre
    # Columna 0: CAMA, Columna 1: NOMBRE, Columna 2: TIPO, Columna 7: FECHA TÉRMINO
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_termino = df.columns[7] # Esta es la COLUMNA I original

    # 4. Normalización de datos
    # Convertimos todo a string y "limpiamos" valores que significan vacío
    df = df.astype(str).apply(lambda x: x.str.strip())
    nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
    
    # Rellenar hacia abajo para filas combinadas
    df[col_cama] = df[col_cama].replace(nulos, np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(nulos, np.nan).ffill()

    # 5. Consolidación de filas (para pacientes con múltiples aislamientos)
    def consolidar(group):
        res = group.iloc[0].copy()
        # Unir tipos de aislamiento
        tipos = [t for t in group[col_tipo].unique() if t not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        # Para la columna de TÉRMINO, verificamos si hay ALGO escrito en el grupo
        fechas = [f for f in group[col_termino].values if f not in nulos]
        res[col_termino] = fechas[0] if fechas else "VACIO"
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # --- 6. EL FILTRO CRÍTICO ---
    # Solo queremos las filas donde la columna de TÉRMINO (Columna I) sea "VACIO"
    df = df[df[col_termino] == "VACIO"]
    
    # Opcional: Quitar la columna de término de la vista ya que sabemos que está vacía
    df = df.drop(columns=[col_termino])
    
    # Ordenar por cama
    df = df[df[col_cama].notna()]
    df = df.sort_values(by=col_cama)
    
    return df

try:
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_aislamientos()

    if not df_final.empty:
        busqueda = st.text_input("🔍 Buscar por Cama o Nombre:")
        if busqueda:
            mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_final = df_final[mask]

        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.success(f"✅ Mostrando {len(df_final)} pacientes aislados (Columna I vacía).")
    else:
        st.warning("⚠️ No se encontraron pacientes con la Columna I (Fecha de Término) vacía.")

except Exception as e:
    st.error(f"Error al procesar: {e}")
