import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Historial con Formato")

# --- 1. CONEXIÓN ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        hoja_plantilla = ss.get_worksheet(0)
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="1000", cols="35")
            
        return ss, hoja_plantilla, hoja_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. LECTURA ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. FUNCIÓN DE PROCESAMIENTO (CON COPIADO DE FORMATO REAL) ---
def procesar_a_historial(ss, h_plantilla, h_historial, fila_datos, index_paciente):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3
        
        # Cada bloque mide 8 filas (A3:AI10)
        fila_destino = (index_paciente * 8) + 1
        
        # --- PASO CRUCIAL: COPIAR RANGO CON FORMATO ENTRE HOJAS ---
        # Usamos el método copy_range directamente desde el objeto Spreadsheet
        # Origen: Hoja 1, Rango A3:AI10 (Filas 3 a 10)
        # Destino: Hoja 2, Rango correspondiente
        ss.values_append(
            f"Historial!A{fila_destino}",
            params={'valueInputOption': 'RAW'},
            body={'values': [[''] * 35] * 8} # Crea el espacio
        )
        
        # Esta función clona el formato de la plantilla a la posición en el historial
        h_historial.copy_range(
            f"'{h_plantilla.title}'!A3:AI10", 
            f"A{fila_destino}:AI{fila_destino + 7}",
            copy_format=True,
            strategy="DEFAULT"
        )

        # PASO 2: Llenar datos (Batch Update)
        batch = [
            {'range': f'Historial!B{fila_destino + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad (B3)
            {'range': f'Historial!B{fila_destino + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama (B4)
            {'range': f'Historial!A{fila_destino + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente (A5)
            {'range': f'Historial!B{fila_destino + 5}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad (B8)
            {'range': f'Historial!B{fila_destino + 6}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro (B9)
            {'range': f'Historial!B{fila_destino + 7}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso (B10)
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': batch})

        # PASO 3: Nueva X
        h_historial.update_cell(fila_destino + 1, columna_x, "X")
        
        return True
    except Exception as e:
        if "429" in str(e):
            time.sleep(15)
            return False
        st.error(f"Error en {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes en Censo", len(df_pacientes))
    
    st.divider()
    limpiar_antes = st.checkbox("Limpiar Hoja de Historial antes de procesar", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO A HISTORIAL", type="primary"):
        ss_obj, h_plant, h_hist = conectar_google_sheets()
        if h_plant and h_hist:
            
            if limpiar_antes:
                h_hist.clear()
                st.info("Historial limpio.")

            progreso = st.progress(0)
            status = st.empty()
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Copiando con formato ({i+1}/{len(df_pacientes)}): {nombre}")
                
                if not procesar_a_historial(ss_obj, h_plant, h_hist, row, i):
                    time.sleep(10)
                    procesar_a_historial(ss_obj, h_plant, h_hist, row, i)
                
                progreso.progress((i + 1) / len(df_pacientes))
                # Pausa necesaria para que Google procese el formato pesado
                time.sleep(7) 
            
            status.success("✅ ¡Censo completado con formato original en la Hoja 2!")
            st.balloons()
