import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_aislamientos_definitivo():
    # Salto de caché de Google Sheets
    url_dinamica = f"{SHEET_URL}&nocache={time.time()}"
    
    # 1. Carga inicial saltando el encabezado de título
    df = pd.read_csv(url_dinamica, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de columnas B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Normalizar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA DE NULOS ---
    # Convertimos todo a string para limpiar espacios y luego detectamos vacíos reales
    df = df.apply(lambda x: x.astype(str).str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 3. LÓGICA DE UNIÓN DE FILAS (Manejo de registros dobles)
    # Rellenamos hacia abajo Cama y Nombre para agrupar filas que pertenecen al mismo registro
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    def consolidar_paciente(group):
        # Usamos la primera fila como molde
        res = group.iloc[0].copy()
        
        # Combinamos los tipos de aislamiento si hay varios en las filas agrupadas
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        
        # Para el resto de las columnas (incluyendo FECHA DE TÉRMINO), 
        # buscamos si alguna de las filas tiene un dato real
        for col in group.columns:
            if col not in [col_tipo, col_cama, col_nombre]:
                val_real = group[col].dropna()
                res[col] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    # Agrupamos por Cama y Nombre para fusionar las filas dobles
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)

    # 4. FILTRO CRÍTICO: AISLAMIENTOS ACTIVOS
    # Solo conservamos las filas donde "FECHA DE TÉRMINO" es nulo (NaN)
    if col_termino in df.columns:
        # Importante: Solo pasan los que NO tienen dato en esa columna
        df = df[df[col_termino].isna()]

    # Limpieza de filas sin cama y ordenamiento
    df = df[df[col_cama].notna()]
    df = df.sort_values(by=col_cama)

    return df

# --- INTERFAZ ---
try:
    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.markdown("### Censo Nominal")
        with col_t2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        df_final = cargar_aislamientos_definitivo()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Filtrar por paciente o cama:", placeholder="Escribe aquí...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success(f"✅ Se encontraron {len(df_final)} pacientes en aislamiento activo.")
            st.caption(f"Sincronizado a las: {time.strftime('%H:%M:%S')}")
        else:
            st.warning("ℹ️ No hay aislamientos activos registrados actualmente.")

except Exception as e:
    st.error(f"Error al leer la base de datos: {e}")
