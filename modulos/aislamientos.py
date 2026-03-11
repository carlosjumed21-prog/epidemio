import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Control de Aislamientos", layout="wide")
st.title("🦠 Control de Aislamientos Activos")

# --- CONFIGURACIÓN DE URLS ---
SHEET_URL_READ = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
DESTINATION_SHEET_ID = "1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A"

def enviar_a_google_sheets(df):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # AJUSTE AQUÍ: Usamos la clave exacta de tus Secrets "connections.gsheets"
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
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10]
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_termino = df.columns[7]

    df = df.astype(str).apply(lambda x: x.str.strip())
    nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
    
    df[col_cama] = df[col_cama].replace(nulos, np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(nulos, np.nan).ffill()

    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = [t for t in group[col_tipo].unique() if t not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        fechas = [f for f in group[col_termino].values if f not in nulos]
        res[col_termino] = fechas[0] if fechas else "VACIO"
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)
    df = df[df[col_termino] == "VACIO"]
    df = df.drop(columns=[col_termino])
    df = df[df[col_cama].notna()].sort_values(by=col_cama)
    
    return df

# --- INTERFAZ ---
try:
    if st.button("🔄 Sincronizar origen"):
        st.cache_data.clear()
        st.rerun()

    df_final = cargar_aislamientos()

    if not df_final.empty:
        if st.button("📤 Actualizar Censo Público", type="primary"):
            with st.spinner("Subiendo datos al Google Sheet de destino..."):
                if enviar_a_google_sheets(df_final):
                    st.success("✅ Censo actualizado con éxito.")
                    st.balloons()

        st.divider()
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No hay aislamientos activos detectados.")

except Exception as e:
    st.error(f"Error general: {e}")
