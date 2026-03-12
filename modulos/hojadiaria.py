import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Procesamiento a Historial")

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
        
        # Obtener Hoja 1 (Plantilla) y Hoja 2 (Historial)
        hoja_plantilla = ss.get_worksheet(0)
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            # Si no existe "Historial", la crea
            hoja_historial = ss.add_worksheet(title="Historial", rows="1000", cols="35")
            
        return hoja_plantilla, hoja_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. FUNCIÓN DE PROCESAMIENTO ---
def procesar_a_historial(h_plantilla, h_historial, fila_datos, index_paciente):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        dia_num = dt.day
        columna_x = dia_num + 3
        
        # Cada bloque de plantilla mide 8 filas. 
        # El primero inicia en la fila 1 de la Hoja 2.
        fila_destino = (index_paciente * 8) + 1
        rango_destino = f"A{fila_destino}:AI{fila_destino + 7}"

        # PASO 1: Copiar estructura de Hoja 1 a Hoja 2
        h_historial.copy_range("A3:AI10", rango_destino)

        # PASO 2: Llenar datos con Batch Update (Calculando desplazamientos)
        batch = [
            {'range': f'B{fila_destino + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad (original B3)
            {'range': f'B{fila_destino + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama (original B4)
            {'range': f'A{fila_destino + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente (original A5)
            {'range': f'B{fila_destino + 5}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad (original B8)
            {'range': f'B{fila_destino + 6}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro (original B9)
            {'range': f'B{fila_destino + 7}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso (original B10)
        ]
        h_historial.batch_update(batch)

        # PASO 3: Nueva X (Original fila 4 -> fila_destino + 1)
        h_historial.update_cell(fila_destino + 1, columna_x, "X")
        
        return True
    except Exception as e:
        if "429" in str(e):
            time.sleep(15)
            return False
        st.error(f"Error con {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Hoja de Salida", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes detectados", len(df_pacientes))
    
    st.divider()

    # Reemplazo de st.confirm por un Checkbox de seguridad
    limpiar_antes = st.checkbox("Limpiar Hoja de Historial antes de procesar", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO A HOJA 2", type="primary"):
        h_plant, h_hist = conectar_google_sheets()
        if h_plant and h_hist:
            
            if limpiar_antes:
                h_hist.clear()
                st.info("Hoja de historial limpiada.")

            progreso = st.progress(0)
            status = st.empty()
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Copiando a Historial ({i+1}/{len(df_pacientes)}): {nombre}")
                
                # Intentar procesar
                if not procesar_a_historial(h_plant, h_hist, row, i):
                    time.sleep(10)
                    procesar_a_historial(h_plant, h_hist, row, i)
                
                progreso.progress((i + 1) / len(df_pacientes))
                # Pausa de 6 segundos para evitar error 429 de Google
                time.sleep(6) 
            
            status.success("✅ ¡Proceso masivo completado en la Hoja 2!")
            st.balloons()
else:
    st.warning("No se pudo cargar la vista previa del censo.")
