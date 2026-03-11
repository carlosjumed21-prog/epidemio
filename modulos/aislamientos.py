import streamlit as st
import pandas as pd
import numpy as np

# Configuración visual
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

st.title("🦠 Control de Aislamientos Activos")
st.markdown("---")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

def cargar_aislamientos_definitivo():
    # 1. Carga inicial
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte estricto de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas para evitar errores de tildes o espacios
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA TOTAL ---
    # Convertimos todo a string para uniformar y quitamos espacios invisibles
    df = df.astype(str).apply(lambda x: x.str.strip())
    
    # Definimos qué palabras el sistema debe tratar como "VACÍO"
    valores_nulos = ['nan', 'None', 'none', 'NULL', '', 'nan']

    # 3. LÓGICA DE UNIÓN DE FILAS (ffill para Cama y Nombre)
    # Reemplazamos los nulos de texto por NaN real de numpy para poder usar ffill()
    df[col_cama] = df[col_cama].replace(valores_nulos, np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(valores_nulos, np.nan).ffill()

    def consolidar_paciente(group):
        res = group.iloc[0].copy()
        # Combinar tipos de aislamiento únicos que no sean nulos
        tipos = [t for t in group[col_tipo].unique() if t not in valores_nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        # Para el resto de columnas, buscamos el primer dato real
        for col in group.columns:
            if col not in [col_tipo, col_cama, col_nombre]:
                validos = [v for v in group[col].values if v not in valores_nulos]
                res[col] = validos[0] if validos else "None"
        return res

    # Agrupamos por Cama y Nombre
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)

    # --- 4. EL FILTRO SOLICITADO (CONDICIÓN COLUMNA I) ---
    # Solo mostramos los que tienen "None" (estaban vacíos en el Excel)
    if col_termino in df.columns:
        # Filtramos para quedarnos SOLO con los que NO tienen fecha de término
        df = df[df[col_termino] == "None"]
        # Una vez filtrado, quitamos la columna de la vista ya que todos son "None"
        df = df.drop(columns=[col_termino])

    # Limpieza final y orden por cama
    df = df[df[col_cama] != "nan"]
    df = df.sort_values(by=col_cama)

    return df

# --- INTERFAZ STREAMLIT ---
try:
    with st.sidebar:
        st.header("⚙️ Controles")
        if st.button("🔄 Sincronizar Excel", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    df_final = cargar_aislamientos_definitivo()
    
    if not df_final.empty:
        # Buscador
        busqueda = st.text_input("🔍 Buscar por Cama o Nombre de Paciente:", placeholder="Escriba aquí...")
        
        if busqueda:
            mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_final = df_final[mask]

        # Estilo de la tabla
        st.dataframe(
            df_final, 
            use_container_width=True, 
            hide_index=True
        )
        
        st.success(f"📋 **{len(df_final)}** Pacientes con Aislamiento Activo (Sin fecha de término registrada).")
    else:
        st.info("✅ Actualmente no hay pacientes aislados (Todos los registros tienen una Fecha de Término).")

except Exception as e:
    st.error(f"❌ Error en el procesamiento: {e}")
