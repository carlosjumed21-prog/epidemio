import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Generador de Kardex")

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
        
        hoja_maestra = ss.get_worksheet(0)
        gid_maestra = hoja_maestra.id
        nombre_maestra = hoja_maestra.title
        
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="3000", cols="35")
        
        gid_historial = hoja_historial.id
            
        return ss, hoja_maestra, nombre_maestra, gid_maestra, hoja_historial, gid_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return [None]*6

# --- 2. LECTURA ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. PROCESAMIENTO CON MAPEO MANUAL ESTRICTO ---
def traspaso_con_formato(ss, h_orig, n_orig, gid_orig, h_dest, gid_dest, fila_datos, index_p):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3 
        
        fila_dest_inicio = (index_p * 8) + 1

        # --- MAPEO ESTRICTO SEGÚN COLUMNAS A, B, C, D, E, G, I ---
        val_fecha_orig = str(fila_datos.iloc[0]) # Col A
        val_especialidad = str(fila_datos.iloc[1]) # Col B
        val_cama = str(fila_datos.iloc[2]) # Col C
        val_registro = str(fila_datos.iloc[3]) # Col D
        val_paciente = str(fila_datos.iloc[4]) # Col E
        val_edad = str(fila_datos.iloc[6]) # Col G (Índice 6)
        val_ingreso = str(fila_datos.iloc[8]) # Col I (Índice 8)

        batch = [
            {'range': 'B3', 'values': [[val_especialidad]]}, # ESPECIALIDAD -> B3
            {'range': 'B4', 'values': [[val_cama]]},         # CAMA -> B4
            {'range': 'A5', 'values': [[val_paciente]]},     # Paciente -> A5
            {'range': 'B7', 'values': [[val_edad]]},         # EDAD -> B7
            {'range': 'B8', 'values': [[val_registro]]},     # REGISTRO -> B8
            {'range': 'B9', 'values': [[val_ingreso]]},      # Fecha de ingreso -> B9
            {'range': 'D4:AH4', 'values': [[''] * 31]}      # Limpieza X
        ]
        
        h_orig.batch_update(batch)
        h_orig.update_cell(4, columna_x, "X")

        # Traspaso al historial
        body = {
            "requests": [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": gid_orig,
                            "startRowIndex": 2, "endRowIndex": 10,
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
        st.error(f"Error procesando a {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Kardex", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    if st.button("📥 INICIAR VACIADO MASIVO", type="primary"):
        ss, h_ma, n_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
        
        if h_ma and h_hi:
            h_hi.clear()
            progreso = st.progress(0)
            status = st.empty()
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Procesando ({i+1}/{len(df_pacientes)}): {nombre}")
                
                if not traspaso_con_formato(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, i):
                    time.sleep(10)
                    traspaso_con_formato(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, i)
                
                progreso.progress((i + 1) / len(df_pacientes))
                time.sleep(8) 
            
            status.success("✅ ¡Vaciado completado con mapeo corregido!")
            st.balloons()
