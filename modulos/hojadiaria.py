import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Generador de Kardex")

# --- 1. CONEXIÓN SEGURA Y OBTENCIÓN DE IDS INTERNOS ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        # Necesitamos los IDs numéricos (GID) de las hojas para el traspaso forzado
        hoja_maestra = ss.get_worksheet(0)
        gid_maestra = hoja_maestra.id
        
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="3000", cols="35")
        
        gid_historial = hoja_historial.id
            
        return ss, hoja_maestra, gid_maestra, hoja_historial, gid_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None, None

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. FUNCIÓN DE TRASPASO FORZADO (VÍA GOOGLE API REQUEST) ---
def traspaso_forzado_con_formato(ss, gid_orig, gid_dest, fila_datos, index_p):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3 # Día 1 = Col D (índice 3 en API)
        
        # Cálculo de fila destino (0-indexed para la API)
        # Bloques de 8 filas. Paciente 0 -> fila 0, Paciente 1 -> fila 8...
        start_row = index_p * 8
        
        # PREPARAR EL PROCESO: Primero escribimos en la MAESTRA (Filas 3-10 -> índices 2-10)
        hoja_maestra = ss.get_worksheet(0)
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X
        ]
        hoja_maestra.batch_update(batch)
        hoja_maestra.update_cell(4, columna_x, "X")

        # PASO MAESTRO: Copiar de Hoja 1 a Hoja 2 usando "CopyPasteRequest" de Google
        # Esto clona TODO: bordes, colores, anchos de columna y datos.
        body = {
            "requests": [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": gid_orig,
                            "startRowIndex": 2, "endRowIndex": 10, # Filas 3 a 10
                            "startColumnIndex": 0, "endColumnIndex": 35 # Col A a AI
                        },
                        "destination": {
                            "sheetId": gid_dest,
                            "startRowIndex": start_row,
                            "endRowIndex": start_row + 8,
                            "startColumnIndex": 0, "endColumnIndex": 35
                        },
                        "pasteType": "PASTE_NORMAL" # Copia TODO (Formato + Valores)
                    }
                }
            ]
        }
        ss.batch_update(body)
        return True
    except Exception as e:
        if "429" in str(e):
            time.sleep(15)
            return False
        st.error(f"Error procesando a {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Kardex", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    st.metric("Pacientes en Censo", len(df_pacientes))
    
    st.divider()
    limpiar = st.checkbox("Limpiar Historial antes de empezar", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO A HISTORIAL", type="primary"):
        ss, h_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
        
        if h_ma and h_hi:
            if limpiar:
                h_hi.clear()
                st.info("Historial reseteado. Iniciando traspaso forzado...")

            progreso = st.progress(0)
            status = st.empty()
            
            for i, row in df_pacientes.iterrows():
                nombre_p = row.iloc[4]
                status.text(f"Traspasando con formato ({i+1}/{len(df_pacientes)}): {nombre_p}")
                
                if not traspaso_forzado_con_formato(ss, gid_ma, gid_hi, row, i):
                    time.sleep(10)
                    traspaso_forzado_con_formato(ss, gid_ma, gid_hi, row, i)
                
                progreso.progress((i + 1) / len(df_pacientes))
                time.sleep(8) # Pausa para estabilidad de cuota
            
            # Limpieza final de Hoja 1
            h_ma.batch_update([{'range': 'A3:AI10', 'values': [[''] * 35] * 8}])
            
            status.success("✅ ¡Proceso terminado! Todos los datos y formatos están en 'Historial'.")
            st.balloons()
else:
    st.error("No se pudo cargar el censo.")
