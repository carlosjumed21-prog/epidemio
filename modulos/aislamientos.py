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
    df = df.iloc[:, 1:10] # B a J
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_protector = df.columns[3] # Columna E
    col_inicio = df.columns[5]    # Columna G (Fecha Inicio)
    col_dias = df.columns[6]      # Columna H (Días de aislamiento)
    col_termino = df.columns[7]   # Columna I

    # 2. Normalización básica
    df[col_cama] = df[col_cama].replace(['nan', 'None', ''], np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(['nan', 'None', ''], np.nan).ffill()

    # 3. Consolidación
    def consolidar(group):
        res = group.iloc[0].copy()
        nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
        
        tipos = [t for t in group[col_tipo].unique() if str(t).strip() not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        prots = [p for p in group[col_protector].unique() if str(p).strip() not in nulos]
        res[col_protector] = " / ".join(prots) if prots else "VACIO"
        
        # Mantener fecha de inicio y término
        inicio_val = [i for i in group[col_inicio].values if str(i).strip() not in nulos]
        res[col_inicio] = inicio_val[0] if inicio_val else "VACIO"
        
        termino_val = [f for f in group[col_termino].values if str(f).strip() not in nulos]
        res[col_termino] = termino_val[0] if termino_val else "VACIO"
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # 4. Filtro Activos (Columna I vacía)
    df = df[df[col_termino] == "VACIO"]

    # --- 5. CÁLCULO DE DÍAS (COLUMNA H) ---
    def calcular_dias(fecha_str):
        try:
            # Intentar convertir la fecha de inicio (Columna G)
            fecha_inicio = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
            if pd.isna(fecha_inicio):
                return "Error Fecha"
            
            hoy = datetime.now()
            # Diferencia + 1 día
            dias = (hoy - fecha_inicio).days + 1
            return dias if dias >= 0 else 0
        except:
            return "N/A"

    df[col_dias] = df[col_inicio].apply(calcular_dias)

    # Limpieza final
    df = df.drop(columns=[col_termino])
    df = df[df[col_cama].notna()].sort_values(by=col_cama)
    return df

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos Activos")

try:
    df_base = cargar_aislamientos()
    col_prot_name = df_base.columns[3]
    
    # Filtro de búsqueda
    busqueda = st.text_input("🔍 Filtrar por Cama o Nombre:")
    if busqueda:
        mask = df_base.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_base[mask]
    else:
        df_filtrado = df_base

    # Métrica de encabezados
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="AISLAMIENTOS TOTALES", value=len(df_filtrado))
    with m2:
        es_protector = df_filtrado[col_prot_name].str.contains("PROTECTOR", case=False, na=False)
        st.metric(label="PROTECTORES DETECTADOS", value=len(df_filtrado[es_protector]))

    st.divider()

    # Botones
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("🔄 Sincronizar Origen"):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("📤 Enviar Datos a Censo", type="primary"):
            with st.spinner("Actualizando Censo..."):
                if enviar_a_google_sheets(df_base):
                    st.success("✅ Datos enviados con días calculados")
                    st.balloons()
    with c3:
        st.link_button("📂 Abrir Google Sheet Público", DESTINATION_SHEET_URL)

    # Vista Previa
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No hay datos para mostrar.")

except Exception as e:
    st.error(f"Error en el procesamiento: {e}")
