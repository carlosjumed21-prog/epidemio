import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Generador de Kardex")

# --- 1. CONEXIÓN SEGURA Y OBTENCIÓN DE IDS ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        # Identificamos la Hoja Maestra (Índice 0)
        hoja_maestra = ss.get_worksheet(0)
        gid_maestra = hoja_maestra.id
        nombre_maestra = hoja_maestra.title
        
        # Identificamos o creamos la Hoja de Historial
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="3000", cols="35")
        
        gid_historial = hoja_historial.id
            
        return ss, hoja_maestra, nombre_maestra, gid_maestra, hoja_historial, gid_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return [None]*6

# --- 2. LECTURA DEL CENSO (CSV PUBLICADO) ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. FUNCIÓN DE PROCESAMIENTO CON NUEVO MAPEO ---
def traspaso_con_formato(ss, h_orig, n_orig, gid_orig, h_dest, gid_dest, fila_datos, index_p):
    try:
        # Procesar fecha para columna X (D4 es día 1 -> columna 4)
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3 
        
        # Fila destino en Historial (bloques de 8 filas)
        fila_dest_inicio = (index_p * 8) + 1

        # A. Vaciado en la Plantilla Maestra (Hoja 1)
        # Basado en tus nuevas coordenadas:
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # ESPECIALIDAD (Col B)
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # CAMA (Col C)
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente (Col E)
            {'range': 'B7', 'values': [[str(fila_datos.iloc[5])]]}, # EDAD (Col G)
            {'range': 'B8', 'values': [[str(fila_datos.iloc[3])]]}, # REGISTRO (Col D)
            {'range': 'B9', 'values': [[str(fila_datos.iloc[6])]]}, # Fecha de ingreso (Col I)
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X previas
        ]
        h_orig.batch_update(batch)
        h_orig.update_cell(4, columna_x, "X") # Marcar día

        # B. Traspaso de bloque completo al Historial (CopyPaste API)
        # Esto clona el molde de Hoja 1 hacia el espacio correspondiente en Hoja 2
        body = {
            "requests": [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": gid_orig,
                            "startRowIndex": 2, "endRowIndex": 10, # A3:AI10
                            "startColumnIndex": 0, "endColumnIndex": 35
                        },
                        "destination": {
                            "sheetId": gid_dest,
                            "startRowIndex": fila_dest_inicio - 1,
                            "endRowIndex": fila_dest_inicio + 7,
                            "startColumnIndex": 0, "endColumnIndex": 35
                        },
                        "pasteType": "PASTE_NORMAL"
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
        st.error(f"Error con {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Kardex en Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    st.metric("Pacientes detectados", len(df_pacientes))
    
    st.divider()
    limpiar_historial = st.checkbox("Limpiar historial antes de empezar", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO", type="primary"):
        ss, h_ma, n_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
        
        if h_ma and h_hi:
            if limpiar_historial:
                h_hi.clear()
                st.info("Historial reseteado. Procesando pacientes...")

            progreso = st.progress(0)
            status = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Traspasando ({i+1}/{total}): {nombre}")
                
                if not traspaso_con_formato(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, i):
                    time.sleep(10)
                    traspaso_con_formato(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, i)
                
                progreso.progress((i + 1) / total)
                time.sleep(8) # Pausa de seguridad para evitar error 429
            
            status.success("✅ ¡Vaciado completado! La Hoja 1 se usó como molde y el Historial está listo.")
            st.balloons()
else:
    st.error("No se pudo cargar el censo.")
