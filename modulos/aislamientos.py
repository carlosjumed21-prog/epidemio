import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_inteligente():
    # 1. Cargar el CSV crudo sin procesar nada
    raw_df = pd.read_csv(SHEET_URL, header=None, engine='python', encoding='utf-8')
    
    # 2. ENCONTRAR LA FILA DE ENCABEZADOS
    # Buscamos en qué fila está la palabra "CAMA"
    fila_encabezado = 0
    for idx, row in raw_df.iterrows():
        if row.astype(str).str.contains('CAMA', case=False, na=False).any():
            fila_encabezado = idx
            break
    
    # 3. REESTRUCTURAR EL DATAFRAME
    # Tomamos esa fila como nombres de columna y los datos hacia abajo
    df = raw_df.iloc[fila_encabezado:].copy()
    df.columns = df.iloc[0] # Asignar nombres
    df = df.iloc[1:]        # Quitar la fila que acabamos de usar como nombre
    
    # 4. RECORTE DE COLUMNAS B a J (Índices posicionales 1 a 9)
    # Independientemente de cómo se llamen, agarramos ese bloque
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas para el filtro
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # 5. FILTRO DE EGRESOS (Columna J / última del recorte)
    # Dejamos solo donde sea Nulo, Vacío o tenga espacios
    col_egreso = df.columns[-1]
    
    # Limpiamos la columna de egreso para detectar espacios vacíos
    df[col_egreso] = df[col_egreso].astype(str).replace(['nan', 'None', 'NULL', ''], pd.NA).str.strip()
    
    # Filtramos: Solo filas donde la última columna sea NA
    df_activos = df[df[col_egreso].isna()]
    
    # Limpieza final: Eliminar filas donde la columna de "NOMBRE" esté vacía 
    # (usualmente la 3ra del recorte B-J)
    col_nombre = df_activos.columns[2]
    df_activos = df_activos[df_activos[col_nombre].notna() & (df_activos[col_nombre] != 'nan')]
    
    return df_activos

try:
    with st.container(border=True):
        if st.button("🔄 Forzar Sincronización"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_inteligente()
        
        if not df_final.empty:
            busqueda = st.text_input("🔍 Buscar paciente:", placeholder="Cama o nombre...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"✅ {len(df_final)} pacientes aislados actualmente.")
        else:
            st.warning("⚠️ No se detectaron pacientes aislados.")
            st.info("Verifica que los pacientes activos NO tengan nada escrito en la columna J (INGRESO/EGRESO).")

except Exception as e:
    st.error(f"Error técnico: {e}")
