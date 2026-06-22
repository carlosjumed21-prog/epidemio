import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

def mostrar_cronologia():
    st.title("⏳ Línea Cronológica Clínica")
    
    # 1. Configuración de credenciales usando el mismo método que tu otro archivo
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # 2. Conexión al Sheet de cronología
        sheet_id = "18ulkVdzPk8OZiswHyIZlI0-lcVOrhQ2LjN2_pDZj_oI"
        sheet = client.open_by_key(sheet_id).sheet1 
        
        # 3. Procesamiento de datos
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Validación de formato de fecha
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df = df.dropna(subset=['Fecha']).sort_values('Fecha')
        
        # 4. Gráfico de línea de tiempo
        if not df.empty:
            fig = px.timeline(
                df, 
                x_start="Fecha", 
                x_end="Fecha", 
                y="Dispositivos Invasivos", 
                color="Origen",
                hover_data=["Procedimientos", "Cultivos / Fiebre / Antibióticos"],
                title="Evolución de Dispositivos e Infecciones"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No hay datos válidos para graficar.")
        
    except Exception as e:
        st.error(f"⚠️ Error al conectar o procesar la cronología: {e}")

if __name__ == "__main__":
    mostrar_cronologia()
