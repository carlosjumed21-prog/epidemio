import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def cargar_datos_cronologia(spreadsheet_id, nombres_hojas):
    # Configuración de credenciales (ajusta según tu configuración actual)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id)
    
    lista_df = []
    
    for nombre in nombres_hojas:
        ws = sheet.worksheet(nombre)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        df['Paciente'] = nombre  # Etiqueta para diferenciar los 3 pacientes
        lista_df.append(df)
        
    return pd.concat(lista_df)

def generar_timeline(df):
    # Aseguramos que la columna Fecha sea datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Creamos el gráfico de línea de tiempo
    fig = px.timeline(
        df, 
        x_start="Fecha", 
        x_end="Fecha", # Ajusta si tienes duración de eventos
        y="Paciente", 
        color="Procedimientos", # O la columna que prefieras resaltar
        hover_data=['Dispositivos Invasivos', 'Cultivos / Fiebre / Antibióticos'],
        title="Línea Cronológica de Eventos Clínicos"
    )
    
    fig.update_yaxes(autorange="reversed") 
    return fig

# En tu main.py, llamarás a estas funciones
