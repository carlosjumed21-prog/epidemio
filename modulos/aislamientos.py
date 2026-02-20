import streamlit as st
import pandas as pd
import numpy as np

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_activos():
    # 1. Saltamos la fila 1 (Título) para que la fila 2 sea el encabezado
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # Identificación de columnas clave
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO" # Columna H (Referencia para el filtro)

    # Reemplazar variantes de "vacío" por NaN real para procesar
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.replace(['nan', 'None', 'none', 'NULL'], np.nan)

    # 3. LÓGICA DE FILAS DOBLES (Agrupación antes de filtrar)
    # Rellenamos hacia abajo para que la fila de abajo herede la identificación
    if col_cama in df.columns and col_nombre in df.columns:
        # Unimos los tipos de aislamiento de las dos filas con "/"
        df[col_tipo] = df.groupby(df[col_cama].ffill())[col_tipo].transform(
            lambda x: ' / '.join(x.dropna().astype(str).unique())
        )
        df[col_cama] = df[col_cama].ffill()
        df[col_nombre] = df[col_nombre].ffill()
        # La fecha de término también debe heredarse para que el filtro afecte a ambas filas
        df[col_termino] = df[col_termino].ffill()

    # 4. FILTRO ESTRICTO: Solo los que NO tienen fecha de término
    # Si la celda está vacía (NaN), el aislamiento continúa.
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # 5. ELIMINAR DUPLICADOS TRAS LA CONSOLIDACIÓN
    df = df.drop_duplicates(subset=[col_cama, col_nombre])
    
    # Limpieza de filas de basura (donde no hay ni cama ni nombre)
    df = df.dropna(subset=[col_cama, col_nombre], how='all')

    return df

try:
    with st.container(border=True):
        if st.button("🔄 Actualizar desde Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_activos()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Buscar en activos:", placeholder="Cama, nombre...")
            
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Mostrar tabla final
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"✅ Se detectaron {len(df_final)} pacientes con aislamiento en curso.")
        else:
            st.warning("⚠️ No hay aislamientos activos (Todos tienen FECHA DE TÉRMINO).")

except Exception as e:
    st.error(f"Error al procesar la información: {e}")
