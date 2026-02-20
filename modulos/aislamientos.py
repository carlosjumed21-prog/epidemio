import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
# Asegúrate de que sea el link de "Publicar en la web" como CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_especifico():
    # 1. Cargamos el archivo saltando la primera fila (el título "AISLAMIENTOS 2026")
    # skiprows=1 hace que la fila 2 sea el encabezado real
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Seleccionamos solo las columnas de la B a la J
    # En Python, las posiciones empiezan en 0 (A=0, B=1, C=2...)
    # Columna B (índice 1) hasta Columna J (índice 9) -> [1:10]
    df = df.iloc[:, 1:10]
    
    # 3. Limpiar nombres de columnas para asegurar el filtro
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # 4. Lógica de exclusión: Solo filas donde la última columna esté vacía
    # Basado en tu archivo, la columna J (índice 8) es "INGRESO/EGRESO"
    col_egreso = df.columns[-1] 
    df = df[df[col_egreso].isna() | (df[col_egreso].astype(str).str.strip() == "")]
    
    # Eliminar filas que estén completamente vacías (por si hay basura al final del Excel)
    df = df.dropna(how='all')
    
    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_especifico()
        
        if not df_final.empty:
            # Buscador por cualquier campo (Cama, Nombre, etc.)
            busqueda = st.text_input("🔍 Buscar paciente:", placeholder="Escribe cama o nombre...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Tabla profesional
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"Se muestran {len(df_final)} aislamientos activos (Col. B a J).")
        else:
            st.info("No se encontraron aislamientos activos o el archivo está vacío.")

except Exception as e:
    st.error(f"Error al procesar: {e}")
    st.info("Asegúrate de que los encabezados reales estén en la segunda fila de tu Google Sheets.")
