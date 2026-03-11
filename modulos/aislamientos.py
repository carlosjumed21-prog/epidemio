import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", layout="wide")

# --- CONFIGURACIÓN DE URLS ---
# Hoja de origen (Lectura CSV Público)
SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
# Hoja de destino (Escritura via API)
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"
DESTINATION_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{DESTINATION_SHEET_ID}/edit"

def enviar_a_google_sheets(df):
    """Función para conectar con la API y escribir los datos calculados"""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Manejo de secretos para formato [connections.gsheets]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            service_account_info = st.secrets["connections"]["gsheets"]
        else:
            service_account_info = st.secrets["connections.gsheets"]
            
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0) 
        
        # 1. Limpiar la hoja de destino por completo
        worksheet.clear()
        
        # 2. Preparar el DataFrame: Convertir todo a string para evitar errores de JSON
        df_envio = df.copy()
        for col in df_envio.columns:
            df_envio[col] = df_envio[col].astype(str)
            
        datos = [df_envio.columns.values.tolist()] + df_envio.values.tolist()
        
        # 3. Escribir nuevos datos
        worksheet.update('A1', datos)
        return True
    except Exception as e:
        st.error(f"Error de conexión/escritura: {e}")
        return False

def cargar_aislamientos():
    # 1. Carga cruda desde el CSV publicado
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    
    # 2. Recorte de columnas B a J (Índices 1 al 9)
    df = df.iloc[:, 1:10]
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Mapeo de columnas por posición
    col_cama = df.columns[0]     # Col B
    col_nombre = df.columns[1]   # Col C
    col_tipo = df.columns[2]     # Col D
    col_protector = df.columns[3] # Col E
    col_inicio = df.columns[5]    # Col G
    col_dias = df.columns[6]      # Col H (A modificar)
    col_termino = df.columns[7]   # Col I

    # 3. Rellenar celdas combinadas (Cama y Nombre)
    df[col_cama] = df[col_cama].replace(['nan', 'None', ''], np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(['nan', 'None', ''], np.nan).ffill()

    # 4. Consolidación de filas para pacientes con múltiples aislamientos
    def consolidar(group):
        res = group.iloc[0].copy()
        nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
        
        # Unir tipos de aislamiento
        tipos = [t for t in group[col_tipo].unique() if str(t).strip() not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        # Unir protectores (Columna E)
        prots = [p for p in group[col_protector].unique() if str(p).strip() not in nulos]
        res[col_protector] = " / ".join(prots) if prots else "VACIO"
        
        # Obtener fecha de inicio y término
        res[col_inicio] = next((i for i in group[col_inicio].values if str(i).strip() not in nulos), "VACIO")
        res[col_termino] = next((f for f in group[col_termino].values if str(f).strip() not in nulos), "VACIO")
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # 5. Filtrar solo los activos (Donde Columna I esté vacía/VACIO)
    df = df[df[col_termino] == "VACIO"]

    # --- 6. CÁLCULO DINÁMICO DE DÍAS (COLUMNA H) ---
    def calcular_dias(fecha_str):
        if str(fecha_str).strip() in ['VACIO', 'nan', '']: return "0"
        try:
            # Limpiar el string de fecha y convertir
            fecha_limpia = str(fecha_str).split(' ')[0]
            fecha_inicio = pd.to_datetime(fecha_limpia, dayfirst=True, errors='coerce')
            
            if pd.isna(fecha_inicio): return "Error Fecha"
            
            hoy = datetime.now()
            # Fórmula: (Hoy - Inicio) + 1 día
            dias = (hoy - fecha_inicio).days + 1
            return str(dias) if dias >= 0 else "0"
        except:
            return "0"

    df[col_dias] = df[col_inicio].apply(calcular_dias)

    # 7. Limpieza final para la vista
    df = df.drop(columns=[col_termino])
    df = df[df[col_cama].notna()].sort_values(by=col_cama)
    
    return df

# --- INTERFAZ STREAMLIT ---
st.title("🦠 Control de Aislamientos Activos")

try:
    df_base = cargar_aislamientos()
    col_prot_name = df_base.columns[3] # Referencia a la columna de Protectores
    
    # Buscador dinámico
    busqueda = st.text_input("🔍 Buscar por Cama o Nombre (Filtra la tabla y estadísticas):")
    if busqueda:
        mask = df_base.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_base[mask]
    else:
        df_filtrado = df_base

    # --- MÉTRICAS DE ENCABEZADO ---
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="AISLAMIENTOS TOTALES", value=len(df_filtrado))
    with m2:
        # Contar solo si la Columna E contiene la palabra "PROTECTOR"
        es_protector = df_filtrado[col_prot_name].str.contains("PROTECTOR", case=False, na=False)
        st.metric(label="PROTECTORES DETECTADOS", value=len(df_filtrado[es_protector]))

    st.divider()

    # --- BOTONES DE ACCIÓN ---
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        if st.button("🔄 Sincronizar Origen"):
            st.cache_data.clear()
            st.rerun()

    with c2:
        if st.button("📤 Enviar Datos a Censo", type="primary"):
            with st.spinner("Procesando y enviando al Google Sheet..."):
                # Enviamos df_base (todos los activos) para asegurar el vaciado completo
                if enviar_a_google_sheets(df_base):
                    st.success("✅ Censo actualizado con días calculados.")
                    st.balloons()

    with c3:
        st.link_button("📂 Visualizar Censo (Google Sheets)", DESTINATION_SHEET_URL)

    # --- TABLA DE DATOS ---
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No se encontraron pacientes activos con los criterios actuales.")

except Exception as e:
    st.error(f"Error crítico en la aplicación: {e}")
