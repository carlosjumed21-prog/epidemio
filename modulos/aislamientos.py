import streamlit as st
import pandas as pd
import numpy as np

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_activos():
    # 1. Saltamos la fila 1 para que la fila 2 sea el encabezado
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO" # Esta es nuestra columna maestra para el filtro

    # Reemplazar celdas que parecen vacías por NaN reales
    df = df.replace(r'^\s*$', np.nan, regex=True)
    # Limpiar también strings que dicen "None" o "none" que a veces genera Google Sheets
    df = df.replace(['None', 'none', 'nan', 'NAN'], np.nan)

    # 3. LÓGICA DE FILAS DOBLES (Consolidación)
    if col_cama in df.columns and col_nombre in df.columns:
        # Rellenamos identificación hacia abajo para no perder la relación en filas dobles
        df[col_cama] = df[col_cama].ffill()
        df[col_nombre] = df[col_nombre].ffill()
        
        # Unimos los tipos de aislamiento (ej. "Contacto / Gotitas") antes de filtrar
        df[col_tipo] = df.groupby([col_cama, col_nombre])[col_tipo].transform(
            lambda x: ' / '.join(x.dropna().astype(str).unique())
        )

    # 4. FILTRO DE ORO: SI TIENE FECHA DE TÉRMINO (FILA VERDE), SE ELIMINA
    if col_termino in df.columns:
        # Filtramos para dejar SOLO los que son NaN (Vacíos)
        # Esto ocultará automáticamente a cualquier fila que ya marcaste en verde con su fecha
        df = df[df[col_termino].isna()]

    # 5. ELIMINAR DUPLICADOS TRAS LA CONSOLIDACIÓN
    df = df.drop_duplicates(subset=[col_cama, col_nombre])
    
    # 6. LIMPIEZA DE FILAS VACÍAS
    df = df[df[col_cama].notna()]

    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar Censo Directo"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_activos()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Filtrar por Cama o Paciente:", placeholder="Ej. 7305...")
            
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Tabla de visualización
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"📋 {len(df_final)} Aislamientos Activos detectados.")
        else:
            st.warning("⚠️ No hay pacientes activos. (Todos los detectados tienen Fecha de Término).")

except Exception as e:
    st.error(f"Error en la sincronización: {e}")
