import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import os
from google.oauth2.service_account import Credentials

def mostrar_cronologia():
    st.title("⏳ Línea Cronológica Clínica")
    
    # Ruta absoluta al archivo credenciales.json en la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_credenciales = os.path.join(base_dir, 'credenciales.json')
    
    # 1. Configuración de credenciales
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    
    try:
        # Carga usando la ruta calculada
        creds = Credentials.from_service_account_file(ruta_credenciales, scopes=scope)
        client = gspread.authorize(creds)
        
        # 2. Conexión al Sheet
        sheet_id = "18ulkVdzPk8OZiswHyIZlI0-lcVOrhQ2LjN2_pDZj_oI"
        sheet = client.open_by_key(sheet_id).sheet1 
        
        # 3. Procesamiento de datos
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Asegurar formato de fecha
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        # 4. Gráfico de línea de tiempo
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
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
        st.write("Verifica que el archivo `credenciales.json` esté en la raíz del proyecto.")

if __name__ == "__main__":
    mostrar_cronologia()
