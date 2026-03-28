import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control de Aislamientos", layout="wide")

SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"
DESTINATION_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{DESTINATION_SHEET_ID}/edit"

def enviar_a_google_sheets(df):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            info = st.secrets["connections"]["gsheets"]
        else:
            info = st.secrets["connections.gsheets"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0)
        worksheet.clear()
        df_envio = df.copy()
        for col in df_envio.columns:
            df_envio[col] = df_envio[col].astype(str).replace(['nan', 'None', 'NaT', 'ACTIVO'], '')
        datos = [df_envio.columns.values.tolist()] + df_envio.values.tolist()
        worksheet.update('A1', datos)
        return True
    except Exception as e:
        st.error(f"Error en Google Sheets: {e}")
        return False

def cargar_aislamientos():
    # 1. Carga inicial
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10] # B a J
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_inicio = df.columns[5]
    col_dias = df.columns[6]
    col_termino = df.columns[7]

    # --- 2. LIMPIEZA INICIAL DE FILAS VACÍAS ---
    # Si la fila no tiene ni cama ni nombre ni tipo, la borramos antes de procesar
    df = df.dropna(subset=[col_cama, col_nombre, col_tipo], how='all')

    # --- 3. NORMALIZACIÓN DE TEXTO ---
    # Eliminamos espacios accidentales que duplican registros
    for col in [col_cama, col_nombre]:
        df[col] = df[col].astype(str).str.strip().str.upper()
    
    # Estandarizar nulos
    nulos = ['NAN', 'NONE', '', 'NULL', ' ', '-', 'VACIO']
    df = df.replace(nulos, np.nan)

    # 4. Rellenar celdas combinadas
    df[col_cama] = df[col_cama].ffill()
    df[col_nombre] = df[col_nombre].ffill()

    # 5. Cálculo de días
    def calc_dias(f):
        if pd.isna(f): return 0
        try:
            inicio = pd.to_datetime(str(f).strip()[:10], dayfirst=True, errors='coerce')
            if pd.isna(inicio): return 0
            d = (datetime.now() - inicio).days + 1
            return d if d >= 0 else 0
        except: return 0

    df[col_dias] = df[col_inicio].apply(calc_dias)

    # --- 6. CONSOLIDACIÓN POR PACIENTE ---
    def consolidar(group):
        # Si un grupo no tiene ninguna fila con "Tipo de Aislamiento", lo ignoramos
        if group[col_tipo].dropna().empty:
            return None
            
        res = group.iloc[0].copy()
        res[col_tipo] = " / ".join(group[col_tipo].dropna().unique())
        
        # Un paciente está ACTIVO si tiene al menos una fila donde el término sea NaN
        esta_activo = group[col_termino].isna().any()
        res[col_termino] = "ACTIVO" if esta_activo else "FINALIZADO"
        
        res[col_dias] = group[col_dias].max()
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)
    
    # Eliminar los "None" que devolvió la consolidación
    df = df.dropna(subset=[col_cama])

    # --- 7. FILTRO FINAL ---
    df_final = df[df[col_termino] == "ACTIVO"].copy()
    df_final = df_final.drop(columns=[col_termino])
    df_final[col_dias] = pd.to_numeric(df_final[col_dias], errors='coerce').fillna(0).astype(int)
    
    return df_final.sort_values(by=col_cama)

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos Activos")

try:
    df_base = cargar_aislamientos()
    
    busqueda = st.text_input("🔍 Buscar por Cama o Nombre:")
    df_filtrado = df_base[df_base.apply(lambda r: r.astype(str).str.contains(busqueda, case=False).any(), axis=1)] if busqueda else df_base

    c1, c2 = st.columns(2)
    c1.metric("TOTAL AISLAMIENTOS", len(df_filtrado))
    
    # BOTONES
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Refrescar Datos"):
            st.cache_data.clear()
            st.rerun()
    with col_btn2:
        if st.button("📤 Sincronizar Censo", type="primary"):
            if enviar_a_google_sheets(df_base):
                st.success("✅ Actualizado")
                st.balloons()

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
