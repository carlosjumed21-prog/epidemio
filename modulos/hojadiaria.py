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
        
        # Identificamos o creamos la Hoja de Historial
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

# --- 3. FUNCIÓN DE TRASPASO CON MAPEO ACTUALIZADO ---
def traspaso_con_formato(ss, gid_orig, gid_dest, fila_datos, index_p):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3 
        
        # Fila destino en la Hoja 2 (0-indexed)
        start_row_dest = index_p * 8
        
        # AJUSTE DE MAPEO POR ELIMINACIÓN DE FILA 5:
        # iloc[0]: Fecha (se mantiene)
        # iloc[1]: Especialidad (se mantiene)
        # iloc[2]: Cama (se mantiene)
        # iloc[3]: Registro (antes era 3, ahora se extrae de la nueva posición)
        # iloc[4]: Nombre (antes era 4, ahora es el nuevo 3 o 4 dependiendo del CSV)
        
        hoja_maestra = ss.get_worksheet(0)
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': 'A5', 'values': [[str(fila_datos.iloc[3])]]}, # Paciente (Ajustado)
            {'range': 'B8', 'values': [[str(fila_datos.iloc[5])]]}, # Edad (Ajustado)
            {'range': 'B9', 'values': [[str(fila_datos.iloc[2])]]}, # Registro (Ajustado)
            {'range': 'B10', 'values': [[str(fila_datos.iloc[7])]]},# Ingreso (Ajustado)
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X
        ]
        hoja_maestra.batch_update(batch)
        hoja_maestra.update_cell(4, columna_x, "X")

        # B. Copiamos el bloque completo de Hoja 1 a Hoja 2 (Historial)
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
                            "startRowIndex": start_row_dest,
                            "endRowIndex": start_row_dest + 8,
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
        st.error(f"Error con {fila_datos.iloc[3] if len(fila_datos)>3 else 'Paciente'}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    st.metric("Pacientes en Censo", len(df_pacientes))
    
    st.divider()
    limpiar_h = st.checkbox("Limpiar Historial antes de empezar", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO", type="primary"):
        ss, h_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
        
        if h_ma and h_hi:
            if limpiar_h:
                h_hi.clear()
                st.info("Historial reseteado. Procesando con nuevo mapeo...")

            progreso = st.progress(0)
            status = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                # Nombre ahora está en iloc[3] tras eliminar la fila 5
                nombre_p = row.iloc[3] if len(row) > 3 else "Paciente"
                status.text(f"Procesando ({i+1}/{total}): {nombre_p}")
                
                if not traspaso_con_formato(ss, gid_ma, gid_hi, row, i):
                    time.sleep(10)
                    traspaso_con_formato(ss, gid_ma, gid_hi, row, i)
                
                progreso.progress((i + 1) / total)
                time.sleep(8) 
            
            status.success("✅ ¡Proceso completado con el nuevo mapeo!")
            st.balloons()
else:
    st.error("No se pudo cargar el censo.")
