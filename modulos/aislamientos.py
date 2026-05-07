import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos | Epidemiología", layout="wide")

# --- CONFIGURACIÓN DE URLS ---
SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"
DESTINATION_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{DESTINATION_SHEET_ID}/edit"

def enviar_a_google_sheets(df):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = st.secrets["connections"]["gsheets"] if "connections" in st.secrets else st.secrets["connections.gsheets"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0) 
        worksheet.clear()
        df_envio = df.copy()
        for col in df_envio.columns:
            df_envio[col] = df_envio[col].astype(str).replace(['nan', 'None', 'NaT'], '')
        datos = [df_envio.columns.values.tolist()] + df_envio.values.tolist()
        worksheet.update('A1', datos)
        return True
    except Exception as e:
        st.error(f"Error al escribir en Google Sheets: {e}")
        return False

def cargar_aislamientos():
    # 1. Carga de datos
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10] 
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]      # B
    col_nombre = df.columns[1]    # C
    col_tipo = df.columns[2]      # D
    col_protector = df.columns[3]  # E
    col_inicio = df.columns[5]     # G
    col_dias = df.columns[6]       # H
    col_termino = df.columns[7]    # I

    # --- 2. NORMALIZACIÓN Y RELLENO ---
    nulos_invalidos = ['NAN', 'NONE', 'none', '', 'NULL', ' ', '-', 'VACIO', 'ACTIVO']
    df = df.replace(nulos_invalidos, np.nan)

    # RELLENO CRÍTICO: Aseguramos que las filas "huérfanas" (como la 160) hereden cama y nombre
    df[col_cama] = df[col_cama].ffill().astype(str).str.strip().str.upper()
    df[col_nombre] = df[col_nombre].ffill().astype(str).str.strip().str.upper()

    # 3. Cálculo de Días (por cada fila individual)
    def calcular_dias_reales(fecha_str):
        try:
            limpia = str(fecha_str).strip()[:10]
            fecha_inicio = pd.to_datetime(limpia, dayfirst=True, errors='coerce')
            if pd.isna(fecha_inicio): return 0
            return (datetime.now() - fecha_inicio).days + 1
        except: return 0

    df[col_dias] = df[col_inicio].apply(calcular_dias_reales)

    # --- 4. FILTRO DE AISLAMIENTOS ACTIVOS (Lógica de Consolidación) ---
    def consolidar_solo_activos(group):
        # Nuestro filtro fundamental: Solo nos importan las filas SIN fecha de término
        filas_vivas = group[group[col_termino].isna()]
        
        # Si el paciente tiene 2 filas y AMBAS tienen fecha de término, el paciente ya no está aislado
        if filas_vivas.empty:
            return None
            
        # Si al menos una fila está vacía (activa), el paciente sigue en aislamiento
        res = filas_vivas.iloc[0].copy()
        
        # Unimos los tipos y protectores SOLO de las filas que siguen activas
        tipos = filas_vivas[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else "SIN ESPECIFICAR"
        
        prots = filas_vivas[col_protector].dropna().unique()
        res[col_protector] = " / ".join(prots) if len(prots) > 0 else "VACÍO"
        
        # Días de aislamiento (máximo entre las filas activas)
        res[col_dias] = filas_vivas[col_dias].max()
        
        return res

    # Agrupamos por cama y nombre para procesar los bloques
    df_final = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_solo_activos)
    
    # Eliminamos pacientes que resultaron en None (porque todos sus aislamientos terminaron)
    df_final = df_final.dropna(subset=[col_cama]).reset_index(drop=True)

    # Quitamos la columna de término para la vista limpia
    if col_termino in df_final.columns:
        df_final = df_final.drop(columns=[col_termino])

    return df_final.sort_values(by=col_cama)

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos Activos")
st.caption("CMN '20 de Noviembre' | Vigilancia Epidemiológica")

try:
    df_base = cargar_aislamientos()
    
    # Buscador
    busqueda = st.text_input("🔍 Buscar por Cama o Nombre:")
    if busqueda:
        mask = df_base.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_base[mask]
    else:
        df_filtrado = df_base

    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="TOTAL PACIENTES", value=len(df_filtrado))
    with m2:
        es_prot = df_filtrado.iloc[:, 3].astype(str).str.contains("PROTECTOR", case=False, na=False)
        st.metric(label="AISL. PROTECTORES", value=len(df_filtrado[es_prot]))
    with m3:
        promedio = int(df_filtrado.iloc[:, 6].mean()) if not df_filtrado.empty else 0
        st.metric(label="PROM. DÍAS", value=f"{promedio} d")

    st.divider()

    # --- ACCIONES ---
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("📤 Enviar a Censo", type="primary", use_container_width=True):
            if enviar_a_google_sheets(df_base):
                st.success("✅ Sincronizado")
                st.balloons()
    with c3:
        st.link_button("📂 Abrir Sheets", DESTINATION_SHEET_URL, use_container_width=True)

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en el sistema: {e}")
