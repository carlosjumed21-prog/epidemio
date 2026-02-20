import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
# Asegúrate de que sea el link de "Publicar en la web" como CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

# Lista de columnas que queremos (en minúsculas para comparar fácil)
COLS_OBJETIVO = [
    "CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", 
    "MOTIVO DE SEGUIMIENTO", "FECHA DE INICIO", "DÍAS DE SEGUIMIENTO", 
    "FECHA DE TÉRMINO", "GUARDIA", "INGRESO/EGRESO"
]

def cargar_datos_robusto():
    # 1. Cargamos el CSV completo
    df = pd.read_csv(SHEET_URL, engine='python', encoding='utf-8')
    
    # 2. LIMPIEZA EXTREMA DE COLUMNAS
    # Quitamos espacios, saltos de línea (\n) y pasamos a mayúsculas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # Formateamos nuestra lista de objetivos igual
    cols_limpias = [c.upper() for c in COLS_OBJETIVO]
    
    # 3. VERIFICACIÓN DE COLUMNAS EXISTENTES
    # Solo seleccionamos las que realmente encontró en tu archivo
    cols_presentes = [c for c in cols_limpias if c in df.columns]
    
    if not cols_presentes:
        st.error("❌ No se encontraron las columnas. Columnas detectadas en tu archivo:")
        st.write(list(df.columns)) # Esto nos servirá para ver cómo las lee el sistema
        return pd.DataFrame()

    df = df[cols_presentes]
    
    # 4. FILTRO DE AISLAMIENTOS ACTIVOS (Donde INGRESO/EGRESO esté vacío)
    if "INGRESO/EGRESO" in df.columns:
        # Dejamos solo las filas donde la celda sea nula o esté vacía
        df = df[df["INGRESO/EGRESO"].isna() | (df["INGRESO/EGRESO"].astype(str).str.strip() == "")]
    
    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_datos_robusto()
        
        if not df_final.empty:
            # Buscador
            busqueda = st.text_input("🔍 Buscar paciente:", placeholder="Cama o Nombre...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Tabla amigable
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            st.success(f"Aislamientos activos: {len(df_final)}")
        else:
            st.info("Esperando datos o lista vacía.")

except Exception as e:
    st.error(f"Hubo un problema al leer el archivo: {e}")
