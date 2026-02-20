import streamlit as st
import pandas as pd
import numpy as np

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_mejorado():
    # 1. Saltamos la fila 1 (Título)
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # Reemplazar vacíos por NaN para procesar
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.replace(['None', 'none', 'nan', 'NAN'], np.nan)

    # 3. LÓGICA DE FILAS DOBLES (Priorizando la fila completa)
    if col_cama in df.columns and col_nombre in df.columns:
        # Rellenamos identificación para agrupar
        df[col_cama] = df[col_cama].ffill()
        df[col_nombre] = df[col_nombre].ffill()
        
        # Unimos los Tipos de Aislamiento de ambas filas (Dato1 / Dato2)
        df[col_tipo] = df.groupby([col_cama, col_nombre])[col_tipo].transform(
            lambda x: ' / '.join(x.dropna().astype(str).unique())
        )

        # ORDENAR: Ponemos las filas con más datos arriba para que 'drop_duplicates' las conserve
        # Esto asegura que si la fila 1 tiene fechas y la fila 2 no, se quede con la fila 1.
        df['temp_count'] = df.notna().sum(axis=1)
        df = df.sort_values(by=[col_cama, 'temp_count'], ascending=[True, False])

    # 4. FILTRO DE TERMINADOS (Verde en Sheets)
    # Si tiene cualquier dato en FECHA DE TÉRMINO, se oculta
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # 5. ELIMINAR DUPLICADOS (Conserva la fila con más datos gracias al sort anterior)
    df = df.drop_duplicates(subset=[col_cama, col_nombre])
    
    # Limpieza final y orden original por cama
    df = df.drop(columns=['temp_count'], errors='ignore')
    df = df.sort_values(by=col_cama)
    df = df[df[col_cama].notna()]

    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar Censo Directo"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_mejorado()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Filtrar por Cama o Paciente:", placeholder="Ej. 2418...")
            
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success(f"📋 {len(df_final)} Aislamientos Activos detectados.")
        else:
            st.warning("⚠️ No hay pacientes activos detectados.")

except Exception as e:
    st.error(f"Error en la sincronización: {e}")
