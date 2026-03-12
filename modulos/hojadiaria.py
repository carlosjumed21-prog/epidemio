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

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        # Cargamos el CSV y nos aseguramos de que no haya problemas con columnas vacías
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. FUNCIÓN DE PROCESAMIENTO (MAPEO CORREGIDO) ---
def traspaso_con_formato(ss, h_orig, n_orig, gid_orig, h_dest, gid_dest, fila_datos, index_p):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3 
        
        fila_dest_inicio = (index_p * 8) + 1

        # Mapeo estricto basado en tus columnas de origen (A=0, B=1, C=2, D=3, E=4, G=6, I=8)
        # y celdas de destino (B3, B4, A5, B7, B8, B9)
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # ESPECIALIDAD -> B3 (Col B)
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # CAMA -> B4 (Col C)
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente -> A5 (Col E)
            {'range': 'B7', 'values': [[str(fila_datos.iloc[6])]]}, # EDAD -> B7 (Col G)
            {'range': 'B8', 'values': [[str(fila_datos.iloc[3])]]}, # REGISTRO -> B8 (Col D)
            {'range': 'B9', 'values': [[str(fila_datos.iloc[8])]]}, # Fecha de ingreso -> B9 (Col I)
            {'range': 'D4:AH4', 'values': [[''] * 31]}            # Limpiar X
        ]
        
        h_orig.batch_update(batch)
        h_orig.update_cell(4, columna_x, "X")

        # Traspaso al historial manteniendo formato
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
    # 1. ENCABEZADO Y MÉTRICA
    st.metric("📊 Total de Pacientes en Censo", len(df_pacientes))
    
    col_link, _ = st.columns([1, 2])
    with col_link:
        st.link_button("📂 Ver Google Sheets (Kardex)", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")

    # 2. VISTA PREVIA
    with st.expander("🔍 Ver listado de pacientes para capturar"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    # 3. ACCIONES
    limpiar_h = st.checkbox("Limpiar historial antes de empezar", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO", type="primary"):
        ss, h_ma, n_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
        
        if h_ma and h_hi:
            if limpiar_h:
                h_hi.clear()
                st.info("Historial reseteado. Procesando...")

            progreso = st.progress(0)
            status = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Procesando ({i+1}/{total}): {nombre}")
                
                if not traspaso_con_formato(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, i):
                    # Pausa si falla por cuota y reintento
                    time.sleep(10)
                    traspaso_con_formato(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, i)
                
                progreso.progress((i + 1) / total)
                time.sleep(8) # Pausa de seguridad
            
            status.success("✅ ¡Censo completado! Datos y formatos en la pestaña 'Historial'.")
            st.balloons()
else:
    st.error("No se pudo cargar el censo. Verifica la conexión o el enlace CSV.")
