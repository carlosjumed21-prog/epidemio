import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", layout="wide")

# --- CONFIGURACIÓN DE URLS ---
SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"
DESTINATION_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{DESTINATION_SHEET_ID}/edit"

def enviar_a_google_sheets(df):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            service_account_info = st.secrets["connections"]["gsheets"]
        else:
            service_account_info = st.secrets["connections.gsheets"]
            
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0) 
        
        worksheet.clear()
        datos = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update('A1', datos)
        return True
    except Exception as e:
        st.error(f"Error de conexión/escritura: {e}")
        return False

def cargar_aislamientos():
    # 1. Carga cruda
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10] # Columnas B a J
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_protector = df.columns[3] # Columna E original
    col_termino = df.columns[7]

    # 2. Normalización básica
    df = df.astype(str).apply(lambda x: x.str.strip())
    nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
    
    df[col_cama] = df[col_cama].replace(nulos, np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(nulos, np.nan).ffill()

    # 3. Consolidación de filas
    def consolidar(group):
        res = group.iloc[0].copy()
        
        # Unir tipos de aislamiento
        tipos = [t for t in group[col_tipo].unique() if t not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        # Consolidar columna E (Protectores)
        prots = [p for p in group[col_protector].unique() if p not in nulos]
        res[col_protector] = " / ".join(prots) if prots else "VACIO"
        
        # Fecha término (Columna I)
        fechas = [f for f in group[col_termino].values if f not in nulos]
        res[col_termino] = fechas[0] if fechas else "VACIO"
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # 4. Filtro crítico: Solo activos (Columna I vacía)
    df = df[df[col_termino] == "VACIO"]
    df = df.drop(columns=[col_termino])
    df = df[df[col_cama].notna()].sort_values(by=col_cama)
    return df

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos Activos")

try:
    df_base = cargar_aislamientos()
    col_prot_name = df_base.columns[3] # Nombre de la columna E procesada
    
    # Buscador para filtrar la vista
    busqueda = st.text_input("🔍 Filtrar vista previa por Cama o Nombre:")
    if busqueda:
        mask = df_base.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_base[mask]
    else:
        df_filtrado = df_base

    # --- ENCABEZADOS DE CONTEO ---
    m1, m2 = st.columns(2)
    
    with m1:
        st.metric(label="AISLAMIENTOS TOTALES", value=len(df_filtrado))
    
    with m2:
        # CONTEO FILTRADO: Solo los que contienen la palabra "PROTECTOR" exactamente
        # Usamos .str.contains para manejar casos donde haya múltiples valores en la celda
        es_protector = df_filtrado[col_prot_name].str.contains("PROTECTOR", case=False, na=False)
        total_protectores = len(df_filtrado[es_protector])
        st.metric(label="PROTECTORES DETECTADOS", value=total_protectores)

    st.divider()

    # --- BOTONES DE ACCIÓN ---
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("🔄 Sincronizar Origen"):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("📤 Enviar Datos a Censo", type="primary"):
            with st.spinner("Actualizando Google Sheet..."):
                if enviar_a_google_sheets(df_base): # Enviamos siempre la base completa de activos
                    st.success("✅ Censo actualizado en la nube")
                    st.balloons()
    with c3:
        st.link_button("📂 Visualizar Censo Público", DESTINATION_SHEET_URL)

    # --- TABLA DE DATOS ---
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No se encontraron resultados con los filtros aplicados.")

except Exception as e:
    st.error(f"Error en el sistema: {e}")
