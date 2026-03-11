import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", layout="wide")

# --- CONFIGURACIÓN DE URLS ---
SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"
DESTINATION_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{DESTINATION_SHEET_ID}/edit"

def enviar_a_google_sheets(df):
    """Escribe los datos procesados en la hoja de destino"""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Acceso anidado para [connections.gsheets]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            info = st.secrets["connections"]["gsheets"]
        else:
            info = st.secrets["connections.gsheets"]
            
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0) 
        
        worksheet.clear()
        # Convertimos todo a string para evitar conflictos de formato en la API
        df_envio = df.copy()
        for col in df_envio.columns:
            df_envio[col] = df_envio[col].astype(str)
            
        datos = [df_envio.columns.values.tolist()] + df_envio.values.tolist()
        worksheet.update('A1', datos)
        return True
    except Exception as e:
        st.error(f"Error al escribir en Google Sheets: {e}")
        return False

def cargar_aislamientos():
    # 1. Carga inicial
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10] # B a J
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_protector = df.columns[3] # Columna E
    col_inicio = df.columns[5]    # Columna G
    col_dias = df.columns[6]      # Columna H
    col_termino = df.columns[7]   # Columna I

    # 2. Rellenar celdas combinadas
    df[col_cama] = df[col_cama].replace(['nan', 'None', ''], np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(['nan', 'None', ''], np.nan).ffill()

    # --- 3. CÁLCULO DE FÓRMULA (COLUMNA H) ANTES DE CONSOLIDAR ---
    def calcular_formula(fecha_str):
        if str(fecha_str).strip() in ['nan', 'None', '', 'VACIO', 'NAN']: return 0
        try:
            # Limpiar fecha (tomar solo la parte de fecha si hay hora)
            limpia = str(fecha_str).split(' ')[0].strip()
            fecha_inicio = pd.to_datetime(limpia, dayfirst=True, errors='coerce')
            if pd.isna(fecha_inicio): return 0
            
            hoy = datetime.now()
            diferencia = (hoy - fecha_inicio).days + 1
            return diferencia if diferencia >= 0 else 0
        except:
            return 0

    # Sobrescribimos la columna H con el cálculo fresco
    df[col_dias] = df[col_inicio].apply(calcular_formula)

    # 4. Consolidación de filas
    def consolidar(group):
        res = group.iloc[0].copy()
        nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
        
        # Unir tipos de aislamiento
        tipos = [t for t in group[col_tipo].unique() if str(t).strip() not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        # Unir protectores
        prots = [p for p in group[col_protector].unique() if str(p).strip() not in nulos]
        res[col_protector] = " / ".join(prots) if prots else "VACIO"
        
        # Fecha de inicio y término (G e I)
        res[col_inicio] = next((i for i in group[col_inicio].values if str(i).strip() not in nulos), "VACIO")
        res[col_termino] = next((f for f in group[col_termino].values if str(f).strip() not in nulos), "VACIO")
        
        # Días (H): Tomamos el máximo del grupo calculado previamente
        res[col_dias] = group[col_dias].max()
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # 5. Filtro de Activos (Solo donde Columna I sea VACIO)
    df = df[df[col_termino] == "VACIO"]
    df = df.drop(columns=[col_termino])
    
    # Asegurar formato numérico para la vista previa
    df[col_dias] = pd.to_numeric(df[col_dias], errors='coerce').fillna(0).astype(int)
    
    return df[df[col_cama].notna()].sort_values(by=col_cama)

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos Activos")

try:
    df_base = cargar_aislamientos()
    col_prot_name = df_base.columns[3]
    
    # Filtro de búsqueda
    busqueda = st.text_input("🔍 Buscar por Cama o Nombre:")
    if busqueda:
        mask = df_base.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_base[mask]
    else:
        df_filtrado = df_base

    # --- MÉTRICAS ---
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="AISLAMIENTOS TOTALES", value=len(df_filtrado))
    with m2:
        # Conteo estricto de PROTECTORES en Columna E
        es_prot = df_filtrado[col_prot_name].str.contains("PROTECTOR", case=False, na=False)
        st.metric(label="PROTECTORES DETECTADOS", value=len(df_filtrado[es_prot]))

    st.divider()

    # --- BOTONES ---
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("🔄 Sincronizar Origen"):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("📤 Enviar Datos a Censo", type="primary"):
            with st.spinner("Actualizando Censo Público..."):
                if enviar_a_google_sheets(df_base):
                    st.success(f"✅ Censo actualizado con éxito ({datetime.now().strftime('%H:%M')})")
                    st.balloons()
    with c3:
        st.link_button("📂 Abrir Hoja de Google Sheets", DESTINATION_SHEET_URL)

    # --- TABLA ---
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No hay aislamientos activos para mostrar.")

except Exception as e:
    st.error(f"Error en el sistema: {e}")
