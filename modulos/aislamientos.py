import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", layout="wide")

# --- CONFIGURACIÓN DE URLS ---
# Hoja de origen (Lectura CSV Público)
SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
# Hoja de destino (Escritura via API)
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"
DESTINATION_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{DESTINATION_SHEET_ID}/edit"

def enviar_a_google_sheets(df):
    """Función para conectar con la API y escribir los datos"""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Acceso correcto al formato [connections.gsheets]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            service_account_info = st.secrets["connections"]["gsheets"]
        else:
            service_account_info = st.secrets["connections.gsheets"]
            
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrir el documento y la primera hoja
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0) 
        
        # Limpiar y actualizar
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
    
    # 2. Recorte B a J (9 columnas)
    df = df.iloc[:, 1:10]
    
    # 3. Limpieza de nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_termino = df.columns[7]

    # 4. Normalización
    df = df.astype(str).apply(lambda x: x.str.strip())
    nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
    
    df[col_cama] = df[col_cama].replace(nulos, np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(nulos, np.nan).ffill()

    # 5. Consolidación
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = [t for t in group[col_tipo].unique() if t not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        fechas = [f for f in group[col_termino].values if f not in nulos]
        res[col_termino] = fechas[0] if fechas else "VACIO"
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)

    # 6. Filtrar solo los activos (Columna I vacía)
    df = df[df[col_termino] == "VACIO"]
    df = df.drop(columns=[col_termino])
    df = df[df[col_cama].notna()].sort_values(by=col_cama)
    
    return df

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos Activos")

try:
    df_final = cargar_aislamientos()
    total_aislados = len(df_final)

    # Encabezado con métrica principal
    st.metric(label="Aislamientos Totales Detectados", value=total_aislados)

    # Fila de botones de acción
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("🔄 Sincronizar Origen"):
            st.cache_data.clear()
            st.rerun()

    with col2:
        if st.button("📤 Enviar Datos a Censo", type="primary"):
            with st.spinner("Actualizando Google Sheet..."):
                if enviar_a_google_sheets(df_final):
                    st.success("✅ Censo actualizado")
                    st.balloons()

    with col3:
        st.link_button("📂 Visualizar Censo (Google Sheets)", DESTINATION_SHEET_URL)

    st.divider()

    # Buscador y Tabla
    if not df_final.empty:
        busqueda = st.text_input("🔍 Buscar por Cama o Nombre:")
        if busqueda:
            mask = df_final.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_mostrar = df_final[mask]
        else:
            df_mostrar = df_final

        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No se encontraron aislamientos activos.")

except Exception as e:
    st.error(f"Error general en la aplicación: {e}")
