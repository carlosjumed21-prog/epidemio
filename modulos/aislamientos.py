import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
# Asegúrate de usar el link de "Publicar en la web" como CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_estricto():
    # 1. Cargamos el CSV saltando solo la primera fila (Título)
    # header=0 en este nuevo contexto será la fila 2 del Excel original
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Seleccionamos de la columna B a la J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # 3. Los pacientes empiezan en la fila 4 del Excel original.
    # Como ya saltamos 1 fila al cargar y la siguiente se usó de encabezado,
    # debemos saltar una fila más de datos para llegar a la 4.
    df = df.iloc[1:].reset_index(drop=True)
    
    # 4. Limpieza de nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # 5. Filtro de Aislamientos Activos (Columna J / INGRESO/EGRESO vacía)
    # Es la última columna de nuestro recorte (índice 8)
    col_egreso = df.columns[-1]
    
    # Normalizamos vacíos para que el filtro sea efectivo
    df[col_egreso] = df[col_egreso].astype(str).replace(['nan', 'None', 'NULL', '', ' '], pd.NA)
    
    # Filtramos: Solo se quedan los que tienen la celda de egreso VACÍA
    df_activos = df[df[col_egreso].isna()].copy()
    
    # Limpieza: Quitar filas donde el NOMBRE esté vacío para evitar basura del final
    # (El nombre es la 3ra columna del recorte: B, C, D -> índice 2)
    if len(df_activos.columns) > 2:
        col_nombre = df_activos.columns[2]
        df_activos = df_activos[df_activos[col_nombre].notna() & (df_activos[col_nombre].astype(str).str.strip() != "")]
    
    return df_activos

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_estricto()
        
        if not df_final.empty:
            # Buscador por cama o nombre
            busqueda = st.text_input("🔍 Buscar paciente:", placeholder="Ej. 4210 o apellido...")
            
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Visualización de la tabla
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"✅ {len(df_final)} pacientes en aislamiento activo detectados.")
        else:
            st.warning("⚠️ No se detectaron pacientes activos.")
            st.info("Nota: Los pacientes que ya tienen registro en la columna 'INGRESO/EGRESO' no se muestran aquí.")

except Exception as e:
    st.error(f"Error al procesar la lista: {e}")
    st.info("Verifica que el archivo en Sheets mantenga el formato: Fila 2 (Encabezados) y Fila 4 (Pacientes).")
