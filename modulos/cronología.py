import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def mostrar_cronologia():
    st.title("⏳ Línea Cronológica Clínica")
    
    # 1. Configuración de credenciales (asegúrate de que el archivo .json esté en la raíz)
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('credenciales.json', scope)
        client = gspread.authorize(creds)
        
        # 2. Conexión al Sheet
        sheet_id = "18ulkVdzPk8OZiswHyIZlI0-lcVOrhQ2LjN2_pDZj_oI"
        sheet = client.open_by_key(sheet_id).sheet1 
        
        # 3. Procesamiento de datos
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Asegurar formato de fecha (ajusta 'Fecha' al nombre exacto de tu columna A)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        # 4. Filtro por paciente (opcional, si tienes una columna para ello)
        # paciente = st.selectbox("Seleccionar paciente:", df['Nombre'].unique())
        # df_filtrado = df[df['Nombre'] == paciente]
        
        # 5. Gráfico de línea de tiempo
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
        st.error(f"No se pudo cargar la hoja: {e}")
        st.write("Verifica que tu `credenciales.json` tenga acceso al archivo.")

# Llamada a la función principal
if __name__ == "__main__":
    mostrar_cronologia()
