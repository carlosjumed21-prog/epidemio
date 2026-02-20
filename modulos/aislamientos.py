import streamlit as st
import pandas as pd
import numpy as np

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_especifico():
    # 1. Saltamos la fila 1 (Título) para que la fila 2 sea el encabezado
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # Reemplazar celdas vacías por NaN reales para procesar
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.replace(['None', 'none', 'nan', 'NAN'], np.nan)

    # 3. LÓGICA DE FUSIÓN SELECTIVA
    if col_cama in df.columns and col_nombre in df.columns:
        # Rellenamos identificación temporalmente para saber quién es quién
        df[col_cama] = df[col_cama].ffill()
        df[col_nombre] = df[col_nombre].ffill()
        
        # Agrupamos y fusionamos únicamente la columna TIPO DE AISLAMIENTO
        # Esto crea una serie con "Aislamiento1 / Aislamiento2"
        tipos_fusionados = df.groupby([col_cama, col_nombre])[col_tipo].transform(
            lambda x: ' / '.join(x.dropna().astype(str).unique())
        )

        # Contamos cuántos datos tiene cada fila para identificar la "Fila Maestra" (la más llena)
        df['temp_count'] = df.notna().sum(axis=1)
        
        # Ordenamos para que la fila con más datos quede arriba
        df = df.sort_values(by=[col_cama, 'temp_count'], ascending=[True, False])
        
        # Aplicamos la fusión de tipos a la columna correspondiente
        df[col_tipo] = tipos_fusionados

    # 4. FILTRO DE FECHA DE TÉRMINO (Ocultar si ya se terminó/sombreado verde)
    if col_termino in df.columns:
        df = df[df[col_termino].isna()]

    # 5. ELIMINAR LA FILA VACÍA (Conserva solo la que tiene más datos)
    # Al haber ordenado por 'temp_count', drop_duplicates dejará la fila con fechas y motivos
    df = df.drop_duplicates(subset=[col_cama, col_nombre], keep='first')
    
    # Limpieza final: quitar columna auxiliar y ordenar por cama
    df = df.drop(columns=['temp_count'], errors='ignore')
    df = df.sort_values(by=col_cama)
    df = df[df[col_cama].notna()]

    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_especifico()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Buscar paciente:", placeholder="Cama o Nombre...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Visualización de la tabla
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"📋 {len(df_final)} pacientes en aislamiento activo detectados.")
        else:
            st.info("No hay aislamientos activos detectados (Celdas de Fecha de Término vacías).")

except Exception as e:
    st.error(f"Error al procesar la lista: {e}")
