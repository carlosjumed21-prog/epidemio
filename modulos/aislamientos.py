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
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_egreso = "INGRESO/EGRESO"

    # Reemplazar celdas vacías por NaN para procesar
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # 3. LÓGICA DE FILAS DOBLES
    # Rellenamos hacia abajo para que la segunda fila del paciente herede la CAMA y NOMBRE
    if col_cama in df.columns and col_nombre in df.columns:
        # IMPORTANTE: Antes de filtrar, unimos los datos de las filas dobles
        df[col_tipo] = df.groupby(df[col_cama].ffill())[col_tipo].transform(
            lambda x: ' / '.join(x.dropna().astype(str).unique())
        )
        # Rellenamos los datos de identificación
        df[col_cama] = df[col_cama].ffill()
        df[col_nombre] = df[col_nombre].ffill()

    # 4. FILTRO CRÍTICO: MOSTRAR SOLO NO RESALTADOS
    # Asumimos que los "Resaltados en Verde" son aquellos que ya tienen datos en INGRESO/EGRESO
    # O que la fila de la CAMA se deja de contabilizar si el paciente ya no está.
    if col_egreso in df.columns:
        # Solo mantenemos filas donde INGRESO/EGRESO está realmente vacío (Aislamiento activo)
        df = df[df[col_egreso].isna() | (df[col_egreso].astype(str).str.strip() == "")]

    # 5. ELIMINAR DUPLICADOS DE FILAS DOBLES
    df = df.drop_duplicates(subset=[col_cama, col_nombre])
    
    # 6. FILTRO DE SEGURIDAD POR COLUMNA CAMA
    # Si la cama está vacía o es 'nan', no se muestra (esto filtra las filas de cierre o basura)
    df = df[df[col_cama].notna() & (df[col_cama].astype(str).str.strip() != "nan")]

    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar Censo Directo"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_activos()
        
        if not df_final.empty:
            # Buscador por cama o nombre
            busqueda = st.text_input("🔍 Filtrar por Cama o Paciente:", placeholder="Ej. 4210...")
            
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
            st.warning("⚠️ No hay pacientes activos detectados que cumplan el criterio.")

except Exception as e:
    st.error(f"Error en la sincronización: {e}")
