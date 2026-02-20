import streamlit as st
import pandas as pd
import numpy as np

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_consolidados():
    # 1. Saltamos la fila 1 (Título) para que la fila 2 sea el encabezado
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # Identificamos las columnas clave por su nombre limpio
    # Basado en tu estructura: B=CAMA, D=NOMBRE, E=TIPO DE AISLAMIENTO, J=INGRESO/EGRESO
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_egreso = "INGRESO/EGRESO"

    # Reemplazar celdas que parecen vacías por NaN para poder procesarlas
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # 3. LÓGICA DE FILAS DOBLES (Agrupación por paciente)
    # Rellenamos hacia abajo el nombre y la cama para que la fila 2 sepa a quién pertenece
    if col_cama in df.columns and col_nombre in df.columns:
        df[col_cama] = df[col_cama].ffill()
        df[col_nombre] = df[col_nombre].ffill()

    # Consolidamos la columna "TIPO DE AISLAMIENTO"
    # Si hay dos filas para el mismo paciente, une los tipos con " / "
    if col_tipo in df.columns:
        df[col_tipo] = df.groupby([col_cama, col_nombre])[col_tipo].transform(
            lambda x: ' / '.join(x.dropna().astype(str).unique())
        )

    # 4. Eliminamos la fila duplicada después de haber unido los datos
    df = df.drop_duplicates(subset=[col_cama, col_nombre])

    # 5. FILTRO DE ACTIVOS (Solo donde INGRESO/EGRESO esté vacío)
    if col_egreso in df.columns:
        # Dejamos solo los que son NaN (no tienen fecha de egreso/sombreado verde)
        df = df[df[col_egreso].isna() | (df[col_egreso].astype(str).str.strip() == "")]
    
    # Limpieza de filas de basura al final del documento
    df = df.dropna(subset=[col_nombre])
    
    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_consolidados()
        
        if not df_final.empty:
            # Buscador funcional
            busqueda = st.text_input("🔍 Buscar en el censo:", placeholder="Escribe cama, nombre o tipo de aislamiento...")
            
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Visualización de la tabla
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"✅ Mostrando {len(df_final)} pacientes aislados.")
        else:
            st.info("No se encontraron aislamientos activos en este momento.")

except Exception as e:
    st.error(f"Error al procesar la información: {e}")
