import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def cargar_datos_cronologia(spreadsheet_id, nombres_hojas):
    # Definir los alcances necesarios
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Cargar credenciales desde el archivo JSON (asegúrate de que esté en tu repo o usa Secrets de Streamlit)
    creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(spreadsheet_id)
    # ... resto de tu lógica para concatenar los DataFrames
