import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

def cargar_aislamientos_definitivo():
    # 1. Carga inicial
    df = pd.read_csv(SHEET_URL, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de columnas (B a J)
    df = df.iloc[:, 1:10]
    
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = "CAMA"
    col_nombre = "NOMBRE"
    col_tipo = "TIPO DE AISLAMIENTO"
    col_termino = "FECHA DE TÉRMINO" # Asegúrate que en tu Excel se llame EXACTAMENTE así

    # --- LIMPIEZA PROFUNDA ---
    # Convertimos todo a string para uniformar
    df = df.astype(str)
    # Quitamos espacios en blanco al inicio y final de cada celda
    df = df.apply(lambda x: x.str.strip())
    
    # Definimos qué palabras significan "SIN FECHA" (Aislamiento Activo)
    valores_vacios = ['nan', 'None', 'none', '', 'nan', 'NAN', 'NULL']

    # 3. LÓGICA DE UNIÓN DE FILAS
    df[col_cama] = df[col_cama].replace(valores_vacios, np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(valores_vacios, np.nan).ffill()

    def consolidar_paciente(group):
        res = group.iloc[0].copy()
        # Consolidar tipos de aislamiento
        tipos = [t for t in group[col_tipo].unique() if t not in valores_vacios]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        # Para el resto de columnas (incluida FECHA DE TÉRMINO)
        for col in group.columns:
            if col not in [col_tipo, col_cama, col_nombre]:
                # Buscamos el primer valor que NO sea uno de nuestros "valores vacíos"
                validos = [v for v in group[col].values if v not in valores_vacios]
                res[col] = validos[0] if validos else "None"
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)

    # --- 4. FILTRO DEFINITIVO (LA CONDICIÓN QUE SOLICITASTE) ---
    # Queremos SOLO los que NO tengan fecha de término.
    # Es decir, que el valor sea "None" (nuestra marca de vacío).
    if col_termino in df.columns:
        # Filtramos: Solo filas donde la fecha es "None"
        df = df[df[col_termino] == "None"]
        
        # Una vez filtrados, borramos la columna para que no estorbe
        df = df.drop(columns=[col_termino])

    # Limpiar filas donde la cama sea inválida
    df = df[~df[col_cama].isin(valores_vacios)]
    df = df.sort_values(by=col_cama)

    return df

# --- INTERFAZ STREAMLIT ---
st.title("🦠 Control de Aislamientos Activos")

try:
    if st.button("🔄 Sincronizar Datos"):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_aislamientos_definitivo()
    
    if not df_final.empty:
        busqueda = st.text_input("🔍 Buscar por Cama o Nombre:")
        if busqueda:
            mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_final = df_final[mask]

        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.success(f"📋 {len(df_final)} Pacientes en aislamiento activo.")
    else:
        st.warning("✅ No hay aislamientos activos (Todos los pacientes tienen fecha de término o la lista está vacía).")

except Exception as e:
    st.error(f"Error: {e}")
