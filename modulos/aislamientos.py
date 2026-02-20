import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_aislamientos_posicional():
    # 1. Cargamos el CSV sin encabezados primero para limpiar basura
    df = pd.read_csv(SHEET_URL, header=None, engine='python', encoding='utf-8')
    
    # 2. Buscamos la fila donde realmente empiezan los datos.
    # Normalmente, si la fila 1 es el título, la fila 2 (índice 1) son los encabezados.
    # Forzamos a que la fila 2 sea el encabezado.
    df.columns = df.iloc[1] # Tomamos la fila 2 como nombres de columna
    df = df.iloc[2:]        # Los datos reales empiezan en la fila 3
    
    # 3. Recortamos estrictamente de la Columna B (1) a la J (9)
    # iloc[:, 1:10] toma las columnas en las posiciones 1,2,3,4,5,6,7,8,9
    df = df.iloc[:, 1:10]
    
    # Limpiamos nombres de columnas (quitar espacios, saltos de línea y pasar a Mayúsculas)
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # 4. Filtro de "Sombreado Verde" (Columna J / INGRESO/EGRESO vacía)
    # Usamos el nombre de la última columna disponible en el recorte
    col_final = df.columns[-1]
    
    # Convertimos a string y limpiamos para validar vacíos
    df = df[df[col_final].isna() | (df[col_final].astype(str).str.strip() == "")]
    
    # Eliminar filas donde el nombre (Columna D original, ahora índice 2) esté vacío
    # para no mostrar filas vacías del final del Excel
    col_nombre = df.columns[2]
    df = df.dropna(subset=[col_nombre])
    
    return df

try:
    with st.container(border=True):
        if st.button("🔄 Sincronizar con Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        df_final = cargar_aislamientos_posicional()
        
        if not df_final.empty:
            # Buscador
            busqueda = st.text_input("🔍 Buscar en la lista:", placeholder="Cama, registro, nombre...")
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Mostrar tabla
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"✅ Se muestran {len(df_final)} pacientes en aislamiento activo.")
        else:
            st.info("No hay pacientes detectados en el rango seleccionado.")

except Exception as e:
    st.error(f"Error en la lectura: {e}")
    st.info("Asegúrate de que la Columna B sea 'CAMA' y la Columna J sea 'INGRESO/EGRESO'.")
