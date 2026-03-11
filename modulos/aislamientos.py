import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

def cargar_aislamientos_definitivo():
    # 1. Carga inicial saltando el título (Fila 1 del Excel)
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte estricto de Columna B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    
    # Limpiar encabezados
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO"

    # --- LIMPIEZA CRÍTICA DE "NONE" Y ESPACIOS ---
    # Convertimos todo a string y reemplazamos variantes de vacío por NaN real
    df = df.apply(lambda x: x.astype(str).str.strip())
    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)

    # 3. LÓGICA DE UNIÓN DE FILAS DOBLES
    # Rellenamos Cama y Nombre hacia abajo para agrupar filas del mismo paciente
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    def consolidar_paciente(group):
        # Tomamos la primera fila como base
        res = group.iloc[0].copy()
        # Combinamos los Tipos de Aislamiento únicos encontrados en el grupo
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        
        # Para el resto de columnas, buscamos el valor que sí tenga datos
        for col in group.columns:
            if col not in [col_tipo, col_cama, col_nombre]:
                val_real = group[col].dropna()
                res[col] = val_real.iloc[0] if not val_real.empty else np.nan
        return res

    # Aplicamos la consolidación
    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)

    # 4. FILTRO DE AISLAMIENTOS VIGENTES (CAMBIO CLAVE)
    # Si la columna tiene un dato (fecha), el aislamiento terminó. 
    # Si es NaN (estaba vacío o decía "None"), el aislamiento sigue ACTIVO.
    if col_termino in df.columns:
        # Solo mantenemos las filas donde FECHA DE TÉRMINO es nulo
        df = df[df[col_termino].isna()]
        # Opcional: Eliminamos la columna de término para la vista final ya que todas estarán vacías
        df = df.drop(columns=[col_termino])

    # Limpieza final de filas vacías y ordenamiento
    df = df[df[col_cama].notna()]
    df = df.sort_values(by=col_cama)

    return df

# --- INTERFAZ DE USUARIO ---
try:
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Sincronizar Censo", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        df_final = cargar_aislamientos_definitivo()
        
        if not df_final.empty:
            with col1:
                busqueda = st.text_input("🔍 Buscar por Cama o Nombre:", placeholder="Ej. 7305...")
            
            if busqueda:
                mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                df_final = df_final[mask]

            # Mostrar tabla
            st.dataframe(
                df_final, 
                use_container_width=True, 
                hide_index=True
            )
            
            st.success(f"📋 Se encontraron **{len(df_final)}** aislamientos activos actualmente.")
        else:
            st.info("✅ No hay aislamientos activos registrados en este momento.")

except Exception as e:
    st.error(f"Hubo un problema al procesar los datos: {e}")
