import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE CONEXIÓN ---
def actualizar_hoja_google(df):
    try:
        # 1. Definir el alcance (Scope)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 2. Cargar tus credenciales (El archivo JSON que descargas de Google Cloud)
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        # 3. Abrir la hoja por su ID
        # Tu ID es: 1vSD2cPIZRxh-b5NyaVARl3Ioa5B0KeIqdLhtDkQ1nldthyu6TIT4KrWG5NWSNiUeY0XWiL1icDafU0P
        SHEET_ID = "1vSD2cPIZRxh-b5NyaVARl3Ioa5B0KeIqdLhtDkQ1nldthyu6TIT4KrWG5NWSNiUeY0XWiL1icDafU0P"
        hoja_documento = client.open_by_key(SHEET_ID)
        hoja = hoja_documento.get_worksheet(0) # Selecciona la primera pestaña

        # 4. Limpiar la hoja y escribir los nuevos datos
        hoja.clear()
        datos = [df.columns.values.tolist()] + df.values.tolist()
        hoja.update('A1', datos)

        # 5. AUTOAJUSTE DE CELDAS (Formato)
        # Esto hace que las columnas se ajusten al ancho del texto automáticamente
        hoja.columns_auto_resize(0, len(df.columns))
        
        # Formato adicional: Encabezados en negrita
        hoja.format("A1:Z1", {"textFormat": {"bold": True}, "horizontalAlignment": "CENTER"})
        
        return True
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return False

# --- INTERFAZ DE STREAMLIT ---
st.subheader("📋 Vista Previa del Censo a Exportar")

# Aquí usamos el DataFrame que ya procesaste con tu función cargar_censo_total()
df_censo = cargar_censo_total() 

if not df_censo.empty:
    st.dataframe(df_censo, use_container_width=True, hide_index=True)
    
    # BOTÓN PARA COPIAR
    if st.button("📤 Enviar Censo a Google Sheets y Autoajustar", use_container_width=True):
        with st.spinner("Sincronizando datos..."):
            if actualizar_hoja_google(df_censo):
                st.success("✅ ¡Datos copiados exitosamente! La hoja se ha autoajustado.")
