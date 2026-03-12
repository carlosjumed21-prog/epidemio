import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Sincronizador de Kardex (Evita Duplicados)")

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
        h_maestra = ss.get_worksheet(0)
        
        try:
            h_historial = ss.worksheet("Historial")
        except:
            h_historial = ss.add_worksheet(title="Historial", rows="5000", cols="35")
            
        return ss, h_maestra, h_historial
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None, None

# --- 2. LECTURA ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. LÓGICA DE PROCESAMIENTO ---
def procesar_paciente(ss, h_maestra, h_historial, fila_datos, reg_map):
    try:
        # Extraer Datos (Mapeo estricto Carlos)
        fecha_str = str(fila_datos.iloc[0])
        especialidad = str(fila_datos.iloc[1])
        cama = str(fila_datos.iloc[2])
        registro = str(fila_datos.iloc[3])
        paciente = str(fila_datos.iloc[4])
        edad = str(fila_datos.iloc[6])
        ingreso = str(fila_datos.iloc[8])

        # Calcular Columna X según el día
        dia = int(fecha_str.split('/')[0])
        col_x = dia + 3 # Día 1 = Col D (4)

        # ¿Ya existe el registro en el Historial?
        if registro in reg_map:
            # PACIENTE EXISTENTE: Usar su fila de inicio
            fila_base = reg_map[registro]
            accion = "Actualizado"
        else:
            # PACIENTE NUEVO: Ir al final del historial
            all_values = h_historial.get_all_values()
            fila_base = len(all_values) + 1
            # Clonar Plantilla de Hoja 1 a la nueva ubicación en Historial
            h_maestra.copy_to(ss.id) # Esto crea una copia temporal
            temp_sheet = ss.get_worksheet(len(ss.worksheets())-1)
            # Usar copyPaste para pasar el formato de la Maestra al final del Historial
            body = {
                "requests": [{
                    "copyPaste": {
                        "source": {"sheetId": h_maestra.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_historial.id, "startRowIndex": fila_base - 1, "endRowIndex": fila_base + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }
                }]
            }
            ss.batch_update(body)
            accion = "Nuevo"

        # Llenar/Actualizar datos en el bloque (Fila base es donde empieza A3)
        # Relativo a fila_base: B3(+0), B4(+1), A5(+2), B7(+4), B8(+5), B9(+6)
        updates = [
            {'range': f'Historial!B{fila_base + 0}', 'values': [[especialidad]]},
            {'range': f'Historial!B{fila_base + 1}', 'values': [[cama]]},
            {'range': f'Historial!A{fila_base + 2}', 'values': [[paciente]]},
            {'range': f'Historial!B{fila_base + 4}', 'values': [[edad]]},
            {'range': f'Historial!B{fila_base + 5}', 'values': [[registro]]},
            {'range': f'Historial!B{fila_base + 6}', 'values': [[ingreso]]}
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': updates})
        
        # Poner la X en la fila 4 del bloque (fila_base + 1)
        h_historial.update_cell(fila_base + 1, col_x, "X")
        
        return accion
    except Exception as e:
        return f"Error: {e}"

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.metric("Pacientes en Censo", len(df_pacientes))
    st.dataframe(df_pacientes.iloc[:, [3, 4, 2]], use_container_width=True) # Mostrar Registro, Nombre, Cama

    if st.button("🚀 SINCRONIZAR CENSO A HISTORIAL", type="primary"):
        ss, h_ma, h_hi = conectar_google_sheets()
        if ss:
            # 1. Crear Mapa de Registros actuales en Historial
            # El registro está en la celda B8 de cada bloque (filas 6, 14, 22...)
            status = st.empty()
            status.info("Analizando historial existente...")
            
            data_historial = h_hi.get_all_values()
            reg_map = {}
            # Buscamos el registro en la Columna B (índice 1) saltando de 8 en 8
            for r in range(5, len(data_historial), 8):
                val = data_historial[r][1]
                if val and val != "":
                    reg_map[val] = r - 5 + 1 # Fila donde inicia el bloque del paciente

            # 2. Procesar
            progreso = st.progress(0)
            n_nuevos = 0
            n_act = 0
            
            for i, row in df_pacientes.iterrows():
                res = procesar_paciente(ss, h_ma, h_hi, row, reg_map)
                if res == "Nuevo": n_nuevos += 1
                if res == "Actualizado": n_act += 1
                progreso.progress((i+1)/len(df_pacientes))
                time.sleep(2) # Pausa mínima para no saturar
            
            status.success(f"Proceso finalizado: {n_nuevos} nuevos y {n_act} actualizados.")
            st.balloons()
